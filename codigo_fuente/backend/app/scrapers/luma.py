import json
import logging
from datetime import datetime
import httpx
from bs4 import BeautifulSoup
from app.config import SCRAPER_REQUEST_DELAY_SECONDS

logger = logging.getLogger(__name__)

def scrape_luma_buenos_aires() -> list[dict]:
    """
    Scrapea eventos de Luma para Buenos Aires.
    Aprovecha la presencia de __NEXT_DATA__ en el HTML para obtener data estructurada 100% fiel.
    """
    url = "https://lu.ma/buenos-aires"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "es-ES,es;q=0.9,en;q=0.8"
    }
    
    events_found = []
    
    try:
        logger.info(f"Iniciando scraping de Luma: {url}")
        with httpx.Client(timeout=15.0, follow_redirects=True) as client:
            response = client.get(url, headers=headers)
            
        if response.status_code != 200:
            logger.error(f"Error cargando Luma: Status {response.status_code}")
            return []
            
        soup = BeautifulSoup(response.text, "html.parser")
        next_data_script = soup.find("script", id="__NEXT_DATA__")
        
        if not next_data_script:
            logger.warning("No se encontró __NEXT_DATA__ en Luma. Buscando alternativas estáticas...")
            return scrape_luma_fallback(soup)
            
        data = json.loads(next_data_script.string)
        
        # Intentar navegar por el árbol JSON para encontrar los eventos.
        # En Next.js, comúnmente están en props -> pageProps o en el query state.
        # Busquemos de forma recursiva o por claves conocidas.
        props = data.get("props", {})
        page_props = props.get("pageProps", {})
        
        # Diferentes estructuras posibles en el JSON de Luma
        events_list = []
        
        # Estructura 0: En initialData (Luma.com)
        if "initialData" in page_props:
            events_list = page_props.get("initialData", {}).get("data", {}).get("events", [])
        # Estructura 1: Directamente en pageProps
        elif "events" in page_props:
            events_list = page_props.get("events", [])
        # Estructura 2: En el estado de consultas pre-cargado de trpc u otros queries
        elif "trpcState" in page_props:
            queries = page_props.get("trpcState", {}).get("queries", [])
            for q in queries:
                state = q.get("state", {})
                q_data = state.get("data", {})
                if isinstance(q_data, dict) and "entries" in q_data:
                    events_list.extend(q_data.get("entries", []))
                elif isinstance(q_data, list):
                    events_list.extend(q_data)
        # Estructura 3: Clave de ciudad
        elif "city" in page_props and isinstance(page_props["city"], dict):
            events_list = page_props["city"].get("featured_events", []) or page_props["city"].get("upcoming_events", [])
            
        # Si no encontramos nada arriba, buscamos cualquier clave de tipo lista que parezca contener eventos
        if not events_list:
            for key, val in page_props.items():
                if isinstance(val, list) and len(val) > 0 and isinstance(val[0], dict) and "event" in val[0]:
                    events_list = val
                    break
        
        logger.info(f"Eventos crudos encontrados en Luma JSON: {len(events_list)}")
        
        for item in events_list:
            try:
                # El item puede contener el evento directamente o dentro de una clave "event"
                event_data = item.get("event", item) if isinstance(item, dict) else None
                if not event_data or not isinstance(event_data, dict):
                    continue
                
                # Campos obligatorios
                title = event_data.get("name")
                source_id = event_data.get("api_id") or event_data.get("id") or event_data.get("url_info", {}).get("slug")
                
                if not title or not source_id:
                    continue
                    
                url_field = event_data.get("url")
                if url_field:
                    if url_field.startswith("http"):
                        source_url = url_field
                    else:
                        source_url = f"https://luma.com/{url_field.strip('/')}"
                else:
                    slug = event_data.get("url_info", {}).get("slug") or source_id
                    source_url = f"https://luma.com/{slug}"
                
                # Fechas
                start_iso = event_data.get("start_at")
                end_iso = event_data.get("end_at")
                
                start_time = None
                if start_iso:
                    # Luma provee formato ISO: 2026-07-25T19:00:00.000Z
                    try:
                        # Limpiar Z y milisegundos para parser
                        clean_iso = start_iso.replace("Z", "+00:00")
                        start_time = datetime.fromisoformat(clean_iso)
                    except ValueError:
                        continue
                
                if not start_time:
                    continue
                    
                end_time = None
                if end_iso:
                    try:
                        clean_iso = end_iso.replace("Z", "+00:00")
                        end_time = datetime.fromisoformat(clean_iso)
                    except ValueError:
                        pass
                
                # Ubicación
                geo_address = event_data.get("geo_address_info", {})
                venue_name = event_data.get("geo_name") or geo_address.get("address")
                address = geo_address.get("full_address") or geo_address.get("address")
                latitude = event_data.get("geo_latitude") or geo_address.get("latitude")
                longitude = event_data.get("geo_longitude") or geo_address.get("longitude")
                
                if latitude:
                    latitude = float(latitude)
                if longitude:
                    longitude = float(longitude)
                
                # Descripción
                description = event_data.get("description") or event_data.get("description_short") or ""
                
                events_found.append({
                    "title": title,
                    "description": description,
                    "source_platform": "luma",
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
                logger.error(f"Error procesando item de Luma: {e}")
                
    except Exception as e:
        logger.error(f"Error general scrapeando Luma: {e}")
        
    return events_found

def scrape_luma_fallback(soup: BeautifulSoup) -> list[dict]:
    """
    Fallback usando selectores HTML tradicionales en caso de que falle el parseo JSON.
    """
    events = []
    # Buscar tarjetas de evento en la página
    cards = soup.select(".event-card") or soup.select("a[href^='/']")
    
    for card in cards:
        try:
            href = card.get("href", "")
            if not href or len(href) < 5 or "privacy" in href or "terms" in href:
                continue
            
            # Limpiar slug
            slug = href.strip("/")
            if "/" in slug:
                continue
                
            title_el = card.select_one(".title") or card.select_one("h3") or card.select_one("h4")
            title = title_el.text.strip() if title_el else ""
            if not title:
                continue
                
            desc_el = card.select_one(".description") or card.select_one("p")
            description = desc_el.text.strip() if desc_el else ""
            
            # Si no tenemos fecha estructurada, usamos la fecha actual o simulada
            start_time = datetime.now()
            
            events.append({
                "title": title,
                "description": description,
                "source_platform": "luma",
                "source_id": slug,
                "source_url": f"https://lu.ma/{slug}",
                "start_time": start_time,
                "end_time": None,
                "venue_name": "Buenos Aires",
                "address": "Buenos Aires, Argentina",
                "latitude": -34.6037,
                "longitude": -58.3816,
                "city": "Buenos Aires",
                "raw_data": {"fallback_scraped": True}
            })
        except Exception as e:
            logger.error(f"Error en fallback de Luma para tarjeta: {e}")
            
    return events
