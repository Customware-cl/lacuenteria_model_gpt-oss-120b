#!/usr/bin/env python3
"""
Prueba completa del pipeline con sistema de feedback QA integrado
"""
import json
import time
import sys
import os
from datetime import datetime
from pathlib import Path
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.agent_runner_optimized import OptimizedAgentRunner
from src.config import AGENT_PIPELINE, QUALITY_THRESHOLDS

def run_complete_pipeline():
    """Ejecuta el pipeline completo con feedback QA"""
    
    print("\n" + "="*70)
    print("🚀 PRUEBA COMPLETA DEL PIPELINE CON FEEDBACK QA")
    print("="*70)
    print("Brief: Emilia y el Unicornio")
    print("Agentes: 12 (pipeline completo)")
    print("QA: Verificador con feedback detallado")
    print("Umbral: 4.0/5 para aprobar")
    print("="*70)
    
    # Crear story_id único
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    story_id = f"complete_test_{timestamp}"
    
    # Crear directorio y brief
    story_path = Path(f"runs/{story_id}")
    story_path.mkdir(parents=True, exist_ok=True)
    
    # Brief de Emilia
    brief = {
        "story_id": story_id,
        "personajes": ["Emilia", "Unicornio"],
        "historia": "Emilia se comunica con un unicornio mágico a través de gestos y descubre que juntos pueden crear luz donde hay oscuridad",
        "mensaje_a_transmitir": "La comunicación va más allá de las palabras",
        "edad_objetivo": 5
    }
    
    # Guardar brief
    with open(story_path / "brief.json", 'w', encoding='utf-8') as f:
        json.dump(brief, f, ensure_ascii=False, indent=2)
    
    # Inicializar runner
    runner = OptimizedAgentRunner(story_id)
    
    # Estadísticas
    stats = {
        "story_id": story_id,
        "start_time": time.time(),
        "agents": {},
        "qa_feedback": {},
        "failures": [],
        "retries": 0,
        "total_problems": 0,
        "total_suggestions": 0
    }
    
    print(f"\n📁 Story ID: {story_id}")
    print(f"📊 Umbral QA: {QUALITY_THRESHOLDS['min_qa_score']}/5")
    print(f"🔄 Reintentos máximos: {QUALITY_THRESHOLDS['max_retries']}")
    print("\n" + "-"*70)
    
    # Ejecutar cada agente
    for i, agent_name in enumerate(AGENT_PIPELINE, 1):
        print(f"\n[{i}/{len(AGENT_PIPELINE)}] {agent_name.upper()}")
        print("-"*50)
        
        agent_start = time.time()
        retry_count = 0
        qa_passed = False
        
        # Intentar hasta max_retries si QA falla
        while retry_count <= QUALITY_THRESHOLDS['max_retries'] and not qa_passed:
            if retry_count > 0:
                print(f"   🔄 Reintento {retry_count}/{QUALITY_THRESHOLDS['max_retries']}")
                stats["retries"] += 1
            
            result = runner.run(agent_name, retry_count)
            
            if result['success']:
                # Leer archivo para obtener feedback QA
                output_file = story_path / f"{agent_name}.json"
                if output_file.exists():
                    with open(output_file, 'r', encoding='utf-8') as f:
                        agent_data = json.load(f)
                    
                    # Extraer evaluación QA
                    if "_qa_evaluation" in agent_data:
                        qa_eval = agent_data["_qa_evaluation"]
                        qa_score = qa_eval.get("promedio", 0)
                        qa_passed = qa_eval.get("pasa_umbral", False)
                        
                        print(f"   📊 QA Score: {qa_score}/5 {'✅' if qa_passed else '❌'}")
                        
                        # Mostrar problemas detectados (primeros 3)
                        problems = qa_eval.get("problemas", [])
                        if problems:
                            print(f"   🔴 Problemas ({len(problems)}):")
                            for p in problems[:3]:
                                print(f"      - {p[:80]}...")
                            stats["total_problems"] += len(problems)
                        
                        # Guardar feedback para análisis
                        stats["qa_feedback"][agent_name] = {
                            "score": qa_score,
                            "passed": qa_passed,
                            "problems_count": len(problems),
                            "problems": problems[:5],
                            "suggestions": qa_eval.get("mejoras", [])[:5]
                        }
                        stats["total_suggestions"] += len(qa_eval.get("mejoras", []))
                        
                        # Tiempo de ejecución
                        exec_time = result.get('execution_time', time.time() - agent_start)
                        print(f"   ⏱️  Tiempo: {exec_time:.1f}s")
                    else:
                        # Sin evaluación QA (validador, critico)
                        qa_passed = True
                        qa_score = 5.0
                        print(f"   ✅ Completado (sin evaluación QA)")
                
                if qa_passed:
                    break
            else:
                print(f"   ❌ Error: {result.get('error', 'Unknown')[:100]}")
                stats["failures"].append(agent_name)
                break
            
            retry_count += 1
            
            if not qa_passed and retry_count <= QUALITY_THRESHOLDS['max_retries']:
                time.sleep(5)  # Esperar antes de reintentar
        
        # Guardar estadísticas del agente
        stats['agents'][agent_name] = {
            'success': qa_passed,
            'retries': retry_count - 1,
            'qa_score': qa_score if 'qa_score' in locals() else 0,
            'execution_time': time.time() - agent_start
        }
        
        if not qa_passed:
            print(f"   ❌ FALLO DEFINITIVO después de {retry_count} intentos")
            stats["failures"].append(agent_name)
    
    # Calcular estadísticas finales
    stats['end_time'] = time.time()
    stats['total_time'] = stats['end_time'] - stats['start_time']
    
    # Resumen
    print("\n" + "="*70)
    print("📊 RESUMEN DE RESULTADOS")
    print("="*70)
    
    # Tiempos
    print(f"\n⏱️  TIEMPOS:")
    print(f"   Total: {stats['total_time']:.1f}s ({stats['total_time']/60:.1f} minutos)")
    print(f"   Promedio por agente: {stats['total_time']/len(AGENT_PIPELINE):.1f}s")
    
    # QA Scores
    print(f"\n📊 CALIDAD (QA):")
    qa_scores = [info.get('qa_score', 0) for info in stats['qa_feedback'].values()]
    if qa_scores:
        print(f"   Promedio QA: {sum(qa_scores)/len(qa_scores):.2f}/5")
        print(f"   Min QA: {min(qa_scores):.2f}/5")
        print(f"   Max QA: {max(qa_scores):.2f}/5")
    
    # Problemas y sugerencias
    print(f"\n🔍 FEEDBACK:")
    print(f"   Problemas detectados: {stats['total_problems']}")
    print(f"   Sugerencias generadas: {stats['total_suggestions']}")
    print(f"   Reintentos totales: {stats['retries']}")
    
    # Agentes problemáticos
    if stats['failures']:
        print(f"\n❌ AGENTES FALLIDOS ({len(stats['failures'])}):")
        for agent in stats['failures']:
            print(f"   - {agent}")
    else:
        print(f"\n✅ Todos los agentes completados")
    
    # Tabla detallada
    print(f"\n📋 DETALLE POR AGENTE:")
    print(f"{'Agente':<20} {'QA':<8} {'Problemas':<12} {'Tiempo':<10} {'Estado':<10}")
    print("-"*70)
    
    for agent_name in AGENT_PIPELINE:
        agent_info = stats['agents'].get(agent_name, {})
        qa_info = stats['qa_feedback'].get(agent_name, {})
        
        qa_score = qa_info.get('score', agent_info.get('qa_score', 0))
        problems = qa_info.get('problems_count', 0)
        exec_time = agent_info.get('execution_time', 0)
        status = "✅" if agent_info.get('success') else "❌"
        
        print(f"{agent_name:<20} {qa_score:<8.2f} {problems:<12} {exec_time:<10.1f} {status:<10}")
    
    # Top 3 problemas más comunes
    print(f"\n🔴 PROBLEMAS MÁS FRECUENTES:")
    all_problems = []
    for qa_info in stats['qa_feedback'].values():
        all_problems.extend(qa_info.get('problems', []))
    
    if all_problems:
        # Contar patrones comunes
        problem_patterns = {
            "repetición": 0,
            "rima": 0,
            "métrica": 0,
            "vacío": 0,
            "inconsistente": 0
        }
        
        for problem in all_problems:
            problem_lower = problem.lower()
            for pattern in problem_patterns:
                if pattern in problem_lower:
                    problem_patterns[pattern] += 1
        
        # Mostrar top 3
        sorted_patterns = sorted(problem_patterns.items(), key=lambda x: x[1], reverse=True)
        for i, (pattern, count) in enumerate(sorted_patterns[:3], 1):
            print(f"   {i}. {pattern.capitalize()}: {count} ocurrencias")
    
    # Guardar estadísticas completas
    stats_file = story_path / "pipeline_stats.json"
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Estadísticas guardadas en: {stats_file}")
    
    # Verificar si se generó el cuento completo
    validador_file = story_path / "validador.json"
    if validador_file.exists():
        print("\n" + "="*70)
        print("✅ CUENTO COMPLETO GENERADO EXITOSAMENTE")
        print(f"   Ver en: {validador_file}")
        print("="*70)
    else:
        print("\n" + "="*70)
        print("⚠️ PIPELINE INCOMPLETO - Revisar fallos arriba")
        print("="*70)
    
    return stats

if __name__ == "__main__":
    try:
        print("\nIniciando prueba completa del pipeline...")
        print("Esto puede tomar 10-15 minutos. Por favor espere...\n")
        
        stats = run_complete_pipeline()
        
        # Evaluación final
        if not stats['failures'] and stats['total_time'] < 600:  # < 10 minutos
            print("\n🎉 PRUEBA EXITOSA - Pipeline estable y funcional")
        elif not stats['failures']:
            print("\n✅ Pipeline completo pero lento - Optimización recomendada")
        else:
            print(f"\n⚠️ Pipeline con fallos - {len(stats['failures'])} agentes fallaron")
            
    except KeyboardInterrupt:
        print("\n\n❌ Prueba interrumpida por el usuario")
    except Exception as e:
        print(f"\n\n❌ Error en la prueba: {e}")
        import traceback
        traceback.print_exc()