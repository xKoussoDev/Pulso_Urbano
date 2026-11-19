# Esquema de base de datos propuesto

**Estado:** migración inicial aplicada el 18 de noviembre de 2026; fotografías, colonias y `incident_confirmations` aplicadas y comprobadas el 19 de noviembre de 2026. SQL en `database/migrations/`.  
**Alcance:** Supabase PostgreSQL + PostGIS para Aguascalientes capital.  
**Referencia de producto:** [`PLAN.md`](../PLAN.md) y [`PROJECT_STATUS.md`](../PROJECT_STATUS.md).

## 1. Principios

- `Report` es una comunicación ciudadana confirmada. `Incident` es el problema urbano observado. Un incidente puede agrupar muchos reportes, aunque en P0 normalmente se creará uno por reporte.
- `WorkOrder` sería una tarea operativa asignada al municipio. No existe en P0/P1; un cambio de estado de incidente no significa que se haya creado una orden de trabajo.
- La identidad de Auth y la autorización del personal se mantienen separadas de reportes e incidentes. En la demo, el ciudadano usa Auth anónimo: no se solicita perfil, nombre, teléfono ni correo.
- Solo se persiste la descripción final revisada y anonimizada. Ni el audio ni la transcripción original se almacenan. No habrá una columna de `confidence_score` inventada por el LLM.
- Las coordenadas se reciben como latitud/longitud, pero se almacenan como un único punto PostGIS con SRID 4326. Al construirlo se utiliza **longitud primero, latitud después**. Esto evita dos fuentes de verdad.
- Todos los tiempos son `timestamptz` en UTC y los identificadores son UUID. Fechas e identidades se asignan en el servidor.

## 2. Tablas P0

| Tabla | Columnas y restricciones principales | Relación |
|---|---|---|
| `public.municipalities` | `id uuid PK`, `code text UNIQUE NOT NULL`, `name text NOT NULL`, `active boolean NOT NULL DEFAULT true`, `created_at timestamptz NOT NULL`. Una fila inicial para Aguascalientes capital. | 1:N con incidentes, reportes y personal. |
| `public.categories` | `id uuid PK`, `code text UNIQUE NOT NULL`, `name text NOT NULL`, `description text`, `default_severity text`, `active boolean NOT NULL DEFAULT true`. Gravedad permitida: `low`, `medium`, `high`, `critical`. | 1:N con reportes e incidentes. |
| `private.staff_members` | `user_id uuid PK` → `auth.users.id`, `municipality_id uuid NOT NULL` → `municipalities.id`, `active boolean NOT NULL DEFAULT true`, `created_at timestamptz NOT NULL`. Solo un administrador del proyecto da de alta funcionarios. | Cuenta de Auth autorizada para el dashboard. No se deriva de `user_metadata`. |
| `public.incidents` | `id uuid PK`, `municipality_id uuid NOT NULL FK`, `category_id uuid NOT NULL FK`, `title text NOT NULL`, `description text NOT NULL`, `location geography(Point,4326) NOT NULL`, `severity text NOT NULL`, `status text NOT NULL DEFAULT 'reported'`, `priority_version integer NOT NULL`, `row_version integer NOT NULL DEFAULT 1`, `opened_at`, `created_at`, `updated_at`, `resolved_at timestamptz`. La prioridad vigente se calcula al consultar para que el factor tiempo no quede desactualizado. | 1:N con reportes, historiales y fotos mediante reportes. |
| `public.reports` | `id uuid PK`, `reporter_id uuid NOT NULL` → `auth.users.id`, `client_request_id uuid NOT NULL`, `incident_id uuid NOT NULL FK`, `municipality_id uuid NOT NULL FK`, `category_id uuid NOT NULL FK`, `description text NOT NULL`, `duration_text text`, `severity_selected text NOT NULL`, `location geography(Point,4326) NOT NULL`, `location_source text NOT NULL`, `source text NOT NULL DEFAULT 'mobile_app'`, `input_method text NOT NULL`, `created_at timestamptz NOT NULL`, `UNIQUE (reporter_id, client_request_id)`. `location_source`: `gps` o `map`; `input_method`: `traditional` o `voice`. | N:1 con incidente. `reporter_id` es un identificador privado, nunca parte de un agregado territorial. La clave de solicitud evita duplicados por reintento. |
| `public.incident_status_history` | `id uuid PK`, `incident_id uuid NOT NULL FK`, `previous_status text NULL`, `new_status text NOT NULL`, `changed_by uuid NULL` → `auth.users.id`, `notes text`, `created_at timestamptz NOT NULL`. Una fila inicial registra `reported`. | N:1 con incidente. Se escribe en la transacción del cambio de estado. |
| `public.priority_history` | `id uuid PK`, `incident_id uuid NOT NULL FK`, `previous_score numeric(5,2) NULL`, `new_score numeric(5,2) NOT NULL`, `calculation_version integer NOT NULL`, `factors jsonb NOT NULL`, `weights jsonb NOT NULL`, `created_at timestamptz NOT NULL`. | N:1 con incidente. Una fila inicial registra el primer cálculo. |

