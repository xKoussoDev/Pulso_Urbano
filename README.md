# Plataforma de Inteligencia Urbana

Monorepositorio del prototipo para Aguascalientes capital. El backend valida sesiones, registra reportes y sirve incidentes a funcionarios. Las nueve funciones P0 se comprobaron: formulario tradicional, voz con sugerencias editables de Gemini, revisión ciudadana, GPS, persistencia, dashboard privado, mapa, detalle y estado, y prioridad explicable. Los estados «Resuelto» y «Descartado» son finales y de solo lectura.

## Estructura

- `mobile/`: app ciudadana con Expo, React Native y TypeScript.
- `dashboard/`: dashboard web con React, TypeScript y Vite.
- `backend/`: API local con FastAPI.
- `database/migrations/` y `database/seeds/`: migraciones inicial, fotografías y polígonos P1. Se aplicaron a Supabase y se comprobaron tablas, índices y permisos.
- `docs/`: diseño de datos y contratos HTTP.
- `PROJECT_STATUS.md`: avance comprobado y siguiente tarea.

## Requisitos comprobados en este equipo

Node.js 26.13.0, npm 11.20.0, Python 3.14.7 y Git 2.51.0. Expo recomienda Node.js LTS; si aparece una incompatibilidad con Node 26, usar Node LTS antes de modificar el proyecto. Para probar en un teléfono se necesita Expo Go y que el teléfono esté en la misma red que la computadora. `adb` no se detectó en PATH, por lo que no se ha probado un emulador Android.

## Variables de entorno

Cada aplicación tiene su propio `.env.example`. Cópialo como `.env` dentro de esa carpeta y reemplaza los valores vacíos o de ejemplo. `.env` se ignora por Git.

- `mobile/` y `dashboard/` solo reciben la **clave publicable** de Supabase y la URL del proyecto. Los prefijos `EXPO_PUBLIC_` y `VITE_` hacen que esos valores sean visibles en la aplicación; nunca pongas ahí una clave secreta. En `mobile/.env`, `EXPO_PUBLIC_SUPABASE_PUBLISHABLE_KEY` debe comenzar con `sb_publishable_`.
- `backend/` guarda `SUPABASE_SECRET_KEY` y `SUPABASE_DB_URL`. Para esta última, usa la URL completa **Session pooler** de Supabase (puerto 5432); codifica caracteres especiales de la contraseña para una URL, por ejemplo `@` como `%40`. Solo el proceso local del backend puede leer estos valores.
- `EXPO_PUBLIC_API_URL` debe contener la IP de la computadora en la red local. `localhost` en el teléfono apuntaría al propio teléfono.
- `CORS_ORIGINS` debe incluir las direcciones desde las que se abre el dashboard. CORS limita navegadores; no sustituye la autenticación.
- `VITE_MAPBOX_TOKEN` es un token **público** de Mapbox (`pk.`) usado solo para dibujar el mapa; nunca pongas un token secreto (`sk.`) en el dashboard.
- `GEMINI_API_KEY` se guarda solo en `backend/.env`. El backend usa `gemini-3.1-flash-lite` del nivel gratuito para ejemplos ficticios. Sin clave o si falla la cuota, el usuario conserva el formulario manual. El nivel gratuito puede usar las entradas para mejorar productos de Google; no envíes información personal.

La API REST de Supabase respondió HTTP 200 en una prueba de solo lectura. PostgreSQL y el esquema inicial se comprobaron; aún faltan las pruebas de autorización con cuentas reales de prueba. La ruta de salud comprueba solamente FastAPI.

## Ejecutar en PowerShell

En terminales separadas:

```powershell
cd D:\HAKATONup\backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Comprobar: `http://localhost:8000/api/v1/health` debe responder `{"status":"ok"}`.

```powershell
cd D:\HAKATONup\dashboard
npm install
Copy-Item .env.example .env
npm run dev -- --host 0.0.0.0
```

Abrir `http://localhost:5173` para iniciar sesión como funcionario y consultar mapa, listas y detalles.

```powershell
cd D:\HAKATONup\mobile
npm install
Copy-Item .env.example .env
npm start -- --lan
```

