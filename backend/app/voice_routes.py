from functools import lru_cache
from io import BytesIO
from pathlib import Path
import re
from threading import BoundedSemaphore

import av
from fastapi import APIRouter, Depends, File, UploadFile
from faster_whisper import WhisperModel
from faster_whisper.audio import decode_audio

from .auth import User, error, require_citizen
from .ai_extraction import extract_suggestions
from .report_routes import EMAIL, PHONE


router = APIRouter(prefix="/api/v1")
MAX_AUDIO_BYTES = 10 * 1024 * 1024
SAMPLE_RATE = 16000
MAX_AUDIO_SECONDS = 10
transcription_slot = BoundedSemaphore(1)
PERSONAL_HINT = re.compile(
    r"\b(?:me llamo|mi nombre es|mi tel[eé]fono|mi celular|mi n[uú]mero es|mi correo|vivo en|mi casa|mi domicilio|mi direcci[oó]n)\b"
    r"|\b(?:calle|avenida|domicilio|departamento|interior)\b.{0,50}\b\d{1,5}\b",
    re.IGNORECASE,
)


@lru_cache(maxsize=1)
def whisper_model() -> WhisperModel:
    model_dir = Path(__file__).resolve().parents[1] / ".models"
    return WhisperModel("base", device="cpu", compute_type="int8", download_root=str(model_dir))


def manual_draft(reason: str, transcription: str | None = None, redacted: bool = False) -> dict:
    description = transcription if transcription and 10 <= len(transcription) <= 1000 else None
    warnings = ["Revisa y corrige todos los datos antes de enviar; no incluyas datos personales"]
    if redacted:
        warnings.insert(0, "Se omitieron posibles datos personales de la transcripción")
    return {
        "mode": "manual_fallback",
        "reason": reason,
        "transcription": transcription,
        "draft": {
            "category_id": None,
            "description": description,
            "duration_text": None,
            "severity_proposed": None,
            "location": None,
        },
        "missing_fields": ["category_id", *([] if description else ["description"]), "severity", "location"],
        "warnings": warnings,
    }


@router.post("/ai/process-voice-report")
def process_voice_report(audio: UploadFile = File(...), _user: User = Depends(require_citizen)) -> dict:
    if not (audio.filename or "").lower().endswith(".m4a") or audio.content_type not in {
        "audio/mp4", "audio/x-m4a", "audio/m4a", "application/octet-stream"
    }:
        raise error(415, "UNSUPPORTED_MEDIA_TYPE", "Se requiere audio .m4a")

    try:
        data = audio.file.read(MAX_AUDIO_BYTES + 1)
    finally:
        audio.file.close()
    if len(data) > MAX_AUDIO_BYTES:
        raise error(413, "PAYLOAD_TOO_LARGE", "El audio supera 10 MB")
    if not data:
        raise error(422, "VALIDATION_ERROR", "El audio está vacío")

    try:
        samples = decode_audio(BytesIO(data), sampling_rate=SAMPLE_RATE)
    except (av.error.FFmpegError, OSError, ValueError) as exc:
        raise error(422, "VALIDATION_ERROR", "No se pudo leer el audio") from exc
    if len(samples) == 0:
        raise error(422, "VALIDATION_ERROR", "El audio está vacío")
    if len(samples) > MAX_AUDIO_SECONDS * SAMPLE_RATE:
        raise error(422, "VALIDATION_ERROR", "El audio supera 10 segundos")
    if max(abs(float(samples.max())), abs(float(samples.min()))) < 0.003:
        return manual_draft("TRANSCRIPTION_UNAVAILABLE")

    if not transcription_slot.acquire(blocking=False):
        raise error(429, "TOO_MANY_REQUESTS", "Hay otra transcripción en curso; intenta de nuevo")
    try:
        segments, _ = whisper_model().transcribe(samples, language="es", beam_size=1)
        transcription = " ".join(segment.text.strip() for segment in segments).strip()
    except Exception:
        return manual_draft("TRANSCRIPTION_UNAVAILABLE")
    finally:
        transcription_slot.release()

    if not transcription:
        return manual_draft("TRANSCRIPTION_UNAVAILABLE")
    sanitized = EMAIL.sub("[correo omitido]", transcription)
    sanitized = PHONE.sub("[teléfono omitido]", sanitized)
    redacted = sanitized != transcription
    if redacted or PERSONAL_HINT.search(sanitized):
        draft = manual_draft("REDACTION_REVIEW_REQUIRED", sanitized, redacted)
        if not redacted:
            draft["warnings"].insert(0, "Puede haber datos personales; corrige el texto antes de enviar")
        return draft
    try:
        suggestion = extract_suggestions(sanitized)
    except Exception:
        suggestion = None
    if not suggestion:
        return manual_draft("EXTRACTION_UNAVAILABLE", sanitized)
    draft = manual_draft("EXTRACTION_UNAVAILABLE", sanitized)
    draft["mode"] = "suggested"
    del draft["reason"]
    draft["draft"].update(suggestion)
    draft["missing_fields"] = [
        *([] if suggestion["category_id"] else ["category_id"]),
        *([] if draft["draft"]["description"] else ["description"]),
        *([] if suggestion["severity_proposed"] else ["severity"]),
        "location",
    ]
    return draft
