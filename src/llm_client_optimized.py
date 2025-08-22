"""
Cliente optimizado para interactuar con el modelo gpt-oss-120b
Incluye parámetros avanzados para control fino de generación
"""
import json
import time
import logging
import requests
from typing import Dict, Any, Optional, List
from src.config import LLM_CONFIG

logger = logging.getLogger(__name__)


class OptimizedLLMClient:
    """Cliente optimizado con parámetros avanzados para GPT-OSS-120B"""
    
    def __init__(self):
        self.endpoint = LLM_CONFIG["endpoint"]
        self.model = LLM_CONFIG["model"]
        self.temperature = LLM_CONFIG["temperature"]
        self.max_tokens = LLM_CONFIG["max_tokens"]
        self.timeout = 900  # 900 segundos para respuestas largas
        self.retry_attempts = LLM_CONFIG["retry_attempts"]
        self.retry_delay = LLM_CONFIG["retry_delay"]
        
    def generate(self, 
                 system_prompt: str, 
                 user_prompt: str,
                 # Parámetros básicos
                 temperature: Optional[float] = None,
                 max_tokens: Optional[int] = None,
                 # Parámetros avanzados de GPT-OSS-120B
                 top_p: Optional[float] = None,
                 top_k: Optional[int] = None,
                 repetition_penalty: Optional[float] = None,
                 frequency_penalty: Optional[float] = None,
                 presence_penalty: Optional[float] = None,
                 stop: Optional[List[str]] = None,
                 seed: Optional[int] = None,
                 # Control de generación
                 num_beams: Optional[int] = None,
                 best_of: Optional[int] = None,
                 length_penalty: Optional[float] = None,
                 early_stopping: Optional[bool] = None,
                 # Formato de respuesta
                 response_format: Optional[str] = None,
                 guided_json: Optional[bool] = None) -> Dict[str, Any]:
        """
        Genera una respuesta del modelo LLM con parámetros avanzados
        
        Args:
            system_prompt: Prompt del sistema (rol del agente)
            user_prompt: Prompt del usuario (entrada específica)
            
            Parámetros básicos:
            - temperature: Control de aleatoriedad (0.0-2.0)
            - max_tokens: Límite de tokens generados
            
            Parámetros de sampling (GPT-OSS-120B):
            - top_p: Nucleus sampling (0.0-1.0)
            - top_k: Limita vocabulario a top k tokens
            - repetition_penalty: Penaliza repeticiones (1.0-2.0)
            - frequency_penalty: Reduce frecuencia de palabras (-2.0 a 2.0)
            - presence_penalty: Incentiva nuevos tópicos (-2.0 a 2.0)
            - stop: Secuencias de parada
            - seed: Semilla para reproducibilidad
            
            Control de generación:
            - num_beams: Número de beams para beam search
            - best_of: Genera N respuestas y retorna la mejor
            - length_penalty: Penalización por longitud
            - early_stopping: Detener cuando todos los beams terminan
            
            Formato:
            - response_format: "json" para forzar JSON válido
            - guided_json: Activar generación guiada de JSON
            
        Returns:
            Dict con la respuesta del modelo
        """
        
        # Agregar instrucción JSON mejorada
        json_instruction = """

FORMATO CRÍTICO:
1. Tu respuesta debe ser ÚNICAMENTE un JSON válido
2. NO incluyas texto antes o después del JSON
3. NO uses markdown (```) para envolver el JSON
4. COMPLETA todas las páginas y campos requeridos
5. USA TODOS los tokens necesarios, NO TRUNCAR"""
        
        # Si se especifica anti-truncamiento, enfatizar más
        if max_tokens and max_tokens >= 6000:
            json_instruction += """
6. TIENES {} TOKENS DISPONIBLES - ÚSALOS TODOS SI ES NECESARIO
7. NO DEJES PÁGINAS VACÍAS O INCOMPLETAS""".format(max_tokens)
        
        messages = [
            {"role": "system", "content": system_prompt + json_instruction},
            {"role": "user", "content": user_prompt}
        ]
        
        # Construir payload base
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature or self.temperature,
            "max_tokens": max_tokens or self.max_tokens
        }
        
        # Agregar parámetros avanzados si se especifican
        if top_p is not None:
            payload["top_p"] = top_p
        if top_k is not None:
            payload["top_k"] = top_k
        if repetition_penalty is not None:
            payload["repetition_penalty"] = repetition_penalty
        if frequency_penalty is not None:
            payload["frequency_penalty"] = frequency_penalty
        if presence_penalty is not None:
            payload["presence_penalty"] = presence_penalty
        if stop is not None:
            payload["stop"] = stop
        if seed is not None:
            payload["seed"] = seed
            payload["do_sample"] = True  # Requerido para usar seed
            
        # Parámetros de beam search
        if num_beams is not None:
            payload["num_beams"] = num_beams
        if best_of is not None:
            payload["best_of"] = best_of
        if length_penalty is not None:
            payload["length_penalty"] = length_penalty
        if early_stopping is not None:
            payload["early_stopping"] = early_stopping
            
        # Formato de respuesta
        if response_format == "json":
            payload["response_format"] = {"type": "json_object"}
        if guided_json:
            payload["guided_json"] = True
            payload["grammar"] = "json"
        
        # Log de parámetros usados para debugging
        logger.debug(f"Parámetros de generación: {json.dumps({k: v for k, v in payload.items() if k != 'messages'}, indent=2)}")
        
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
                
                # Extraer información de tokens
                tokens_info = {}
                if "usage" in result:
                    tokens_info = {
                        "prompt_tokens": result["usage"].get("prompt_tokens", 0),
                        "completion_tokens": result["usage"].get("completion_tokens", 0),
                        "total_tokens": result["usage"].get("total_tokens", 0)
                    }
                    logger.info(f"Tokens usados - Prompt: {tokens_info['prompt_tokens']}, "
                               f"Completion: {tokens_info['completion_tokens']}, "
                               f"Total: {tokens_info['total_tokens']}")
                
                # Extraer el contenido generado
                if "choices" in result and len(result["choices"]) > 0:
                    content = result["choices"][0].get("message", {}).get("content")
                    
                    if content is None or content == "":
                        logger.warning("El modelo devolvió contenido vacío")
                        raise ValueError("El modelo no generó contenido")
                    
                    # Detectar posibles respuestas truncadas
                    if self._is_truncated(content):
                        logger.warning(f"Posible respuesta truncada detectada")
                        logger.debug(f"Últimos 100 caracteres: ...{content[-100:]}")
                        # Si hay reintentos disponibles, intentar con más tokens
                        if attempt < self.retry_attempts - 1 and max_tokens:
                            payload["max_tokens"] = int(max_tokens * 1.5)
                            logger.info(f"Aumentando max_tokens a {payload['max_tokens']} para siguiente intento")
                            raise ValueError("Respuesta truncada, reintentando con más tokens")
                    
                    # Intentar parsear como JSON
                    try:
                        json_content = json.loads(content)
                        logger.info("✅ Respuesta JSON válida recibida del LLM")
                        
                        # Validar completitud para editor_claridad
                        if "paginas" in json_content:
                            empty_pages = [p for p, text in json_content["paginas"].items() 
                                         if not text.get("texto", "").strip()]
                            if empty_pages:
                                logger.warning(f"⚠️ Páginas vacías detectadas: {empty_pages}")
                                if attempt < self.retry_attempts - 1:
                                    raise ValueError(f"Páginas vacías: {empty_pages}")
                        
                        # Agregar metadata
                        if tokens_info:
                            json_content["_metadata_tokens"] = tokens_info
                        json_content["_metadata_params"] = {
                            "temperature": temperature or self.temperature,
                            "top_p": top_p,
                            "repetition_penalty": repetition_penalty,
                            "attempt": attempt + 1
                        }
                        
                        return json_content
                        
                    except json.JSONDecodeError as e:
                        logger.warning(f"La respuesta no es JSON válido: {e}")
                        # Intentar limpiar y parsear de nuevo
                        cleaned_content = self._clean_json_response(content)
                        try:
                            json_content = json.loads(cleaned_content)
                            logger.info("JSON limpiado y parseado exitosamente")
                            if tokens_info:
                                json_content["_metadata_tokens"] = tokens_info
                            return json_content
                        except:
                            raise ValueError(f"No se pudo parsear como JSON: {content[:500]}...")
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
    
    def _is_truncated(self, content: str) -> bool:
        """
        Detecta si una respuesta parece estar truncada
        """
        content = content.rstrip()
        
        # Indicadores de truncamiento
        truncation_indicators = [
            '...',
            '\\',
            '"',
            ',',
            '{',
            '[',
            ':',
            # JSON incompleto
            content.count('{') != content.count('}'),
            content.count('[') != content.count(']'),
            # Termina en medio de una palabra
            content[-1:].isalpha() and not content.endswith('"}')
        ]
        
        return any(truncation_indicators[:7]) or truncation_indicators[7] or truncation_indicators[8] or truncation_indicators[9]
    
    def _clean_json_response(self, content: str) -> str:
        """
        Intenta limpiar una respuesta para hacerla JSON válido
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
        
        cleaned = content[start_idx:end_idx]
        
        # Intentar arreglar JSON truncado común
        if cleaned.count('{') > cleaned.count('}'):
            cleaned += '}' * (cleaned.count('{') - cleaned.count('}'))
        if cleaned.count('[') > cleaned.count(']'):
            cleaned += ']' * (cleaned.count('[') - cleaned.count(']'))
            
        return cleaned
    
    def validate_connection(self) -> bool:
        """
        Valida que el endpoint del LLM esté disponible
        """
        try:
            # Intentar endpoint /v1/models
            models_endpoint = self.endpoint.replace("/v1/chat/completions", "/v1/models")
            response = requests.get(models_endpoint, timeout=5)
            if response.status_code == 200:
                return True
        except:
            pass
        
        try:
            # Si no funciona, intentar con una petición mínima
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
        Aproximación: 1 token ≈ 4 caracteres
        """
        return len(text) // 4


# Singleton optimizado
_optimized_client = None

def get_optimized_llm_client() -> OptimizedLLMClient:
    """
    Obtiene una instancia singleton del cliente LLM optimizado
    """
    global _optimized_client
    if _optimized_client is None:
        _optimized_client = OptimizedLLMClient()
    return _optimized_client