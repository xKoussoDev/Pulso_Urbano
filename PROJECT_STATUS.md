# Estado del proyecto: Plataforma de Inteligencia Urbana

**Actualizado:** 19 de noviembre de 2026  
**Fase:** P2 — confirmaciones independientes comprobadas de extremo a extremo  
**Avance funcional verificado:** 9 de 9 funciones P0  
**Tiempo de implementación previsto:** dos días intensivos, aproximadamente 20 horas efectivas  
**Tiempo restante:** sin estimación fiable hasta medir horas efectivas de P0  
**Próxima tarea:** revisión final de la demo y sus datos ficticios, o la siguiente funcionalidad que el usuario priorice.

## Publicación de la versión 2 — 19 de noviembre de 2026

La versión 2 reúne el rediseño de móvil y dashboard, la bienvenida, la voz desde el primer paso, el logo de ciudad y pulso, las mejoras de formulario y grabación, y el conteo de incidentes activos por colonia. La publicación se identifica con la etiqueta Git `v2.0.0`. Antes de preparar el commit se verificó que los archivos `.env` siguen ignorados y que los archivos previstos no contienen patrones de credenciales.

## Logo de Pulso Urbano — 19 de noviembre de 2026

Se adaptó el logo aportado por el usuario (ciudad y pulso) a azul marino `#142641` y cian `#00A6BC`. El símbolo sustituye al icono anterior en la bienvenida, el encabezado móvil y web, la pestaña web y los indicadores de carga. Se preparó una versión transparente para el icono adaptable Android. La frase de bienvenida y la lógica de las pantallas no cambiaron.

**Verificación:** `npx tsc --noEmit` y `npm run lint` pasaron en móvil; `npm run build` y `npm run lint` pasaron en dashboard. El usuario confirmó que el logo se ve bien en la bienvenida, el formulario, el panel y las cargas tras reiniciar Expo y recargar el dashboard. El icono de la aplicación instalada requiere una nueva compilación para verse fuera de Expo Go.

## Bienvenida, voz inicial y hover de incidentes — 19 de noviembre de 2026

`mobile/WelcomeScreen.tsx` muestra PULSO URBANO, la frase solicitada y el icono anterior de la app con una sola animación. Se quitó el segundo personaje de carga simultáneo; si la carga inicial tarda más, aparece un mensaje breve hasta que termine. `mobile/App.tsx` mantiene la bienvenida aproximadamente 1,5 segundos y sale con un desvanecimiento que respeta movimiento reducido. El mismo grabador de `mobile/VoiceRecorder.tsx` se movió al bloque 01, conserva el servicio de transcripción/IA y ahora permite cancelar y borrar el audio sin procesarlo. Los campos de categoría y descripción siguen editables, con selección manual y revisión antes de enviar. `dashboard/src/App.css` deja el título oscuro y coloca su regla de hover, foco y pulsación después del estilo general de botones para que el fondo azul tenue no sea sobrescrito.

**Verificación:** `npx tsc --noEmit` y `npm run lint` pasaron en móvil; `npm run build` y `npm run lint` pasaron en dashboard tras la corrección. El usuario comprobó en Expo Go que voz inicial, extracción, edición, cancelación y selección manual funcionan. También confirmó que la bienvenida corregida muestra un solo logo y pasa al formulario. Queda pendiente comprobar visualmente el hover/foco corregidos con sesión real en el dashboard; no se marca ese ajuste como terminado hasta esa comprobación.

## Rediseño UI/UX de Pulso Urbano — 19 de noviembre de 2026

Se analizaron las cuatro referencias entregadas y las pantallas actuales. La identidad y sus decisiones están en `docs/design-system.md`: azul marino y cian, violeta moderado, superficies claras, tipografía del sistema, botones grandes, tarjetas con jerarquía y colores de estado con texto. Móvil agrupó el formulario en problema, descripción, fotografías y ubicación, conservando voz, revisión, envío y confirmaciones cercanas. El dashboard reorganizó filtro y mapa, mejoró tabla, detalle e inicio de sesión, y agregó estados de carga reales. El indicador “cuadra” animado se implementó en ambos clientes y respeta movimiento reducido. Se creó un icono original de la misma cuadra para móvil y dashboard. No hubo cambios de API ni base de datos para este rediseño, ni se instalaron dependencias.

**Comprobaciones:** `npx tsc --noEmit` y `npm run lint` pasaron en móvil; la exportación iOS final incluyó el nuevo icono y pasó fuera del aislamiento porque Hermes no pudo escribir en la carpeta temporal del sandbox. `npm run build` y `npm run lint` pasaron en el dashboard. Una captura headless a 768 px mostró el acceso completo; la captura a 375 px quedó recortada por el viewport mínimo de Chrome headless y no permitió medir el diseño a ese ancho. El usuario comprobó en el navegador, con sesión real, filtro, mapa, tabla, detalle y regreso a la lista. En iPhone comprobó que todos los controles se ven completos y que un reporte ficticio con voz, foto, GPS y revisión se registra con folio. No se observaron regresiones en esas pruebas. El icono de inicio como aplicación instalada aún no se ha probado; Expo Go y el bundle sí cargan el nuevo recurso.

## Conteo de incidentes activos por colonia — 19 de noviembre de 2026

`GET /api/v1/neighborhoods` ahora cuenta solo incidentes cuyo estado no sea `resolved` ni `discarded`; los conserva en la lista de finalizados. El selector del dashboard indica explícitamente «incidente(s) activo(s)» y el contrato en `docs/api.md` refleja el criterio. Se amplió la prueba de integración para comparar el conteo de una colonia contra PostgreSQL, priorizando una con incidentes finalizados.

**Verificación:** `npm run build` y `npm run lint` pasaron en el dashboard. `tests.test_neighborhood_filter` pasó contra la base de demo con acceso de red: el conteo del catálogo coincidió con el número de incidentes activos. Tras recargar y buscar «UNIVERSIDAD BONATERRA», el usuario confirmó que el selector muestra «incidentes activos» y excluye finalizados. No se cambió el filtro de la lista ni del mapa.

## Ajuste del formulario y la grabación — 19 de noviembre de 2026

Se actualizó `mobile/App.tsx` para pedir categoría, descripción, gravedad elegida y ubicación GPS antes de abrir la revisión. Si falta alguno, aparece la alerta exacta solicitada. «¿Desde cuándo?» y fotografías siguen siendo opcionales. Se quitó el aviso inicial de demo y se acortaron instrucciones y mensajes técnicos. `mobile/VoiceRecorder.tsx` limita la grabación a 10 segundos tanto en Expo Audio como en el temporizador de respaldo; conserva el envío al detenerla antes y la eliminación del archivo temporal. `backend/app/voice_routes.py` rechaza audio que supere 10 segundos y se ajustó la prueba correspondiente.

**Verificación:** `npx tsc --noEmit` y `npm run lint` pasaron en móvil; las seis pruebas de `tests.test_voice_routes` pasaron en backend, incluido el rechazo de 11 segundos. La búsqueda del código fuente relacionado no encontró textos ni límites de grabación de 30 segundos. En Expo Go, el usuario confirmó que la alerta exacta aparece sin avanzar de pantalla; una grabación se detuvo sola a los 10 segundos y otra se detuvo manualmente antes del límite. Ambas se transcribieron y dejaron editar la descripción. No quedan errores conocidos de este ajuste.

## Estado inicial

El repositorio contenía `PLAN.md` y los tres documentos de diseño. En P0.1 se inicializó Git y se crearon las bases de Expo, Vite y FastAPI. En P0.3 se aplicó la migración inicial de tablas y catálogos. En ese momento las funciones P0 todavía no existían; los avances posteriores se registran abajo.

## Preparación para GitHub

El usuario pidió subir el monorepositorio a GitHub. Se detectó un `.git` interno creado por la plantilla de `mobile/`; su historial se conservó en `.mobile-git-backup/`, ignorado por el repositorio principal. La app móvil quedó preparada como archivos normales del monorepo. Se excluyeron `.env`, el manifiesto local de los cinco reportes demo, dependencias, salidas de compilación y archivos de IDE. Se revisaron los 80 archivos preparados: no se detectaron claves reales; `.env.example` solo contiene variables vacías y una URL de formato con contraseña de marcador de posición. El primer commit local `437fcb1` se subió a la rama `main` de `https://github.com/xKoussoDev/Pulso_Urbano.git`; `git ls-remote` confirmó el mismo hash en GitHub y el árbol local limpio. El remoto `origin` quedó configurado para futuros cambios.

