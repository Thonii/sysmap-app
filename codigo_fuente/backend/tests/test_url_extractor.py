import pytest
import socket
from unittest.mock import MagicMock, patch
from datetime import datetime
from app.scrapers.url_extractor import extract_event_from_url

# Respuestas HTML simuladas
MOCK_EVENTBRITE_HTML = """
<html>
  <head>
    <script type="application/ld+json">
      {
        "@context": "https://schema.org",
        "@type": "BusinessEvent",
        "name": "IA para PyMEs Test",
        "startDate": "2026-08-13T08:30:00-03:00",
        "endDate": "2026-08-13T13:30:00-03:00",
        "description": "Un taller sobre inteligencia artificial aplicado a pequeñas empresas.",
        "location": {
          "@type": "Place",
          "name": "Av. Paseo Colón 1380",
          "address": {
            "@type": "PostalAddress",
            "streetAddress": "1380 Avenida Paseo Colón"
          },
          "geo": {
            "@type": "GeoCoordinates",
            "latitude": "-34.6178",
            "longitude": "-58.3689"
          }
        }
      }
    </script>
  </head>
</html>
"""

MOCK_LUMA_HTML = """
<html>
  <head>
    <script id="__NEXT_DATA__" type="application/json">
      {
        "props": {
          "pageProps": {
            "event": {
              "api_id": "evt-luma123",
              "name": "Luma Tech Meetup",
              "start_at": "2026-09-10T18:00:00.000Z",
              "end_at": "2026-09-10T21:00:00.000Z",
              "description": "Charlas y networking sobre software libre.",
              "geo_name": "Area Tres",
              "geo_address_info": {
                "full_address": "El Salvador 5218, Palermo",
                "latitude": -34.5889,
                "longitude": -58.4312
              }
            }
          }
        }
      }
    </script>
  </head>
</html>
"""

MOCK_MEETUP_HTML = """
<html>
  <head>
    <script type="application/ld+json">
      {
        "@context": "https://schema.org",
        "@type": "Event",
        "name": "Meetup de Rust en Buenos Aires",
        "startDate": "2026-10-05T19:00:00-03:00",
        "endDate": "2026-10-05T22:00:00-03:00",
        "description": "Introducción al lenguaje Rust y sus ventajas.",
        "location": {
          "@type": "Place",
          "name": "Digital House",
          "address": {
            "@type": "PostalAddress",
            "streetAddress": "Av. Monroe 860"
          },
          "geo": {
            "@type": "GeoCoordinates",
            "latitude": "-34.5544",
            "longitude": "-58.4488"
          }
        }
      }
    </script>
  </head>
</html>
"""

def mock_httpx_stream(html_content, status_code=200):
    # Mock de response
    mock_response = MagicMock()
    mock_response.status_code = status_code
    mock_response.headers = {
        "content-type": "text/html",
        "content-length": str(len(html_content))
    }
    # iter_text devuelve un generador/iterable
    mock_response.iter_text.return_value = [html_content]
    
    # Mock del context manager
    mock_enter = MagicMock()
    mock_enter.return_value = mock_response
    
    mock_context = MagicMock()
    mock_context.__enter__ = mock_enter
    mock_context.__exit__ = MagicMock()
    
    return mock_context

@patch("httpx.Client.stream")
@patch("socket.getaddrinfo")
def test_extract_eventbrite_success(mock_getaddrinfo, mock_stream):
    # DNS simulada pública válida (Google DNS)
    mock_getaddrinfo.return_value = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("8.8.8.8", 80))]
    mock_stream.return_value = mock_httpx_stream(MOCK_EVENTBRITE_HTML)

    url = "https://www.eventbrite.com.ar/e/ia-para-pymes-tickets-1986993388714"
    result = extract_event_from_url(url)

    assert result["source_platform"] == "eventbrite"
    assert result["source_id"] == "1986993388714"
    assert result["title"] == "IA para PyMEs Test"
    assert result["venue_name"] == "Av. Paseo Colón 1380"
    assert result["address"] == "1380 Avenida Paseo Colón"
    assert result["latitude"] == -34.6178
    assert result["longitude"] == -58.3689
    assert isinstance(result["start_time"], datetime)

