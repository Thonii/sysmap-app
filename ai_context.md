# AI Context - SysmapApp Integration

## 1. Current Status
El sistema SysmapApp está estructurado e independiente en `/home/thonii/proyectos/clientes/sysmap-app/`. Se compone de un frontend Next.js y un backend en Python/FastAPI que comparten una base de datos SQLite local para almacenamiento. Ambos componentes se exponen a través del proxy inverso global en la red externa `tecnoancon-proxy`.

## 2. Recent Changes
- **Migración Física a Multi-Repo:**
  * Movidas las carpetas originales de código fuente (`backend/` y `frontend/`) desde `/home/thonii/proyectos/sysmap/` al subdirectorio `codigo_fuente/` de este repositorio.
  * Modificadas las directivas `build` en `docker-compose.yml` para usar las rutas relativas `./codigo_fuente/backend` y `./codigo_fuente/frontend`, haciendo la aplicación totalmente portable y local-first.
- **Cambio de Red de Gateway:**
  * Actualizados los servicios y la definición de red externa en `docker-compose.yml` a `tecnoancon-proxy` para unificar el enrutamiento central de Traefik.

## 3. Active Constraints
- **Base de Datos Compartida:** El backend y el frontend comparten el mismo archivo SQLite `sysmap.db` en el volumen `sysmap_db_data`. Se debe evitar cargas excesivas de escritura concurrente para no generar bloqueos de base de datos (`database is locked`).
- **Configuración de APIs externas:** El sistema requiere variables como `GEMINI_API_KEY`, `RESEND_API_KEY` y `EVENTBRITE_API_KEY` (renombradas para consistencia en compose) en el archivo `.env` del cliente.

## 4. Pending Backlog
- Levantar los contenedores locales de `sysmap-app` usando `docker compose up -d --build`.
- Probar el ruteo de Traefik: validar que la raíz `/` cargue el frontend Next.js y `/api` sea correctamente redirigido al backend tras remover el prefijo.
- Verificar la inicialización automática de las tablas SQLite en el arranque.
