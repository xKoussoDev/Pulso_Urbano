import os
import unittest
from io import BytesIO
from unittest.mock import MagicMock, patch
from uuid import UUID

from fastapi.testclient import TestClient
from PIL import Image
import psycopg

from app.auth import User, require_citizen
from app.main import app
from app.photo_routes import clean_image
from app.report_routes import database_url
from app.supabase_client import get_supabase_client


REPORT_ID = "11111111-1111-4111-8111-111111111111"


def sample_image() -> bytes:
    image = Image.new("RGB", (20, 20), "red")
    metadata = Image.Exif()
    metadata[315] = "Nombre privado"
    output = BytesIO()
    image.save(output, format="JPEG", exif=metadata)
    return output.getvalue()


class PhotoRouteTests(unittest.TestCase):
    def setUp(self):
        app.dependency_overrides[require_citizen] = lambda: User(UUID(int=1), True)
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        app.dependency_overrides.clear()

    def post_photo(self, data: bytes, mime: str = "image/jpeg"):
        return self.client.post(
            f"/api/v1/reports/{REPORT_ID}/photos",
            files={"photo": ("demo.jpg", data, mime)},
        )

    def test_requires_session(self):
        app.dependency_overrides.clear()
        response = self.post_photo(sample_image())
        self.assertEqual(response.status_code, 401)

    def test_rejects_invalid_image_and_size(self):
        image = sample_image()
        self.assertEqual(self.post_photo(image, "text/plain").status_code, 415)
        self.assertEqual(self.post_photo(b"broken").status_code, 422)
        self.assertEqual(self.post_photo(b"x" * (5 * 1024 * 1024 + 1)).status_code, 413)
        self.assertEqual(self.post_photo(b"").status_code, 422)
        self.assertEqual(self.post_photo(image, "image/png").status_code, 415)

    def test_removes_embedded_metadata(self):
        original = sample_image()
        cleaned = clean_image(original, "image/jpeg")
        with Image.open(BytesIO(cleaned)) as image:
            self.assertEqual(image.format, "JPEG")
            self.assertEqual(len(image.getexif()), 0)
        self.assertNotIn(b"Nombre privado", cleaned)

    @patch("app.photo_routes.get_supabase_client")
    @patch("app.photo_routes.psycopg.connect")
    @patch("app.photo_routes.database_url", return_value="postgresql://example")
    def test_uploads_only_to_owned_report(self, _url, connect, supabase):
        connection = connect.return_value.__enter__.return_value
        connection.execute.return_value.fetchone.side_effect = [(UUID(REPORT_ID),), (0,)]
        bucket = supabase.return_value.storage.from_.return_value
        response = self.post_photo(sample_image())
        self.assertEqual(response.status_code, 201)
        self.assertIn("photo_id", response.json())
        self.assertEqual(connection.execute.call_count, 3)
        self.assertIn("reporter_id=%s", connection.execute.call_args_list[0].args[0])
        self.assertEqual(connection.execute.call_args_list[0].args[1][1], UUID(int=1))
        self.assertEqual(bucket.upload.call_count, 1)
        path, data, options = bucket.upload.call_args.args
        self.assertTrue(path.startswith(f"{REPORT_ID}/"))
        self.assertEqual(options["content-type"], "image/jpeg")
        self.assertEqual(options["upsert"], "false")
        self.assertEqual(len(Image.open(BytesIO(data)).getexif()), 0)

    @patch("app.photo_routes.psycopg.connect")
    @patch("app.photo_routes.database_url", return_value="postgresql://example")
    def test_hides_other_report_and_limits_two_photos(self, _url, connect):
        connection = connect.return_value.__enter__.return_value
        connection.execute.return_value.fetchone.return_value = None
        self.assertEqual(self.post_photo(sample_image()).status_code, 404)
        connection.execute.return_value.fetchone.side_effect = [(UUID(REPORT_ID),), (2,)]
        self.assertEqual(self.post_photo(sample_image()).status_code, 422)

    @patch("app.photo_routes.get_supabase_client")
    @patch("app.photo_routes.psycopg.connect")
    @patch("app.photo_routes.database_url", return_value="postgresql://example")
    def test_removes_uploaded_file_when_database_insert_fails(self, _url, connect, supabase):
        connection = connect.return_value.__enter__.return_value
        connection.execute.return_value.fetchone.side_effect = [(UUID(REPORT_ID),), (0,)]
        connection.execute.side_effect = [
            MagicMock(fetchone=lambda: (UUID(REPORT_ID),)),
            MagicMock(fetchone=lambda: (0,)),
            psycopg.Error("falló la inserción"),
        ]
        bucket = supabase.return_value.storage.from_.return_value
        response = self.post_photo(sample_image())
        self.assertEqual(response.status_code, 503)
        path = bucket.upload.call_args.args[0]
        bucket.remove.assert_called_once_with([path])

    @unittest.skipUnless(os.getenv("RUN_PHOTO_INTEGRATION") == "1", "Requiere Supabase de demo")
    def test_real_private_upload_and_cleanup(self):
        with psycopg.connect(database_url(), connect_timeout=5) as connection:
            row = connection.execute(
                """select r.id, r.reporter_id from public.reports r
                   where (select count(*) from public.report_photos p where p.report_id=r.id) < 2
                   order by r.created_at desc limit 1"""
            ).fetchone()
        if row is None:
            self.skipTest("No hay reporte ficticio apto para la prueba")
        report_id, reporter_id = row
        app.dependency_overrides[require_citizen] = lambda: User(reporter_id, True)
        photo_id = None
        path = None
        bucket = get_supabase_client().storage.from_("report-photos")
        try:
            response = self.client.post(
                f"/api/v1/reports/{report_id}/photos",
                files={"photo": ("demo.jpg", sample_image(), "image/jpeg")},
            )
            self.assertEqual(response.status_code, 201, response.json())
            photo_id = UUID(response.json()["photo_id"])
            path = f"{report_id}/{photo_id}.jpg"
            with psycopg.connect(database_url(), connect_timeout=5) as connection:
                stored = connection.execute(
                    "select storage_path, mime_type, size_bytes from public.report_photos where id=%s",
                    (photo_id,),
                ).fetchone()
            self.assertIsNotNone(stored)
            stored_path, mime, size = stored
            self.assertEqual(stored_path, path)
            self.assertEqual(mime, "image/jpeg")
            downloaded = bucket.download(path)
            self.assertEqual(len(downloaded), size)
            self.assertEqual(len(Image.open(BytesIO(downloaded)).getexif()), 0)
        finally:
            if path is not None:
                bucket.remove([path])
            if photo_id is not None:
                with psycopg.connect(database_url(), connect_timeout=5) as connection:
                    connection.execute("delete from public.report_photos where id=%s", (photo_id,))


if __name__ == "__main__":
    unittest.main()
