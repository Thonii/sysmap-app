import logging
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import DATABASE_URL

logger = logging.getLogger(__name__)

# Configuración del motor de base de datos SQLite como motor único
sqlite_url = DATABASE_URL
if not sqlite_url.startswith("sqlite:///"):
    sqlite_url = "sqlite:///sysmap.db"

# check_same_thread es necesario para SQLite en entornos multi-hilo como FastAPI
engine = create_engine(
    sqlite_url,
    connect_args={"check_same_thread": False}
)

# Configurar modo WAL (Write-Ahead Logging) y sincronicidad NORMAL para evitar bloqueos concurrentes
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.close()

logger.info(f"Conexión a base de datos SQLite establecida en: {sqlite_url}")

# Constructor de sesiones
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Clase base declarativa
Base = declarative_base()

# Inicialización automática de tablas (Resiliencia en SQLite / bases de datos vacías)
try:
    # Importar modelos para que declarative_base los reconozca al crear las tablas
    import app.models
    Base.metadata.create_all(bind=engine)
    logger.info("Tablas de base de datos verificadas/creadas con éxito.")
except Exception as e:
    logger.error(f"Error inicializando tablas automáticamente: {e}")

# Dependencia para obtener la sesión de base de datos en endpoints FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
