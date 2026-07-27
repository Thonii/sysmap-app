import pytest
from app.pipeline.classifier import heuristic_classify

def test_heuristic_classify_tech_success():
    """
    Prueba que palabras clave obvias de tecnología clasifiquen el evento como tecnológico.
    """
    title = "Workshop de Python y Machine Learning"
    description = "Aprende Python desde cero y construye tus primeros modelos de machine learning en este taller práctico."
    
    is_tech, tags = heuristic_classify(title, description)
    
    assert is_tech is True
    assert "python" in tags
    assert "machine learning" in tags

def test_heuristic_classify_non_tech_success():
    """
    Prueba que palabras clave no tecnológicas descarten el evento inmediatamente.
    """
    title = "Clase abierta de Salsa y Bachata"
    description = "Ven a bailar con nosotros este viernes por la noche en Palermo. No se requiere experiencia previa."
    
    is_tech, tags = heuristic_classify(title, description)
    
    assert is_tech is False
    assert len(tags) == 0

def test_heuristic_classify_doubtful():
    """
    Prueba que un evento con contenido ambiguo no sea clasificado por la heurística local (retorne None).
    """
    title = "Reunión de Emprendedores y Creadores en Palermo"
    description = "Ven a charlar sobre ideas de negocios, conocer gente interesante y compartir experiencias en un bar local."
    
    is_tech, tags = heuristic_classify(title, description)
    
    assert is_tech is None
    assert len(tags) == 0
