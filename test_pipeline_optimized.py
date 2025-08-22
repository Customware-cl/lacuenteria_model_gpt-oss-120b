#!/usr/bin/env python3
"""
Prueba del pipeline completo con configuraciones optimizadas
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

# Agregar src al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.agent_runner_optimized import OptimizedAgentRunner
from src.config import AGENT_PIPELINE, QUALITY_THRESHOLDS


def run_optimized_pipeline():
    """Ejecuta el pipeline completo con configuraciones optimizadas"""
    
    print("\n" + "="*60)
    print("🚀 PRUEBA DE PIPELINE OPTIMIZADO")
    print("="*60)
    print("Usando configuraciones individuales optimizadas por agente")
    print("Brief: Emilia y el Unicornio")
    print("="*60)
    
    # Crear story_id único
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    story_id = f"optimized_test_{timestamp}"
    
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
    
    # Inicializar runner optimizado
    runner = OptimizedAgentRunner(story_id)
    
    # Estadísticas
    stats = {
        "story_id": story_id,
        "start_time": time.time(),
        "agents": {},
        "retries": {},
        "qa_scores": {},
        "execution_times": {},
        "failures": []
    }
    
    print(f"\n📁 Story ID: {story_id}")
    print(f"📊 Umbral QA mínimo: {QUALITY_THRESHOLDS['min_qa_score']}")
    print(f"🔄 Reintentos máximos: {QUALITY_THRESHOLDS['max_retries']}")
    print("\n" + "-"*60)
    
    # Ejecutar cada agente
    for i, agent_name in enumerate(AGENT_PIPELINE, 1):
        print(f"\n[{i}/{len(AGENT_PIPELINE)}] {agent_name}")
        print("-"*40)
        
        agent_start = time.time()
        retry_count = 0
        success = False
        qa_passed = False
        
        # Intentar hasta max_retries
        while retry_count <= QUALITY_THRESHOLDS['max_retries'] and not qa_passed:
            if retry_count > 0:
                print(f"   🔄 Reintento {retry_count}/{QUALITY_THRESHOLDS['max_retries']}")
            
            result = runner.run(agent_name, retry_count)
            
            if result['success']:
                qa_passed = result.get('qa_passed', True)
                qa_scores = result.get('qa_scores', {})
                qa_avg = qa_scores.get('promedio', 0)
                
                if qa_passed:
                    print(f"   ✅ Completado | QA: {qa_avg:.2f}/5 | Tiempo: {result['execution_time']:.1f}s")
                    success = True
                    break
                else:
                    print(f"   ⚠️ QA bajo: {qa_avg:.2f}/5 (mínimo: {QUALITY_THRESHOLDS['min_qa_score']})")
                    
            else:
                print(f"   ❌ Error: {result.get('error', 'Unknown')[:50]}")
            
            retry_count += 1
            
            if not qa_passed and retry_count <= QUALITY_THRESHOLDS['max_retries']:
                time.sleep(QUALITY_THRESHOLDS.get('retry_delay', 5))
        
        # Guardar estadísticas
        agent_time = time.time() - agent_start
        stats['agents'][agent_name] = {
            'success': success,
            'retries': retry_count - 1,
            'qa_passed': qa_passed,
            'execution_time': agent_time
        }
        
        if success:
            stats['qa_scores'][agent_name] = qa_scores
            stats['execution_times'][agent_name] = result['execution_time']
        else:
            stats['failures'].append(agent_name)
            print(f"   ❌ FALLO DEFINITIVO después de {retry_count} intentos")
    
    # Calcular estadísticas finales
    stats['end_time'] = time.time()
    stats['total_time'] = stats['end_time'] - stats['start_time']
    stats['total_retries'] = sum(a.get('retries', 0) for a in stats['agents'].values())
    
    # Calcular QA promedio
    if stats['qa_scores']:
        all_qa = [scores.get('promedio', 0) for scores in stats['qa_scores'].values()]
        stats['qa_average'] = sum(all_qa) / len(all_qa) if all_qa else 0
    else:
        stats['qa_average'] = 0
    
    # Mostrar resumen
    print("\n" + "="*60)
    print("📊 RESUMEN DE RESULTADOS")
    print("="*60)
    
    print(f"\n⏱️ Tiempo total: {stats['total_time']:.1f} segundos ({stats['total_time']/60:.1f} minutos)")
    print(f"🔄 Reintentos totales: {stats['total_retries']}")
    print(f"📈 QA promedio global: {stats['qa_average']:.2f}/5")
    
    if stats['failures']:
        print(f"❌ Agentes fallidos: {', '.join(stats['failures'])}")
    else:
        print("✅ Todos los agentes completados exitosamente")
    
    # Tabla de resultados por agente
    print("\n📋 Detalle por agente:")
    print(f"{'Agente':<20} {'QA':<8} {'Tiempo':<10} {'Reintentos':<10} {'Estado':<10}")
    print("-"*60)
    
    for agent_name in AGENT_PIPELINE:
        agent_stats = stats['agents'].get(agent_name, {})
        qa_score = stats['qa_scores'].get(agent_name, {}).get('promedio', 0)
        exec_time = stats['execution_times'].get(agent_name, 0)
        retries = agent_stats.get('retries', 0)
        status = "✅" if agent_stats.get('success') else "❌"
        
        print(f"{agent_name:<20} {qa_score:<8.2f} {exec_time:<10.1f} {retries:<10} {status:<10}")
    
    # Comparación con baseline
    print("\n" + "="*60)
    print("📊 COMPARACIÓN CON BASELINE")
    print("="*60)
    
    baseline = {
        "total_time": 791.88,  # 13 minutos del test anterior
        "qa_average": 3.3,
        "total_retries": 14,
        "failures": 6  # Agentes con QA < umbral
    }
    
    improvements = {
        "time": ((baseline['total_time'] - stats['total_time']) / baseline['total_time'] * 100),
        "qa": ((stats['qa_average'] - baseline['qa_average']) / baseline['qa_average'] * 100),
        "retries": ((baseline['total_retries'] - stats['total_retries']) / baseline['total_retries'] * 100),
        "failures": baseline['failures'] - len(stats['failures'])
    }
    
    print(f"\nTiempo:")
    print(f"  Baseline: {baseline['total_time']:.1f}s")
    print(f"  Optimizado: {stats['total_time']:.1f}s")
    print(f"  Mejora: {improvements['time']:+.1f}%")
    
    print(f"\nQA Promedio:")
    print(f"  Baseline: {baseline['qa_average']:.2f}/5")
    print(f"  Optimizado: {stats['qa_average']:.2f}/5")
    print(f"  Mejora: {improvements['qa']:+.1f}%")
    
    print(f"\nReintentos:")
    print(f"  Baseline: {baseline['total_retries']}")
    print(f"  Optimizado: {stats['total_retries']}")
    print(f"  Mejora: {improvements['retries']:+.1f}%")
    
    print(f"\nAgentes Fallidos:")
    print(f"  Baseline: {baseline['failures']}")
    print(f"  Optimizado: {len(stats['failures'])}")
    print(f"  Mejora: -{improvements['failures']} agentes")
    
    # Guardar estadísticas
    stats_file = story_path / "optimization_stats.json"
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Estadísticas guardadas en: {stats_file}")
    
    # Verificar si se generó el cuento completo
    validador_file = story_path / "validador.json"
    if validador_file.exists():
        print("\n✅ CUENTO COMPLETO GENERADO")
        print(f"   Ver en: {validador_file}")
    else:
        print("\n⚠️ Cuento incompleto - revisar fallos")
    
    return stats


if __name__ == "__main__":
    try:
        stats = run_optimized_pipeline()
        
        # Determinar éxito global
        if stats['qa_average'] >= 4.0 and len(stats['failures']) == 0:
            print("\n" + "🎉"*20)
            print("🏆 OPTIMIZACIÓN EXITOSA - Objetivos alcanzados")
            print("🎉"*20)
        elif stats['qa_average'] >= 3.5:
            print("\n✅ Optimización parcialmente exitosa - Mejoras significativas")
        else:
            print("\n⚠️ Optimización requiere más ajustes")
            
    except KeyboardInterrupt:
        print("\n\n❌ Prueba interrumpida por el usuario")
    except Exception as e:
        print(f"\n\n❌ Error en la prueba: {e}")
        import traceback
        traceback.print_exc()