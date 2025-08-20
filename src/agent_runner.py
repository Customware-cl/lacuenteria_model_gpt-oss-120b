"""
Ejecutor de agentes individuales
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from config import (
    get_agent_prompt_path,
    get_artifact_path,
    AGENT_DEPENDENCIES
)
from llm_client import get_llm_client
from quality_gates import get_quality_checker

logger = logging.getLogger(__name__)


class AgentRunner:
    """Ejecuta agentes individuales con sus dependencias"""
    
    def __init__(self, story_id: str):
        self.story_id = story_id
        self.llm_client = get_llm_client()
        self.quality_checker = get_quality_checker()
        
    def run_agent(self, agent_name: str, retry_count: int = 0) -> Dict[str, Any]:
        """
        Ejecuta un agente específico
        
        Args:
            agent_name: Nombre del agente a ejecutar
            retry_count: Número de reintentos actuales
            
        Returns:
            Diccionario con el resultado de la ejecución
        """
        logger.info(f"Ejecutando agente: {agent_name} (intento {retry_count + 1})")
        
        try:
            # 1. Cargar el prompt del sistema
            system_prompt = self._load_system_prompt(agent_name)
            
            # 2. Cargar las dependencias (artefactos previos)
            dependencies = self._load_dependencies(agent_name)
            
            # 3. Construir el prompt del usuario
            user_prompt = self._build_user_prompt(agent_name, dependencies)
            
            # 4. Obtener temperatura específica del agente
            from config import AGENT_TEMPERATURES, AGENT_MAX_TOKENS
            agent_temperature = AGENT_TEMPERATURES.get(agent_name, None)
            
            # 5. Llamar al LLM con temperatura específica
            # Usar configuración de max_tokens específica por agente si existe
            max_tokens = AGENT_MAX_TOKENS.get(agent_name, None)
            
            start_time = datetime.now()
            agent_output = self.llm_client.generate(
                system_prompt, 
                user_prompt,
                temperature=agent_temperature,
                max_tokens=max_tokens
            )
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # 5. Validar estructura de salida
            valid_structure, structure_errors = self.quality_checker.validate_output_structure(
                agent_output, agent_name
            )
            
            if not valid_structure:
                logger.error(f"Estructura inválida para {agent_name}: {structure_errors}")
                return {
                    "status": "error",
                    "agent": agent_name,
                    "error": "Estructura de salida inválida",
                    "details": structure_errors,
                    "retry_count": retry_count
                }
            
            # 6. Verificar quality gates (excepto para validador y critico que no tienen QA)
            if agent_name not in ["validador", "critico"]:
                qa_passed, qa_scores, qa_issues = self.quality_checker.check_qa_scores(
                    agent_output, agent_name
                )
                
                if not qa_passed:
                    logger.warning(f"QA no pasó para {agent_name}: {qa_issues}")
                    
                    # Generar instrucciones de mejora
                    improvement_instructions = self.quality_checker.generate_improvement_instructions(
                        agent_name, qa_scores, qa_issues, agent_output
                    )
                    
                    # Verificar si podemos reintentar
                    if self.quality_checker.should_retry(retry_count):
                        logger.info(f"Reintentando {agent_name} con mejoras")
                        
                        # Agregar las instrucciones al prompt y reintentar
                        return self._retry_with_improvements(
                            agent_name, 
                            improvement_instructions, 
                            retry_count + 1
                        )
                    else:
                        logger.error(f"Máximo de reintentos alcanzado para {agent_name}")
                        return {
                            "status": "qa_failed",
                            "agent": agent_name,
                            "output": agent_output,
                            "qa_scores": qa_scores,
                            "qa_issues": qa_issues,
                            "retry_count": retry_count,
                            "execution_time": execution_time
                        }
            else:
                qa_scores = {}
                qa_passed = True
            
            # 7. Guardar la salida
            output_file = self._get_output_filename(agent_name)
            self._save_output(output_file, agent_output)
            
            # 8. Guardar log
            self._save_log(agent_name, {
                "timestamp": datetime.now().isoformat(),
                "retry_count": retry_count,
                "qa_scores": qa_scores if agent_name != "validador" else None,
                "execution_time": execution_time,
                "temperature": agent_temperature or self.llm_client.temperature,
                "status": "success"
            })
            
            return {
                "status": "success",
                "agent": agent_name,
                "output": agent_output,
                "qa_scores": qa_scores,
                "retry_count": retry_count,
                "execution_time": execution_time
            }
            
        except Exception as e:
            logger.error(f"Error ejecutando {agent_name}: {e}")
            return {
                "status": "error",
                "agent": agent_name,
                "error": str(e),
                "retry_count": retry_count
            }
    
    def _load_system_prompt(self, agent_name: str) -> str:
        """Carga el prompt del sistema para un agente"""
        prompt_path = get_agent_prompt_path(agent_name)
        
        with open(prompt_path, 'r', encoding='utf-8') as f:
            agent_config = json.load(f)
        
        if "content" not in agent_config:
            raise ValueError(f"Archivo de agente {agent_name} no tiene campo 'content'")
        
        return agent_config["content"]
    
    def _load_dependencies(self, agent_name: str) -> Dict[str, Any]:
        """Carga las dependencias (artefactos previos) para un agente"""
        dependencies = {}
        
        if agent_name not in AGENT_DEPENDENCIES:
            logger.warning(f"No se encontraron dependencias definidas para {agent_name}")
            return dependencies
        
        for dependency_file in AGENT_DEPENDENCIES[agent_name]:
            artifact_path = get_artifact_path(self.story_id, dependency_file)
            
            if artifact_path.exists():
                with open(artifact_path, 'r', encoding='utf-8') as f:
                    dependencies[dependency_file] = json.load(f)
                logger.info(f"Cargada dependencia: {dependency_file}")
            else:
                logger.warning(f"Dependencia no encontrada: {artifact_path}")
        
        return dependencies
    
    def _build_user_prompt(self, agent_name: str, dependencies: Dict[str, Any]) -> str:
        """Construye el prompt del usuario con las dependencias"""
        prompt_parts = []
        
        # Agregar contexto de la historia
        prompt_parts.append("CONTEXTO DE LA HISTORIA:")
        prompt_parts.append("=" * 50)
        
        # Agregar cada dependencia
        for dep_name, dep_content in dependencies.items():
            prompt_parts.append(f"\n### {dep_name}:")
            prompt_parts.append(json.dumps(dep_content, ensure_ascii=False, indent=2))
            prompt_parts.append("")
        
        # Instrucciones específicas del agente
        prompt_parts.append("\nINSTRUCCIONES:")
        prompt_parts.append("=" * 50)
        prompt_parts.append(self._get_agent_instructions(agent_name))
        
        # Recordatorio del formato de salida
        prompt_parts.append("\nRECUERDA:")
        prompt_parts.append("- Devuelve ÚNICAMENTE el JSON especificado en tu contrato")
        prompt_parts.append("- No incluyas texto adicional fuera del JSON")
        prompt_parts.append("- Asegura que todos los campos requeridos estén presentes")
        prompt_parts.append("- Los scores QA deben ser números del 1 al 5")
        
        return "\n".join(prompt_parts)
    
    def _get_agent_instructions(self, agent_name: str) -> str:
        """Obtiene instrucciones específicas para cada agente"""
        instructions = {
            "director": "Crea una Beat Sheet de 10 escenas con arco emocional completo y leitmotiv memorable.",
            "psicoeducador": "Define metas conductuales y recursos psicoeducativos apropiados para la edad.",
            "cuentacuentos": "Convierte la estructura en versos líricos de 4-5 líneas por página.",
            "editor_claridad": "Simplifica el texto para máxima comprensión sin perder belleza.",
            "ritmo_rima": "Ajusta ritmo y rima para fluidez natural y musicalidad.",
            "continuidad": "Crea la Character Bible con consistencia visual completa.",
            "diseno_escena": "Genera prompts visuales detallados y filmables para cada página.",
            "direccion_arte": "Define paleta cromática y estilo visual coherente.",
            "sensibilidad": "Audita contenido para seguridad infantil y sensibilidad cultural.",
            "portadista": "Crea 3 opciones de título y prompt de portada atractivos.",
            "loader": "Genera 10 mensajes de carga personalizados y mágicos.",
            "validador": "Ensambla el JSON final con todas las páginas y elementos."
        }
        
        return instructions.get(agent_name, "Procesa según tu contrato definido.")
    
    def _retry_with_improvements(self, agent_name: str, improvements: str, retry_count: int) -> Dict[str, Any]:
        """Reintenta un agente con instrucciones de mejora"""
        logger.info(f"Reintentando {agent_name} con mejoras (intento {retry_count})")
        
        # Modificar el prompt del usuario para incluir las mejoras
        system_prompt = self._load_system_prompt(agent_name)
        dependencies = self._load_dependencies(agent_name)
        
        # Construir prompt con mejoras
        user_prompt = self._build_user_prompt(agent_name, dependencies)
        user_prompt += f"\n\n{improvements}\n\nPor favor, genera una nueva versión mejorada siguiendo estas instrucciones."
        
        # Ejecutar de nuevo (recursivamente)
        return self.run_agent(agent_name, retry_count)
    
    def _get_output_filename(self, agent_name: str) -> str:
        """Genera el nombre del archivo de salida para un agente"""
        agent_index = {
            "director": "01",
            "psicoeducador": "02",
            "cuentacuentos": "03",
            "editor_claridad": "04",
            "ritmo_rima": "05",
            "continuidad": "06",
            "diseno_escena": "07",
            "direccion_arte": "08",
            "sensibilidad": "09",
            "portadista": "10",
            "loader": "11",
            "validador": "12"
        }
        
        index = agent_index.get(agent_name, "99")
        return f"{index}_{agent_name}.json"
    
    def _save_output(self, filename: str, content: Dict[str, Any]):
        """Guarda la salida de un agente"""
        output_path = get_artifact_path(self.story_id, filename)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(content, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Salida guardada en: {output_path}")
    
    def _save_log(self, agent_name: str, log_entry: Dict[str, Any]):
        """Guarda una entrada de log para un agente"""
        log_dir = get_artifact_path(self.story_id, "logs")
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / f"{agent_name}.log"
        
        # Agregar al log existente si existe
        logs = []
        if log_file.exists():
            with open(log_file, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        
        logs.append(log_entry)
        
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Log guardado para {agent_name}")