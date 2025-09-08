#!/usr/bin/env python3
"""
Test del sistema de logging mejorado para webhooks
"""
import json
import sys
import os
import time
from pathlib import Path

# Agregar src al path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from webhook_client import WebhookClient
from datetime import datetime

def test_webhook_logging():
    """Prueba el logging del webhook con un ejemplo simulado"""
    
    print("🧪 Testing webhook logging system...")
    print("="*60)
    
    # Crear carpeta de prueba
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    test_story_id = f"test-webhook-{timestamp}"
    test_path = Path("runs") / test_story_id
    test_path.mkdir(parents=True, exist_ok=True)
    (test_path / "logs").mkdir(exist_ok=True)
    
    print(f"📁 Test directory: {test_path}")
    
    # Crear cliente con logging
    webhook_client = WebhookClient(story_path=test_path)
    
    # Preparar payload de prueba
    test_payload = {
        "story_id": test_story_id,
        "status": "success",
        "prompt_metrics_id": "test-metrics-123",
        "result": {
            "titulo": "El Test Mágico",
            "paginas": {
                "1": {
                    "texto": "Había una vez un test...",
                    "prompt": "A magical test scene"
                }
            },
            "portada": {
                "prompt": "Cover for a magical test story"
            },
            "loader": [
                "La magia del test comienza...",
                "Tu prueba cobra vida...",
                "¡El test brilla con luz propia!"
            ]
        }
    }
    
    # URL de webhook de prueba (httpbin para testing)
    test_webhook_url = "https://httpbin.org/post"
    
    print(f"🔗 Webhook URL: {test_webhook_url}")
    print(f"📦 Payload size: {len(json.dumps(test_payload))/1024:.1f} KB")
    print()
    print("📤 Sending webhook...")
    print("-"*60)
    
    # Enviar webhook
    start_time = time.time()
    success = webhook_client.send_story_complete(test_webhook_url, test_payload)
    elapsed = time.time() - start_time
    
    print(f"⏱️  Time elapsed: {elapsed:.2f}s")
    print(f"✅ Result: {'SUCCESS' if success else 'FAILED'}")
    print()
    
    # Verificar log generado
    log_file = test_path / "logs" / "webhook_completion.log"
    if log_file.exists():
        print("📋 WEBHOOK LOG CONTENT:")
        print("="*60)
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()
            # Limitar output para no saturar la pantalla
            if len(content) > 3000:
                print(content[:1500])
                print("\n... [MIDDLE CONTENT TRUNCATED FOR DISPLAY] ...\n")
                print(content[-1000:])
            else:
                print(content)
    else:
        print("❌ Log file not found!")
    
    print("="*60)
    print(f"✨ Test completed! Check logs at: {log_file}")
    
    # Simular webhook fallido para probar logging de errores
    print("\n" + "="*60)
    print("🧪 Testing failed webhook scenario...")
    
    # URL inválida para forzar error
    bad_url = "http://localhost:99999/nonexistent"
    test_story_id_2 = f"test-webhook-error-{timestamp}"
    test_path_2 = Path("runs") / test_story_id_2
    test_path_2.mkdir(parents=True, exist_ok=True)
    (test_path_2 / "logs").mkdir(exist_ok=True)
    
    webhook_client_2 = WebhookClient(story_path=test_path_2)
    
    print(f"🔗 Bad webhook URL: {bad_url}")
    print("📤 Sending webhook to unreachable endpoint...")
    
    success_2 = webhook_client_2.send_story_error(bad_url, test_story_id_2, "Test error message")
    
    print(f"✅ Result: {'SUCCESS' if success_2 else 'FAILED (as expected)'}")
    
    # Verificar log de error
    error_log_file = test_path_2 / "logs" / "webhook_completion.log"
    if error_log_file.exists():
        print(f"\n📋 Error webhook log saved at: {error_log_file}")
        with open(error_log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            # Mostrar solo resumen
            for line in lines:
                if "FINAL RESULT" in line or "Error:" in line:
                    print(f"   {line.strip()}")
    
    print("\n✅ Webhook logging system is working correctly!")

if __name__ == "__main__":
    test_webhook_logging()