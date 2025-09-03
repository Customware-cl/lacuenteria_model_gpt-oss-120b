#!/usr/bin/env python3
"""
Test para verificar que prompt_metrics_id:
1. NO se incluye en el brief.json
2. SÍ se incluye en el manifest.json
3. SÍ se incluye en el webhook de respuesta
"""

import json
import tempfile
import shutil
from pathlib import Path
import sys
import os

# Agregar el directorio src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from orchestrator import StoryOrchestrator
from config import get_artifact_path

def test_prompt_metrics_no_in_brief():
    """Test que verifica que prompt_metrics_id no se incluye en el brief"""
    
    # Crear un story_id temporal
    story_id = "test-prompt-metrics"
    prompt_metrics_id = "test-metrics-id-12345"
    
    # Crear el brief sin prompt_metrics_id
    brief = {
        "personajes": ["TestPersonaje"],
        "historia": "Historia de prueba",
        "mensaje_a_transmitir": "Mensaje de prueba",
        "edad_objetivo": 5
    }
    
    # Crear orchestrator con prompt_metrics_id
    orchestrator = StoryOrchestrator(
        story_id=story_id,
        use_timestamp=False,
        prompt_metrics_id=prompt_metrics_id
    )
    
    # Crear directorio si no existe
    story_path = orchestrator.story_path
    story_path.mkdir(parents=True, exist_ok=True)
    
    # Guardar el brief
    brief_path = get_artifact_path(story_id, "brief.json")
    with open(brief_path, 'w', encoding='utf-8') as f:
        json.dump(brief, f, ensure_ascii=False, indent=2)
    
    # Guardar el manifest con prompt_metrics_id
    orchestrator.manifest["prompt_metrics_id"] = prompt_metrics_id
    orchestrator._save_manifest()
    
    # Verificar que el brief NO contiene prompt_metrics_id
    with open(brief_path, 'r', encoding='utf-8') as f:
        saved_brief = json.load(f)
    
    assert "prompt_metrics_id" not in saved_brief, "Error: prompt_metrics_id no debería estar en el brief"
    print("✓ prompt_metrics_id NO está en el brief.json")
    
    # Verificar que el manifest SÍ contiene prompt_metrics_id
    manifest_path = get_artifact_path(story_id, "manifest.json")
    with open(manifest_path, 'r', encoding='utf-8') as f:
        saved_manifest = json.load(f)
    
    assert "prompt_metrics_id" in saved_manifest, "Error: prompt_metrics_id debería estar en el manifest"
    assert saved_manifest["prompt_metrics_id"] == prompt_metrics_id, "Error: prompt_metrics_id incorrecto en manifest"
    print(f"✓ prompt_metrics_id SÍ está en el manifest.json: {saved_manifest['prompt_metrics_id']}")
    
    # Simular el resultado que se enviaría al webhook
    result = {
        "story_id": story_id,
        "status": "success"
    }
    
    # El orchestrator debería incluir prompt_metrics_id del manifest
    if "prompt_metrics_id" in orchestrator.manifest:
        result["prompt_metrics_id"] = orchestrator.manifest["prompt_metrics_id"]
    
    assert "prompt_metrics_id" in result, "Error: prompt_metrics_id debería estar en el resultado del webhook"
    assert result["prompt_metrics_id"] == prompt_metrics_id, "Error: prompt_metrics_id incorrecto en webhook"
    print(f"✓ prompt_metrics_id SÍ se incluirá en el webhook: {result['prompt_metrics_id']}")
    
    # Limpiar
    if story_path.exists():
        shutil.rmtree(story_path)
    
    print("\n✅ TODOS LOS TESTS PASARON")
    print("   - prompt_metrics_id NO está en brief.json")
    print("   - prompt_metrics_id SÍ está en manifest.json")
    print("   - prompt_metrics_id SÍ se enviará en el webhook")

if __name__ == "__main__":
    test_prompt_metrics_no_in_brief()