import pytest
from datetime import datetime, timezone
from app.models.event import Event
from app.pipeline.newsletter import build_newsletter_html, build_welcome_html

def test_build_newsletter_html():
    # 1. Crear un evento de prueba
    event = Event(
        id="123e4567-e89b-12d3-a456-426614174000",
        title="Python Buenos Aires Meetup",
        source_platform="Meetup",
        source_url="https://meetup.com/python-ba",
        start_time=datetime(2026, 8, 1, 19, 0, tzinfo=timezone.utc),
        venue_name="Área Tres El Salvador",
        address="El Salvador 5218, CABA",
        tags=["python", "django", "backend"],
        is_tech=True
    )
    
    events = [event]
    subscriber_email = "test_sub@example.com"
    
    # 2. Generar HTML
    html = build_newsletter_html(events, subscriber_email)
    
    # 3. Validar contenido esperado
    assert "SYSMAP" in html
    assert "Python Buenos Aires Meetup" in html
    assert "test_sub@example.com" in html
    # Validar que incluye el enlace de desuscripción
    assert "unsubscribe?email=test_sub@example.com" in html
    # Validar que incluye los tags de tecnología
    assert "#python" in html
    # Validar que incluye el link de Google Maps
    assert "https://www.google.com/maps/search/?api=1" in html
    # Validar enlace de registro
    assert "https://meetup.com/python-ba" in html

def test_build_welcome_html():
    event = Event(
        title="AI Workshop",
        start_time=datetime(2026, 8, 2, 10, 0, tzinfo=timezone.utc),
        venue_name="Online",
        is_tech=True
    )
    
    html = build_welcome_html("welcome_user@example.com", [event])
    
    assert "Bienvenido a Sysmap" in html
    assert "Suscripción Confirmada" in html
    assert "welcome_user@example.com" in html
    assert "AI Workshop" in html
