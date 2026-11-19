-- P1: metadatos de fotografías. El archivo vive en el bucket privado report-photos.
create table if not exists public.report_photos (
    id uuid primary key default gen_random_uuid(),
    report_id uuid not null references public.reports(id),
    storage_path text not null unique,
    mime_type text not null check (mime_type in ('image/jpeg', 'image/png')),
    size_bytes integer not null check (size_bytes between 1 and 5242880),
    created_at timestamptz not null default now(),
    constraint report_photos_path_format check (
        storage_path ~ '^[0-9a-f-]{36}/[0-9a-f-]{36}\.(jpg|png)$'
    )
);

create index if not exists report_photos_report_date_idx
    on public.report_photos (report_id, created_at desc);

alter table public.report_photos enable row level security;
-- Los clientes consultarán fotos únicamente mediante FastAPI.
revoke all on public.report_photos from public, anon, authenticated;
grant select, insert, delete on public.report_photos to service_role;
