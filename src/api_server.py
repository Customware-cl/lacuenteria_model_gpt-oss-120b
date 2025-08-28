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
    get_agent_prompt_path,
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


def process_story_async(story_id: str, brief: dict, webhook_url: str, mode_verificador_qa: bool = True, pipeline_version: str = 'v1'):
    """
    Procesa una historia de forma asíncrona
    
    Args:
        story_id: ID de la historia
        brief: Brief de la historia
        webhook_url: URL para notificaciones
        mode_verificador_qa: Si True usa verificador QA estricto, si False usa autoevaluación
        pipeline_version: Versión del pipeline a usar (v1, v2, etc.)
    """
    try:
        logger.info(f"Iniciando procesamiento asíncrono de historia: {story_id} (verificador_qa={mode_verificador_qa}, version={pipeline_version})")
        
        # Crear orquestador con modo y versión configurables
        from config import load_version_config
        version_config = load_version_config(pipeline_version)
        
        # Si la versión especifica config especiales, aplicarlas
        if version_config:
            # Actualizar modo QA si la versión lo especifica
            if 'mode_verificador_qa' in version_config:
                mode_verificador_qa = version_config['mode_verificador_qa']
        
        orchestrator = StoryOrchestrator(story_id, mode_verificador_qa=mode_verificador_qa, pipeline_version=pipeline_version)
        
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
    - mode_verificador_qa: (opcional) Si True usa verificador QA estricto, si False usa autoevaluación. Default: True
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
        mode_verificador_qa = data.get('mode_verificador_qa', True)  # Default: True (estricto)
        
        # Detectar versión del pipeline (default v1 para compatibilidad)
        pipeline_version = data.get('pipeline_version', 'v1')
        if pipeline_version not in ['v1', 'v2']:
            pipeline_version = 'v1'  # Fallback seguro
        
        logger.info(f"Creando historia {story_id} con pipeline {pipeline_version}")
        
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
                    validador_path = get_artifact_path(story_id, "validador.json")
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
        
        # Log del modo de verificación
        logger.info(f"Creando historia {story_id} con mode_verificador_qa={mode_verificador_qa}")
        
        # Agregar a cola de procesamiento
        with processing_lock:
            processing_queue[story_id] = {
                "status": "queued",
                "queued_at": datetime.now().isoformat(),
                "mode_verificador_qa": mode_verificador_qa
            }
        
        # Iniciar procesamiento asíncrono con versión
        thread = threading.Thread(
            target=process_story_async,
            args=(story_id, brief, webhook_url, mode_verificador_qa, pipeline_version)
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
        validador_path = get_artifact_path(story_id, "validador.json")
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


def validate_external_story(story_data):
    """
    Valida la estructura de una historia externa
    Usa la misma estructura que genera el pipeline de 12 agentes
    
    Returns:
        tuple: (is_valid, error_message)
    """
    try:
        # 1. Verificar campos requeridos (según formato del validador)
        required_fields = ["titulo", "paginas", "portada", "loader"]
        for field in required_fields:
            if field not in story_data:
                return False, f"Campo requerido faltante: {field}"
        
        # 2. Verificar que paginas es un diccionario
        if not isinstance(story_data["paginas"], dict):
            return False, "El campo 'paginas' debe ser un diccionario"
        
        # 3. Verificar que hay al menos 1 página
        num_pages = len(story_data["paginas"])
        if num_pages == 0:
            return False, "La historia debe tener al menos 1 página"
        
        # 4. Verificar estructura de cada página (flexible en numeración)
        for page_key, page in story_data["paginas"].items():
            if not isinstance(page, dict):
                return False, f"La página '{page_key}' debe ser un diccionario"
            
            if "texto" not in page:
                return False, f"La página '{page_key}' no tiene campo 'texto'"
            
            if "prompt" not in page:
                return False, f"La página '{page_key}' no tiene campo 'prompt'"
        
        # 5. Verificar tamaño máximo (1MB)
        json_size = len(json.dumps(story_data))
        if json_size > 1_000_000:
            return False, f"Historia demasiado grande: {json_size/1_000_000:.2f}MB (máximo 1MB)"
        
        # 6. Verificar portada
        if not isinstance(story_data["portada"], dict):
            return False, "El campo 'portada' debe ser un diccionario"
        
        if "prompt" not in story_data["portada"]:
            return False, "La portada debe tener campo 'prompt'"
        
        # 7. Verificar loader
        if not isinstance(story_data["loader"], list):
            return False, "El campo 'loader' debe ser una lista"
        
        if len(story_data["loader"]) == 0:
            return False, "Debe haber al menos un mensaje de carga"
        
        return True, None
        
    except Exception as e:
        return False, f"Error validando estructura: {str(e)}"


def run_critico_on_data(story_data, story_id="external"):
    """
    Ejecuta el agente crítico sobre datos de historia sin depender de archivos locales
    
    Args:
        story_data: Diccionario con la historia completa
        story_id: ID de la historia (para logging)
    
    Returns:
        Diccionario con la evaluación crítica
    """
    try:
        from llm_client import LLMClient
        
        # Cargar prompt del crítico
        critico_prompt_path = get_agent_prompt_path("critico")
        with open(critico_prompt_path, 'r', encoding='utf-8') as f:
            critico_config = json.load(f)
        
        # Preparar el prompt con los datos de la historia
        system_prompt = critico_config["content"]
        user_prompt = f"""Evalúa el siguiente cuento infantil:

{json.dumps(story_data, ensure_ascii=False, indent=2)}

Recuerda responder ÚNICAMENTE con el JSON de evaluación crítica especificado."""
        
        # Ejecutar LLM
        llm_client = LLMClient()
        logger.info(f"Ejecutando crítico para historia externa: {story_id}")
        
        evaluacion = llm_client.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.4,  # Baja para evaluación consistente
            max_tokens=4000   # Suficiente para evaluación completa
        )
        
        return evaluacion
        
    except Exception as e:
        logger.error(f"Error ejecutando crítico en datos externos: {e}")
        raise


