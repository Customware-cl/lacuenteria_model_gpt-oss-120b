#!/usr/bin/env python3
"""
Prueba rápida de un agente para verificar que los tokens se guardan en logs
"""
import json
import sys
import os
from pathlib import Path

# Agregar src al path
sys.path.append(str(Path(__file__).parent / "src"))

from agent_runner import AgentRunner
from config import get_story_path, get_artifact_path

def test_agent_with_tokens():
    """Ejecuta el agente director y verifica que se guarden los tokens"""
    
    print("=" * 60)
    print("PRUEBA DE REGISTRO DE TOKENS EN AGENTE")
    print("=" * 60)
    
    # Crear un story_id de prueba
    story_id = "test-tokens-001"
    story_path = get_story_path(story_id)
    
    print(f"\n1. Creando historia de prueba: {story_id}")
    
    # Crear directorio y brief
    story_path.mkdir(parents=True, exist_ok=True)
    logs_dir = story_path / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    # Crear brief de prueba
    brief = {
        "personajes": ["María"],
        "historia": "María aprende a compartir sus juguetes",
        "mensaje_a_transmitir": "La importancia de compartir",
        "edad_objetivo": 4
    }
    
    brief_path = get_artifact_path(story_id, "brief.json")
    with open(brief_path, 'w', encoding='utf-8') as f:
        json.dump(brief, f, ensure_ascii=False, indent=2)
    
    print("   Brief creado ✅")
    
    # Ejecutar agente director
    print("\n2. Ejecutando agente director...")
    runner = AgentRunner(story_id)
    result = runner.run_agent("director")
    
    if result["status"] == "success":
        print("   Agente ejecutado exitosamente ✅")
        
        # Leer el log del director
        log_path = story_path / "logs" / "director.log"
        if log_path.exists():
            with open(log_path, 'r', encoding='utf-8') as f:
                logs = json.load(f)
            
            print("\n3. Contenido del log:")
            if logs and len(logs) > 0:
                log_entry = logs[-1]  # Última entrada
                
                print(f"   - Timestamp: {log_entry.get('timestamp', 'N/A')}")
                print(f"   - Temperatura: {log_entry.get('temperature', 'N/A')}")
                print(f"   - Max tokens: {log_entry.get('max_tokens', 'N/A')}")
                print(f"   - Tiempo ejecución: {log_entry.get('execution_time', 'N/A')}s")
                
                if "tokens_consumed" in log_entry:
                    tokens = log_entry["tokens_consumed"]
                    print(f"\n   ✅ TOKENS REGISTRADOS:")
                    print(f"   - Prompt tokens: {tokens.get('prompt_tokens', 'N/A')}")
                    print(f"   - Completion tokens: {tokens.get('completion_tokens', 'N/A')}")
                    print(f"   - Total tokens: {tokens.get('total_tokens', 'N/A')}")
                else:
                    print(f"\n   ⚠️ NO HAY INFORMACIÓN DE TOKENS EN EL LOG")
        else:
            print("   ❌ No se encontró archivo de log")
    else:
        print(f"   ❌ Error ejecutando agente: {result.get('error', 'Unknown')}")
    
    # Verificar manifest
    print("\n4. Verificando manifest.json...")
    manifest_path = get_artifact_path(story_id, "manifest.json")
    if manifest_path.exists():
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        
        if "configuracion_modelo" in manifest:
            config = manifest["configuracion_modelo"]
            print("   ✅ Configuración del modelo en manifest:")
            print(f"   - Modelo: {config.get('modelo', 'N/A')}")
            print(f"   - Endpoint: {config.get('endpoint', 'N/A')}")
            print(f"   - Timeout: {config.get('timeout', 'N/A')}s")
            print(f"   - Default temperature: {config.get('default_temperature', 'N/A')}")
            print(f"   - Default max_tokens: {config.get('default_max_tokens', 'N/A')}")
        else:
            print("   ⚠️ No hay configuración del modelo en manifest")
    
    print("\n" + "=" * 60)
    print("PRUEBA COMPLETADA")
    print("=" * 60)

if __name__ == "__main__":
    test_agent_with_tokens()