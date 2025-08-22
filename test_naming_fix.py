#!/usr/bin/env python3
"""
Prueba rápida del fix de nomenclatura - solo primeros 3 agentes
"""
import json
import sys
import os
from datetime import datetime
from pathlib import Path

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.agent_runner_optimized import OptimizedAgentRunner

def test_naming_fix():
    print("\n" + "="*60)
    print("🔍 PRUEBA DE FIX DE NOMENCLATURA")
    print("="*60)
    
    # Crear story_id único
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    story_id = f"test_naming_{timestamp}"
    
    # Crear directorio y brief
    story_path = Path(f"runs/{story_id}")
    story_path.mkdir(parents=True, exist_ok=True)
    
    # Brief de Emilia
    brief = {
        "story_id": story_id,
        "personajes": ["Emilia", "Unicornio"],
        "historia": "Emilia se comunica con un unicornio mágico",
        "mensaje_a_transmitir": "La comunicación va más allá de las palabras",
        "edad_objetivo": 5
    }
    
    # Guardar brief
    with open(story_path / "brief.json", 'w', encoding='utf-8') as f:
        json.dump(brief, f, ensure_ascii=False, indent=2)
    
    # Inicializar runner
    runner = OptimizedAgentRunner(story_id)
    
    # Probar solo primeros 3 agentes
    test_agents = ["director", "psicoeducador", "cuentacuentos"]
    
    for agent_name in test_agents:
        print(f"\n🔄 Ejecutando {agent_name}...")
        result = runner.run(agent_name)
        
        if result['success']:
            # Verificar archivo generado
            expected_file = story_path / f"{agent_name}.json"
            if expected_file.exists():
                print(f"   ✅ Archivo generado correctamente: {agent_name}.json")
                
                # Verificar que las dependencias se pueden cargar
                if agent_name == "psicoeducador":
                    director_file = story_path / "director.json"
                    if director_file.exists():
                        print(f"   ✅ Dependencia encontrada: director.json")
                    else:
                        print(f"   ❌ Dependencia NO encontrada: director.json")
                        
                elif agent_name == "cuentacuentos":
                    deps_ok = True
                    for dep in ["director.json", "psicoeducador.json"]:
                        dep_file = story_path / dep
                        if dep_file.exists():
                            print(f"   ✅ Dependencia encontrada: {dep}")
                        else:
                            print(f"   ❌ Dependencia NO encontrada: {dep}")
                            deps_ok = False
                    
                    if deps_ok:
                        print("   ✅ TODAS las dependencias resueltas correctamente")
            else:
                print(f"   ❌ Archivo NO generado: {agent_name}.json")
        else:
            print(f"   ❌ Error: {result.get('error', 'Unknown')}")
    
    # Listar archivos generados
    print(f"\n📁 Archivos en {story_path}:")
    for f in sorted(story_path.glob("*.json")):
        print(f"   - {f.name}")
    
    print("\n" + "="*60)
    print("✅ PRUEBA DE FIX DE NOMENCLATURA COMPLETADA")
    print("="*60)

if __name__ == "__main__":
    test_naming_fix()