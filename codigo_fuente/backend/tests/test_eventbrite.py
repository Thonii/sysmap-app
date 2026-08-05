import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
from app.scrapers.eventbrite import (
    scrape_eventbrite_buenos_aires,
    scrape_eventbrite_html_public,
    scrape_eventbrite_api_events
)

# Respuestas HTML mockeadas para Eventbrite
MOCK_EVENTBRITE_JSON_LD = """
<html>
  <head>
    <script type="application/ld+json">
      {
        "@type": "Event",
        "name": "Conferencia de React y TypeScript",
        "url": "https://www.eventbrite.com.ar/e/react-typescript-tickets-789012345678",
        "startDate": "2026-09-25T18:00:00Z",
        "endDate": "2026-09-25T21:00:00Z",
        "description": "Patrones avanzados de tipado y componentes.",
        "location": {
          "@type": "Place",
          "name": "Marea Coworking",
          "address": {
            "@type": "PostalAddress",
            "streetAddress": "Av. Juan B. Justo 2300"
          },
          "geo": {
            "@type": "GeoCoordinates",
            "latitude": "-34.5822",
            "longitude": "-58.4233"
          }
        }
      }
    </script>
  </head>
</html>
"""

MOCK_EVENTBRITE_HTML_CARDS = """
<html>
  <body>
    <section class="discover-horizontal-event-card">
      <a href="https://www.eventbrite.com.ar/e/taller-de-python-intermedio-tickets-456123/">
        <h3>Taller de Python Intermedio</h3>
      </a>
    </section>
    <section class="discover-horizontal-event-card">
      <a href="https://www.eventbrite.com.ar/e/taller-sin-id-en-url/">
        <h3>Taller Sin ID</h3>
      </a>
    </section>
  </body>
</html>
"""

MOCK_EVENTBRITE_API_RESPONSE = {
    "events": [
        {
            "id": "api-eb-001",
            "name": {"text": "API Eventbrite Event"},
            "url": "https://www.eventbrite.com/e/api-eb-001",
            "start": {"utc": "2026-10-10T15:00:00Z"},
            "end": {"utc": "2026-10-10T18:00:00Z"},
            "description": {"text": "Evento a través de la API oficial."},
            "online": False,
            "venue": {
                "name": "Digital House",
                "address": {
                    "localized_address_display": "Av. Monroe 860, Buenos Aires",
                    "latitude": "-34.5544",
                    "longitude": "-58.4488"
                }
            }
        }
    ]
}

@patch("httpx.Client")
def test_scrape_eventbrite_html_json_ld_success(mock_client_class):
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = MOCK_EVENTBRITE_JSON_LD
    mock_client.get.return_value = mock_response
    mock_client_class.return_value.__enter__.return_value = mock_client

    events = scrape_eventbrite_html_public()

    assert len(events) > 0
    event = events[0]
    assert event["title"] == "Conferencia de React y TypeScript"
    assert event["source_platform"] == "eventbrite"
    assert event["source_id"] == "789012345678"
    assert event["venue_name"] == "Marea Coworking"
    assert event["address"] == "Av. Juan B. Justo 2300"
    assert event["latitude"] == -34.5822
    assert event["longitude"] == -58.4233
    assert isinstance(event["start_time"], datetime)

@patch("httpx.Client")
def test_scrape_eventbrite_html_fallback_success(mock_client_class):
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = MOCK_EVENTBRITE_HTML_CARDS
    mock_client.get.return_value = mock_response
    mock_client_class.return_value.__enter__.return_value = mock_client

    events = scrape_eventbrite_html_public()

    assert len(events) == 2
    
    # Evento 1: extrae ID numérico mediante regex
    event1 = events[0]
    assert event1["title"] == "Taller de Python Intermedio"
    assert event1["source_platform"] == "eventbrite"
    assert event1["source_id"] == "456123"
    assert event1["address"] == "Buenos Aires, Argentina"
    assert isinstance(event1["start_time"], datetime)

    # Evento 2: fallback a MD5 al no tener dígitos la URL
    event2 = events[1]
    assert event2["title"] == "Taller Sin ID"
    assert len(event2["source_id"]) == 15
    assert event2["source_id"] != "456123"

@patch("httpx.Client")
@patch("app.scrapers.eventbrite.EVENTBRITE_API_TOKEN", "fake-token")
def test_scrape_eventbrite_api_success(mock_client_class):
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = MOCK_EVENTBRITE_API_RESPONSE
    mock_client.get.return_value = mock_response
    mock_client_class.return_value.__enter__.return_value = mock_client

    events = scrape_eventbrite_api_events()

    assert len(events) == 1
    event = events[0]
    assert event["title"] == "API Eventbrite Event"
    assert event["source_platform"] == "eventbrite"
    assert event["source_id"] == "api-eb-001"
    assert event["venue_name"] == "Digital House"
    assert event["address"] == "Av. Monroe 860, Buenos Aires"
    assert event["latitude"] == -34.5544
    assert event["longitude"] == -58.4488
    assert isinstance(event["start_time"], datetime)

@patch("httpx.Client")
@patch("app.scrapers.eventbrite.EVENTBRITE_API_TOKEN", "fake-token")
def test_scrape_eventbrite_buenos_aires_integration(mock_client_class):
    # Mockear las llamadas para el HTML público y la API REST
    mock_client = MagicMock()
    mock_response_html = MagicMock()
    mock_response_html.status_code = 200
    mock_response_html.text = MOCK_EVENTBRITE_JSON_LD
    
    mock_response_api = MagicMock()
    mock_response_api.status_code = 200
    mock_response_api.json.return_value = MOCK_EVENTBRITE_API_RESPONSE
    
    mock_client.get.side_effect = [
        mock_response_html, # Para category: science-and-tech
        mock_response_html, # Para category: business
        mock_response_html, # Para category: tech
        mock_response_html, # Para category: family-and-education
        mock_response_html, # Para category: community
        mock_response_api   # Para la llamada de la API
    ]
    
    mock_client_class.return_value.__enter__.return_value = mock_client

    events = scrape_eventbrite_buenos_aires()
    
    # Debe consolidar el evento único de HTML + el evento de API
    assert len(events) == 2
    platforms = [e["source_platform"] for e in events]
    assert all(p == "eventbrite" for p in platforms)
