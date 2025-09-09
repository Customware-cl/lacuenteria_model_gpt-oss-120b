"""
Orquestador principal del pipeline de Cuentería
"""
import json
import logging
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
import uuid
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

from config import (
    AGENT_PIPELINE,
    get_story_path,
    get_artifact_path,
    PROCESSING_CONFIG,
    validate_config
)
from agent_runner import AgentRunner
from llm_client import get_llm_client

logger = logging.getLogger(__name__)


class StoryOrchestrator:
    """Orquesta el pipeline completo de generación de cuentos"""
    
    def __init__(self, story_id: Optional[str] = None, mode_verificador_qa: bool = True, pipeline_version: str = 'v1', use_timestamp: bool = True, prompt_metrics_id: Optional[str] = None, pipeline_request_id: Optional[str] = None):
        """
        Inicializa el orquestador
        
        Args:
            story_id: ID de la historia (si None, se genera uno)
            mode_verificador_qa: Si True usa verificador_qa, si False usa autoevaluación
            pipeline_version: Versión del pipeline a usar (v1, v2, etc.)
            use_timestamp: Si True, añade timestamp al nombre de la carpeta
            prompt_metrics_id: ID de métricas del prompt (solo para manifest y webhook)
        """
        from config import generate_timestamped_story_folder
        
        self.original_story_id = story_id or self._generate_story_id()
        
        # Si use_timestamp es True, añadir timestamp al nombre de la carpeta
        if use_timestamp:
            self.story_id = generate_timestamped_story_folder(self.original_story_id)
        else:
            self.story_id = self.original_story_id
            
        self.story_path = get_story_path(self.story_id)
        self.mode_verificador_qa = mode_verificador_qa
        self.pipeline_version = pipeline_version
        self.prompt_metrics_id = prompt_metrics_id
        self.pipeline_request_id = pipeline_request_id
        self.agent_runner = AgentRunner(self.story_id, mode_verificador_qa=mode_verificador_qa, version=pipeline_version)
        self.manifest = self._init_manifest()
        
        logger.info(f"Orchestrator inicializado - story_id: {self.story_id}, original_id: {self.original_story_id}, mode_verificador_qa: {mode_verificador_qa}, version: {pipeline_version}")
        
    def _generate_story_id(self) -> str:
        """Genera un ID único para la historia"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        return f"{timestamp}_{unique_id}"
    
    def _init_manifest(self) -> Dict[str, Any]:
        """Inicializa o carga el manifest de la historia"""
        manifest_path = get_artifact_path(self.story_id, "manifest.json")
        
        if manifest_path.exists():
            with open(manifest_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            from config import LLM_CONFIG
            return {
                "story_id": self.story_id,
                "original_story_id": self.original_story_id,
                "source": "local",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "estado": "iniciado",
                "paso_actual": None,
                "qa_historial": {},
                "devoluciones": [],
                "reintentos": {},
                "timestamps": {},
                "webhook_url": None,
                "webhook_attempts": 0,
                "pipeline_version": getattr(self, 'pipeline_version', 'v1'),
                "configuracion_modelo": {
                    "modelo": LLM_CONFIG["model"],
                    "endpoint": LLM_CONFIG.get("api_url", "http://69.19.136.204:8000/v1/chat/completions"),
                    "timeout": self.agent_runner.llm_client.timeout,
                    "default_temperature": LLM_CONFIG["temperature"],
                    "default_max_tokens": LLM_CONFIG["max_tokens"]
                }
            }
    
    def process_story(self, brief: Dict[str, Any], webhook_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Procesa una historia completa a través del pipeline
        
        Args:
            brief: Diccionario con personajes, historia, mensaje_a_transmitir, edad_objetivo
            webhook_url: URL opcional para notificaciones
            
        Returns:
            Diccionario con el resultado del procesamiento
        """
        logger.info(f"Iniciando procesamiento de historia: {self.story_id}")
        
        try:
            # Validar configuración
            validate_config()
            
            # Crear directorio de la historia
            self.story_path.mkdir(parents=True, exist_ok=True)
            logs_dir = self.story_path / "logs"
            logs_dir.mkdir(exist_ok=True)
            
            # Guardar brief
            brief_path = get_artifact_path(self.story_id, "brief.json")
            with open(brief_path, 'w', encoding='utf-8') as f:
                json.dump(brief, f, ensure_ascii=False, indent=2)
            
            # Actualizar manifest
            self.manifest["webhook_url"] = webhook_url
            # Guardar prompt_metrics_id si fue proporcionado al orchestrator
            if self.prompt_metrics_id:
                self.manifest["prompt_metrics_id"] = self.prompt_metrics_id
            # Guardar pipeline_request_id si fue proporcionado
            if self.pipeline_request_id:
                self.manifest["pipeline_request_id"] = self.pipeline_request_id
            self.manifest["estado"] = "en_progreso"
            self._save_manifest()
            
            # Obtener pipeline de la versión configurada
            pipeline = self.agent_runner.version_config.get('pipeline', AGENT_PIPELINE)
            
            # Obtener toggles de agentes (por defecto todos habilitados)
            agent_toggles = self.agent_runner.version_config.get('agent_toggles', {})
            
            # Ejecutar pipeline
            for agent_name in pipeline:
                # Verificar si el agente está habilitado
                if not agent_toggles.get(agent_name, True):
                    logger.info(f"Saltando agente deshabilitado: {agent_name}")
                    self._handle_skipped_agent(agent_name)
                    continue
                
                logger.info(f"Ejecutando agente: {agent_name}")
                
                # Actualizar manifest
                self.manifest["paso_actual"] = agent_name
                self.manifest["updated_at"] = datetime.now().isoformat()
                self._save_manifest()
                
                # Ejecutar agente
                start_time = datetime.now()
                result = self.agent_runner.run_agent(agent_name)
                execution_time = (datetime.now() - start_time).total_seconds()
                
                # Registrar en manifest
                self.manifest["timestamps"][agent_name] = {
                    "start": start_time.isoformat(),
                    "end": datetime.now().isoformat(),
                    "duration": execution_time
                }
                
                # Verificar resultado
                if result["status"] == "error":
                    logger.error(f"Error en agente {agent_name}: {result.get('error')}")
                    self.manifest["estado"] = "error"
                    self.manifest["error"] = {
                        "agent": agent_name,
                        "message": result.get("error"),
                        "timestamp": datetime.now().isoformat()
                    }
                    self._save_manifest()
                    return self._build_error_response(agent_name, result.get("error"))
                
                elif result["status"] == "qa_failed":
                    logger.warning(f"QA falló para {agent_name} después de reintentos")
                    
                    # Registrar QA scores
                    if "qa_scores" in result:
                        self.manifest["qa_historial"][agent_name] = result["qa_scores"]
                    
                    # Registrar devolución
                    self.manifest["devoluciones"].append({
                        "paso": agent_name,
                        "motivo": "QA bajo umbral después de reintentos",
                        "qa_scores": result.get("qa_scores"),
                        "issues": result.get("qa_issues"),
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    # Registrar reintentos
                    if agent_name not in self.manifest["reintentos"]:
                        self.manifest["reintentos"][agent_name] = 0
                    self.manifest["reintentos"][agent_name] = result.get("retry_count", 0)
                    
                    self.manifest["estado"] = "qa_failed"
                    self._save_manifest()
                    
                    # Continuar con advertencia (o detener según configuración)
                    logger.warning(f"Continuando pipeline a pesar de QA bajo para {agent_name}")
                
                else:  # success
                    logger.info(f"Agente {agent_name} completado exitosamente")
                    
                    # Registrar QA scores
                    if "qa_scores" in result:
                        self.manifest["qa_historial"][agent_name] = result["qa_scores"]
                    
                    # Registrar reintentos si hubo
                    if result.get("retry_count", 0) > 0:
                        self.manifest["reintentos"][agent_name] = result["retry_count"]
                
                self._save_manifest()
            
            # Pipeline completado
            logger.info("Pipeline completado exitosamente")
            self.manifest["estado"] = "completo"
            self.manifest["updated_at"] = datetime.now().isoformat()
            self._save_manifest()
            
            # Obtener resultado final
            final_result = self._get_final_result()
            
            result_dict = {
                "status": "success",
                "story_id": self.original_story_id,  # Usar ID original para compatibilidad con BD
                "result": final_result,
                "qa_scores": self._calculate_overall_qa(),
                "processing_time": self._calculate_total_time(),
                "metadata": {
                    "retries": self.manifest.get("reintentos", {}),
                    "warnings": self.manifest.get("devoluciones", [])
                }
            }
            
            # Incluir prompt_metrics_id si existe
            if "prompt_metrics_id" in self.manifest:
                result_dict["prompt_metrics_id"] = self.manifest["prompt_metrics_id"]
            
            # Incluir pipeline_request_id si existe
            if "pipeline_request_id" in self.manifest:
                result_dict["pipeline_request_id"] = self.manifest["pipeline_request_id"]
            
            return result_dict
            
        except Exception as e:
            logger.error(f"Error fatal en pipeline: {e}")
            self.manifest["estado"] = "error"
            self.manifest["error"] = {
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }
            self._save_manifest()
            return self._build_error_response("orchestrator", str(e))
    
    def resume_story(self) -> Dict[str, Any]:
        """
        Reanuda el procesamiento de una historia interrumpida
        
        Returns:
            Diccionario con el resultado
        """
        logger.info(f"Reanudando historia: {self.story_id}")
        
        # Cargar brief
        brief_path = get_artifact_path(self.story_id, "brief.json")
        if not brief_path.exists():
            return self._build_error_response("resume", "Brief no encontrado")
        
        with open(brief_path, 'r', encoding='utf-8') as f:
            brief = json.load(f)
        
        # Determinar desde dónde continuar
        last_completed = self._find_last_completed_agent()
        
        if last_completed is None:
            # Empezar desde el principio
            return self.process_story(brief, self.manifest.get("webhook_url"))
        
        # Obtener pipeline de la versión configurada
        pipeline = self.agent_runner.version_config.get('pipeline', AGENT_PIPELINE)
        
        # Encontrar siguiente agente
        try:
            last_index = pipeline.index(last_completed)
            remaining_agents = pipeline[last_index + 1:]
        except ValueError:
            return self._build_error_response("resume", f"Agente desconocido: {last_completed}")
        
        if not remaining_agents:
            logger.info("Historia ya completada")
            return {
                "status": "already_completed",
                "story_id": self.original_story_id,  # Usar ID original para compatibilidad con BD
                "result": self._get_final_result()
            }
        
        # Continuar con agentes restantes
        logger.info(f"Continuando desde: {remaining_agents[0]}")
        
        for agent_name in remaining_agents:
            logger.info(f"Ejecutando agente: {agent_name}")
            
            self.manifest["paso_actual"] = agent_name
            self.manifest["updated_at"] = datetime.now().isoformat()
            self._save_manifest()
            
            result = self.agent_runner.run_agent(agent_name)
            
            if result["status"] == "error":
                logger.error(f"Error en agente {agent_name}: {result.get('error')}")
                self.manifest["estado"] = "error"
                self._save_manifest()
                return self._build_error_response(agent_name, result.get("error"))
            
            if "qa_scores" in result:
                self.manifest["qa_historial"][agent_name] = result["qa_scores"]
            
            self._save_manifest()
        
        # Completado
        self.manifest["estado"] = "completo"
        self._save_manifest()
        
        result_dict = {
            "status": "success",
            "story_id": self.original_story_id,  # Usar ID original para compatibilidad con BD
            "result": self._get_final_result(),
            "resumed": True
        }
        
        # Incluir prompt_metrics_id si existe
        if "prompt_metrics_id" in self.manifest:
            result_dict["prompt_metrics_id"] = self.manifest["prompt_metrics_id"]
        
        return result_dict
    
    def get_status(self) -> Dict[str, Any]:
        """
        Obtiene el estado actual de la historia
        
        Returns:
            Diccionario con el estado
        """
        return {
            "story_id": self.story_id,
            "estado": self.manifest.get("estado"),
            "paso_actual": self.manifest.get("paso_actual"),
            "qa_historial": self.manifest.get("qa_historial"),
            "reintentos": self.manifest.get("reintentos"),
            "created_at": self.manifest.get("created_at"),
            "updated_at": self.manifest.get("updated_at")
        }
    
    def _find_last_completed_agent(self) -> Optional[str]:
        """Encuentra el último agente completado exitosamente"""
        # Obtener pipeline de la versión configurada
        pipeline = self.agent_runner.version_config.get('pipeline', AGENT_PIPELINE)
        
        for agent in reversed(pipeline):
            output_file = self._get_agent_output_file(agent)
            if get_artifact_path(self.story_id, output_file).exists():
                return agent
        return None
    
    def _get_agent_output_file(self, agent_name: str) -> str:
        """Obtiene el nombre del archivo de salida de un agente"""
        # Usar solo el nombre del agente sin numeración para evitar problemas de dependencias
        return f"{agent_name}.json"
    
    def _handle_skipped_agent(self, agent_name: str):
        """
        Maneja un agente que fue saltado, creando los archivos necesarios
        para que los siguientes agentes encuentren sus dependencias.
        """
        import shutil
        
        # Mapeo de qué archivo usar cuando se salta un agente
        dependency_mapping = {
            "04_editor_claridad": "03_cuentacuentos",
            "05_ritmo_rima": "04_editor_claridad",  # Si editor está saltado, usa cuentacuentos
            "06_continuidad": "05_ritmo_rima",
            "07_diseno_escena": "05_ritmo_rima",
            "08_direccion_arte": "07_diseno_escena",
            "09_sensibilidad": "05_ritmo_rima",
            "10_portadista": "05_ritmo_rima",
            "11_loader": "10_portadista",
            "12_validador": "05_ritmo_rima"
        }
        
        # Si el agente saltado tiene un mapeo, copiar el archivo anterior
        if agent_name in dependency_mapping:
            source_agent = dependency_mapping[agent_name]
            
            # Si el agente fuente también fue saltado, buscar recursivamente
            agent_toggles = self.agent_runner.version_config.get('agent_toggles', {})
            while source_agent in dependency_mapping and not agent_toggles.get(source_agent, True):
                source_agent = dependency_mapping[source_agent]
            
            # Remover números del inicio del nombre del agente para el archivo
            source_file_name = source_agent.lstrip('0123456789_')
            target_file_name = agent_name.lstrip('0123456789_')
            
            source_file = get_artifact_path(self.story_id, f"{source_file_name}.json")
            target_file = get_artifact_path(self.story_id, f"{target_file_name}.json")
            
            if source_file.exists():
                logger.info(f"Copiando {source_file.name} como {target_file.name} para mantener dependencias")
                shutil.copy2(source_file, target_file)
                
                # Registrar en manifest que el agente fue saltado
                self.manifest["timestamps"][agent_name] = {
                    "skipped": True,
                    "source_file": source_agent,
                    "timestamp": datetime.now().isoformat()
                }
                self._save_manifest()
            else:
                logger.warning(f"No se pudo encontrar archivo fuente {source_file} para agente saltado {agent_name}")
    
    def _get_final_result(self) -> Dict[str, Any]:
        """Obtiene el resultado final del validador"""
        validador_path = get_artifact_path(self.story_id, "validador.json")
        
        if validador_path.exists():
            with open(validador_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return {}
    
    def _calculate_overall_qa(self) -> Dict[str, float]:
        """Calcula los scores QA generales"""
        qa_historial = self.manifest.get("qa_historial", {})
        
        if not qa_historial:
            return {"overall": 0.0}
        
        all_scores = []
        for agent_scores in qa_historial.values():
            if isinstance(agent_scores, dict):
                for metric, score in agent_scores.items():
                    if metric != "promedio" and isinstance(score, (int, float)):
                        all_scores.append(score)
        
        if all_scores:
            overall = sum(all_scores) / len(all_scores)
            return {
                "overall": round(overall, 2),
                "by_agent": qa_historial
            }
        
        return {"overall": 0.0, "by_agent": qa_historial}
    
    def _calculate_total_time(self) -> float:
        """Calcula el tiempo total de procesamiento"""
        timestamps = self.manifest.get("timestamps", {})
        total_time = 0
        
        for agent_times in timestamps.values():
            if "duration" in agent_times:
                total_time += agent_times["duration"]
        
        return round(total_time, 2)
    
    def _save_manifest(self):
        """Guarda el manifest actualizado"""
        manifest_path = get_artifact_path(self.story_id, "manifest.json")
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(self.manifest, f, ensure_ascii=False, indent=2)
    
    def _build_error_response(self, agent: str, error: str) -> Dict[str, Any]:
        """Construye una respuesta de error"""
        return {
            "status": "error",
            "story_id": self.original_story_id,  # Usar ID original para compatibilidad con BD
            "agent": agent,
            "error": error,
            "manifest": self.manifest
        }


def main():
    """Función principal para ejecución CLI"""
    parser = argparse.ArgumentParser(description="Orquestador de Cuentería")
    parser.add_argument("--story-id", help="ID de la historia")
    parser.add_argument("--brief", help="Ruta al archivo brief.json")
    parser.add_argument("--resume", action="store_true", help="Reanudar historia existente")
    parser.add_argument("--validate", help="Validar historia por ID")
    parser.add_argument("--status", help="Ver estado de historia por ID")
    parser.add_argument("--log-level", default="INFO", help="Nivel de logging")
    
    args = parser.parse_args()
    
    # Configurar logging
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Validar modelo LLM disponible
    llm_client = get_llm_client()
    if not llm_client.validate_connection():
        logger.error("No se pudo conectar al modelo LLM. Verifica la configuración.")
        return 1
    
    # Ejecutar según argumentos
    if args.resume and args.story_id:
        orchestrator = StoryOrchestrator(args.story_id)
        result = orchestrator.resume_story()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
    elif args.status and args.story_id:
        orchestrator = StoryOrchestrator(args.story_id)
        status = orchestrator.get_status()
        print(json.dumps(status, ensure_ascii=False, indent=2))
        
    elif args.brief:
        # Cargar brief
        with open(args.brief, 'r', encoding='utf-8') as f:
            brief = json.load(f)
        
        orchestrator = StoryOrchestrator(args.story_id)
        result = orchestrator.process_story(brief)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
    else:
        parser.print_help()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())