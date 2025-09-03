#!/usr/bin/env python3
"""
Prueba simple de webhook para verificar conectividad
"""

import json
import requests
import time

WEBHOOK_URL = "https://ogegdctdniijmublbmgy.supabase.co/functions/v1/pipeline-webhook"

# Payload mínimo de prueba
payload = {
    "event": "story_error",
    "timestamp": time.time(),
    "data": {
        "story_id": "test-connection-123",
        "status": "error",
        "error": "Prueba de conectividad desde Cuentería"
    }
}

print("Enviando webhook de prueba...")
print(f"URL: {WEBHOOK_URL}")
print(f"Payload: {json.dumps(payload, indent=2)}")

try:
    response = requests.post(
        WEBHOOK_URL,
        json=payload,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "Cuenteria-Test/1.0"
        },
        timeout=10
    )
    
    print(f"\n📡 Status: {response.status_code}")
    print(f"📝 Response: {response.text}")
    
except Exception as e:
    print(f"❌ Error: {e}")