| Elemento | Estado | Evidencia pendiente |
|---|---|---|
| Arquitectura y alcance | Aprobados por el usuario | Ninguna para P0.1 |
| Esquema de base de datos | Migración inicial aplicada y comprobada | Pruebas de integración y políticas con usuarios reales de prueba en tareas posteriores |
| Contratos de API | Documentados; rutas implementadas por bloques | Rutas restantes y pruebas de integración posteriores |
| Base móvil Expo + TypeScript | Formulario, GPS, revisión y envío comprobados en Expo Go | Voz y consultas futuras |
| Base dashboard React + TypeScript | Acceso privado y lista implementados; build y lint pasan | Prueba funcional en navegador con cuenta autorizada |
| Base backend FastAPI | Auth, categorías, registro y listado privado comprobados | Mapa, detalle, estado, métricas e IA posteriores |

## Registro de P0.7 — dashboard privado en verificación

Se creó `backend/app/incident_routes.py` con `GET /api/v1/incidents`: exige funcionario activo y filtra por su municipio; admite filtros documentados y paginación por cursor. Calcula la puntuación actual a partir de gravedad y tiempo abierto con los pesos configurados. `backend/app/main.py` incorpora la ruta. En el dashboard se añadió `src/supabase.ts`, se reemplazó la plantilla de `src/App.tsx` por inicio de sesión, comprobación de rol, listado y cierre de sesión, y se simplificaron los estilos. Se instaló `@supabase/supabase-js` con versión exacta y se configuró `dashboard/.env` con **solo** URL y clave publicables, además de la URL LAN de FastAPI.

**Pruebas realizadas:** un funcionario ficticio temporal obtuvo dos incidentes del municipio. `priority_level=high` filtró el listado y un cursor inválido devolvió `422`. Con `limit=1`, dos páginas devolvieron IDs distintos. Una sesión ciudadana recibió `403`. Al cambiar temporalmente al funcionario a otro municipio ficticio, el listado devolvió cero incidentes; se eliminaron cuentas y municipio temporales. `npm run build` y `npm run lint` pasaron. Vite existente en `localhost:5173` sirve el código nuevo y la solicitud CORS previa hacia FastAPI respondió `200` con ese origen permitido.

**Cuenta de demo:** el usuario creó `funcionario.demo@example.invalid` en Supabase Auth con contraseña privada. Se comprobó que es una cuenta única, confirmada y no anónima, y se vinculó a Aguascalientes capital en `private.staff_members`. Queda pendiente comprobar que el usuario inicia sesión y ve la lista en el navegador, y que puede cerrar sesión. P0.7 aún no se marca terminado.

**Cierre de P0.7:** el usuario confirmó en `http://localhost:5173/` que inició sesión, vio «Incidentes del municipio» con los reportes ficticios y que «Cerrar sesión» devolvió el formulario de acceso. FastAPI registró `GET /auth/me` y `GET /incidents?limit=20` con HTTP 200 desde el navegador. P0.7 quedó comprobado; mapa, detalle, cambio de estado y explicaciones de prioridad siguen pendientes.

## Registro de P0.8 — mapa en verificación

Se agregó `GET /api/v1/incidents/map` en `backend/app/incident_routes.py`: exige funcionario activo, consulta solo su municipio, filtra por caja geográfica (`bbox`) y admite filtros del listado. Rechaza coordenadas inválidas y vistas demasiado amplias; el máximo configurable por eje es `MAP_MAX_BBOX_SPAN` (0,8 grados iniciales). Devuelve hasta 500 marcadores sin identidad ni descripción personal y `truncated` si existen más. En el dashboard se añadió `src/IncidentMap.tsx` con Mapbox GL JS y marcadores por prioridad; carga el módulo solo después de autorizar al funcionario y vuelve a consultar al mover o acercar la vista. `dashboard/.env.example` incluye `VITE_MAPBOX_TOKEN` público. El usuario lo configuró localmente; se comprobó que empieza con `pk.` y que Mapbox respondió HTTP 200 al solicitar el estilo.

**Pruebas backend:** con un funcionario temporal, una caja que contiene la zona devolvió dos puntos, otra fuera devolvió cero, cajas inválidas y demasiado grandes devolvieron `422`, y un ciudadano recibió `403`. Se eliminaron las cuentas temporales. TypeScript/build y lint del dashboard pasaron. Mapbox ocupa un chunk grande (aprox. 1,9 MB) que se carga de forma diferida tras iniciar sesión. **Pendiente:** verificar que el navegador muestra mapa y marcadores y que actualizar la vista consulta nuevos puntos. P0.8 aún no se marca terminado.

**Prueba visual y corrección:** el usuario confirmó que el mapa funciona y responde al movimiento, pero dos reportes cercanos se empalmaban y parecía verse solo uno. Se modificó `dashboard/src/IncidentMap.tsx` para agrupar marcadores separados por menos de 36 píxeles en pantalla: el círculo muestra la cantidad y el popup enumera los incidentes. No se cambian coordenadas almacenadas. Build y lint pasaron después del cambio. Falta la confirmación visual del usuario de que ambos incidentes son accesibles.

**Cierre de P0.8:** tras recargar el dashboard, el usuario confirmó que el marcador con «2» aparece y que al pulsarlo ve ambos incidentes. FastAPI registró varias consultas `GET /incidents/map` con HTTP 200 al mover o acercar la vista. El mapa y la agrupación quedaron comprobados en navegador. Las coordenadas de la base no se modificaron.

## Registro de P0.9 — detalle, estado y prioridad comprobados

Se agregaron `GET /api/v1/incidents/{id}` y `PATCH /api/v1/incidents/{id}/status` en `backend/app/incident_routes.py`. El detalle exige funcionario activo del mismo municipio y devuelve estado, descripción confirmada, ubicación, conteo de reportes, historial y prioridad vigente con factores `G/T`, pesos y versión. El PATCH bloquea la fila, comprueba `expected_version` y las transiciones aprobadas, rechaza notas con correo/teléfono detectables y actualiza estado e historial en una transacción. Al reabrir un incidente resuelto o descartado reinicia `opened_at` y registra el nuevo cálculo de prioridad. El dashboard añadió `src/IncidentDetail.tsx`; se puede abrir desde lista o marcador, ver la explicación y cambiar estado.

**Pruebas backend:** con cuentas y reporte ficticios temporales, el detalle devolvió `200`, prioridad `60.0` con `G=75`, y la sesión ciudadana recibió `403`. Un funcionario asignado a otro municipio recibió `404`. La secuencia `reported → in_review → confirmed → in_progress → resolved → in_review` devolvió `200` y terminó en `row_version=6`, seis filas de historial de estado y dos de prioridad. Versión antigua y transición inválida devolvieron `409`; nota con correo devolvió `422`. Se eliminaron los datos temporales. Build y lint del dashboard pasaron; CORS permitió el preflight de PATCH con HTTP 200. **Pendiente:** prueba visual del usuario en navegador, incluido cambio de estado y actualización de la lista.

**Confirmación del usuario y ajuste:** el usuario vio factores G/T y pesos, cambió el estado en el dashboard y observó que «Resuelto» y «Descartado» ofrecían volver a «En revisión». Se decidió que ambos sean finales para esta demo. `GET /incidents` admite `scope=active|closed`; el dashboard presenta «Activos» y «Completados y descartados», y el mapa muestra solo activos. El detalle finalizado no presenta controles de edición. El historial ahora muestra la cuenta Auth del funcionario que cambió el estado; la creación inicial aparece como «Sistema». Descartar conserva el registro y el historial por trazabilidad.

**Pruebas del ajuste:** dos incidentes temporales recorrieron las rutas hasta `discarded` y `resolved`. Ambos aparecieron en la lista cerrada, no en la activa ni en el mapa activo; un PATCH posterior devolvió `409`. El detalle devolvió el autor en el historial. Los dos incidentes temporales se eliminaron. Se corrigió una coma sobrante en el SQL detectada por la primera prueba; la repetición pasó. La prioridad de un descartado se congela al cerrarlo; las consultas reales de listas y mapa con ese cálculo respondieron `200`. `npm run build`, `npm run lint` y `compileall` pasaron. La prueba visual final se documenta en «Causa confirmada y cierre».

