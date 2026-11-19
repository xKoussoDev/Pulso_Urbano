# PLATAFORMA DE INTELIGENCIA URBANA
## Sistema de recolección, procesamiento y visualización de problemáticas ciudadanas

**Versión:** 1.0  
**Tipo de entrega:** MVP funcional  
**Tiempo de desarrollo:** 2 días intensivos  
**Ubicación inicial:** Aguascalientes capital, México  
**Modelo de negocio:** B2G (Business to Government)

---

# 1. DESCRIPCIÓN GENERAL DEL PROYECTO

## 1.1. Concepto

Desarrollaremos una plataforma de inteligencia urbana que permita recolectar información sobre problemáticas que afectan a los ciudadanos, procesarla mediante herramientas de inteligencia artificial y representarla geográficamente para facilitar su análisis por parte del gobierno municipal.

La plataforma estará compuesta por dos interfaces independientes:

1. Una aplicación móvil para ciudadanos, mediante la cual podrán registrar problemáticas urbanas.
2. Un dashboard web privado para funcionarios gubernamentales, donde podrán visualizar, analizar y priorizar los incidentes reportados.

El sistema buscará transformar reportes individuales en información estructurada, georreferenciada y ponderada según su importancia.

## 1.2. Problemática que buscamos resolver

Las problemáticas urbanas suelen comunicarse mediante diferentes canales y de manera desorganizada. Esto dificulta identificar:

- Qué problemas existen.
- Dónde se concentran.
- Cuántas personas están afectadas.
- Cuáles requieren atención prioritaria.
- Qué zonas presentan mayores necesidades.
- Cómo evolucionan las problemáticas a lo largo del tiempo.

Nuestra propuesta consiste en centralizar esta información y convertirla en una herramienta de análisis territorial.

## 1.3. Propuesta de valor

Ofrecer al gobierno municipal una plataforma que permita transformar la participación ciudadana en información útil para la toma de decisiones.

El valor principal no es la aplicación móvil por sí sola, sino la capacidad de:

- Recolectar información ciudadana.
- Procesar reportes mediante inteligencia artificial.
- Clasificar y organizar incidentes.
- Identificar reportes relacionados.
- Geolocalizar problemáticas.
- Calcular niveles de prioridad.
- Visualizar las necesidades urbanas mediante un mapa interactivo.

---

# 2. MODELO DE NEGOCIO

## 2.1. Modelo B2G

El cliente objetivo es el gobierno municipal de Aguascalientes.

| Elemento | Definición |
|---|---|
| Cliente | Gobierno municipal |
| Usuario principal | Funcionarios autorizados |
| Fuente de información | Ciudadanos |
| Canal inicial | Aplicación móvil |
| Producto comercial | Plataforma de inteligencia urbana |
| Valor entregado | Información territorial organizada y priorizada |
| Mercado inicial | Aguascalientes capital |
| Expansión futura | Otros municipios y entidades |

## 2.2. Separación entre producto y canal de recolección

Es importante comprender que la aplicación móvil no constituye el producto comercial completo.

Es el primer canal mediante el cual se obtiene información.

El producto central es el sistema de procesamiento y visualización de datos para el gobierno.

Por esta razón, la arquitectura deberá permitir incorporar otros canales de recolección sin modificar la lógica central del sistema.

**Canales actuales y futuros:**

- Aplicación móvil: implementación inicial.
- WhatsApp Business: expansión futura.
- Portal web ciudadano: posible expansión.
- Integraciones institucionales: posible expansión.

---

# 3. ALCANCE GEOGRÁFICO Y FUNCIONAL

## 3.1. Alcance geográfico

El primer MVP estará limitado a Aguascalientes capital.

No desarrollaremos inicialmente una plataforma estatal ni multimunicipal.

Sin embargo, la base de datos y la arquitectura deberán permitir incorporar posteriormente otras ciudades.

## 3.2. Tipos de problemáticas

La aplicación permitirá registrar diferentes categorías de incidentes urbanos.

Categorías iniciales:

1. Falta de agua potable.
2. Fugas de agua.
3. Baches.
4. Calles deterioradas.
5. Falta de alumbrado público.
6. Luminarias dañadas.
7. Acumulación de basura.
8. Inundaciones.
9. Infraestructura urbana dañada.
10. Otros problemas urbanos.

