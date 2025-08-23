#!/usr/bin/env python3
"""
Test del verificador_qa con feedback detallado
"""
import json
import sys
import os
from datetime import datetime
from pathlib import Path

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.agent_runner_optimized import OptimizedAgentRunner

def test_qa_feedback():
    print("\n" + "="*60)
    print("🔍 TEST DE VERIFICADOR QA CON FEEDBACK")
    print("="*60)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    story_id = f"qa_feedback_{timestamp}"
    
    story_path = Path(f"runs/{story_id}")
    story_path.mkdir(parents=True, exist_ok=True)
    
    # Brief simple
    brief = {
        "story_id": story_id,
        "personajes": ["Emilia", "Unicornio"],
        "historia": "Emilia y un unicornio crean luz donde hay oscuridad",
        "mensaje_a_transmitir": "La comunicación trasciende las palabras",
        "edad_objetivo": 5
    }
    
    with open(story_path / "brief.json", 'w', encoding='utf-8') as f:
        json.dump(brief, f, ensure_ascii=False, indent=2)
    
    runner = OptimizedAgentRunner(story_id)
    
    # Probar con cuentacuentos que genera contenido completo pero con problemas
    test_agents = ["director", "psicoeducador", "cuentacuentos"]
    
    for agent in test_agents:
        print(f"\n{'='*40}")
        print(f"Ejecutando: {agent}")
        print('='*40)
        
        result = runner.run(agent)
        
        if result['success']:
            # Leer el archivo generado para ver el feedback QA
            output_file = story_path / f"{agent}.json"
            if output_file.exists():
                with open(output_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Mostrar evaluación QA si existe
                if "_qa_evaluation" in data:
                    qa_eval = data["_qa_evaluation"]
                    
                    print(f"\n📊 EVALUACIÓN QA de {agent}:")
                    print(f"   Score promedio: {qa_eval['promedio']}/5")
                    print(f"   Pasa umbral (4.0): {'✅' if qa_eval['pasa_umbral'] else '❌'}")
                    
                    if qa_eval['problemas']:
                        print(f"\n   🔴 Problemas detectados ({len(qa_eval['problemas'])}):")
                        for i, problema in enumerate(qa_eval['problemas'][:5], 1):
                            print(f"      {i}. {problema}")
                    
                    if qa_eval['mejoras']:
                        print(f"\n   💡 Mejoras sugeridas ({len(qa_eval['mejoras'])}):")
                        for i, mejora in enumerate(qa_eval['mejoras'][:5], 1):
                            print(f"      {i}. {mejora}")
                    
                    if qa_eval['justificacion']:
                        print(f"\n   📝 Justificación:")
                        print(f"      {qa_eval['justificacion']}")
                    
                    # Mostrar scores por métrica
                    if qa_eval['scores']:
                        print(f"\n   📈 Scores por métrica:")
                        for metrica, score in qa_eval['scores'].items():
                            if metrica != "promedio":
                                print(f"      - {metrica}: {score}/5")
                else:
                    print(f"\n⚠️ No hay evaluación QA para {agent}")
                    print(f"   QA score básico: {data.get('qa', {}).get('promedio', 'N/A')}")
        else:
            print(f"❌ Error: {result.get('error', 'Unknown')[:100]}")
    
    print("\n" + "="*60)
    print("✅ TEST COMPLETADO - Revisa el feedback detallado arriba")
    print("="*60)

if __name__ == "__main__":
    test_qa_feedback()