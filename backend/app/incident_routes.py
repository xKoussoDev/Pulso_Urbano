import base64
import json
import math
from datetime import datetime
from typing import Literal
from uuid import UUID

import psycopg
import httpx
from fastapi import APIRouter, Depends, Query, Response
from pydantic import BaseModel, ConfigDict, Field, field_validator
from storage3.exceptions import StorageException

from .auth import User, error, require_citizen, require_staff
from .config import demo_bbox, map_max_bbox_span, priority_weight_g, priority_weight_t, supabase_db_url
from .report_routes import EMAIL, PHONE, Location
from .supabase_client import get_supabase_client


router = APIRouter(prefix="/api/v1")
Severity = Literal["low", "medium", "high", "critical"]
Status = Literal["reported", "in_review", "confirmed", "in_progress", "resolved", "discarded"]
SCORE_SQL = """round((%s * case i.severity when 'low' then 25 when 'medium' then 50
              when 'high' then 75 else 100 end + %s * least(100, greatest(0,
              extract(epoch from (coalesce(i.resolved_at, case when i.status='discarded' then i.updated_at end, now()) - i.opened_at)) / 1209600 * 100)))::numeric, 2)"""
LEVEL_SQL = "case when priority_score >= 75 then 'critical' when priority_score >= 50 then 'high' when priority_score >= 25 then 'medium' else 'low' end"
TIME_SQL = "least(100, greatest(0, extract(epoch from (coalesce(i.resolved_at, case when i.status='discarded' then i.updated_at end, now()) - i.opened_at)) / 1209600 * 100))"
GRAVITY = {"low": 25, "medium": 50, "high": 75, "critical": 100}
TRANSITIONS = {
    "reported": {"in_review", "discarded"},
    "in_review": {"confirmed", "discarded"},
    "confirmed": {"in_progress", "discarded"},
    "in_progress": {"resolved", "in_review"},
    "resolved": set(),
    "discarded": set(),
}
NEARBY_RADIUS_METERS = 1000


class StatusInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Status
    notes: str | None = Field(default=None, max_length=500)
    expected_version: int = Field(ge=1)

    @field_validator("notes", mode="before")
    @classmethod
    def clean_notes(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if EMAIL.search(value) or PHONE.search(value):
            raise ValueError("No incluyas correo ni teléfono personal")
        return value or None


def read_cursor(value: str | None) -> tuple[datetime, UUID] | None:
    if value is None:
        return None
    try:
        timestamp, incident_id = json.loads(base64.urlsafe_b64decode(value + "=" * (-len(value) % 4)))
        date = datetime.fromisoformat(timestamp)
        if date.tzinfo is None:
            raise ValueError
        return date, UUID(incident_id)
    except (ValueError, TypeError, UnicodeDecodeError, json.JSONDecodeError):
        raise error(422, "VALIDATION_ERROR", "Cursor inválido") from None


def make_cursor(date: datetime, incident_id: UUID) -> str:
    raw = json.dumps([date.isoformat(), str(incident_id)]).encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def read_bbox(value: str) -> tuple[float, float, float, float]:
    try:
        west, south, east, north = (float(part) for part in value.split(","))
        valid = (all(math.isfinite(x) for x in (west, south, east, north))
                 and -180 <= west < east <= 180 and -90 <= south < north <= 90)
        if not valid:
            raise ValueError
        if east - west > map_max_bbox_span or north - south > map_max_bbox_span:
            raise error(422, "VALIDATION_ERROR", "Acerca el mapa para consultar un área menor")
        return west, south, east, north
    except ValueError:
        raise error(422, "VALIDATION_ERROR", "bbox debe contener oeste,sur,este,norte") from None


def check_demo_location(latitude: float, longitude: float) -> None:
    west, south, east, north = demo_bbox
    if not (math.isfinite(latitude) and math.isfinite(longitude)
            and south <= latitude <= north and west <= longitude <= east):
        raise error(422, "VALIDATION_ERROR", "Ubicación fuera del área de la demo")


@router.get("/neighborhoods")
def list_neighborhoods(staff: tuple[User, UUID] = Depends(require_staff)) -> dict:
    if not supabase_db_url:
        raise error(503, "DEPENDENCY_UNAVAILABLE", "Base de datos no configurada")
    try:
        with psycopg.connect(supabase_db_url, connect_timeout=5) as conn:
            rows = conn.execute(
                """select n.id, n.name, n.settlement_type, n.source_key, n.postal_code,
                          count(i.id) as incidents_count
                   from public.neighborhoods n
                   left join public.incidents i on i.neighborhood_id = n.id
                   where n.municipality_id = %s
                   group by n.id
                   order by incidents_count desc, n.name, n.settlement_type, n.source_key""",
                (staff[1],),
            ).fetchall()
    except psycopg.Error as exc:
        raise error(503, "DEPENDENCY_UNAVAILABLE", "Base de datos no disponible") from exc
    return {"items": [{"id": str(id_), "name": name, "settlement_type": kind,
                       "source_key": key, "postal_code": postal_code,
                       "incidents_count": count}
                      for id_, name, kind, key, postal_code, count in rows]}


@router.get("/incidents/nearby")
def nearby_incidents(
    response: Response,
    latitude: float = Query(ge=-90, le=90),
    longitude: float = Query(ge=-180, le=180),
    user: User = Depends(require_citizen),
) -> dict:
    check_demo_location(latitude, longitude)
    if not supabase_db_url:
        raise error(503, "DEPENDENCY_UNAVAILABLE", "Base de datos no configurada")
    try:
        with psycopg.connect(supabase_db_url, connect_timeout=5) as conn:
            rows = conn.execute(
                """with search as (
                       select extensions.ST_SetSRID(extensions.ST_MakePoint(%s, %s), 4326)
                           ::extensions.geography as point
                   )
                   select i.id, c.name,
                          (round(extensions.ST_Distance(i.location, s.point) / 50.0) * 50)::integer,
                          i.created_at::date,
                          (select count(*) from public.incident_confirmations ic
                           where ic.incident_id = i.id),
                          exists(select 1 from public.incident_confirmations ic
                                 where ic.incident_id = i.id and ic.user_id = %s)
                   from public.incidents i
                   join public.categories c on c.id = i.category_id
                   join public.municipalities m on m.id = i.municipality_id
                   cross join search s
                   where m.code = 'aguascalientes_capital' and m.active
                     and i.status not in ('resolved', 'discarded')
                     and extensions.ST_DWithin(i.location, s.point, %s)
                     and not exists(select 1 from public.reports r
                                    where r.incident_id = i.id and r.reporter_id = %s)
                   order by extensions.ST_Distance(i.location, s.point), i.created_at desc
                   limit 10""",
                (longitude, latitude, user.id, NEARBY_RADIUS_METERS, user.id),
            ).fetchall()
    except psycopg.Error as exc:
        raise error(503, "DEPENDENCY_UNAVAILABLE", "Base de datos no disponible") from exc
    response.headers["Cache-Control"] = "no-store"
    return {"items": [{"id": str(id_), "category_name": category,
                       "distance_m_approx": distance, "reported_on": date.isoformat(),
                       "confirmations_count": count, "confirmed_by_me": confirmed}
                      for id_, category, distance, date, count, confirmed in rows]}


@router.get("/incidents")
def list_incidents(
    staff: tuple[User, UUID] = Depends(require_staff),
    category_id: UUID | None = None,
    neighborhood_id: UUID | None = None,
    severity: Severity | None = None,
    priority_level: Severity | None = None,
    status: Status | None = None,
    scope: Literal["active", "closed"] | None = None,
    from_date: datetime | None = Query(default=None, alias="from"),
    to_date: datetime | None = Query(default=None, alias="to"),
    limit: int = Query(default=20, ge=1, le=50),
    cursor: str | None = None,
) -> dict:
    if from_date and from_date.tzinfo is None or to_date and to_date.tzinfo is None:
        raise error(422, "VALIDATION_ERROR", "Las fechas necesitan zona horaria")
    if from_date and to_date and from_date > to_date:
        raise error(422, "VALIDATION_ERROR", "El inicio debe ser anterior al fin")
    position = read_cursor(cursor)
    if not supabase_db_url:
        raise error(503, "DEPENDENCY_UNAVAILABLE", "Base de datos no configurada")

    filters = ["i.municipality_id = %s"]
    values: list = [staff[1]]
    if scope == "active":
        filters.append("i.status not in ('resolved', 'discarded')")
    elif scope == "closed":
        filters.append("i.status in ('resolved', 'discarded')")
    for column, value in [("i.category_id", category_id), ("i.neighborhood_id", neighborhood_id),
                          ("i.severity", severity), ("i.status", status)]:
        if value is not None:
            filters.append(f"{column} = %s")
            values.append(value)
    if from_date:
        filters.append("i.created_at >= %s")
        values.append(from_date)
    if to_date:
        filters.append("i.created_at <= %s")
        values.append(to_date)
    if position:
        filters.append("(i.created_at, i.id) < (%s, %s)")
        values.extend(position)

    query = f"""with ranked as (
        select i.id, i.title, i.severity, i.status, i.created_at,
               c.code as category_code, c.name as category_name,
               (select count(*) from public.reports r where r.incident_id = i.id) as reports_count,
               {SCORE_SQL} as priority_score
        from public.incidents i join public.categories c on c.id = i.category_id
        where {' and '.join(filters)}
    ) select * from ranked
      {'where ' + LEVEL_SQL + ' = %s' if priority_level else ''}
      order by created_at desc, id desc limit %s"""
    params = [priority_weight_g, priority_weight_t, *values]
    if priority_level:
        params.append(priority_level)
    params.append(limit + 1)
    try:
        with psycopg.connect(supabase_db_url, connect_timeout=5) as conn:
            rows = conn.execute(query, params).fetchall()
    except psycopg.Error as exc:
        raise error(503, "DEPENDENCY_UNAVAILABLE", "Base de datos no disponible") from exc

    visible = rows[:limit]
    items = []
    for incident_id, title, sev, state, created_at, code, name, count, score_value in visible:
        score_number = float(score_value)
        level = "critical" if score_number >= 75 else "high" if score_number >= 50 else "medium" if score_number >= 25 else "low"
        items.append({"id": str(incident_id), "category": {"code": code, "name": name}, "title": title,
                      "severity": sev, "status": state, "reports_count": count,
                      "priority_score": score_number, "priority_level": level,
                      "created_at": created_at.isoformat()})
    next_cursor = make_cursor(visible[-1][4], visible[-1][0]) if len(rows) > limit else None
    return {"items": items, "next_cursor": next_cursor}


@router.get("/incidents/map")
def map_incidents(
    bbox: str,
    staff: tuple[User, UUID] = Depends(require_staff),
    category_id: UUID | None = None,
    neighborhood_id: UUID | None = None,
    severity: Severity | None = None,
    priority_level: Severity | None = None,
    status: Status | None = None,
    scope: Literal["active", "closed"] | None = None,
    from_date: datetime | None = Query(default=None, alias="from"),
    to_date: datetime | None = Query(default=None, alias="to"),
) -> dict:
    west, south, east, north = read_bbox(bbox)
    if from_date and from_date.tzinfo is None or to_date and to_date.tzinfo is None:
        raise error(422, "VALIDATION_ERROR", "Las fechas necesitan zona horaria")
    if from_date and to_date and from_date > to_date:
        raise error(422, "VALIDATION_ERROR", "El inicio debe ser anterior al fin")
    if not supabase_db_url:
        raise error(503, "DEPENDENCY_UNAVAILABLE", "Base de datos no configurada")

    filters = ["i.municipality_id = %s", "extensions.ST_Intersects(i.location, extensions.ST_MakeEnvelope(%s, %s, %s, %s, 4326)::extensions.geography)"]
    values: list = [staff[1], west, south, east, north]
    if scope == "active":
        filters.append("i.status not in ('resolved', 'discarded')")
    elif scope == "closed":
        filters.append("i.status in ('resolved', 'discarded')")
    for column, value in [("i.category_id", category_id), ("i.neighborhood_id", neighborhood_id),
                          ("i.severity", severity), ("i.status", status)]:
        if value is not None:
            filters.append(f"{column} = %s")
            values.append(value)
    if from_date:
        filters.append("i.created_at >= %s")
        values.append(from_date)
    if to_date:
        filters.append("i.created_at <= %s")
        values.append(to_date)

    query = f"""with ranked as (
        select i.id, i.status, i.created_at, c.code as category_code,
               extensions.ST_Y(i.location::extensions.geometry) as latitude,
               extensions.ST_X(i.location::extensions.geometry) as longitude,
               {SCORE_SQL} as priority_score
        from public.incidents i join public.categories c on c.id = i.category_id
        where {' and '.join(filters)}
    ) select id, status, category_code, latitude, longitude, priority_score from ranked
      {'where ' + LEVEL_SQL + ' = %s' if priority_level else ''}
      order by created_at desc, id desc limit 501"""
    params = [priority_weight_g, priority_weight_t, *values]
    if priority_level:
        params.append(priority_level)
    try:
        with psycopg.connect(supabase_db_url, connect_timeout=5) as conn:
            rows = conn.execute(query, params).fetchall()
    except psycopg.Error as exc:
        raise error(503, "DEPENDENCY_UNAVAILABLE", "Base de datos no disponible") from exc

    items = []
    for incident_id, state, code, lat, lon, score_value in rows[:500]:
        score = float(score_value)
        level = "critical" if score >= 75 else "high" if score >= 50 else "medium" if score >= 25 else "low"
        items.append({"id": str(incident_id), "latitude": lat, "longitude": lon,
                      "category_code": code, "priority_score": score, "priority_level": level, "status": state})
    return {"items": items, "truncated": len(rows) > 500}


@router.post("/incidents/{incident_id}/confirmations")
def confirm_incident(incident_id: UUID, location: Location, user: User = Depends(require_citizen)) -> Response:
    check_demo_location(location.latitude, location.longitude)
    if not supabase_db_url:
        raise error(503, "DEPENDENCY_UNAVAILABLE", "Base de datos no configurada")
    try:
        with psycopg.connect(supabase_db_url, connect_timeout=5) as conn:
            incident = conn.execute(
                """select i.status,
                          extensions.ST_DWithin(i.location,
                              extensions.ST_SetSRID(extensions.ST_MakePoint(%s, %s), 4326)
                                  ::extensions.geography, %s)
                   from public.incidents i
                   join public.municipalities m on m.id = i.municipality_id
                   where i.id = %s and m.code = 'aguascalientes_capital' and m.active
                   for share of i""",
                (location.longitude, location.latitude, NEARBY_RADIUS_METERS, incident_id),
            ).fetchone()
            if incident is None:
                raise error(404, "NOT_FOUND", "Incidente no encontrado")
            if incident[0] in ("resolved", "discarded"):
                raise error(409, "CONFLICT", "El incidente ya está finalizado")
            if not incident[1]:
                raise error(422, "VALIDATION_ERROR", "Debes estar cerca del incidente para confirmarlo")
            own_report = conn.execute(
                "select 1 from public.reports where incident_id = %s and reporter_id = %s limit 1",
                (incident_id, user.id),
            ).fetchone()
            if own_report:
                raise error(409, "CONFLICT", "Tu reporte ya cuenta para este incidente")
            inserted = conn.execute(
                """insert into public.incident_confirmations (incident_id, user_id)
                   values (%s, %s) on conflict (incident_id, user_id) do nothing returning id""",
                (incident_id, user.id),
            ).fetchone()
            count = conn.execute(
                "select count(*) from public.incident_confirmations where incident_id = %s",
                (incident_id,),
            ).fetchone()[0]
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=201 if inserted else 200,
            content={"incident_id": str(incident_id), "confirmed": True,
                     "confirmations_count": count},
            headers={"Cache-Control": "no-store"},
        )
    except psycopg.Error as exc:
        raise error(503, "DEPENDENCY_UNAVAILABLE", "Base de datos no disponible") from exc


