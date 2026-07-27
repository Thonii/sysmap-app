from fastapi import FastAPI, Depends, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text, and_, or_
from datetime import datetime, date, timezone, timedelta
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.db import get_db, engine
from app.models.event import Event, Subscription
from app.config import DEFAULT_CITY, DEFAULT_LATITUDE, DEFAULT_LONGITUDE
from app.pipeline.ingest import ingest_events_pipeline
from app.pipeline.newsletter import send_welcome_email, send_weekly_newsletter

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Sysmap API",
    description="API para el agregador de eventos tecnológicos locales de TecnoAncon",
    version="1.0.0"
)

# Permitir CORS para desarrollo frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # En producción se debe restringir a dominios específicos
    allow_credentials=False, # Cambiado a False para permitir wildcard * sin conflictos
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar planificador de tareas (APScheduler)
scheduler = BackgroundScheduler()

def scheduled_ingest():
    """Tarea programada para correr la ingesta."""
    logger.info("Iniciando ingesta programada automática diaria...")
    db = next(get_db())
    try:
        results = ingest_events_pipeline(db)
        logger.info(f"Ingesta programada finalizada con éxito: {results}")
    except Exception as e:
        logger.error(f"Error en la ingesta programada: {e}")
    finally:
        db.close()

def scheduled_newsletter():
    db = next(get_db())
    try:
        import asyncio
        results = asyncio.run(send_weekly_newsletter(db))
        logger.info(f"Boletín programado finalizado con éxito: {results}")
    except Exception as e:
        logger.error(f"Error en el boletín programado: {e}")
    finally:
        db.close()

@app.on_event("startup")
def startup_event():
    # Programar ingesta diaria a las 03:00 AM
    scheduler.add_job(
        scheduled_ingest,
        trigger=CronTrigger(hour=3, minute=0),
        id="daily_ingest",
        replace_existing=True
    )
    # Programar boletín semanal los días lunes a las 08:00 AM
    scheduler.add_job(
        scheduled_newsletter,
        trigger=CronTrigger(day_of_week='mon', hour=8, minute=0),
        id="weekly_newsletter",
        replace_existing=True
    )
    scheduler.start()
    logger.info("Planificador de tareas de Sysmap iniciado.")
    
    # Ingesta inicial inmediata en segundo plano si la DB está vacía
    db = next(get_db())
    try:
        if db.query(Event).count() == 0:
            logger.info("Base de datos de Sysmap vacía. Disparando ingesta inicial automática en segundo plano...")
            scheduler.add_job(
                scheduled_ingest,
                id="initial_ingest_startup",
                replace_existing=True
            )
    except Exception as e:
        logger.error(f"Error comprobando DB vacía en startup: {e}")
    finally:
        db.close()

@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown()
    logger.info("Planificador de tareas de Sysmap apagado.")

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        # Verificar conexión a base de datos
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected", "timestamp": datetime.now()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

@app.get("/events")
def get_events(
    city: str = DEFAULT_CITY,
    is_tech: bool = True,
    start_date: date = None,
    latitude: float = Query(None, description="Latitud del usuario para búsqueda por proximidad"),
    longitude: float = Query(None, description="Longitud del usuario para búsqueda por proximidad"),
    radius_km: float = Query(15.0, description="Radio máximo en kilómetros para búsqueda geográfica"),
    db: Session = Depends(get_db)
):
    """
    Obtiene la lista de eventos filtrada.
    Si se envían coordenadas (latitude/longitude), ordena los eventos por distancia geográfica 
    utilizando la fórmula de Haversine e incluye solo los que están dentro del radio configurado.
    """
    ahora = datetime.now(timezone.utc)
    limite_sin_fin = ahora - timedelta(hours=4)

    query = db.query(Event).filter(
        Event.city == city,
        Event.is_tech == is_tech,
        or_(
            Event.end_time >= ahora,
            and_(Event.end_time.is_(None), Event.start_time >= limite_sin_fin)
        )
    )
    
    if start_date:
        query = query.filter(Event.start_time >= datetime.combine(start_date, datetime.min.time()).replace(tzinfo=timezone.utc))

    events = []
    
    # Búsqueda geográfica por proximidad si hay coordenadas
    if latitude is not None and longitude is not None:
        # Consulta con fórmula de Haversine para cálculo de distancia en SQL
        # 6371 es el radio de la tierra en km
        haversine_expr = text(
            "6371 * acos(cos(radians(:lat)) * cos(radians(latitude)) * "
            "cos(radians(longitude) - radians(:lon)) + "
            "sin(radians(:lat)) * sin(radians(latitude)))"
        )
        
        # Filtrar y ordenar usando SQL puro para eficiencia
        raw_query = db.query(Event, haversine_expr.label("distance")).filter(
            Event.city == city,
            Event.is_tech == is_tech,
            or_(
                Event.end_time >= ahora,
                and_(Event.end_time.is_(None), Event.start_time >= limite_sin_fin)
            ),
            Event.latitude.isnot(None),
            Event.longitude.isnot(None)
        )
        
        if start_date:
            raw_query = raw_query.filter(Event.start_time >= datetime.combine(start_date, datetime.min.time()).replace(tzinfo=timezone.utc))
            
        # Ejecutar la consulta enlazando los parámetros
        results = raw_query.params(lat=latitude, lon=longitude).all()
        
        # Filtrar por radio de distancia en Python para simplificar el HAVING de SQL
        for event, distance in results:
            if distance <= radius_km:
                event_dict = event.__dict__.copy()
                event_dict.pop('_sa_instance_state', None)
                event_dict["distance_km"] = round(distance, 2)
                events.append(event_dict)
                
        # Ordenar por distancia de menor a mayor
        events.sort(key=lambda x: x["distance_km"])
    else:
        # Retorno cronológico estándar
        db_events = query.order_by(Event.start_time.asc()).all()
        for event in db_events:
            event_dict = event.__dict__.copy()
            event_dict.pop('_sa_instance_state', None)
            event_dict["distance_km"] = None
            events.append(event_dict)
            
    return events

