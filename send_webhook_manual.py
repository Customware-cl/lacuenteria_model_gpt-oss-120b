#!/usr/bin/env python3
"""
Script para enviar manualmente el webhook de una historia completada
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

# Leer el resultado validado
story_path = Path(f"runs/{STORY_ID}")
with open(story_path / "12_validador.json", 'r', encoding='utf-8') as f:
    cuento = json.load(f)

# Preparar el payload del webhook
webhook_payload = {
    "event": "story_complete",
    "timestamp": time.time(),
    "data": {
        "story_id": ORIGINAL_STORY_ID,
        "status": "success",
        "cuento": cuento,
        "prompt_metrics_id": PROMPT_METRICS_ID,
        "metadata": {
            "pipeline_version": "v1",
            "processing_time": 1064,  # ~17 minutos según timestamps
            "qa_passed": True,
            "warnings": []
        }
    }
}

print(f"Enviando webhook a: {WEBHOOK_URL}")
print(f"Story ID: {ORIGINAL_STORY_ID}")
print(f"Prompt Metrics ID: {PROMPT_METRICS_ID}")

# Enviar el webhook
try:
    response = requests.post(
        WEBHOOK_URL,
        json=webhook_payload,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "Cuenteria/1.0"
        },
        timeout=30
    )
    
    print(f"\nRespuesta del webhook:")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text[:500] if response.text else 'No response body'}")
    
    if response.status_code in [200, 201, 202, 204]:
        print("\n✅ Webhook enviado exitosamente")
    else:
        print(f"\n⚠️ Webhook devolvió código {response.status_code}")
        
except requests.exceptions.Timeout:
    print("\n❌ Error: Timeout al enviar webhook")
except requests.exceptions.ConnectionError as e:
    print(f"\n❌ Error de conexión: {e}")
except Exception as e:
    print(f"\n❌ Error inesperado: {e}")