**Regresión reportada y corrección:** el usuario mostró un dashboard con sesión abierta, pero sin mapa ni listas. FastAPI `/health` respondió `200`. En `dashboard/src/App.tsx` el listener de Supabase borraba `role` en cualquier evento, incluso `INITIAL_SESSION` o `TOKEN_REFRESHED`; combinado con `getSession` podía dejar la interfaz sin rol y sin mensaje. Se usa ahora un solo listener para la sesión, se limpian datos privados solo al cerrar sesión o cambiar de usuario, y se añade «Verificando acceso» con reintento si falla la carga. Build y lint pasan; Vite sirve el `App.tsx` actualizado con HTTP 200. **Pendiente:** comprobar en el navegador que reaparecen mapa y tablas; hasta esa prueba no se da por cerrada la regresión.

**Causa confirmada y cierre:** la segunda captura mostró `Failed to fetch`. `dashboard/.env` apuntaba a `172.24.11.145`, dirección que dejó de responder al cambiar la red Wi-Fi; la computadora usa ahora `192.168.5.200`. FastAPI respondió `200` tanto en `localhost:8000` como en esa IP. Se actualizó `dashboard/.env` a `http://localhost:8000/api/v1` y `mobile/.env` a la nueva IP LAN. Vite sirvió el código actualizado con la nueva URL. El usuario confirmó que reaparecieron el mapa y ambas listas, y que un incidente finalizado se abre en modo de solo lectura. El ajuste de P0.9 queda probado; voz es la única función P0 pendiente.

## Registro de P0.10a — viabilidad de transcripción local

Se instalaron `faster-whisper==1.2.1` y sus dependencias en el entorno virtual del backend. Se eligió el modelo multilingüe `base` en CPU con cuantización `int8` para esta prueba. El modelo se descargó a `backend/.models`, carpeta excluida de Git. El equipo tiene 12 procesadores lógicos y Python 3.14.7; `pip check` no encontró dependencias rotas.

**Incompatibilidad encontrada y corregida:** la versión publicada 1.2.1 de `faster-whisper` llama a `av.open(..., metadata_errors=...)`, argumento eliminado en PyAV 19. La primera transcripción falló por ese motivo. Se fijó `av==18.0.0` en `backend/requirements.txt`, se regeneró `backend/requirements.lock` y se repitió la prueba.

**Resultado medido:** con una frase ficticia en inglés generada localmente en WAV, el modelo ya descargado cargó en 2.63 s y transcribió en 1.96 s con el texto esperado. La primera carga con descarga tardó 19.43 s antes del error de PyAV. Esta prueba valida instalación, decodificación e inferencia local; **no valida aún la precisión en español ni el audio `.m4a` real del iPhone**. No se integró voz al formulario, no se llamó Gemini y no se creó ningún reporte con IA.

## Registro de P0.10b — grabación móvil en verificación

Se creó `mobile/VoiceRecorder.tsx` como prueba aislada de micrófono. Solicita permiso al tocar el botón, graba hasta 30 segundos con `expo-audio`, muestra el tiempo y, al detener, comprueba existencia, extensión y tamaño con `expo-file-system`. Borra el archivo temporal antes de mostrar el resultado. `mobile/App.tsx` muestra esta prueba junto al formulario tradicional e impide pasar a revisión durante una grabación. Se instalaron `expo-audio` y `expo-file-system` con `expo install`; `mobile/app.json` declara el texto del permiso de micrófono en español. No se envía audio a FastAPI, no se llama Gemini y no se crean reportes de voz en este bloque.

**Pruebas realizadas:** `npx tsc --noEmit`, `npx expo lint` y exportación iOS pasaron. La primera exportación falló al escribir el archivo temporal de Hermes dentro del sandbox; la repetición autorizada pasó y generó el bundle iOS. **Pendiente:** prueba real del micrófono y del borrado en Expo Go. La función P0 de reporte mediante voz sigue pendiente.

**Cierre de P0.10b:** el usuario confirmó en su iPhone con Expo Go que una grabación ficticia mostró duración, archivo `.m4a`, tamaño y «Archivo borrado», y que el formulario tradicional seguía visible. Captura y limpieza local comprobadas. La función P0 de voz aún requiere transcripción, propuesta editable y envío confirmado.

## Registro de P0.10c — ruta de transcripción local comprobada

Se creó `backend/app/voice_routes.py` y se registró `POST /api/v1/ai/process-voice-report` en FastAPI. Exige una sesión ciudadana, acepta audio `.m4a`, limita el archivo a 10 MB y la duración decodificada a 30 segundos. Usa el modelo `base` de faster-whisper en CPU, con una sola transcripción simultánea. No guarda audio ni crea reportes. Sustituye patrones detectados de correo y teléfono antes de devolver el texto; la respuesta por ahora es `manual_fallback` con descripción editable porque Gemini aún no está conectado. Se añadió `python-multipart==0.0.34`, se actualizaron `requirements.txt`, `requirements.lock` y `docs/api.md`.

**Pruebas realizadas:** cuatro pruebas HTTP locales pasaron: sesión obligatoria, correo omitido y borrador editable, rechazo de formato/audio ilegible/archivo mayor de 10 MB, y rechazo de audio de 31 segundos. `pip check` y compilación Python pasaron. Una prueba adicional con el modelo real y un `.m4a` ficticio devolvió HTTP 200, transcripción no vacía y `EXTRACTION_UNAVAILABLE` en 18.79 s con carga inicial. `TestClient` se bloqueó dentro del sandbox incluso en `/health`; estas pruebas se repitieron fuera de él y pasaron. La muestra hablada era en inglés; falta comprobar precisión en español con audio ficticio del iPhone. No se llamó a Gemini ni se enviaron datos personales o reportes.

**Pendiente:** integrar el envío desde Expo Go, permitir corrección de los campos y confirmar un reporte de voz extremo a extremo. La función P0 de voz permanece pendiente.

## Registro de P0.10d — integración móvil en verificación

`mobile/VoiceRecorder.tsx` conserva el archivo `.m4a` hasta recibir respuesta de FastAPI y lo borra después, tanto en éxito como en error. Muestra un estado durante la transcripción. `mobile/App.tsx` envía el archivo como `multipart/form-data` con la sesión ciudadana anónima, limita la espera a 60 segundos y coloca la transcripción en la descripción editable. Solo ese campo se llena automáticamente; categoría, gravedad y GPS siguen requiriendo revisión del ciudadano. Cuando hay texto transcrito, el reporte final usa `input_method: voice`, pero se guarda solo al pulsar «Confirmar y enviar» en la pantalla de revisión. `README.md` describe el flujo actual.

**Pruebas realizadas:** `npx tsc --noEmit` y `npm run lint` pasaron. La exportación iOS falló dentro del sandbox porque Hermes no pudo escribir su archivo temporal; repetida fuera del sandbox, pasó y generó el bundle. Se confirmó en el código local de React Native que `FormData` acepta archivos con `{ uri, name, type }`. FastAPI no respondió desde el entorno de pruebas de esta sesión; hace falta verificarlo desde el teléfono en la red local. **Pendiente:** prueba real desde iPhone con FastAPI y Expo activos; hasta entonces no se marca P0.10d como comprobado ni se completa la función P0 de voz.

**Fallo observado en iPhone y ajuste:** el usuario recibió «No se pudo conectar con FastAPI» al intentar transcribir. La primera comprobación desde el sandbox dio un falso negativo; desde el sistema anfitrión `/health` respondió HTTP 200 por `localhost` y `192.168.5.200`, y OpenAPI confirmó la ruta de voz. Safari en el mismo iPhone mostró `{ "status": "ok" }`, así que la conexión básica por LAN funciona. Se reemplazó la subida con `fetch`/`FormData` por `File.upload` de `expo-file-system` en modo multipart nativo, manteniendo autorización, límite de espera y borrado. TypeScript, lint y exportación iOS fuera del sandbox pasan. La causa exacta del fallo de `fetch` no se midió en el dispositivo.

**Verificación parcial en iPhone:** tras reiniciar Metro, el usuario confirmó que la voz se transcribe y que aparece la confirmación de borrado del audio. Quedan por probar la corrección del texto, la pantalla de revisión, el envío y el método `voice` persistido.

**Cierre de P0.10d:** el usuario corrigió una palabra de la transcripción, revisó y envió un reporte ficticio desde Expo Go; confirmó que apareció «Reporte enviado» con ID de incidente. Una consulta de solo lectura a Supabase mostró que el reporte más reciente tenía `input_method: voice` y se había creado aproximadamente 94 segundos antes. El conector Supabase rechazó la consulta por permisos; la comprobación se hizo con la conexión PostgreSQL del backend fuera del sandbox, sin leer descripción ni datos personales. La transcripción, edición, borrado del audio y persistencia quedan comprobados. El reporte de voz todavía no propone categoría, duración ni gravedad mediante Gemini; por eso la función P0 de voz con IA sigue pendiente.

