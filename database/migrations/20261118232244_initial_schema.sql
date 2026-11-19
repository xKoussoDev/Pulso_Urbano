-- P0: esquema inicial. Aplicar una sola vez después de revisar las tablas existentes.
-- No contiene usuarios, reportes ni incidentes ficticios.

create schema if not exists extensions;
create extension if not exists postgis with schema extensions;
create schema if not exists private;

revoke all on schema private from public, anon, authenticated;
grant usage on schema private to service_role;

create table public.municipalities (
    id uuid primary key default gen_random_uuid(),
    code text not null unique,
    name text not null,
    active boolean not null default true,
    created_at timestamptz not null default now(),
    constraint municipalities_code_not_blank check (length(trim(code)) > 0),
    constraint municipalities_name_not_blank check (length(trim(name)) > 0)
);

create table public.categories (
    id uuid primary key default gen_random_uuid(),
    code text not null unique,
    name text not null,
    description text,
    default_severity text not null default 'medium',
    active boolean not null default true,
    constraint categories_code_not_blank check (length(trim(code)) > 0),
    constraint categories_name_not_blank check (length(trim(name)) > 0),
    constraint categories_severity_valid check (
        default_severity in ('low', 'medium', 'high', 'critical')
    )
);

create table private.staff_members (
    user_id uuid primary key references auth.users(id),
    municipality_id uuid not null references public.municipalities(id),
    active boolean not null default true,
    created_at timestamptz not null default now()
);

create table public.incidents (
    id uuid primary key default gen_random_uuid(),
    municipality_id uuid not null references public.municipalities(id),
    category_id uuid not null references public.categories(id),
    title text not null,
    description text not null,
    location extensions.geography(Point, 4326) not null,
    severity text not null,
    status text not null default 'reported',
    priority_version integer not null default 1,
    row_version integer not null default 1,
    opened_at timestamptz not null default now(),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    resolved_at timestamptz,
    constraint incidents_category_and_municipality_unique unique (id, municipality_id, category_id),
    constraint incidents_title_not_blank check (length(trim(title)) > 0),
    constraint incidents_description_not_blank check (length(trim(description)) > 0),
    constraint incidents_severity_valid check (severity in ('low', 'medium', 'high', 'critical')),
    constraint incidents_status_valid check (
        status in ('reported', 'in_review', 'confirmed', 'in_progress', 'resolved', 'discarded')
    ),
    constraint incidents_resolved_at_valid check ((status = 'resolved') = (resolved_at is not null)),
    constraint incidents_versions_positive check (priority_version > 0 and row_version > 0)
);

create table public.reports (
    id uuid primary key default gen_random_uuid(),
    reporter_id uuid not null references auth.users(id),
    client_request_id uuid not null,
    incident_id uuid not null,
    municipality_id uuid not null references public.municipalities(id),
    category_id uuid not null references public.categories(id),
    description text not null,
    duration_text text,
    severity_selected text not null,
    location extensions.geography(Point, 4326) not null,
    location_source text not null,
    source text not null default 'mobile_app',
    input_method text not null,
    created_at timestamptz not null default now(),
    constraint reports_request_unique unique (reporter_id, client_request_id),
    constraint reports_incident_consistent foreign key (incident_id, municipality_id, category_id)
        references public.incidents(id, municipality_id, category_id),
    constraint reports_description_length check (length(trim(description)) between 10 and 1000),
    constraint reports_duration_length check (duration_text is null or length(duration_text) <= 100),
    constraint reports_severity_valid check (severity_selected in ('low', 'medium', 'high', 'critical')),
    constraint reports_location_source_valid check (location_source in ('gps', 'map')),
    constraint reports_source_valid check (source in ('mobile_app', 'whatsapp', 'web')),
    constraint reports_input_method_valid check (input_method in ('traditional', 'voice'))
);