@router.get("/incidents/{incident_id}")
def get_incident(incident_id: UUID, response: Response, staff: tuple[User, UUID] = Depends(require_staff)) -> dict:
    if not supabase_db_url:
        raise error(503, "DEPENDENCY_UNAVAILABLE", "Base de datos no configurada")
    query = f"""select i.id, c.code, c.name, i.title, i.description,
               extensions.ST_Y(i.location::extensions.geometry),
               extensions.ST_X(i.location::extensions.geometry),
               i.severity, i.status, i.row_version,
               (select count(*) from public.reports r where r.incident_id=i.id),
               (select count(*) from public.incident_confirmations ic where ic.incident_id=i.id),
               i.priority_version, {SCORE_SQL}, {TIME_SQL}, now(), i.created_at, i.updated_at
        from public.incidents i join public.categories c on c.id=i.category_id
        where i.id=%s and i.municipality_id=%s"""
    try:
        with psycopg.connect(supabase_db_url, connect_timeout=5) as conn:
            row = conn.execute(query, (priority_weight_g, priority_weight_t, incident_id, staff[1])).fetchone()
            if not row:
                raise error(404, "NOT_FOUND", "Incidente no encontrado")
            history = conn.execute(
                """select h.previous_status, h.new_status, h.notes, h.created_at,
                          h.changed_by, u.email
                   from public.incident_status_history h
                   left join auth.users u on u.id=h.changed_by
                   where h.incident_id=%s
                   order by h.created_at, h.id""", (incident_id,),
            ).fetchall()
            photo_rows = conn.execute(
                """select p.id, p.storage_path, p.created_at
                   from public.report_photos p
                   join public.reports r on r.id=p.report_id
                   where r.incident_id=%s
                   order by p.created_at, p.id""", (incident_id,),
            ).fetchall()
    except psycopg.Error as exc:
        raise error(503, "DEPENDENCY_UNAVAILABLE", "Base de datos no disponible") from exc

    try:
        bucket = get_supabase_client().storage.from_("report-photos") if photo_rows else None
        photos = []
        for photo_id, path, date in photo_rows:
            signed = bucket.create_signed_url(path, 300) if bucket else None
            url = signed.get("signedURL") if signed else None
            if not url:
                raise RuntimeError("Storage no devolvió un enlace temporal")
            photos.append({"id": str(photo_id), "url": url, "created_at": date.isoformat()})
    except (StorageException, httpx.HTTPError, RuntimeError) as exc:
        raise error(503, "DEPENDENCY_UNAVAILABLE", "No se pudieron cargar las fotografías") from exc

    response.headers["Cache-Control"] = "no-store"

    (id_, code, name, title, description, lat, lon, severity, state, version,
     count, confirmations_count, priority_version, score_value, time_factor, calculated_at,
     created_at, updated_at) = row
    score = float(score_value)
    level = "critical" if score >= 75 else "high" if score >= 50 else "medium" if score >= 25 else "low"
    return {
        "id": str(id_), "category": {"code": code, "name": name}, "title": title,
        "description": description, "location": {"latitude": lat, "longitude": lon},
        "severity": severity, "status": state, "row_version": version,
        "reports_count": count, "confirmations_count": confirmations_count,
        "priority": {"score": score, "level": level, "version": priority_version,
                     "factors": {"G": GRAVITY[severity], "T": round(float(time_factor), 4)},
                     "weights": {"G": priority_weight_g, "T": priority_weight_t},
                     "calculated_at": calculated_at.isoformat()},
        "status_history": [{"previous_status": old, "new_status": new, "notes": notes,
                            "created_at": date.isoformat(), "changed_by": str(actor_id) if actor_id else None,
                            "changed_by_label": actor_email if actor_email else ("Sistema" if actor_id is None else "Funcionario no disponible")}
                           for old, new, notes, date, actor_id, actor_email in history],
        "photos": photos, "created_at": created_at.isoformat(), "updated_at": updated_at.isoformat(),
    }