@app.route('/api/stories/<story_id>/evaluate', methods=['POST'])
def evaluate_story(story_id):
    """
    Ejecuta el agente crítico sobre una historia (interna o externa)
    
    Soporta dos modos:
    1. Historia interna: Busca en runs/{story_id}/
    2. Historia externa: Recibe el JSON completo en el body del request
    
    Returns:
        JSON con evaluación crítica y métricas (si aplican)
    """
    try:
        story_source = None
        story_data = None
        evaluacion = None
        
        # Primero intentar buscar historia local
        story_path = get_story_path(story_id)
        validador_path = get_artifact_path(story_id, "validador.json")
        
        if story_path.exists() and validador_path.exists():
            # HISTORIA INTERNA
            logger.info(f"Historia interna encontrada: {story_id}")
            story_source = "internal"
            
            # Leer datos de la historia
            with open(validador_path, 'r', encoding='utf-8') as f:
                story_data = json.load(f)
            
            # Ejecutar evaluación crítica usando el runner existente
            from agent_runner import AgentRunner
            runner = AgentRunner(story_id)
            
            logger.info(f"Ejecutando evaluación crítica para historia interna: {story_id}")
            result = runner.run_agent("critico")
            
            if result["status"] == "success":
                # Leer el resultado del crítico
                critico_path = get_artifact_path(story_id, "critico.json")
                if not critico_path.exists():
                    # Intentar con nombres alternativos
                    for alt_name in ["13_critico.json", "99_critico.json"]:
                        alt_path = get_artifact_path(story_id, alt_name)
                        if alt_path.exists():
                            critico_path = alt_path
                            break
                
                if critico_path.exists():
                    with open(critico_path, 'r', encoding='utf-8') as f:
                        evaluacion = json.load(f)
                else:
                    return jsonify({
                        "status": "error",
                        "message": "No se pudo leer el resultado de la evaluación"
                    }), 500
            else:
                # Si falló, devolver información parcial
                return jsonify({
                    "status": "error",
                    "story_id": story_id,
                    "source": story_source,
                    "message": "Error ejecutando crítico",
                    "details": result.get("error", "Unknown error")
                }), 500
                
        elif request.json:
            # HISTORIA EXTERNA
            logger.info(f"Procesando historia externa: {story_id}")
            story_source = "external"
            story_data = request.json
            
            # Validar estructura de historia externa
            is_valid, error_msg = validate_external_story(story_data)
            if not is_valid:
                return jsonify({
                    "status": "error",
                    "message": f"Historia externa inválida: {error_msg}"
                }), 400
            
            # Ejecutar crítico directamente sobre los datos
            logger.info(f"Ejecutando crítico para historia externa: {story_id}")
            evaluacion = run_critico_on_data(story_data, story_id)
            
        else:
            # No se encontró historia local ni se proporcionó en el body
            return jsonify({
                "status": "error",
                "message": "Historia no encontrada. Proporcione datos en el body para historias externas."
            }), 404
        
        # Construir respuesta base
        response = {
            "status": "success",
            "story_id": story_id,
            "source": story_source,
            "evaluacion_critica": evaluacion.get("evaluacion_critica", evaluacion) if evaluacion else {},
            "timestamp": datetime.now().isoformat()
        }
        
        # Agregar métricas solo para historias internas
        if story_source == "internal":
            try:
                from metrics_consolidator import consolidate_agent_metrics
                metricas = consolidate_agent_metrics(story_id)
                
                if metricas:
                    response["metricas_pipeline"] = metricas
                    response["metricas_disponibles"] = True
                    logger.info(f"Métricas consolidadas para historia interna: {story_id}")
                else:
                    response["metricas_disponibles"] = False
                    response["metricas_nota"] = "Métricas no disponibles para esta ejecución"
            except Exception as e:
                logger.warning(f"No se pudieron consolidar métricas: {e}")
                response["metricas_disponibles"] = False
        
        # Nota informativa para historias externas
        if story_source == "external":
            response["nota"] = "Historia externa evaluada. Las métricas del pipeline no aplican."
        
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Error ejecutando evaluación crítica: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route('/api/v1/stories/create', methods=['POST'])
def create_story_v1():
    """
    Endpoint explícito para crear historias con pipeline v1
    Usa la configuración actual de producción sin cambios
    """
    try:
        data = request.get_json()
        # Inyectar versión
        data['pipeline_version'] = 'v1'
        
        # Procesar directamente
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
        mode_verificador_qa = data.get('mode_verificador_qa', True)
        
        logger.info(f"Creando historia {story_id} con pipeline v1 (explícito)")
        
        # Verificar si existe
        story_path = get_story_path(story_id)
        if story_path.exists():
            manifest_path = get_artifact_path(story_id, "manifest.json")
            if manifest_path.exists():
                with open(manifest_path, 'r', encoding='utf-8') as f:
                    manifest = json.load(f)
                
                if manifest.get("estado") == "completo":
                    validador_path = get_artifact_path(story_id, "validador.json")
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
        
        # Agregar a cola
        with processing_lock:
            processing_queue[story_id] = {
                "status": "queued",
                "queued_at": datetime.now().isoformat(),
                "mode_verificador_qa": mode_verificador_qa,
                "pipeline_version": "v1"
            }
        
        # Iniciar procesamiento asíncrono
        thread = threading.Thread(
            target=process_story_async,
            args=(story_id, brief, webhook_url, mode_verificador_qa, "v1")
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            "story_id": story_id,
            "status": "processing",
            "pipeline_version": "v1",
            "estimated_time": 180,
            "accepted_at": datetime.now().isoformat()
        }), 202
        
    except Exception as e:
        logger.error(f"Error creando historia v1: {e}")
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