Las categorías deberán manejarse mediante un catálogo centralizado para facilitar su ampliación.

---

# 4. USUARIOS Y PERMISOS

El sistema tendrá dos tipos principales de usuarios.

## 4.1. Ciudadanos

Podrán:

- Crear reportes.
- Describir problemáticas.
- Enviar fotografías.
- Registrar reportes mediante voz.
- Compartir su ubicación actual.
- Seleccionar manualmente una ubicación.
- Consultar la confirmación de su propio reporte.
- Confirmar un incidente existente cuando corresponda.

No podrán:

- Acceder al dashboard gubernamental.
- Consultar información privada de otros ciudadanos.
- Modificar la puntuación de prioridad.
- Eliminar o alterar reportes ajenos.

## 4.2. Funcionarios gubernamentales

Podrán:

- Iniciar sesión en el dashboard privado.
- Consultar los incidentes registrados.
- Visualizar reportes en un mapa.
- Filtrar por categoría, gravedad, colonia y estado.
- Consultar evidencias fotográficas.
- Revisar las confirmaciones ciudadanas.
- Consultar la puntuación de prioridad.
- Actualizar el estado de atención de un incidente.
- Consultar estadísticas generales.

El acceso estará protegido mediante autenticación y autorización por roles.

---

# 5. FUNCIONALIDADES DEL MVP

El desarrollo se concentrará en demostrar el siguiente flujo completo.

## 5.1. Aplicación móvil ciudadana

### A. Pantalla principal

Debe incluir:

- Identidad visual del proyecto.
- Botón para crear un reporte.
- Acceso al reporte inteligente por voz.
- Acceso al formulario tradicional.
- Información básica sobre el funcionamiento.

### B. Creación de reportes

El usuario podrá registrar:

- Categoría.
- Descripción.
- Ubicación geográfica.
- Fotografía como evidencia.
- Fecha y hora.

La ubicación será un dato obligatorio para registrar un incidente en el mapa.

### C. Reportes inteligentes mediante voz

Esta será una de las funcionalidades diferenciadoras del proyecto.

El usuario podrá describir verbalmente el problema.

Ejemplo:

"Hay una fuga de agua bastante grande afuera de mi casa, lleva aproximadamente tres días y ya está inundando parte de la calle".

El sistema procesará la información y propondrá los campos correspondientes.

Ejemplo de resultado:

- Categoría: fuga de agua.
- Descripción: fuga de agua que provoca inundación parcial de la calle.
- Duración: aproximadamente tres días.
- Gravedad: alta, propuesta por la IA.
- Ubicación: pendiente.
- Fotografía: opcional.

La aplicación mostrará los campos identificados y solicitará únicamente la información faltante.

### D. Ubicación

Se ofrecerán dos métodos:

1. Utilizar la ubicación actual del dispositivo.
2. Seleccionar manualmente un punto en el mapa o introducir una dirección.

La ubicación deberá almacenarse mediante coordenadas geográficas de latitud y longitud.

### E. Confirmación

Antes de enviar el reporte, el ciudadano podrá revisar y editar:

- Categoría.
- Descripción.
- Gravedad propuesta.
- Ubicación.
- Fotografía.

El usuario deberá confirmar el envío.

### F. Registro

Al confirmar, el sistema guardará el reporte y devolverá un identificador único.

---

## 5.2. Dashboard gubernamental privado

El dashboard será una aplicación web independiente.

### A. Inicio de sesión

- Autenticación de funcionarios.
- Protección de rutas.
- Control de permisos.
- Cierre de sesión.

### B. Panel de indicadores

Indicadores principales:

- Total de incidentes activos.
- Total de reportes recibidos.
- Incidentes críticos.
- Incidentes pendientes.
- Incidentes atendidos.
- Incidentes resueltos.

### C. Mapa interactivo

Será el componente central del dashboard.

Permitirá:

- Visualizar los incidentes geográficamente.
- Diferenciar categorías mediante colores o iconos.
- Representar niveles de prioridad.
- Consultar detalles al seleccionar un marcador.
- Filtrar incidentes.
- Identificar concentraciones de problemas.