## Registro de P0.10e — extracción Gemini en verificación

Se añadió `backend/app/ai_extraction.py`. Usa el endpoint REST `generateContent` con el modelo `gemini-3.1-flash-lite`, documentado con nivel gratuito el 19 de noviembre de 2026. La clave se lee solo del entorno del backend; se añadió el campo vacío a `.env.example`. El modelo recibe únicamente texto ficticio transcrito, códigos/nombres de categorías activas y una instrucción para devolver JSON; no recibe audio, ubicación, token ciudadano ni identificadores. La descripción permanece como transcripción editable. Antes de llamar a Gemini, `voice_routes.py` bloquea patrones detectables de datos personales. El backend acepta categoría, duración y gravedad solo si son válidas y vienen con evidencia literal en el texto. Si falta la clave o falla la extracción, continúa el modo manual. Se fijó `httpx==0.28.1` como dependencia directa ya instalada.

**Pruebas locales:** nueve pruebas pasaron, incluidas ausencia de clave sin llamada externa, propuesta válida, descarte de duración/gravedad inventadas, bloqueo de texto con señal personal y respaldo manual ante fallo de Gemini. `pip check` y `compileall` pasaron. La app móvil aún no muestra categoría, duración ni gravedad sugeridas. El nivel gratuito puede usar las entradas para mejorar productos de Google, por lo que la demo debe usar solo reportes ficticios.

**Prueba real y cierre del backend P0.10e:** el usuario guardó `GEMINI_API_KEY` en `backend/.env`; se comprobó su presencia sin mostrarla. Una petición real inicial con un texto ficticio devolvió HTTP 403. Una petición diagnóstica mínima respondió HTTP 200 y la repetición de la extracción completa respondió HTTP 200: devolvió una categoría activa y duración/gravedad apoyadas en citas literales del texto. No se cambió código entre ambas peticiones; se desconoce la causa del 403 inicial y se conserva como error intermitente observado. La ruta mantiene `manual_fallback` si Gemini falla. No se enviaron audio, ubicación ni datos personales. P0.10e queda probado en backend; la función P0 de voz con IA aún requiere que la app muestre y permita corregir los campos sugeridos.

## Registro de P0.10f — sugerencias móviles en verificación

El usuario observó correctamente que el backend ya proponía categoría, gravedad y duración, pero `mobile/App.tsx` solo aplicaba la descripción. Se amplió el tipo de respuesta y ahora la app coloca `category_id`, `duration_text` y `severity_proposed` en los controles existentes cuando `mode=suggested` y los valores son válidos. Los controles siguen siendo editables. Un aviso persistente enumera los campos llenados inicialmente por IA y la pantalla de revisión vuelve a pedir que se confirmen. Si Gemini no propone algún dato, el formulario conserva la selección manual. No se cambió el envío final ni la regla de confirmar antes de guardar.

**Pruebas realizadas:** `npx tsc --noEmit`, `npm run lint` y exportación iOS pasaron. **Pendiente:** prueba en iPhone con una frase ficticia que mencione categoría, tiempo y gravedad; P0.10f y la novena función P0 siguen sin marcarse completas hasta esa prueba.

**Verificación parcial en iPhone:** el usuario confirmó que al decir «Hay una fuga de agua desde hace tres días. La gravedad es alta» se llenaron categoría, «¿Desde cuándo?» y gravedad, y que pudo editar los tres campos. Falta comprobar que los valores corregidos lleguen a la pantalla de revisión y se guarden al confirmar el reporte.

**Cierre de P0.10f y P0:** el usuario cambió «¿Desde cuándo?» tras una propuesta de Gemini, vio el valor corregido junto con categoría y gravedad en la revisión, confirmó el envío y recibió un ID de incidente. Una consulta PostgreSQL de solo lectura al reporte más reciente confirmó `input_method=voice`, categoría `fuga_agua`, duración presente, gravedad `high` y estado `reported`; no se leyeron descripción ni coordenadas. El formulario tradicional, la voz con propuesta editable, GPS, persistencia, dashboard, mapa, detalle/estado y prioridad explicable ya cuentan con prueba funcional. **P0: 9/9 funciones comprobadas.**

**Límites conocidos al cerrar P0:** una petición real a Gemini devolvió HTTP 403 y la repetición funcionó sin cambios; la ruta ofrece formulario manual si ocurre de nuevo. El filtro de datos personales detecta patrones, pero no garantiza anonimización total; la demo usa solo reportes ficticios. FastAPI se expone por HTTP en la red local y las claves siguen solo en el backend. Fotografías, filtro por colonia y confirmaciones independientes pertenecen a P1/P2.

## Registro de P1.1 — base de fotografías comprobada

El usuario autorizó continuar con P1. Se revisó el esquema y se comprobó que `public.report_photos` y el bucket `report-photos` no existían. Se creó la migración `database/migrations/20261119000000_report_photos.sql`, aplicada a Supabase, con FK a `reports`, ruta única, restricciones JPEG/PNG y tamaño máximo 5 MB, índice por reporte/fecha, RLS activo y ningún permiso directo para `anon` o `authenticated`. La carpeta `backend/scripts/setup_photo_bucket.py` crea o verifica de forma repetible el bucket privado con los mismos límites. El CLI de Supabase no está instalado y el proyecto no tiene `supabase_migrations.schema_migrations`; la migración se aplicó con la conexión PostgreSQL del backend. El bucket se creó mediante la API de Storage, de acuerdo con la restricción vigente sobre escrituras SQL directas en el esquema `storage`.

**Pruebas:** lectura posterior confirmó RLS activo, cero políticas sobre `report_photos`, `anon` y `authenticated` sin `SELECT`, `service_role` con `SELECT`, y bucket privado con límite 5 242 880 bytes y MIME `image/jpeg`/`image/png`. No se subieron archivos ni se modificaron reportes. **Pendiente:** endpoint de subida, acceso autorizado a imágenes y app móvil; la función P1 «Fotografías» todavía no está terminada.

## Registro de P1.2 — subida privada de fotografías comprobada

Se agregó `backend/app/photo_routes.py` y se registró en `backend/app/main.py` la ruta `POST /api/v1/reports/{id}/photos`. Exige sesión ciudadana y verifica en PostgreSQL que el reporte pertenezca a esa sesión. Acepta JPEG/PNG real de hasta 5 MB, como máximo dos fotos por reporte. Pillow reorienta y vuelve a guardar la imagen a 2048 píxeles de lado como máximo, sin metadatos EXIF. El archivo se sube al bucket privado; si falla la inserción de metadatos, se intenta borrar el archivo subido. La foto es opcional y un fallo no elimina el reporte ya creado. Se añadió Pillow 13.0.0 a las dependencias directas y fijadas.

**Pruebas:** 15 pruebas locales del backend pasaron; una prueba de integración adicional subió una imagen ficticia al Storage privado, comprobó la fila y los bytes descargados sin EXIF, y borró el archivo y la fila. La prueba de integración se omite en la suite normal y se activa con `RUN_PHOTO_INTEGRATION=1`. Se probaron 401 sin sesión, 404 si el reporte no pertenece al usuario, 413 por tamaño, 415 por formato, 422 por archivo dañado o límite de dos fotos, y limpieza al fallar la inserción. **Pendiente:** captura/subida desde Expo y lectura autorizada en dashboard; P1 «Fotografías» sigue en curso. En la demo se usarán solo fotos ficticias sin personas, placas u otros datos personales visibles: quitar EXIF no elimina información visible en los píxeles.

## Registro de P1.3 — app móvil en verificación

En `mobile/App.tsx` se añadió selección desde galería o cámara, hasta dos fotografías opcionales, vista previa, eliminación y revisión antes de confirmar. `expo-image-manipulator` prepara una copia JPEG de hasta 1600 píxeles por lado para admitir las fotos HEIC habituales del iPhone; el backend sigue siendo quien verifica formato, tamaño y elimina EXIF. Después de crear el reporte, la app sube las fotos con la misma sesión ciudadana. Si una subida falla, muestra el incidente ya guardado y permite reintentar solo las fotos pendientes, sin crear otro reporte. `mobile/app.json` declara los textos de permisos para cámara y fotos.