@router.patch("/incidents/{incident_id}/status")
def change_status(
    incident_id: UUID, body: StatusInput, staff: tuple[User, UUID] = Depends(require_staff)
) -> dict:
    if not supabase_db_url:
        raise error(503, "DEPENDENCY_UNAVAILABLE", "Base de datos no configurada")
    try:
        with psycopg.connect(supabase_db_url, connect_timeout=5) as conn:
            row = conn.execute(
                """select i.status, i.row_version
                    from public.incidents i where i.id=%s and i.municipality_id=%s for update""",
                (incident_id, staff[1]),
            ).fetchone()
            if not row:
                raise error(404, "NOT_FOUND", "Incidente no encontrado")
            previous, version = row
            if version != body.expected_version:
                raise error(409, "CONFLICT", "El incidente cambió; actualiza el detalle")
            if body.status not in TRANSITIONS[previous]:
                raise error(409, "CONFLICT", "Transición de estado no permitida")
            updated = conn.execute(
                """update public.incidents set status=%s, row_version=row_version+1,
                   updated_at=now(), resolved_at=case when %s='resolved' then now() else null end
                   where id=%s returning row_version, updated_at""",
                (body.status, body.status, incident_id),
            ).fetchone()
            conn.execute(
                """insert into public.incident_status_history
                   (incident_id, previous_status, new_status, changed_by, notes)
                   values (%s, %s, %s, %s, %s)""",
                (incident_id, previous, body.status, staff[0].id, body.notes),
            )
        return {"id": str(incident_id), "status": body.status,
                "row_version": updated[0], "updated_at": updated[1].isoformat()}
    except psycopg.Error as exc:
        raise error(503, "DEPENDENCY_UNAVAILABLE", "Base de datos no disponible") from exc
