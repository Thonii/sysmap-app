# AI Context - SysmapApp Integration

## 1. Current Status
El sistema SysmapApp ha sido elevado a **v1.0 (Producto Estrella)**. El frontend Next.js y el backend FastAPI están plenamente acoplados mediante una base de datos SQLite compartida (`sysmap.db`). El backend procesa las ingestas con IA y caché preventivo, mientras que el frontend expone una interfaz premium, Mobile-First (360x800px) y adaptada a la Constitución de la Software Factory de TecnoAncon.
La base de datos SQLite está sincronizada con el esquema actualizado de Prisma. El proyecto compila en producción con cero advertencias o errores de TypeScript.

## 2. Recent Changes
- **Modelado en Base de Datos (SQLite):**
  * Modificado `prisma/schema.prisma` para incluir el modelo `Lead` (captación de organizadores B2B) y `SavedEvent` (eventos guardados por usuarios NextAuth).
  * Ejecutado `npx prisma db push` y `npx prisma generate` para sincronizar los tipos de Prisma Client y la base de datos de producción/desarrollo local.
- **Endpoints de la API de Next.js:**
  * **API de Leads B2B (`/api/leads`):** Implementada una ruta `POST` segura para almacenar la información de contacto de organizadores de eventos interesados.
  * **API de Favoritos (`/api/saved-events`):** Creada una ruta con soporte `GET` (listar favoritos del usuario) y `POST` (toggle de guardar/eliminar evento de favoritos), validando la sesión del usuario.
- **Resolución de Ruteo en Traefik (docker-compose.yml):**
  * Excluidas las rutas de API del frontend (`/api/preferences`, `/api/saved-events`, `/api/leads`) en la regla de enrutamiento del backend de Traefik para evitar que intercepte y retorne 404 en las llamadas de Next.js.
- **Rediseño Premium de la Interfaz:**
  * **Hero Section Minimalista:** Incorporado un H1 llamativo con gradiente Solarpunk e información descriptiva inmediatamente debajo de la barra de navegación para dar contexto inmediato sobre Sysmap.
  * **Captación B2B Above-the-Fold:** Agregado un botón de alto contraste (`glow-btn`) responsivo en el Header y una tarjeta destacada al inicio de la barra lateral derecha para promover que los organizadores registren sus eventos.
  * **Modal de Lead Minimalista:** Creado un componente de diálogo flotante con Backdrop blur y animación premium para recolectar leads de organizadores de manera interactiva.
  * **Empty State Inteligente con Suscripción:** Refactorizada la lógica de `EventList.tsx` para discernir cuando la base de datos está totalmente vacía de cuando **no hay resultados por filtros activos**. Para filtros activos, se implementa una UI de retención que ofrece activar alertas por correo de esa categoría específica.
  * **Toast Notification System:** Implementado un gestor de estados en `page.tsx` que dispara avisos sutiles (Toasts) flotantes en pantalla al guardar favoritos o enviar leads de forma exitosa.
  * **Autoridad y Enlaces Open-Core:** Agregado un Footer robusto con referencias a TecnoAncon y un botón SVG embebido de GitHub en Header y Footer.
- **Documentación de Ingeniería:**
  * Creado un `README.md` impecable en la raíz que detalla la visión, diagramas Mermaid de arquitectura, despliegue con Docker Compose y pasos para correr localmente.

## 3. Active Constraints
- **Base de Datos Compartida SQLite:** Se mantiene el volumen compartido `sysmap_db_data` montado en `/app/database` para frontend y backend.
- **Regeneración de Prisma:** Al realizar cambios en la base de datos, siempre se debe ejecutar `npx prisma generate` en el directorio de frontend para re-compilar los tipos.

## 4. Pending Backlog
- Monitorear en producción las suscripciones del boletín inteligente e ingestas concurrentes.
- Agregar test de integración Playwright para verificar el flujo de captación de Leads B2B de extremo a extremo.
