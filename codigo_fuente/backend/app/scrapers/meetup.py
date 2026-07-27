import json
import logging
import re
from datetime import datetime
import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

def scrape_meetup_buenos_aires() -> list[dict]:
    """
    Scrapea eventos de Meetup en Buenos Aires enfocados en tecnología.
    Extrae la información usando JSON-LD (Schema.org) estructurado para mayor precisión y robustez.
    """
    # URL de Meetup filtrada por ubicación (Buenos Aires, Argentina) y categoría de Tecnología (546)
    url = "https://www.meetup.com/find/?source=EVENTS&location=ar--buenos-aires&categoryId=546"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "es-ES,es;q=0.9,en;q=0.8"
    }
    
    events_found = []
    
    try:
        logger.info(f"Iniciando scraping de Meetup: {url}")
        with httpx.Client(timeout=15.0, follow_redirects=True) as client:
            response = client.get(url, headers=headers)
            
        if response.status_code != 200:
            logger.error(f"Error cargando Meetup: Status {response.status_code}")
            return []
            
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Buscar bloques JSON-LD
        ld_json_scripts = soup.find_all("script", type="application/ld+json")
        logger.info(f"Bloques JSON-LD encontrados en Meetup: {len(ld_json_scripts)}")
        
        raw_events = []
        for script in ld_json_scripts:
            try:
                if not script.string:
                    continue
                content = json.loads(script.string)
                
                # Meetup puede inyectar un único Evento o una lista (ItemList)
                if isinstance(content, list):
                    for item in content:
                        if item.get("@type") == "Event":
                            raw_events.append(item)
                elif isinstance(content, dict):
                    if content.get("@type") == "Event":
                        raw_events.append(content)
                    elif content.get("@type") == "ItemList":
                        items = content.get("itemListElement", [])
                        for element in items:
                            item = element.get("item", {})
                            if item.get("@type") == "Event":
                                raw_events.append(item)
            except Exception as e:
                logger.error(f"Error parseando script JSON-LD de Meetup: {e}")
                
        # Si no encontramos eventos estructurados JSON-LD, intentamos raspar tarjetas
        if not raw_events:
            logger.warning("No se encontraron eventos JSON-LD en Meetup. Intentando scraping de tarjetas HTML...")
            return scrape_meetup_cards_fallback(soup)
            
        logger.info(f"Eventos crudos JSON-LD encontrados en Meetup: {len(raw_events)}")
        
        for event_data in raw_events:
            try:
                title = event_data.get("name")
                source_url = event_data.get("url")
                
                if not title or not source_url:
                    continue
                
                # Extraer un ID único de la URL del evento
                # Formato típico: https://www.meetup.com/es/grupo/events/123456/
                match = re.search(r"/events/(\w+)", source_url)
                source_id = match.group(1) if match else hashlib.md5(source_url.encode()).hexdigest()[:15]
                
                # Fechas
                start_str = event_data.get("startDate")
                end_str = event_data.get("endDate")
                
                start_time = None
                if start_str:
                    try:
                        # Reemplazar Z por offset UTC si aplica
                        clean_start = start_str.replace("Z", "+00:00")
                        start_time = datetime.fromisoformat(clean_start)
                    except ValueError:
                        continue
                
                if not start_time:
                    continue
                    
                end_time = None
                if end_str:
                    try:
                        clean_end = end_str.replace("Z", "+00:00")
                        end_time = datetime.fromisoformat(clean_end)
                    except ValueError:
                        pass
                
                # Ubicación
                location = event_data.get("location", {})
                venue_name = location.get("name") if isinstance(location, dict) else "Online/A confirmar"
                
                address = "Online"
                latitude = None
                longitude = None
                
                if isinstance(location, dict) and location.get("@type") == "Place":
                    address_info = location.get("address", {})
                    if isinstance(address_info, dict):
                        address = address_info.get("streetAddress") or address_info.get("name") or venue_name
                    else:
                        address = str(address_info) or venue_name
                        
                    geo = location.get("geo", {})
                    if isinstance(geo, dict):
                        latitude = geo.get("latitude")
                        longitude = geo.get("longitude")
                
                if latitude:
                    latitude = float(latitude)
                if longitude:
                    longitude = float(longitude)
                
                # Descripción
                description = event_data.get("description", "")
                
                events_found.append({
                    "title": title,
                    "description": description,
                    "source_platform": "meetup",
                    "source_id": str(source_id),
                    "source_url": source_url,
                    "start_time": start_time,
                    "end_time": end_time,
                    "venue_name": venue_name,
                    "address": address,
                    "latitude": latitude,
                    "longitude": longitude,
                    "city": "Buenos Aires",
                    "raw_data": event_data
                })
            except Exception as e:
                logger.error(f"Error procesando evento JSON-LD de Meetup: {e}")
                
    except Exception as e:
        logger.error(f"Error general scrapeando Meetup: {e}")
        
    return events_found

def scrape_meetup_cards_fallback(soup: BeautifulSoup) -> list[dict]:
    """
    Fallback de scraping de tarjetas HTML cuando no hay JSON-LD disponible.
    """
    events = []
    # Buscar enlaces a eventos individuales
    links = soup.find_all("a", href=re.compile(r"/events/\d+/"))
    
    for link in links:
        try:
            href = link.get("href", "")
            if not href.startswith("http"):
                href = f"https://www.meetup.com{href}"
                
            match = re.search(r"/events/(\d+)", href)
            if not match:
                continue
            source_id = match.group(1)
            
            title_el = link.find("span") or link.find("h3")
            title = title_el.text.strip() if title_el else "Evento de Tecnología"
            
            events.append({
                "title": title,
                "description": "Detalles en la página del evento.",
                "source_platform": "meetup",
                "source_id": source_id,
                "source_url": href,
                "start_time": datetime.now(),
                "end_time": None,
                "venue_name": "Meetup Venue",
                "address": "Buenos Aires, Argentina",
                "latitude": -34.6037,
                "longitude": -58.3816,
                "city": "Buenos Aires",
                "raw_data": {"fallback_scraped": True}
            })
        except Exception as e:
            logger.error(f"Error en fallback de Meetup: {e}")
            
    return events
