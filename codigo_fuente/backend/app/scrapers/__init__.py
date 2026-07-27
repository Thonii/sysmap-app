import logging
import time
from app.scrapers.luma import scrape_luma_buenos_aires
from app.scrapers.meetup import scrape_meetup_buenos_aires
from app.scrapers.eventbrite import scrape_eventbrite_buenos_aires
from app.config import SCRAPER_REQUEST_DELAY_SECONDS

logger = logging.getLogger(__name__)

def run_all_scrapers() -> list[dict]:
    """
    Ejecuta de manera secuencial y segura todos los scrapers configurados.
    Introduce retardos (rate limits amigables) para evitar bloqueos.
    """
    all_events = []
    
    # 1. Luma
    try:
        luma_events = scrape_luma_buenos_aires()
        logger.info(f"Luma Scraper finalizado. Encontrados: {len(luma_events)}")
        all_events.extend(luma_events)
    except Exception as e:
        logger.error(f"Error ejecutando Luma scraper: {e}")
        
    time.sleep(SCRAPER_REQUEST_DELAY_SECONDS)
    
    # 2. Meetup
    try:
        meetup_events = scrape_meetup_buenos_aires()
        logger.info(f"Meetup Scraper finalizado. Encontrados: {len(meetup_events)}")
        all_events.extend(meetup_events)
    except Exception as e:
        logger.error(f"Error ejecutando Meetup scraper: {e}")
        
    time.sleep(SCRAPER_REQUEST_DELAY_SECONDS)
    
    # 3. Eventbrite
    try:
        eventbrite_events = scrape_eventbrite_buenos_aires()
        logger.info(f"Eventbrite Scraper finalizado. Encontrados: {len(eventbrite_events)}")
        all_events.extend(eventbrite_events)
    except Exception as e:
        logger.error(f"Error ejecutando Eventbrite scraper: {e}")
        
    logger.info(f"Proceso de scraping completo. Total eventos crudos acumulados: {len(all_events)}")
    return all_events
