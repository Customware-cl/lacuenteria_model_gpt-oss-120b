#!/usr/bin/env python3
"""
Script para enviar el resultado del cuento 6909686d-252f-4627-bdf6-8d0f8003f92e al webhook
"""
import json
import sys
import os
from pathlib import Path
from datetime import datetime

# Agregar src al path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from webhook_client import WebhookClient

def send_existing_story_webhook():
    """Envía el resultado de una historia ya procesada al webhook"""
    
    # IDs de la historia
    original_story_id = "6909686d-252f-4627-bdf6-8d0f8003f92e"
    timestamped_id = "20250903-023820-6909686d-252f-4627-bdf6-8d0f8003f92e"
    story_path = Path("runs") / timestamped_id
    
    print(f"📚 Enviando resultado del cuento: {original_story_id}")
    print(f"📁 Carpeta: {story_path}")
    print("="*60)
    
    # Verificar que existe
    if not story_path.exists():
        print(f"❌ Error: No se encuentra la carpeta {story_path}")
        return False
    
    # Leer el resultado final (validador)
    validador_path = story_path / "12_validador.json"
    if not validador_path.exists():
        print(f"❌ Error: No se encuentra el archivo {validador_path}")
        return False
    
    with open(validador_path, 'r', encoding='utf-8') as f:
        story_result = json.load(f)
    
    # Leer manifest para obtener webhook URL y otros datos
    manifest_path = story_path / "manifest.json"
    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)
    
    webhook_url = manifest.get("webhook_url")
    if not webhook_url:
        print("❌ Error: No hay webhook_url en el manifest")
        return False
    
    print(f"🔗 Webhook URL: {webhook_url}")
    print(f"📊 Estado del cuento: {manifest.get('estado')}")
    
    # Verificar si hay prompt_metrics_id
    prompt_metrics_id = manifest.get("prompt_metrics_id")
    if prompt_metrics_id:
        print(f"📈 Prompt Metrics ID: {prompt_metrics_id}")
    else:
        print("⚠️  No hay prompt_metrics_id en el manifest")
        prompt_metrics_id = None  # Será None si no existe
    
    # Preparar el payload completo como lo espera el webhook
    # IMPORTANTE: Usar el ID original, no el timestamped
    webhook_payload = {
        "status": "success",
        "story_id": original_story_id,  # Usar ID original para que coincida con la BD
        "result": story_result,
        "qa_scores": manifest.get("qa_historial", {}),
        "processing_time": None,  # No calculable desde aquí
        "metadata": {
            "retries": manifest.get("reintentos", {}),
            "warnings": manifest.get("devoluciones", [])
        }
    }
    
    # Agregar prompt_metrics_id si existe
    if prompt_metrics_id:
        webhook_payload["prompt_metrics_id"] = prompt_metrics_id
    
    print(f"📦 Tamaño del payload: {len(json.dumps(webhook_payload))/1024:.1f} KB")
    print()
    
    # Crear cliente con logging
    webhook_client = WebhookClient(story_path=story_path)
    
    print("📤 Enviando webhook...")
    print("-"*60)
    
    # Enviar webhook
    success = webhook_client.send_story_complete(webhook_url, webhook_payload)
    
    if success:
        print("✅ Webhook enviado exitosamente")
        
        # Actualizar manifest con resultado
        manifest["webhook_result"] = {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "url": webhook_url,
            "status": "success",
            "manual_resend": True
        }
        
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)
        
        print("✅ Manifest actualizado con resultado del webhook")
    else:
        print("❌ Error al enviar el webhook")
        
        # Actualizar manifest con fallo
        manifest["webhook_result"] = {
            "success": False,
            "timestamp": datetime.now().isoformat(),
            "url": webhook_url,
            "status": "failed",
            "manual_resend": True
        }
        
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)
    
    # Mostrar log generado
    log_file = story_path / "logs" / "webhook_completion.log"
    if log_file.exists():
        print()
        print("📋 Log del webhook guardado en:")
        print(f"   {log_file}")
        print()
        print("Para ver el log completo:")
        print(f"   cat {log_file}")
    
    return success

if __name__ == "__main__":
    success = send_existing_story_webhook()
    exit(0 if success else 1)