#!/usr/bin/env python3
"""
Prueba rápida de estabilidad - solo 3 agentes
"""
import json
import sys
import os
from datetime import datetime
from pathlib import Path

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.agent_runner_optimized import OptimizedAgentRunner

def quick_test():
    print("\n🚀 PRUEBA RÁPIDA DE ESTABILIDAD (3 agentes)")
    print("="*50)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    story_id = f"quick_{timestamp}"
    
    story_path = Path(f"runs/{story_id}")
    story_path.mkdir(parents=True, exist_ok=True)
    
    brief = {
        "story_id": story_id,
        "personajes": ["Emilia", "Unicornio"],
        "historia": "Emilia y un unicornio crean luz juntos",
        "mensaje_a_transmitir": "La comunicación trasciende las palabras",
        "edad_objetivo": 5
    }
    
    with open(story_path / "brief.json", 'w', encoding='utf-8') as f:
        json.dump(brief, f, ensure_ascii=False, indent=2)
    
    runner = OptimizedAgentRunner(story_id)
    
    test_agents = ["director", "psicoeducador", "cuentacuentos"]
    
    for i, agent in enumerate(test_agents, 1):
        print(f"\n[{i}/3] Ejecutando {agent}...")
        result = runner.run(agent)
        
        if result['success']:
            file = story_path / f"{agent}.json"
            if file.exists():
                print(f"   ✅ {agent}.json creado ({file.stat().st_size} bytes)")
                
                # Verificar dependencias
                if agent == "psicoeducador":
                    if (story_path / "director.json").exists():
                        print(f"   ✅ Dependencia director.json OK")
                elif agent == "cuentacuentos":
                    for dep in ["director.json", "psicoeducador.json"]:
                        if (story_path / dep).exists():
                            print(f"   ✅ Dependencia {dep} OK")
            else:
                print(f"   ❌ Archivo no creado")
                return False
        else:
            print(f"   ❌ Error: {result.get('error', 'Unknown')[:80]}")
            return False
    
    print("\n" + "="*50)
    print("✅ PIPELINE ESTABLE - Dependencias funcionando")
    return True

if __name__ == "__main__":
    success = quick_test()
    exit(0 if success else 1)