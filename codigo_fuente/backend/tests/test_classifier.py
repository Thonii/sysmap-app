import pytest
from unittest.mock import MagicMock, patch
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db import Base
from app.models.event import IACache, Event
from app.pipeline.classifier import process_and_classify_event, heuristic_classify
from app.pipeline.classifier_adapter import load_classification_skill, GeminiFlashClassifier

# Configuración de base de datos SQLite en memoria para pruebas
@pytest.fixture(name="db_session")
def fixture_db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()

def test_load_classification_skill():
    """Verifica que el skill markdown se cargue correctamente y contenga palabras clave."""
    skill_content = load_classification_skill()
    assert skill_content is not None
    assert "Sysmap" in skill_content
    assert "is_tech" in skill_content
    assert "Few-Shot" in skill_content

@patch("google.generativeai.GenerativeModel")
@patch("app.pipeline.classifier_adapter.GEMINI_API_KEY", "fake-key")
def test_gemini_classifier_success(mock_model_class):
    """Prueba que el clasificador invoque a Gemini y retorne la estructura JSON parseada."""
    mock_model = MagicMock()
    mock_response = MagicMock()
    mock_response.text = '{"is_tech": true, "tags": ["React", "AI"], "reason": "Es un evento de desarrollo e IA."}'
    mock_model.generate_content.return_value = mock_response
    mock_model_class.return_value = mock_model

    classifier = GeminiFlashClassifier(model_name="gemini-2.5-flash")
    result = classifier.classify_event("Workshop de Inteligencia Artificial", "Taller interactivo de LLMs.")

    assert result["is_tech"] is True
    assert "React" in result["tags"]
    assert "AI" in result["tags"]
    mock_model_class.assert_called_with("gemini-2.5-flash", generation_config={"response_mime_type": "application/json"})

@patch("google.generativeai.GenerativeModel")
@patch("app.pipeline.classifier_adapter.GEMINI_API_KEY", "fake-key")
def test_gemini_classifier_fallback(mock_model_class):
    """Prueba que si falla el modelo principal (gemini-2.5-flash) se recurra a gemini-1.5-flash."""
    # Primer modelo falla, el segundo (fallback) tiene éxito
    mock_model_primary = MagicMock()
    mock_model_primary.generate_content.side_effect = Exception("API Error")
    
    mock_model_fallback = MagicMock()
    mock_response = MagicMock()
    mock_response.text = '{"is_tech": true, "tags": ["Python"], "reason": "Fallback exitoso."}'
    mock_model_fallback.generate_content.return_value = mock_response

    # Configuramos el mock para retornar el modelo primario en la primera llamada y el de fallback en la segunda
    mock_model_class.side_effect = [mock_model_primary, mock_model_fallback]

    classifier = GeminiFlashClassifier(model_name="gemini-2.5-flash")
    result = classifier.classify_event("Reunión de Pythonistas", "Comunidad de Python.")

    assert result["is_tech"] is True
    assert "Python" in result["tags"]
    assert result["reason"] == "Fallback exitoso."
    assert mock_model_class.call_count == 2

def test_process_and_classify_heuristic(db_session):
    """Prueba que el pipeline principal use la heurística y no llame a la IA si es concluyente."""
    with patch("app.pipeline.classifier.classify_event_with_ia") as mock_ia:
        is_tech, tags = process_and_classify_event(db_session, "Clase abierta de Salsa y Bachata", "Ven a bailar.")
        assert is_tech is False
        assert len(tags) == 0
        mock_ia.assert_not_called()

def test_process_and_classify_cached(db_session):
    """Prueba que si el hash ya existe en IACache se use el resultado de caché a Costo 0."""
    title = "Reunión de Emprendedores Tech"
    description = "Networking de fundadores."
    
    # Pre-cargar caché
    import hashlib
    text_hash = hashlib.md5(f"{title}|||{description}".encode("utf-8")).hexdigest()
    cache_entry = IACache(key=text_hash, value={"is_tech": True, "tags": ["Startups"]})
    db_session.add(cache_entry)
    db_session.commit()

    with patch("app.pipeline.classifier.classify_event_with_ia") as mock_ia:
        is_tech, tags = process_and_classify_event(db_session, title, description)
        assert is_tech is True
        assert "Startups" in tags
        mock_ia.assert_not_called()

def test_process_and_classify_ia_calls_and_saves_to_cache(db_session):
    """Prueba que si no hay heurística ni caché, llame a la IA y guarde el resultado en IACache."""
    title = "Reunión de Emprendedores Tech"
    description = "Networking de fundadores."
    
    with patch("app.pipeline.classifier.classify_event_with_ia") as mock_ia:
        mock_ia.return_value = {"is_tech": True, "tags": ["Startups"], "reason": "IA clasifica tech."}
        
        is_tech, tags = process_and_classify_event(db_session, title, description)
        
        assert is_tech is True
        assert "Startups" in tags
        mock_ia.assert_called_once()
        
        # Verificar que se guardó en caché de BD
        import hashlib
        text_hash = hashlib.md5(f"{title}|||{description}".encode("utf-8")).hexdigest()
        cached = db_session.query(IACache).filter(IACache.key == text_hash).first()
        assert cached is not None
        assert cached.value["is_tech"] is True
        assert "Startups" in cached.value["tags"]
