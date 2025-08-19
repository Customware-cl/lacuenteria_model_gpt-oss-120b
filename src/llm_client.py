"""
Cliente para interactuar con el modelo gpt-oss-120b local
"""
import json
import time
import logging
import requests
from typing import Dict, Any, Optional
from config import LLM_CONFIG

logger = logging.getLogger(__name__)


class LLMClient:
    """Cliente para el modelo LLM local gpt-oss-120b"""
    
    def __init__(self):
        self.endpoint = LLM_CONFIG["endpoint"]
        self.model = LLM_CONFIG["model"]
        self.temperature = LLM_CONFIG["temperature"]
        self.max_tokens = LLM_CONFIG["max_tokens"]
        self.timeout = LLM_CONFIG["timeout"]
        self.retry_attempts = LLM_CONFIG["retry_attempts"]
        self.retry_delay = LLM_CONFIG["retry_delay"]
        
    def generate(self, 
                 system_prompt: str, 
                 user_prompt: str,
                 temperature: Optional[float] = None,
                 max_tokens: Optional[int] = None) -> Dict[str, Any]:
        """
        Genera una respuesta del modelo LLM
        
        Args:
            system_prompt: Prompt del sistema (rol del agente)
            user_prompt: Prompt del usuario (entrada específica)
            temperature: Temperatura opcional (sobrescribe la configuración)
            max_tokens: Tokens máximos opcionales (sobrescribe la configuración)
            
        Returns:
            Dict con la respuesta del modelo
            
        Raises:
            Exception: Si falla después de todos los reintentos
        """
        # Construir el prompt completo
        # Incluir instrucción JSON en el system prompt
        json_instruction = "\n\nIMPORTANTE: Tu respuesta debe ser ÚNICAMENTE un JSON válido, sin texto adicional antes o después."
        messages = [
            {"role": "system", "content": system_prompt + json_instruction},
            {"role": "user", "content": user_prompt}
        ]
        
        # Preparar el payload para chat/completions
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature or self.temperature,
            "max_tokens": max_tokens or self.max_tokens
        }
        
        # Intentar con reintentos
        last_error = None
        for attempt in range(self.retry_attempts):
            try:
                logger.info(f"Intento {attempt + 1}/{self.retry_attempts} de llamada a LLM")
                
                # Hacer la petición
                response = requests.post(
                    self.endpoint,
                    json=payload,
                    timeout=self.timeout,
                    headers={"Content-Type": "application/json"}
                )
                
                # Verificar respuesta
                response.raise_for_status()
                
                # Parsear respuesta
                result = response.json()
                
                # Extraer el contenido generado
                if "choices" in result and len(result["choices"]) > 0:
                    content = result["choices"][0].get("message", {}).get("content")
                    
                    if content is None or content == "":
                        logger.warning("El modelo devolvió contenido vacío")
                        raise ValueError("El modelo no generó contenido")
                    
                    # Intentar parsear como JSON
                    try:
                        json_content = json.loads(content)
                        logger.info("Respuesta JSON válida recibida del LLM")
                        return json_content
                    except json.JSONDecodeError as e:
                        logger.warning(f"La respuesta no es JSON válido: {e}")
                        logger.debug(f"Contenido recibido: {content[:500]}")
                        # Intentar limpiar y parsear de nuevo
                        cleaned_content = self._clean_json_response(content)
                        try:
                            json_content = json.loads(cleaned_content)
                            logger.info("Respuesta JSON limpiada y parseada exitosamente")
                            return json_content
                        except:
                            raise ValueError(f"No se pudo parsear la respuesta como JSON: {content[:500]}")
                else:
                    raise ValueError(f"Respuesta inesperada del modelo: {result}")
                    
            except requests.exceptions.Timeout:
                last_error = f"Timeout en intento {attempt + 1}"
                logger.warning(last_error)
                
            except requests.exceptions.RequestException as e:
                last_error = f"Error de red en intento {attempt + 1}: {e}"
                logger.warning(last_error)
                
            except Exception as e:
                last_error = f"Error en intento {attempt + 1}: {e}"
                logger.error(last_error)
                
            # Esperar antes de reintentar
            if attempt < self.retry_attempts - 1:
                time.sleep(self.retry_delay)
        
        # Si llegamos aquí, todos los intentos fallaron
        raise Exception(f"Fallo después de {self.retry_attempts} intentos. Último error: {last_error}")
    
    def _clean_json_response(self, content: str) -> str:
        """
        Intenta limpiar una respuesta para hacerla JSON válido
        
        Args:
            content: Contenido a limpiar
            
        Returns:
            Contenido limpio
        """
        # Remover posibles marcadores de código
        content = content.replace("```json", "").replace("```", "")
        
        # Remover espacios en blanco al inicio y final
        content = content.strip()
        
        # Si no empieza con { o [, buscar el primer carácter válido
        start_idx = 0
        for i, char in enumerate(content):
            if char in "{[":
                start_idx = i
                break
        
        # Si no termina con } o ], buscar el último carácter válido
        end_idx = len(content)
        for i in range(len(content) - 1, -1, -1):
            if content[i] in "}]":
                end_idx = i + 1
                break
        
        return content[start_idx:end_idx]
    
    def validate_connection(self) -> bool:
        """
        Valida que el endpoint del LLM esté disponible
        
        Returns:
            True si el endpoint responde, False en caso contrario
        """
        try:
            # Primero intentar endpoint /v1/models
            models_endpoint = self.endpoint.replace("/v1/chat/completions", "/v1/models")
            response = requests.get(models_endpoint, timeout=5)
            if response.status_code == 200:
                return True
        except:
            pass
        
        try:
            # Si no funciona, intentar con una petición mínima de chat
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": "test"}],
                "max_tokens": 1
            }
            response = requests.post(
                self.endpoint,
                json=payload,
                timeout=5,
                headers={"Content-Type": "application/json"}
            )
            return response.status_code == 200
        except:
            return False
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estima el número de tokens en un texto
        Aproximación simple: 1 token ≈ 4 caracteres
        
        Args:
            text: Texto a estimar
            
        Returns:
            Número estimado de tokens
        """
        return len(text) // 4


# Singleton para reutilizar el cliente
_client_instance = None

def get_llm_client() -> LLMClient:
    """
    Obtiene una instancia singleton del cliente LLM
    
    Returns:
        Instancia de LLMClient
    """
    global _client_instance
    if _client_instance is None:
        _client_instance = LLMClient()
    return _client_instance