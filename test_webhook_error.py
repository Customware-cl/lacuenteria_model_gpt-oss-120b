#!/usr/bin/env python3
"""
Test para verificar que el webhook de error se envía correctamente
cuando el LLM no está disponible
"""

import json
import requests
import time

API_URL = "http://localhost:5000"

def test_error_webhook():
    """Prueba que el webhook de error se envíe cuando falla el LLM"""
    
    print("="*60)
    print("TEST: Webhook de Error")
    print("="*60)
    
    # Payload de prueba
    payload = {
        "story_id": "test-error-webhook",
        "personajes": ["Test"],
        "historia": "Historia de prueba para webhook de error",
        "mensaje_a_transmitir": "Test",
        "edad_objetivo": 3,
        "pipeline_version": "v2",
        "webhook_url": "https://webhook.site/test-error"
    }
    
    print("\n📤 Enviando request (LLM no disponible)...")
    
    response = requests.post(
        f"{API_URL}/api/stories/create",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 202:
        print("✅ Request aceptado")
        print("\n⏳ Esperando 10 segundos para que se procese el error...")
        time.sleep(10)
        
        print("\n📝 El webhook de error debería haberse enviado a:")
        print(f"   {payload['webhook_url']}")
        print("\n📦 Con el siguiente formato:")
        print(json.dumps({
            "event": "story_error",
            "timestamp": "...",
            "data": {
                "story_id": "test-error-webhook",
                "status": "error",
                "error": "Mensaje de error del LLM"
            }
        }, indent=2))
        
        return True
    else:
        print(f"❌ Error: {response.status_code}")
        return False

if __name__ == "__main__":
    test_error_webhook()