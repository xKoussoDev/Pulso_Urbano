"""Importa los polígonos oficiales DCAH 2024 y asigna incidentes sin adivinar."""

import argparse
import hashlib
import io
import sys
import zipfile
from datetime import datetime
from pathlib import Path

import psycopg
import shapefile
from pyproj import CRS, Transformer
from shapely import transform as transform_geometry
from shapely.geometry import MultiPolygon, shape

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.config import supabase_db_url  # noqa: E402


EXPECTED_SHA256 = "e36f706c7d896cdb46d00ec8f7b72c697bae3c89a90ab52eac9396347fb83d5c"
SOURCE_PREFIX = "conjunto_de_datos/01as"


def read_neighborhoods(zip_path: Path) -> list[tuple]:
    if hashlib.sha256(zip_path.read_bytes()).hexdigest() != EXPECTED_SHA256:
        raise ValueError("El ZIP no coincide con el paquete DCAH 2024 revisado")

    with zipfile.ZipFile(zip_path) as archive:
        reader = shapefile.Reader(
            shp=io.BytesIO(archive.read(SOURCE_PREFIX + ".shp")),
            shx=io.BytesIO(archive.read(SOURCE_PREFIX + ".shx")),
            dbf=io.BytesIO(archive.read(SOURCE_PREFIX + ".dbf")),
            encoding="latin1",
        )
        source_crs = CRS.from_wkt(archive.read(SOURCE_PREFIX + ".prj").decode("ascii"))
        transformer = Transformer.from_crs(source_crs, "EPSG:4326", always_xy=True)

        rows = []
        keys = set()
        for item in reader.iterShapeRecords():
            data = item.record.as_dict()
            if (data["CVE_ENT"], data["CVE_MUN"]) != ("01", "001"):
                continue
            key = data["CVEGEO"].strip()
            if key in keys or not key:
                raise ValueError(f"Clave de origen duplicada o vacía: {key}")
            keys.add(key)
            boundary = transform_geometry(
                shape(item.shape.__geo_interface__), transformer.transform, interleaved=False
            )
            if boundary.geom_type == "Polygon":
                boundary = MultiPolygon([boundary])
            if boundary.geom_type != "MultiPolygon" or boundary.is_empty or not boundary.is_valid:
                raise ValueError(f"Geometría inválida para {key}")
            min_lon, min_lat, max_lon, max_lat = boundary.bounds
            if not (-103 < min_lon < max_lon < -101 and 21 < min_lat < max_lat < 23):
                raise ValueError(f"Coordenadas fuera de Aguascalientes: {key}")
            postal_code = str(data["CP"]).strip()
            if len(postal_code) != 5 or not postal_code.isdigit():
                raise ValueError(f"Código postal inválido para {key}")
            rows.append((
                key,
                data["NOM_ASEN"].strip(),
                data["TIPO"].strip(),
                datetime.strptime(data["FECHA_ACT"], "%m/%Y").date(),
                data["INSTITUCIO"].strip(),
                None if postal_code == "00000" else postal_code,
                boundary.wkb,
            ))
    if len(rows) != 1020 or any(not row[1] for row in rows):
        raise ValueError(f"Se esperaban 1020 asentamientos con nombre; llegaron {len(rows)}")
    return rows


def import_rows(rows: list[tuple]) -> None:
    if not supabase_db_url:
        raise RuntimeError("Falta SUPABASE_DB_URL en backend/.env")
    with psycopg.connect(supabase_db_url, connect_timeout=10) as connection:
        with connection.cursor() as cursor:
            cursor.execute("select id from public.municipalities where code = 'aguascalientes_capital'")
            municipality = cursor.fetchone()
            if municipality is None:
                raise RuntimeError("No existe el municipio aguascalientes_capital")
            municipality_id = municipality[0]
            cursor.executemany(
                """insert into public.neighborhoods
                   (municipality_id, source_key, name, settlement_type,
                    source_updated_at, source_institution, postal_code, boundary)
                   values (%s, %s, %s, %s, %s, %s, %s,
                           extensions.ST_Multi(extensions.ST_GeomFromWKB(%s, 4326)))
                   on conflict (municipality_id, source_key) do update set
                       name = excluded.name,
                       settlement_type = excluded.settlement_type,
                       source_updated_at = excluded.source_updated_at,
                       source_institution = excluded.source_institution,
                       postal_code = excluded.postal_code,
                       boundary = excluded.boundary""",
                [(municipality_id, *row) for row in rows],
            )
            cursor.execute(
                """with matches as (
                       select i.id, min(n.id::text)::uuid as neighborhood_id,
                              count(n.id) as match_count
                       from public.incidents i
                       left join public.neighborhoods n
                         on n.municipality_id = i.municipality_id
                        and extensions.ST_Covers(n.boundary, i.location::extensions.geometry)
                       where i.municipality_id = %s
                       group by i.id
                   )
                   update public.incidents i
                   set neighborhood_id = case when m.match_count = 1
                                              then m.neighborhood_id else null end
                   from matches m where i.id = m.id
                     and i.neighborhood_id is distinct from
                         case when m.match_count = 1 then m.neighborhood_id else null end""",
                (municipality_id,),
            )
            cursor.execute(
                """select count(*), count(i.neighborhood_id)
                   from public.incidents i where i.municipality_id = %s""",
                (municipality_id,),
            )
            total, assigned = cursor.fetchone()
            cursor.execute(
                "select count(*) from public.neighborhoods where municipality_id = %s",
                (municipality_id,),
            )
            imported = cursor.fetchone()[0]
            if imported != 1020:
                raise RuntimeError(f"La base contiene {imported} polígonos; se esperaban 1020")
    print(f"Polígonos: {imported}; incidentes asignados: {assigned}/{total}")


