-- P2.1: una confirmación por sesión ciudadana e incidente.
create table public.incident_confirmations (
    id uuid primary key default gen_random_uuid(),
    incident_id uuid not null references public.incidents(id),
    user_id uuid not null references auth.users(id),
    created_at timestamptz not null default now(),
    constraint incident_confirmations_once_per_user unique (incident_id, user_id)
);

alter table public.incident_confirmations enable row level security;
revoke all on public.incident_confirmations from public, anon, authenticated;
grant select, insert, delete on public.incident_confirmations to service_role;
