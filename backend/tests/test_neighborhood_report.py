"""Prueba opcional del alta real con puntos de cobertura única, ambigua y nula."""

import os
import unittest
from uuid import UUID, uuid4

import psycopg
from fastapi.testclient import TestClient

from app.auth import User, require_citizen
from app.config import demo_bbox
from app.main import app
from app.report_routes import database_url


@unittest.skipUnless(os.getenv("RUN_NEIGHBORHOOD_INTEGRATION") == "1", "Requiere Supabase de demo")
class NeighborhoodReportTests(unittest.TestCase):
    def test_new_reports_use_only_unique_spatial_match(self):
        west, south, east, north = demo_bbox
        with psycopg.connect(database_url(), connect_timeout=10) as connection:
            user = connection.execute(
                """select r.reporter_id from public.reports r
                   join auth.users u on u.id = r.reporter_id
                   where u.is_anonymous order by r.created_at desc limit 1"""
            ).fetchone()
            category = connection.execute(
                "select id from public.categories where code = 'fuga_agua' and active"
            ).fetchone()
            unique = connection.execute(
                """with points as (
                       select extensions.ST_PointOnSurface(boundary) as point
                       from public.neighborhoods
                   )
                   select extensions.ST_Y(p.point), extensions.ST_X(p.point),
                          min(n.id::text)::uuid
                   from points p join public.neighborhoods n
                     on extensions.ST_Covers(n.boundary, p.point)
                   where extensions.ST_X(p.point) between %s and %s
                     and extensions.ST_Y(p.point) between %s and %s
                   group by p.point having count(*) = 1 limit 1""",
                (west, east, south, north),
            ).fetchone()
            overlap = connection.execute(
                """with points as (
                       select extensions.ST_PointOnSurface(extensions.ST_Intersection(
                           a.boundary, b.boundary)) as point
                       from public.neighborhoods a join public.neighborhoods b
                         on a.id < b.id and a.boundary && b.boundary
                        and extensions.ST_Area(extensions.ST_Intersection(a.boundary, b.boundary)) > 0
                   )
                   select extensions.ST_Y(point), extensions.ST_X(point)
                   from points where extensions.ST_X(point) between %s and %s
                     and extensions.ST_Y(point) between %s and %s limit 1""",
                (west, east, south, north),
            ).fetchone()
            outside = connection.execute(
                """select lat, lon from
                       (select %s + (%s - %s) * y / 20.0 as lat,
                               %s + (%s - %s) * x / 20.0 as lon
                        from generate_series(1, 19) x cross join generate_series(1, 19) y) p
                   where not exists (
                       select 1 from public.neighborhoods n
                       where extensions.ST_Covers(n.boundary,
                           extensions.ST_SetSRID(extensions.ST_MakePoint(p.lon, p.lat), 4326)))
                   limit 1""",
                (south, north, south, west, east, west),
            ).fetchone()
        self.assertIsNotNone(user)
        self.assertIsNotNone(category)
        self.assertIsNotNone(unique)
        self.assertIsNotNone(overlap)
        self.assertIsNotNone(outside)

        app.dependency_overrides[require_citizen] = lambda: User(user[0], True)
        created = []
        try:
            with TestClient(app) as client:
                for index, (lat, lon, expected) in enumerate((
                    (unique[0], unique[1], unique[2]),
                    (overlap[0], overlap[1], None),
                    (outside[0], outside[1], None),
                )):
                    payload = {
                        "client_request_id": str(uuid4()),
                        "category_id": str(category[0]),
                        "description": f"Fuga de agua ficticia para prueba espacial {index}",
                        "duration_text": "hoy",
                        "severity": "medium",
                        "location": {"latitude": float(lat), "longitude": float(lon)},
                        "location_source": "gps",
                        "input_method": "traditional",
                    }
                    response = client.post("/api/v1/reports", json=payload)
                    self.assertEqual(response.status_code, 201, response.json())
                    result = response.json()
                    created.append((UUID(result["id"]), UUID(result["incident_id"])))
                    with psycopg.connect(database_url(), connect_timeout=10) as connection:
                        stored = connection.execute(
                            "select neighborhood_id from public.incidents where id = %s",
                            (created[-1][1],),
                        ).fetchone()
                    self.assertEqual(stored[0], expected)
                    if index == 0:
                        retry = client.post("/api/v1/reports", json=payload)
                        self.assertEqual(retry.status_code, 200, retry.json())
                        self.assertEqual(retry.json()["id"], result["id"])
        finally:
            app.dependency_overrides.clear()
            with psycopg.connect(database_url(), connect_timeout=10) as connection:
                for report_id, incident_id in created:
                    connection.execute("delete from public.reports where id = %s", (report_id,))
                    connection.execute("delete from public.incident_status_history where incident_id = %s", (incident_id,))
                    connection.execute("delete from public.priority_history where incident_id = %s", (incident_id,))
                    connection.execute("delete from public.incidents where id = %s", (incident_id,))


if __name__ == "__main__":
    unittest.main()