**Pruebas locales:** `npx tsc --noEmit` y `npm run lint` pasaron; `npx expo export --platform ios --output-dir .expo/photo-check` generó el bundle iOS fuera del sandbox. La primera exportación falló porque Hermes no pudo escribir en el directorio temporal virtualizado del sandbox; fuera de él pasó sin cambios de código. **Prueba en iPhone:** el usuario confirmó selección, vista previa, eliminación, nueva selección y envío de una fotografía ficticia; la app mostró «Fotografías guardadas: 1». Una consulta PostgreSQL de solo lectura confirmó una fila JPEG reciente con tamaño dentro de 5 MB, sin leer la imagen. **P1.3 cerrado.** La selección pendiente vive en memoria/caché de la app durante esta demo; si se cierra Expo Go antes de reintentar, el reporte permanece guardado pero la app no puede recuperar esas fotos pendientes. El reintento tras una falla de red aún no se probó en el teléfono.

## Registro de P1.4 — fotografías en el dashboard comprobadas

`backend/app/incident_routes.py` consulta fotos solo después de comprobar que el incidente pertenece al municipio del funcionario y crea enlaces temporales de Storage válidos por 300 segundos. La respuesta del detalle no devuelve identidad ciudadana ni rutas internas y lleva `Cache-Control: no-store`. `dashboard/src/IncidentDetail.tsx` muestra las imágenes en el detalle privado, o «Sin fotografías» si no hay, con `referrerPolicy="no-referrer"`. Se agregó estilo sencillo en `dashboard/src/App.css`.

**Pruebas:** las pruebas de backend confirmaron `401` sin sesión, `403` para ciudadano y `404` para otro municipio antes de firmar enlaces. Una prueba real encontró la foto ficticia enviada desde el iPhone, obtuvo un enlace temporal, descargó una imagen válida sin imprimirla y confirmó `404` para un municipio ajeno. La suite normal pasó 17 pruebas y omitió dos de integración que requieren Supabase; la prueba específica con Supabase pasó. `npm run build` y `npm run lint` del dashboard pasaron. El usuario abrió el incidente en navegador, vio la foto y confirmó «Sin fotografías» en otro incidente. **La función P1 «Fotografías» está comprobada.** Los enlaces firmados son utilizables por quien los posea hasta que caduquen; solo se usan imágenes ficticias. La prueba de reintento móvil tras fallo de red queda pendiente como mejora de robustez.

## Registro de P1.5 — evaluación de fuente territorial

Se revisó el contrato P1 y se documentó en `docs/neighborhood-source.md` la DCAH 2024 del INEGI como fuente candidata de polígonos de colonias y otros asentamientos humanos para Aguascalientes. Su capa declara claves de entidad, municipio, localidad y asentamiento, nombre, tipo, fecha e institución que la avala. El catálogo tabular del INEGI no basta para asignar un punto GPS. La nota técnica del INEGI advierte que las delimitaciones corresponden al ayuntamiento y pueden requerir validación municipal. **No se descargaron ni importaron polígonos, no se modificó Supabase y el filtro sigue pendiente.** P1.6 comprobará el paquete real y su cobertura antes de implementar.

## Registro de P1.6 — capa oficial inspeccionada

Se obtuvo desde la ficha oficial del INEGI la URL de `01_aguascalientes.zip` de DCAH 2024 y se descargó a una carpeta temporal. `docs/neighborhood-source.md` conserva URL, tamaño, SHA-256 y resultados. El paquete contiene la capa `01as` y metadatos. Se comprobaron 1 679 polígonos estatales, 1 020 del municipio `01001`, cero geometrías inválidas o vacías y cero claves compuestas repetidas dentro del municipio. El `.prj` declara `MEXICO_ITRF_2008_LCC` y se transformó a 4326; un punto central de Aguascalientes coincidió con un polígono. Hay un par superpuesto, 348 registros de tipo `NINGUNO` y fechas de actualización 2020–2023, aunque la edición es 2024. Los términos de INEGI permiten adaptación con crédito de fuente. **No se modificó Supabase ni se habilitó el filtro.** Siguiente paso: importación controlada y pruebas espaciales.

## Registro de P1.7 — polígonos y asignación espacial comprobados

Se aplicó `database/migrations/20261119010000_neighborhoods.sql`: crea `public.neighborhoods` con clave oficial, nombre, tipo, fecha, institución y límite PostGIS MultiPolygon 4326; agrega `incidents.neighborhood_id` opcional y una FK que obliga a pertenecer al mismo municipio. Hay índices GiST y de consulta, RLS activa y ningún permiso directo para `anon` ni `authenticated`. El importador `backend/scripts/import_neighborhoods.py` exige el SHA-256 exacto del ZIP oficial, lee su `.prj`, transforma a 4326, valida 1 020 geometrías y carga por clave de origen de forma repetible. Se conservaron metadatos de fuente y no se almacenó información personal.

**Pruebas en Supabase:** se comprobaron 1 020 polígonos y 5 de 5 incidentes existentes asignados por coincidencia única. Una consulta independiente confirmó cero incidentes con asignación que contradiga el conteo espacial. Se probaron un punto interior, uno en el borde, uno en la zona superpuesta (más de una coincidencia, por tanto sin asignación) y uno exterior (cero coincidencias). RLS y ausencia de `SELECT` directo para ambos roles cliente quedaron verificadas. Se repitió la importación del mismo ZIP: siguieron siendo 1 020 polígonos y 5 de 5 incidentes asignados, con todas las verificaciones aprobadas. **P1.7 terminado.** Los nuevos reportes aún no se asignan automáticamente y el filtro del dashboard sigue apagado hasta P1.8 y pruebas del flujo nuevo.

## Registro de P1.8 — asignación al crear reportes comprobada

`backend/app/report_routes.py` consulta `public.neighborhoods` con `ST_Covers` dentro de la transacción de `POST /api/v1/reports`. Solo guarda `incidents.neighborhood_id` cuando existe una coincidencia única del municipio. Si no hay cobertura o hay superposición, deja la columna vacía. El JSON público y los campos que revisa el ciudadano no cambian. `backend/tests/test_neighborhood_report.py` prueba el flujo real con datos ficticios y limpia sus filas temporales.

**Pruebas:** la suite backend pasó 17 pruebas normales; omitió las 3 de integración que requieren Supabase. La prueba P1.8 con Supabase pasó para un punto único, uno superpuesto y uno exterior; confirmó el ID almacenado o `NULL`, y verificó que repetir el mismo `client_request_id` devuelve el reporte existente con HTTP 200. Después de limpiar, una consulta encontró cero incidentes de prueba restantes. **P1.8 terminado.** El catálogo y el filtro privado siguen pendientes de P1.9; no se ha probado aún el despliegue visual de ese filtro.

## Registro de P1.9 — catálogo y filtro en verificación

`backend/app/incident_routes.py` ahora ofrece `GET /api/v1/neighborhoods` solo a funcionarios activos, con ID, nombre, tipo, clave de origen y conteo agregado de incidentes del municipio, sin geometrías ni datos ciudadanos. Ordena primero las zonas con incidentes para facilitar la demo. `GET /api/v1/incidents` y `/incidents/map` aceptan `neighborhood_id` además de los filtros existentes. El dashboard agregó un selector «Colonia o asentamiento» con crédito al INEGI; aplica la misma selección a lista y mapa y permite volver a «Todos los asentamientos». No se implementaron métricas ni acceso público al catálogo.

**Pruebas realizadas:** con Supabase se obtuvieron los 1 020 asentamientos y se confirmó que un incidente aparece con su colonia en lista y mapa, pero no con otra; UUID mal formado respondió `422` y catálogo sin sesión `401`. `npm run build` y `npm run lint` pasaron. Vite mantiene el aviso previo por el tamaño de Mapbox, cargado de forma diferida. **Pendiente:** prueba visual del usuario en navegador antes de marcar P1.9 terminado.

**Prueba visual parcial y mejora solicitada:** el usuario confirmó que el filtro de lista y mapa funciona y pidió encontrar colonias por nombre y CP, con opciones dependientes del CP. Se agregó la migración `20261119020000_neighborhood_postal_code.sql`, se reimportó el CP oficial y se comprobó que 39 registros `00000` quedaron como `NULL` y hay 132 CP utilizables distintos. El catálogo privado ahora entrega CP; el dashboard reduce opciones por nombre o prefijo de CP, conservando la selección por ID de polígono. La prueba de API con Supabase, build y lint pasaron nuevamente. **Pendiente:** confirmación visual de las dos búsquedas antes de cerrar P1.9.

**Cierre de P1.9:** el usuario confirmó en el navegador que buscar `20263` reduce las opciones al CP esperado, que buscar por nombre y seleccionar una colonia actualiza lista y mapa, y que borrar la búsqueda y elegir «Todos los asentamientos» restaura el conjunto completo. P1.9 y el alcance funcional P1 quedaron comprobados. Queda como mejora de robustez el reintento móvil de fotografías tras un fallo de red, ya registrado en P1.3.