@patch("httpx.Client.stream")
@patch("socket.getaddrinfo")
def test_extract_luma_success(mock_getaddrinfo, mock_stream):
    # DNS simulada pública válida (Cloudflare DNS)
    mock_getaddrinfo.return_value = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("1.1.1.1", 80))]
    mock_stream.return_value = mock_httpx_stream(MOCK_LUMA_HTML)

    url = "https://lu.ma/evt-luma123"
    result = extract_event_from_url(url)

    assert result["source_platform"] == "luma"
    assert result["source_id"] == "evt-luma123"
    assert result["title"] == "Luma Tech Meetup"
    assert result["venue_name"] == "Area Tres"
    assert result["address"] == "El Salvador 5218, Palermo"
    assert result["latitude"] == -34.5889
    assert result["longitude"] == -58.4312

@patch("httpx.Client.stream")
@patch("socket.getaddrinfo")
def test_extract_meetup_success(mock_getaddrinfo, mock_stream):
    # DNS simulada pública válida (Quad9 DNS)
    mock_getaddrinfo.return_value = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("9.9.9.9", 80))]
    mock_stream.return_value = mock_httpx_stream(MOCK_MEETUP_HTML)

    url = "https://www.meetup.com/es-ES/rust-ba/events/315710131/"
    result = extract_event_from_url(url)

    assert result["source_platform"] == "meetup"
    assert result["source_id"] == "315710131"
    assert result["title"] == "Meetup de Rust en Buenos Aires"
    assert result["venue_name"] == "Digital House"
    assert result["address"] == "Av. Monroe 860"
    assert result["latitude"] == -34.5544
    assert result["longitude"] == -58.4488

def test_extract_unsupported_platform():
    url = "https://www.google.com"
    with pytest.raises(ValueError) as excinfo:
        extract_event_from_url(url)
    assert "Plataforma no soportada" in str(excinfo.value)

def test_extract_invalid_scheme():
    url = "ftp://lu.ma/evt-123"
    with pytest.raises(ValueError) as excinfo:
        extract_event_from_url(url)
    assert "Esquema de URL no soportado" in str(excinfo.value)

@patch("socket.getaddrinfo")
def test_extract_ssrf_localhost(mock_getaddrinfo):
    mock_getaddrinfo.return_value = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 80))]
    
    url = "https://lu.ma/evt-123"
    with patch("urllib.parse.urlparse") as mock_urlparse:
        mock_parsed = MagicMock()
        mock_parsed.scheme = "https"
        mock_parsed.hostname = "localhost"
        mock_urlparse.return_value = mock_parsed
        
        with pytest.raises(ValueError) as excinfo:
            extract_event_from_url(url)
        assert "Acceso denegado" in str(excinfo.value)

@patch("socket.getaddrinfo")
def test_extract_ssrf_private_ip(mock_getaddrinfo):
    mock_getaddrinfo.return_value = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("192.168.1.1", 80))]
    
    url = "https://lu.ma/evt-123"
    with patch("urllib.parse.urlparse") as mock_urlparse:
        mock_parsed = MagicMock()
        mock_parsed.scheme = "https"
        mock_parsed.hostname = "192.168.1.1"
        mock_urlparse.return_value = mock_parsed
        
        with pytest.raises(ValueError) as excinfo:
            extract_event_from_url(url)
        assert "Acceso denegado" in str(excinfo.value)

@patch("httpx.Client.stream")
@patch("socket.getaddrinfo")
def test_extract_dos_large_content(mock_getaddrinfo, mock_stream):
    # DNS simulada pública válida
    mock_getaddrinfo.return_value = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("8.8.8.8", 80))]
    
    # Mockear response que supera tamaño
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {"content-type": "text/html", "content-length": "6000000"} # 6 MB
    
    mock_enter = MagicMock()
    mock_enter.return_value = mock_response
    
    mock_context = MagicMock()
    mock_context.__enter__ = mock_enter
    mock_stream.return_value = mock_context
    
    url = "https://lu.ma/evt-123"
    with pytest.raises(ValueError) as excinfo:
        extract_event_from_url(url)
    assert "excede el tamaño máximo" in str(excinfo.value)

def test_string_sanitization():
    from app.scrapers.url_extractor import sanitize_string
    unsafe = "<h1>Hola Mundo</h1><script>alert('XSS')</script>   Texto  limpio"
    safe = sanitize_string(unsafe)
    assert "<h1>" not in safe
    assert "<script>" not in safe
    # BeautifulSoup extrae texto limpio ignorando scripts completos
    assert safe == "Hola Mundo Texto limpio"
