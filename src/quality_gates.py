"""
Sistema de Quality Gates para validación de salidas de agentes
"""
import logging
import re
from typing import Dict, Any, List, Tuple, Optional
from config import QUALITY_THRESHOLDS

logger = logging.getLogger(__name__)


class QualityGateChecker:
    """Validador de quality gates para las salidas de los agentes"""
    
    def __init__(self, agent_qa_thresholds=None):
        self.min_qa_score = QUALITY_THRESHOLDS["min_qa_score"]
        self.max_retries = QUALITY_THRESHOLDS["max_retries"]
        # Umbrales específicos por agente (opcional)
        self.agent_qa_thresholds = agent_qa_thresholds or {}
        
    def check_qa_scores(self, agent_output: Dict[str, Any], agent_name: str) -> Tuple[bool, Dict[str, float], List[str]]:
        """
        Verifica los scores QA de la salida de un agente
        
        Args:
            agent_output: Salida JSON del agente
            agent_name: Nombre del agente
            
        Returns:
            Tupla con (passed, scores, issues)
            - passed: True si todos los scores >= min_qa_score
            - scores: Diccionario con los scores individuales
            - issues: Lista de problemas encontrados
        """
        issues = []
        scores = {}
        
        # Verificar que existe el campo qa
        if "qa" not in agent_output:
            logger.error(f"Agente {agent_name} no devolvió campo 'qa'")
            return False, {}, ["No se encontró campo 'qa' en la respuesta"]
        
        qa_scores = agent_output["qa"]
        
        # Verificar cada score
        for metric, score in qa_scores.items():
            scores[metric] = score
            
            # Validar que el score está en rango válido (1-5)
            if not isinstance(score, (int, float)) or score < 1 or score > 5:
                issues.append(f"Score '{metric}' inválido: {score} (debe ser entre 1 y 5)")
                continue
            
            # Verificar si cumple el umbral mínimo (específico por agente o global)
            threshold = self.agent_qa_thresholds.get(agent_name, self.min_qa_score)
            if score < threshold:
                issues.append(f"Score '{metric}' bajo umbral: {score} < {threshold}")
        
        # Calcular score promedio
        if scores:
            avg_score = sum(scores.values()) / len(scores)
            scores["promedio"] = round(avg_score, 2)
            
            # El gate pasa si el promedio cumple el umbral específico del agente
            threshold = self.agent_qa_thresholds.get(agent_name, self.min_qa_score)
            passed = avg_score >= threshold and len(issues) == 0
        else:
            passed = False
            issues.append("No se encontraron scores QA válidos")
        
        return passed, scores, issues
    
    def generate_improvement_instructions(self, 
                                         agent_name: str, 
                                         scores: Dict[str, float], 
                                         issues: List[str],
                                         agent_output: Dict[str, Any]) -> str:
        """
        Genera instrucciones específicas de mejora para un agente
        
        Args:
            agent_name: Nombre del agente
            scores: Scores QA obtenidos
            issues: Problemas encontrados
            agent_output: Salida completa del agente
            
        Returns:
            Instrucciones de mejora como string
        """
        instructions = []
        specific_corrections = []  # Correcciones muy específicas para el JSON
        
        # Instrucciones específicas por agente
        agent_specific = {
            "director": {
                "arco_completo": "Revisa que el arco narrativo tenga introducción, desarrollo, clímax y resolución claros",
                "claridad_visual": "Asegura que cada escena pueda visualizarse sin ambigüedad",
                "potencia_leitmotiv": "El leitmotiv debe ser memorable y repetible 3-4 veces"
            },
            "psicoeducador": {
                "ajuste_edad": "Verifica que las habilidades sean apropiadas para la edad objetivo",
                "alineacion_mensaje": "Asegura que cada página refuerce el mensaje principal",
                "tono_amable": "Usa lenguaje validante y esperanzador, evita moralizar"
            },
            "cuentacuentos": {
                "emocion": "Intensifica la carga emocional en los momentos clave",
                "claridad_visual": "Cada verso debe pintar una imagen clara",
                "uso_leitmotiv": "Integra el leitmotiv en páginas 2, 4, 7 y 10"
            },
            "editor_claridad": {
                "comprensibilidad": "Simplifica palabras complejas y estructuras confusas",
                "imagen_inequivoca": "Elimina toda ambigüedad visual en los versos"
            },
            "ritmo_rima": {
                "fluidez": "Ajusta el silabeo para mantener ritmo natural",
                "consistencia_rima": "Mantén esquemas de rima coherentes por página",
                "variacion_cierres": "No repitas palabras finales en versos consecutivos"
            },
            "continuidad": {
                "coherencia_rasgos": "Verifica consistencia en rasgos físicos y personalidad",
                "utilidad_arte": "Asegura que la bible sea específica y visual"
            },
            "diseno_escena": {
                "alineacion_verso_escena": "Cada prompt debe reflejar exactamente los versos",
                "variedad_planos": "Alterna entre planos generales, medios y primeros planos"
            },
            "direccion_arte": {
                "coherencia_visual": "Mantén consistencia en paleta y estilo",
                "progresion_emocional": "El color script debe reflejar el arco emocional"
            },
            "sensibilidad": {
                "seguridad_respeto": "Elimina elementos que puedan asustar o estereotipar"
            },
            "portadista": {
                "recordabilidad_titulo": "El título debe ser pegadizo y claro para niños",
                "sintesis_emotiva": "La portada debe capturar la esencia del cuento"
            },
            "loader": {
                "pertinencia": "Usa elementos específicos de la historia",
                "brevedad_tono": "Máximo 70 caracteres, tono mágico",
                "sensacion_adaptativa": "Cada mensaje debe sentirse personalizado"
            }
        }
        
        # Generar instrucciones basadas en scores bajos
        if agent_name in agent_specific:
            for metric, score in scores.items():
                if metric != "promedio" and score < self.min_qa_score:
                    if metric in agent_specific[agent_name]:
                        instructions.append(f"- {agent_specific[agent_name][metric]}")
        
        # Agregar instrucciones generales basadas en issues
        for issue in issues:
            if "bajo umbral" in issue:
                metric = issue.split("'")[1]
                instructions.append(f"- Mejorar {metric}: puntaje actual {scores.get(metric, 0)}")
        
        # Generar correcciones específicas basadas en los issues más comunes
        if agent_name == "director" or agent_name.endswith("_director"):
            for issue in issues[:3]:  # Solo los 3 problemas principales
                if "Repetición" in issue and "leitmotiv" in issue.lower():
                    if "beat_sheet" in agent_output:
                        # Encontrar dónde se repite
                        leitmotiv = agent_output.get("leitmotiv", "")
                        specific_corrections.append(
                            f"CAMBIO ESPECÍFICO: En 'leitmotiv', reemplaza '{leitmotiv}' por una frase diferente que no se repita más de 3 veces"
                        )
                elif "clímax" in issue.lower():
                    specific_corrections.append(
                        "CAMBIO ESPECÍFICO: En beat_sheet[7] o beat_sheet[8], marca claramente el punto de máxima tensión en el campo 'conflicto'"
                    )
                elif "resolucion" in issue and "conflicto" in issue:
                    specific_corrections.append(
                        "CAMBIO ESPECÍFICO: En beat_sheet[9], cambia el campo 'resolucion' por 'conflicto'. Solo beat_sheet[10] debe tener 'resolucion'"
                    )
                elif "escalada" in issue.lower() or "tensión" in issue.lower():
                    specific_corrections.append(
                        "CAMBIO ESPECÍFICO: En beat_sheet[4] a beat_sheet[9], asegura que cada 'conflicto' sea progresivamente más intenso"
                    )
        
        elif agent_name == "cuentacuentos" or agent_name.endswith("_cuentacuentos"):
            for issue in issues[:3]:
                if "rima forzada" in issue.lower():
                    # Buscar página específica si se menciona
                    page_match = re.search(r'página (\d+)', issue.lower())
                    if page_match:
                        page_num = page_match.group(1)
                        specific_corrections.append(
                            f"CAMBIO ESPECÍFICO: En paginas_texto['{page_num}'], reescribe los versos para que la rima fluya naturalmente"
                        )
                elif "repetición" in issue.lower():
                    word_match = re.search(r"'([^']+)'", issue)
                    if word_match:
                        word = word_match.group(1)
                        specific_corrections.append(
                            f"CAMBIO ESPECÍFICO: Busca la palabra '{word}' y reemplázala con sinónimos variados"
                        )
        
        # Si no hay instrucciones específicas, dar feedback general
        if not instructions and not specific_corrections:
            instructions.append("- Revisar la calidad general de la salida")
            instructions.append("- Asegurar coherencia con los artefactos previos")
            instructions.append("- Verificar cumplimiento del contrato JSON")
        
        # Combinar instrucciones generales y correcciones específicas
        result = "INSTRUCCIONES DE MEJORA:\n"
        
        if specific_corrections:
            result += "\n🔧 CORRECCIONES ESPECÍFICAS EN EL JSON:\n"
            result += "\n".join(specific_corrections)
            result += "\n\n"
        
        if instructions:
            result += "📝 MEJORAS GENERALES:\n"
            result += "\n".join(instructions)
        
        return result
    
    def should_retry(self, retry_count: int) -> bool:
        """
        Determina si se debe reintentar basado en el contador
        
        Args:
            retry_count: Número de reintentos ya realizados
            
        Returns:
            True si se puede reintentar, False si se alcanzó el límite
        """
        return retry_count < self.max_retries
    
    def validate_output_structure(self, agent_output: Dict[str, Any], agent_name: str) -> Tuple[bool, List[str]]:
        """
        Valida que la estructura de salida cumpla con el contrato esperado
        
        Args:
            agent_output: Salida del agente
            agent_name: Nombre del agente
            
        Returns:
            Tupla con (valid, errors)
        """
        errors = []
        
        # Definir campos requeridos por agente
        required_fields = {
            "director": ["leitmotiv", "beat_sheet", "variantes", "qa"],
            "psicoeducador": ["metas_generales", "mapa_psico_narrativo", "banderas", "qa"],
            "cuentacuentos": ["paginas_texto", "leitmotiv_usado_en", "qa"],
            "editor_claridad": ["paginas_texto_claro", "glosario", "cambios_clave", "qa"],
            "ritmo_rima": ["paginas_texto_pulido", "esquema_rima", "finales_de_verso", "qa"],
            "continuidad": ["character_bible", "continuidad_narrativa", "qa"],
            "diseno_escena": ["prompts_paginas", "anotaciones", "qa"],
            "direccion_arte": ["estilo_global", "color_script", "transiciones", "qa"],
            "sensibilidad": ["riesgos_detectados", "correcciones_sugeridas", "apto_para_ninos", "qa"],
            "portadista": ["titulos", "portada", "qa"],
            "loader": ["loader", "qa"],
            "validador": ["titulo", "paginas", "portada", "loader"]
        }
        
        # Verificar campos requeridos
        if agent_name in required_fields:
            for field in required_fields[agent_name]:
                if field not in agent_output:
                    errors.append(f"Campo requerido '{field}' no encontrado")
        
        # Validaciones específicas por agente
        if agent_name == "cuentacuentos" and "paginas_texto" in agent_output:
            # Verificar que hay exactamente 10 páginas
            paginas = agent_output["paginas_texto"]
            for i in range(1, 11):
                if str(i) not in paginas:
                    errors.append(f"Falta página {i}")
        
        if agent_name == "loader" and "loader" in agent_output:
            # Verificar que hay exactamente 10 mensajes
            if len(agent_output["loader"]) != 10:
                errors.append(f"Se esperan 10 mensajes de loader, se encontraron {len(agent_output['loader'])}")
        
        if agent_name == "validador" and "paginas" in agent_output:
            # Verificar estructura del validador
            paginas = agent_output["paginas"]
            for i in range(1, 11):
                page_key = str(i)
                if page_key not in paginas:
                    errors.append(f"Falta página {i} en salida final")
                elif not isinstance(paginas[page_key], dict):
                    errors.append(f"Página {i} debe ser un diccionario")
                elif "texto" not in paginas[page_key] or "prompt" not in paginas[page_key]:
                    errors.append(f"Página {i} debe tener 'texto' y 'prompt'")
        
        valid = len(errors) == 0
        return valid, errors


# Singleton para reutilizar el checker
_checker_instance = None

def get_quality_checker(agent_qa_thresholds=None) -> QualityGateChecker:
    """
    Obtiene una instancia del quality checker con umbrales opcionales
    
    Args:
        agent_qa_thresholds: Diccionario opcional con umbrales específicos por agente
    
    Returns:
        Instancia de QualityGateChecker
    """
    # No usar singleton cuando hay umbrales específicos
    if agent_qa_thresholds:
        return QualityGateChecker(agent_qa_thresholds)
    
    global _checker_instance
    if _checker_instance is None:
        _checker_instance = QualityGateChecker()
    return _checker_instance