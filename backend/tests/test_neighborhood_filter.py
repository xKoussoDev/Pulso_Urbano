"""Prueba opcional del catálogo y filtro con la base de datos de la demo."""

import os
import unittest
from uuid import UUID

import psycopg
from fastapi.testclient import TestClient

from app.auth import User, require_staff
from app.main import app
from app.report_routes import database_url


@unittest.skipUnless(os.getenv("RUN_NEIGHBORHOOD_INTEGRATION") == "1", "Requiere Supabase de demo")
class NeighborhoodFilterTests(unittest.TestCase):
    def test_catalog_and_list_map_filters(self):
        with psycopg.connect(database_url(), connect_timeout=10) as connection:
            row = connection.execute(
                """select id, municipality_id, neighborhood_id,
                          extensions.ST_Y(location::extensions.geometry),
                          extensions.ST_X(location::extensions.geometry), status
                   from public.incidents where neighborhood_id is not null
                   order by (status in ('resolved', 'discarded')) desc limit 1"""
            ).fetchone()
            self.assertIsNotNone(row)
            incident_id, municipality_id, neighborhood_id, lat, lon, status = row
            active_count = connection.execute(
                """select count(*) from public.incidents
                   where neighborhood_id = %s and status not in ('resolved', 'discarded')""",
                (neighborhood_id,),
            ).fetchone()[0]
            other = connection.execute(
                "select id from public.neighborhoods where municipality_id = %s and id <> %s limit 1",
                (municipality_id, neighborhood_id),
            ).fetchone()[0]
        scope = "closed" if status in ("resolved", "discarded") else "active"
        with TestClient(app) as client:
            self.assertEqual(client.get("/api/v1/neighborhoods").status_code, 401)
        app.dependency_overrides[require_staff] = lambda: (User(UUID(int=2), False), municipality_id)
        try:
            with TestClient(app) as client:
                catalog = client.get("/api/v1/neighborhoods")
                self.assertEqual(catalog.status_code, 200, catalog.json())
                self.assertEqual(len(catalog.json()["items"]), 1020)
                self.assertIn(str(neighborhood_id), {item["id"] for item in catalog.json()["items"]})
                selected_area = next(item for item in catalog.json()["items"]
                                     if item["id"] == str(neighborhood_id))
                self.assertEqual(selected_area["incidents_count"], active_count)
                self.assertTrue(any(item["postal_code"] for item in catalog.json()["items"]))
                self.assertTrue(any(item["postal_code"] is None for item in catalog.json()["items"]))
                self.assertNotIn("boundary", str(catalog.json()))
                params = {"scope": scope, "neighborhood_id": str(neighborhood_id)}
                listing = client.get("/api/v1/incidents", params=params)
                self.assertEqual(listing.status_code, 200, listing.json())
                self.assertIn(str(incident_id), [item["id"] for item in listing.json()["items"]])
                params["neighborhood_id"] = str(other)
                other_list = client.get("/api/v1/incidents", params=params)
                self.assertEqual(other_list.status_code, 200, other_list.json())
                self.assertNotIn(str(incident_id), [item["id"] for item in other_list.json()["items"]])
                params.update({"neighborhood_id": str(neighborhood_id),
                               "bbox": f"{lon - .01},{lat - .01},{lon + .01},{lat + .01}"})
                mapped = client.get("/api/v1/incidents/map", params=params)
                self.assertEqual(mapped.status_code, 200, mapped.json())
                self.assertIn(str(incident_id), [item["id"] for item in mapped.json()["items"]])
                params["neighborhood_id"] = str(other)
                other_map = client.get("/api/v1/incidents/map", params=params)
                self.assertEqual(other_map.status_code, 200, other_map.json())
                self.assertNotIn(str(incident_id), [item["id"] for item in other_map.json()["items"]])
                self.assertEqual(client.get("/api/v1/incidents?neighborhood_id=bad").status_code, 422)
        finally:
            app.dependency_overrides.clear()


if __name__ == "__main__":
    unittest.main()
