"""
Cliente para enviar notificaciones webhook a lacuenteria.cl
"""
import json
import logging
import time
import requests
import os
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime
from config import WEBHOOK_CONFIG

# Cargar anon_key desde archivo .env si existe
def load_anon_key():
    """Carga el anon_key desde el archivo .env"""
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                if line.startswith('anon_key='):
                    return line.split('=', 1)[1].strip()
    return os.getenv("anon_key")  # Fallback a variable de entorno del sistema

logger = logging.getLogger(__name__)


class WebhookClient:
    """Cliente para enviar webhooks a lacuenteria.cl"""
    
    def __init__(self, story_path: Optional[Path] = None):
        self.timeout = WEBHOOK_CONFIG["timeout"]
        self.max_attempts = WEBHOOK_CONFIG.get("max_attempts", WEBHOOK_CONFIG.get("max_retries", 3))
        self.retry_delay = WEBHOOK_CONFIG["retry_delay"]
        self.story_path = story_path
        self.webhook_log_path = None
        if story_path:
            self.webhook_log_path = Path(story_path) / "logs" / "webhook_completion.log"
        
        # Obtener anon_key del archivo .env o variables de entorno
        self.anon_key = load_anon_key()
        if not self.anon_key:
            logger.warning("No se encontró anon_key en .env ni en variables de entorno")
    
    def _write_webhook_log(self, content: str):
        """Escribe contenido al archivo de log del webhook"""
        if self.webhook_log_path:
            try:
                with open(self.webhook_log_path, 'a', encoding='utf-8') as f:
                    f.write(content)
            except Exception as e:
                logger.error(f"Error escribiendo log de webhook: {e}")
    
    def _format_headers(self, headers: Dict, hide_auth: bool = True) -> str:
        """Formatea headers para el log, ocultando información sensible"""
        formatted = {}
        for key, value in headers.items():
            if hide_auth and key.lower() in ['authorization', 'x-api-key']:
                formatted[key] = '[REDACTED]'
            else:
                formatted[key] = value
        return json.dumps(formatted, indent=2, ensure_ascii=False)
    
    def _build_request_headers(self, webhook_url: str) -> Dict:
        """Construye los headers para el request incluyendo autenticación si es necesario"""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Cuenteria-Orchestrator/1.0"
        }
        
        # Agregar autenticación de Supabase si está configurada
        if self.anon_key and "supabase" in webhook_url.lower():
            headers["Authorization"] = f"Bearer {self.anon_key}"
        
        return headers
    
    def _start_webhook_log(self, webhook_url: str, event_type: str, payload: Dict):
        """Inicia el log del webhook con información inicial"""
        if not self.webhook_log_path:
            return
            
        story_id = payload.get('story_id', 'unknown')
        timestamp = datetime.now().isoformat()
        
        log_header = f"""
{'='*80}
                        WEBHOOK COMPLETION LOG
{'='*80}
Story ID: {story_id}
Timestamp: {timestamp}
Event Type: {event_type}
{'='*80}

WEBHOOK ENDPOINT:
{webhook_url}

REQUEST HEADERS:
{self._format_headers(self._build_request_headers(webhook_url))}

PAYLOAD SENT ({len(json.dumps(payload))/1024:.1f} KB):
{json.dumps(payload, indent=2, ensure_ascii=False)[:5000]}{'...[TRUNCATED]' if len(json.dumps(payload)) > 5000 else ''}

{'='*80}
"""
        self._write_webhook_log(log_header)
    
    def _log_webhook_attempt(self, attempt: int, start_time: float, response=None, error=None):
        """Registra un intento de envío de webhook"""
        if not self.webhook_log_path:
            return
            
        elapsed = time.time() - start_time
        timestamp = datetime.now().isoformat()
        
        log_content = f"""ATTEMPT {attempt}/{self.max_attempts} - {timestamp}
{'-'*80}
Response Time: {elapsed:.3f}s
"""
        
        if response:
            log_content += f"""Status Code: {response.status_code} {response.reason if hasattr(response, 'reason') else ''}
Response Headers:
{self._format_headers(dict(response.headers))}

Response Body:
{response.text[:2000]}{'...[TRUNCATED]' if len(response.text) > 2000 else ''}
"""
            # Log adicional para errores del servidor
            if response.status_code >= 400:
                log_content += f"""
Status: ERROR - Server returned {response.status_code}
Full Response Text: {response.text}
"""
        elif error:
            log_content += f"""Error: {str(error)}
"""
        
        log_content += "\n"
        self._write_webhook_log(log_content)
    
    def _finalize_webhook_log(self, success: bool, total_attempts: int, start_time: float):
        """Finaliza el log del webhook con el resultado final"""
        if not self.webhook_log_path:
            return
            
        total_time = time.time() - start_time
        result = "SUCCESS" if success else "FAILED"
        
        log_footer = f"""{'='*80}
FINAL RESULT: {result}
Total Attempts: {total_attempts}
Total Time: {total_time:.3f}s
{'='*80}

"""
        self._write_webhook_log(log_footer)
    
    def send_notification(self, 
                         webhook_url: str, 
                         payload: Dict[str, Any],
                         event_type: str = "story_complete") -> bool:
        """
        Envía una notificación webhook
        
        Args:
            webhook_url: URL del webhook
            payload: Datos a enviar
            event_type: Tipo de evento
            
        Returns:
            True si se envió exitosamente, False en caso contrario
        """
        if not webhook_url:
            logger.warning("No se proporcionó URL de webhook")
            return False
        
        # Agregar metadatos al payload
        webhook_payload = {
            "event": event_type,
            "timestamp": time.time(),
            "data": payload
        }
        
        # Iniciar log del webhook
        self._start_webhook_log(webhook_url, event_type, webhook_payload)
        
        # Registrar tiempo de inicio para el proceso completo
        process_start_time = time.time()
        
        # Intentar enviar con reintentos
        for attempt in range(1, self.max_attempts + 1):
            attempt_start_time = time.time()
            try:
                logger.info(f"Enviando webhook a {webhook_url} (intento {attempt}/{self.max_attempts})")
                
                # Usar el método helper para construir headers
                headers = self._build_request_headers(webhook_url)
                
                if "Authorization" in headers:
                    logger.debug("Agregando autenticación Supabase al webhook")
                
                response = requests.post(
                    webhook_url,
                    json=webhook_payload,
                    headers=headers,
                    timeout=self.timeout
                )
                
                # SIEMPRE registrar el intento en log, exitoso o no
                self._log_webhook_attempt(attempt, attempt_start_time, response=response)
                
                # Verificar respuesta
                if response.status_code in [200, 201, 202, 204]:
                    logger.info(f"Webhook enviado exitosamente: {response.status_code}")
                    self._finalize_webhook_log(True, attempt, process_start_time)
                    return True
                else:
                    logger.warning(f"Webhook respondió con código: {response.status_code}")
                    logger.debug(f"Respuesta: {response.text[:500]}")
                    # Si es el último intento y falló, agregar información adicional al log
                    if attempt == self.max_attempts:
                        logger.error(f"Webhook falló con status {response.status_code}: {response.text[:200]}")
                    
            except requests.exceptions.Timeout as e:
                logger.warning(f"Timeout en webhook intento {attempt}")
                self._log_webhook_attempt(attempt, attempt_start_time, error=f"Timeout: {e}")
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Error enviando webhook: {e}")
                self._log_webhook_attempt(attempt, attempt_start_time, error=f"RequestException: {e}")
                
            except Exception as e:
                logger.error(f"Error inesperado en webhook: {e}")
                self._log_webhook_attempt(attempt, attempt_start_time, error=f"Unexpected error: {e}")
            
            # Esperar antes de reintentar
            if attempt < self.max_attempts:
                time.sleep(self.retry_delay)
        
        logger.error(f"Fallo el envío de webhook después de {self.max_attempts} intentos")
        self._finalize_webhook_log(False, self.max_attempts, process_start_time)
        return False
    
    def send_story_complete(self, webhook_url: str, story_result: Dict[str, Any]) -> bool:
        """
        Envía notificación de historia completada
        
        Args:
            webhook_url: URL del webhook
            story_result: Resultado completo de la historia
            
        Returns:
            True si se envió exitosamente
        """
        return self.send_notification(
            webhook_url,
            story_result,
            "story_complete"
        )
    
    def send_story_error(self, webhook_url: str, story_id: str, error: str) -> bool:
        """
        Envía notificación de error en historia
        
        Args:
            webhook_url: URL del webhook
            story_id: ID de la historia
            error: Mensaje de error
            
        Returns:
            True si se envió exitosamente
        """
        logger.info(f"Preparando webhook de error para {story_id}")
        payload = {
            "story_id": story_id,
            "status": "error",
            "error": error
        }
        
        return self.send_notification(
            webhook_url,
            payload,
            "story_error"
        )
    
    def send_story_progress(self, webhook_url: str, story_id: str, 
                           current_agent: str, progress_percent: int) -> bool:
        """
        Envía notificación de progreso
        
        Args:
            webhook_url: URL del webhook
            story_id: ID de la historia
            current_agent: Agente actual en ejecución
            progress_percent: Porcentaje de progreso (0-100)
            
        Returns:
            True si se envió exitosamente
        """
        payload = {
            "story_id": story_id,
            "status": "processing",
            "current_agent": current_agent,
            "progress": progress_percent
        }
        
        return self.send_notification(
            webhook_url,
            payload,
            "story_progress"
        )


# Singleton para reutilizar el cliente
_client_instance = None

def get_webhook_client(story_path: Optional[Path] = None) -> WebhookClient:
    """
    Obtiene una instancia del cliente webhook
    
    Args:
        story_path: Path opcional de la historia para logging
    
    Returns:
        Instancia de WebhookClient
    """
    global _client_instance
    # Si se proporciona story_path, crear nueva instancia con logging
    if story_path:
        return WebhookClient(story_path)
    # Si no, usar singleton sin logging de archivo
    if _client_instance is None:
        _client_instance = WebhookClient()
    return _client_instance