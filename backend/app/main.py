from fastapi import Depends, FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import cors_origins
from .auth import User, get_current_user, get_staff_municipality
from .report_routes import router as report_router
from .incident_routes import router as incident_router
from .voice_routes import router as voice_router
from .photo_routes import router as photo_router


app = FastAPI(title="Plataforma de Inteligencia Urbana")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["Authorization", "Content-Type"],
)
app.include_router(report_router)
app.include_router(incident_router)
app.include_router(voice_router)
app.include_router(photo_router)


@app.exception_handler(HTTPException)
def handle_http_error(_request, exc: HTTPException) -> JSONResponse:
    if isinstance(exc.detail, dict) and "error" in exc.detail:
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    code = {401: "UNAUTHENTICATED", 403: "FORBIDDEN", 404: "NOT_FOUND"}.get(exc.status_code, "BAD_REQUEST")
    return JSONResponse(status_code=exc.status_code, content={"error": {"code": code, "message": str(exc.detail)}})


@app.exception_handler(RequestValidationError)
def handle_validation_error(_request, exc: RequestValidationError) -> JSONResponse:
    fields = {".".join(str(part) for part in item["loc"][1:]): item["type"] for item in exc.errors()}
    return JSONResponse(status_code=422, content={"error": {"code": "VALIDATION_ERROR", "message": "Datos inválidos", "fields": fields}})


@app.get("/api/v1/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/auth/me")
def auth_me(user: User = Depends(get_current_user)) -> dict[str, str | None]:
    municipality_id = get_staff_municipality(user)
    role = "staff" if municipality_id else "citizen" if user.is_anonymous else "unassigned"
    return {"user_id": str(user.id), "role": role, "municipality_id": str(municipality_id) if municipality_id else None}

