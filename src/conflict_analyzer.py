"""
Sistema de análisis de conflictos entre prompts y evaluaciones QA
Detecta patrones de fallo y genera recomendaciones específicas
"""
import json
import logging
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)


class ConflictAnalyzer:
    """Analiza conflictos entre prompts de agentes y evaluaciones del verificador QA"""
    
    def __init__(self, version: str = 'v2'):
        self.version = version
        self.dashboard_path = Path(__file__).parent.parent / f'flujo/{version}/qa_conflict_dashboard.json'
        self.dashboard = self._load_dashboard()
        
        # Mapeo de issues comunes a patrones
        self.issue_patterns = {
            # Director
            r"repetición.*leitmotiv.*(\d+).*veces": "leitmotiv_repetition_conflict",
            r"falta.*campo.*resolu[ción|cion]": "missing_resolution_field",
            r"conflicto.*interno": "internal_conflict_not_visual",
            
            # Cuentacuentos
            r"metro.*inconsistente": "metro_not_specified",
            r"rima.*forzada": "forced_rhyme",
            r"repetición.*excesiva.*palabra": "word_repetition_excessive",
            r"(\d+).*sílabas": "syllable_count_issue",
            
            # Editor claridad
            r"falta.*glosario": "missing_glossary_field",
            r"ausencia.*cambios_clave": "missing_changes_field",
            r"lenguaje.*abstracto": "abstract_language",
            
            # Ritmo rima
            r"rima.*pobre": "poor_rhyme_quality",
            r"inversión.*sintáctica": "syntactic_inversion",
            r"terminación.*repetida": "repeated_endings",
            
            # General
            r"vocabulario.*complejo": "complex_vocabulary",
            r"coherencia": "coherence_issue",
            r"ambigüedad|ambiguo": "ambiguity_issue"
        }
        
        # Recomendaciones predefinidas por patrón
        self.pattern_recommendations = {
            "leitmotiv_repetition_conflict": "Especificar número exacto de repeticiones (ej: 'exactamente 3 veces')",
            "missing_resolution_field": "Aclarar estructura JSON: conflicto para páginas 1-9, resolución solo para página 10",
            "internal_conflict_not_visual": "Especificar que todos los conflictos deben ser externos y visualizables",
            "metro_not_specified": "Agregar restricción: 'cada verso debe tener 8-10 sílabas'",
            "forced_rhyme": "Agregar: 'prioriza naturalidad sobre rima perfecta, acepta asonancia'",
            "word_repetition_excessive": "Agregar: 'evita repetir la misma palabra más de 2 veces por página'",
            "syllable_count_issue": "Especificar conteo exacto de sílabas por verso",
            "missing_glossary_field": "Actualizar JSON contract para incluir campo 'glosario'",
            "missing_changes_field": "Actualizar JSON contract para incluir campo 'cambios_clave'",
            "abstract_language": "Agregar: 'usa lenguaje concreto y visual, evita abstracciones'",
            "poor_rhyme_quality": "Especificar tipos de rima aceptables y ejemplos a evitar",
            "syntactic_inversion": "Agregar: 'mantén orden natural de las palabras, evita inversiones'",
            "repeated_endings": "Agregar: 'varía las terminaciones, máximo 2 repeticiones del mismo final'",
            "complex_vocabulary": "Especificar nivel de vocabulario para la edad objetivo",
            "coherence_issue": "Agregar verificación de coherencia con artefactos previos",
            "ambiguity_issue": "Agregar: 'cada descripción debe ser inequívoca y clara'"
        }
    
    def _load_dashboard(self) -> Dict[str, Any]:
        """Carga el dashboard existente o crea uno nuevo"""
        if self.dashboard_path.exists():
            try:
                with open(self.dashboard_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error cargando dashboard: {e}")
        
        # Dashboard inicial vacío
        return {
            "version": self.version,
            "last_updated": datetime.now().isoformat(),
            "total_conflicts_analyzed": 0,
            "conflict_patterns": {},
            "agent_conflicts": {},
            "prompt_improvements": {}
        }
    
    def analyze_qa_failure(self, 
                          agent_name: str,
                          qa_issues: List[str],
                          qa_scores: Dict[str, float],
                          story_id: str,
                          agent_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Analiza un fallo de QA y extrae patrones de conflicto
        
        Args:
            agent_name: Nombre del agente que falló
            qa_issues: Lista de problemas detectados por el verificador
            qa_scores: Scores QA obtenidos
            story_id: ID de la historia
            agent_prompt: Prompt del agente (opcional, para análisis profundo)
        
        Returns:
            Análisis con patrones detectados y recomendaciones
        """
        analysis = {
            "agent": agent_name,
            "story_id": story_id,
            "patterns_detected": [],
            "recommendations": [],
            "prompt_conflicts": []
        }
        
        # Analizar cada issue
        for issue in qa_issues:
            issue_lower = issue.lower()
            
            # Buscar patrones conocidos
            for pattern_regex, pattern_id in self.issue_patterns.items():
                if re.search(pattern_regex, issue_lower):
                    pattern_info = {
                        "pattern_id": pattern_id,
                        "issue_text": issue,
                        "recommendation": self.pattern_recommendations.get(pattern_id, "Revisar prompt")
                    }
                    
                    # Si tenemos el prompt, buscar la línea específica
                    if agent_prompt:
                        conflicting_line = self._find_conflicting_line(agent_prompt, pattern_id)
                        if conflicting_line:
                            pattern_info["prompt_line"] = conflicting_line
                    
                    analysis["patterns_detected"].append(pattern_info)
                    
                    # Actualizar dashboard
                    self._update_pattern_count(agent_name, pattern_id, issue, story_id)
                    
                    # Agregar recomendación si no está ya
                    if pattern_info["recommendation"] not in analysis["recommendations"]:
                        analysis["recommendations"].append(pattern_info["recommendation"])
                    
                    break  # Un issue puede matchear solo un patrón
        
        # Si no se detectaron patrones conocidos, registrar como nuevo
        if not analysis["patterns_detected"] and qa_issues:
            for issue in qa_issues:
                self._register_new_pattern(agent_name, issue, story_id)
                analysis["patterns_detected"].append({
                    "pattern_id": "unknown",
                    "issue_text": issue,
                    "recommendation": "Patrón nuevo detectado - requiere análisis manual"
                })
        
        # Guardar dashboard actualizado
        self._save_dashboard()
        
        return analysis
    
    def _find_conflicting_line(self, prompt: str, pattern_id: str) -> Optional[str]:
        """Busca la línea específica del prompt que causa el conflicto"""
        # Mapeo de patrones a keywords en el prompt
        prompt_keywords = {
            "leitmotiv_repetition_conflict": ["3-4 veces", "3–4 veces", "repetible"],
            "missing_resolution_field": ["resolucion", "resolución", "JSON contract"],
            "internal_conflict_not_visual": ["conflicto", "imagen", "visual"],
            "metro_not_specified": ["verso", "AABB", "rima"],
            "forced_rhyme": ["rima", "AABB", "perfecto"],
            "word_repetition_excessive": ["repetición", "palabra", "evita"],
            "syllable_count_issue": ["sílaba", "verso", "metro"],
            "missing_glossary_field": ["glosario", "JSON", "contract"],
            "missing_changes_field": ["cambios_clave", "JSON", "contract"]
        }
        
        keywords = prompt_keywords.get(pattern_id, [])
        if not keywords:
            return None
        
        # Buscar líneas que contengan los keywords
        lines = prompt.split('.')
        for line in lines:
            if any(keyword in line for keyword in keywords):
                return line.strip()
        
        return None
    
    def _update_pattern_count(self, agent_name: str, pattern_id: str, issue: str, story_id: str):
        """Actualiza el contador de un patrón en el dashboard"""
        if agent_name not in self.dashboard["conflict_patterns"]:
            self.dashboard["conflict_patterns"][agent_name] = {}
        
        if pattern_id not in self.dashboard["conflict_patterns"][agent_name]:
            self.dashboard["conflict_patterns"][agent_name][pattern_id] = {
                "count": 0,
                "first_seen": datetime.now().isoformat(),
                "typical_issue": issue,
                "recommendation": self.pattern_recommendations.get(pattern_id, ""),
                "stories_affected": []
            }
        
        pattern_data = self.dashboard["conflict_patterns"][agent_name][pattern_id]
        pattern_data["count"] += 1
        pattern_data["last_seen"] = datetime.now().isoformat()
        
        if story_id not in pattern_data["stories_affected"]:
            pattern_data["stories_affected"].append(story_id)
        
        # Actualizar contador total
        self.dashboard["total_conflicts_analyzed"] += 1
        self.dashboard["last_updated"] = datetime.now().isoformat()
    
    def _register_new_pattern(self, agent_name: str, issue: str, story_id: str):
        """Registra un patrón nuevo no reconocido"""
        if agent_name not in self.dashboard["conflict_patterns"]:
            self.dashboard["conflict_patterns"][agent_name] = {}
        
        # Usar hash del issue como ID temporal
        pattern_id = f"new_{hash(issue) % 10000}"
        
        if pattern_id not in self.dashboard["conflict_patterns"][agent_name]:
            self.dashboard["conflict_patterns"][agent_name][pattern_id] = {
                "count": 1,
                "first_seen": datetime.now().isoformat(),
                "typical_issue": issue,
                "recommendation": "Requiere análisis manual",
                "stories_affected": [story_id],
                "status": "unresolved"
            }
    
    def analyze_agent_conflicts(self, manifest: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analiza conflictos entre agentes basado en el manifest completo
        
        Args:
            manifest: Manifest completo de una historia con devoluciones
        
        Returns:
            Análisis de conflictos inter-agentes
        """
        conflicts = {}
        devoluciones = manifest.get("devoluciones", [])
        
        if len(devoluciones) < 2:
            return conflicts
        
        # Analizar secuencias de fallos
        for i in range(len(devoluciones) - 1):
            current = devoluciones[i]
            next_dev = devoluciones[i + 1]
            
            # Si dos agentes consecutivos fallan, puede haber conflicto
            conflict_key = f"{current['paso']}->{next_dev['paso']}"
            
            # Buscar patrones de conflicto conocidos
            if self._is_related_failure(current, next_dev):
                if conflict_key not in self.dashboard["agent_conflicts"]:
                    self.dashboard["agent_conflicts"][conflict_key] = {
                        "count": 0,
                        "description": f"Fallo en cadena: {current['paso']} produce output que {next_dev['paso']} no puede procesar",
                        "typical_scores": {
                            current["paso"]: current.get("qa_scores", {}).get("promedio", 0),
                            next_dev["paso"]: next_dev.get("qa_scores", {}).get("promedio", 0)
                        },
                        "stories_affected": []
                    }
                
                self.dashboard["agent_conflicts"][conflict_key]["count"] += 1
                
                story_id = manifest.get("story_id", "unknown")
                if story_id not in self.dashboard["agent_conflicts"][conflict_key]["stories_affected"]:
                    self.dashboard["agent_conflicts"][conflict_key]["stories_affected"].append(story_id)
        
        self._save_dashboard()
        return conflicts
    
    def _is_related_failure(self, dev1: Dict, dev2: Dict) -> bool:
        """Determina si dos fallos están relacionados"""
        # Heurística: si el segundo agente depende del primero y ambos fallan
        # con scores bajos, probablemente hay conflicto
        score1 = dev1.get("qa_scores", {}).get("promedio", 5)
        score2 = dev2.get("qa_scores", {}).get("promedio", 5)
        
        return score1 < 3.5 and score2 < 3.5
    
    def get_recommendations_for_retry(self, agent_name: str) -> List[str]:
        """
        Obtiene recomendaciones específicas para un agente basadas en patrones conocidos
        
        Args:
            agent_name: Nombre del agente
        
        Returns:
            Lista de recomendaciones para inyectar en el retry
        """
        recommendations = []
        
        if agent_name not in self.dashboard["conflict_patterns"]:
            return recommendations
        
        # Obtener los 3 patrones más frecuentes para este agente
        patterns = self.dashboard["conflict_patterns"][agent_name]
        sorted_patterns = sorted(patterns.items(), key=lambda x: x[1]["count"], reverse=True)[:3]
        
        for pattern_id, pattern_data in sorted_patterns:
            if pattern_data["count"] >= 2:  # Solo si ha ocurrido al menos 2 veces
                rec = pattern_data.get("recommendation", "")
                if rec and rec not in recommendations:
                    recommendations.append(f"⚠️ Problema frecuente detectado: {rec}")
        
        return recommendations
    
    def generate_improvement_report(self) -> str:
        """Genera un reporte de mejoras sugeridas para los prompts"""
        report = []
        report.append("# Reporte de Análisis de Conflictos QA")
        report.append(f"Fecha: {datetime.now().isoformat()}")
        report.append(f"Total de conflictos analizados: {self.dashboard['total_conflicts_analyzed']}")
        report.append("")
        
        # Patrones por agente
        report.append("## Patrones de Conflicto por Agente")
        for agent, patterns in self.dashboard["conflict_patterns"].items():
            if patterns:
                report.append(f"\n### {agent}")
                sorted_patterns = sorted(patterns.items(), key=lambda x: x[1]["count"], reverse=True)
                
                for pattern_id, data in sorted_patterns:
                    report.append(f"- **{pattern_id}** (ocurrencias: {data['count']})")
                    report.append(f"  - Issue típico: {data['typical_issue']}")
                    report.append(f"  - Recomendación: {data['recommendation']}")
                    report.append(f"  - Historias afectadas: {len(data['stories_affected'])}")
        
        # Conflictos entre agentes
        if self.dashboard["agent_conflicts"]:
            report.append("\n## Conflictos Entre Agentes")
            for conflict_key, data in self.dashboard["agent_conflicts"].items():
                report.append(f"- **{conflict_key}** (ocurrencias: {data['count']})")
                report.append(f"  - {data['description']}")
        
        # Mejoras prioritarias
        report.append("\n## Mejoras Prioritarias Sugeridas")
        priority_improvements = self._calculate_priority_improvements()
        for agent, improvement in priority_improvements[:5]:
            report.append(f"- **{agent}**: {improvement}")
        
        return "\n".join(report)
    
    def _calculate_priority_improvements(self) -> List[Tuple[str, str]]:
        """Calcula las mejoras más prioritarias basadas en frecuencia"""
        improvements = []
        
        for agent, patterns in self.dashboard["conflict_patterns"].items():
            for pattern_id, data in patterns.items():
                if data["count"] >= 3:  # Alta prioridad si ocurre 3+ veces
                    improvements.append((
                        agent,
                        f"{data['recommendation']} (afecta {data['count']} historias)"
                    ))
        
        return sorted(improvements, key=lambda x: x[1], reverse=True)
    
    def _save_dashboard(self):
        """Guarda el dashboard actualizado"""
        try:
            # Crear directorio si no existe
            self.dashboard_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.dashboard_path, 'w', encoding='utf-8') as f:
                json.dump(self.dashboard, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Dashboard guardado en {self.dashboard_path}")
        except Exception as e:
            logger.error(f"Error guardando dashboard: {e}")


# Singleton para reutilizar el analyzer
_analyzer_instance = None

def get_conflict_analyzer(version: str = 'v2') -> ConflictAnalyzer:
    """
    Obtiene una instancia singleton del conflict analyzer
    
    Args:
        version: Versión del pipeline
    
    Returns:
        Instancia de ConflictAnalyzer
    """
    global _analyzer_instance
    if _analyzer_instance is None or _analyzer_instance.version != version:
        _analyzer_instance = ConflictAnalyzer(version)
    return _analyzer_instance