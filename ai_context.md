# AI Context - SysmapApp Integration

## 1. Current Status
El sistema SysmapApp está estructurado e independiente en `/home/thonii/proyectos/clientes/sysmap-app/`. Se compone de un frontend Next.js y un backend en Python/FastAPI que comparten una base de datos SQLite local para almacenamiento. Ambos componentes se exponen a través del proxy inverso global en la red externa `tecnoancon-proxy`.
El backend cuenta con scrapers de categorías extendidas para Eventbrite y un endpoint seguro `/events/import-url` blindado contra ataques SSRF, DoS por sobrecarga de descarga e inyecciones de código HTML/XSS. El frontend tiene integrada la barra de importación rápida al lado del encabezado "Directorio" en la columna de eventos.

## 2. Recent Changes
- **Alineación y Refinamiento Estético de UI (Frontend):**
  * **Ubicación en Cabecera de Columna:** Movido el componente `<ImportEventBar />` para renderizarse a la derecha del título `Directorio` en `page.tsx` dentro de un contenedor flex. Esto asocia directamente la acción de importar con el listado de eventos y lo quita del espacio flotante entre paneles.
  * **Ajuste de Botón Compacto:** Rediseñado el botón en estado colapsado a un formato súper compacto (`padding: 6px 12px`, `font-size: 0.75rem`, y texto simplificado a `+ Importar`) para que se alinee estéticamente a la par del título de la columna.
  * **Expansión Inline Fluidas:** Al hacer clic en el botón de importar, el formulario se expande de forma completa ocupando el 100% de la columna justo debajo del título.
- **Blindaje de Seguridad en Ingesta de URLs:**
  * **Whitelist de Dominios:** Restringida la ingesta únicamente a dominios oficiales de Eventbrite, Luma y Meetup en `url_extractor.py`.
  * **Mitigación SSRF:** Implementada resolución DNS previa con validación de IP (bloqueo de loopback, IPs privadas RFC 1918, link-local, reservadas y no especificadas).
  * **Mitigación DoS:** Reemplazado `client.get` por `client.stream`. Se valida que el `Content-Type` sea text/html y que el `Content-Length` sea menor a 5 MB. Se limita la lectura a un máximo acumulativo de 5 MB de datos por request.
  * **Sanitización HTML/XSS:** Implementado `sanitize_string` en el backend para limpiar recursivamente etiquetas HTML de los títulos, descripciones, lugares y direcciones de eventos antes de guardarse en SQLite.
- **Suite de Pruebas de Seguridad robustecida:**
  * Añadidos 5 tests unitarios a `test_url_extractor.py` validando esquemas inválidos, SSRF Localhost, SSRF IP privada, DoS por tamaño de archivo y sanitización de código HTML. La suite completa pasa exitosamente (`14 passed`).
- **Scraper Ampliado de Eventbrite:**
  * Modificado `scrape_eventbrite_html_public` para iterar y recopilar eventos públicos de las categorías `science-and-tech`, `business` y `tech`. Esto incrementó los eventos públicos recuperados de Eventbrite de 8 a 20 en la última corrida.
  * Añadida de-duplicación por `source_id` para evitar redundancias de eventos pertenecientes a múltiples categorías.

## 3. Active Constraints
- **Base de Datos Compartida:** El backend y el frontend comparten el mismo archivo SQLite `sysmap.db` en el volumen `sysmap_db_data`. Se debe evitar cargas excesivas de escritura concurrente para no generar bloqueos de base de datos (`database is locked`).
- **Configuración de APIs externas:** El sistema requiere variables como `GEMINI_API_KEY`, `RESEND_API_KEY` y `EVENTBRITE_API_TOKEN` en el archivo `.env` del backend.
- **Formato de URL en Importación:** La importación manual de URLs espera enlaces bien formados que contengan las palabras clave `eventbrite`, `lu.ma`, `luma.com` o `meetup.com` y que resuelvan a IPs públicas globales válidas.

## 4. Pending Backlog
- Monitorear el correcto bloqueo de intentos sospechosos o ataques en el log de producción de FastAPI.
- Validar el flujo visual de la barra de importación rápida directamente en la UI del navegador a resolución móvil (360x800px) tras desplegar los cambios en producción.
