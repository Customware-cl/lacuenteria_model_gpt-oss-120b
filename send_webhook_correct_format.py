#!/usr/bin/env python3
"""
Script para enviar el webhook con el formato correcto
"""

import json
import requests
import time
from pathlib import Path

# Datos de la historia
STORY_ID = "20250903-010240-c0d344dc-f99f-475a-b105-dd0b67260142"
ORIGINAL_STORY_ID = "c0d344dc-f99f-475a-b105-dd0b67260142"
WEBHOOK_URL = "https://ogegdctdniijmublbmgy.supabase.co/functions/v1/pipeline-webhook"
PROMPT_METRICS_ID = "05b451c3-7452-4cd3-8970-837c647d263b"
ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9nZWdkY3Rkbmlpam11YmxibWd5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDY4OTcyNjMsImV4cCI6MjA2MjQ3MzI2M30.v7RTmoetmlJMOQfYdu_AmIgsYwm6JvW3eQVTlNeO0hk"

# Leer el resultado validado
story_path = Path(f"runs/{STORY_ID}")
with open(story_path / "12_validador.json", 'r', encoding='utf-8') as f:
    cuento = json.load(f)

# Preparar el payload - formato simplificado que espera el webhook
webhook_payload = {
    "story_id": ORIGINAL_STORY_ID,
    "status": "success",
    "result": cuento,  # Cambiar "cuento" por "result"
    "prompt_metrics_id": PROMPT_METRICS_ID,
    "metadata": {
        "pipeline_version": "v1",
        "processing_time": 1064,
        "qa_passed": True,
        "warnings": []
    }
}

print(f"Enviando webhook a: {WEBHOOK_URL}")
print(f"Story ID: {ORIGINAL_STORY_ID}")
print(f"Prompt Metrics ID: {PROMPT_METRICS_ID}")
print(f"Payload keys: {list(webhook_payload.keys())}")

# Enviar el webhook con autorización
try:
    response = requests.post(
        WEBHOOK_URL,
        json=webhook_payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {ANON_KEY}",
            "User-Agent": "Cuenteria/1.0"
        },
        timeout=30
    )
    
    print(f"\nRespuesta del webhook:")
    print(f"Status Code: {response.status_code}")
    print(f"Response Body: {response.text[:1000] if response.text else 'No response body'}")
    
    if response.status_code in [200, 201, 202, 204]:
        print("\n✅ Webhook enviado exitosamente")
        if response.text:
            try:
                response_json = response.json()
                print(f"Respuesta del servidor: {json.dumps(response_json, indent=2, ensure_ascii=False)}")
            except:
                pass
    else:
        print(f"\n⚠️ Webhook devolvió código {response.status_code}")
        
except requests.exceptions.Timeout:
    print("\n❌ Error: Timeout al enviar webhook")
except requests.exceptions.ConnectionError as e:
    print(f"\n❌ Error de conexión: {e}")
except Exception as e:
    print(f"\n❌ Error inesperado: {e}")