### D. Filtros

- Categoría.
- Gravedad.
- Nivel de prioridad.
- Colonia.
- Fecha.
- Estado del incidente.

### E. Detalles del incidente

Al seleccionar un incidente se mostrarán:

- Identificador.
- Categoría.
- Descripción.
- Ubicación.
- Fecha de creación.
- Evidencia fotográfica.
- Número de reportes asociados.
- Gravedad estimada.
- Puntuación de prioridad.
- Nivel de confianza.
- Estado de atención.

### F. Gestión de incidentes

Estados iniciales:

1. Reportado.
2. En revisión.
3. Confirmado.
4. En atención.
5. Resuelto.
6. Descartado.

Debe conservarse el historial de cambios de estado.

---

# 6. INTELIGENCIA ARTIFICIAL

La inteligencia artificial deberá resolver problemas reales dentro de la plataforma.

No se utilizará únicamente como elemento demostrativo.

## 6.1. Reportes inteligentes por voz

**Prioridad P0.**

Tecnologías:

- Whisper o faster-whisper.
- LLM mediante API.
- FastAPI para coordinar el procesamiento.
- Validación de esquemas JSON.

### Flujo

1. El ciudadano graba una descripción.
2. La aplicación envía el audio al backend.
3. Whisper convierte el audio en texto.
4. El LLM interpreta la descripción.
5. El LLM devuelve información estructurada.
6. FastAPI valida los campos.
7. Se identifican los campos faltantes.
8. React Native muestra un formulario dinámico.
9. El ciudadano completa la información faltante.
10. El usuario confirma.
11. Se registra el reporte en Supabase.

### Ejemplo de salida estructurada

    {
      "category": "fuga_de_agua",
      "description": "Fuga de agua que provoca inundación parcial de la calle",
      "duration": "3 días",
      "severity": "high",
      "location": null,
      "missing_fields": ["location"],
      "confidence": 0.92
    }

Este JSON es ilustrativo. La estructura definitiva deberá validarse mediante un esquema compartido entre backend y frontend.

### Responsabilidades de cada tecnología

| Tecnología | Responsabilidad |
|---|---|
| Whisper | Transcribir audio |
| LLM | Extraer y estructurar información |
| FastAPI | Validar y procesar resultados |
| React Native | Mostrar campos y solicitar información faltante |
| Supabase | Guardar el reporte confirmado |

El LLM no deberá inventar ubicaciones, coordenadas, fotografías ni datos que el ciudadano no haya proporcionado.

La gravedad será una propuesta basada en criterios definidos y deberá poder ser corregida antes de enviar el reporte.

## 6.2. Clasificación automática mediante visión artificial

**Prioridad P1.**

En una etapa posterior se incorporará un modelo de visión por computadora que analice las fotografías.

Objetivos:

- Identificar baches.
- Detectar acumulación de basura.
- Identificar fugas de agua.
- Detectar inundaciones.
- Identificar infraestructura dañada.

También podrá estimar características visuales relacionadas con la gravedad.

Se podrán evaluar modelos preentrenados como YOLO o MobileNet.

No se entrenará un modelo desde cero durante el MVP.

## 6.3. Detección de reportes duplicados

**Prioridad P1.**

Tecnologías propuestas:

- all-MiniLM-L6-v2.
- Embeddings.
- pgvector.
- PostGIS.
- Análisis de proximidad temporal y geográfica.

Objetivo:

Evitar que múltiples reportes sobre un mismo problema se conviertan en incidentes independientes.

Ejemplo:

Treinta ciudadanos reportan un mismo bache.

El sistema deberá poder asociar los treinta reportes a un solo incidente, conservando las confirmaciones individuales.

Para el MVP se puede implementar una primera versión mediante proximidad geográfica, categoría y tiempo. La comparación semántica avanzada se incorporará posteriormente.

## 6.4. Detección de spam y reportes falsos

**Prioridad P2.**

Se evaluarán:

- Frecuencia de reportes por usuario.
- Repetición de contenido.
- Consistencia geográfica.
- Coincidencia de evidencias.
- Confirmaciones de otros ciudadanos.
- Historial de reportes.

La confianza de un reporte no deberá confundirse con su gravedad.

---