Los estados válidos de incidente son `reported`, `in_review`, `confirmed`, `in_progress`, `resolved` y `discarded`. Para esta demo, `resolved` y `discarded` son estados finales: no se pueden reabrir ni editar, pero permanecen consultables en la lista de finalizados. `resolved_at` solo tendrá valor si el estado es `resolved`. El autor de cada cambio se conserva en `changed_by`; su correo se consulta en `auth.users` solo para el detalle privado del funcionario.

El backend debe verificar que `reports.municipality_id`, `reports.category_id` y el incidente vinculado sean coherentes. En P0, la creación de reporte + incidente + ambas filas históricas ocurre en **una transacción**. No se acepta `reporter_id`, `created_at`, `priority_score` ni `status` desde el cliente.

### Catálogo inicial de categorías

`falta_agua_potable`, `fuga_agua`, `bache`, `calle_deteriorada`, `falta_alumbrado`, `luminaria_danada`, `basura`, `inundacion`, `infraestructura_danada` y `otro`. Los códigos permanecen estables aunque cambien los nombres mostrados.

### Índices P0

| Tabla | Índice | Motivo |
|---|---|---|
| `incidents` | GiST sobre `location` | Marcadores por área y futuras búsquedas de cercanía. |
| `reports` | GiST sobre `location` | Futuras comprobaciones geográficas. |
| `incidents` | B-tree `(municipality_id, status, created_at DESC)` | Dashboard y métricas por municipio/estado. |
| `incidents` | B-tree `(municipality_id, category_id, created_at DESC)` | Filtros por categoría y fecha. |
| `incidents` | B-tree `(municipality_id, status, severity, id)` | Filtrado previo al cálculo y orden de prioridades. En el prototipo se ordena la puntuación calculada sobre el conjunto filtrado. |
| `reports` | B-tree `(reporter_id, created_at DESC, id)` | `GET /reports/me`. |
| `reports` | B-tree `(incident_id, created_at DESC)` | Detalle y conteo de reportes asociados. |
| `incident_status_history`, `priority_history` | B-tree `(incident_id, created_at DESC)` | Historial del detalle. |
| `report_photos` | B-tree `(report_id, created_at DESC)` | Fotos asociadas al reporte. |

Las llaves primarias y `UNIQUE` crean sus índices propios. La necesidad de índices adicionales se decidirá con consultas reales, no por anticipación.

## 3. Tabla P1 aplicada y campos posteriores

