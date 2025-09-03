#!/usr/bin/env python3
"""
Test para verificar que los agentes se pueden saltar correctamente
"""
import sys
import json
from pathlib import Path
from datetime import datetime
sys.path.append(str(Path(__file__).parent))
from src.orchestrator import StoryOrchestrator

def test_agentes_saltados():
    """Prueba el flujo con agentes deshabilitados"""
    
    # Crear un ID único para el test
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    story_id = f"test-toggles-{timestamp}"
    
    print(f"\n🧪 Test de agentes saltados")
    print(f"Story ID: {story_id}")
    print("-" * 50)
    
    # Brief de prueba
    brief = {
        "personajes": ["Ana", "Luis"],
        "historia": "Dos amigos encuentran un mapa del tesoro",
        "mensaje_a_transmitir": "La importancia de la amistad",
        "edad_objetivo": 5
    }
    
    # Crear orquestador con pipeline v2
    orchestrator = StoryOrchestrator(
        story_id=story_id,
        mode_verificador_qa=True,
        pipeline_version='v2'
    )
    
    print("\n📋 Configuración de toggles:")
    config_path = Path("flujo/v2/config.json")
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    toggles = config.get('agent_toggles', {})
    for agent, enabled in toggles.items():
        status = "✅ Habilitado" if enabled else "❌ Deshabilitado"
        print(f"  {agent}: {status}")
    
    print("\n🚀 Iniciando procesamiento...")
    
    # Solo ejecutar primeros 6 agentes para test rápido
    pipeline_corto = [
        "01_director",
        "02_psicoeducador", 
        "03_cuentacuentos",
        "04_editor_claridad",  # Deshabilitado
        "05_ritmo_rima",       # Deshabilitado
        "06_continuidad"
    ]
    
    # Modificar temporalmente el pipeline
    orchestrator.agent_runner.version_config['pipeline'] = pipeline_corto
    
    # Ejecutar el procesamiento
    result = orchestrator.process_story(brief)
    
    print("\n📊 Resultados:")
    
    # Verificar qué archivos se generaron
    story_path = Path(f"runs/{story_id}/outputs/agents")
    if story_path.exists():
        files = list(story_path.glob("*.json"))
        print(f"\n📁 Archivos generados en outputs/agents:")
        for file in sorted(files):
            print(f"  - {file.name}")
    
    # Verificar manifest para ver qué agentes se saltaron
    manifest_path = Path(f"runs/{story_id}/manifest.json")
    if manifest_path.exists():
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        print(f"\n⏱️ Timestamps de ejecución:")
        for agent, info in manifest.get('timestamps', {}).items():
            if isinstance(info, dict) and info.get('skipped'):
                print(f"  {agent}: ⏭️ SALTADO (usando {info.get('source_file')})")
            elif isinstance(info, dict):
                print(f"  {agent}: ✅ Ejecutado")
    
    print("\n✅ Test completado")
    return result

if __name__ == "__main__":
    test_agentes_saltados()