# 7. SISTEMA DE PONDERACIÓN Y PRIORIZACIÓN

El sistema de ponderación será uno de los elementos centrales del producto.

No queremos representar únicamente cuántos reportes existen, sino qué tan importante es atender cada problemática.

## 7.1. Variables de ponderación

Se proponen cinco dimensiones:

| Variable | Descripción |
|---|---|
| G | Gravedad del incidente |
| A | Alcance o población potencialmente afectada |
| C | Confirmaciones de ciudadanos únicos |
| T | Tiempo sin resolver |
| V | Vulnerabilidad o importancia territorial |

## 7.2. Fórmula inicial

Se utilizará un modelo de puntuación normalizada:

    P = (wG × G) + (wA × A) + (wC × C)
        + (wT × T) + (wV × V)

Donde:

- P: puntuación de prioridad.
- w: peso asignado a cada variable.
- Cada variable deberá estar normalizada en una escala de 0 a 100.
- La suma de los pesos deberá ser igual a 1.

Los pesos iniciales serán configurables y deberán justificarse mediante criterios de impacto social.

La puntuación no será una medición científica de la necesidad real, sino un indicador de apoyo a la priorización gubernamental.

## 7.3. Reglas fundamentales

1. La cantidad de reportes no determinará por sí sola la prioridad.
2. La gravedad tendrá una influencia importante.
3. Se considerará la población potencialmente afectada.
4. Se evitará premiar automáticamente a las colonias con mayor conectividad.
5. Los reportes duplicados deberán agruparse.
6. Se distinguirá entre reportes ciudadanos e incidentes.
7. Los funcionarios podrán consultar cómo se obtuvo la puntuación.
8. Los datos insuficientes deberán identificarse explícitamente.

## 7.4. Representación visual

Se utilizarán niveles de prioridad:

- Crítica.
- Alta.
- Media.
- Baja.

La escala de colores será consistente en todo el dashboard.

Los umbrales se definirán durante la implementación y podrán ajustarse después de probar el modelo.

---

# 8. ARQUITECTURA TECNOLÓGICA

## 8.1. Stack tecnológico

| Capa | Tecnología |
|---|---|
| Aplicación móvil | React Native + Expo |
| Lenguaje móvil | TypeScript |
| Dashboard web | React + TypeScript |
| Backend | Python + FastAPI |
| Base de datos | Supabase PostgreSQL |
| Autenticación | Supabase Auth |
| Almacenamiento de imágenes | Supabase Storage |
| Consultas geográficas | PostGIS |
| Mapas | Mapbox |
| Transcripción de audio | Whisper / faster-whisper |
| IA generativa | LLM mediante API |
| Embeddings | all-MiniLM-L6-v2 |
| Búsqueda vectorial | pgvector |
| Control de versiones | Git + GitHub |

## 8.2. Justificación

### React Native + Expo

Permite desarrollar la aplicación móvil para Android y iOS utilizando una misma base de código.

Se utilizará para:

- Captura de audio.
- Captura de fotografías.
- Geolocalización.
- Formularios.
- Navegación.

### React + TypeScript

Se utilizará para desarrollar el dashboard gubernamental.

La aplicación web estará separada de la aplicación móvil, pero compartirá backend y base de datos.

### FastAPI

Será el núcleo de procesamiento del sistema.

Responsabilidades:

- Recibir solicitudes.
- Procesar audios.
- Comunicarse con Whisper.
- Comunicarse con el LLM.
- Validar información.
- Ejecutar reglas de negocio.
- Registrar reportes.
- Calcular prioridades.
- Administrar incidentes.

### Supabase

Se utilizará como infraestructura de datos.

Servicios:

- PostgreSQL.
- Autenticación.
- Almacenamiento de fotografías.
- Seguridad mediante Row Level Security.
- Extensiones geográficas.
- Extensiones vectoriales cuando sean necesarias.

**Recomendación:** mantener la lógica de negocio y las integraciones de IA en FastAPI. Supabase será la infraestructura de persistencia, autenticación y almacenamiento, no el sustituto de todo el backend.

---

# 9. ARQUITECTURA GENERAL DEL SISTEMA

