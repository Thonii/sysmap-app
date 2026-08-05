import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
from app.scrapers.luma import scrape_luma_buenos_aires

# Respuestas HTML mockeadas para Luma con __NEXT_DATA__
MOCK_LUMA_NEXT_DATA = """
<html>
  <head>
    <script id="__NEXT_DATA__" type="application/json">
      {
        "props": {
          "pageProps": {
            "initialData": {
              "data": {
                "events": [
                  {
                    "event": {
                      "id": "evt-luma777",
                      "name": "Conferencia de Cloud Computing",
                      "url": "cloud-conferencia",
                      "start_at": "2026-08-20T14:00:00.000Z",
                      "end_at": "2026-08-20T18:00:00.000Z",
                      "description": "Explorando la infraestructura moderna.",
                      "geo_name": "Digital House Belgrano",
                      "geo_address_info": {
                        "full_address": "Av. Monroe 860",
                        "latitude": -34.5544,
                        "longitude": -58.4488
                      }
                    }
                  }
                ]
              }
            }
          }
        }
      }
    </script>
  </head>
</html>
"""

MOCK_LUMA_HTML_CARDS = """
<html>
  <body>
    <a href="/rust-networking" class="event-card">
      <h3 class="title">Networking de Rust & Web3</h3>
      <p class="description">Charla informal y cervezas en Palermo.</p>
    </a>
  </body>
</html>
"""

@patch("httpx.Client")
def test_scrape_luma_next_data_success(mock_client_class):
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = MOCK_LUMA_NEXT_DATA
    mock_client.get.return_value = mock_response
    mock_client_class.return_value.__enter__.return_value = mock_client

    events = scrape_luma_buenos_aires()

    assert len(events) == 1
    event = events[0]
    assert event["title"] == "Conferencia de Cloud Computing"
    assert event["source_platform"] == "luma"
    assert event["source_id"] == "evt-luma777"
    assert event["source_url"] == "https://luma.com/cloud-conferencia"
    assert event["venue_name"] == "Digital House Belgrano"
    assert event["address"] == "Av. Monroe 860"
    assert event["latitude"] == -34.5544
    assert event["longitude"] == -58.4488
    assert isinstance(event["start_time"], datetime)

@patch("httpx.Client")
def test_scrape_luma_fallback_success(mock_client_class):
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = MOCK_LUMA_HTML_CARDS
    mock_client.get.return_value = mock_response
    mock_client_class.return_value.__enter__.return_value = mock_client

    events = scrape_luma_buenos_aires()

    assert len(events) == 1
    event = events[0]
    assert event["title"] == "Networking de Rust & Web3"
    assert event["source_platform"] == "luma"
    assert event["source_id"] == "rust-networking"
    assert event["source_url"] == "https://lu.ma/rust-networking"
    assert isinstance(event["start_time"], datetime)

@patch("httpx.Client")
def test_scrape_luma_failure_status(mock_client_class):
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_client.get.return_value = mock_response
    mock_client_class.return_value.__enter__.return_value = mock_client

    events = scrape_luma_buenos_aires()
    assert len(events) == 0
