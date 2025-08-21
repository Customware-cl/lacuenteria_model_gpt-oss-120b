"""
Consolidador de métricas de agentes para el sistema Cuentería.
Recolecta y agrega estadísticas de los logs de ejecución de los agentes.
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from config import AGENT_PIPELINE, AGENT_TEMPERATURES

logger = logging.getLogger(__name__)


def consolidate_agent_metrics(story_id: str) -> Optional[Dict[str, Any]]:
    """
    Consolida las métricas de todos los agentes ejecutados para una historia.
    
    Args:
        story_id: Identificador de la historia
        
    Returns:
        Dict con métricas consolidadas o None si no hay suficientes datos
    """
    try:
        # Construir path a los logs
        logs_dir = Path(f"runs/{story_id}/logs")
        
        # Verificar si existe el directorio de logs
        if not logs_dir.exists():
            logger.info(f"No se encontró directorio de logs para {story_id}")
            return None
        
        # Recolectar métricas disponibles
        agent_metrics = collect_available_metrics(story_id, logs_dir)
        
        # Si no hay suficientes datos, retornar None
        if len([m for m in agent_metrics if m["disponible"]]) < 3:
            logger.info(f"Datos insuficientes para consolidar métricas de {story_id}")
            return None
        
        # Calcular estadísticas agregadas
        stats = calculate_statistics(agent_metrics)
        
        # Construir respuesta consolidada
        return {
            "resumen_global": stats["resumen"],
            "detalle_agentes": agent_metrics,
            "estadisticas": {
                "temperaturas": stats["temperaturas"],
                "tiempos": stats["tiempos"],
                "qa_scores": stats["qa_scores"]
            },
            "metadata": {
                "fecha_consolidacion": datetime.now().isoformat(),
                "agentes_procesados": stats["agentes_procesados"],
                "agentes_faltantes": stats["agentes_faltantes"]
            }
        }
        
    except Exception as e:
        logger.error(f"Error consolidando métricas para {story_id}: {e}")
        return None


def collect_available_metrics(story_id: str, logs_dir: Path) -> List[Dict[str, Any]]:
    """
    Recolecta las métricas disponibles de cada agente.
    
    Args:
        story_id: Identificador de la historia
        logs_dir: Path al directorio de logs
        
    Returns:
        Lista de métricas por agente
    """
    metrics = []
    
    for agent_name in AGENT_PIPELINE:
        log_file = logs_dir / f"{agent_name}.log"
        
        if log_file.exists():
            log_data = try_read_agent_log(log_file)
            if log_data:
                # Procesar el último intento (puede haber múltiples si hubo reintentos)
                last_attempt = log_data[-1] if isinstance(log_data, list) else log_data
                
                metrics.append({
                    "agente": agent_name,
                    "disponible": True,
                    "temperatura": last_attempt.get("temperature", "N/A"),
                    "temperatura_configurada": AGENT_TEMPERATURES.get(agent_name, 0.7),
                    "tiempo_ejecucion": last_attempt.get("execution_time", "N/A"),
                    "qa_promedio": calculate_qa_average(last_attempt.get("qa_scores", {})),
                    "qa_detalle": last_attempt.get("qa_scores", {}),
                    "reintentos": last_attempt.get("retry_count", 0),
                    "status": last_attempt.get("status", "unknown"),
                    "timestamp": last_attempt.get("timestamp", "N/A")
                })
            else:
                metrics.append({
                    "agente": agent_name,
                    "disponible": False,
                    "nota": "Error al leer log"
                })
        else:
            metrics.append({
                "agente": agent_name,
                "disponible": False,
                "nota": "Log no encontrado"
            })
    
    return metrics


def try_read_agent_log(log_file: Path) -> Optional[Any]:
    """
    Intenta leer un archivo de log de agente.
    
    Args:
        log_file: Path al archivo de log
        
    Returns:
        Contenido del log o None si falla
    """
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"No se pudo leer {log_file}: {e}")
        return None


def calculate_qa_average(qa_scores: Dict[str, Any]) -> Optional[float]:
    """
    Calcula el promedio de los QA scores.
    
    Args:
        qa_scores: Diccionario con scores QA
        
    Returns:
        Promedio de scores o None si no hay datos
    """
    if not qa_scores:
        return None
    
    # El promedio puede venir pre-calculado
    if "promedio" in qa_scores:
        return qa_scores["promedio"]
    
    # Si no, calcularlo de los scores individuales
    numeric_scores = []
    for key, value in qa_scores.items():
        if isinstance(value, (int, float)) and key != "promedio":
            numeric_scores.append(value)
    
    if numeric_scores:
        return round(sum(numeric_scores) / len(numeric_scores), 2)
    
    return None


def calculate_statistics(agent_metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calcula estadísticas agregadas de las métricas.
    
    Args:
        agent_metrics: Lista de métricas por agente
        
    Returns:
        Diccionario con estadísticas calculadas
    """
    # Filtrar solo agentes con datos disponibles
    available_metrics = [m for m in agent_metrics if m["disponible"]]
    
    # Extraer valores numéricos
    tiempos = [m["tiempo_ejecucion"] for m in available_metrics 
               if isinstance(m.get("tiempo_ejecucion"), (int, float))]
    
    temperaturas = [m["temperatura"] for m in available_metrics 
                    if isinstance(m.get("temperatura"), (int, float))]
    
    qa_promedios = [m["qa_promedio"] for m in available_metrics 
                    if isinstance(m.get("qa_promedio"), (int, float))]
    
    reintentos_totales = sum([m.get("reintentos", 0) for m in available_metrics 
                              if isinstance(m.get("reintentos"), int)])
    
    # Calcular distribución de QA scores
    qa_distribucion = {}
    for m in available_metrics:
        promedio = m.get("qa_promedio")
        if promedio:
            score_int = int(promedio)
            qa_distribucion[str(score_int)] = qa_distribucion.get(str(score_int), 0) + 1
    
    # Identificar agentes con QA bajo umbral (< 4.0)
    agentes_bajo_umbral = [
        m["agente"] for m in available_metrics 
        if isinstance(m.get("qa_promedio"), (int, float)) and m["qa_promedio"] < 4.0
    ]
    
    # Construir estadísticas
    stats = {
        "resumen": {
            "total_agentes": len(AGENT_PIPELINE),
            "agentes_ejecutados": len(available_metrics),
            "tiempo_total_segundos": round(sum(tiempos), 2) if tiempos else None,
            "promedio_qa_global": round(sum(qa_promedios) / len(qa_promedios), 2) if qa_promedios else None,
            "reintentos_totales": reintentos_totales,
            "tasa_exito_primera": round(
                (len(available_metrics) - reintentos_totales) / len(available_metrics) * 100, 1
            ) if available_metrics else 0
        },
        "temperaturas": {
            "min": round(min(temperaturas), 2) if temperaturas else None,
            "max": round(max(temperaturas), 2) if temperaturas else None,
            "promedio": round(sum(temperaturas) / len(temperaturas), 2) if temperaturas else None,
            "rango_configurado": [
                min(AGENT_TEMPERATURES.values()),
                max(AGENT_TEMPERATURES.values())
            ]
        },
        "tiempos": {
            "min": round(min(tiempos), 2) if tiempos else None,
            "max": round(max(tiempos), 2) if tiempos else None,
            "promedio": round(sum(tiempos) / len(tiempos), 2) if tiempos else None,
            "total": round(sum(tiempos), 2) if tiempos else None,
            "agente_mas_lento": identify_slowest_agent(available_metrics),
            "agente_mas_rapido": identify_fastest_agent(available_metrics)
        },
        "qa_scores": {
            "distribucion": qa_distribucion,
            "agentes_bajo_umbral": agentes_bajo_umbral,
            "mejor_agente": identify_best_qa_agent(available_metrics),
            "agente_menor_qa": identify_worst_qa_agent(available_metrics)
        },
        "agentes_procesados": len(available_metrics),
        "agentes_faltantes": [m["agente"] for m in agent_metrics if not m["disponible"]]
    }
    
    return stats