La arquitectura deberá mantener separadas las interfaces y la lógica de negocio.

    CIUDADANO
        |
        v
    REACT NATIVE + EXPO
        |
        | HTTPS / REST
        v
    FASTAPI
        |
        |---- Whisper
        |       |
        |       v
        |    Transcripción
        |
        |---- LLM
        |       |
        |       v
        |    Extracción estructurada
        |
        |---- Validación de campos
        |
        |---- Lógica de reportes
        |
        |---- Cálculo de prioridad
        |
        v
    SUPABASE
        |
        |---- PostgreSQL
        |---- PostGIS
        |---- Auth
        |---- Storage
        |
        v
    REACT + TYPESCRIPT
        |
        v
    DASHBOARD GUBERNAMENTAL PRIVADO

La futura integración de WhatsApp deberá ingresar por el mismo backend y reutilizar los servicios de procesamiento y registro.

## 9.1. Principio de escalabilidad

La lógica central de creación de reportes no debe depender de la aplicación móvil.

Debe existir un servicio independiente que reciba información estructurada y permita registrar reportes desde distintos canales.

Esto facilitará incorporar WhatsApp Business sin reconstruir la base de datos ni el dashboard.

---

# 10. MODELO DE DATOS INICIAL

La base de datos deberá diferenciar los incidentes de los reportes individuales.

## 10.1. Tabla: users

Información de los usuarios.

Campos sugeridos:

- id
- name
- phone
- role
- created_at

Los datos personales deberán mantenerse separados de la información pública o analítica de los incidentes.

## 10.2. Tabla: categories

Catálogo de problemáticas.

Campos:

- id
- name
- description
- default_severity
- active

Ejemplos: bache, fuga de agua, inundación y alumbrado público.

## 10.3. Tabla: incidents

Representa un problema urbano identificado.

Campos:

- id
- category_id
- title
- description
- latitude
- longitude
- location_description
- severity
- confidence_score
- priority_score
- status
- reports_count
- created_at
- updated_at
- resolved_at

## 10.4. Tabla: reports

Representa cada comunicación ciudadana.

Campos:

- id
- user_id
- incident_id
- category_id
- description
- original_transcription
- latitude
- longitude
- image_url
- source
- ai_processed
- created_at

La fuente permitirá distinguir:

- mobile_app
- whatsapp
- web

WhatsApp será una fuente futura, no una integración del MVP.

## 10.5. Tabla: incident_confirmations

Permite registrar confirmaciones de ciudadanos.

Campos:

- id
- incident_id
- user_id
- report_id
- created_at

Debe evitarse que un mismo usuario incremente repetidamente la cantidad de confirmaciones de un incidente.

## 10.6. Tabla: incident_status_history

Registra cambios de estado.

Campos:

- id
- incident_id
- previous_status
- new_status
- changed_by
- notes
- created_at

## 10.7. Tabla: priority_history

Permite conservar la evolución de las puntuaciones.

Campos:

- id
- incident_id
- previous_score
- new_score
- calculation_version
- created_at

## 10.8. Relaciones principales

- Un usuario puede generar múltiples reportes.
- Una categoría puede estar asociada a múltiples incidentes.
- Un incidente puede tener múltiples reportes.
- Un incidente puede tener múltiples confirmaciones.
- Un incidente puede tener múltiples cambios de estado.
- Un incidente puede tener múltiples registros históricos de prioridad.

La estructura deberá implementarse mediante relaciones y restricciones de integridad referencial.

---

# 11. ESTRUCTURA DE CARPETAS DEL PROYECTO

