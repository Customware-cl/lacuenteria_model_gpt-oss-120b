#!/usr/bin/env python3
"""
Script de prueba para validar los dos modos de verificación QA:
1. mode_verificador_qa=True: Usa el verificador_qa riguroso
2. mode_verificador_qa=False: Usa autoevaluación (más rápido, menos estricto)
"""

import json
import sys
import time
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from agent_runner_optimized import OptimizedAgentRunner
from config import get_artifact_path

def test_single_agent(story_id: str, agent_name: str, mode_verificador: bool):
    """
    Prueba un agente individual con el modo de verificación especificado
    """
    print(f"\n{'='*60}")
    print(f"Probando {agent_name} con mode_verificador_qa={mode_verificador}")
    print(f"{'='*60}")
    
    # Crear runner con el modo especificado
    runner = OptimizedAgentRunner(story_id, mode_verificador_qa=mode_verificador)
    
    # Ejecutar el agente
    start_time = time.time()
    result = runner.run(agent_name)
    execution_time = time.time() - start_time
    
    # Mostrar resultados
    if result["success"]:
        qa_eval = result.get("output", {}).get("_qa_evaluation", {})
        evaluator_type = qa_eval.get("evaluator", "unknown")
        promedio = qa_eval.get("promedio", 0)
        pasa_umbral = qa_eval.get("pasa_umbral", False)
        
        print(f"✅ Éxito en {execution_time:.2f}s")
        print(f"📊 Evaluador usado: {evaluator_type}")
        print(f"📈 Score promedio: {promedio}/5")
        print(f"🎯 Pasa umbral: {'SÍ' if pasa_umbral else 'NO'}")
        
        if evaluator_type == "verificador_qa":
            # Mostrar detalles del verificador_qa
            problemas = qa_eval.get("problemas", [])
            if problemas:
                print(f"⚠️  Problemas detectados:")
                for p in problemas[:3]:
                    print(f"   - {p}")
        elif evaluator_type == "self_evaluation":
            # Mostrar detalles de autoevaluación
            scores = qa_eval.get("scores", {})
            print(f"📋 Scores detallados:")
            for key, value in scores.items():
                if key != "promedio":
                    print(f"   - {key}: {value}/5")
    else:
        print(f"❌ Error: {result.get('error', 'Unknown error')}")
    
    return result

def compare_modes():
    """
    Compara ambos modos de verificación con el mismo agente
    """
    print("\n" + "="*80)
    print("COMPARACIÓN DE MODOS DE VERIFICACIÓN QA")
    print("="*80)
    
    # Crear brief de prueba
    brief = {
        "personajes": ["Luna", "Estrella mágica"],
        "historia": "Luna encuentra una estrella que le enseña a brillar con luz propia",
        "mensaje_a_transmitir": "La confianza en uno mismo",
        "edad_objetivo": 4
    }
    
    # Guardar brief
    story_id = "test_verificador_modes"
    story_path = Path(f"runs/{story_id}")
    story_path.mkdir(parents=True, exist_ok=True)
    
    brief_path = get_artifact_path(story_id, "00_brief.json")
    with open(brief_path, 'w', encoding='utf-8') as f:
        json.dump(brief, f, ensure_ascii=False, indent=2)
    
    # Probar director con ambos modos
    print("\n🔬 Probando agente DIRECTOR con ambos modos...")
    
    # Modo 1: Con verificador_qa
    print("\n--- MODO 1: CON VERIFICADOR_QA (Riguroso) ---")
    result1 = test_single_agent(story_id, "director", mode_verificador=True)
    
    # Modo 2: Con autoevaluación
    print("\n--- MODO 2: CON AUTOEVALUACIÓN (Rápido) ---")
    result2 = test_single_agent(story_id, "director", mode_verificador=False)
    
    # Comparación
    print("\n" + "="*80)
    print("RESUMEN COMPARATIVO")
    print("="*80)
    
    if result1["success"] and result2["success"]:
        qa1 = result1["output"].get("_qa_evaluation", {})
        qa2 = result2["output"].get("_qa_evaluation", {})
        
        print(f"{'Aspecto':<30} {'Verificador QA':<20} {'Autoevaluación':<20}")
        print("-"*70)
        print(f"{'Evaluador':<30} {qa1.get('evaluator', 'N/A'):<20} {qa2.get('evaluator', 'N/A'):<20}")
        print(f"{'Score promedio':<30} {qa1.get('promedio', 0):<20.1f} {qa2.get('promedio', 0):<20.1f}")
        print(f"{'Pasa umbral':<30} {str(qa1.get('pasa_umbral', False)):<20} {str(qa2.get('pasa_umbral', False)):<20}")
        print(f"{'Problemas detectados':<30} {len(qa1.get('problemas', [])):<20} {len(qa2.get('problemas', [])):<20}")
        
        print("\n📊 Conclusiones:")
        print("- Verificador QA: Más riguroso, detecta más problemas, scores más bajos")
        print("- Autoevaluación: Más permisivo, más rápido, scores más altos")
        print("- Recomendación: Usar verificador_qa para producción, autoevaluación para desarrollo")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Prueba los modos de verificación QA")
    parser.add_argument("--mode", choices=["verificador", "auto", "compare"], 
                       default="compare",
                       help="Modo a probar: verificador, auto, o compare (default)")
    parser.add_argument("--agent", default="director",
                       help="Agente a probar (default: director)")
    
    args = parser.parse_args()
    
    if args.mode == "compare":
        compare_modes()
    else:
        story_id = f"test_{args.mode}_{int(time.time())}"
        
        # Crear brief mínimo
        brief = {
            "personajes": ["Test"],
            "historia": "Historia de prueba",
            "mensaje_a_transmitir": "Mensaje de prueba",
            "edad_objetivo": 4
        }
        
        story_path = Path(f"runs/{story_id}")
        story_path.mkdir(parents=True, exist_ok=True)
        
        brief_path = get_artifact_path(story_id, "00_brief.json")
        with open(brief_path, 'w', encoding='utf-8') as f:
            json.dump(brief, f, ensure_ascii=False, indent=2)
        
        mode_verificador = (args.mode == "verificador")
        test_single_agent(story_id, args.agent, mode_verificador)
    
    print("\n✅ Prueba completada")