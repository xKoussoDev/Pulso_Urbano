import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv(Path(__file__).resolve().parents[1] / ".env")

cors_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
    if origin.strip()
]

supabase_url = os.getenv("SUPABASE_URL")
supabase_secret_key = os.getenv("SUPABASE_SECRET_KEY")
supabase_db_url = os.getenv("SUPABASE_DB_URL")

# Límites provisionales de la demo: oeste, sur, este, norte.
demo_bbox = tuple(float(value) for value in os.getenv("DEMO_BBOX", "-102.50,21.70,-102.10,22.10").split(","))
if len(demo_bbox) != 4 or demo_bbox[0] >= demo_bbox[2] or demo_bbox[1] >= demo_bbox[3]:
    raise ValueError("DEMO_BBOX debe tener oeste,sur,este,norte")

priority_weight_g = float(os.getenv("PRIORITY_WEIGHT_G", "0.8"))
priority_weight_t = float(os.getenv("PRIORITY_WEIGHT_T", "0.2"))
if priority_weight_g < 0 or priority_weight_t < 0 or abs(priority_weight_g + priority_weight_t - 1) > 0.000001:
    raise ValueError("Los pesos de prioridad deben ser positivos y sumar 1")

map_max_bbox_span = float(os.getenv("MAP_MAX_BBOX_SPAN", "0.8"))
if not 0 < map_max_bbox_span <= 5:
    raise ValueError("MAP_MAX_BBOX_SPAN debe estar entre 0 y 5 grados")

