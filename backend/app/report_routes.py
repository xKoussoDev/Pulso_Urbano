import re
from typing import Literal
from uuid import UUID

import psycopg
from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field, field_validator
from psycopg.types.json import Jsonb

from .auth import User, error, get_current_user, get_staff_municipality, require_citizen
from .config import demo_bbox, priority_weight_g, priority_weight_t, supabase_db_url


router = APIRouter(prefix="/api/v1")
SEVERITY_SCORE = {"low": 25, "medium": 50, "high": 75, "critical": 100}
EMAIL = re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b")
PHONE = re.compile(r"(?<!\d)(?:\+?52[ -]?)?(?:\d[ -]?){10}(?!\d)")


class Location(BaseModel):
    model_config = ConfigDict(extra="forbid")
    latitude: float = Field(ge=-90, le=90, allow_inf_nan=False)
    longitude: float = Field(ge=-180, le=180, allow_inf_nan=False)


class ReportInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    client_request_id: UUID
    category_id: UUID
    description: str = Field(min_length=10, max_length=1000)
    duration_text: str | None = Field(default=None, max_length=100)
    severity: Literal["low", "medium", "high", "critical"]
    location: Location
    location_source: Literal["gps", "map"]
    input_method: Literal["traditional", "voice"]

    @field_validator("description", "duration_text", mode="before")
    @classmethod
    def clean_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if EMAIL.search(value) or PHONE.search(value):
            raise ValueError("No incluyas correo ni teléfono personal")
        return value


def database_url() -> str:
    if not supabase_db_url:
        raise error(503, "DEPENDENCY_UNAVAILABLE", "Base de datos no configurada")
    return supabase_db_url


@router.get("/categories")
def categories(user: User = Depends(get_current_user)) -> dict:
    if not user.is_anonymous and get_staff_municipality(user) is None:
        raise error(403, "FORBIDDEN", "Cuenta sin acceso")
    try:
        with psycopg.connect(database_url(), connect_timeout=5) as conn:
            rows = conn.execute(
                "select id, code, name, default_severity from public.categories where active order by name"
            ).fetchall()
        return {"items": [{"id": str(i), "code": c, "name": n, "default_severity": s} for i, c, n, s in rows]}
    except psycopg.Error as exc:
        raise error(503, "DEPENDENCY_UNAVAILABLE", "Base de datos no disponible") from exc


@router.post("/reports", status_code=201)
def create_report(body: ReportInput, user: User = Depends(require_citizen)) -> dict:
    # Caja aproximada para la demo; no sustituye el polígono oficial del municipio.
    lat, lon = body.location.latitude, body.location.longitude
    west, south, east, north = demo_bbox
    if not (south <= lat <= north and west <= lon <= east):
        raise error(422, "VALIDATION_ERROR", "Ubicación fuera del área aproximada de la demo")
    try:
        with psycopg.connect(database_url(), connect_timeout=5) as conn:
            # Serializa reintentos concurrentes del mismo usuario y solicitud.
            conn.execute("select pg_advisory_xact_lock(hashtextextended(%s, 0))", (f"{user.id}:{body.client_request_id}",))
            previous = conn.execute(
                """select r.id, r.incident_id, r.created_at, r.category_id, r.description,
                          r.duration_text, r.severity_selected, r.location_source, r.input_method,
                          extensions.ST_Y(r.location::extensions.geometry),
                          extensions.ST_X(r.location::extensions.geometry)
                   from public.reports r where r.reporter_id=%s and r.client_request_id=%s""",
                (user.id, body.client_request_id),
            ).fetchone()
            if previous:
                same = (
                    previous[3] == body.category_id and previous[4] == body.description
                    and previous[5] == body.duration_text and previous[6] == body.severity
                    and previous[7] == body.location_source and previous[8] == body.input_method
                    and abs(previous[9] - lat) < 0.0000001 and abs(previous[10] - lon) < 0.0000001
                )
                if not same:
                    raise error(409, "CONFLICT", "La clave de solicitud ya se utilizó con otros datos")
                from fastapi.responses import JSONResponse
                return JSONResponse(status_code=200, content={"id": str(previous[0]), "incident_id": str(previous[1]), "status": "reported", "created_at": previous[2].isoformat()})

            municipality = conn.execute(
                "select id from public.municipalities where code='aguascalientes_capital' and active"
            ).fetchone()
            if not municipality:
                raise error(503, "DEPENDENCY_UNAVAILABLE", "Municipio de la demo no disponible")
            category = conn.execute(
                "select name from public.categories where id=%s and active", (body.category_id,)
            ).fetchone()
            if not category:
                raise error(422, "VALIDATION_ERROR", "Categoría inexistente o inactiva")

            neighborhood = conn.execute(
                """select min(n.id::text)::uuid from public.neighborhoods n
                   where n.municipality_id = %s
                     and extensions.ST_Covers(n.boundary,
                         extensions.ST_SetSRID(extensions.ST_MakePoint(%s, %s), 4326))
                   having count(*) = 1""",
                (municipality[0], lon, lat),
            ).fetchone()
            neighborhood_id = neighborhood[0] if neighborhood else None
            point = "extensions.ST_SetSRID(extensions.ST_MakePoint(%s, %s), 4326)::extensions.geography"
            incident = conn.execute(
                f"""insert into public.incidents
                    (municipality_id, category_id, title, description, location, severity, neighborhood_id)
                    values (%s, %s, %s, %s, {point}, %s, %s) returning id""",
                (municipality[0], body.category_id, category[0], body.description,
                 lon, lat, body.severity, neighborhood_id),
            ).fetchone()[0]
            report = conn.execute(
                f"""insert into public.reports
                    (reporter_id, client_request_id, incident_id, municipality_id, category_id,
                     description, duration_text, severity_selected, location, location_source, input_method)
                    values (%s, %s, %s, %s, %s, %s, %s, %s, {point}, %s, %s)
                    returning id, created_at""",
                (user.id, body.client_request_id, incident, municipality[0], body.category_id,
                 body.description, body.duration_text, body.severity, lon, lat,
                 body.location_source, body.input_method),
            ).fetchone()
            conn.execute(
                "insert into public.incident_status_history (incident_id, new_status) values (%s, 'reported')",
                (incident,),
            )
            gravity = SEVERITY_SCORE[body.severity]
            conn.execute(
                """insert into public.priority_history
                   (incident_id, new_score, calculation_version, factors, weights)
                   values (%s, %s, 1, %s, %s)""",
                (incident, priority_weight_g * gravity, Jsonb({"G": gravity, "T": 0}), Jsonb({"G": priority_weight_g, "T": priority_weight_t})),
            )
        return {"id": str(report[0]), "incident_id": str(incident), "status": "reported", "created_at": report[1].isoformat()}
    except psycopg.Error as exc:
        raise error(503, "DEPENDENCY_UNAVAILABLE", "Base de datos no disponible") from exc