Se recomienda un monorepositorio para mantener los componentes organizados.

    urban-intelligence/
    |
    |-- mobile/
    |   |-- src/
    |   |   |-- components/
    |   |   |-- screens/
    |   |   |-- navigation/
    |   |   |-- services/
    |   |   |-- hooks/
    |   |   |-- types/
    |   |   |-- utils/
    |   |   |-- assets/
    |   |
    |   |-- app.json
    |   |-- package.json
    |   |-- tsconfig.json
    |
    |-- dashboard/
    |   |-- src/
    |   |   |-- components/
    |   |   |-- pages/
    |   |   |-- layouts/
    |   |   |-- services/
    |   |   |-- hooks/
    |   |   |-- types/
    |   |   |-- utils/
    |   |   |-- maps/
    |   |
    |   |-- package.json
    |
    |-- backend/
    |   |-- app/
    |   |   |-- api/
    |   |   |-- core/
    |   |   |-- models/
    |   |   |-- schemas/
    |   |   |-- services/
    |   |   |-- repositories/
    |   |   |-- ai/
    |   |   |   |-- transcription/
    |   |   |   |-- extraction/
    |   |   |   |-- embeddings/
    |   |   |   |-- classification/
    |   |   |
    |   |   |-- main.py
    |   |
    |   |-- requirements.txt
    |   |-- .env.example
    |
    |-- database/
    |   |-- migrations/
    |   |-- seeds/
    |   |-- schema.sql
    |
    |-- docs/
    |   |-- architecture.md
    |   |-- api.md
    |   |-- data-model.md
    |   |-- whatsapp-roadmap.md
    |
    |-- PROJECT_STATUS.md
    |-- README.md
    |-- .gitignore

Esta estructura es una propuesta inicial. Puede simplificarse durante el MVP, siempre que se mantenga la separación de responsabilidades.

---

# 12. API DEL BACKEND

Los endpoints principales deberán organizarse por dominio.

## 12.1. Procesamiento de IA

### POST /api/v1/ai/transcribe

Recibe audio y devuelve la transcripción.

### POST /api/v1/ai/extract-report

Recibe texto y devuelve información estructurada.

Ejemplo de respuesta:

    {
      "category": "bache",
      "description": "Bache profundo en avenida Universidad",
      "severity": "high",
      "missing_fields": ["location"]
    }

### POST /api/v1/ai/process-voice-report

Endpoint opcional que coordina transcripción y extracción en una sola operación.

## 12.2. Reportes

### POST /api/v1/reports

Crea un reporte después de validar la información.

### GET /api/v1/reports/me

Consulta los reportes del usuario autenticado.

### GET /api/v1/reports/{id}

Consulta los detalles de un reporte autorizado.

## 12.3. Incidentes

### GET /api/v1/incidents

Obtiene incidentes con filtros.

### GET /api/v1/incidents/{id}

Obtiene los detalles de un incidente.

### PATCH /api/v1/incidents/{id}/status

Actualiza su estado. Solamente funcionarios autorizados podrán ejecutar esta operación.

### GET /api/v1/incidents/map

Devuelve los incidentes necesarios para representar el mapa, aplicando filtros y límites geográficos.

## 12.4. Dashboard

### GET /api/v1/dashboard/metrics

Devuelve los indicadores generales.

### GET /api/v1/dashboard/priorities

Devuelve los incidentes ordenados por prioridad.

Los endpoints gubernamentales deberán requerir autenticación y permisos administrativos.

---

# 13. SEGURIDAD Y PRIVACIDAD

La plataforma manejará ubicaciones, fotografías y posibles datos personales.

Se deberán considerar las siguientes medidas:

1. Autenticación de usuarios.
2. Autorización por roles.
3. Row Level Security en Supabase.
4. Protección de endpoints privados.
5. Validación de archivos y formatos.
6. Restricción de tamaño de fotografías y audios.
7. Protección de claves y variables de entorno.
8. Acceso restringido a evidencias.
9. Separación entre información ciudadana e información analítica.
10. Política de privacidad y consentimiento informado.

La clave administrativa de Supabase nunca deberá incluirse en React Native ni en el frontend web.

Los usuarios ciudadanos solamente podrán acceder a sus propios reportes y operaciones autorizadas.

El dashboard tendrá acceso a la información administrativa mediante permisos específicos.

---

# 14. ROADMAP DE DESARROLLO

## FASE 1. MVP — Dos días intensivos

### Día 1: Infraestructura y recolección de información

**Objetivo:** conseguir que un ciudadano pueda generar un reporte y almacenarlo correctamente.

Tareas:

1. Crear repositorio y estructura del proyecto.
2. Configurar React Native + Expo.
3. Configurar React + TypeScript para dashboard.
4. Crear proyecto de Supabase.
5. Diseñar e implementar tablas iniciales.
6. Configurar FastAPI.
7. Implementar autenticación y permisos básicos.
8. Crear formulario tradicional de reportes.
9. Implementar captura de ubicación.
10. Implementar carga de fotografías si el tiempo lo permite.
11. Conectar el backend con Supabase.
12. Probar creación y recuperación de reportes.

