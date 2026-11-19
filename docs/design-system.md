# Identidad visual de Pulso Urbano

## Dirección

El lenguaje combina cuatro ideas de las referencias entregadas: mapas suaves y capas claras (imagen 1), geometría simple como firma visual (imagen 2), acentos azules y cian (imagen 3) y tarjetas amplias con acciones directas (imagen 4). La geometría se limita al símbolo de marca y de carga; no compite con los datos. Se usa tipografía del sistema para mantener legibilidad y evitar descargas de fuentes.

## Tokens

| Uso | Color |
|---|---|
| Texto principal | `#142641` |
| Texto secundario | `#50647B` |
| Acción principal | `#1749A2` |
| Azul intenso | `#10367D` |
| Acento de orientación | `#00A6BC` |
| Acento secundario | `#7047B9` |
| Fondo | `#F4F7FB` |
| Superficie | `#FFFFFF` |
| Bordes | `#CBD7E4` |
| Éxito / resuelto | `#196B4B` sobre `#E9F7EF` |
| Advertencia / en revisión | `#895500` sobre `#FFF4D9` |
| Error / descartado | `#A42B40` sobre `#FFF0F2` |

Espaciado base: 4, 8, 16, 24 y 32 unidades. Títulos: 28–38 en web, 32 en móvil. Subtítulos: 21–22. Texto: 16–17. Botones y campos: al menos 44 px en web y 54 unidades en móvil. Bordes redondeados moderados; sombras muy suaves.

Los valores viven en `dashboard/src/index.css` y `mobile/theme.ts`. Son dos representaciones del mismo sistema porque CSS y React Native consumen estilos distintos. No se agregó una dependencia ni una capa de compilación compartida.

El logo aportado por el usuario combina una silueta urbana y una línea de pulso. Se adaptó a azul marino `#142641` y cian `#00A6BC`. El símbolo cuadrado está en `mobile/assets/pulso-icon.png`; su versión transparente para el icono adaptable Android está en `mobile/assets/pulso-foreground.png`. El dashboard usa la misma imagen en `dashboard/public/pulso-icon.png`. El indicador de carga anima ese símbolo con movimiento breve.

## Estados y acciones

La API actual usa `reported`, `in_review`, `confirmed`, `in_progress`, `resolved` y `discarded`. Sus colores son: azul, ámbar, azul, violeta, verde y rojo, respectivamente. Las etiquetas visibles mantienen el significado real: Reportado, En revisión, Confirmado, En atención, Resuelto y Descartado. **Canalizado** y **Rechazado** no son estados de la API; su incorporación requeriría una decisión de producto y cambios de backend. No se cambiaron etiquetas para simularlos.

Botones primarios: azul sólido. Secundarios: fondo azul claro y borde. Acciones destructivas: rojo; en el panel, guardar `discarded` usa ese tratamiento. Error, éxito y advertencia incluyen texto además de color. El foco de teclado tiene contorno cian. Los controles de opción móviles exponen su selección para lectores de pantalla.

## Movimiento y carga

El símbolo de ciudad y pulso se mueve pocos píxeles mientras hay una operación real en curso. Web respeta `prefers-reduced-motion`; móvil consulta la preferencia de movimiento reducido de React Native. El dashboard muestra esqueletos solo mientras espera la lista y un indicador sobre el mapa durante la carga. La app usa el símbolo durante peticiones y transcripción. No hay esperas artificiales.

## Flujos conservados

El formulario móvil mantiene categoría, descripción manual o por voz, duración opcional, gravedad, fotografías opcionales, GPS, revisión y envío. Los incidentes cercanos siguen disponibles como acción secundaria. El panel conserva acceso privado, mapa, búsqueda por colonia y CP, listas de activos/finalizados, detalle, fotografías, prioridad e historial. El rediseño no modifica API, esquema ni transiciones de estado.