## Registro de P2.1 — confirmación independiente en backend

Se aplicó `database/migrations/20261119030000_incident_confirmations.sql`. La tabla tiene una restricción única por incidente y sesión de Auth, FK a incidente y usuario, RLS activa y ningún permiso directo para clientes. `POST /api/v1/incidents/{id}/confirmations` en `backend/app/incident_routes.py` permite confirmar solo a una sesión ciudadana anónima distinta del autor de un reporte vinculado. Solo admite incidentes activos del municipio de la demo. La primera solicitud devuelve `201`; repetirla devuelve `200` sin aumentar el conteo. No cambia gravedad, estado ni prioridad. La respuesta no contiene identidad ciudadana.

**Pruebas:** con dos sesiones ficticias existentes, el autor recibió `409`, otra sesión obtuvo `201` y un reintento `200` con el mismo conteo; un incidente finalizado dio `409`, uno inexistente `404`, un ID inválido `422`, un funcionario `403` y una solicitud sin sesión `401`. Se comprobaron RLS y permisos y se eliminó la confirmación temporal; el conteo volvió al inicial. La suite backend pasó 17 pruebas normales y omitió 5 integraciones optativas; la integración P2.1 pasó por separado. **P2.1 terminado.** Todavía falta descubrir incidentes desde el móvil y mostrar el conteo en dashboard. Con Auth anónimo se garantizan sesiones únicas, no personas físicas únicas; reinstalar la app puede crear otra sesión.

## Registro de P2.2 — consulta cercana y botón móvil en verificación

`GET /api/v1/incidents/nearby` devuelve hasta 10 incidentes activos a 1 km del GPS de una sesión ciudadana anónima, excluye sus propios reportes y solo muestra categoría, distancia redondeada a 50 m, fecha y conteo de confirmaciones. No devuelve ubicación precisa del incidente, descripción ni identidad. El POST de confirmación ahora exige GPS y comprueba el radio de 1 km sin persistir ese punto. `mobile/App.tsx` añadió «Ver incidentes cercanos», una pantalla de tarjetas y un botón para confirmar, sin borrar el borrador del formulario al volver.

**Pruebas técnicas:** la integración con Supabase confirmó autorización, exclusión del autor, respuesta mínima, límite geográfico, `201` inicial, `200` al repetir y conteo estable; eliminó la fila ficticia. TypeScript y `expo lint` pasaron. La exportación iOS falló en el sandbox por la ruta temporal de Hermes y pasó fuera de él, generando un bundle de 2,5 MB. **Pendiente:** prueba en iPhone con un incidente de otra sesión antes de marcar P2.2 completo. El dashboard todavía no muestra el conteo.

**Datos ficticios para la prueba móvil:** a petición del usuario se creó `backend/scripts/seed_confirmation_demo.py`, que usa una sesión anónima nueva y `POST /api/v1/reports` para guardar cinco reportes con prefijo `[DEMO CONFIRMACIONES]` en cinco asentamientos distintos: José Vasconcelos Calderón (CP 20200, cerca de un reporte previo), Arroyo El Molino (20123), Vistas de Oriente (20196), Central de Abastos (20280) y La Trinidad (20326). El script comprobó cinco incidentes `reported`, cinco colonias distintas y una sola sesión autora. Una consulta independiente confirmó que al menos una sesión anterior tiene un incidente demo a 1 km de un reporte propio. Los IDs y el usuario anónimo de la muestra están en `backend/.confirmation_demo_seed.json`, ignorado por Git; no contiene token ni clave. No se guardaron fotos ni datos personales en la muestra. P2.2 sigue pendiente de prueba visual en el iPhone.

**Cierre de P2.2:** el usuario confirmó en Expo Go que apareció un incidente ficticio de otra sesión, pudo confirmarlo y vio el botón «Ya confirmaste» con el conteo incrementado. Una consulta PostgreSQL de solo lectura encontró una confirmación para los incidentes demo, sin consultar identidad ni ubicación. **P2.2 terminado.** Falta mostrar el agregado en el dashboard; la prioridad sigue sin incorporar confirmaciones.

## Registro de P2.3 — conteo en dashboard en verificación

El detalle privado `GET /api/v1/incidents/{id}` ahora devuelve `confirmations_count` mediante un conteo agregado después de verificar el municipio del funcionario. No devuelve filas de confirmaciones ni identidad ciudadana. `dashboard/src/IncidentDetail.tsx` muestra reportes y confirmaciones por separado y explica que las confirmaciones aún no modifican la prioridad.

**Pruebas técnicas:** dos pruebas de integración con Supabase pasaron, incluida la comparación del conteo del detalle con PostgreSQL para el incidente confirmado desde el iPhone y la ausencia de `user_id`/`reporter_id`. La suite backend pasó 17 pruebas normales (6 integraciones optativas omitidas). `npm run build` y `npm run lint` del dashboard pasaron; Vite conservó el aviso previo sobre el tamaño del módulo diferido de Mapbox. **Pendiente:** confirmación visual en navegador antes de cerrar P2.3.

**Identificación de la muestra:** se comprobó que el listado no enseñaba el prefijo de la descripción ficticia. Se actualizaron únicamente los títulos de los cinco incidentes del manifiesto para empezar por `[DEMO]`, con verificación de 5 de 5. `backend/scripts/seed_confirmation_demo.py` incluye esa marca para futuras ejecuciones; los textos originales y las confirmaciones no se modificaron.

**Cierre de P2.3:** el usuario recargó el dashboard, abrió el incidente demo confirmado desde el iPhone y vio «1 confirmación(es) de otras sesiones» junto a los reportes y la nota de que el dato no modifica la prioridad. **P2.3 y el alcance aprobado de confirmaciones independientes quedaron comprobados de extremo a extremo.** Siguen fuera de alcance la deduplicación automática, la verificación de personas físicas y un peso de confirmaciones en la fórmula de prioridad.

## Registro de P0.4 — autenticación backend en curso

Se creó `backend/app/auth.py` para verificar el token mediante Supabase Auth, exigir sesión ciudadana anónima y consultar `private.staff_members` para el permiso de funcionario activo. `backend/app/main.py` expone `GET /api/v1/auth/me` y devuelve los errores de autenticación con el formato JSON del contrato. `backend/app/config.py` lee la URL de PostgreSQL. Se actualizó `docs/api.md` con el contrato de la nueva ruta. No se implementaron reportes, dashboard ni IA.

**Pruebas realizadas:** compilación de `backend/app`; dependencias directas verificadas para ausencia de token (`401`), token inválido (`401`), ciudadano permitido y funcionario autorizado o denegado. Con Supabase real, un token inválido produjo `401 UNAUTHENTICATED` y un UUID no inscrito en personal no obtuvo municipio. Una prueba HTTP local de FastAPI devolvió `200` en `/health` y `401` con el JSON esperado en `/auth/me` sin token.

**Bloqueo resuelto:** la primera prueba de inicio anónimo respondió `422 anonymous_provider_disabled`. El usuario habilitó Anonymous Sign-Ins en Supabase y se repitió la prueba con éxito.

**Pruebas reales de P0.4:** una sesión anónima temporal produjo un JWT válido; FastAPI la reconoció como `citizen`, permitió la dependencia ciudadana y negó el permiso de funcionario con `403`. `GET /api/v1/auth/me` respondió `200` con `role: citizen` y sin municipio. Se eliminó el usuario temporal. Luego se creó una cuenta ficticia temporal y un registro activo en `private.staff_members`: la ruta respondió `200` con `role: staff` y municipio. Al desactivar el registro respondió `role: unassigned`, sin municipio. Se eliminaron el registro y la cuenta. No se conservaron credenciales ni tokens de estas pruebas. P0.4 está comprobado; aún faltan autenticación en móvil/dashboard y autorización de rutas de negocio, que pertenecen a los siguientes bloques.

## Registro de P0.5 — categorías y reporte tradicional backend

Se creó `backend/app/report_routes.py` con `GET /api/v1/categories` y `POST /api/v1/reports`. El registro exige sesión ciudadana anónima, categoría activa, descripción de 10 a 1000 caracteres sin correo o teléfono detectable, gravedad y ubicación válidas. Usa una caja geográfica **aproximada** configurada por `DEMO_BBOX`; no equivale al límite oficial del municipio. El usuario confirma los datos antes de llamar a esta ruta desde la futura app. Reporte, incidente e historiales se crean en una transacción. La clave `client_request_id` serializa reintentos del mismo usuario: un reintento idéntico devuelve `200` y uno diferente `409`. La prioridad inicial usa pesos configurables y guarda factores y pesos. `backend/app/main.py` incorpora las rutas y el formato JSON de errores 422; `backend/app/config.py` y `.env.example` incorporan la caja y los pesos.

