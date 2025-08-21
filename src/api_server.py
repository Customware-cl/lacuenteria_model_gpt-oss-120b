"""
Servidor API REST para recibir solicitudes desde lacuenteria.cl
"""
import json
import logging
import threading
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS

from config import (
    API_CONFIG,
    get_story_path,
    get_artifact_path,
    validate_config
)
from orchestrator import StoryOrchestrator
from webhook_client import get_webhook_client
from llm_client import get_llm_client

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Crear aplicación Flask
app = Flask(__name__)
CORS(app, origins=API_CONFIG["cors_origins"])

# Cola de procesamiento (simple, sin Redis/Celery por ahora)
processing_queue = {}
processing_lock = threading.Lock()


def process_story_async(story_id: str, brief: dict, webhook_url: str):
    """
    Procesa una historia de forma asíncrona
    
    Args:
        story_id: ID de la historia
        brief: Brief de la historia
        webhook_url: URL para notificaciones
    """
    try:
        logger.info(f"Iniciando procesamiento asíncrono de historia: {story_id}")
        
        # Crear orquestador
        orchestrator = StoryOrchestrator(story_id)
        
        # Procesar historia
        result = orchestrator.process_story(brief, webhook_url)
        
        # Enviar webhook con resultado
        if webhook_url:
            webhook_client = get_webhook_client()
            if result["status"] == "success":
                webhook_client.send_story_complete(webhook_url, result)
            else:
                webhook_client.send_story_error(
                    webhook_url, 
                    story_id, 
                    result.get("error", "Error desconocido")
                )
        
        # Actualizar estado en cola
        with processing_lock:
            if story_id in processing_queue:
                processing_queue[story_id] = result
        
        logger.info(f"Procesamiento completado para historia: {story_id}")
        
    except Exception as e:
        logger.error(f"Error procesando historia {story_id}: {e}")
        
        # Actualizar estado de error
        with processing_lock:
            if story_id in processing_queue:
                processing_queue[story_id] = {
                    "status": "error",
                    "error": str(e)
                }
        
        # Enviar webhook de error
        if webhook_url:
            webhook_client = get_webhook_client()
            webhook_client.send_story_error(webhook_url, story_id, str(e))


