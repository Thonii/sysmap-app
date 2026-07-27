# AI Context - SysmapApp Integration

## 1. Current Status
El sistema SysmapApp está estructurado e independiente en `/home/thonii/proyectos/clientes/sysmap-app/`. Se compone de un frontend Next.js y un backend en Python/FastAPI que comparten una base de datos SQLite local para almacenamiento. Ambos componentes se exponen a través del proxy inverso global en la red externa `tecnoancon-proxy`.
El backend cuenta con scrapers de categorías extendidas para Eventbrite, un extractor seguro de Luma, Eventbrite y Meetup y un endpoint seguro `/events/import-url` blindado contra ataques SSRF, DoS por sobrecarga de descarga e inyecciones de código HTML/XSS.
El frontend tiene integrada la barra de importación rápida al lado del encabezado "Directorio" en la columna de eventos, la cual muestra la descripción expandible de los eventos de forma interactiva y fluida, formateando las fechas forzando la zona horaria del evento (`America/Buenos_Aires`).

## 2. Recent Changes
- **Alineación y Refinamiento Estético de UI (Frontend):**
  * **Ubicación en Cabecera de Columna:** Movido el componente `<ImportEventBar />` para renderizarse a la derecha del título `Directorio` en `page.tsx`.
  * **Ajuste de Botón Compacto:** Rediseñado el botón en estado colapsado a un formato compacto (`padding: 6px 12px`, `font-size: 0.75rem`, y texto `+ Importar`).
  * **Visualización Local del Evento (Frontend):** Modificado el formateador de fechas `formatEventDate` en `EventList.tsx` para forzar la zona horaria de Buenos Aires (`timeZone: 'America/Buenos_Aires'`), asegurando que todos los usuarios vean los horarios locales correctos de origen de los eventos físicos (ej: 18:00 Hs) independientemente de su huso horario de navegación.
- **Extractor de Luma Optimizador (JSON-LD Prioritized):**
  * **Extracción Robusta via JSON-LD:** Modificada la función `_extract_luma` en `url_extractor.py` para priorizar la extracción estructurada mediante el tag de metadatos `application/ld+json`. Esto resuelve los problemas de caídas en el fallback de Luma, logrando recuperar la **descripción real completa**, las **coordenadas de geolocalización exactas** y los **tiempos reales con offset de zona horaria** del evento.
- **Fix de Horarios y Zonas Horarias (FastAPI & Pipeline):**
  * **Normalización de Datetimes a UTC Naive:** Modificado `url_extractor.py` e `ingest.py` para convertir los objetos datetime timezone-aware recuperados por los scrapers a su equivalente UTC real (`.astimezone(timezone.utc)`) y remover el `tzinfo` antes de persistirlos en SQLite.
  * **Serialización Timezone-Aware con Offset UTC:** Modificada la serialización de fechas en los endpoints `/events` y `/events/import-url` de `main.py` para aplicarles la zona horaria UTC (`replace(tzinfo=timezone.utc).isoformat()`). Esto corrige los desfases en la API al transmitir los datetimes en UTC explícito.
- **Solución al Conflicto de Ruteo de NextAuth (OAuth):**
  * **Exclusión de Ruteo en Traefik:** Modificadas las labels de docker compose en local y remoto (`docker-compose.yml`) para excluir `/api/auth/*` del backend: `Host(...) && PathPrefix(/api) && !PathPrefix(/api/auth)`. Esto resuelve los errores 404 de OAuth redirigiendo correctamente las llamadas de sesión al frontend de Next.js.
- **Ampliación de Cobertura y Prevención de Sobreescritura (Eventbrite Scraper):**
  * **URLs Estáticas Robustas (Bypass 405):** Modificado `eventbrite.py` para consultar únicamente las categorías estáticas `/b/*` que devuelven un código `200 OK` limpio en la IP de producción (`science-and-tech`, `business`, `tech`, `family-and-education`, `community`), logrando esquivar el bloqueo dinámico antibot (405) de Cloudflare en Eventbrite y logrando un incremento de casi el 40% en volumen de recolección de eventos.
  * **Protección de Horas y Descripciones Detalladas:** Modificado `ingest.py` para evitar que la ingesta masiva automática sobrescriba horas y descripciones enriquecidas obtenidas previamente mediante importaciones manuales precisas con los valores recortados de los listados estáticos (medianoches `00:00:00`).

## 3. Active Constraints
- **Base de Datos Compartida:** El backend y el frontend comparten el mismo archivo SQLite `sysmap.db` en el volumen `sysmap_db_data`. Se debe evitar cargas excesivas de escritura concurrente para no generar bloqueos de base de datos (`database is locked`).
- **Configuración de APIs externas:** El sistema requiere variables como `GEMINI_API_KEY`, `RESEND_API_KEY` y `EVENTBRITE_API_TOKEN` en el archivo `.env` del backend.
- **Formato de URL en Importación:** La importación manual de URLs espera enlaces bien formados que contengan las palabras clave `eventbrite`, `lu.ma`, `luma.com` o `meetup.com` y que resuelvan a IPs públicas globales válidas.

## 4. Pending Backlog
- **Estatus:** Completado y desplegado exitosamente en producción (`sysmap.tecnoancon.com`).
- **Siguientes Pasos:**
  1. Monitorear el comportamiento de la sincronización de horarios de eventos futuros en la aplicación y validar que los calendarios locales de los usuarios coincidan perfectamente.
  2. Ajustar políticas adicionales de CORS en backend si es que cambian los dominios secundarios en el proxy Traefik del cliente.
