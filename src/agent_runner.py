"""
Ejecutor de agentes individuales
"""
import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from config import (
    get_agent_prompt_path,
    get_artifact_path,
    get_story_path as get_story_dir,
    AGENT_DEPENDENCIES
)
from llm_client import get_llm_client
from quality_gates import get_quality_checker
from conflict_analyzer import get_conflict_analyzer

logger = logging.getLogger(__name__)


class AgentRunner:
    """Ejecuta agentes individuales con sus dependencias"""
    
    def __init__(self, story_id: str, mode_verificador_qa: bool = True, version: str = 'v1'):
        self.story_id = story_id
        self.llm_client = get_llm_client()
        self.mode_verificador_qa = mode_verificador_qa
        self.version = version  # Nueva propiedad para versión
        
        # Establecer directorio base
        from pathlib import Path
        self.base_dir = Path(__file__).parent.parent
        
        # Cargar configuración de versión
        from config import load_version_config
        self.version_config = load_version_config(version)
        
        # Inicializar quality_checker con umbrales específicos si existen
        agent_qa_thresholds = self.version_config.get('agent_qa_thresholds', {})
        self.quality_checker = get_quality_checker(agent_qa_thresholds)
        
        # Inicializar analizador de conflictos para v2
        self.conflict_analyzer = None
        if version != 'v1':
            self.conflict_analyzer = get_conflict_analyzer(version)
        
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
        logger.info(f"DEBUG: Verificando configuración para '{agent_name}'")
        
        # SIEMPRE usar procesamiento especial para cuentacuentos en v2
        if agent_name == "03_cuentacuentos" and self.version == "v2":
            # Usar siempre el procesador especial (que ahora es secuencial)
            logger.info(f"🚀 Usando procesamiento ESPECIAL para {agent_name}")
            try:
                from parallel_cuentacuentos import ParallelCuentacuentos
                processor = ParallelCuentacuentos(self.story_id, self.version)
                result = processor.run()
                
                # Adaptar resultado al formato esperado
                if result["status"] == "completed":
                    return {
                        "status": "success",
                        "agent_output": result["agent_output"],
                        "qa_passed": True,
                        "qa_score": result["agent_output"]["metadata"].get("average_qa_score", 4.0),
                        "processing_mode": "parallel",
                        "processing_time": result["total_time"]
                    }
                else:
                    return {
                        "status": "partial_failure",
                        "agent_output": result["agent_output"],
                        "qa_passed": False,
                        "error": f"Solo {result['pages_successful']}/10 páginas completadas",
                        "processing_mode": "parallel",
                        "processing_time": result["total_time"]
                    }
            except Exception as e:
                logger.error(f"❌ Error en procesamiento paralelo, fallback a secuencial: {e}")
                # Continuar con procesamiento normal si falla
        
        try:
            # 1. Cargar el prompt del sistema
            system_prompt = self._load_system_prompt(agent_name)
            
            # 2. Cargar las dependencias (artefactos previos)
            dependencies = self._load_dependencies(agent_name)
            
            # 3. Construir el prompt del usuario
            user_prompt = self._build_user_prompt(agent_name, dependencies)
            
            # 4. Obtener configuración específica del agente
            agent_config = {}
            agent_temperature = None
            max_tokens = None
            top_p = None
            
            # Para v2+, usar configuración desde agent_config.json
            if self.version != 'v1' and 'agent_config' in self.version_config:
                agent_config = self.version_config['agent_config'].get(agent_name, {})
                agent_temperature = agent_config.get('temperature')
                max_tokens = agent_config.get('max_tokens')
                top_p = agent_config.get('top_p')
            
            # Fallback para v1 o si no hay configuración específica
            if agent_temperature is None:
                from config import AGENT_TEMPERATURES
                agent_temperature = AGENT_TEMPERATURES.get(agent_name, None)
            
            if max_tokens is None:
                from config import AGENT_MAX_TOKENS
                max_tokens = AGENT_MAX_TOKENS.get(agent_name, None)
            if max_tokens:
                logger.info(f"📊 Usando max_tokens específico para {agent_name}: {max_tokens}")
            else:
                logger.info(f"📊 Sin configuración específica para '{agent_name}', usando default: {self.llm_client.max_tokens}")
            
            if top_p:
                logger.info(f"📊 Usando top_p específico para {agent_name}: {top_p}")
            
            # Guardar solicitud completa antes de enviar
            self._save_agent_request(
                agent_name=agent_name,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=agent_temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                dependencies=list(dependencies.keys()) if dependencies else [],
                retry_count=retry_count
            )
            
            start_time = datetime.now()
            try:
                agent_output = self.llm_client.generate(
                    system_prompt, 
                    user_prompt,
                    temperature=agent_temperature,
                    max_tokens=max_tokens,
                    top_p=top_p
                )
            except ValueError as ve:
                # Capturar el caso especial de STOP
                if "STOP:" in str(ve):
                    logger.error(f"🛑 {agent_name} - Contexto excedido en primer intento")
                    
                    # Crear alerta crítica
                    alert_data = {
                        "tipo": "contexto_excedido",
                        "agente": agent_name,
                        "intento": retry_count + 1,
                        "timestamp": datetime.now().isoformat(),
                        "critico": True,
                        "contexto": {
                            "temperatura": agent_temperature or self.llm_client.temperature,
                            "max_tokens": max_tokens or self.llm_client.max_tokens,
                            "timeout": self.llm_client.timeout,
                            "prompt_length": len(user_prompt),
                            "dependencies_size": sum(len(str(v)) for v in dependencies.values()) if dependencies else 0,
                            "total_chars": len(system_prompt) + len(user_prompt),
                            "approx_tokens": (len(system_prompt) + len(user_prompt)) // 4
                        },
                        "diagnostico": self._diagnosticar_problema_contenido(agent_name, user_prompt, dependencies),
                        "accion": "PROCESO DETENIDO - No se realizarán reintentos"
                    }
                    
                    # Guardar alerta crítica
                    self._registrar_alerta_temprana(alert_data)
                    
                    # NO reintentar - propagar el error inmediatamente
                    return {
                        "status": "error",
                        "agent": agent_name,
                        "error": "Contexto excedido - El modelo no puede procesar esta cantidad de información",
                        "details": alert_data,
                        "retry_count": retry_count
                    }
                    
                elif "El modelo no generó contenido" in str(ve):
                    # ALERTA TEMPRANA - Intento sin contenido (no es el primero)
                    logger.error(f"🚨 ALERTA: {agent_name} - El modelo no generó contenido en intento {retry_count + 1}")
                    
                    # Crear alerta detallada
                    alert_data = {
                        "tipo": "contenido_vacio",
                        "agente": agent_name,
                        "intento": retry_count + 1,
                        "timestamp": datetime.now().isoformat(),
                        "contexto": {
                            "temperatura": agent_temperature or self.llm_client.temperature,
                            "max_tokens": max_tokens or self.llm_client.max_tokens,
                            "timeout": self.llm_client.timeout,
                            "prompt_length": len(user_prompt),
                            "dependencies_size": sum(len(str(v)) for v in dependencies.values()) if dependencies else 0
                        },
                        "diagnostico": self._diagnosticar_problema_contenido(agent_name, user_prompt, dependencies)
                    }
                    
                    # Guardar alerta en manifest
                    self._registrar_alerta_temprana(alert_data)
                    
                    # Re-lanzar para que el flujo normal maneje el reintento
                    raise
                else:
                    # Otros errores de ValueError
                    raise
            
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
                # Decidir si usar verificador_qa o autoevaluación basado en mode_verificador_qa
                if self.mode_verificador_qa:
                    # MODO VERIFICADOR QA INDEPENDIENTE (ESTRICTO)
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
                        
                        # Guardar solicitud del verificador QA
                        verificador_system_prompt = self._load_system_prompt("verificador_qa")
                        self._save_agent_request(
                            agent_name=f"verificador_qa_{agent_name}",
                            system_prompt=verificador_system_prompt,
                            user_prompt=verification_prompt,
                            temperature=0.3,
                            max_tokens=30000,
                            dependencies=[f"{agent_name}.json"],
                            retry_count=0
                        )
                        
                        verificador_result = self.llm_client.generate(
                            system_prompt=verificador_system_prompt,
                            user_prompt=verification_prompt,
                            temperature=0.3,  # Baja para evaluación consistente
                            max_tokens=30000  # Masivo para evaluar contenidos grandes
                        )
                        
                        # Restaurar timeout original
                        self.llm_client.timeout = original_timeout
                        
                        # Parsear resultado del verificador si es necesario
                        import json
                        if isinstance(verificador_result, str):
                            verification = json.loads(verificador_result)
                        else:
                            verification = verificador_result  # Ya es un dict
                        
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
                else:
                    # MODO AUTOEVALUACIÓN (RÁPIDO, MENOS ESTRICTO)
                    logger.info(f"Ejecutando autoevaluación para {agent_name} (mode_verificador_qa=False)")
                    
                    # Usar autoevaluación directamente del output del agente
                    qa_passed, qa_scores, qa_issues = self.quality_checker.check_qa_scores(
                        agent_output, agent_name
                    )
                    
                    logger.info(f"Autoevaluación para {agent_name}: promedio={qa_scores.get('promedio', 0)}, pasa={qa_passed}")
                
                if not qa_passed:
                    logger.warning(f"QA no pasó para {agent_name}: {qa_issues}")
                    
                    # Analizar conflictos si estamos en v2
                    conflict_analysis = None
                    if self.conflict_analyzer:
                        # Cargar el prompt del agente para análisis profundo
                        agent_prompt = self._load_system_prompt(agent_name)
                        conflict_analysis = self.conflict_analyzer.analyze_qa_failure(
                            agent_name=agent_name,
                            qa_issues=qa_issues,
                            qa_scores=qa_scores,
                            story_id=self.story_id,
                            agent_prompt=agent_prompt
                        )
                        logger.info(f"Análisis de conflictos para {agent_name}: {len(conflict_analysis['patterns_detected'])} patrones detectados")
                    
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
                            retry_count + 1,
                            conflict_analysis=conflict_analysis,
                            qa_issues=qa_issues,
                            previous_output=agent_output
                        )
                    else:
                        logger.error(f"Máximo de reintentos alcanzado para {agent_name}")
                        
                        # IMPORTANTE: Guardar el output aunque falle QA para no romper dependencias
                        output_file = self._get_output_filename(agent_name)
                        # Agregar metadata de QA al output antes de guardar
                        agent_output_with_qa = agent_output.copy()
                        agent_output_with_qa["_qa_metadata"] = {
                            "status": "failed",
                            "scores": qa_scores,
                            "issues": qa_issues[:5],  # Solo los 5 principales
                            "retry_count": retry_count,
                            "timestamp": datetime.now().isoformat()
                        }
                        self._save_output(output_file, agent_output_with_qa)
                        logger.warning(f"Output guardado con QA fallido para {agent_name} (para mantener dependencias)")
                        
                        # Guardar log del fallo
                        log_data = {
                            "timestamp": datetime.now().isoformat(),
                            "retry_count": retry_count,
                            "qa_scores": qa_scores,
                            "execution_time": execution_time,
                            "temperature": agent_temperature or self.llm_client.temperature,
                            "max_tokens": max_tokens or self.llm_client.max_tokens,
                            "status": "qa_failed",
                            "qa_issues": qa_issues[:5]
                        }
                        self._save_log(agent_name, log_data)
                        
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
        """Carga el prompt del sistema para un agente según versión"""
        # Usar versión para obtener el path correcto
        logger.info(f"🔍 Cargando prompt para {agent_name} con versión {self.version}")
        prompt_path = get_agent_prompt_path(agent_name, self.version)
        logger.info(f"🔍 Path calculado: {prompt_path}")
        
        with open(prompt_path, 'r', encoding='utf-8') as f:
            agent_config = json.load(f)
        
        if "content" not in agent_config:
            raise ValueError(f"Archivo de agente {agent_name} no tiene campo 'content'")
        
        # NO reemplazar placeholders - actúan como referencias descriptivas
        # La información real viene del brief.json en el user_prompt
        return agent_config["content"]
    
    def _load_dependencies(self, agent_name: str) -> Dict[str, Any]:
        """Carga las dependencias (artefactos previos) para un agente"""
        dependencies = {}
        
        # Usar dependencias de la versión configurada
        agent_dependencies = self.version_config.get('dependencies', {})
        
        if agent_name not in agent_dependencies:
            logger.warning(f"No se encontraron dependencias definidas para {agent_name}")
            return dependencies
        
        for dependency_file in agent_dependencies[agent_name]:
            # Para v2, convertir nombres numerados a nombres simples para buscar archivos
            # Ej: "01_director.json" -> "director.json" para compatibilidad
            if self.version != 'v1' and dependency_file.startswith(('0', '1')):
                # Mantener el nombre numerado para v2
                artifact_path = get_artifact_path(self.story_id, dependency_file)
            else:
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
        
        # Cargar criterios de evaluación desde el archivo JSON si existe
        criterios_path = self.base_dir / f"flujo/{self.version}/criterios_evaluacion/{agent_name}.json"
        criterios_content = None
        
        if criterios_path.exists():
            try:
                with open(criterios_path, 'r', encoding='utf-8') as f:
                    criterios_content = json.load(f)
                    prompt_parts.append("\nCRITERIOS DE EVALUACIÓN (desde archivo JSON):")
                    prompt_parts.append("=" * 50)
                    prompt_parts.append(json.dumps(criterios_content, ensure_ascii=False, indent=2))
            except Exception as e:
                logger.warning(f"Error cargando criterios de evaluación: {e}")
        
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
        
        if criterios_content:
            prompt_parts.append("1. USA LOS CRITERIOS DEL JSON CARGADO ARRIBA")
            prompt_parts.append("2. Evalúa cada criterio como true/false según el output")
            prompt_parts.append("3. Calcula porcentajes según la configuración del JSON")
            prompt_parts.append("4. Aplica penalizaciones automáticas si están definidas")
            prompt_parts.append("5. El umbral de aprobación está en el JSON")
        else:
            prompt_parts.append("1. Analiza el output buscando problemas específicos")
            prompt_parts.append("2. Aplica las penalizaciones automáticas según corresponda")
            prompt_parts.append("3. Calcula el score para cada métrica del agente")
            prompt_parts.append("4. Determina si pasa el umbral de 4.0")
        
        prompt_parts.append("6. Genera feedback específico y accionable")
        prompt_parts.append("7. En 'mejoras_especificas', incluye instrucciones CONCRETAS para corregir cada problema")
        
        prompt_parts.append("\nRECUERDA:")
        prompt_parts.append("- Sé CRÍTICO y OBJETIVO")
        prompt_parts.append("- Usa la configuración del JSON de criterios si está disponible")
        prompt_parts.append("- Las mejoras_especificas deben ser ACCIONABLES y CLARAS")
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
    
    def _retry_with_improvements(self, 
                                 agent_name: str, 
                                 improvements: str, 
                                 retry_count: int,
                                 conflict_analysis: Optional[Dict[str, Any]] = None,
                                 qa_issues: Optional[List[str]] = None,
                                 previous_output: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Reintenta un agente con instrucciones de mejora y feedback específico"""
        logger.info(f"Reintentando {agent_name} con mejoras (intento {retry_count})")
        
        # Modificar el prompt del usuario para incluir las mejoras
        system_prompt = self._load_system_prompt(agent_name)
        dependencies = self._load_dependencies(agent_name)
        
        # Construir prompt base
        user_prompt = self._build_user_prompt(agent_name, dependencies)
        
        # Agregar sección de mejoras específicas
        user_prompt += "\n\n" + "=" * 50
        user_prompt += "\n⚠️ RETROALIMENTACIÓN DEL VERIFICADOR DE CALIDAD ⚠️\n"
        user_prompt += "=" * 50 + "\n"
        
        # IMPORTANTE: Incluir el output anterior para que el modelo lo corrija
        if previous_output:
            user_prompt += "\n📝 TU OUTPUT ANTERIOR (que necesita correcciones):\n"
            user_prompt += "```json\n"
            user_prompt += json.dumps(previous_output, ensure_ascii=False, indent=2)
            user_prompt += "\n```\n"
            user_prompt += "\n⚠️ INSTRUCCIÓN CRÍTICA: NO generes un output completamente nuevo.\n"
            user_prompt += "Toma el JSON anterior como base y MODIFICA SOLO lo necesario para corregir los problemas señalados.\n"
            user_prompt += "Mantén todo lo que está bien y cambia únicamente lo que se indica a continuación.\n"
        
        # Si tenemos análisis de conflictos (v2), usar feedback específico
        if conflict_analysis and conflict_analysis.get('recommendations'):
            user_prompt += "\n📊 PROBLEMAS DETECTADOS Y SOLUCIONES:\n"
            for i, rec in enumerate(conflict_analysis['recommendations'], 1):
                user_prompt += f"{i}. {rec}\n"
            
            # Agregar patrones específicos detectados
            if conflict_analysis.get('patterns_detected'):
                user_prompt += "\n🔍 DETALLES ESPECÍFICOS:\n"
                for pattern in conflict_analysis['patterns_detected']:
                    user_prompt += f"- Problema: {pattern['issue_text']}\n"
                    user_prompt += f"  Solución: {pattern['recommendation']}\n"
        
        # Si tenemos recomendaciones del dashboard para este agente
        if self.conflict_analyzer:
            dashboard_recommendations = self.conflict_analyzer.get_recommendations_for_retry(agent_name)
            if dashboard_recommendations:
                user_prompt += "\n📚 ERRORES COMUNES A EVITAR:\n"
                for rec in dashboard_recommendations:
                    user_prompt += f"- {rec}\n"
        
        # Agregar issues específicos del verificador
        if qa_issues:
            user_prompt += "\n❌ PROBLEMAS ESPECÍFICOS ENCONTRADOS:\n"
            for issue in qa_issues[:5]:  # Limitar a los 5 más importantes
                user_prompt += f"- {issue}\n"
        
        # Agregar las instrucciones genéricas de mejora
        user_prompt += f"\n{improvements}"
        
        # Instrucción final enfática
        user_prompt += "\n\n" + "=" * 50
        if previous_output:
            user_prompt += "\n🎯 MODO CORRECCIÓN ACTIVADO:\n"
            user_prompt += "1. USA el JSON anterior como base\n"
            user_prompt += "2. APLICA SOLO las correcciones específicas mencionadas\n"
            user_prompt += "3. MANTÉN todo lo demás exactamente igual\n"
            user_prompt += "4. NO regeneres desde cero\n"
        else:
            user_prompt += "\n🎯 IMPORTANTE: Por favor, genera una nueva versión que ESPECÍFICAMENTE resuelva los problemas mencionados arriba.\n"
            user_prompt += "No repitas los mismos errores. Presta especial atención a los puntos marcados con ⚠️.\n"
        user_prompt += "=" * 50
        
        # Ejecutar de nuevo (recursivamente)
        return self.run_agent(agent_name, retry_count)
    
    def _get_output_filename(self, agent_name: str) -> str:
        """Genera el nombre del archivo de salida para un agente"""
        # Para v2, mantener numeración en el nombre del archivo
        # Para v1, usar solo el nombre del agente
        return f"{agent_name}.json"
    
    def _save_output(self, filename: str, content: Dict[str, Any]):
        """Guarda la salida de un agente"""
        # Guardar en outputs/agents
        story_path = Path(get_story_dir(self.story_id))
        outputs_dir = story_path / "outputs" / "agents"
        outputs_dir.mkdir(parents=True, exist_ok=True)
        
        output_path = outputs_dir / filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(content, f, ensure_ascii=False, indent=2)
        
        # También guardar en raíz por compatibilidad
        legacy_path = get_artifact_path(self.story_id, filename)
        with open(legacy_path, 'w', encoding='utf-8') as f:
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
    
    def _diagnosticar_problema_contenido(self, agent_name: str, user_prompt: str, dependencies: Dict[str, Any]) -> Dict[str, Any]:
        """Diagnostica por qué el modelo no generó contenido"""
        diagnostico = {
            "posibles_causas": [],
            "metricas": {},
            "recomendaciones": []
        }
        
        # Analizar tamaño del prompt
        prompt_tokens_approx = len(user_prompt) // 4  # Aproximación
        diagnostico["metricas"]["prompt_tokens_aprox"] = prompt_tokens_approx
        
        if prompt_tokens_approx > 3000:
            diagnostico["posibles_causas"].append("Prompt demasiado largo (>3000 tokens aprox)")
            diagnostico["recomendaciones"].append("Reducir tamaño de dependencias o simplificar prompt")
        
        # Analizar dependencias
        if dependencies:
            dep_size = sum(len(str(v)) for v in dependencies.values())
            diagnostico["metricas"]["dependencies_chars"] = dep_size
            
            if dep_size > 20000:
                diagnostico["posibles_causas"].append(f"Dependencias muy grandes ({dep_size} caracteres)")
                diagnostico["recomendaciones"].append("Considerar resumir o filtrar dependencias")
        
        # Analizar agente específico
        agentes_problematicos = ["cuentacuentos", "validador", "loader"]
        if agent_name in agentes_problematicos:
            diagnostico["posibles_causas"].append(f"Agente {agent_name} requiere output extenso")
            diagnostico["recomendaciones"].append(f"Aumentar max_tokens para {agent_name}")
        
        # Verificar JSON complejo
        if agent_name in ["validador", "cuentacuentos"]:
            diagnostico["posibles_causas"].append("Output JSON muy complejo requerido")
            diagnostico["recomendaciones"].append("Considerar dividir en sub-tareas")
        
        # Timeout vs contenido vacío
        if self.llm_client.timeout < 600:
            diagnostico["posibles_causas"].append(f"Timeout muy corto ({self.llm_client.timeout}s)")
            diagnostico["recomendaciones"].append("Aumentar timeout a 900s")
        
        return diagnostico
    
    def _registrar_alerta_temprana(self, alert_data: Dict[str, Any]):
        """Registra una alerta temprana en el manifest y logs"""
        try:
            # Actualizar manifest con alerta
            manifest_path = get_artifact_path(self.story_id, "manifest.json")
            
            if os.path.exists(manifest_path):
                with open(manifest_path, 'r', encoding='utf-8') as f:
                    manifest = json.load(f)
            else:
                manifest = {}
            
            # Agregar sección de alertas si no existe
            if "alertas_tempranas" not in manifest:
                manifest["alertas_tempranas"] = []
            
            manifest["alertas_tempranas"].append(alert_data)
            
            # También actualizar el campo de error si es relevante
            if alert_data["intento"] == 1:  # Primer intento
                manifest["primer_fallo_contenido"] = {
                    "agente": alert_data["agente"],
                    "timestamp": alert_data["timestamp"],
                    "diagnostico_resumen": alert_data["diagnostico"]["posibles_causas"][:2] if alert_data["diagnostico"]["posibles_causas"] else []
                }
            
            with open(manifest_path, 'w', encoding='utf-8') as f:
                json.dump(manifest, f, ensure_ascii=False, indent=2)
            
            # Guardar también en log específico de alertas
            alerts_dir = os.path.join(get_story_dir(self.story_id), "alerts")
            os.makedirs(alerts_dir, exist_ok=True)
            
            alert_file = os.path.join(alerts_dir, f"{alert_data['agente']}_alert.json")
            with open(alert_file, 'w', encoding='utf-8') as f:
                json.dump(alert_data, f, ensure_ascii=False, indent=2)
            
            logger.warning(f"🚨 Alerta temprana registrada para {alert_data['agente']}: {alert_data['diagnostico']['posibles_causas'][:1]}")
            
        except Exception as e:
            logger.error(f"Error registrando alerta temprana: {e}")
    
    def _save_agent_request(self, agent_name: str, system_prompt: str, user_prompt: str, 
                           temperature: float = None, max_tokens: int = None, top_p: float = None,
                           dependencies: list = None, retry_count: int = 0):
        """Guarda la solicitud completa enviada a un agente en la carpeta inputs/"""
        try:
            # Crear carpeta inputs si no existe
            inputs_dir = os.path.join(get_story_dir(self.story_id), "inputs")
            os.makedirs(inputs_dir, exist_ok=True)
            
            # Construir datos de la solicitud
            request_data = {
                "agent": agent_name,
                "timestamp": datetime.now().isoformat(),
                "endpoint": self.llm_client.endpoint,
                "model": self.llm_client.model,
                "temperature": temperature or self.llm_client.temperature,
                "max_tokens": max_tokens or self.llm_client.max_tokens,
                "top_p": top_p,
                "timeout": self.llm_client.timeout,
                "retry_count": retry_count,
                "dependencies": dependencies or [],
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
                "prompt_stats": {
                    "system_prompt_chars": len(system_prompt),
                    "user_prompt_chars": len(user_prompt),
                    "total_chars": len(system_prompt) + len(user_prompt),
                    "approx_tokens": (len(system_prompt) + len(user_prompt)) // 4
                }
            }
            
            # Guardar en inputs/agents para agentes regulares
            if "cuentacuentos" not in agent_name:
                agents_inputs_dir = os.path.join(inputs_dir, "agents")
                os.makedirs(agents_inputs_dir, exist_ok=True)
                request_file = os.path.join(agents_inputs_dir, f"{agent_name}_request.json")
            else:
                # Para cuentacuentos, mantener en inputs/ por ahora (se maneja en parallel_cuentacuentos)
                request_file = os.path.join(inputs_dir, f"{agent_name}_request.json")
            
            with open(request_file, 'w', encoding='utf-8') as f:
                json.dump(request_data, f, ensure_ascii=False, indent=2)
            
            logger.debug(f"📝 Solicitud guardada: {request_file}")
            
        except Exception as e:
            logger.warning(f"Error al guardar solicitud de {agent_name}: {e}")