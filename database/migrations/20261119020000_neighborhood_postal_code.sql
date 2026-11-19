-- P1.9: código postal oficial para buscar asentamientos; 00000 se trata como desconocido.
alter table public.neighborhoods add column postal_code text
    check (postal_code is null or (postal_code ~ '^[0-9]{5}$' and postal_code <> '00000'));

create index neighborhoods_municipality_postal_code_idx
    on public.neighborhoods (municipality_id, postal_code, name);
