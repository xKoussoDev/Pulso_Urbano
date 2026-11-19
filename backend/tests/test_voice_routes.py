import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from uuid import UUID

from fastapi.testclient import TestClient

from app.auth import User, require_citizen
from app.main import app


class VoiceRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not shutil.which("ffmpeg"):
            raise unittest.SkipTest("ffmpeg no está instalado")
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.audio_path = Path(cls.temp_dir.name) / "demo.m4a"
        subprocess.run(
            ["ffmpeg", "-nostdin", "-loglevel", "error", "-f", "lavfi", "-i",
             "sine=frequency=440:duration=2", "-c:a", "aac", str(cls.audio_path)],
            check=True,
        )
        cls.long_audio_path = Path(cls.temp_dir.name) / "long.m4a"
        subprocess.run(
            ["ffmpeg", "-nostdin", "-loglevel", "error", "-f", "lavfi", "-i",
             "anullsrc=r=16000:cl=mono", "-t", "31", "-c:a", "aac", str(cls.long_audio_path)],
            check=True,
        )

    @classmethod
    def tearDownClass(cls):
        cls.temp_dir.cleanup()

    def setUp(self):
        app.dependency_overrides[require_citizen] = lambda: User(UUID(int=1), True)
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        app.dependency_overrides.clear()

    def post_audio(self, data, filename="demo.m4a", mime="audio/mp4"):
        return self.client.post(
            "/api/v1/ai/process-voice-report",
            files={"audio": (filename, data, mime)},
        )

    def test_requires_citizen_session(self):
        app.dependency_overrides.clear()
        response = self.post_audio(self.audio_path.read_bytes())
        self.assertEqual(response.status_code, 401)

    def test_returns_editable_redacted_transcription_without_report(self):
        fake_model = SimpleNamespace(transcribe=lambda *_args, **_kwargs: (
            iter([SimpleNamespace(text="Hay una fuga. Mi correo es demo@example.com")]), None
        ))
        with patch("app.voice_routes.whisper_model", return_value=fake_model), \
             patch("app.voice_routes.extract_suggestions") as extract:
            response = self.post_audio(self.audio_path.read_bytes())
            extract.assert_not_called()
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["mode"], "manual_fallback")
        self.assertEqual(body["reason"], "REDACTION_REVIEW_REQUIRED")
        self.assertNotIn("demo@example.com", body["transcription"])
        self.assertEqual(body["draft"]["description"], body["transcription"])
        self.assertIsNone(body["draft"]["category_id"])

    def test_rejects_wrong_format_bad_audio_and_large_upload(self):
        data = self.audio_path.read_bytes()
        self.assertEqual(self.post_audio(data, filename="demo.wav").status_code, 415)
        self.assertEqual(self.post_audio(b"not audio").status_code, 422)
        self.assertEqual(self.post_audio(b"x" * (10 * 1024 * 1024 + 1)).status_code, 413)

    def test_rejects_audio_over_30_seconds(self):
        response = self.post_audio(self.long_audio_path.read_bytes())
        self.assertEqual(response.status_code, 422)

    def test_personal_hint_skips_gemini(self):
        fake_model = SimpleNamespace(transcribe=lambda *_args, **_kwargs: (
            iter([SimpleNamespace(text="Me llamo Persona Demo y hay un bache")]), None
        ))
        with patch("app.voice_routes.whisper_model", return_value=fake_model), \
             patch("app.voice_routes.extract_suggestions") as extract:
            response = self.post_audio(self.audio_path.read_bytes())
            extract.assert_not_called()
        self.assertEqual(response.json()["reason"], "REDACTION_REVIEW_REQUIRED")

    def test_gemini_failure_keeps_manual_draft(self):
        fake_model = SimpleNamespace(transcribe=lambda *_args, **_kwargs: (
            iter([SimpleNamespace(text="Hay una fuga de agua desde ayer")]), None
        ))
        with patch("app.voice_routes.whisper_model", return_value=fake_model), \
             patch("app.voice_routes.extract_suggestions", side_effect=RuntimeError("unavailable")):
            response = self.post_audio(self.audio_path.read_bytes())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["reason"], "EXTRACTION_UNAVAILABLE")
        self.assertEqual(response.json()["draft"]["description"], "Hay una fuga de agua desde ayer")


if __name__ == "__main__":
    unittest.main()
