"""Prueba opcional del endpoint con sesiones y reportes ficticios existentes."""

import os
import unittest
from uuid import UUID, uuid4

import psycopg
from fastapi.testclient import TestClient

from app.auth import User, get_current_user, require_staff
from app.config import demo_bbox
from app.main import app
from app.report_routes import database_url


@unittest.skipUnless(os.getenv("RUN_CONFIRMATION_INTEGRATION") == "1", "Requiere Supabase de demo")
class ConfirmationTests(unittest.TestCase):
    def test_staff_detail_shows_only_confirmation_total(self):
        with psycopg.connect(database_url(), connect_timeout=10) as connection:
            row = connection.execute(
                """select i.id, i.municipality_id, count(ic.id)
                   from public.incidents i
                   join public.incident_confirmations ic on ic.incident_id = i.id
                   group by i.id having count(ic.id) > 0 limit 1"""
            ).fetchone()
        if row is None:
            self.skipTest("No hay una confirmación ficticia guardada")
        incident_id, municipality_id, count = row
        app.dependency_overrides[require_staff] = lambda: (User(UUID(int=2), False), municipality_id)
        try:
            with TestClient(app) as client:
                detail = client.get(f"/api/v1/incidents/{incident_id}")
                self.assertEqual(detail.status_code, 200, detail.json())
                self.assertEqual(detail.json()["confirmations_count"], count)
                self.assertNotIn("user_id", detail.json())
                self.assertNotIn("reporter_id", detail.json())
                self.assertNotIn("confirmations", detail.json())
        finally:
            app.dependency_overrides.clear()

    def test_independent_confirmation_is_unique_and_private(self):
        with psycopg.connect(database_url(), connect_timeout=10) as connection:
            row = connection.execute(
                """select i.id, r.reporter_id,
                          (select r2.reporter_id from public.reports r2
                           join auth.users u2 on u2.id = r2.reporter_id
                           where u2.is_anonymous and r2.reporter_id <> r.reporter_id
                           limit 1) as other_user,
                          extensions.ST_Y(i.location::extensions.geometry),
                          extensions.ST_X(i.location::extensions.geometry)
                   from public.incidents i join public.reports r on r.incident_id = i.id
                   join auth.users u on u.id = r.reporter_id
                   where i.status not in ('resolved', 'discarded') and u.is_anonymous
                   limit 1"""
            ).fetchone()
            closed = connection.execute(
                "select id from public.incidents where status in ('resolved', 'discarded') limit 1"
            ).fetchone()
            self.assertIsNotNone(row)
            self.assertIsNotNone(row[2])
            self.assertIsNotNone(closed)
            incident_id, reporter_id, other_user, latitude, longitude = row
            before = connection.execute(
                "select count(*) from public.incident_confirmations where incident_id = %s",
                (incident_id,),
            ).fetchone()[0]
            self.assertTrue(connection.execute(
                "select relrowsecurity from pg_class where oid = 'public.incident_confirmations'::regclass"
            ).fetchone()[0])
            self.assertEqual(connection.execute(
                """select has_table_privilege('anon', 'public.incident_confirmations', 'SELECT'),
                          has_table_privilege('authenticated', 'public.incident_confirmations', 'INSERT')"""
            ).fetchone(), (False, False))

        try:
            with TestClient(app) as client:
                route = f"/api/v1/incidents/{incident_id}/confirmations"
                location = {"latitude": latitude, "longitude": longitude}
                params = {"latitude": latitude, "longitude": longitude}
                self.assertEqual(client.post(route, json=location).status_code, 401)
                self.assertEqual(client.get("/api/v1/incidents/nearby", params=params).status_code, 401)
                app.dependency_overrides[get_current_user] = lambda: User(UUID(int=2), False)
                self.assertEqual(client.post(route, json=location).status_code, 403)
                app.dependency_overrides[get_current_user] = lambda: User(reporter_id, True)
                self.assertEqual(client.post(route, json=location).status_code, 409)
                own_list = client.get("/api/v1/incidents/nearby", params=params)
                self.assertEqual(own_list.status_code, 200)
                self.assertNotIn(str(incident_id), [item["id"] for item in own_list.json()["items"]])
                app.dependency_overrides[get_current_user] = lambda: User(other_user, True)
                nearby = client.get("/api/v1/incidents/nearby", params=params)
                self.assertEqual(nearby.status_code, 200, nearby.json())
                item = next(item for item in nearby.json()["items"] if item["id"] == str(incident_id))
                self.assertEqual(item["confirmations_count"], before)
                self.assertFalse(item["confirmed_by_me"])
                self.assertNotIn("location", item)
                self.assertNotIn("description", item)
                self.assertNotIn("user_id", item)
                self.assertEqual(client.get("/api/v1/incidents/nearby", params={"latitude": 0, "longitude": 0}).status_code, 422)
                self.assertEqual(client.post(f"/api/v1/incidents/{closed[0]}/confirmations", json=location).status_code, 409)
                self.assertEqual(client.post(f"/api/v1/incidents/{uuid4()}/confirmations", json=location).status_code, 404)
                self.assertEqual(client.post("/api/v1/incidents/bad/confirmations", json=location).status_code, 422)
                north = demo_bbox[3]
                far_location = {"latitude": latitude + .02 if latitude + .02 < north else latitude - .02,
                                "longitude": longitude}
                self.assertEqual(client.post(route, json=far_location).status_code, 422)
                first = client.post(route, json=location)
                self.assertEqual(first.status_code, 201, first.json())
                self.assertEqual(first.json()["confirmations_count"], before + 1)
                self.assertNotIn("user_id", first.json())
                repeated = client.post(route, json=location)
                self.assertEqual(repeated.status_code, 200, repeated.json())
                self.assertEqual(repeated.json()["confirmations_count"], before + 1)
                confirmed_list = client.get("/api/v1/incidents/nearby", params=params)
                confirmed = next(item for item in confirmed_list.json()["items"] if item["id"] == str(incident_id))
                self.assertTrue(confirmed["confirmed_by_me"])
        finally:
            app.dependency_overrides.clear()
            with psycopg.connect(database_url(), connect_timeout=10) as connection:
                connection.execute(
                    "delete from public.incident_confirmations where incident_id = %s and user_id = %s",
                    (incident_id, other_user),
                )
                remaining = connection.execute(
                    "select count(*) from public.incident_confirmations where incident_id = %s",
                    (incident_id,),
                ).fetchone()[0]
                self.assertEqual(remaining, before)


if __name__ == "__main__":
    unittest.main()
