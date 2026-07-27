import logging
from sqlalchemy.orm import Session
from app.scrapers import run_all_scrapers
from app.pipeline.classifier import process_and_classify_event
from app.models.event import Event

logger = logging.getLogger(__name__)

def ingest_events_pipeline(db: Session) -> dict:
    """
    Ejecuta el pipeline completo de ingesta, normalización, clasificación semántica
    y guardado en base de datos.
    """
    logger.info("Iniciando pipeline de ingesta y normalización...")
    
    # 1. Obtener eventos de todos los scrapers
    raw_events = run_all_scrapers()
    
    stats = {
        "total_scraped": len(raw_events),
        "inserted": 0,
        "updated": 0,
        "is_tech_count": 0,
        "discarded_non_tech": 0,
        "errors": 0
    }
    
    for event_data in raw_events:
        try:
            # 2. Verificar duplicados (source_platform + source_id)
            existing_event = db.query(Event).filter(
                Event.source_platform == event_data["source_platform"],
                Event.source_id == event_data["source_id"]
            ).first()
            
            # 3. Clasificación (solo requerida para eventos nuevos o que no tengan clasificación previa)
            if existing_event:
                # Si ya existe, actualizamos los datos dinámicos (fecha, ubicación, descripción)
                existing_event.title = event_data["title"]
                existing_event.description = event_data["description"]
                existing_event.start_time = event_data["start_time"]
                existing_event.end_time = event_data["end_time"]
                existing_event.venue_name = event_data["venue_name"]
                existing_event.address = event_data["address"]
                existing_event.latitude = event_data["latitude"]
                existing_event.longitude = event_data["longitude"]
                existing_event.raw_data = event_data["raw_data"]
                # No re-clasificamos para evitar llamadas innecesarias a la IA (Token-Economy)
                
                if existing_event.is_tech:
                    stats["is_tech_count"] += 1
                else:
                    stats["discarded_non_tech"] += 1
                    
                stats["updated"] += 1
                logger.info(f"Evento existente actualizado: {event_data['title']} ({event_data['source_platform']})")
            else:
                # Si es un evento nuevo, ejecutamos la clasificación semántica (heurística + IA + caché)
                is_tech, tags = process_and_classify_event(
                    db,
                    event_data["title"],
                    event_data["description"]
                )
                
                # Crear nuevo registro
                new_event = Event(
                    title=event_data["title"],
                    description=event_data["description"],
                    source_platform=event_data["source_platform"],
                    source_id=event_data["source_id"],
                    source_url=event_data["source_url"],
                    start_time=event_data["start_time"],
                    end_time=event_data["end_time"],
                    venue_name=event_data["venue_name"],
                    address=event_data["address"],
                    latitude=event_data["latitude"],
                    longitude=event_data["longitude"],
                    city=event_data["city"],
                    tags=tags,
                    raw_data=event_data["raw_data"],
                    is_tech=is_tech
                )
                
                db.add(new_event)
                
                if is_tech:
                    stats["is_tech_count"] += 1
                else:
                    stats["discarded_non_tech"] += 1
                    
                stats["inserted"] += 1
                logger.info(f"Nuevo evento insertado: {event_data['title']} (is_tech={is_tech}, tags={tags})")
                
            db.commit()
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error procesando evento en pipeline de ingesta: {e}", exc_info=True)
            stats["errors"] += 1
            
    logger.info(f"Pipeline de ingesta finalizado. Resultados: {stats}")
    return stats
