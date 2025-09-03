"""
Cliente para enviar notificaciones webhook a lacuenteria.cl
"""
import json
import logging
import time
import requests
from typing import Dict, Any, Optional
from config import WEBHOOK_CONFIG

logger = logging.getLogger(__name__)


class WebhookClient:
    """Cliente para enviar webhooks a lacuenteria.cl"""
    
    def __init__(self):
        self.timeout = WEBHOOK_CONFIG["timeout"]
        self.max_attempts = WEBHOOK_CONFIG.get("max_attempts", WEBHOOK_CONFIG.get("max_retries", 3))
        self.retry_delay = WEBHOOK_CONFIG["retry_delay"]
    
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
        
        # Intentar enviar con reintentos
        for attempt in range(1, self.max_attempts + 1):
            try:
                logger.info(f"Enviando webhook a {webhook_url} (intento {attempt}/{self.max_attempts})")
                
                response = requests.post(
                    webhook_url,
                    json=webhook_payload,
                    headers={
                        "Content-Type": "application/json",
                        "User-Agent": "Cuenteria-Orchestrator/1.0"
                    },
                    timeout=self.timeout
                )
                
                # Verificar respuesta
                if response.status_code in [200, 201, 202, 204]:
                    logger.info(f"Webhook enviado exitosamente: {response.status_code}")
                    return True
                else:
                    logger.warning(f"Webhook respondió con código: {response.status_code}")
                    logger.debug(f"Respuesta: {response.text[:500]}")
                    
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout en webhook intento {attempt}")
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Error enviando webhook: {e}")
                
            except Exception as e:
                logger.error(f"Error inesperado en webhook: {e}")
            
            # Esperar antes de reintentar
            if attempt < self.max_attempts:
                time.sleep(self.retry_delay)
        
        logger.error(f"Fallo el envío de webhook después de {self.max_attempts} intentos")
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

def get_webhook_client() -> WebhookClient:
    """
    Obtiene una instancia singleton del cliente webhook
    
    Returns:
        Instancia de WebhookClient
    """
    global _client_instance
    if _client_instance is None:
        _client_instance = WebhookClient()
    return _client_instance