**Entregable del día 1:** aplicación móvil conectada al backend y base de datos, capaz de registrar reportes georreferenciados.

### Día 2: IA, visualización y demostración

**Objetivo:** demostrar cómo la información recolectada se transforma en inteligencia territorial.

Tareas:

1. Integrar Whisper.
2. Integrar LLM para extracción estructurada.
3. Implementar detección de campos faltantes.
4. Crear formulario dinámico en React Native.
5. Implementar confirmación del reporte.
6. Crear dashboard privado.
7. Integrar mapa interactivo.
8. Visualizar incidentes.
9. Implementar filtros básicos.
10. Implementar puntuación de prioridad.
11. Crear indicadores principales.
12. Probar el flujo completo.

**Entregable del día 2:** MVP demostrable de principio a fin.

---

# 15. FUNCIONALIDADES FUERA DEL MVP

Estas funcionalidades no deben comprometer la entrega inicial.

## Segunda etapa

- Integración con WhatsApp Business Cloud API.
- Clasificación automática avanzada de fotografías.
- Agrupación semántica de reportes duplicados.
- Confirmación avanzada de incidentes.
- Panel de seguimiento institucional.
- Notificaciones.
- Reportes ejecutivos automáticos.

## Tercera etapa

- Detección pasiva de baches mediante acelerómetro y giroscopio.
- Predicción de zonas de riesgo.
- Análisis de patrones temporales.
- Integración con información meteorológica.
- Rutas que eviten incidentes.
- Análisis de fotografías con modelos especializados.

## Cuarta etapa

- Expansión a otros municipios.
- Multi-tenancy.
- Diferentes perfiles gubernamentales.
- Integraciones institucionales.
- Indicadores de desempeño municipal.
- Herramientas de planeación y asignación de recursos.

---

# 16. ESCALABILIDAD: FUTURA INTEGRACIÓN CON WHATSAPP

La integración de WhatsApp es una evolución prevista desde el diseño.

No se implementará en el primer entregable.

El flujo futuro será:

1. El ciudadano envía un mensaje a un número oficial.
2. WhatsApp Business envía el evento al webhook de FastAPI.
3. El backend identifica el tipo de contenido.
4. Si es audio, utiliza Whisper.
5. Si es texto, utiliza directamente el servicio de extracción.
6. Si es fotografía, procesa la evidencia.
7. El LLM identifica los datos disponibles.
8. El chatbot solicita la información faltante.
9. El ciudadano comparte su ubicación.
10. El backend valida la información.
11. Se crea el reporte.
12. El dashboard gubernamental muestra el nuevo incidente.

La lógica de negocio y el modelo de datos serán los mismos para ambos canales.

---

# 17. CRITERIOS DE ÉXITO DEL MVP

El MVP se considerará funcional cuando se pueda demostrar el siguiente escenario:

1. Un ciudadano abre la aplicación móvil.
2. Describe un problema mediante voz.
3. El audio llega al backend.
4. Whisper genera la transcripción.
5. El LLM identifica categoría, descripción y gravedad propuesta.
6. El sistema detecta que falta la ubicación.
7. La aplicación solicita la ubicación.
8. El ciudadano utiliza GPS o selecciona un punto manualmente.
9. Se presenta un resumen editable.
10. El ciudadano confirma el reporte.
11. El backend registra el reporte en Supabase.
12. El incidente aparece en el dashboard privado.
13. El mapa representa su ubicación y prioridad.
14. El funcionario puede consultar sus detalles.

También deberá comprobarse el flujo tradicional de creación de reportes.

No consideraremos una funcionalidad terminada hasta haberla probado.

---

# 18. MÉTRICAS PARA EVALUAR EL PROYECTO

## Métricas técnicas

- Tiempo promedio de procesamiento de audio.
- Porcentaje de transcripciones correctas.
- Porcentaje de extracción estructurada válida.
- Porcentaje de reportes completados correctamente.
- Tiempo de respuesta del backend.
- Precisión de la detección de duplicados cuando se implemente.

## Métricas de producto

