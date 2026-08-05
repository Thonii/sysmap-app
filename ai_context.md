# AI Context - SysmapApp Integration

## 1. Business Use Case & Stakeholders
* **Business Use Case:** Sysmap es un sistema de inteligencia de mercado y radar de eventos de tecnología e innovación regionalizado en Buenos Aires. Automatiza el ciclo completo de descubrimiento de eventos, reduciendo el ruido de la información mediante filtrado semántico y heurístico local, sin intervención humana manual.
* **Impacto en Departamentos:**
  * **Estrategia/Ventas B2B:** Identifica tendencias y temas emergentes (ej. agentes de IA, Web3, computación en la nube) para diseñar posicionamiento de marca y oportunidades comerciales.
  * **HR (Recruiting):** Localiza focos activos de comunidades y hubs de talento local para reclutamiento de perfiles de ingeniería de software.
  * **PMO (Project Management Office):** Permite organizar la participación corporativa en eventos clave, optimizar presupuestos de patrocinios y alinear equipos.
* **Propietario y Marca:** Diseñado bajo los pilares de **TecnoAncon** (Ancón, Lima, Perú) para garantizar la modularidad, aislamiento multi-tenant y resiliencia local-first.

---

## 2. Current Status
El sistema Sysmap se encuentra en la versión **v1.2 (Estándar Corporativo y Validado)**:
* **Frontend (Next.js 16 + React 19 + Prisma 7 + Tailwind 4):** Interfaz premium mobile-first (360x800px) integrada con SQLite compartida para visualización de favoritos, leads B2B e empty states con alertas.
* **Backend (FastAPI + SQLAlchemy + Python 3.12):** Pipeline de ingesta asíncrono y de-duplicado secuencial que lee de Luma, Meetup y Eventbrite.
* **Motor de Clasificación de IA (Gemini 2.5 Flash + Fallback Gemini 1.5 Flash):** Totalmente optimizado bajo el principio **Token-Economy**. Las directrices del clasificador se cargan dinámicamente desde un archivo Markdown estático de skills (`app/skills/classification_skill.md`).
* **Estado de Pruebas:** 30 pruebas unitarias exitosas pasadas con `pytest` en el backend, cubriendo el pipeline, el extractor de URLs individuales y las tres suites específicas para cada uno de los scrapers (Meetup, Luma y Eventbrite).

---

## 3. Agent Workflow & Prompt Architecture
* **Orquestación de Ingesta Externa:**
  * Ejecución en lote secuencial de scrapers (`run_all_scrapers`): Luma -> Meetup -> Eventbrite.
  * Incorporación de rate-limits amigables (`SCRAPER_REQUEST_DELAY_SECONDS` = 2) entre plataformas para evitar bloqueos por IP y denegaciones de servicio.
  * **Meetup Scraper:** Extrae información estructurada mediante bloques `application/ld+json` en HTML. Fallback a raspado de tarjetas HTML tradicionales.
  * **Luma Scraper:** Extrae información a través del nodo `__NEXT_DATA__` (JSON de Next.js) garantizando consistencia absoluta de datos. Fallback a selectores CSS tradicionales.
  * **Eventbrite Scraper:** Extrae eventos públicos a través de JSON-LD en múltiples categorías (Business, Tech, Community, etc.) y de la API REST oficial `/users/me/events/` si se provee un token de autorización.
* **Prompt Architecture (Skills Estáticos):**
  * La directriz de IA se define en [classification_skill.md](file:///home/thonii/proyectos/sysmap-app/codigo_fuente/backend/app/skills/classification_skill.md). El backend lee este archivo markdown e inyecta su contenido en la llamada al LLM, separando las reglas de negocio de la lógica del código de programación.
  * Configuración del LLM en modo JSON estricto (`response_mime_type: "application/json"`) utilizando el modelo principal `gemini-2.5-flash` y `gemini-1.5-flash` como fallback en caso de contingencias de red o cuotas de API.

---

## 4. Memory Strategy & Knowledge Scaffolding
* **Arquitectura de Memoria local-first:**
  * **Memoria a largo plazo (Relacional):** Base de datos SQLite compartida (`sysmap.db`). Las tablas `eventos` y `suscripciones` registran el histórico y las preferencias locales.
  * **Caché Preventivo de IA (`IACache`):** Almacenamiento clave-valor relacional en SQLite. Se calcula el hash MD5 del texto de entrada (`title` + `description`). Si el hash ya existe en la tabla `cache_ia`, se recupera la respuesta del LLM a Costo 0 sin realizar llamadas de API redundantes.
  * **Heurística de Clasificación Local (Costo 0):** Evaluación regex de listas curadas de palabras clave (`TECH_KEYWORDS` y `NON_TECH_KEYWORDS`) con límites de palabra (`\bword\b`). Si coincide inequívocamente, se descarta o aprueba localmente, evitando consultar al modelo de IA y protegiendo el consumo de tokens.

---

## 5. Failure Modes & Troubleshooting

### Protocolos de Contingencia Documentados:

1. **Scraping Breaks (Cambios de HTML en Origen):**
   * *Problema:* Las plataformas externas modifican su estructura HTML o nodos de script JSON-LD.
   * *Mitigación:* Captura de excepciones a nivel de scraper individual. Si falla Meetup, el pipeline continúa procesando Luma y Eventbrite de forma transparente. Se implementan fallbacks a selectores CSS básicos en todos los scrapers.
2. **Rate Limits y Timeouts en APIs Externas:**
   * *Problema:* Bloqueos temporales en llamadas HTTP a plataformas de eventos o a la API de Gemini (HTTP 429).
   * *Mitigación:* Timeouts explícitos y restrictivos (15s en scrapers, 20s en API de Eventbrite). Fallback automático en cascada del modelo de IA (`gemini-2.5-flash` -> `gemini-1.5-flash`). En caso de fallo general del LLM, se retorna un estado predeterminado de no-tecnológico por seguridad operativa.
3. **Consistencia de Datos Públicos y Duplicados:**
   * *Problema:* Cambios dinámicos de fechas, coordenadas o descripciones en eventos ya indexados.
   * *Mitigación:* Deduplicación primaria por clave compuesta (`source_platform` + `source_id`). Si el evento ya existe, se actualizan sus coordenadas y fechas pero se conserva la clasificación semántica previa, ahorrando tokens de cómputo.
   * *Corrección Aplicada:* Los hashes de ID de respaldo para URLs sin ID numérico nativo en Meetup y Eventbrite se generan mediante funciones deterministas MD5 de 15 caracteres (`hashlib.md5()`), eliminando la duplicación en reinicios del servidor por el no-determinismo del anterior método `hash()`.

---

## 6. Pending Backlog

### Tareas de Optimización Futura:
- [ ] **Optimización del Pipeline de Ingesta (Cuellos de Botella):**
  - Implementar paginación básica en scrapers. Actualmente se solicita y procesa la primera página de forma completa; si crece el volumen, aumentará drásticamente la latencia de red.
  - Implementar ejecución paralela controlada (con límites de concurrencia) de los scrapers en lugar de secuencial para optimizar el uso de CPU.
- [ ] **Monitoreo de Telemetría Avanzada:**
  - Agregar persistencia de métricas de telemetría (latencias, tasas de acierto de caché) en logs estructurados o en una tabla de base de datos dedicada.
