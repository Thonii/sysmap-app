import os
from dotenv import load_dotenv

# Cargar variables de entorno del archivo .env si existe
load_dotenv()

# Configuración Base de Datos (SQLite por defecto para el Open-Core)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///sysmap.db")

# APIs
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
EVENTBRITE_API_TOKEN = os.getenv("EVENTBRITE_API_TOKEN", os.getenv("EVENTBRITE_API_KEY", ""))

# Configuración Geográfica de Búsqueda (Foco exclusivo en Buenos Aires para el MVP)
DEFAULT_CITY = "Buenos Aires"
DEFAULT_LATITUDE = -34.603722
DEFAULT_LONGITUDE = -58.381592
DEFAULT_RADIUS_KM = 15.0

# Rate limits y demoras en scrapers
SCRAPER_REQUEST_DELAY_SECONDS = 2
