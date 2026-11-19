from dataclasses import dataclass
from uuid import UUID

import httpx
import psycopg
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from supabase_auth.errors import AuthError

from .config import supabase_db_url
from .supabase_client import get_supabase_client


bearer = HTTPBearer(auto_error=False)


@dataclass
class User:
    id: UUID
    is_anonymous: bool


def error(status: int, code: str, message: str) -> HTTPException:
    return HTTPException(status_code=status, detail={"error": {"code": code, "message": message}})


def get_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)) -> User:
    if credentials is None:
        raise error(401, "UNAUTHENTICATED", "Se requiere una sesión válida")
    try:
        auth_user = get_supabase_client().auth.get_user(credentials.credentials).user
        if auth_user is None:
            raise error(401, "UNAUTHENTICATED", "Token inválido o vencido")
        return User(id=UUID(str(auth_user.id)), is_anonymous=auth_user.is_anonymous is True)
    except AuthError as exc:
        if getattr(exc, "status", 401) >= 500:
            raise error(503, "DEPENDENCY_UNAVAILABLE", "Servicio de autenticación no disponible") from exc
        raise error(401, "UNAUTHENTICATED", "Token inválido o vencido") from exc
    except httpx.HTTPError as exc:
        raise error(503, "DEPENDENCY_UNAVAILABLE", "Servicio de autenticación no disponible") from exc


def get_staff_municipality(user: User) -> UUID | None:
    if user.is_anonymous:
        return None
    if not supabase_db_url:
        raise error(503, "DEPENDENCY_UNAVAILABLE", "Base de datos no configurada")
    try:
        with psycopg.connect(supabase_db_url, connect_timeout=5) as connection:
            row = connection.execute(
                """select s.municipality_id from private.staff_members s
                   join public.municipalities m on m.id = s.municipality_id
                   where s.user_id = %s and s.active and m.active""",
                (user.id,),
            ).fetchone()
            return row[0] if row else None
    except psycopg.Error as exc:
        raise error(503, "DEPENDENCY_UNAVAILABLE", "Base de datos no disponible") from exc


def require_citizen(user: User = Depends(get_current_user)) -> User:
    if not user.is_anonymous:
        raise error(403, "FORBIDDEN", "Se requiere una sesión ciudadana")
    return user


def require_staff(user: User = Depends(get_current_user)) -> tuple[User, UUID]:
    municipality_id = get_staff_municipality(user)
    if municipality_id is None:
        raise error(403, "FORBIDDEN", "Se requiere una cuenta de funcionario activo")
    return user, municipality_id
