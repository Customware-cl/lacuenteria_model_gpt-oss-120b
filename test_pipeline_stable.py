#!/usr/bin/env python3
"""
Prueba de estabilidad del pipeline con fixes aplicados
Solo ejecuta primeros 6 agentes para verificar que las dependencias funcionan
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
from src.config import QUALITY_THRESHOLDS

def test_pipeline_stability():
    """Prueba de estabilidad con primeros 6 agentes"""
    
    print("\n" + "="*60)
    print("🔬 PRUEBA DE ESTABILIDAD DEL PIPELINE")
    print("="*60)
    print("Probando primeros 6 agentes con nueva nomenclatura")
    print("Brief: Emilia y el Unicornio")
    print("="*60)
    
    # Crear story_id único
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    story_id = f"stable_test_{timestamp}"
    
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
    
    # Agentes a probar (primeros 6)
    test_agents = [
        "director",
        "psicoeducador", 
        "cuentacuentos",
        "editor_claridad",
        "ritmo_rima",
        "continuidad"
    ]
    
    results = {}
    all_success = True
    
    print(f"\n📁 Story ID: {story_id}")
    print("-"*60)
    
    for i, agent_name in enumerate(test_agents, 1):
        print(f"\n[{i}/{len(test_agents)}] {agent_name}")
        print("-"*40)
        
        start_time = time.time()
        result = runner.run(agent_name)
        execution_time = time.time() - start_time
        
        if result['success']:
            qa_scores = result.get('qa_scores', {})
            qa_avg = qa_scores.get('promedio', 0)
            
            # Verificar archivo generado
            expected_file = story_path / f"{agent_name}.json"
            if expected_file.exists():
                file_size = expected_file.stat().st_size
                print(f"   ✅ Archivo generado: {agent_name}.json ({file_size} bytes)")
                print(f"   📊 QA Score: {qa_avg:.2f}/5")
                print(f"   ⏱️  Tiempo: {execution_time:.1f}s")
                
                # Verificar dependencias específicas
                if agent_name == "psicoeducador":
                    if (story_path / "director.json").exists():
                        print(f"   ✅ Dependencia verificada: director.json")
                    else:
                        print(f"   ❌ FALLO: Dependencia no encontrada")
                        all_success = False
                        
                elif agent_name == "continuidad":
                    deps_ok = True
                    for dep in ["ritmo_rima.json", "brief.json"]:
                        if (story_path / dep).exists():
                            print(f"   ✅ Dependencia verificada: {dep}")
                        else:
                            print(f"   ❌ FALLO: Dependencia {dep} no encontrada")
                            deps_ok = False
                            all_success = False
                    
                results[agent_name] = {
                    'success': True,
                    'qa_score': qa_avg,
                    'time': execution_time,
                    'file_size': file_size
                }
            else:
                print(f"   ❌ FALLO: Archivo no generado")
                all_success = False
                results[agent_name] = {'success': False}
        else:
            print(f"   ❌ Error: {result.get('error', 'Unknown')[:100]}")
            all_success = False
            results[agent_name] = {'success': False, 'error': result.get('error')}
    
    # Resumen
    print("\n" + "="*60)
    print("📊 RESUMEN DE RESULTADOS")
    print("="*60)
    
    # Listar todos los archivos generados
    print("\n📁 Archivos generados:")
    for f in sorted(story_path.glob("*.json")):
        size = f.stat().st_size
        print(f"   - {f.name:25} ({size:,} bytes)")
    
    # Tabla de resultados
    print("\n📋 Resultados por agente:")
    print(f"{'Agente':<20} {'Estado':<10} {'QA':<8} {'Tiempo':<10}")
    print("-"*50)
    
    for agent_name in test_agents:
        r = results.get(agent_name, {})
        status = "✅" if r.get('success') else "❌"
        qa = f"{r.get('qa_score', 0):.2f}" if r.get('success') else "N/A"
        time_str = f"{r.get('time', 0):.1f}s" if r.get('success') else "N/A"
        print(f"{agent_name:<20} {status:<10} {qa:<8} {time_str:<10}")
    
    # Verificación final
    print("\n" + "="*60)
    if all_success:
        print("✅ PRUEBA EXITOSA - Pipeline estable con nueva nomenclatura")
        print("   Todas las dependencias se resolvieron correctamente")
    else:
        print("❌ PRUEBA FALLIDA - Revisar errores arriba")
    print("="*60)
    
    return all_success, results

if __name__ == "__main__":
    try:
        success, results = test_pipeline_stability()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Prueba interrumpida por el usuario")
        exit(1)
    except Exception as e:
        print(f"\n\n❌ Error en la prueba: {e}")
        import traceback
        traceback.print_exc()
        exit(1)