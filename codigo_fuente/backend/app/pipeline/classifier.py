import hashlib
import json
import logging
from sqlalchemy.orm import Session
from app.config import GEMINI_API_KEY
from app.models.event import IACache
from app.pipeline.classifier_adapter import GeminiFlashClassifier

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Instancia global del clasificador por defecto (Gemini 2.5 Flash)
# Se puede parametrizar o cargar dinámicamente si se añaden otros adaptadores
classifier_instance = GeminiFlashClassifier(model_name="gemini-2.5-flash")

# Listas de palabras clave para clasificación heurística local
TECH_KEYWORDS = [
    "python", "javascript", "typescript", "react", "vue", "angular", "node", "backend", "frontend",
    "devops", "docker", "kubernetes", "aws", "gcp", "azure", "cloud", "machine learning", "deep learning",
    "inteligencia artificial", "ia", "ai", "datascience", "ciencia de datos", "sql", "postgresql",
    "mongodb", "rust", "golang", "java", "kotlin", "swift", "flutter", "react native", "api", "git",
    "github", "blockchain", "ciberseguridad", "cybersecurity", "security", "agile", "scrum",
    "ux", "ui", "product management", "qa", "testing", "microservicios", "linux", "programming",
    "programacion", "desarrollo", "software", "tecnologia", "web3", "copilot", "llm", "prompt engineering"
]

NON_TECH_KEYWORDS = [
    "yoga", "meditacion", "salsa", "bachata", "futbol", "canto", "teatro", "cocina", "gastronomia",
    "ingles conversacional", "idiomas", "finanzas personales", "inversiones inmobiliarias",
    "bienes raices", "terapia", "astrologia", "tarot", "psicologia", "autoayuda", "cuidado de la piel",
    "maquillaje", "moda", "costura", "ciclismo", "maraton", "fitness", "crossfit", "baile"
]

import re

def clean_text(text: str) -> str:
    if not text:
        return ""
    return text.lower().strip()

def word_in_text(word: str, text: str) -> bool:
    """Busca una palabra o frase exacta en el texto usando límites de palabra."""
    pattern = rf"\b{re.escape(word)}\b"
    return bool(re.search(pattern, text, re.IGNORECASE))

def heuristic_classify(title: str, description: str) -> tuple[bool | None, list[str]]:
    """
    Clasifica el evento de forma local usando palabras clave heurísticas precisas.
    Retorna (is_tech, tags) si se puede clasificar localmente, o (None, []) si es dudoso.
    """
    title_clean = clean_text(title)
    desc_clean = clean_text(description)
    
    # 1. Comprobar palabras que descartan tecnología de forma contundente (límites de palabra)
    for keyword in NON_TECH_KEYWORDS:
        if word_in_text(keyword, title_clean):
            logger.info(f"Heurística NO-TECH detectada en título: '{keyword}' para '{title}'")
            return False, []

    # 2. Comprobar palabras de tecnología contundentes (límites de palabra)
    matched_tags = []
    for keyword in TECH_KEYWORDS:
        in_title = word_in_text(keyword, title_clean)
        in_desc = len(re.findall(rf"\b{re.escape(keyword)}\b", desc_clean)) >= 2
        if in_title or in_desc:
            matched_tags.append(keyword)

    if matched_tags:
        logger.info(f"Heurística TECH detectada: {matched_tags} para '{title}'")
        return True, matched_tags

    # Si no coincide con nada obvio, queda en duda (None)
    return None, []

def get_hash(text: str) -> str:
    """Genera un hash md5 único para el texto."""
    return hashlib.md5(text.encode("utf-8")).hexdigest()

def get_cached_classification(db: Session, text_hash: str) -> dict | None:
    """Busca una clasificación previa en caché."""
    cached = db.query(IACache).filter(IACache.key == text_hash).first()
    if cached:
        logger.info("Clasificación recuperada de la CACHÉ local (Costo 0)")
        return cached.value
    return None

def save_to_cache(db: Session, text_hash: str, value: dict):
    """Guarda la clasificación en caché."""
    try:
        new_cache = IACache(key=text_hash, value=value)
        db.add(new_cache)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Error guardando caché IA: {e}")

def classify_event_with_ia(title: str, description: str) -> dict:
    """
    Llama al clasificador configurado para clasificar el evento y extraer tags.
    """
    return classifier_instance.classify_event(title, description)

def process_and_classify_event(db: Session, title: str, description: str) -> tuple[bool, list[str]]:
    """
    Pipeline principal de clasificación:
    1. Heurística local (Costo 0).
    2. Si hay duda, buscar en caché de base de datos (Costo 0).
    3. Si no está en caché, llamar a Gemini 1.5 Flash y persistir resultado.
    """
    # 1. Heurística
    is_tech, tags = heuristic_classify(title, description)
    if is_tech is not None:
        return is_tech, tags

    # 2. Generar hash y verificar caché
    text_to_hash = f"{title}|||{description or ''}"
    text_hash = get_hash(text_to_hash)
    
    cached_result = get_cached_classification(db, text_hash)
    if cached_result:
        return cached_result.get("is_tech", True), cached_result.get("tags", [])

    # 3. Clasificación con IA
    logger.info(f"Llamando al clasificador IA configurado ({classifier_instance.model_name}) para clasificar: '{title}'")
    ia_result = classify_event_with_ia(title, description)
    
    # Guardar en caché
    save_to_cache(db, text_hash, ia_result)
    
    return ia_result.get("is_tech", True), ia_result.get("tags", [])
