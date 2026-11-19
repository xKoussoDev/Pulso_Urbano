import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.ai_extraction import extract_suggestions


class GeminiExtractionTests(unittest.TestCase):
    def setUp(self):
        self.categories = {"fuga_agua": ("11111111-1111-4111-8111-111111111111", "Fuga de agua")}

    def fake_response(self, fields):
        import json
        return SimpleNamespace(
            raise_for_status=lambda: None,
            json=lambda: {"candidates": [{"finishReason": "STOP", "content": {"parts": [{"text": json.dumps(fields)}]}}]},
        )

    def test_missing_key_never_calls_gemini(self):
        with patch.dict(os.environ, {"GEMINI_API_KEY": ""}), patch("app.ai_extraction.httpx.post") as post:
            self.assertIsNone(extract_suggestions("Hay una fuga de agua"))
            post.assert_not_called()

    def test_accepts_only_supported_fields(self):
        fields = {
            "category_code": "fuga_agua", "category_evidence": "fuga de agua",
            "duration_text": "tres días", "severity_proposed": "high", "severity_evidence": "muy grave",
        }
        text = "Hay una fuga de agua desde hace tres días. Es muy grave."
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"}), \
             patch("app.ai_extraction.active_categories", return_value=self.categories), \
             patch("app.ai_extraction.httpx.post", return_value=self.fake_response(fields)) as post:
            result = extract_suggestions(text)
        self.assertEqual(result["category_id"], self.categories["fuga_agua"][0])
        self.assertEqual(result["duration_text"], "tres días")
        self.assertEqual(result["severity_proposed"], "high")
        request = post.call_args.kwargs
        self.assertEqual(request["json"]["contents"][0]["parts"][0]["text"], text)
        self.assertNotIn("location", request["json"])
        self.assertEqual(request["headers"]["x-goog-api-key"], "test_key")

    def test_rejects_hallucinated_evidence(self):
        fields = {
            "category_code": "fuga_agua", "category_evidence": "fuga de agua",
            "duration_text": "tres días", "severity_proposed": "critical", "severity_evidence": "riesgo de muerte",
        }
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"}), \
             patch("app.ai_extraction.active_categories", return_value=self.categories), \
             patch("app.ai_extraction.httpx.post", return_value=self.fake_response(fields)):
            result = extract_suggestions("Hay una fuga de agua.")
        self.assertEqual(result["category_id"], self.categories["fuga_agua"][0])
        self.assertIsNone(result["duration_text"])
        self.assertIsNone(result["severity_proposed"])


if __name__ == "__main__":
    unittest.main()
