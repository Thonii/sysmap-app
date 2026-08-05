import logging
import json
import re
import hashlib
from datetime import datetime
import httpx
from bs4 import BeautifulSoup
from app.config import EVENTBRITE_API_TOKEN, DEFAULT_LATITUDE, DEFAULT_LONGITUDE

logger = logging.getLogger(__name__)

def scrape_eventbrite_html_public() -> list[dict]:
    """
    Scrapea las listas públicas de categorías y búsquedas por palabra clave de Eventbrite en Buenos Aires.
    Usa la extracción de scripts JSON-LD para robustez y de-duplica los resultados.
    """
    categories = ["science-and-tech", "business", "tech", "family-and-education", "community"]
    
    targets = []
    for cat in categories:
        targets.append(("category", cat, f"https://www.eventbrite.com.ar/b/argentina--buenos-aires/{cat}/"))
        
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "es-ES,es;q=0.9,en;q=0.8"
    }
    
    events_by_id = {}
    
    for t_type, t_val, url in targets:
        try:
            logger.info(f"Iniciando scraping HTML de Eventbrite ({t_type} {t_val}): {url}")
            with httpx.Client(timeout=20.0, follow_redirects=True) as client:
                response = client.get(url, headers=headers)
                
            if response.status_code != 200:
                logger.error(f"Error cargando HTML de Eventbrite para {t_val}: Status {response.status_code}")
                continue
                
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Buscar bloques JSON-LD
            ld_json_scripts = soup.find_all("script", type="application/ld+json")
            logger.info(f"Bloques JSON-LD públicos encontrados en {t_val}: {len(ld_json_scripts)}")
            
            raw_events = []
            for script in ld_json_scripts:
                try:
                    if not script.string:
                        continue
                    content = json.loads(script.string)
                    
                    if isinstance(content, list):
                        for item in content:
                            if isinstance(item, dict) and (item.get("@type") == "Event" or "Event" in str(item.get("@type"))):
                                raw_events.append(item)
                    elif isinstance(content, dict):
                        if content.get("@type") == "Event" or "Event" in str(content.get("@type")):
                            raw_events.append(content)
                        elif content.get("@type") == "ItemList":
                            items = content.get("itemListElement", [])
                            for element in items:
                                item = element.get("item", {})
                                if isinstance(item, dict) and (item.get("@type") == "Event" or "Event" in str(item.get("@type"))):
                                    raw_events.append(item)
                except Exception as e:
                    logger.error(f"Error parseando script JSON-LD de Eventbrite en {t_val}: {e}")
                    
            # Fallback básico si no hay JSON-LD en este target
            if not raw_events:
                logger.warning(f"No se encontraron eventos estructurados para {t_val}. Usando fallback de tarjetas HTML...")
                fallback_events = scrape_eventbrite_cards_fallback(soup)
                for fe in fallback_events:
                    events_by_id[fe["source_id"]] = fe
                continue
                
            for event_data in raw_events:
                try:
                    title = event_data.get("name")
                    source_url = event_data.get("url")
                    
                    if not title or not source_url:
                        continue
                    
                    match = re.search(r"-tickets-(\d+)", source_url) or re.search(r"/e/.*?(\d+)", source_url) or re.search(r"/e/(\d+)", source_url)
                    source_id = match.group(1) if match else hashlib.md5(source_url.encode()).hexdigest()[:15]
                    
                    # Fechas
                    start_str = event_data.get("startDate")
                    end_str = event_data.get("endDate")
                    
                    start_time = None
                    if start_str:
                        try:
                            clean_start = start_str.replace("Z", "+00:00")
                            start_time = datetime.fromisoformat(clean_start)
                        except ValueError:
                            try:
                                # Fallback para fechas sin hora (ej: 2026-08-13)
                                start_time = datetime.strptime(start_str.split("T")[0], "%Y-%m-%d")
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
                            try:
                                end_time = datetime.strptime(end_str.split("T")[0], "%Y-%m-%d")
                            except ValueError:
                                pass
                    
                    # Ubicación
                    location = event_data.get("location", {})
                    venue_name = "Online"
                    address = "Online"
                    latitude = None
                    longitude = None
                    
                    if isinstance(location, dict):
                        venue_name = location.get("name", "A confirmar")
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
                    
                    description = event_data.get("description", "")
                    
                    events_by_id[str(source_id)] = {
                        "title": title,
                        "description": description,
                        "source_platform": "eventbrite",
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
                    }
                except Exception as e:
                    logger.error(f"Error procesando evento estructurado de Eventbrite: {e}")
                    
        except Exception as e:
            logger.error(f"Error general scrapeando Eventbrite {t_type} {t_val}: {e}")
            
    return list(events_by_id.values())

