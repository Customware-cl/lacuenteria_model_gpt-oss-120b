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
            
            # Extraer información de tokens si está disponible
            tokens_info = agent_output.pop("_metadata_tokens", {})
            
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
            if agent_name not in ["validador", "critico", "verificador_qa"]:
                # Usar verificador_qa independiente en lugar de autoevaluación
                logger.info(f"Ejecutando verificación QA independiente para {agent_name}")
                
                # Preparar contexto para el verificador
                verification_context = {
                    "agente_a_evaluar": agent_name,
                    "output_del_agente": agent_output,
                    "dependencias_usadas": dependencies if dependencies else {}
                }
                
                # Ejecutar verificador_qa
                verification_prompt = self._build_verification_prompt(agent_name, agent_output, dependencies)
                
                try:
                    # Llamar al verificador con temperatura baja para consistencia
                    # Guardar configuración actual de timeout
                    original_timeout = self.llm_client.timeout
                    self.llm_client.timeout = 900  # 900 segundos para evitar truncamiento
                    
                    verificador_result, _, _ = self.llm_client.generate(
                        system_prompt=self._load_system_prompt("verificador_qa"),
                        user_prompt=verification_prompt,
                        temperature=0.3,  # Baja para evaluación consistente
                        max_tokens=3000  # Aumentado para respuestas completas
                    )
                    
                    # Restaurar timeout original
                    self.llm_client.timeout = original_timeout
                    
                    # Parsear resultado del verificador
                    import json
                    verification = json.loads(verificador_result)
                    
                    # Extraer scores y verificar umbral
                    qa_scores = verification.get("qa_scores", {})
                    qa_scores["promedio"] = verification.get("promedio", 0)
                    qa_passed = verification.get("pasa_umbral", False)
                    qa_issues = verification.get("problemas_detectados", [])
                    
                    # Log de la evaluación independiente
                    logger.info(f"Verificación QA para {agent_name}: promedio={qa_scores.get('promedio', 0)}, pasa={qa_passed}")
                    
                except Exception as e:
                    logger.error(f"Error en verificación QA independiente: {e}")
                    # Fallback a la autoevaluación si falla el verificador
                    logger.warning("Usando autoevaluación como fallback")
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
            log_data = {
                "timestamp": datetime.now().isoformat(),
                "retry_count": retry_count,
                "qa_scores": qa_scores if agent_name != "validador" else None,
                "execution_time": execution_time,
                "temperature": agent_temperature or self.llm_client.temperature,
                "max_tokens": max_tokens or self.llm_client.max_tokens,
                "status": "success"
            }
            
            # Agregar información de tokens si está disponible
            if tokens_info:
                log_data["tokens_consumed"] = tokens_info
            
            self._save_log(agent_name, log_data)
            
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
    
    def _build_verification_prompt(self, agent_name: str, agent_output: Dict[str, Any], dependencies: Dict[str, Any]) -> str:
        """Construye el prompt para el verificador QA"""
        prompt_parts = []
        
        prompt_parts.append("TAREA: Evaluar objetivamente el trabajo del siguiente agente")
        prompt_parts.append("=" * 50)
        prompt_parts.append(f"\nAGENTE A EVALUAR: {agent_name}")
        
        # Incluir dependencias que usó el agente para contexto
        if dependencies:
            prompt_parts.append("\nDEPENDENCIAS QUE USÓ EL AGENTE:")
            prompt_parts.append("-" * 30)
            for dep_name in dependencies.keys():
                prompt_parts.append(f"- {dep_name}")
        
        prompt_parts.append("\nOUTPUT DEL AGENTE A EVALUAR:")
        prompt_parts.append("=" * 50)
        prompt_parts.append(json.dumps(agent_output, ensure_ascii=False, indent=2))
        
        prompt_parts.append("\n\nINSTRUCCIONES DE EVALUACIÓN:")
        prompt_parts.append("=" * 50)
        prompt_parts.append("1. Analiza el output buscando problemas específicos")
        prompt_parts.append("2. Aplica las penalizaciones automáticas según corresponda")
        prompt_parts.append("3. Calcula el score para cada métrica del agente")
        prompt_parts.append("4. Determina si pasa el umbral de 4.0")
        prompt_parts.append("5. Genera feedback específico y accionable")
        
        prompt_parts.append("\nRECUERDA:")
        prompt_parts.append("- Sé CRÍTICO y OBJETIVO")
        prompt_parts.append("- La mayoría de outputs deben estar en 3-3.5")
        prompt_parts.append("- Un 5/5 es excepcional y requiere justificación")
        prompt_parts.append("- Devuelve ÚNICAMENTE el JSON especificado")
        
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
            "validador": "12",
            "critico": "13"
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