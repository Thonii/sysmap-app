import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
from app.scrapers.meetup import scrape_meetup_buenos_aires

# Respuestas HTML mockeadas para Meetup
MOCK_MEETUP_JSON_LD = """
<html>
  <head>
    <script type="application/ld+json">
      [
        {
          "@type": "Event",
          "name": "Meetup de IA y Machine Learning",
          "url": "https://www.meetup.com/es/ai-ba/events/meetup123/",
          "startDate": "2026-09-15T19:00:00Z",
          "endDate": "2026-09-15T22:00:00Z",
          "description": "Una charla de agentes autónomos y LLMs.",
          "location": {
            "@type": "Place",
            "name": "Area Tres Palermo",
            "address": {
              "@type": "PostalAddress",
              "streetAddress": "El Salvador 5218"
            },
            "geo": {
              "@type": "GeoCoordinates",
              "latitude": "-34.5889",
              "longitude": "-58.4312"
            }
          }
        }
      ]
    </script>
  </head>
</html>
"""

MOCK_MEETUP_HTML_CARDS = """
<html>
  <body>
    <div>
      <a href="/es-ES/events/987654321/">
        <span>Taller de Programación en Rust</span>
      </a>
    </div>
  </body>
</html>
"""

@patch("httpx.Client")
def test_scrape_meetup_json_ld_success(mock_client_class):
    # Configurar mock de httpx.Client
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = MOCK_MEETUP_JSON_LD
    mock_client.get.return_value = mock_response
    mock_client_class.return_value.__enter__.return_value = mock_client

    events = scrape_meetup_buenos_aires()

    assert len(events) == 1
    event = events[0]
    assert event["title"] == "Meetup de IA y Machine Learning"
    assert event["source_platform"] == "meetup"
    assert event["source_id"] == "meetup123"
    assert event["venue_name"] == "Area Tres Palermo"
    assert event["address"] == "El Salvador 5218"
    assert event["latitude"] == -34.5889
    assert event["longitude"] == -58.4312
    assert isinstance(event["start_time"], datetime)

@patch("httpx.Client")
def test_scrape_meetup_fallback_success(mock_client_class):
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = MOCK_MEETUP_HTML_CARDS
    mock_client.get.return_value = mock_response
    mock_client_class.return_value.__enter__.return_value = mock_client

    events = scrape_meetup_buenos_aires()

    assert len(events) == 1
    event = events[0]
    assert event["title"] == "Taller de Programación en Rust"
    assert event["source_platform"] == "meetup"
    assert event["source_id"] == "987654321"
    assert event["address"] == "Buenos Aires, Argentina"
    assert isinstance(event["start_time"], datetime)

@patch("httpx.Client")
def test_scrape_meetup_failure_status(mock_client_class):
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_client.get.return_value = mock_response
    mock_client_class.return_value.__enter__.return_value = mock_client

    events = scrape_meetup_buenos_aires()
    assert len(events) == 0