Abrir el código QR con Expo Go. El flujo tradicional se probó en el teléfono. El servidor debe anunciar una dirección de la red local; si el firewall la bloquea, permitir el puerto de desarrollo solo en la red privada. La app solicita permiso GPS al tocar «Obtener ubicación» y solo guarda un reporte al confirmar en la pantalla de revisión. «Reporte mediante voz» graba un audio ficticio, lo envía a FastAPI para transcripción local, coloca texto y sugerencias de categoría, duración y gravedad en campos editables y borra el archivo temporal al terminar. El usuario probó en iPhone la corrección de esos campos, revisión y envío; una consulta de solo lectura confirmó el reporte de voz en PostgreSQL.

La demo local puede transportar tokens por HTTP en la red interna. Usaremos cuentas y reportes ficticios; antes de aceptar datos reales sería necesario HTTPS y otra revisión de seguridad.

`backend/requirements.txt` enumera las dependencias directas; `backend/requirements.lock` fija también sus dependencias internas para reproducir el entorno probado.

Para preparar Storage P1 en otro proyecto, aplica `database/migrations/20261119000000_report_photos.sql` en SQL Editor y ejecuta desde `backend/` `.\.venv\Scripts\python.exe -m scripts.setup_photo_bucket`. El script verifica que el bucket siga siendo privado y admita solo JPEG/PNG de hasta 5 MB. FastAPI expone `POST /api/v1/reports/{id}/photos` para el autor. La app móvil permite elegir o tomar hasta dos fotos ficticias, revisarlas y subirlas tras guardar el reporte. El detalle privado del dashboard muestra las fotos mediante enlaces temporales de 300 segundos creados solo para funcionarios del municipio; el flujo se comprobó con una foto ficticia enviada desde iPhone.

Para importar la capa oficial de colonias y otros asentamientos de Aguascalientes, consulta `docs/neighborhood-source.md`. Las migraciones `20261119010000_neighborhoods.sql` y `20261119020000_neighborhood_postal_code.sql` y el importador ya se aplicaron y verificaron con 1 020 polígonos.

Los reportes nuevos también reciben `neighborhood_id` automáticamente cuando su ubicación tiene una sola coincidencia espacial. La prueba de integración se ejecuta desde `backend/` con `$env:RUN_NEIGHBORHOOD_INTEGRATION='1'; .\.venv\Scripts\python.exe -m unittest tests.test_neighborhood_report -v` y elimina sus reportes ficticios al terminar. El dashboard incluye un filtro privado por «Colonia o asentamiento» para lista y mapa y búsqueda local de opciones por nombre o CP. La búsqueda y el filtro se comprobaron en navegador.

P2.1 agregó `database/migrations/20261119030000_incident_confirmations.sql` y `POST /api/v1/incidents/{id}/confirmations`. El backend ya comprueba una confirmación por sesión e incidente, excluye al autor de un reporte y rechaza incidentes finalizados. Para repetir la prueba ficticia y limpiar su fila temporal: desde `backend/`, `$env:RUN_CONFIRMATION_INTEGRATION='1'; .\.venv\Scripts\python.exe -m unittest tests.test_incident_confirmations -v`.

P2.2 añadió `GET /api/v1/incidents/nearby` y la pantalla «Ver incidentes cercanos» en Expo Go. El POST de confirmación requiere JSON con latitud y longitud actuales y comprueba un radio de 1 km; esa ubicación no se guarda en confirmaciones. TypeScript, lint, bundle iOS y la prueba backend pasaron. El usuario comprobó búsqueda y confirmación en iPhone; PostgreSQL registró una confirmación demo. El conteo en dashboard sigue pendiente.

Para la prueba de confirmaciones se crearon cinco reportes ficticios en zonas distintas mediante `backend/scripts/seed_confirmation_demo.py`. Sus descripciones empiezan con `[DEMO CONFIRMACIONES]` y sus títulos con `[DEMO]` para reconocerlos en el listado. El manifiesto local `backend/.confirmation_demo_seed.json` guarda los IDs sin credenciales y se ignora por Git. El script se niega a repetir la carga si el manifiesto existe, para evitar duplicados. Una de las ubicaciones está cerca de un reporte anterior, de modo que una sesión distinta puede verla desde «Ver incidentes cercanos» si el teléfono está en esa zona.

El detalle privado del dashboard muestra `confirmations_count` separado de `reports_count`. Una prueba real confirmó que el agregado coincide con PostgreSQL y no expone identidad ciudadana; el usuario verificó en navegador una confirmación del incidente demo y la nota de que no cambia la prioridad.

