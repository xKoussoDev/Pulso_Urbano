# Contratos HTTP de la API

**Estado:** `/health`, `/auth/me`, `/categories`, `POST /reports`, `POST /ai/process-voice-report`, `GET /incidents`, `GET /incidents/map`, `GET /incidents/{id}` y `PATCH /incidents/{id}/status` implementadas y probadas. Las demás rutas siguen pendientes.  
**Versión:** `/api/v1`.  
**Clientes:** app Expo para ciudadanos y dashboard React para funcionarios. Ambos hablan con FastAPI; Supabase Auth gestiona las sesiones.  
**Referencia:** [`data-model.md`](data-model.md) y [`PROJECT_STATUS.md`](../PROJECT_STATUS.md).

## 1. Convenciones y autorización

- En la demo, la app ciudadana inicia una sesión **anónima** de Supabase Auth. El dashboard inicia sesión con una cuenta de funcionario creada previamente. El inicio/cierre de sesión usa el SDK de Auth, no rutas duplicadas de FastAPI.
- Toda ruta salvo `/health` exige `Authorization: Bearer <access_token>`. FastAPI valida el JWT y obtiene el `user_id` del token, nunca del cuerpo. Para rutas gubernamentales consulta que el usuario esté activo en `private.staff_members` y usa su `municipality_id` para limitar los datos.
- Las respuestas son JSON UTF-8. Las entradas son JSON, excepto audio y fotos (`multipart/form-data`). Los tiempos usan ISO 8601 UTC y los identificadores usan UUID. Los objetos de ubicación usan `{ "latitude": número, "longitude": número }`, con latitud entre -90 y 90 y longitud entre -180 y 180; el backend además comprueba el área configurada para la demo.
- Los nombres de estado son `reported`, `in_review`, `confirmed`, `in_progress`, `resolved`, `discarded`; los de gravedad son `low`, `medium`, `high`, `critical`. `priority_level` usa esos cuatro niveles. `source` lo fija el backend como `mobile_app`.
- El navegador del dashboard solo puede llamar al origen local de FastAPI permitido por CORS. El teléfono usa la IP local de esa computadora; `localhost` en el teléfono apuntaría al teléfono, no al backend. Supabase, Gemini y Mapbox requieren internet.
- Si la demo utiliza HTTP en la red local, los tokens viajan sin cifrado en ese tramo. Se restringe a una red confiable, cuentas de prueba y datos ficticios; una versión con usuarios reales requerirá HTTPS.
- Ningún cliente envía `reporter_id`, `municipality_id`, fechas de servidor, puntuación o rol. Los campos desconocidos en solicitudes de escritura se rechazan, para detectar errores de contrato.

