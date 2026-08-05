import json
import logging
import os
import time
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

def load_classification_skill() -> str:
    """Carga las directrices del clasificador desde el archivo Markdown estático de skills."""
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        skill_path = os.path.join(os.path.dirname(current_dir), "skills", "classification_skill.md")
        with open(skill_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error cargando el archivo de skill markdown: {e}")
        # Prompt de respaldo en caso de fallo de lectura física
        return """
        Evalúa si el siguiente evento pertenece al nicho de tecnología, programación, desarrollo de software, startups de base tecnológica, diseño UX/UI o gestión de productos digitales.
        Responde estrictamente en formato JSON válido con los siguientes campos:
        - is_tech (boolean): true si es un evento tecnológico, false de lo contrario.
        - tags (array de strings): hasta 4 tags tecnológicos aplicables.
        - reason (string): breve explicación en español.
        """

class GeminiFlashClassifier(EventClassifierAdapter):
    """
    Implementación nativa de EventClassifierAdapter usando Gemini 2.5 Flash / 1.5 Flash.
    Carga dinámicamente las directrices del radar desde un archivo de skill en Markdown.
    """
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        self.model_name = model_name

    def classify_event(self, title: str, description: str) -> dict:
        if not GEMINI_API_KEY:
            logger.warning("GEMINI_API_KEY no configurada. Retornando falso en clasificación IA por seguridad.")
            return {"is_tech": False, "tags": [], "reason": "No API Key configured"}

        # 1. Cargar el prompt de skill estático en Markdown
        skill_content = load_classification_skill()

        # 2. Construir prompt inyectando variables del evento
        prompt = f"""
{skill_content}

---
A continuación se encuentra el evento a clasificar del radar en tiempo real:
Título: {title}
Descripción: {description[:1000] if description else ""}

Recuerda responder única y estrictamente con el JSON solicitado sin bloques de código markdown ni explicaciones adicionales.
"""

        # 3. Invocar modelo principal con telemetría de latencia
        start_time = time.time()
        active_model = self.model_name
        
        try:
            logger.info(f"Iniciando llamada a {active_model} para clasificar evento: '{title}'")
            model = genai.GenerativeModel(
                active_model,
                generation_config={"response_mime_type": "application/json"}
            )
            response = model.generate_content(prompt)
            result = json.loads(response.text)
            
            latency = time.time() - start_time
            logger.info(f"[TELEMETRÍA] Clasificación exitosa con {active_model} | Latencia: {latency:.3f}s")
            return result

        except Exception as e:
            logger.warning(f"Error en GeminiFlashClassifier con {active_model}: {e}. Intentando fallback...")
            
            # Fallback inmediato a gemini-1.5-flash
            if active_model != "gemini-1.5-flash":
                fallback_start = time.time()
                active_model = "gemini-1.5-flash"
                try:
                    logger.info(f"Llamando al modelo de fallback {active_model} para: '{title}'")
                    fallback_model = genai.GenerativeModel(
                        active_model,
                        generation_config={"response_mime_type": "application/json"}
                    )
                    response = fallback_model.generate_content(prompt)
                    result = json.loads(response.text)
                    
                    latency = time.time() - fallback_start
                    logger.info(f"[TELEMETRÍA] Fallback exitoso con {active_model} | Latencia: {latency:.3f}s")
                    return result
                except Exception as ex:
                    logger.error(f"Error crítico en fallback a {active_model}: {ex}")
            
            # Fallback final a valores por defecto seguros
            total_latency = time.time() - start_time
            logger.error(f"[TELEMETRÍA] Clasificación fallida tras {total_latency:.3f}s | Retornando default")
            return {
                "is_tech": False,
                "tags": [],
                "reason": f"Fallo en todos los modelos de IA: {str(e)}"
            }

