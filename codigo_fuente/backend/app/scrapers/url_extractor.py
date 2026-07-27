import re
import json
import logging
import socket
import ipaddress
import httpx
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Expresión regular para validar dominios autorizados de la lista blanca
# Eventbrite: eventbrite.com, eventbrite.com.ar, eventbrite.es, eventbrite.co.uk, etc.
# Luma: lu.ma, luma.com
# Meetup: meetup.com, es.meetup.com, etc.
ALLOWED_DOMAINS_RE = re.compile(
    r"^(?:[a-z0-9\-]+\.)*(?:eventbrite\.[a-z]{2,}(?:\.[a-z]{2})?|lu\.ma|luma\.com|meetup\.com)$",
    re.IGNORECASE
)

def sanitize_string(text: str) -> str:
    """
    Sanitiza strings removiendo etiquetas HTML para prevenir inyecciones en base de datos.
    """
    if not text:
        return ""
    try:
        # Eliminar cualquier tag HTML usando BeautifulSoup
        soup = BeautifulSoup(text, "html.parser")
        cleaned = soup.get_text()
        # Normalizar espacios en blanco
        return " ".join(cleaned.split()).strip()
    except Exception:
        # Fallback de seguridad por expresiones regulares si falla BeautifulSoup
        return re.sub(r"<[^>]*>", "", text).strip()

def validate_and_resolve_url(url: str) -> str:
    """
    Valida el esquema, dominio y resolución IP de la URL por motivos de seguridad contra SSRF.
    Retorna la URL normalizada si es válida, de lo contrario lanza ValueError.
    """
    try:
        parsed = urlparse(url)
    except Exception as e:
        raise ValueError(f"URL mal formada: {str(e)}")
        
    scheme = parsed.scheme.lower()
    if scheme not in ("http", "https"):
        raise ValueError("Esquema de URL no soportado. Debe ser http o https.")
        
    host = parsed.hostname
    if not host:
        raise ValueError("URL inválida: no contiene un host válido.")
        
    # 1. Validar contra la Whitelist de dominios
    if not ALLOWED_DOMAINS_RE.match(host):
        raise ValueError("Plataforma no soportada. Solo se admiten enlaces oficiales de Eventbrite, Luma y Meetup.")
        
    # 2. Resolución DNS para prevenir SSRF (bloquear IPs locales/privadas/reservadas)
    try:
        addr_info = socket.getaddrinfo(host, None)
    except socket.gaierror as e:
        raise ValueError(f"No se pudo resolver el nombre de host '{host}': {str(e)}")
        
    for family, kind, proto, canonname, sockaddr in addr_info:
        ip = sockaddr[0]
        try:
            ip_obj = ipaddress.ip_address(ip)
            if (ip_obj.is_loopback or 
                ip_obj.is_private or 
                ip_obj.is_link_local or 
                ip_obj.is_unspecified or 
                ip_obj.is_reserved):
                raise ValueError(f"Acceso denegado: el host '{host}' resuelve a una IP interna o reservada.")
        except ValueError as ve:
            if "Acceso denegado" in str(ve):
                raise ve
            raise ValueError(f"Acceso denegado: IP '{ip}' inválida o no soportada.")
            
    return url