### Errores comunes

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "La ubicación es obligatoria",
    "fields": { "location": "required" }
  }
}
```

| HTTP | Código | Significado |
|---|---|---|
| 400 | `BAD_REQUEST` | Parámetros de URL o formato incoherentes. |
| 401 | `UNAUTHENTICATED` | Falta el token o no es válido/vigente. |
| 403 | `FORBIDDEN` | El usuario existe, pero no tiene el rol o municipio requerido. |
| 404 | `NOT_FOUND` | No existe el recurso o no está visible para ese usuario. No revela cuál de las dos causas ocurrió. |
| 409 | `CONFLICT` | Versión de estado desactualizada o clave de solicitud reutilizada con contenido distinto. |
| 413 | `FILE_TOO_LARGE` | Audio o imagen excede el límite. |
| 415 | `UNSUPPORTED_MEDIA_TYPE` | Archivo o tipo de contenido no permitido. |
| 422 | `VALIDATION_ERROR` | JSON bien formado con datos inválidos; `fields` señala los campos. |
| 429 | `RATE_LIMITED` | Demasiadas solicitudes de voz o carga. |
| 500 | `INTERNAL_ERROR` | Error inesperado; no devuelve secretos ni trazas al cliente. |
| 502 | `AI_UPSTREAM_ERROR` | Fallo de Gemini después de transcribir; la ruta de voz preferirá responder con modo manual y texto transcrito si lo tiene. |
| 503 | `DEPENDENCY_UNAVAILABLE` | Base de datos o servicio necesario no disponible. No crea reportes parciales. |

Las rutas de lectura aceptan `limit` de 1 a 50 y `cursor` opaco cuando se indica; responden `next_cursor: null` al terminar. Valores fuera de rango producen `422`. Las consultas se limitan siempre al municipio asignado al funcionario.

## 2. Rutas P0

### `GET /api/v1/health`

Sin autenticación. Respuesta `200`: `{ "status": "ok" }`. Confirma que FastAPI responde; no revela claves, configuración ni estado interno de Supabase. No demuestra que la aplicación completa funcione.

### `GET /api/v1/auth/me`

Requiere `Authorization: Bearer <access_token>` de Supabase Auth. Devuelve `200` con el usuario verificado y su acceso actual:

```json
{ "user_id": "11111111-1111-4111-8111-111111111111", "role": "citizen", "municipality_id": null }
```

`role` puede ser `citizen` para una sesión anónima, `staff` para un funcionario activo de un municipio activo o `unassigned` para otra cuenta autenticada. La API obtiene el rol de `private.staff_members`, no de metadatos editables. Errores: `401` si falta o falla el token; `503` si Supabase Auth o PostgreSQL no están disponibles.

### `GET /api/v1/categories`

Ciudadano o funcionario autenticado. Sin parámetros. Respuesta `200`:

```json
{
  "items": [
    { "id": "11111111-1111-4111-8111-111111111111", "code": "fuga_agua", "name": "Fuga de agua", "default_severity": "medium" }
  ]
}
```

Solo devuelve categorías activas. Errores: `401`, `503`.

### `POST /api/v1/ai/process-voice-report`

Solo ciudadano autenticado. `multipart/form-data` con campo `audio` obligatorio. Formatos aceptados inicialmente: audio grabado por Expo con MIME que el backend compruebe; lista exacta tras probar el dispositivo. Límite inicial: 30 segundos y 10 MB. No guarda audio ni crea un reporte. El backend transcribe localmente, quita patrones personales detectables, envía solo texto ficticio anonimizado a Gemini y valida la estructura devuelta contra las categorías válidas. Ubicación, foto y fecha nunca salen del LLM.

**Estado comprobado P0:** la ruta acepta `.m4a` con MIME `audio/mp4`, `audio/x-m4a`, `audio/m4a` o `application/octet-stream` y comprueba que sea audio decodificable. Usa Whisper local en CPU. Si `GEMINI_API_KEY` está configurada, envía **solo la transcripción ficticia** al modelo gratuito `gemini-3.1-flash-lite` para proponer categoría, duración y gravedad. Antes bloquea el envío si detecta patrones de correo, teléfono, frases de identidad o algunas direcciones precisas. Esto no garantiza detectar todos los datos personales: el ciudadano debe usar ejemplos ficticios y revisar el texto. El backend comprueba que las propuestas se apoyen en citas literales del texto y que la categoría esté activa; la descripción sigue siendo la transcripción editable. Sin clave, cuota, conexión o salida válida de Gemini devuelve `manual_fallback` sin impedir el formulario. El audio no sale a Gemini ni se guarda; ubicación y datos de sesión tampoco se envían. La app móvil aplica los campos sugeridos como valores editables; el usuario comprobó corrección, revisión y envío desde iPhone.

Respuesta `200` cuando hay propuesta:

```json
{
  "mode": "suggested",
  "transcription": "Hay una fuga de agua desde hace tres días",
  "draft": {
    "category_id": "11111111-1111-4111-8111-111111111111",
    "description": "Fuga de agua reportada desde hace tres días",
    "duration_text": "tres días",
    "severity_proposed": "high",
    "location": null
  },
  "missing_fields": ["location"],
  "warnings": ["Revisa y corrige todos los datos antes de enviar; no incluyas datos personales"]
}
```

Respuesta `200` cuando Whisper o Gemini falla de forma recuperable:

```json
{
  "mode": "manual_fallback",
  "reason": "TRANSCRIPTION_UNAVAILABLE",
  "transcription": null,
  "draft": {
    "category_id": null,
    "description": null,
    "duration_text": null,
    "severity_proposed": null,
    "location": null
  },
  "missing_fields": ["category_id", "description", "severity", "location"],
  "warnings": ["Completa el formulario manualmente"]
}
```

Si solo falla Gemini, `reason` será `EXTRACTION_UNAVAILABLE` y `transcription` conservará el texto anonimizado para que el ciudadano lo edite. Si el texto parece contener información personal que no puede tratarse con seguridad, `reason` será `REDACTION_REVIEW_REQUIRED` y no se enviará a Gemini. **La anonimización automática no es una garantía**; la demo utilizará entradas ficticias. Errores: `401`, `413`, `415`, `422` (audio vacío/ilegible), `429`, `500`. Ninguna respuesta de esta ruta implica registro.

### `POST /api/v1/reports`

Solo ciudadano autenticado. Se llama únicamente después de mostrar el resumen editable y de que la persona confirme. El cliente genera `client_request_id` una vez por intento de envío y lo reutiliza si reintenta por pérdida de conexión.

Entrada JSON:

```json
{
  "client_request_id": "22222222-2222-4222-8222-222222222222",
  "category_id": "11111111-1111-4111-8111-111111111111",
  "description": "Fuga de agua en la calle, sin datos personales",
  "duration_text": "tres días",
  "severity": "high",
  "location": { "latitude": 21.8818, "longitude": -102.2916 },
  "location_source": "gps",
  "input_method": "voice"
}
```

Respuesta `201` para una creación nueva:

```json
{
  "id": "33333333-3333-4333-8333-333333333333",
  "incident_id": "44444444-4444-4444-8444-444444444444",
  "status": "reported",
  "created_at": "2026-11-18T18:00:00Z"
}
```

P0 crea un incidente nuevo por cada reporte confirmado. Un reintento con el mismo `client_request_id` y mismo contenido devuelve `200` con el mismo JSON, sin duplicar filas; si cambia el contenido, `409`. Validaciones: categoría activa; descripción de 10 a 1000 caracteres sin correo/teléfono detectables; gravedad válida; ubicación obligatoria y en el área configurada; `duration_text` opcional hasta 100 caracteres; `location_source` e `input_method` válidos. `source`, usuario, estado, prioridad y fecha los fija el backend. Reporte, incidente e historiales se crean en una transacción. Errores: `401`, `409`, `422`, `503`.

Desde P1.8, en esa misma transacción el backend busca los polígonos oficiales que cubren el punto. Guarda `incidents.neighborhood_id` solo cuando hay exactamente una coincidencia del municipio; si no hay ninguna o hay varias, lo deja vacío. El ciudadano no elige ni recibe una colonia supuesta y el JSON de respuesta permanece igual.

**Límite de P0.5:** el área se comprueba con `DEMO_BBOX` (oeste, sur, este, norte), una caja provisional; la capa de asentamientos no equivale al límite oficial del municipio. Los pesos iniciales de prioridad se configuran con `PRIORITY_WEIGHT_G` y `PRIORITY_WEIGHT_T`, cuya suma debe ser 1.

### `GET /api/v1/reports/me`

Solo ciudadano autenticado. Parámetros `limit` (predeterminado 20) y `cursor` opcional. Respuesta `200`:

```json
{
  "items": [
    {
      "id": "33333333-3333-4333-8333-333333333333",
      "incident_id": "44444444-4444-4444-8444-444444444444",
      "category": { "code": "fuga_agua", "name": "Fuga de agua" },
      "status": "reported",
      "created_at": "2026-11-18T18:00:00Z"
    }
  ],
  "next_cursor": null
}
```

Filtra por el `user_id` del JWT; una sesión anónima perdida no permite recuperar esta lista. Errores: `401`, `422`, `503`.

### `GET /api/v1/reports/{id}`

Autor del reporte o funcionario activo del municipio correspondiente. Respuesta `200`:

```json
{
  "id": "33333333-3333-4333-8333-333333333333",
  "incident_id": "44444444-4444-4444-8444-444444444444",
  "category": { "code": "fuga_agua", "name": "Fuga de agua" },
  "description": "Fuga de agua en la calle, sin datos personales",
  "duration_text": "tres días",
  "severity": "high",
  "location": { "latitude": 21.8818, "longitude": -102.2916 },
  "location_source": "gps",
  "input_method": "voice",
  "status": "reported",
  "created_at": "2026-11-18T18:00:00Z",
  "photos": []
}
```

`photos` será vacío en P0. No devuelve `reporter_id` a funcionarios ni a otros usuarios. Errores: `401`, `404`, `422` (UUID inválido), `503`.

### `GET /api/v1/incidents`

Solo funcionario activo. Parámetros opcionales: `category_id`, `severity`, `priority_level`, `status`, `scope`, `from`, `to`, `limit`, `cursor`. `scope=active` muestra estados en atención y `scope=closed` muestra `resolved` y `discarded`; sin `scope` devuelve ambos. `from` y `to` son fechas ISO 8601 y filtran `created_at`; `from <= to`. Respuesta `200`:

```json
{
  "items": [
    {
      "id": "44444444-4444-4444-8444-444444444444",
      "category": { "code": "fuga_agua", "name": "Fuga de agua" },
      "title": "Fuga de agua",
      "severity": "high",
      "status": "reported",
      "reports_count": 1,
      "priority_score": 60.0,
      "priority_level": "high",
      "created_at": "2026-11-18T18:00:00Z"
    }
  ],
  "next_cursor": null
}
```

Orden predeterminado: `created_at DESC, id DESC`. Desde P1.9, `neighborhood_id` opcional filtra incidentes cuyo punto tuvo una coincidencia espacial única. Sin filtro se incluyen también los incidentes sin colonia asignada. Errores: `401`, `403`, `422`, `503`.

### `GET /api/v1/incidents/map`

Solo funcionario activo. Parámetro obligatorio `bbox=min_longitude,min_latitude,max_longitude,max_latitude`; acepta los filtros de incidentes salvo `cursor`. El dashboard pide `scope=active` para ocultar los finalizados del mapa operativo. Respuesta `200`:

```json
{
  "items": [
    {
      "id": "44444444-4444-4444-8444-444444444444",
      "latitude": 21.8818,
      "longitude": -102.2916,
      "category_code": "fuga_agua",
      "priority_score": 60.0,
      "priority_level": "high",
      "status": "reported"
    }
  ],
  "truncated": false
}
```

Se exigen cuatro coordenadas ordenadas, un área máxima configurada y un máximo inicial de 500 marcadores; `truncated: true` avisa que hay más resultados y el dashboard debe acercar el mapa. No incluye reportes, fotos ni identidad. Errores: `401`, `403`, `422`, `503`. En FastAPI la ruta estática `/map` debe registrarse antes de `/{id}`.

En P0.8 el límite configurado es `MAP_MAX_BBOX_SPAN=0.8`: cada eje de la caja puede abarcar como máximo 0,8 grados. Si la vista excede el límite, la API devuelve `422` y el dashboard pide acercar el mapa.

### `GET /api/v1/incidents/{id}`

Solo funcionario activo del municipio. Respuesta `200`:

```json
{
  "id": "44444444-4444-4444-8444-444444444444",
  "category": { "code": "fuga_agua", "name": "Fuga de agua" },
  "title": "Fuga de agua",
  "description": "Fuga de agua en la calle",
  "location": { "latitude": 21.8818, "longitude": -102.2916 },
  "severity": "high",
  "status": "reported",
  "row_version": 1,
  "reports_count": 1,
  "confirmations_count": 1,
  "priority": {
    "score": 60.0,
    "level": "high",
    "version": 1,
    "factors": { "G": 75, "T": 0 },
    "weights": { "G": 0.8, "T": 0.2 },
    "calculated_at": "2026-11-18T18:00:00Z"
  },
  "status_history": [
    { "previous_status": null, "new_status": "reported", "notes": null, "created_at": "2026-11-18T18:00:00Z", "changed_by": null, "changed_by_label": "Sistema" }
  ],
  "photos": [
    { "id": "55555555-5555-4555-8555-555555555555", "url": "https://…/storage/v1/object/sign/…", "created_at": "2026-11-18T18:00:00Z" }
  ],
  "created_at": "2026-11-18T18:00:00Z",
  "updated_at": "2026-11-18T18:00:00Z"
}
```

`reports_count` proviene de reportes existentes; `confirmations_count` cuenta sesiones anónimas que confirmaron por separado. Ninguno lo envía el cliente y las confirmaciones no cambian estado, gravedad ni prioridad. Cada cambio de estado hecho por un funcionario devuelve `changed_by` y `changed_by_label` (correo de su cuenta Auth) únicamente en este detalle privado; la creación inicial aparece como `Sistema`. La identidad del funcionario se consulta desde Auth y no se copia a los datos territoriales. `photos` puede ser `[]`; si hay imágenes, contiene enlaces de Storage válidos por 300 segundos, creados solo después de comprobar el municipio del funcionario. No se devuelven `reporter_id`, `user_id` de confirmaciones ni rutas internas del bucket. La respuesta lleva `Cache-Control: no-store`; el dashboard usa `referrerPolicy="no-referrer"` para las imágenes. Quien reciba un enlace temporal puede usarlo mientras siga vigente, por lo que la demo usa exclusivamente fotos ficticias. No se muestra un porcentaje de confianza del LLM. Errores: `401`, `403`, `404`, `422`, `503`.

### `PATCH /api/v1/incidents/{id}/status`

Solo funcionario activo del municipio. Entrada JSON:

```json
{ "status": "in_review", "notes": "Revisión inicial", "expected_version": 1 }
```

Respuesta `200`:

```json
{
  "id": "44444444-4444-4444-8444-444444444444",
  "status": "in_review",
  "row_version": 2,
  "updated_at": "2026-11-18T18:05:00Z"
}
```

Transiciones P0: `reported → in_review|discarded`; `in_review → confirmed|discarded`; `confirmed → in_progress|discarded`; `in_progress → resolved|in_review`. `resolved` y `discarded` son finales y de solo lectura; cualquier PATCH posterior devuelve `409`. Descartar no elimina el registro: conserva el historial para auditoría y permite distinguir un reporte rechazado de uno nunca recibido. `notes` admite hasta 500 caracteres y no debe contener datos personales. `expected_version` impide sobrescribir un cambio de otro funcionario. Estado e historial se actualizan en una transacción. Errores: `401`, `403`, `404`, `409` (transición o versión), `422`, `503`.

### `GET /api/v1/dashboard/metrics`

Solo funcionario activo. Parámetros opcionales `from`, `to`, `category_id`. Respuesta `200`:

```json
{
  "reports_total": 12,
  "incidents_active": 9,
  "critical": 1,
  "pending": 5,
  "in_progress": 2,
  "resolved": 2,
  "discarded": 1
}
```

`active` excluye `resolved` y `discarded`; `pending` incluye `reported`, `in_review` y `confirmed`; `critical` cuenta incidentes activos con nivel crítico. Todos los valores se calculan con los mismos filtros y municipio. Errores: `401`, `403`, `422`, `503`.

### `GET /api/v1/dashboard/priorities`

Solo funcionario activo. Parámetros opcionales `category_id`, `status`, `limit`, `cursor`. Respuesta `200`:

```json
{
  "items": [
    {
      "incident_id": "44444444-4444-4444-8444-444444444444",
      "title": "Fuga de agua",
      "score": 60.0,
      "level": "high",
      "version": 1,
      "factors": { "G": 75, "T": 0 },
      "weights": { "G": 0.8, "T": 0.2 }
    }
  ],
  "next_cursor": null
}
```

Orden descendente por puntuación vigente, calculada al consultar, y después por `id`. La versión 1 usa `0.8G + 0.2T`; los pesos y umbrales están documentados en `data-model.md`. Errores: `401`, `403`, `422`, `503`.

## 3. Extensiones P1, fuera del contrato ejecutable P0

| Método y ruta | Permiso | Entrada y respuesta | Validación y errores |
|---|---|---|---|
| `POST /api/v1/reports/{id}/photos` (implementado) | Ciudadano autor del reporte | `multipart/form-data` con `photo`; `201 { "photo_id": "uuid" }`. | JPEG/PNG real, hasta 5 MB por archivo y dos fotos por reporte; se elimina EXIF. `401` sin sesión, `403` para funcionario, `404` para reporte ajeno o inexistente, `413` por tamaño, `415` por tipo, `422` por entrada dañada, UUID inválido o límite de fotos, `503` por Storage/DB. Un fallo no elimina el reporte. |
| `GET /api/v1/neighborhoods` (implementado) | Funcionario activo del municipio | `200 { "items": [{ "id": "uuid", "name": "…", "settlement_type": "…", "source_key": "0100100010001", "postal_code": "20263", "incidents_count": 2 }] }`, primero los asentamientos con más incidentes activos; sin geometrías. `postal_code` puede ser `null` y el conteo excluye resueltos y descartados. | `401` sin sesión, `403` sin rol, `503` por base de datos. Solo devuelve su municipio. |
| Filtro `neighborhood_id` en `GET /incidents` y `GET /incidents/map` (implementado) | Funcionario activo | UUID opcional; misma respuesta que sin filtro. Se combina con `scope`, `bbox` y los demás filtros. | `422` si el UUID está mal formado; un UUID válido sin incidentes del municipio devuelve lista vacía. |

## 4. Extensiones P2

### `GET /api/v1/incidents/nearby` (implementado)

Exige sesión ciudadana anónima. Recibe `latitude` y `longitude` por query; acepta solo el área aproximada de la demo. Devuelve hasta 10 incidentes activos del municipio a un máximo de 1 km, ordenados por distancia. Excluye los incidentes que esa sesión ya reportó. Respuesta `200`:

```json
{ "items": [{ "id": "44444444-4444-4444-8444-444444444444", "category_name": "Fuga de agua", "distance_m_approx": 150, "reported_on": "2026-11-19", "confirmations_count": 1, "confirmed_by_me": false }] }
```

La distancia se redondea a intervalos de 50 m. No devuelve coordenadas del incidente, descripción, fotografías ni identidad de quien lo reportó. `Cache-Control: no-store`. Errores: `401` sin sesión, `403` para funcionario, `422` por coordenadas inválidas/fuera de la demo y `503` por base de datos.

### `POST /api/v1/incidents/{id}/confirmations` (implementado)

Exige sesión ciudadana anónima. Recibe JSON `{ "latitude": 21.8818, "longitude": -102.2916 }` obtenido del GPS actual; no almacena ese punto. Registra una confirmación solo si el incidente está activo y a 1 km o menos de ese punto. Respuesta nueva `201`:

```json
{ "incident_id": "44444444-4444-4444-8444-444444444444", "confirmed": true, "confirmations_count": 1 }
```

Repetirla con la misma sesión devuelve `200` con la misma estructura sin agregar otra fila. `user_id` se toma del token y nunca aparece en la respuesta. Errores: `401` sin sesión, `403` para funcionario, `404` si no existe el incidente de la demo, `409` si está resuelto/descartado o si la misma sesión creó un reporte vinculado, `422` para ID o GPS inválido, GPS fuera de la demo o distancia mayor a 1 km, y `503` si falla PostgreSQL. La unicidad se garantiza en la base con `UNIQUE (incident_id, user_id)`. La confirmación no cambia gravedad, estado ni prioridad. Una sesión anónima nueva puede confirmar de nuevo; por ello el conteo representa **sesiones únicas**, no personas verificadas. La búsqueda y el botón se comprobaron en Expo Go.

### Extensiones todavía pendientes

- Sugerencia y consolidación de duplicados: primero se valida categoría, distancia y tiempo con casos reales de prueba; una unión conserva auditoría y cada reporte original.
- WhatsApp, pgvector y órdenes de trabajo no tienen rutas reservadas en esta versión para evitar un contrato ficticio.

## 5. Pruebas contractuales necesarias cuando exista código

1. Ciudadano crea un reporte tradicional, consulta solo el suyo y no puede leer el de otra sesión.
2. Voz devuelve propuesta editable; fallo de Whisper devuelve `manual_fallback` y no crea filas.
3. Reenvío con el mismo `client_request_id` no duplica reportes ni incidentes.
4. Ciudadano recibe `403` en dashboard, mapa y cambio de estado; funcionario inactivo también.
5. Funcionario ve mapa, detalle, métricas y factores de prioridad del mismo municipio; `PATCH` con versión antigua da `409` y conserva historial correcto.
6. Entradas fuera de catálogo, coordenadas inválidas, textos con correo/teléfono y archivos grandes se rechazan con el error documentado.

Hasta ejecutar estas pruebas, los contratos permanecen **documentados**, no verificados.