**Pruebas reales:** con un usuario anónimo temporal, `GET /categories` devolvió diez categorías. `POST /reports` devolvió `201` y estado `reported`; el reintento idéntico devolvió `200` con el mismo ID; uno con contenido distinto devolvió `409`. Un correo en la descripción y una ubicación fuera de la caja devolvieron `422`. Una segunda creación permitió comprobar en PostgreSQL un reporte enlazado a un incidente con punto `(latitud 21.8818, longitud -102.2916)`, una fila inicial de estado y prioridad `60.00` con `G=75`, `T=0` y pesos `0.8/0.2`. Se eliminaron los usuarios y datos de ambas pruebas. No se ha probado aún el formulario móvil ni el flujo de voz.

## Registro de P0.6 — formulario móvil en verificación

Se añadió `mobile/supabase.ts` para sesiones anónimas persistidas mediante el almacenamiento local de Expo SQLite. `mobile/App.tsx` ahora muestra categorías, descripción, duración opcional, gravedad y GPS. Antes de enviar presenta un resumen y permite volver a editar. Solo al confirmar llama a `POST /reports`, con un UUID estable para reintentos; tras éxito muestra el ID del incidente. El texto recuerda usar solo reportes ficticios y omitir datos personales. Se instalaron `@supabase/supabase-js`, `react-native-url-polyfill`, `expo-sqlite`, `expo-location` y `expo-crypto`; las dos dependencias no nativas se fijaron a versión exacta en `package.json` y lockfile.

**Pruebas realizadas:** TypeScript y `expo lint` pasaron. La exportación iOS pasó al repetirla fuera del sandbox, donde Hermes sí pudo escribir su archivo temporal. La URL pública y la clave publicable configuradas en `mobile/.env` iniciaron una sesión anónima real; se eliminó el usuario temporal. FastAPI respondió `{"status":"ok"}` y Expo HTTP 200 en `172.24.11.145`; la URL API configurada en el móvil devolvió diez categorías con token real. **Pendiente:** prueba visual y funcional desde Expo Go en el teléfono, permiso GPS y envío ficticio. No se marca P0.6 terminado todavía.

**Prueba posterior en dispositivo:** el usuario confirmó que ve la pantalla y las diez categorías, y que GPS funciona. El servidor Expo registró un bundle Android; FastAPI recibió `GET /categories` con `200` y `POST /reports` con `201` desde la IP del teléfono. Falta confirmar visualmente la edición desde el resumen y que la pantalla de éxito mostró el ID. No se inspeccionó ni alteró el contenido del reporte enviado por el usuario.

**Cierre de P0.6:** el usuario confirmó en Expo Go que pudo volver desde «Revisar reporte», modificar los datos, revisar de nuevo y enviar. Vio «Reporte enviado» con un ID de incidente. Junto con el `201` observado en FastAPI, esta prueba completa el flujo tradicional móvil. El reporte ficticio enviado por el usuario se conserva como dato de demo; no se modificó ni eliminó.

## Registro de P0.1 — 18 de noviembre de 2026

**Archivos nuevos:** `.gitignore`, `README.md`, `mobile/.env.example`, `mobile/eslint.config.js`, `dashboard/.env.example`, `backend/.env.example`, `backend/requirements.txt`, `backend/requirements.lock`, `backend/app/__init__.py`, `backend/app/config.py`, `backend/app/supabase_client.py`, `backend/app/main.py`, marcadores de `database/migrations/` y `database/seeds/`, y archivos generados por las plantillas oficiales de Expo y Vite, incluidos `package.json` y `package-lock.json`.

**Archivos modificados:** `mobile/app.json` (nombre de la app), `mobile/package.json` y su lockfile (ESLint agregado por Expo), `dashboard/index.html` (idioma y título), `PROJECT_STATUS.md` (este avance). `PLAN.md` y los documentos de diseño no se cambiaron.

**Herramientas comprobadas:** Node.js 26.13.0, npm 11.20.0, Python 3.14.7, Git 2.51.0 y Java 21.0.13. `adb` y `nvm` no están en PATH. Expo recomienda Node LTS; Node 26 funcionó en las pruebas de compilación realizadas, sin garantizar compatibilidad en el dispositivo.

**Dependencias directas instaladas:** móvil: Expo 58.0.26, React Native 0.88.1, React 19.3.0, TypeScript 6.0.3 y ESLint de Expo; dashboard: React 19.3.1, Vite 8.3.8, TypeScript y oxlint; backend: FastAPI 0.164.0, Uvicorn 0.54.0, python-dotenv 1.2.4 y cliente Supabase 2.34.1. Los lockfiles fijan dependencias transitivas.

**Pruebas realizadas:** `npm run build` y `npm run lint` del dashboard pasaron; Vite respondió HTTP 200 con el título correcto. `npx tsc --noEmit`, `npx expo lint` y `npx expo export --platform android` del móvil pasaron. Python compiló `backend/app`, `pip check` no encontró conflictos y FastAPI respondió HTTP 200 con `{"status":"ok"}`. Los archivos `.env` reales y dependencias generadas quedaron ignorados por Git. La exportación Android necesitó ejecutarse fuera del sandbox porque Hermes no podía escribir en su carpeta temporal aislada.

**Límites de la verificación:** el usuario mostró la plantilla móvil cargada en Expo Go para iOS, pero todavía no hay funciones propias que probar. Supabase REST respondió en una prueba posterior de solo lectura; no se han probado tablas, Auth ni políticas. No se ha verificado conectividad desde el teléfono hacia FastAPI en la IP local. El backend solo tiene la ruta de salud, sin rutas de negocio.

**Comprobación del usuario:** la captura de Expo Go confirma que la plantilla móvil carga. La primera captura web mostró `dashboard/index.html` abierto como archivo, que no ejecuta Vite. Tras abrir `http://localhost:5173/`, el usuario confirmó que ambas pantallas base se ven correctamente. Esta prueba solo valida las plantillas, no las funciones del producto.

## Registro de P0.2 — conectividad

El usuario comunicó que FastAPI y Supabase mostraban estado OK. Se comprobó que `backend/.env` contiene URL y clave privada sin imprimir sus valores, y una solicitud de solo lectura a la API REST del proyecto Supabase respondió **HTTP 200**. `SUPABASE_DB_URL` aún no está configurada; el conector Supabase de esta sesión no muestra proyectos. No se modificó la base de datos ni se creó código en este paso. La conexión al servicio está verificada, mientras que el esquema y los permisos siguen pendientes.

## Registro de P0.3 — esquema inicial preparado

Se creó `database/migrations/20261118232244_initial_schema.sql` mediante la CLI de Supabase y se colocó en la estructura del monorepositorio. Contiene siete tablas, nueve índices, RLS en las siete tablas, permisos directos denegados a clientes y semillas para un municipio y las diez categorías. Una revisión estática confirmó esos conteos. La API REST solo mostró la ruta `/rpc/rls_auto_enable`; esto **no prueba** que PostgreSQL no tenga tablas privadas o no expuestas. No se aplicó la migración: falta `SUPABASE_DB_URL` o acceso del conector al proyecto, y no se ha ejecutado SQL contra la base. El esquema sigue sin marcarse como terminado.

**Intento posterior de conexión:** el usuario configuró `SUPABASE_DB_URL` con la cadena Direct connection. Se instaló `psycopg[binary]` 3.3.9 y se probó la URL sin imprimir secretos. Su host `db.<proyecto>.supabase.co` no resolvió en esta computadora (`getaddrinfo failed`), por lo que no se pudo inspeccionar ni cambiar PostgreSQL. La prueba normalizó en memoria caracteres especiales de la contraseña; no modificó el `.env`. Se necesita la cadena Session pooler (puerto 5432) o una red con acceso al host directo. La migración continúa sin aplicar.

**Última comprobación:** la contraseña en `.env` ya tiene un carácter especial codificado, pero el host sigue siendo `db.<proyecto>.supabase.co` (Direct connection). Se omitió repetir la conexión fallida. Se actualizó `backend/requirements.lock` con `psycopg` y `psycopg-binary` 3.3.9. No se aplicó SQL.