def identify_slowest_agent(metrics: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Identifica el agente más lento."""
    valid_times = [(m["agente"], m["tiempo_ejecucion"]) for m in metrics 
                   if isinstance(m.get("tiempo_ejecucion"), (int, float))]
    
    if valid_times:
        slowest = max(valid_times, key=lambda x: x[1])
        return {"agente": slowest[0], "tiempo": round(slowest[1], 2)}
    return None


def identify_fastest_agent(metrics: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Identifica el agente más rápido."""
    valid_times = [(m["agente"], m["tiempo_ejecucion"]) for m in metrics 
                   if isinstance(m.get("tiempo_ejecucion"), (int, float))]
    
    if valid_times:
        fastest = min(valid_times, key=lambda x: x[1])
        return {"agente": fastest[0], "tiempo": round(fastest[1], 2)}
    return None


def identify_best_qa_agent(metrics: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Identifica el agente con mejor QA score."""
    valid_qa = [(m["agente"], m["qa_promedio"]) for m in metrics 
                if isinstance(m.get("qa_promedio"), (int, float))]
    
    if valid_qa:
        best = max(valid_qa, key=lambda x: x[1])
        return {"agente": best[0], "qa_promedio": round(best[1], 2)}
    return None


def identify_worst_qa_agent(metrics: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Identifica el agente con menor QA score."""
    valid_qa = [(m["agente"], m["qa_promedio"]) for m in metrics 
                if isinstance(m.get("qa_promedio"), (int, float))]
    
    if valid_qa:
        worst = min(valid_qa, key=lambda x: x[1])
        return {"agente": worst[0], "qa_promedio": round(worst[1], 2)}
    return None