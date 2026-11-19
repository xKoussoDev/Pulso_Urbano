from io import BytesIO
from uuid import UUID, uuid4

import psycopg
from fastapi import APIRouter, Depends, File, UploadFile
from PIL import Image, ImageOps, UnidentifiedImageError
from storage3.exceptions import StorageException

from .auth import User, error, require_citizen
from .report_routes import database_url
from .supabase_client import get_supabase_client


router = APIRouter(prefix="/api/v1")
BUCKET = "report-photos"
MAX_BYTES = 5 * 1024 * 1024
MAX_PHOTOS = 2
Image.MAX_IMAGE_PIXELS = 25_000_000
FORMATS = {"image/jpeg": ("JPEG", "jpg"), "image/png": ("PNG", "png")}


def clean_image(data: bytes, mime: str) -> bytes:
    try:
        with Image.open(BytesIO(data)) as source:
            if source.format != FORMATS[mime][0] or getattr(source, "n_frames", 1) != 1:
                raise error(415, "UNSUPPORTED_MEDIA_TYPE", "La imagen no coincide con JPEG/PNG")
            if source.width * source.height > 25_000_000:
                raise error(422, "VALIDATION_ERROR", "La imagen tiene demasiados píxeles")
            source.load()
            oriented = ImageOps.exif_transpose(source)
            oriented.thumbnail((2048, 2048))
            mode = "RGB" if mime == "image/jpeg" else "RGBA"
            pixels = Image.new(mode, oriented.size)
            pixels.paste(oriented.convert(mode))
            output = BytesIO()
            if mime == "image/jpeg":
                pixels.save(output, format="JPEG", quality=85, optimize=True)
            else:
                pixels.save(output, format="PNG", optimize=True)
            cleaned = output.getvalue()
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError) as exc:
        raise error(422, "VALIDATION_ERROR", "La imagen está dañada o no se puede leer") from exc
    if len(cleaned) > MAX_BYTES:
        raise error(413, "PAYLOAD_TOO_LARGE", "La imagen procesada supera 5 MB")
    return cleaned


@router.post("/reports/{report_id}/photos", status_code=201)
def add_report_photo(report_id: UUID, photo: UploadFile = File(...), user: User = Depends(require_citizen)) -> dict:
    mime = photo.content_type or ""
    if mime not in FORMATS:
        raise error(415, "UNSUPPORTED_MEDIA_TYPE", "Solo se aceptan imágenes JPEG o PNG")
    try:
        data = photo.file.read(MAX_BYTES + 1)
    finally:
        photo.file.close()
    if len(data) > MAX_BYTES:
        raise error(413, "PAYLOAD_TOO_LARGE", "La fotografía supera 5 MB")
    if not data:
        raise error(422, "VALIDATION_ERROR", "La fotografía está vacía")
    cleaned = clean_image(data, mime)

    photo_id = uuid4()
    path = f"{report_id}/{photo_id}.{FORMATS[mime][1]}"
    uploaded = False
    bucket = None
    try:
        with psycopg.connect(database_url(), connect_timeout=5) as conn:
            owner = conn.execute(
                "select id from public.reports where id=%s and reporter_id=%s for update",
                (report_id, user.id),
            ).fetchone()
            if owner is None:
                raise error(404, "NOT_FOUND", "Reporte no encontrado")
            count = conn.execute(
                "select count(*) from public.report_photos where report_id=%s", (report_id,)
            ).fetchone()[0]
            if count >= MAX_PHOTOS:
                raise error(422, "VALIDATION_ERROR", "El reporte ya tiene dos fotografías")
            bucket = get_supabase_client().storage.from_(BUCKET)
            bucket.upload(path, cleaned, {"content-type": mime, "upsert": "false"})
            uploaded = True
            conn.execute(
                """insert into public.report_photos (id, report_id, storage_path, mime_type, size_bytes)
                   values (%s, %s, %s, %s, %s)""",
                (photo_id, report_id, path, mime, len(cleaned)),
            )
    except (psycopg.Error, StorageException, RuntimeError) as exc:
        if uploaded and bucket is not None:
            try:
                bucket.remove([path])
            except StorageException:
                pass
        raise error(503, "DEPENDENCY_UNAVAILABLE", "No se pudo guardar la fotografía") from exc
    return {"photo_id": str(photo_id)}
