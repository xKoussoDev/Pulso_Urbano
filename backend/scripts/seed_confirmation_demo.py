"""Crea cinco reportes ficticios para probar confirmaciones desde otra sesión."""

import json
from pathlib import Path
from uuid import uuid4

import psycopg
from fastapi.testclient import TestClient

from app.config import demo_bbox, supabase_db_url
from app.main import app
from app.supabase_client import get_supabase_client


STATE = Path(__file__).resolve().parents[1] / ".confirmation_demo_seed.json"
PREFIX = "[DEMO CONFIRMACIONES]"
TARGETS = [
    ("norte", -102.29, 21.94, "bache", "Bache ficticio para probar confirmaciones en la zona norte."),
    ("oriente", -102.24, 21.88, "fuga_agua", "Fuga ficticia para probar confirmaciones en la zona oriente."),
    ("sur", -102.29, 21.83, "falta_alumbrado", "Falla ficticia de alumbrado para probar confirmaciones en la zona sur."),
    ("poniente", -102.35, 21.88, "infraestructura_danada", "Daño ficticio de infraestructura para probar confirmaciones en la zona poniente."),
]


def choose_locations(connection: psycopg.Connection) -> list[tuple]:
    west, south, east, north = demo_bbox
    anchor = connection.execute(
        """select i.neighborhood_id, n.name, n.postal_code,
                  extensions.ST_Y(i.location::extensions.geometry),
                  extensions.ST_X(i.location::extensions.geometry)
           from public.incidents i
           join public.neighborhoods n on n.id = i.neighborhood_id
           where i.municipality_id = n.municipality_id
           order by i.created_at desc limit 1"""
    ).fetchone()
    if anchor is None:
        raise RuntimeError("Falta un incidente previo para ubicar la muestra cercana")
    selected = [("cercana", *anchor, "basura",
                 "Acumulación ficticia de residuos para probar confirmaciones cerca de un reporte previo.")]
    used = [anchor[0]]
    for zone, target_lon, target_lat, category, description in TARGETS:
        row = connection.execute(
            """select n.id, n.name, n.postal_code,
                      extensions.ST_Y(p.point), extensions.ST_X(p.point)
               from public.neighborhoods n
               cross join lateral (select extensions.ST_PointOnSurface(n.boundary) as point) p
               where n.id <> all(%s)
                 and n.name <> 'NINGUNO'
                 and extensions.ST_X(p.point) between %s and %s
                 and extensions.ST_Y(p.point) between %s and %s
                 and (select count(*) from public.neighborhoods n2
                      where n2.municipality_id = n.municipality_id
                        and extensions.ST_Covers(n2.boundary, p.point)) = 1
               order by extensions.ST_Distance(p.point::extensions.geography,
                   extensions.ST_SetSRID(extensions.ST_MakePoint(%s, %s), 4326)
                       ::extensions.geography)
               limit 1""",
            (used, west, east, south, north, target_lon, target_lat),
        ).fetchone()
        if row is None:
            raise RuntimeError(f"No se encontró un polígono único para la zona {zone}")
        selected.append((zone, *row, category, description))
        used.append(row[0])
    return selected


def remove_partial(user_id: str, report_ids: list[str], incident_ids: list[str]) -> None:
    with psycopg.connect(supabase_db_url, connect_timeout=10) as connection:
        for report_id, incident_id in zip(report_ids, incident_ids):
            connection.execute("delete from public.reports where id = %s", (report_id,))
            connection.execute("delete from public.incident_status_history where incident_id = %s", (incident_id,))
            connection.execute("delete from public.priority_history where incident_id = %s", (incident_id,))
            connection.execute("delete from public.incidents where id = %s", (incident_id,))
    get_supabase_client().auth.admin.delete_user(user_id)


def main() -> None:
    if STATE.exists():
        raise RuntimeError("La muestra ya tiene manifiesto local; no se crearán duplicados")
    if not supabase_db_url:
        raise RuntimeError("Falta SUPABASE_DB_URL")
    with psycopg.connect(supabase_db_url, connect_timeout=10) as connection:
        places = choose_locations(connection)
        categories = dict(connection.execute(
            "select code, id from public.categories where active"
        ).fetchall())
    if any(category not in categories for *_, category, description in places):
        raise RuntimeError("Falta una categoría activa para la muestra")

    auth = get_supabase_client().auth.sign_in_anonymously()
    if auth.user is None or auth.session is None:
        raise RuntimeError("No se pudo crear la sesión anónima de demo")
    user_id = str(auth.user.id)
    token = auth.session.access_token
    records = []
    try:
        with TestClient(app) as client:
            for zone, neighborhood_id, name, postal_code, lat, lon, category, description in places:
                response = client.post(
                    "/api/v1/reports",
                    headers={"Authorization": f"Bearer {token}"},
                    json={"client_request_id": str(uuid4()), "category_id": str(categories[category]),
                          "description": f"{PREFIX} {description}", "duration_text": "hoy",
                          "severity": "medium", "location": {"latitude": lat, "longitude": lon},
                          "location_source": "map", "input_method": "traditional"},
                )
                if response.status_code != 201:
                    raise RuntimeError(f"La API rechazó la zona {zone}: HTTP {response.status_code}")
                result = response.json()
                records.append({"zone": zone, "neighborhood": name, "postal_code": postal_code,
                                "neighborhood_id": str(neighborhood_id), "report_id": result["id"],
                                "incident_id": result["incident_id"]})
        with psycopg.connect(supabase_db_url, connect_timeout=10) as connection:
            connection.execute(
                """update public.incidents set title = '[DEMO] ' || title
                   where id = any(%s) and title not like '[DEMO] %%'""",
                ([item["incident_id"] for item in records],),
            )
            count, zones = connection.execute(
                """select count(*), count(distinct neighborhood_id) from public.incidents
                   where id = any(%s) and status = 'reported' and description like %s""",
                ([item["incident_id"] for item in records], PREFIX + "%"),
            ).fetchone()
            if (count, zones) != (5, 5):
                raise RuntimeError("La verificación de cinco zonas distintas falló")
        STATE.write_text(json.dumps({"user_id": user_id, "records": records}, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception:
        remove_partial(user_id, [item["report_id"] for item in records],
                       [item["incident_id"] for item in records])
        raise
    print("Reportes ficticios guardados en cinco zonas distintas:")
    for item in records:
        print(f"- {item['zone']}: {item['neighborhood']} (CP {item['postal_code'] or 'sin dato'})")
    print("IDs guardados en backend/.confirmation_demo_seed.json; no contiene claves ni tokens")


if __name__ == "__main__":
    main()
