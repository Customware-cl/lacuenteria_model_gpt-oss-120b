#!/usr/bin/env python3
"""
Test de integración completo del webhook con el flujo v2
Verifica que los IDs se usen correctamente y el webhook se envíe con éxito
"""

import json
import requests
import time
import sys
from datetime import datetime

def test_webhook_integration():
    """Prueba el flujo completo con webhook"""
    
    print("🧪 Test de integración del webhook con flujo v2")
    print("="*60)
    
    # Generar un story_id único para el test
    test_story_id = f"test-webhook-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    # Brief de prueba simplificado
    test_brief = {
        "story_id": test_story_id,
        "personajes": ["Luna", "Sol"],
        "historia": "Una historia de amistad entre la luna y el sol",
        "mensaje_a_transmitir": "La amistad supera las diferencias",
        "edad_objetivo": 5,
        "webhook_url": "https://httpbin.org/post",  # Webhook de prueba que siempre responde OK
        "pipeline_version": "v2"
    }
    
    print(f"📖 Story ID: {test_story_id}")
    print(f"🔗 Webhook URL: {test_brief['webhook_url']}")
    print(f"📝 Historia: {test_brief['historia']}")
    print()
    
    # Llamar a la API para crear la historia
    api_url = "http://localhost:5000/api/stories/create"
    
    print("📤 Enviando request a la API...")
    try:
        response = requests.post(
            api_url,
            json=test_brief,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 202:
            print("✅ Historia aceptada para procesamiento")
            result = response.json()
            print(f"   Status: {result.get('status')}")
            print(f"   Message: {result.get('message')}")
            
            # Esperar un poco y verificar el estado
            print("\n⏳ Esperando 5 segundos para verificar estado...")
            time.sleep(5)
            
            # Consultar el estado
            status_url = f"http://localhost:5000/api/stories/{test_story_id}/status"
            status_response = requests.get(status_url)
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                print(f"\n📊 Estado actual:")
                print(f"   Estado: {status_data.get('estado')}")
                print(f"   Paso actual: {status_data.get('paso_actual')}")
                
                # Verificar si hay información del webhook
                if 'webhook_result' in status_data:
                    webhook_result = status_data['webhook_result']
                    print(f"\n🔔 Resultado del webhook:")
                    print(f"   Success: {webhook_result.get('success')}")
                    print(f"   Timestamp: {webhook_result.get('timestamp')}")
                    print(f"   URL: {webhook_result.get('url')}")
                
                # Verificar los logs del webhook
                import os
                from pathlib import Path
                
                # Buscar la carpeta con timestamp
                runs_dir = Path("runs")
                matching_dirs = list(runs_dir.glob(f"*{test_story_id}"))
                
                if matching_dirs:
                    story_dir = matching_dirs[0]
                    webhook_log = story_dir / "logs" / "webhook_completion.log"
                    
                    if webhook_log.exists():
                        print(f"\n📋 Log del webhook encontrado: {webhook_log}")
                        with open(webhook_log, 'r') as f:
                            lines = f.readlines()
                            # Buscar líneas clave
                            for line in lines:
                                if "FINAL RESULT:" in line:
                                    print(f"   {line.strip()}")
                                elif "Status Code:" in line and "200" in line:
                                    print(f"   ✅ Webhook respondió con status 200")
                                elif "story_id" in line and test_story_id in line:
                                    print(f"   ✅ Story ID correcto en el payload")
                    else:
                        print(f"\n⚠️  No se encontró log del webhook")
                else:
                    print(f"\n⚠️  No se encontró carpeta para {test_story_id}")
                    
            else:
                print(f"❌ Error al consultar estado: {status_response.status_code}")
                
        else:
            print(f"❌ Error al crear historia: {response.status_code}")
            print(f"   Respuesta: {response.text[:200]}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Error: No se puede conectar con la API")
        print("   Asegúrate de que el servidor esté corriendo:")
        print("   python3 src/api_server.py")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")

    print("\n" + "="*60)
    print("✨ Test completado")
    print("\nNOTA: Este test usa un webhook de prueba (httpbin.org)")
    print("Para probar con el webhook real de Supabase, actualiza webhook_url en el brief")

if __name__ == "__main__":
    test_webhook_integration()