`public.report_photos` ya existe con `id uuid PK`, `report_id uuid FK` a `reports`, `storage_path text UNIQUE`, `mime_type` limitado a JPEG/PNG, `size_bytes` entre 1 byte y 5 MB, y `created_at`. RLS está activo y no hay políticas de acceso directo para clientes. El bucket `report-photos` es privado, admite solo JPEG/PNG y limita cada objeto a 5 MB. El backend autoriza la escritura mediante `POST /reports/{id}/photos` y, tras comprobar el municipio del funcionario, entrega enlaces de lectura válidos por 300 segundos en `GET /incidents/{id}`. La app móvil envía las fotos tras confirmar el reporte. La imagen se vuelve a guardar sin metadatos EXIF antes de almacenarla.

| Fase | Elemento | Diseño |
|---|---|---|
| P1 | `public.neighborhoods` | Aplicada: `id uuid PK`, `municipality_id uuid FK`, `source_key text` único por municipio, `name`, `settlement_type`, `source_updated_at`, `source_institution`, `postal_code text NULL`, `boundary geometry(MultiPolygon,4326)` válida. Índices GiST en límite y B-tree en municipio/nombre y municipio/CP/nombre. `00000` se convierte en `NULL`. `incidents.neighborhood_id uuid NULL` tiene FK compuesta para impedir cruzar municipios; los incidentes anteriores y los nuevos se asignan solo con una coincidencia espacial única. RLS activa y acceso directo cliente denegado. |
| P2 | `public.incident_confirmations` | Aplicada: `id uuid PK`, `incident_id uuid FK`, `user_id uuid FK` a Auth, `created_at`, `UNIQUE (incident_id, user_id)`. RLS activa y sin acceso directo para clientes. Se cuenta una vez por sesión anónima e incidente. No se usa `report_id` del borrador de `PLAN.md` porque confirmar es una acción independiente de crear un reporte; el autor de un reporte vinculado no puede autoconfirmarse. |
| P2 | Consolidación de duplicados | Registro de unión con incidente origen, destino, funcionario, motivo y fecha; los reportes conservan su identidad. Primero se prueban reglas de categoría, distancia y tiempo. |
| P3 | `work_orders` | `id`, `incident_id FK`, responsable/área, estado operativo, fechas e historial propio. La prioridad del incidente no asigna una orden automáticamente. |
| P3 | Embeddings/pgvector | Se agregan solo si una evaluación demuestra mejor detección de duplicados. No se crea una columna vectorial vacía en P0. |

## 4. Prioridad y datos territoriales

Versión inicial: `score = 0.80 × G + 0.20 × T`, con `G` y `T` entre 0 y 100. `G` usa una tabla explícita (`low=25`, `medium=50`, `high=75`, `critical=100`). `T` aumenta de 0 a 100 durante los primeros 14 días sin resolver; después queda en 100. Se redondea a dos decimales. La gravedad seleccionada por el ciudadano es una declaración, no una verificación municipal.

Los niveles visuales iniciales serán `low` para 0–24,99, `medium` para 25–49,99, `high` para 50–74,99 y `critical` para 75–100. Estos umbrales deberán probarse con ejemplos antes de usarse en la demo. El factor tiempo se calcula desde `opened_at` al consultar; se congela en `resolved_at` al resolver y en `updated_at` al descartar. Los estados finales no figuran entre prioridades activas. `priority_history` registra la puntuación inicial y futuros cambios de factores, si se implementan. No se escribe una fila histórica en cada lectura ni se afirma que el historial sea una muestra diaria completa.

La fórmula completa prevista en `PLAN.md` contempla gravedad `G`, alcance `A`, confirmaciones `C`, tiempo `T` y vulnerabilidad `V`. `A`, `C` y `V` tienen peso cero en P0 porque faltan datos o funciones para medirlos. Una nueva versión de fórmula tendrá pesos que sumen uno, una versión distinta e historial conservado. Ningún valor faltante se reemplaza silenciosamente por una medición inventada.

## 5. Seguridad y privacidad