- Cantidad de reportes recibidos.
- Cantidad de incidentes identificados.
- Número de ciudadanos participantes.
- Distribución por categorías.
- Distribución territorial.
- Tiempo promedio de atención.
- Porcentaje de incidentes resueltos.

## Métricas de impacto

- Zonas con mayor concentración de problemáticas.
- Problemas de mayor gravedad.
- Población potencialmente afectada.
- Evolución de problemáticas por periodo.
- Diferencia entre reportes recibidos e incidentes atendidos.

Estas métricas deberán presentarse como indicadores de apoyo a la gestión, no como evidencia automática de causalidad o impacto social.

---

# 19. PRINCIPIOS OBLIGATORIOS DE DESARROLLO

1. Priorizar un MVP funcional sobre una plataforma excesivamente compleja.
2. Respetar el límite de dos días.
3. Evitar funcionalidades que no aporten al objetivo principal.
4. Mantener separadas las responsabilidades del frontend, backend y base de datos.
5. No duplicar lógica de negocio entre aplicaciones.
6. No almacenar datos sin validar.
7. No permitir que la IA invente información.
8. Validar las salidas del LLM mediante esquemas.
9. Mantener un historial de cambios relevantes.
10. Utilizar variables de entorno para credenciales.
11. Documentar decisiones técnicas.
12. Probar cada funcionalidad antes de continuar.
13. Mantener la arquitectura preparada para WhatsApp.
14. No afirmar que una funcionalidad está terminada si no ha sido probada.

---

# 20. METODOLOGÍA DE TRABAJO CON EL EQUIPO DE DESARROLLO

El equipo de desarrollo deberá trabajar de forma iterativa.

Antes de cada implementación deberá:

1. Explicar qué se construirá.
2. Identificar archivos que se crearán o modificarán.
3. Justificar las decisiones técnicas importantes.
4. Proporcionar código completo cuando sea conveniente.
5. Explicar cómo ejecutarlo.
6. Definir cómo probarlo.
7. Esperar la validación antes de avanzar a la siguiente etapa.

No se deberán realizar cambios masivos sin entender primero la arquitectura y el estado actual del proyecto.

## Control de avance

Se mantendrá un archivo `PROJECT_STATUS.md` con:

- Porcentaje de avance.
- Funcionalidades terminadas y verificadas.
- Funcionalidades pendientes.
- Errores conocidos.
- Decisiones técnicas.
- Próxima tarea.
- Tiempo restante.

Las prioridades se clasificarán así:

- P0: indispensable para la demostración.
- P1: importante, pero simplificable.
- P2: mejora opcional.
- P3: fuera del alcance actual.

---

# 21. PRIMERA INSTRUCCIÓN PARA INICIAR EL DESARROLLO

Antes de comenzar a programar, el equipo deberá:

1. Revisar el documento completo.
2. Identificar riesgos técnicos y dependencias.
3. Validar la compatibilidad del stack tecnológico.
4. Proponer una estructura definitiva de repositorio.
5. Definir el esquema inicial de Supabase.
6. Definir los contratos de comunicación entre React Native, FastAPI y el dashboard.
7. El servicio de IA generativa será con Gemini API(modelo con cuato gratuita)
8. Definir cómo se desplegará FastAPI para permitir que las aplicaciones se comuniquen con él.
9. Establecer el cronograma realista de dos días.

No comenzar a programar hasta presentar el plan técnico inicial.

---

# 22. VISIÓN FINAL DEL PRODUCTO

El proyecto busca desarrollar una plataforma de inteligencia urbana que permita a los gobiernos municipales comprender mejor las necesidades de sus ciudadanos mediante información geográfica, participación comunitaria e inteligencia artificial.

El MVP demostrará el funcionamiento de este modelo en Aguascalientes capital.

La aplicación móvil será el primer canal de recolección de información, mientras que el dashboard privado será la herramienta de análisis y visualización para el gobierno.

La arquitectura se diseñará para evolucionar hacia una plataforma multicanal, incorporando WhatsApp y otras fuentes de información sin reconstruir el sistema central.

**Objetivo final: convertir reportes ciudadanos dispersos en información territorial estructurada, priorizada y útil para la toma de decisiones gubernamentales.**