def safe_download_html(url: str, headers: dict) -> str:
    """
    Descarga el HTML de la URL de forma segura previniendo ataques de DoS por tamaño de archivo.
    Lanza ValueError o Exception si excede los límites seguros.
    """
    validate_and_resolve_url(url)
    
    max_size = 5 * 1024 * 1024  # Límite seguro de 5 MB
    timeout = httpx.Timeout(10.0, connect=5.0)
    
    try:
        with httpx.Client(timeout=timeout, max_redirects=3, follow_redirects=True) as client:
            # Iniciamos stream para validar headers antes de bajar el cuerpo completo
            with client.stream("GET", url, headers=headers) as response:
                if response.status_code != 200:
                    raise Exception(f"No se pudo acceder al evento. Código de estado HTTP: {response.status_code}")
                    
                # 1. Validar Content-Type
                content_type = response.headers.get("content-type", "").lower()
                if "text/html" not in content_type and "application/xhtml+xml" not in content_type:
                    raise ValueError(f"Tipo de archivo no soportado: '{content_type}'. Solo se admiten páginas HTML.")
                    
                # 2. Validar Content-Length
                content_length = response.headers.get("content-length")
                if content_length:
                    try:
                        if int(content_length) > max_size:
                            raise ValueError(f"La página excede el tamaño máximo seguro permitido (5 MB).")
                    except ValueError as ve:
                        if "excede el tamaño" in str(ve):
                            raise ve
                            
                # 3. Descarga incremental segura
                body_chunks = []
                bytes_read = 0
                for chunk in response.iter_text():
                    body_chunks.append(chunk)
                    # Convertir a bytes para contar con precisión
                    bytes_read += len(chunk.encode("utf-8", errors="ignore"))
                    if bytes_read > max_size:
                        raise ValueError(f"La descarga del cuerpo excede el límite de seguridad (5 MB).")
                        
                return "".join(body_chunks)
    except httpx.TooManyRedirects:
        raise ValueError("La URL generó demasiadas redirecciones (posible bucle infinito de redirecciones).")
    except httpx.TimeoutException:
        raise ValueError("Tiempo de espera agotado al descargar la página del evento.")
    except Exception as e:
        if isinstance(e, ValueError):
            raise e
        raise Exception(f"Error al descargar la página: {str(e)}")

