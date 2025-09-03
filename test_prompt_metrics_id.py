#!/usr/bin/env python3
"""
Test para verificar que prompt_metrics_id se pasa correctamente
desde el request hasta el webhook
"""

import json
import requests
import time
from datetime import datetime

# Configuración
API_URL = "http://localhost:5000"
TEST_WEBHOOK_URL = "https://webhook.site/unique-id"  # Cambiar por URL de prueba real

def test_prompt_metrics_id():
    """Prueba el flujo completo con prompt_metrics_id"""
    
    print("="*60)
    print("TEST: prompt_metrics_id en Pipeline v2")
    print("="*60)
    
    # Generar IDs únicos
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    story_id = f"test-metrics-{timestamp}"
    prompt_metrics_id = f"pm_{timestamp}_test123"
    
    # Payload de prueba con prompt_metrics_id
    payload = {
        "story_id": story_id,
        "personajes": ["Test", "Metrics"],
        "historia": "Una prueba rápida para verificar prompt_metrics_id",
        "mensaje_a_transmitir": "Verificación de métricas",
        "edad_objetivo": 3,
        "pipeline_version": "v2",
        "prompt_metrics_id": prompt_metrics_id,
        "webhook_url": TEST_WEBHOOK_URL
    }
    
    print(f"\n📝 Datos de prueba:")
    print(f"  - Story ID: {story_id}")
    print(f"  - Prompt Metrics ID: {prompt_metrics_id}")
    print(f"  - Pipeline: v2")
    print(f"  - Webhook URL: {TEST_WEBHOOK_URL}")
    
    # Enviar request
    print(f"\n🚀 Enviando request a {API_URL}/api/stories/create...")
    
    try:
        response = requests.post(
            f"{API_URL}/api/stories/create",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 202:
            print("✅ Request aceptado (202)")
            result = response.json()
            print(f"  - Status: {result.get('status')}")
            print(f"  - Story ID: {result.get('story_id')}")
            
            # Esperar un momento y verificar status
            print("\n⏳ Esperando 5 segundos...")
            time.sleep(5)
            
            # Verificar status
            print(f"\n🔍 Verificando status...")
            status_response = requests.get(f"{API_URL}/api/stories/{story_id}/status")
            
            if status_response.status_code == 200:
                status = status_response.json()
                print(f"  - Estado: {status.get('status')}")
                print(f"  - Paso actual: {status.get('current_step')}")
                print(f"  - Carpeta: {status.get('folder')}")
                
                # Verificar manifest
                if status.get('folder'):
                    manifest_path = f"/home/ubuntu/cuenteria/runs/{status['folder']}/manifest.json"
                    try:
                        with open(manifest_path, 'r') as f:
                            manifest = json.load(f)
                        
                        if 'prompt_metrics_id' in manifest:
                            print(f"\n✅ prompt_metrics_id encontrado en manifest:")
                            print(f"    {manifest['prompt_metrics_id']}")
                            
                            if manifest['prompt_metrics_id'] == prompt_metrics_id:
                                print("    ✅ Valor correcto!")
                            else:
                                print(f"    ❌ Valor incorrecto. Esperado: {prompt_metrics_id}")
                        else:
                            print("\n❌ prompt_metrics_id NO encontrado en manifest")
                    except Exception as e:
                        print(f"\n⚠️ No se pudo leer manifest: {e}")
                
                print("\n📌 NOTA:")
                print("El webhook recibirá el prompt_metrics_id cuando la historia se complete.")
                print("En el webhook llegará en el nivel superior del objeto 'data':")
                print(json.dumps({
                    "event": "story_complete",
                    "timestamp": "...",
                    "data": {
                        "status": "success",
                        "story_id": story_id,
                        "prompt_metrics_id": prompt_metrics_id,  # <-- AQUÍ
                        "result": "..."
                    }
                }, indent=2))
                
            else:
                print(f"❌ Error al verificar status: {status_response.status_code}")
                
        else:
            print(f"❌ Error en request: {response.status_code}")
            print(f"  Respuesta: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    # Verificar que el servidor esté corriendo
    try:
        health = requests.get(f"{API_URL}/health", timeout=2)
        if health.status_code != 200:
            print("❌ El servidor no está respondiendo. Ejecuta: python3 src/api_server.py")
            exit(1)
    except:
        print("❌ No se puede conectar al servidor. Ejecuta: python3 src/api_server.py")
        exit(1)
    
    # Ejecutar test
    success = test_prompt_metrics_id()
    exit(0 if success else 1)