def verify_database() -> None:
    if not supabase_db_url:
        raise RuntimeError("Falta SUPABASE_DB_URL en backend/.env")
    with psycopg.connect(supabase_db_url, connect_timeout=10) as connection:
        with connection.cursor() as cursor:
            cursor.execute("select count(*) from public.neighborhoods")
            assert cursor.fetchone()[0] == 1020
            cursor.execute(
                """select count(*) filter (where postal_code is null),
                          count(distinct postal_code) from public.neighborhoods"""
            )
            assert cursor.fetchone() == (39, 132)
            cursor.execute("select relrowsecurity from pg_class where oid = 'public.neighborhoods'::regclass")
            assert cursor.fetchone()[0] is True
            cursor.execute(
                """select has_table_privilege('anon', 'public.neighborhoods', 'SELECT'),
                          has_table_privilege('authenticated', 'public.neighborhoods', 'SELECT')"""
            )
            assert cursor.fetchone() == (False, False)
            cursor.execute(
                """select count(*) from public.incidents i
                   left join lateral (
                       select count(*) as total, min(n.id::text)::uuid as only_id
                       from public.neighborhoods n
                       where n.municipality_id = i.municipality_id
                         and extensions.ST_Covers(n.boundary, i.location::extensions.geometry)
                   ) matches on true
                   where i.neighborhood_id is distinct from
                         case when matches.total = 1 then matches.only_id else null end"""
            )
            assert cursor.fetchone()[0] == 0
            cursor.execute(
                """with points as (
                       select 'interior' as kind, extensions.ST_PointOnSurface(boundary) as point
                       from public.neighborhoods order by source_key limit 1
                   )
                   select count(*) from public.neighborhoods n, points p
                   where extensions.ST_Covers(n.boundary, p.point)"""
            )
            assert cursor.fetchone()[0] >= 1
            cursor.execute(
                """with points as (
                       select extensions.ST_PointN(extensions.ST_ExteriorRing(
                           extensions.ST_GeometryN(boundary, 1)), 1) as point
                       from public.neighborhoods order by source_key limit 1
                   )
                   select count(*) from public.neighborhoods n, points p
                   where extensions.ST_Covers(n.boundary, p.point)"""
            )
            assert cursor.fetchone()[0] >= 1
            cursor.execute(
                """with overlap as (
                       select extensions.ST_PointOnSurface(extensions.ST_Intersection(
                           a.boundary, b.boundary)) as point
                       from public.neighborhoods a join public.neighborhoods b
                         on a.id < b.id and a.boundary && b.boundary
                        and extensions.ST_Area(extensions.ST_Intersection(a.boundary, b.boundary)) > 0
                       limit 1
                   )
                   select count(*) from public.neighborhoods n, overlap o
                   where extensions.ST_Covers(n.boundary, o.point)"""
            )
            assert cursor.fetchone()[0] > 1
            cursor.execute(
                """select count(*) from public.neighborhoods n
                   where extensions.ST_Covers(n.boundary,
                       extensions.ST_SetSRID(extensions.ST_MakePoint(-102.75, 21.6), 4326))"""
            )
            assert cursor.fetchone()[0] == 0
    print("Verificación: RLS/permisos, asignaciones, interior, borde, solape y exterior OK")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("zip_path", type=Path, help="ZIP oficial 01_aguascalientes.zip")
    parser.add_argument("--apply", action="store_true", help="Guardar en Supabase y asignar incidentes")
    parser.add_argument("--verify", action="store_true", help="Comprobar la base sin modificarla")
    args = parser.parse_args()
    neighborhoods = read_neighborhoods(args.zip_path)
    print(f"Validación del ZIP: {len(neighborhoods)} polígonos municipales correctos")
    if args.apply:
        import_rows(neighborhoods)
    if args.apply or args.verify:
        verify_database()