**Incidente de credencial:** al diagnosticar una URL Session pooler mal formada, un comando mostró accidentalmente la cadena de conexión y su contraseña en la salida de esta conversación. Se retiró `SUPABASE_DB_URL` de `backend/.env` y se comprobó que quedó vacía; las otras variables no se modificaron. La contraseña expuesta debe cambiarse en Supabase antes de volver a conectar. La migración sigue sin aplicar y no se ejecutó SQL con esa URL.

**Prueba de la nueva URL:** el usuario indicó que configuró una nueva cadena. Se detectó que empezaba por `//` y se agregó únicamente el prefijo `postgresql:` en `backend/.env`. Se verificó el formato Session pooler, puerto 5432, base `postgres` y que el identificador del usuario coincide con el proyecto Supabase. La primera conexión, dentro del entorno aislado, falló por DNS; al repetirla fuera de ese aislamiento, el servidor respondió con **fallo de autenticación por contraseña**. Por ello no se inspeccionaron tablas ni se aplicó la migración. La contraseña no se mostró en estas pruebas.

**P0.3 completado tras corregir la contraseña:** el usuario actualizó la URL y la conexión PostgreSQL respondió `select 1`. Antes de aplicar SQL, `public` no contenía tablas; `private` y PostGIS tampoco existían. Se aplicó `database/migrations/20261118232244_initial_schema.sql` en una transacción. La verificación posterior encontró las siete tablas esperadas con RLS habilitada, los nueve índices previstos, PostGIS, un municipio y diez categorías. Los privilegios directos comprobados dieron `anon` sin `SELECT` sobre `reports`, `authenticated` sin `INSERT` sobre `incidents` y `service_role` con `INSERT` sobre `reports`. No se insertaron reportes ni usuarios. Quedan por probar restricciones con datos de ejemplo, rutas API y autorización por JWT.

## Decisiones aprobadas

1. El MVP inicia en Aguascalientes capital y mantiene separados `Report`, `Incident` y una futura `WorkOrder`.
2. React Native con Expo y TypeScript será la app ciudadana; React con TypeScript será el dashboard; FastAPI concentrará validación, lógica de negocio e integración de IA; Supabase aportará Auth, PostgreSQL, PostGIS y Storage; Mapbox mostrará el mapa del dashboard.
3. La transcripción usará solo una alternativa gratuita, ejecutada localmente con `faster-whisper` o Whisper. No se contratará un servicio de transcripción. Se medirá su rendimiento con un audio real al comienzo de P0.
4. Gemini se usará en su modalidad gratuita y solo con reportes ficticios. Antes de enviar texto a Gemini se quitarán datos personales detectables. Los ejemplos de la demo no incluirán información personal. El audio y la transcripción original no se conservarán en la base de datos.
5. La IA propone campos; el ciudadano siempre puede corregir categoría, descripción, gravedad y ubicación antes de enviar. Si la transcripción falla, la app permite llenar el formulario manualmente. La falla no crea un reporte.
6. FastAPI y el dashboard se ejecutarán en una computadora de la misma red que el teléfono. Supabase, Gemini y Mapbox seguirán necesitando internet. Las claves secretas permanecerán en el backend local.
7. Cada cambio funcional se marcará como terminado solo después de una prueba observable. Este archivo registrará avances, decisiones, errores y la siguiente tarea.

## Alcance aprobado

| Funcionalidad | Prioridad | Estado |
|---|---|---|
| Formulario tradicional | P0 | Comprobado en Expo Go y FastAPI |
| Reporte mediante voz | P0 | Transcripción, propuesta Gemini editable, revisión y envío comprobados en iPhone |
| Revisión y confirmación del ciudadano | P0 | Comprobadas en Expo Go |
| Ubicación GPS | P0 | Comprobada en Expo Go |
| Registro y persistencia | P0 | Comprobados para reportes ficticios tradicional y por voz; consulta de reportes propios pospuesta |
| Dashboard privado | P0 | Acceso, listado y cierre comprobados en navegador |
| Mapa de incidentes | P0 | Comprobado en navegador, incluidos marcadores agrupados |
| Detalle y estado del incidente | P0 | Detalle, cambio, historial y estados finales comprobados en navegador |
| Prioridad explicable | P0 | Factores G/T y pesos vistos por el usuario en el dashboard |
| Fotografías | P1 | Comprobada de extremo a extremo: envío móvil, Storage privado y visualización autorizada |
| Filtro por colonia | P1 | Comprobado en navegador: búsqueda por nombre/CP y filtro de lista y mapa |
| Confirmaciones independientes | P2 | Comprobadas de extremo a extremo: móvil, persistencia y conteo privado en dashboard |

**Fuera del prototipo de dos días:** WhatsApp, clasificación visual, embeddings y pgvector, predicción, multitenencia y órdenes de trabajo. La sugerencia y consolidación de duplicados se difiere hasta poder probar una regla que no mezcle problemas distintos. El modelo permite asociar varios reportes a un incidente cuando se incorpore ese flujo.

## Decisiones de diseño documentadas, aún sin implementar

- **Identidad ciudadana para la demo:** sesión anónima de Supabase Auth. Proporciona un identificador de sesión sin solicitar nombre, teléfono ni correo. Si se pierde la sesión, no habrá recuperación de reportes en este prototipo. Los funcionarios usarán cuentas de Auth y una tabla restringida de personal autorizado.
- **Datos personales:** no se guardarán perfiles ciudadanos ni texto bruto de audio. La descripción confirmada deberá ser apta para análisis territorial. La anonimización automática es una ayuda, no una garantía; se usarán datos ficticios y se rechazarán patrones obvios de correo o teléfono. Las ubicaciones precisas y fotografías, si las hay, siguen siendo datos sensibles y solo se mostrarán a funcionarios autorizados.
- **Prioridad P0:** gravedad y tiempo abierto, con pesos iniciales configurables de 0,80 y 0,20. El factor de confirmaciones, población afectada y vulnerabilidad territorial no se simulará sin datos; sus pesos serán cero hasta la fase correspondiente. Se guardarán versión, factores y pesos en el historial.
- **Seguridad:** clientes solo usan la clave publicable de Supabase para Auth; las tablas de negocio y Storage no tendrán acceso directo de escritura desde los clientes. FastAPI verificará el JWT y el rol. RLS y permisos de base de datos limitarán el acceso directo a Supabase.
- **Ubicación manual:** el plan contempla seleccionar un punto o introducir dirección. El flujo GPS es P0; la selección manual se realizará si cabe sin comprometer los flujos aprobados y se registrará como pendiente si no llega a probarse. No se inferirán coordenadas desde Gemini.

## Pendientes y riesgos abiertos

1. Verificar conectividad del teléfono hacia FastAPI y el firewall de la red privada cuando empiece la integración móvil. Las claves de Gemini y Mapbox se comprobarán cuando les corresponda.
2. Confirmar disponibilidad de CPU, RAM y espacio suficientes para `faster-whisper`; medir descarga, arranque y procesamiento de un audio corto en la tarea de voz. Sin esta prueba, su viabilidad P0 no está demostrada.
3. Definir y cargar un límite geográfico confiable para el municipio. La caja actual `DEMO_BBOX` sirve solo para la demo y puede aceptar puntos fuera del municipio real.
4. Conseguir una fuente confiable de colonias para P1. No se etiquetará una colonia mediante suposición de la IA.
5. Probar que la sesión anónima de Supabase Auth sea suficiente para la demo y que la cuenta de funcionario no pueda ser creada por un ciudadano.
6. Probar restricciones con datos de ejemplo, autorización de API y almacenamiento privado cuando existan sus rutas y usuarios de prueba. RLS y privilegios iniciales ya se comprobaron a nivel de catálogo.

## Errores conocidos

La instalación de Expo informa tres alertas **moderadas** de npm sobre `minimatch`, dependencia transitiva de `@expo/fingerprint`. `npm audit --omit=dev` confirma la cadena. La corrección automática propuesta por npm instalaría Expo 52, incompatible con el SDK 58 elegido; no se aplicó. Se revisará cuando exista una corrección compatible. No se observaron fallos de compilación, lint ni respuesta HTTP en las bases creadas. La primera exportación Android falló por permisos de escritura del sandbox; la repetición autorizada pasó.

## Criterio para actualizar este archivo

Después de cada bloque se anotarán fecha, funcionalidad, archivos cambiados, comando o pasos de prueba, resultado y cualquier error pendiente. El porcentaje funcional solo aumentará por funciones probadas de la tabla de alcance, no por archivos creados.
