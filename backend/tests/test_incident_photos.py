import os
import unittest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from uuid import UUID

import httpx
import psycopg
from fastapi.testclient import TestClient

from app.auth import User, get_current_user, require_staff
from app.main import app
from app.report_routes import database_url


INCIDENT_ID = UUID("11111111-1111-4111-8111-111111111111")
MUNICIPALITY_ID = UUID("22222222-2222-4222-8222-222222222222")
PHOTO_ID = UUID("33333333-3333-4333-8333-333333333333")
NOW = datetime.now(timezone.utc)


class IncidentPhotoTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        app.dependency_overrides.clear()

    @staticmethod
    def staff(municipality=MUNICIPALITY_ID):
        app.dependency_overrides[require_staff] = lambda: (User(UUID(int=2), False), municipality)

    def test_requires_staff(self):
        self.assertEqual(self.client.get(f"/api/v1/incidents/{INCIDENT_ID}").status_code, 401)
        app.dependency_overrides[get_current_user] = lambda: User(UUID(int=3), True)
        self.assertEqual(self.client.get(f"/api/v1/incidents/{INCIDENT_ID}").status_code, 403)

    @patch("app.incident_routes.get_supabase_client")
    @patch("app.incident_routes.psycopg.connect")
    def test_signs_photos_only_after_municipality_check(self, connect, supabase):
        self.staff()
        connection = connect.return_value.__enter__.return_value
        connection.execute.return_value.fetchone.return_value = None
        denied = self.client.get(f"/api/v1/incidents/{INCIDENT_ID}")
        self.assertEqual(denied.status_code, 404)
        self.assertEqual(connection.execute.call_count, 1)
        supabase.assert_not_called()

        row = (INCIDENT_ID, "fuga_agua", "Fuga de agua", "Fuga de agua", "Ejemplo ficticio",
               21.88, -102.29, "high", "reported", 1, 1, 2, 1, 60, 0, NOW, NOW, NOW)
        connection.execute.side_effect = [
            MagicMock(fetchone=lambda: row),
            MagicMock(fetchall=lambda: []),
            MagicMock(fetchall=lambda: [(PHOTO_ID, f"{UUID(int=4)}/{PHOTO_ID}.jpg", NOW)]),
        ]
        bucket = supabase.return_value.storage.from_.return_value
        bucket.create_signed_url.return_value = {"signedURL": "https://example.invalid/signed"}
        allowed = self.client.get(f"/api/v1/incidents/{INCIDENT_ID}")
        self.assertEqual(allowed.status_code, 200)
        self.assertEqual(allowed.headers["cache-control"], "no-store")
        self.assertEqual(allowed.json()["photos"][0]["url"], "https://example.invalid/signed")
        self.assertEqual(allowed.json()["confirmations_count"], 2)
        self.assertNotIn("reporter_id", str(allowed.json()["photos"]))
        self.assertNotIn("storage_path", str(allowed.json()["photos"]))
        bucket.create_signed_url.assert_called_once_with(f"{UUID(int=4)}/{PHOTO_ID}.jpg", 300)

    @unittest.skipUnless(os.getenv("RUN_PHOTO_INTEGRATION") == "1", "Requiere Supabase de demo")
    def test_real_photo_url_is_private_and_municipality_scoped(self):
        with psycopg.connect(database_url(), connect_timeout=5) as connection:
            row = connection.execute(
                """select i.id, i.municipality_id, p.id
                   from public.report_photos p
                   join public.reports r on r.id=p.report_id
                   join public.incidents i on i.id=r.incident_id
                   order by p.created_at desc limit 1"""
            ).fetchone()
        if row is None:
            self.skipTest("No hay foto ficticia guardada")
        incident_id, municipality_id, photo_id = row
        self.staff(UUID(int=999))
        self.assertEqual(self.client.get(f"/api/v1/incidents/{incident_id}").status_code, 404)
        self.staff(municipality_id)
        response = self.client.get(f"/api/v1/incidents/{incident_id}")
        self.assertEqual(response.status_code, 200, response.json())
        photo = next(item for item in response.json()["photos"] if item["id"] == str(photo_id))
        downloaded = httpx.get(photo["url"], timeout=10)
        self.assertEqual(downloaded.status_code, 200)
        self.assertTrue(downloaded.headers["content-type"].startswith("image/"))
        self.assertGreater(len(downloaded.content), 0)


if __name__ == "__main__":
    unittest.main()
