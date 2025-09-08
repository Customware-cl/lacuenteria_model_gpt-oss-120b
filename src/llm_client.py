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
        self.endpoint = LLM_CONFIG.get("api_url", "http://69.19.136.204:8000/v1/chat/completions")
        self.model = "openai/gpt-oss-120b"  # Corregido al nombre del modelo correcto
        self.temperature = LLM_CONFIG["temperature"]
        self.max_tokens = LLM_CONFIG["max_tokens"]
        self.timeout = 900  # Aumentar timeout a 900 segundos para respuestas largas
        self.retry_attempts = LLM_CONFIG["retry_attempts"]
        self.retry_delay = LLM_CONFIG["retry_delay"]
        
    def generate(self, 
                 system_prompt: str, 
                 user_prompt: str,
                 temperature: Optional[float] = None,
                 max_tokens: Optional[int] = None,
                 top_p: Optional[float] = None) -> Dict[str, Any]:
        """
        Genera una respuesta del modelo LLM
        
        Args:
            system_prompt: Prompt del sistema (rol del agente)
            user_prompt: Prompt del usuario (entrada específica)
            temperature: Temperatura opcional (sobrescribe la configuración)
            max_tokens: Tokens máximos opcionales (sobrescribe la configuración)
            top_p: Top-p (nucleus sampling) opcional (sobrescribe la configuración)
            
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
        
        # Agregar top_p si se proporciona
        if top_p is not None:
            payload["top_p"] = top_p
        
        # Intentar con reintentos
        last_error = None
        stop_immediately = False
        stop_error = None
        
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
                
                # Extraer tokens consumidos si están disponibles
                tokens_info = {}
                if "usage" in result:
                    tokens_info = {
                        "prompt_tokens": result["usage"].get("prompt_tokens", 0),
                        "completion_tokens": result["usage"].get("completion_tokens", 0),
                        "total_tokens": result["usage"].get("total_tokens", 0)
                    }
                    logger.debug(f"Tokens consumidos - Prompt: {tokens_info['prompt_tokens']}, Completion: {tokens_info['completion_tokens']}")
                
                # Extraer el contenido generado
                if "choices" in result and len(result["choices"]) > 0:
                    content = result["choices"][0].get("message", {}).get("content")
                    
                    # Detectar contenido vacío o respuestas de rechazo
                    respuestas_rechazo = [
                        "lo siento",
                        "no puedo",
                        "unable to",
                        "cannot comply",
                        "no es posible"
                    ]
                    
                    es_contenido_vacio = content is None or content == ""
                    es_rechazo = False
                    
                    if content and len(content) < 200:  # Solo verificar respuestas cortas
                        contenido_lower = content.lower()
                        es_rechazo = any(frase in contenido_lower for frase in respuestas_rechazo)
                    
                    if es_contenido_vacio or es_rechazo:
                        if es_contenido_vacio:
                            logger.error("🚨 ALERTA: El modelo devolvió contenido vacío")
                        else:
                            logger.error(f"🚨 ALERTA: El modelo rechazó la solicitud: {content[:100]}")
                        
                        # Si es el primer intento, detener inmediatamente sin reintentar
                        if attempt == 0:
                            logger.error("❌ DETENIENDO: Contenido vacío en primer intento - NO se reintentará")
                            logger.error(f"   Contexto del fallo:")
                            logger.error(f"   - Max tokens: {max_tokens}")
                            logger.error(f"   - Temperature: {temperature}")
                            logger.error(f"   - Timeout: {self.timeout}s")
                            logger.error(f"   - Prompt length: {len(user_prompt)} chars")
                            logger.error(f"   - System prompt length: {len(system_prompt)} chars")
                            logger.error(f"   - Total: {len(system_prompt) + len(user_prompt)} chars (~{(len(system_prompt) + len(user_prompt))//4} tokens)")
                            
                            # Lanzar excepción especial para indicar que no debe reintentarse
                            if es_rechazo:
                                raise ValueError(f"STOP: El modelo rechazó la solicitud en el primer intento: {content[:100]}")
                            else:
                                raise ValueError("STOP: El modelo no generó contenido en el primer intento - contexto probablemente excedido")
                        else:
                            logger.warning(f"Contenido vacío/rechazado en intento {attempt + 1}")
                            if es_rechazo:
                                raise ValueError(f"El modelo rechazó la solicitud: {content[:100]}")
                            else:
                                raise ValueError("El modelo no generó contenido")
                    
                    # Detectar posibles respuestas truncadas
                    if content.rstrip().endswith(('...', '"', '\\', ',', '{', '[')):
                        logger.warning(f"Posible respuesta truncada detectada. Último carácter: '{content[-1]}'")
                        logger.debug(f"Longitud de respuesta: {len(content)} caracteres")
                    
                    # Intentar parsear como JSON
                    try:
                        json_content = json.loads(content)
                        logger.info("Respuesta JSON válida recibida del LLM")
                        # Agregar información de tokens al resultado
                        if tokens_info:
                            json_content["_metadata_tokens"] = tokens_info
                        return json_content
                    except json.JSONDecodeError as e:
                        logger.warning(f"La respuesta no es JSON válido: {e}")
                        logger.debug(f"Contenido recibido: {content[:500]}")
                        
                        # Verificar si es una respuesta de rechazo antes de intentar limpiar
                        respuestas_rechazo_json = [
                            "i'm sorry", "i cannot", "unable to", "cannot comply",
                            "lo siento", "no puedo", "no es posible", "can't fulfill"
                        ]
                        contenido_lower = content.lower() if content else ""
                        es_rechazo_json = any(frase in contenido_lower for frase in respuestas_rechazo_json)
                        
                        if es_rechazo_json and attempt == 0:
                            logger.error(f"🛑 STOP: Modelo rechazó generar JSON en primer intento: {content[:100]}")
                            raise ValueError(f"STOP: El modelo rechazó generar JSON: {content[:100]}")
                        
                        # Intentar limpiar y parsear de nuevo
                        cleaned_content = self._clean_json_response(content)
                        try:
                            json_content = json.loads(cleaned_content)
                            logger.info("Respuesta JSON limpiada y parseada exitosamente")
                            # Agregar información de tokens al resultado
                            if tokens_info:
                                json_content["_metadata_tokens"] = tokens_info
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
                
            except ValueError as ve:
                # Si es el error especial de STOP, salir inmediatamente del bucle
                if "STOP:" in str(ve):
                    logger.error("🛑 Deteniendo proceso - No se realizarán reintentos")
                    stop_immediately = True
                    stop_error = ve
                    break  # Salir del bucle for inmediatamente
                else:
                    last_error = f"Error en intento {attempt + 1}: {ve}"
                    logger.error(last_error)
                    
            except Exception as e:
                last_error = f"Error en intento {attempt + 1}: {e}"
                logger.error(last_error)
                
            # Esperar antes de reintentar
            if attempt < self.retry_attempts - 1:
                time.sleep(self.retry_delay)
        
        # Verificar si debemos detener inmediatamente
        if stop_immediately:
            raise stop_error
        
        # Si llegamos aquí, todos los intentos fallaron normalmente
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