@app.route('/api/v2/stories/create', methods=['POST'])
def create_story_v2():
    """
    Endpoint explícito para crear historias con pipeline v2
    Usa optimizaciones y nueva configuración
    """
    try:
        data = request.get_json()
        # Inyectar versión
        data['pipeline_version'] = 'v2'
        
        # Procesar directamente
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
        mode_verificador_qa = data.get('mode_verificador_qa', True)
        
        logger.info(f"Creando historia {story_id} con pipeline v2 (explícito)")
        
        # Verificar si existe
        story_path = get_story_path(story_id)
        if story_path.exists():
            manifest_path = get_artifact_path(story_id, "manifest.json")
            if manifest_path.exists():
                with open(manifest_path, 'r', encoding='utf-8') as f:
                    manifest = json.load(f)
                
                if manifest.get("estado") == "completo":
                    validador_path = get_artifact_path(story_id, "validador.json")
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
        
        # Agregar a cola
        with processing_lock:
            processing_queue[story_id] = {
                "status": "queued",
                "queued_at": datetime.now().isoformat(),
                "mode_verificador_qa": mode_verificador_qa,
                "pipeline_version": "v2"
            }
        
        # Iniciar procesamiento asíncrono
        thread = threading.Thread(
            target=process_story_async,
            args=(story_id, brief, webhook_url, mode_verificador_qa, "v2")
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            "story_id": story_id,
            "status": "processing",
            "pipeline_version": "v2",
            "estimated_time": 120,  # Menor tiempo estimado con optimizaciones
            "accepted_at": datetime.now().isoformat()
        }), 202
        
    except Exception as e:
        logger.error(f"Error creando historia v2: {e}")
        return jsonify({
            "status": "error",
            "error": str(e)
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
        
        # Detectar versión desde el manifest si existe
        pipeline_version = 'v1'  # Default
        manifest_path = get_artifact_path(story_id, "manifest.json")
        if manifest_path.exists():
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
                pipeline_version = manifest.get('pipeline_version', 'v1')
        
        # Crear orquestador con la versión correcta
        orchestrator = StoryOrchestrator(story_id, pipeline_version=pipeline_version)
        
        # Reanudar en thread separado
        thread = threading.Thread(
            target=lambda: orchestrator.resume_story()
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            "story_id": story_id,
            "status": "resuming",
            "message": "Procesamiento reanudado",
            "pipeline_version": pipeline_version
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