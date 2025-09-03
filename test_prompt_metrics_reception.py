#!/usr/bin/env python3
"""
Script para probar si prompt_metrics_id se está recibiendo correctamente
"""

import json
import requests
from datetime import datetime

# URL del API
API_URL = "http://localhost:5000"

def test_with_prompt_metrics():
    """Prueba envío con prompt_metrics_id"""
    
    print("="*60)
    print("TEST: Recepción de prompt_metrics_id")
    print("="*60)
    
    # Generar IDs únicos
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    story_id = f"test-pm-{timestamp}"
    prompt_metrics_id = f"pm_{timestamp}_test789"
    
    # Payload con prompt_metrics_id
    payload = {
        "story_id": story_id,
        "personajes": ["Test", "Metrics"],
        "historia": "Historia de prueba para verificar prompt_metrics_id",
        "mensaje_a_transmitir": "Verificación técnica",
        "edad_objetivo": 3,
        "pipeline_version": "v2",
        "prompt_metrics_id": prompt_metrics_id,
        "webhook_url": "https://webhook.site/test"
    }
    
    print(f"\n📤 Enviando payload:")
    print(json.dumps(payload, indent=2))
    
    # Enviar request
    response = requests.post(
        f"{API_URL}/api/stories/create",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"\n📥 Respuesta: {response.status_code}")
    print(response.json())
    
    if response.status_code == 202:
        # Esperar un segundo y verificar archivos
        import time
        time.sleep(2)
        
        # Buscar la carpeta creada
        import glob
        pattern = f"/home/ubuntu/cuenteria/runs/{story_id}-*"
        folders = glob.glob(pattern)
        
        if folders:
            folder = folders[0]
            print(f"\n📁 Carpeta creada: {folder}")
            
            # Verificar brief.json
            brief_path = f"{folder}/brief.json"
            try:
                with open(brief_path, 'r') as f:
                    brief = json.load(f)
                print(f"\n📋 Brief.json:")
                print(json.dumps(brief, indent=2))
                
                if 'prompt_metrics_id' in brief:
                    print(f"\n✅ prompt_metrics_id ENCONTRADO en brief: {brief['prompt_metrics_id']}")
                else:
                    print(f"\n❌ prompt_metrics_id NO ENCONTRADO en brief")
                    
            except Exception as e:
                print(f"\n⚠️ Error leyendo brief: {e}")
                
            # Verificar manifest.json
            manifest_path = f"{folder}/manifest.json"
            try:
                with open(manifest_path, 'r') as f:
                    manifest = json.load(f)
                
                if 'prompt_metrics_id' in manifest:
                    print(f"\n✅ prompt_metrics_id ENCONTRADO en manifest: {manifest['prompt_metrics_id']}")
                else:
                    print(f"\n❌ prompt_metrics_id NO ENCONTRADO en manifest")
                    
            except Exception as e:
                print(f"\n⚠️ Error leyendo manifest: {e}")
        else:
            print(f"\n❌ No se encontró carpeta para {story_id}")
    
    return story_id

if __name__ == "__main__":
    # Verificar servidor
    try:
        health = requests.get(f"{API_URL}/health", timeout=2)
        print(f"🟢 Servidor activo: {health.status_code}")
    except:
        print("🔴 Servidor no responde")
        exit(1)
    
    # Ejecutar test
    test_with_prompt_metrics()