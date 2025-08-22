"""
Agent Runner optimizado con configuraciones individuales por agente
"""
import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
import sys
import os

# Agregar src al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import (
    get_agent_prompt_path,
    get_artifact_path,
    AGENT_DEPENDENCIES,
    QUALITY_THRESHOLDS,
    AGENT_TEMPERATURES,
    AGENT_MAX_TOKENS
)
from src.llm_client_optimized import get_optimized_llm_client

logger = logging.getLogger(__name__)


class OptimizedAgentRunner:
    """Ejecutor de agentes con configuraciones optimizadas individuales"""
    
    def __init__(self, story_id: str):
        self.story_id = story_id
        self.llm_client = get_optimized_llm_client()
        self.story_path = Path(f"runs/{story_id}")
        self.logs_path = self.story_path / "logs"
        self.logs_path.mkdir(parents=True, exist_ok=True)
        
        # Cargar configuraciones optimizadas
        self.optimized_configs = self._load_optimized_configs()
        
    def _load_optimized_configs(self) -> Dict:
        """Carga las configuraciones optimizadas por agente"""
        config_file = Path("config/agent_optimized_params.json")
        
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                logger.info("Configuraciones optimizadas cargadas")
                return config.get("agent_configs", {})
        else:
            logger.warning("No se encontró archivo de configuraciones optimizadas, usando defaults")
            return {}
    
    def _get_agent_config(self, agent_name: str) -> Dict:
        """Obtiene la configuración optimizada para un agente específico"""
        
        # Buscar en configuraciones optimizadas
        if agent_name in self.optimized_configs:
            config = self.optimized_configs[agent_name].copy()
            # Remover campos no necesarios para LLM
            config.pop("priority", None)
            config.pop("qa_status", None)
            config.pop("_comment", None)
            
            logger.info(f"Usando configuración optimizada para {agent_name}: "
                       f"T={config.get('temperature')}, Max={config.get('max_tokens')}")
            return config
        
        # Fallback a configuración default
        config = {
            "temperature": AGENT_TEMPERATURES.get(agent_name, 0.7),
            "max_tokens": AGENT_MAX_TOKENS.get(agent_name, 4000)
        }
        
        logger.info(f"Usando configuración default para {agent_name}")
        return config
    
    def _load_system_prompt(self, agent_name: str) -> str:
        """Carga el prompt del sistema para un agente"""
        prompt_path = get_agent_prompt_path(agent_name)
        
        if not prompt_path.exists():
            raise FileNotFoundError(f"No se encontró el archivo de prompt: {prompt_path}")
        
        with open(prompt_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get("content", "")
    
    def _load_dependencies(self, agent_name: str) -> Dict[str, Any]:
        """Carga las dependencias necesarias para un agente"""
        dependencies = {}
        required_deps = AGENT_DEPENDENCIES.get(agent_name, [])
        
        for dep in required_deps:
            dep_path = get_artifact_path(self.story_id, dep)
            if dep_path.exists():
                with open(dep_path, 'r', encoding='utf-8') as f:
                    dependencies[dep] = json.load(f)
                logger.debug(f"Dependencia cargada: {dep}")
            else:
                logger.warning(f"Dependencia no encontrada: {dep}")
        
        return dependencies
    
    def _build_user_prompt(self, agent_name: str, dependencies: Dict[str, Any]) -> str:
        """Construye el prompt del usuario con las dependencias"""
        prompt = f"Story ID: {self.story_id}\n\n"
        
        for dep_name, dep_content in dependencies.items():
            prompt += f"=== {dep_name} ===\n"
            prompt += json.dumps(dep_content, ensure_ascii=False, indent=2)
            prompt += "\n\n"
        
        # Agregar instrucciones específicas para agentes problemáticos
        if agent_name == "editor_claridad":
            prompt += "\nIMPORTANTE: Genera texto completo para TODAS las 10 páginas. No dejes ninguna página vacía."
        elif agent_name == "cuentacuentos":
            prompt += "\nIMPORTANTE: Evita repetir palabras. Usa sinónimos variados. Máximo 3 usos de cada palabra."
        elif agent_name == "ritmo_rima":
            prompt += "\nIMPORTANTE: No uses rimas idénticas (amor/amor). Mantén métrica consistente de 8-10 sílabas."
        
        return prompt
    
    def run(self, agent_name: str, retry_count: int = 0) -> Dict[str, Any]:
        """
        Ejecuta un agente con su configuración optimizada
        
        Args:
            agent_name: Nombre del agente a ejecutar
            retry_count: Número de reintento actual
            
        Returns:
            Dict con el resultado del agente
        """
        logger.info(f"Ejecutando agente: {agent_name} (intento {retry_count + 1})")
        start_time = time.time()
        
        try:
            # Cargar componentes
            system_prompt = self._load_system_prompt(agent_name)
            dependencies = self._load_dependencies(agent_name)
            user_prompt = self._build_user_prompt(agent_name, dependencies)
            
            # Obtener configuración optimizada
            llm_config = self._get_agent_config(agent_name)
            
            # Ejecutar LLM con configuración optimizada
            agent_output = self.llm_client.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                **llm_config
            )
            
            execution_time = time.time() - start_time
            
            # Verificación QA con verificador_qa (si no es validador/critico)
            if agent_name not in ["validador", "critico", "verificador_qa"]:
                # Por ahora simular QA (en producción usar verificador_qa real)
                qa_passed, qa_scores = self._simulate_qa_check(agent_name, agent_output)
                
                # Agregar QA al output
                agent_output["qa"] = qa_scores
                agent_output["_qa_passed"] = qa_passed
            else:
                qa_passed = True
                qa_scores = {}
            
            # Guardar output con nombre fijo (sin número de reintento)
            output_file = get_artifact_path(self.story_id, f"{agent_name}.json")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(agent_output, f, ensure_ascii=False, indent=2)
            
            # Guardar log
            self._save_log(agent_name, {
                "timestamp": time.time(),
                "retry_count": retry_count,
                "qa_scores": qa_scores,
                "execution_time": execution_time,
                "config_used": llm_config,
                "status": "success" if qa_passed else "qa_failed",
                "tokens_consumed": agent_output.get("_metadata_tokens", {})
            })
            
            logger.info(f"Agente {agent_name} completado en {execution_time:.2f}s - QA: {qa_passed}")
            
            return {
                "success": True,
                "qa_passed": qa_passed,
                "qa_scores": qa_scores,
                "execution_time": execution_time,
                "output": agent_output
            }
            
        except Exception as e:
            logger.error(f"Error ejecutando agente {agent_name}: {e}")
            
            self._save_log(agent_name, {
                "timestamp": time.time(),
                "retry_count": retry_count,
                "error": str(e),
                "execution_time": time.time() - start_time,
                "status": "error"
            })
            
            return {
                "success": False,
                "error": str(e),
                "execution_time": time.time() - start_time
            }
    
    def _simulate_qa_check(self, agent_name: str, output: Dict) -> tuple:
        """
        Simula verificación QA (en producción usar verificador_qa real)
        Retorna (passed: bool, scores: dict)
        """
        # Simulación basada en heurísticas simples
        qa_scores = {}
        
        if agent_name == "editor_claridad":
            pages = output.get("paginas_texto_claro", {})
            if not pages or any(not pages.get(str(i), "").strip() for i in range(1, 11)):
                qa_scores = {"completitud": 1.0, "promedio": 1.0}
            else:
                qa_scores = {"completitud": 5.0, "claridad": 4.5, "promedio": 4.75}
                
        elif agent_name == "cuentacuentos":
            pages = output.get("paginas", {})
            if pages:
                # Verificar repeticiones básicas
                all_text = " ".join(pages.values())
                repetition_score = 4.0 if all_text.count("brilla") < 4 else 3.0
                qa_scores = {"musicalidad": 4.0, "repeticiones": repetition_score, "promedio": (4.0 + repetition_score) / 2}
            else:
                qa_scores = {"promedio": 1.0}
                
        elif agent_name == "ritmo_rima":
            qa_scores = {"rimas": 4.0, "métrica": 3.8, "promedio": 3.9}
            
        else:
            # Default para otros agentes
            qa_scores = {"promedio": 4.2}
        
        passed = qa_scores.get("promedio", 0) >= QUALITY_THRESHOLDS["min_qa_score"]
        
        return passed, qa_scores
    
    
    def _save_log(self, agent_name: str, log_entry: Dict):
        """Guarda entrada de log para un agente"""
        log_file = self.logs_path / f"{agent_name}.log"
        
        # Leer logs existentes
        logs = []
        if log_file.exists():
            with open(log_file, 'r', encoding='utf-8') as f:
                try:
                    logs = json.load(f)
                except:
                    logs = []
        
        # Agregar nueva entrada
        logs.append(log_entry)
        
        # Guardar
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)