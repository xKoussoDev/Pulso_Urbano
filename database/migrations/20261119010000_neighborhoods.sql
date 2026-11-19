-- P1.7: límites del INEGI DCAH 2024; los clientes siguen usando FastAPI.
create table public.neighborhoods (
    id uuid primary key default gen_random_uuid(),
    municipality_id uuid not null references public.municipalities(id),
    source_key text not null,
    name text not null,
    settlement_type text not null,
    source_updated_at date not null,
    source_institution text,
    boundary extensions.geometry(MultiPolygon, 4326) not null,
    constraint neighborhoods_source_unique unique (municipality_id, source_key),
    constraint neighborhoods_municipality_pair unique (id, municipality_id),
    constraint neighborhoods_source_key_not_blank check (length(trim(source_key)) > 0),
    constraint neighborhoods_name_not_blank check (length(trim(name)) > 0),
    constraint neighborhoods_boundary_valid check (extensions.ST_IsValid(boundary))
);

create index neighborhoods_boundary_idx on public.neighborhoods using gist (boundary);
create index neighborhoods_municipality_name_idx on public.neighborhoods (municipality_id, name);

alter table public.incidents add column neighborhood_id uuid;
alter table public.incidents add constraint incidents_neighborhood_municipality_fk
    foreign key (neighborhood_id, municipality_id)
    references public.neighborhoods (id, municipality_id);
create index incidents_municipality_neighborhood_idx
    on public.incidents (municipality_id, neighborhood_id);

alter table public.neighborhoods enable row level security;
revoke all on public.neighborhoods from public, anon, authenticated;
grant select, insert, update on public.neighborhoods to service_role;