@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint de health check"""
    try:
        # Verificar conexión con LLM
        llm_client = get_llm_client()
        llm_available = llm_client.validate_connection()
        
        # Verificar configuración
        config_valid = True
        try:
            validate_config()
        except Exception as e:
            config_valid = False
            logger.error(f"Configuración inválida: {e}")
        
        return jsonify({
            "status": "healthy" if (llm_available and config_valid) else "degraded",
            "timestamp": datetime.now().isoformat(),
            "checks": {
                "llm_connection": llm_available,
                "config_valid": config_valid
            }
        }), 200 if (llm_available and config_valid) else 503
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


@app.route('/api/stories/create', methods=['POST'])
def create_story():
    """
    Endpoint para crear una nueva historia
    
    Espera un JSON con:
    - story_id: ID proporcionado por lacuenteria.cl
    - personajes: Lista de personajes
    - historia: Trama principal
    - mensaje_a_transmitir: Objetivo educativo
    - edad_objetivo: Edad target
    - webhook_url: URL para notificaciones
    """
    try:
        data = request.get_json()
        
        # Validar campos requeridos
        required_fields = ['story_id', 'personajes', 'historia', 
                         'mensaje_a_transmitir', 'edad_objetivo']
        
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({
                "status": "error",
                "error": f"Campos faltantes: {', '.join(missing_fields)}"
            }), 400
        
        story_id = data['story_id']
        webhook_url = data.get('webhook_url')
        
        # Verificar si la historia ya existe
        story_path = get_story_path(story_id)
        if story_path.exists():
            # Verificar estado
            manifest_path = get_artifact_path(story_id, "manifest.json")
            if manifest_path.exists():
                with open(manifest_path, 'r', encoding='utf-8') as f:
                    manifest = json.load(f)
                
                if manifest.get("estado") == "completo":
                    # Devolver resultado existente
                    validador_path = get_artifact_path(story_id, "12_validador.json")
                    if validador_path.exists():
                        with open(validador_path, 'r', encoding='utf-8') as f:
                            result = json.load(f)
                        
                        return jsonify({
                            "story_id": story_id,
                            "status": "already_completed",
                            "result": result
                        }), 200
                
                elif manifest.get("estado") == "en_progreso":
                    return jsonify({
                        "story_id": story_id,
                        "status": "already_processing",
                        "message": "La historia ya está siendo procesada"
                    }), 200
        
        # Preparar brief
        brief = {
            "personajes": data['personajes'],
            "historia": data['historia'],
            "mensaje_a_transmitir": data['mensaje_a_transmitir'],
            "edad_objetivo": data['edad_objetivo']
        }
        
        # Agregar a cola de procesamiento
        with processing_lock:
            processing_queue[story_id] = {
                "status": "queued",
                "queued_at": datetime.now().isoformat()
            }
        
        # Iniciar procesamiento asíncrono
        thread = threading.Thread(
            target=process_story_async,
            args=(story_id, brief, webhook_url)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            "story_id": story_id,
            "status": "processing",
            "estimated_time": 180,
            "accepted_at": datetime.now().isoformat()
        }), 202
        
    except Exception as e:
        logger.error(f"Error creando historia: {e}")
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


@app.route('/api/stories/<story_id>/status', methods=['GET'])
def get_story_status(story_id):
    """Obtiene el estado de una historia"""
    try:
        # Verificar en cola de procesamiento
        with processing_lock:
            if story_id in processing_queue:
                return jsonify(processing_queue[story_id]), 200
        
        # Verificar en disco
        manifest_path = get_artifact_path(story_id, "manifest.json")
        if not manifest_path.exists():
            return jsonify({
                "status": "not_found",
                "error": "Historia no encontrada"
            }), 404
        
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        
        return jsonify({
            "story_id": story_id,
            "status": manifest.get("estado", "unknown"),
            "current_step": manifest.get("paso_actual"),
            "qa_scores": manifest.get("qa_historial", {}),
            "created_at": manifest.get("created_at"),
            "updated_at": manifest.get("updated_at")
        }), 200
        
    except Exception as e:
        logger.error(f"Error obteniendo estado: {e}")
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


@app.route('/api/stories/<story_id>/result', methods=['GET'])
def get_story_result(story_id):
    """Obtiene el resultado final de una historia"""
    try:
        # Verificar que existe
        story_path = get_story_path(story_id)
        if not story_path.exists():
            return jsonify({
                "status": "not_found",
                "error": "Historia no encontrada"
            }), 404
        
        # Verificar estado
        manifest_path = get_artifact_path(story_id, "manifest.json")
        if manifest_path.exists():
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
            
            if manifest.get("estado") != "completo":
                return jsonify({
                    "status": "not_ready",
                    "current_state": manifest.get("estado"),
                    "message": "La historia aún no está completa"
                }), 202
        
        # Obtener resultado del validador
        validador_path = get_artifact_path(story_id, "12_validador.json")
        if not validador_path.exists():
            return jsonify({
                "status": "error",
                "error": "Resultado no encontrado"
            }), 404
        
        with open(validador_path, 'r', encoding='utf-8') as f:
            result = json.load(f)
        
        # Calcular QA scores
        qa_scores = {}
        if manifest_path.exists():
            qa_historial = manifest.get("qa_historial", {})
            if qa_historial:
                all_scores = []
                for agent_scores in qa_historial.values():
                    if isinstance(agent_scores, dict):
                        for metric, score in agent_scores.items():
                            if metric != "promedio" and isinstance(score, (int, float)):
                                all_scores.append(score)
                
                if all_scores:
                    qa_scores = {
                        "overall": round(sum(all_scores) / len(all_scores), 2),
                        "by_agent": qa_historial
                    }
        
        # Obtener evaluación crítica si existe
        evaluacion_critica = None
        critico_path = get_artifact_path(story_id, "13_critico.json")
        if critico_path.exists():
            try:
                with open(critico_path, 'r', encoding='utf-8') as f:
                    critico_data = json.load(f)
                evaluacion_critica = critico_data.get("evaluacion_critica", None)
            except Exception as e:
                logger.warning(f"No se pudo cargar evaluación crítica: {e}")
        
        response = {
            "story_id": story_id,
            "status": "completed",
            "result": result,
            "qa_scores": qa_scores,
            "metadata": {
                "created_at": manifest.get("created_at"),
                "completed_at": manifest.get("updated_at"),
                "retries": manifest.get("reintentos", {}),
                "warnings": manifest.get("devoluciones", [])
            }
        }
        
        # Incluir evaluación crítica si existe
        if evaluacion_critica:
            response["evaluacion_critica"] = evaluacion_critica
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error obteniendo resultado: {e}")
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


@app.route('/api/stories/<story_id>/logs', methods=['GET'])
def get_story_logs(story_id):
    """Obtiene los logs de procesamiento de una historia"""
    try:
        logs_dir = get_story_path(story_id) / "logs"
        if not logs_dir.exists():
            return jsonify({
                "status": "not_found",
                "error": "Logs no encontrados"
            }), 404
        
        all_logs = {}
        for log_file in logs_dir.glob("*.log"):
            agent_name = log_file.stem
            with open(log_file, 'r', encoding='utf-8') as f:
                all_logs[agent_name] = json.load(f)
        
        return jsonify({
            "story_id": story_id,
            "logs": all_logs
        }), 200
        
    except Exception as e:
        logger.error(f"Error obteniendo logs: {e}")
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


@app.route('/api/stories/<story_id>/evaluate', methods=['POST'])
def evaluate_story(story_id):
    """
    Ejecuta el agente crítico sobre una historia completada
    
    Returns:
        JSON estructurado en cascada con la evaluación crítica
    """
    try:
        # Verificar que la historia existe
        story_path = get_story_path(story_id)
        if not story_path.exists():
            return jsonify({
                "status": "error",
                "message": "Historia no encontrada"
            }), 404
        
        # Verificar que existe el archivo validador
        validador_path = get_artifact_path(story_id, "12_validador.json")
        if not validador_path.exists():
            return jsonify({
                "status": "error",
                "message": "Historia no completada. Falta archivo validador."
            }), 400
        
        # Ejecutar evaluación crítica
        from agent_runner import AgentRunner
        runner = AgentRunner(story_id)
        
        logger.info(f"Ejecutando evaluación crítica para historia: {story_id}")
        result = runner.run_agent("critico")
        
        if result["status"] == "success":
            # Leer el resultado del crítico (puede estar como 13_critico.json o 99_critico.json)
            critico_path = get_artifact_path(story_id, "13_critico.json")
            if not critico_path.exists():
                # Intentar con el nombre alternativo
                critico_path = get_artifact_path(story_id, "99_critico.json")
            
            if critico_path.exists():
                with open(critico_path, 'r', encoding='utf-8') as f:
                    evaluacion = json.load(f)
                
                # Intentar consolidar métricas del pipeline
                from metrics_consolidator import consolidate_agent_metrics
                metricas = consolidate_agent_metrics(story_id)
                
                # Construir respuesta base
                response = {
                    "status": "success",
                    "story_id": story_id,
                    "evaluacion_critica": evaluacion.get("evaluacion_critica", {}),
                    "timestamp": datetime.now().isoformat()
                }
                
                # Agregar métricas si están disponibles
                if metricas:
                    response["metricas_pipeline"] = metricas
                    response["metricas_disponibles"] = True
                    logger.info(f"Métricas consolidadas exitosamente para {story_id}")
                else:
                    response["metricas_disponibles"] = False
                    response["metricas_nota"] = "Métricas no disponibles para esta ejecución"
                    logger.info(f"No se pudieron consolidar métricas para {story_id}")
                
                # Retornar la evaluación crítica estructurada con métricas opcionales
                return jsonify(response)
            else:
                return jsonify({
                    "status": "error",
                    "message": "No se pudo leer el resultado de la evaluación"
                }), 500
        else:
            # Si falló pero hay QA scores, incluirlos
            response = {
                "status": "partial",
                "story_id": story_id,
                "message": "Evaluación con observaciones"
            }
            
            if "qa_scores" in result:
                response["qa_scores"] = result["qa_scores"]
            
            if "qa_issues" in result:
                response["qa_issues"] = result["qa_issues"]
            
            return jsonify(response), 206  # Partial Content
    
    except Exception as e:
        logger.error(f"Error ejecutando evaluación crítica: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route('/api/stories/<story_id>/retry', methods=['POST'])
def retry_story(story_id):
    """Reintenta el procesamiento de una historia desde donde falló"""
    try:
        # Verificar que existe
        story_path = get_story_path(story_id)
        if not story_path.exists():
            return jsonify({
                "status": "not_found",
                "error": "Historia no encontrada"
            }), 404
        
        # Crear orquestador y reanudar
        orchestrator = StoryOrchestrator(story_id)
        
        # Reanudar en thread separado
        thread = threading.Thread(
            target=lambda: orchestrator.resume_story()
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            "story_id": story_id,
            "status": "resuming",
            "message": "Procesamiento reanudado"
        }), 202
        
    except Exception as e:
        logger.error(f"Error reintentando historia: {e}")
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


@app.errorhandler(404)
def not_found(error):
    """Manejador de errores 404"""
    return jsonify({
        "status": "not_found",
        "error": "Endpoint no encontrado"
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Manejador de errores 500"""
    return jsonify({
        "status": "error",
        "error": "Error interno del servidor"
    }), 500


def main():
    """Función principal para iniciar el servidor"""
    try:
        # Validar configuración
        validate_config()
        
        # Verificar conexión con LLM
        llm_client = get_llm_client()
        if not llm_client.validate_connection():
            logger.error("No se pudo conectar al modelo LLM")
            logger.warning("El servidor iniciará pero las historias fallarán")
        
        # Iniciar servidor
        logger.info(f"Iniciando servidor en {API_CONFIG['host']}:{API_CONFIG['port']}")
        app.run(
            host=API_CONFIG["host"],
            port=API_CONFIG["port"],
            debug=API_CONFIG["debug"]
        )
        
    except Exception as e:
        logger.error(f"Error iniciando servidor: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())