def scrape_eventbrite_cards_fallback(soup: BeautifulSoup) -> list[dict]:
    events = []
    cards = soup.select("section.discover-horizontal-event-card") or soup.select("article")
    for card in cards:
        try:
            link = card.find("a")
            if not link:
                continue
            href = link.get("href", "")
            if not href or "/e/" not in href:
                continue
                
            title_el = card.find("h3") or card.find("h2")
            title = title_el.text.strip() if title_el else "Evento Eventbrite"
            
            match = re.search(r"/e/.*?(\d+)", href)
            source_id = match.group(1) if match else hashlib.md5(href.encode()).hexdigest()[:15]
            
            events.append({
                "title": title,
                "description": "Detalles del evento en Eventbrite.",
                "source_platform": "eventbrite",
                "source_id": source_id,
                "source_url": href,
                "start_time": datetime.now(),
                "end_time": None,
                "venue_name": "Buenos Aires",
                "address": "Buenos Aires, Argentina",
                "latitude": -34.6037,
                "longitude": -58.3816,
                "city": "Buenos Aires",
                "raw_data": {"fallback_scraped": True}
            })
        except Exception as e:
            logger.error(f"Error en fallback de Eventbrite HTML: {e}")
    return events

def scrape_eventbrite_api_events() -> list[dict]:
    """
    Consume el endpoint de eventos propios del usuario/organización asociado al token API.
    """
    url = "https://www.eventbriteapi.com/v3/users/me/events/"
    headers = {
        "Authorization": f"Bearer {EVENTBRITE_API_TOKEN}",
        "Accept": "application/json"
    }
    
    events_found = []
    
    try:
        logger.info("Intentando obtener eventos de Eventbrite desde API REST /users/me/events/...")
        with httpx.Client(timeout=20.0) as client:
            response = client.get(url, headers=headers, params={"expand": "venue"})
            
        if response.status_code != 200:
            logger.warning(f"La API de Eventbrite retornó código {response.status_code}. Omitiendo fallback de API.")
            return []
            
        data = response.json()
        raw_events = data.get("events", [])
        
        for event_data in raw_events:
            try:
                title = event_data.get("name", {}).get("text")
                source_url = event_data.get("url")
                source_id = event_data.get("id")
                
                if not title or not source_url or not source_id:
                    continue
                
                start_str = event_data.get("start", {}).get("utc")
                end_str = event_data.get("end", {}).get("utc")
                
                start_time = None
                if start_str:
                    try:
                        start_time = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
                    except ValueError:
                        continue
                if not start_time:
                    continue
                    
                end_time = None
                if end_str:
                    try:
                        end_time = datetime.fromisoformat(end_str.replace("Z", "+00:00"))
                    except ValueError:
                        pass
                
                venue = event_data.get("venue", {})
                venue_name = "Online" if event_data.get("online") else "A confirmar"
                address = "Online" if event_data.get("online") else "Buenos Aires, Argentina"
                latitude = None
                longitude = None
                
                if venue:
                    venue_name = venue.get("name") or venue_name
                    address_info = venue.get("address", {})
                    address = address_info.get("localized_address_display") or address_info.get("address_1") or address
                    
                    latitude_str = address_info.get("latitude") or venue.get("latitude")
                    longitude_str = address_info.get("longitude") or venue.get("longitude")
                    if latitude_str:
                        latitude = float(latitude_str)
                    if longitude_str:
                        longitude = float(longitude_str)
                
                description = event_data.get("description", {}).get("text", "")
                
                events_found.append({
                    "title": title,
                    "description": description,
                    "source_platform": "eventbrite",
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
            except Exception as ex:
                logger.error(f"Error procesando evento individual desde API Eventbrite: {ex}")
                
    except Exception as e:
        logger.error(f"Error general llamando a la API de Eventbrite: {e}")
        
    return events_found

def scrape_eventbrite_buenos_aires() -> list[dict]:
    """
    Punto de entrada principal: combina scraping HTML de eventos públicos y la API oficial.
    """
    events = scrape_eventbrite_html_public()
    
    if EVENTBRITE_API_TOKEN:
        api_events = scrape_eventbrite_api_events()
        if api_events:
            logger.info(f"Se sumaron {len(api_events)} eventos desde la API oficial de Eventbrite.")
            events.extend(api_events)
            
    return events