# Control de cooldown para evitar abuso del disparador de ingesta (Rate-Limiting)
LAST_INGEST_TIME = None
INGEST_COOLDOWN_MINUTES = 0.5

@app.post("/ingest")
def trigger_ingest(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Ejecuta el pipeline de ingesta de eventos en segundo plano con control de cooldown.
    """
    global LAST_INGEST_TIME
    ahora = datetime.now(timezone.utc)
    
    if LAST_INGEST_TIME:
        diferencia = ahora - LAST_INGEST_TIME
        if diferencia < timedelta(minutes=INGEST_COOLDOWN_MINUTES):
            minutos_restantes = INGEST_COOLDOWN_MINUTES - (diferencia.total_seconds() / 60)
            raise HTTPException(
                status_code=429,
                detail=f"Sincronización en cooldown. Por favor, intenta de nuevo en {int(minutos_restantes) + 1} minutos."
            )
            
    # Registrar el inicio del proceso de ingesta
    LAST_INGEST_TIME = ahora

    def run_ingest():
        db_session = next(get_db())
        try:
            ingest_events_pipeline(db_session)
        except Exception as e:
            logger.error(f"Error en la ingesta disparada por API: {e}")
        finally:
            db_session.close()

    background_tasks.add_task(run_ingest)
    return {"message": "Sincronización de eventos iniciada en segundo plano con éxito."}

@app.post("/subscriptions")
def create_subscription(
    email: str,
    background_tasks: BackgroundTasks,
    phone: str = Query(None, description="Número de teléfono opcional para WhatsApp"),
    preference_channel: str = Query("email", description="Canal preferido: 'email' o 'whatsapp'"),
    city: str = DEFAULT_CITY,
    latitude: float = Query(None),
    longitude: float = Query(None),
    radius_km: float = Query(15.0),
    db: Session = Depends(get_db)
):
    """
    Crea una nueva suscripción para recibir el boletín de eventos locales.
    """
    # Verificar si el canal de preferencia es válido
    if preference_channel not in ["email", "whatsapp"]:
        raise HTTPException(status_code=400, detail="preference_channel debe ser 'email' o 'whatsapp'")
        
    # Verificar si ya existe
    existing = db.query(Subscription).filter(Subscription.email == email).first()
    if existing:
        # Actualizar campos
        existing.phone = phone
        existing.preference_channel = preference_channel
        existing.city = city
        existing.latitude = latitude
        existing.longitude = longitude
        existing.radius_km = radius_km
        existing.is_active = True
        db.commit()
        
        # Disparar email de bienvenida en segundo plano
        if preference_channel == "email":
            background_tasks.add_task(send_welcome_email, email, db)
            
        return {"message": "Suscripción existente actualizada con éxito.", "id": str(existing.id)}
        
    new_sub = Subscription(
        email=email,
        phone=phone,
        preference_channel=preference_channel,
        city=city,
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km,
        is_active=True
    )
    
    db.add(new_sub)
    db.commit()
    db.refresh(new_sub)
    
    # Disparar email de bienvenida en segundo plano
    if preference_channel == "email":
        background_tasks.add_task(send_welcome_email, email, db)
        
    return {"message": "Suscripción creada con éxito.", "id": str(new_sub.id)}

@app.get("/subscriptions")
def get_subscriptions(db: Session = Depends(get_db)):
    """
    Devuelve todas las suscripciones activas.
    """
    subs = db.query(Subscription).filter(Subscription.is_active == True).all()
    result = []
    for sub in subs:
        sub_dict = sub.__dict__.copy()
        sub_dict.pop('_sa_instance_state', None)
        result.append(sub_dict)
    return result

@app.get("/subscriptions/unsubscribe")
def unsubscribe(email: str, db: Session = Depends(get_db)):
    """
    Desactiva una suscripción de boletín mediante el enlace del correo.
    """
    sub = db.query(Subscription).filter(Subscription.email == email).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Suscripción no encontrada.")
    sub.is_active = False
    db.commit()
    return {"message": f"Te has desuscrito con éxito del boletín de Sysmap para el email: {email}."}

@app.post("/newsletter/send-weekly")
async def trigger_weekly_newsletter(db: Session = Depends(get_db)):
    """
    Fuerza el envío manual del boletín semanal de eventos.
    """
    stats = await send_weekly_newsletter(db)
    return {"message": "Boletín semanal enviado con éxito.", "stats": stats}
