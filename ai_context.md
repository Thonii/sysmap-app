# AI Context - SysmapApp Integration

## 1. Current Status
El sistema SysmapApp está estructurado e independiente en `/home/thonii/proyectos/clientes/sysmap-app/`. Se compone de un frontend Next.js y un backend en Python/FastAPI que comparten una base de datos SQLite local para almacenamiento. Ambos componentes se exponen a través del proxy inverso global en la red externa `tecnoancon-proxy`.
El backend cuenta con scrapers de categorías extendidas para Eventbrite, un extractor seguro de Luma, Eventbrite y Meetup y un endpoint seguro `/events/import-url` blindado contra ataques SSRF, DoS por sobrecarga de descarga e inyecciones de código HTML/XSS.
El frontend tiene integrada la barra de importación rápida al lado del encabezado "Directorio" en la columna de eventos, la cual muestra la descripción expandible de los eventos de forma interactiva y fluida.

## 2. Recent Changes
- **Alineación y Refinamiento Estético de UI (Frontend):**
  * **Ubicación en Cabecera de Columna:** Movido el componente `<ImportEventBar />` para renderizarse a la derecha del título `Directorio` en `page.tsx` dentro de un contenedor flex.
  * **Ajuste de Botón Compacto:** Rediseñado el botón en estado colapsado a un formato súper compacto (`padding: 6px 12px`, `font-size: 0.75rem`, y texto simplificado a `+ Importar`) para que se alinee estéticamente a la par del título de la columna.
  * **Renderizado de Descripción en Producción:** Asegurada la copia del archivo actualizado `EventList.tsx` para corregir la ausencia del renderizado de descripción en el ambiente de producción.
- **Extractor de Luma Optimizador (JSON-LD Prioritized):**
  * **Extracción Robusta via JSON-LD:** Modificada la función `_extract_luma` en `url_extractor.py` para priorizar la extracción estructurada mediante el tag de metadatos `application/ld+json`. Esto resuelve los problemas de caídas en el fallback de Luma, logrando recuperar la **descripción real completa**, las **coordenadas de geolocalización exactas** y los **tiempos reales con offset de zona horaria** del evento.
- **Fix de Horarios y Zonas Horarias (FastAPI):**
  * **Serialización Timezone-Aware con Offset UTC:** Modificada la serialización de fechas en los endpoints `/events` y `/events/import-url` de `main.py` para verificar si las propiedades `start_time` y `end_time` son objetos `datetime` naive y aplicarles la zona horaria UTC (`replace(tzinfo=timezone.utc).isoformat()`). Esto corrige el desfase horario que provocaba que el navegador del usuario interpretara la hora UTC naive como local del sistema.
- **Sincronización y Despliegue en Producción:**
  * Transferidos todos los parches mediante SCP e implementados reiniciando/reconstruyendo los contenedores Docker en el directorio `/root/clientes/sysmap-app/`.
  * Verificado con éxito a través de peticiones HTTP en producción que los campos de hora devuelven el offset correcto y las descripciones largas se recuperan en su totalidad sin cortes.

## 3. Active Constraints
- **Base de Datos Compartida:** El backend y el frontend comparten el mismo archivo SQLite `sysmap.db` en el volumen `sysmap_db_data`. Se debe evitar cargas excesivas de escritura concurrente para no generar bloqueos de base de datos (`database is locked`).
- **Configuración de APIs externas:** El sistema requiere variables como `GEMINI_API_KEY`, `RESEND_API_KEY` y `EVENTBRITE_API_TOKEN` en el archivo `.env` del backend.
- **Formato de URL en Importación:** La importación manual de URLs espera enlaces bien formados que contengan las palabras clave `eventbrite`, `lu.ma`, `luma.com` o `meetup.com` y que resuelvan a IPs públicas globales válidas.

## 4. Pending Backlog
- **Estatus:** Completado y desplegado exitosamente en producción (`sysmap.tecnoancon.com`).
- **Siguientes Pasos:**
  1. Monitorear el comportamiento de la sincronización de horarios de eventos futuros en la aplicación y validar que los calendarios locales de los usuarios coincidan perfectamente.
  2. Ajustar políticas adicionales de CORS en backend si es que cambian los dominios secundarios en el proxy Traefik del cliente.