| Recurso | Ciudadano autenticado | Funcionario activo | Acceso directo con clave publicable |
|---|---|---|---|
| Categorías activas | Leer vía FastAPI | Leer vía FastAPI | Sin necesidad de Data API |
| Reporte propio | Crear y leer vía FastAPI | Leer para el municipio asignado | Denegado |
| Reportes ajenos e identidad | Denegado | Solo lo necesario para atención; sin nombre/contacto ciudadano | Denegado |
| Incidentes, mapa, métricas e historiales | Denegado en P0 | Leer; cambiar estado cuando corresponda | Denegado |
| Personal autorizado | Denegado | Sin edición desde el dashboard MVP | Denegado |
| Fotos P1 | Solo las propias mediante FastAPI | Acceso autorizado mediante enlace temporal | Bucket privado, sin lectura pública |

- Supabase Auth emite el JWT. FastAPI valida firma, emisor, expiración y sujeto; luego consulta `private.staff_members` para privilegios de funcionario. `user_metadata` no concede roles. Las sesiones anónimas de ciudadanos no se confunden con privilegios de personal.
- El esquema `private` no se expone por la Data API: `anon` y `authenticated` no reciben permiso de uso sobre él. `private.staff_members` también tendrá RLS habilitada como defensa adicional. En el esquema `public`, RLS se habilita en **todas** las tablas. Se revocan privilegios de `anon` y `authenticated` sobre tablas de negocio y no se crean políticas de acceso directo; clientes usan FastAPI. El acceso administrativo del backend puede omitir RLS, por lo que la autorización en cada ruta de FastAPI es obligatoria.
- El bucket P1 es privado y no concede políticas de lectura o carga directa a usuarios finales. FastAPI autoriza cada operación y usa su credencial privada para Storage. El enlace temporal de lectura se emite solo después de esa comprobación.
- No se crean vistas públicas para análisis; si posteriormente existen, deben excluir `reporter_id`, texto bruto, rutas de fotos y coordenadas precisas cuando no sean necesarias. Una vista con privilegios elevados podría ignorar RLS y requeriría revisión específica.
- El audio de voz se procesa en memoria o archivo temporal local con eliminación al terminar. Se anonimiza el texto detectable antes de enviarlo a Gemini y se vuelve a revisar antes de persistir la descripción confirmada. Para esta demo solo se admiten datos ficticios. La anonimización automática no garantiza eliminar nombres, domicilios u otros identificadores inesperados.
- La ubicación precisa puede revelar hábitos o domicilio incluso sin nombre. El mapa y detalle son privados; futuras estadísticas públicas deberán agregar por zona y evitar reportes individuales.
- La clave publicable de Supabase puede estar en los clientes para Auth; las credenciales administrativas, la cadena de conexión y la clave de Gemini solo estarán en el backend local.
- En la demo, HTTP dentro de una red local confiable transportaría el JWT sin cifrado entre teléfono y FastAPI. Solo se usarán cuentas y datos ficticios. Antes de cualquier uso real se necesitará HTTPS de extremo a extremo y una revisión adicional de privacidad y seguridad.

## 6. Verificación del esquema

Se aplicó la migración en una transacción después de comprobar que `public` no tenía tablas. La lectura posterior confirmó siete tablas con RLS habilitada, nueve índices, PostGIS, un municipio y diez categorías. A nivel de privilegios, `anon` carece de `SELECT` en `reports`, `authenticated` carece de `INSERT` en `incidents` y `service_role` tiene `INSERT` en `reports`.

Faltan pruebas de restricciones con datos de ejemplo, consultas espaciales reales, acceso por JWT, aislamiento entre ciudadanos y autorización de cambios de estado por funcionarios. Esas pruebas pertenecen a las tareas donde se implementen las rutas y cuentas correspondientes.

**Fuentes de diseño:** [RLS](https://supabase.com/docs/guides/database/postgres/row-level-security), [PostGIS](https://supabase.com/docs/guides/database/extensions/postgis), [JWT](https://supabase.com/docs/guides/auth/jwts), [Storage](https://supabase.com/docs/guides/storage/security/access-control).