create table public.incident_status_history (
    id uuid primary key default gen_random_uuid(),
    incident_id uuid not null references public.incidents(id),
    previous_status text,
    new_status text not null,
    changed_by uuid references auth.users(id),
    notes text,
    created_at timestamptz not null default now(),
    constraint status_history_previous_valid check (
        previous_status is null or previous_status in
        ('reported', 'in_review', 'confirmed', 'in_progress', 'resolved', 'discarded')
    ),
    constraint status_history_new_valid check (
        new_status in ('reported', 'in_review', 'confirmed', 'in_progress', 'resolved', 'discarded')
    ),
    constraint status_history_notes_length check (notes is null or length(notes) <= 500)
);

create table public.priority_history (
    id uuid primary key default gen_random_uuid(),
    incident_id uuid not null references public.incidents(id),
    previous_score numeric(5, 2),
    new_score numeric(5, 2) not null,
    calculation_version integer not null,
    factors jsonb not null,
    weights jsonb not null,
    created_at timestamptz not null default now(),
    constraint priority_history_previous_range check (
        previous_score is null or previous_score between 0 and 100
    ),
    constraint priority_history_new_range check (new_score between 0 and 100),
    constraint priority_history_version_positive check (calculation_version > 0),
    constraint priority_history_json_objects check (
        jsonb_typeof(factors) = 'object' and jsonb_typeof(weights) = 'object'
    )
);

create index incidents_location_idx on public.incidents using gist (location);
create index reports_location_idx on public.reports using gist (location);
create index incidents_municipality_status_date_idx
    on public.incidents (municipality_id, status, created_at desc);
create index incidents_municipality_category_date_idx
    on public.incidents (municipality_id, category_id, created_at desc);
create index incidents_municipality_status_severity_idx
    on public.incidents (municipality_id, status, severity, id);
create index reports_reporter_date_idx on public.reports (reporter_id, created_at desc, id);
create index reports_incident_date_idx on public.reports (incident_id, created_at desc);
create index status_history_incident_date_idx
    on public.incident_status_history (incident_id, created_at desc);
create index priority_history_incident_date_idx
    on public.priority_history (incident_id, created_at desc);

alter table public.municipalities enable row level security;
alter table public.categories enable row level security;
alter table private.staff_members enable row level security;
alter table public.incidents enable row level security;
alter table public.reports enable row level security;
alter table public.incident_status_history enable row level security;
alter table public.priority_history enable row level security;

-- Los clientes usan FastAPI para datos de negocio. No hay políticas directas para anon/authenticated.
revoke all on public.municipalities from public, anon, authenticated;
revoke all on public.categories from public, anon, authenticated;
revoke all on private.staff_members from public, anon, authenticated;
revoke all on public.incidents from public, anon, authenticated;
revoke all on public.reports from public, anon, authenticated;
revoke all on public.incident_status_history from public, anon, authenticated;
revoke all on public.priority_history from public, anon, authenticated;

grant select, insert, update, delete on public.municipalities to service_role;
grant select, insert, update, delete on public.categories to service_role;
grant select, insert, update, delete on private.staff_members to service_role;
grant select, insert, update, delete on public.incidents to service_role;
grant select, insert, update, delete on public.reports to service_role;
grant select, insert, update, delete on public.incident_status_history to service_role;
grant select, insert, update, delete on public.priority_history to service_role;

insert into public.municipalities (code, name)
values ('aguascalientes_capital', 'Aguascalientes capital')
on conflict (code) do nothing;

insert into public.categories (code, name, default_severity) values
    ('falta_agua_potable', 'Falta de agua potable', 'high'),
    ('fuga_agua', 'Fuga de agua', 'medium'),
    ('bache', 'Bache', 'medium'),
    ('calle_deteriorada', 'Calle deteriorada', 'medium'),
    ('falta_alumbrado', 'Falta de alumbrado público', 'medium'),
    ('luminaria_danada', 'Luminaria dañada', 'low'),
    ('basura', 'Acumulación de basura', 'medium'),
    ('inundacion', 'Inundación', 'high'),
    ('infraestructura_danada', 'Infraestructura urbana dañada', 'medium'),
    ('otro', 'Otro problema urbano', 'low')
on conflict (code) do nothing;