def extract_event_from_url(url: str) -> dict:
    """
    Descarga una URL de evento de Eventbrite, Luma o Meetup,
    extrae sus detalles y los formatea según el esquema del sistema de forma segura.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
    }

    url_lower = url.lower()
    
    if "eventbrite" in url_lower:
        return _extract_eventbrite(url, headers)
    elif "lu.ma" in url_lower or "luma.com" in url_lower:
        return _extract_luma(url, headers)
    elif "meetup.com" in url_lower:
        return _extract_meetup(url, headers)
    else:
        # Esta validación también se hace en validate_and_resolve_url pero se deja aquí por robustez
        raise ValueError("Plataforma no soportada. Solo se admiten enlaces oficiales de Eventbrite, Luma y Meetup.")

def _extract_eventbrite(url: str, headers: dict) -> dict:
    logger.info(f"Extrayendo evento individual de Eventbrite seguro: {url}")
    html_content = safe_download_html(url, headers)
    
    soup = BeautifulSoup(html_content, "html.parser")
    ld_json_scripts = soup.find_all("script", type="application/ld+json")
    
    event_data = None
    for script in ld_json_scripts:
        try:
            if not script.string:
                continue
            content = json.loads(script.string)
            if isinstance(content, dict):
                if content.get("@type") == "Event" or "Event" in str(content.get("@type")):
                    event_data = content
                    break
            elif isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and (item.get("@type") == "Event" or "Event" in str(item.get("@type"))):
                        event_data = item
                        break
                if event_data:
                    break
        except Exception:
            pass
            
    if not event_data:
        raise ValueError("No se pudo encontrar información estructurada del evento en la página de Eventbrite.")
        
    # Extraer ID
    match = re.search(r"-tickets-(\d+)", url) or re.search(r"/e/.*?(\d+)", url) or re.search(r"/e/(\d+)", url)
    source_id = match.group(1) if match else str(hash(url))
    
    # Mapear datos sanitizados
    title = sanitize_string(event_data.get("name", ""))
    if not title:
        raise ValueError("El evento de Eventbrite no tiene un título válido.")
        
    description = sanitize_string(event_data.get("description", ""))
    
    # Fechas
    start_str = event_data.get("startDate")
    end_str = event_data.get("endDate")
    
    start_time = None
    if start_str:
        try:
            start_time = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
        except ValueError:
            pass
            
    if not start_time:
        raise ValueError("El evento de Eventbrite no tiene una fecha de inicio válida.")
        
    end_time = None
    if end_str:
        try:
            end_time = datetime.fromisoformat(end_str.replace("Z", "+00:00"))
        except ValueError:
            pass
            
    # Ubicación
    location = event_data.get("location", {})
    venue_name = "Online"
    address = "Online"
    latitude = None
    longitude = None
    
    if isinstance(location, dict):
        venue_name = sanitize_string(location.get("name", "A confirmar"))
        address_info = location.get("address", {})
        if isinstance(address_info, dict):
            address = sanitize_string(address_info.get("streetAddress") or address_info.get("name") or venue_name)
        else:
            address = sanitize_string(str(address_info) or venue_name)
            
        geo = location.get("geo", {})
        if isinstance(geo, dict):
            try:
                lat = geo.get("latitude")
                lon = geo.get("longitude")
                if lat is not None:
                    latitude = float(lat)
                if lon is not None:
                    longitude = float(lon)
            except (ValueError, TypeError):
                pass
                
    return {
        "title": title,
        "description": description,
        "source_platform": "eventbrite",
        "source_id": str(source_id),
        "source_url": url,
        "start_time": start_time,
        "end_time": end_time,
        "venue_name": venue_name,
        "address": address,
        "latitude": latitude,
        "longitude": longitude,
        "city": "Buenos Aires",
        "raw_data": event_data
    }

def _extract_luma(url: str, headers: dict) -> dict:
    logger.info(f"Extrayendo evento individual de Luma seguro: {url}")
    html_content = safe_download_html(url, headers)
    
    soup = BeautifulSoup(html_content, "html.parser")
    next_data_script = soup.find("script", id="__NEXT_DATA__")
    
    event_data = None
    if next_data_script and next_data_script.string:
        try:
            data = json.loads(next_data_script.string)
            page_props = data.get("props", {}).get("pageProps", {})
            
            if "event" in page_props:
                event_data = page_props["event"]
            elif "initialData" in page_props:
                event_data = page_props["initialData"].get("event")
            else:
                # Búsqueda recursiva en JSON
                def find_event_obj(d):
                    if isinstance(d, dict):
                        if "api_id" in d and "name" in d and "start_at" in d:
                            return d
                        for v in d.values():
                            res = find_event_obj(v)
                            if res:
                                return res
                    elif isinstance(d, list):
                        for item in d:
                            res = find_event_obj(item)
                            if res:
                                return res
                    return None
                event_data = find_event_obj(data)
        except Exception as e:
            logger.error(f"Error parseando __NEXT_DATA__ en importación de Luma: {e}")
            
    if not event_data:
        # Fallback básico si no hay __NEXT_DATA__
        title_el = soup.find("h1") or soup.find("title")
        title = sanitize_string(title_el.text if title_el else "Evento Luma")
        
        slug = url.split("/")[-1].split("?")[0]
        
        return {
            "title": title,
            "description": "Detalles del evento en Luma.",
            "source_platform": "luma",
            "source_id": slug,
            "source_url": url,
            "start_time": datetime.now(),
            "end_time": None,
            "venue_name": "A confirmar",
            "address": "A confirmar",
            "latitude": None,
            "longitude": None,
            "city": "Buenos Aires",
            "raw_data": {"fallback_import": True}
        }

    # Extraer campos si tenemos event_data estructurado
    title = sanitize_string(event_data.get("name", ""))
    source_id = event_data.get("api_id") or event_data.get("id") or url.split("/")[-1].split("?")[0]
    
    start_iso = event_data.get("start_at")
    end_iso = event_data.get("end_at")
    
    start_time = None
    if start_iso:
        try:
            start_time = datetime.fromisoformat(start_iso.replace("Z", "+00:00"))
        except ValueError:
            pass
            
    if not start_time:
        start_time = datetime.now()
        
    end_time = None
    if end_iso:
        try:
            end_time = datetime.fromisoformat(end_iso.replace("Z", "+00:00"))
        except ValueError:
            pass
            
    geo_address = event_data.get("geo_address_info", {})
    venue_name = sanitize_string(event_data.get("geo_name") or geo_address.get("address") or "A confirmar")
    address = sanitize_string(geo_address.get("full_address") or geo_address.get("address") or "A confirmar")
    latitude = event_data.get("geo_latitude") or geo_address.get("latitude")
    longitude = event_data.get("geo_longitude") or geo_address.get("longitude")
    
    try:
        if latitude:
            latitude = float(latitude)
        if longitude:
            longitude = float(longitude)
    except (ValueError, TypeError):
        latitude = None
        longitude = None
        
    description = sanitize_string(event_data.get("description") or event_data.get("description_short") or "")
    
    return {
        "title": title,
        "description": description,
        "source_platform": "luma",
        "source_id": str(source_id),
        "source_url": url,
        "start_time": start_time,
        "end_time": end_time,
        "venue_name": venue_name,
        "address": address,
        "latitude": latitude,
        "longitude": longitude,
        "city": "Buenos Aires",
        "raw_data": event_data
    }

def _extract_meetup(url: str, headers: dict) -> dict:
    logger.info(f"Extrayendo evento individual de Meetup seguro: {url}")
    html_content = safe_download_html(url, headers)
    
    soup = BeautifulSoup(html_content, "html.parser")
    ld_json_scripts = soup.find_all("script", type="application/ld+json")
    
    event_data = None
    for script in ld_json_scripts:
        try:
            if not script.string:
                continue
            content = json.loads(script.string)
            if isinstance(content, dict) and content.get("@type") == "Event":
                event_data = content
                break
            elif isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get("@type") == "Event":
                        event_data = item
                        break
                if event_data:
                    break
        except Exception:
            pass
            
    if not event_data:
        raise ValueError("No se pudo encontrar información estructurada del evento en la página de Meetup.")
        
    title = sanitize_string(event_data.get("name", ""))
    if not title:
        raise ValueError("El evento de Meetup no tiene un título válido.")
        
    # Extraer ID
    match = re.search(r"/events/(\w+)", url)
    source_id = match.group(1) if match else str(hash(url))
    
    description = sanitize_string(event_data.get("description", ""))
    
    start_str = event_data.get("startDate")
    end_str = event_data.get("endDate")
    
    start_time = None
    if start_str:
        try:
            start_time = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
        except ValueError:
            pass
            
    if not start_time:
        raise ValueError("El evento de Meetup no tiene una fecha de inicio válida.")
        
    end_time = None
    if end_str:
        try:
            end_time = datetime.fromisoformat(end_str.replace("Z", "+00:00"))
        except ValueError:
            pass
            
    location = event_data.get("location", {})
    venue_name = sanitize_string(location.get("name") if isinstance(location, dict) else "Online/A confirmar")
    address = "Online"
    latitude = None
    longitude = None
    
    if isinstance(location, dict) and location.get("@type") == "Place":
        address_info = location.get("address", {})
        if isinstance(address_info, dict):
            address = sanitize_string(address_info.get("streetAddress") or address_info.get("name") or venue_name)
        else:
            address = sanitize_string(str(address_info) or venue_name)
            
        geo = location.get("geo", {})
        if isinstance(geo, dict):
            try:
                lat = geo.get("latitude")
                lon = geo.get("longitude")
                if lat is not None:
                    latitude = float(lat)
                if lon is not None:
                    longitude = float(lon)
            except (ValueError, TypeError):
                pass
                
    return {
        "title": title,
        "description": description,
        "source_platform": "meetup",
        "source_id": str(source_id),
        "source_url": url,
        "start_time": start_time,
        "end_time": end_time,
        "venue_name": venue_name,
        "address": address,
        "latitude": latitude,
        "longitude": longitude,
        "city": "Buenos Aires",
        "raw_data": event_data
    }
