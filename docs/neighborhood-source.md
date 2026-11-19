# Fuente para el filtro por colonia (P1.5)

**Decisión:** usar la *Delimitación de Colonias y otros Asentamientos Humanos 2024* (DCAH) del INEGI para Aguascalientes. Se descargó e inspeccionó el [ZIP oficial de Aguascalientes](https://www.inegi.org.mx/contenidos/productos/prod_serv/contenidos/espanol/bvinegi/productos/geografia/delimitaciones/794551132180/01_aguascalientes.zip), enlazado desde la [ficha del producto](https://www.inegi.org.mx/app/biblioteca/ficha.html?upc=794551132180). La [descripción oficial](https://www.inegi.org.mx/programas/dcah/) indica que los polígonos proceden de un trabajo con autoridades municipales.

La capa contiene `CVE_ENT`, `CVE_MUN`, `CVE_LOC`, `CVE_ASEN`, `NOM_ASEN`, `TIPO`, `FECHA_ACT` e `INSTITUCION`. Para el municipio inicial solo se aceptarían registros `CVE_ENT='01'` y `CVE_MUN='001'`. Se conservaría la clave compuesta de localidad y asentamiento como identificador de origen; el nombre puede repetirse. Se incluirían colonias, fraccionamientos y barrios con el tipo oficial, y la interfaz diría «Colonia o asentamiento». El catálogo tabular de asentamientos del [servicio geoestadístico del INEGI](https://www.inegi.org.mx/servicios/catalogounico/) sirve para contrastar claves y nombres, pero sus nombres por sí solos no permiten asignar una ubicación GPS.

## Verificación antes de importar

1. Descargar el archivo oficial y comprobar licencia, fecha, campos, municipio `01001`, sistema de coordenadas de su archivo `.prj`, número de polígonos y geometrías válidas. La ficha indica proyección Cónica Conforme de Lambert e ITRF2008; no se asumirá un EPSG sin revisar `.prj`.
2. Transformar a 4326 y comparar visualmente varias zonas conocidas con el mapa. Registrar cuántos polígonos se superponen, dejan huecos o quedan fuera del municipio.
3. Asignar un incidente solo si su punto GPS cae dentro de un único polígono verificado. Si no hay coincidencia o hay varias, dejar `neighborhood_id` vacío; no usar el LLM ni el asentamiento más cercano para inventar una colonia.
4. Probar al menos un punto interior, uno en un borde y uno sin cobertura antes de habilitar el filtro. Los reportes anteriores se asignarán solo con la misma regla espacial.

## Resultado de inspección (19 de noviembre de 2026)

El ZIP descargado mide 30 092 806 bytes; SHA-256: `E36F706C7D896CDB46D00EC8F7B72C697BAE3C89A90AB52EAC9396347FB83D5C`. Contiene `conjunto_de_datos/01as.shp`, `.shx`, `.dbf`, `.prj`, `.cpg`, catálogo y metadatos. Hay 1 679 polígonos estatales y **1 020 del municipio `01001`**. La capa usa `MEXICO_ITRF_2008_LCC`; el archivo `.prj` no se identifica con un código EPSG simple, pero se transformó a WGS84/4326 con `pyproj`. Su `.cpg` declara `ISO 88591`; para leer nombres se usó Latin-1.

En `01001` no se encontraron geometrías vacías o inválidas ni claves compuestas repetidas. Un punto de prueba en el centro de Aguascalientes coincidió con un polígono. Se encontró **un par de polígonos con superposición material**; los puntos que caigan en más de uno quedarán sin asignación. Los 1 020 registros tienen nombre; 348 tienen `TIPO=NINGUNO`, así que no se tratarán automáticamente como «colonia». Las fechas `FECHA_ACT` son 985 de noviembre de 2023, 32 de noviembre de 2020 y 3 de noviembre de 2021. Trece registros muestran como institución a Jesús María aun cuando `CVE_MUN='001'`; conviene revisar esos límites antes de usarlos en la demo.

Los [términos de uso del INEGI](https://www.inegi.org.mx/inegi/terminos.html) permiten extraer y adaptar la información con crédito a la fuente y sin quitar metadatos de copias distribuidas. El dashboard deberá citar: «Fuente: INEGI, Delimitación de colonias y otros asentamientos humanos 2024». El [INEGI precisa](https://www.inegi.org.mx/contenidos/programas/dcah/doc/nota_tecnica.pdf) que la delimitación es competencia municipal; la capa no garantiza límites actuales. El [VisorAGS](https://visor.aguascalientes.gob.mx/visorags) muestra una capa «Colonias y fracc.», pero no se verificó una descarga reutilizable.

**Siguiente paso:** preparar una importación reproducible de los 1 020 polígonos, conservar la clave y fecha de origen, transformar desde el `.prj` a 4326, comprobar la superposición y validar puntos interiores, de borde y sin cobertura antes de habilitar el filtro. En P1.6 no se modificó Supabase ni se cambiaron reportes.

## Importación aplicada (P1.7)

`database/migrations/20261119010000_neighborhoods.sql` crea la tabla restringida `public.neighborhoods` y la referencia opcional desde `incidents`. La migración `20261119020000_neighborhood_postal_code.sql` agrega el CP opcional. `backend/scripts/import_neighborhoods.py` acepta **solo** el ZIP cuyo SHA-256 aparece arriba. Usa `CVEGEO` como clave estable, conserva nombre, tipo, fecha, institución y CP, y transforma desde el `.prj` original. Las dependencias geográficas están en `backend/scripts/requirements-neighborhoods.txt`; no forman parte de la API en ejecución.

Para reproducirlo, descarga el ZIP de la URL oficial de arriba, aplica las dos migraciones SQL en orden una vez en el editor de Supabase y ejecuta desde la raíz del proyecto:

```powershell
.\backend\.venv\Scripts\python.exe -m pip install -r backend\scripts\requirements-neighborhoods.txt
.\backend\.venv\Scripts\python.exe backend\scripts\import_neighborhoods.py C:\ruta\01_aguascalientes.zip
.\backend\.venv\Scripts\python.exe backend\scripts\import_neighborhoods.py C:\ruta\01_aguascalientes.zip --apply
.\backend\.venv\Scripts\python.exe backend\scripts\import_neighborhoods.py C:\ruta\01_aguascalientes.zip --verify
```

El primer comando del importador valida sin modificar la base; `--apply` hace la carga y la asignación. Un punto se asigna solo si `ST_Covers` encuentra exactamente un polígono del mismo municipio; cero o varias coincidencias dejan `neighborhood_id` en `NULL`. `--verify` comprueba permisos, RLS, correspondencia de incidentes y puntos interior, borde, superposición y exterior. La carga aplicada produjo 1 020 polígonos y 5 de 5 incidentes asignados; la verificación posterior pasó. Los reportes nuevos usan la misma regla y el filtro de lista y mapa se comprobó en el dashboard.

En el campo `CP` del ZIP, 39 polígonos tienen `00000`; el importador los guarda con `postal_code = NULL` porque no es un CP utilizable. Los otros registros contienen 132 códigos postales distintos de cinco dígitos. El dashboard busca por nombre y por prefijo de CP dentro del catálogo cargado para el funcionario; las opciones de asentamiento cambian al escribir. El CP sirve para encontrar una opción, pero la consulta de incidentes sigue usando el ID del polígono verificado.
