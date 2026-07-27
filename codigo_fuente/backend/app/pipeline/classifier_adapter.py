import json
import logging
from abc import ABC, abstractmethod
import google.generativeai as genai
from app.config import GEMINI_API_KEY

logger = logging.getLogger(__name__)

# Configurar API de Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

class EventClassifierAdapter(ABC):
    """
    Clase base abstracta para clasificadores de eventos.
    Permite intercambiar el motor de clasificación semántica (Gemini, Ollama, Regex, etc.).
    """
    @abstractmethod
    def classify_event(self, title: str, description: str) -> dict:
        """
        Clasifica un evento a partir de su título y descripción.
        Retorna un diccionario con la estructura:
        {
            "is_tech": bool,
            "tags": list[str],
            "reason": str
        }
        """
        pass

class GeminiFlashClassifier(EventClassifierAdapter):
    """
    Implementación nativa de EventClassifierAdapter usando Gemini 2.5 Flash / 1.5 Flash.
    """
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        self.model_name = model_name

    def classify_event(self, title: str, description: str) -> dict:
        if not GEMINI_API_KEY:
            logger.warning("GEMINI_API_KEY no configurada. Retornando falso en clasificación IA por seguridad.")
            return {"is_tech": False, "tags": [], "reason": "No API Key configured"}

        prompt = f"""
        Evalúa si el siguiente evento pertenece al nicho de tecnología, programación, desarrollo de software, startups de base tecnológica, diseño UX/UI o gestión de productos digitales.
        
        Título: {title}
        Descripción: {description[:1000] if description else ""}
        
        Responde estrictamente en formato JSON válido con los siguientes campos:
        - is_tech (boolean): true si es un evento tecnológico, false de lo contrario.
        - tags (array de strings): hasta 4 tags tecnológicos aplicables (ej: "Python", "React", "AI", "UX/UI"). Si is_tech es false, el array debe estar vacío.
        - reason (string): breve explicación de 1 frase en español.
        """

        try:
            model = genai.GenerativeModel(
                self.model_name,
                generation_config={"response_mime_type": "application/json"}
            )
            response = model.generate_content(prompt)
            result = json.loads(response.text)
            return result
        except Exception as e:
            logger.error(f"Error en GeminiFlashClassifier ({self.model_name}): {e}")
            # Fallback en caso de error del modelo
            if self.model_name != "gemini-1.5-flash":
                logger.info("Intentando fallback a gemini-1.5-flash...")
                try:
                    fallback_model = genai.GenerativeModel(
                        "gemini-1.5-flash",
                        generation_config={"response_mime_type": "application/json"}
                    )
                    response = fallback_model.generate_content(prompt)
                    return json.loads(response.text)
                except Exception as ex:
                    logger.error(f"Error en fallback a gemini-1.5-flash: {ex}")
            
            return {"is_tech": False, "tags": [], "reason": f"Gemini API Error: {str(e)}"}
