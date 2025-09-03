#!/usr/bin/env python3
"""
Script de prueba para enviar webhook a Supabase Edge Function
con el último cuento generado
"""

import json
import sys
import time
import requests
from pathlib import Path
from datetime import datetime

# Configuración
STORY_ID = "6534605d-961d-43be-890a-8da9a59bcd94-20250902-155259"
WEBHOOK_URL = "https://ogegdctdniijmublbmgy.supabase.co/functions/v1/pipeline-webhook"

def load_story_result():
    """Carga el resultado del validador"""
    validador_path = Path(f"/home/ubuntu/cuenteria/runs/{STORY_ID}/outputs/agents/12_validador.json")
    
    if not validador_path.exists():
        print(f"❌ No se encontró el archivo validador: {validador_path}")
        return None
    
    with open(validador_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_manifest():
    """Carga el manifest para obtener metadata"""
    manifest_path = Path(f"/home/ubuntu/cuenteria/runs/{STORY_ID}/manifest.json")
    
    if not manifest_path.exists():
        return {}
    
    with open(manifest_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def calculate_qa_scores(manifest):
    """Calcula los scores QA del manifest"""
    qa_historial = manifest.get("qa_historial", {})
    
    if not qa_historial:
        return {"overall": 0.0}
    
    all_scores = []
    for agent_scores in qa_historial.values():
        if isinstance(agent_scores, dict):
            # Buscar el promedio de cada agente
            if "promedio" in agent_scores:
                score = agent_scores["promedio"].get("nota_final", 0)
                if isinstance(score, (int, float)):
                    all_scores.append(score)
    
    if all_scores:
        overall = sum(all_scores) / len(all_scores)
        return {
            "overall": round(overall, 2),
            "by_agent": qa_historial
        }
    
    return {"overall": 0.0}

def send_webhook(webhook_url, payload):
    """Envía el webhook a Supabase"""
    print("\n" + "="*60)
    print("ENVIANDO WEBHOOK A SUPABASE")
    print("="*60)
    print(f"URL: {webhook_url}")
    print(f"Story ID: {payload['data']['story_id']}")
    print(f"Título: {payload['data']['result'].get('titulo', 'Sin título')}")
    
    try:
        response = requests.post(
            webhook_url,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Cuenteria-Test/1.0"
            },
            timeout=30
        )
        
        print(f"\n📡 Respuesta HTTP: {response.status_code}")
        
        if response.status_code in [200, 201, 202, 204]:
            print("✅ Webhook enviado exitosamente!")
            
            # Mostrar respuesta si hay contenido
            if response.text:
                print("\n📝 Respuesta del servidor:")
                try:
                    response_json = response.json()
                    print(json.dumps(response_json, indent=2, ensure_ascii=False))
                except:
                    print(response.text[:500])
        else:
            print(f"⚠️ Respuesta inesperada: {response.status_code}")
            print(f"Contenido: {response.text[:500]}")
            
        return response
        
    except requests.exceptions.Timeout:
        print("❌ Timeout al enviar webhook (30 segundos)")
        return None
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error al enviar webhook: {e}")
        return None
        
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return None

def main():
    print("\n" + "="*60)
    print("TEST DE WEBHOOK - SUPABASE EDGE FUNCTION")
    print("="*60)
    
    # Cargar datos
    print("\n📚 Cargando datos del cuento...")
    story_result = load_story_result()
    if not story_result:
        print("❌ No se pudo cargar el resultado del cuento")
        return 1
    
    manifest = load_manifest()
    
    # Calcular métricas
    qa_scores = calculate_qa_scores(manifest)
    
    # Calcular tiempo de procesamiento
    created_at = manifest.get("created_at", "")
    updated_at = manifest.get("updated_at", "")
    processing_time = 0
    
    if created_at and updated_at:
        try:
            start = datetime.fromisoformat(created_at)
            end = datetime.fromisoformat(updated_at)
            processing_time = (end - start).total_seconds()
        except:
            pass
    
    # Construir payload como lo haría el sistema real
    webhook_payload = {
        "event": "story_complete",
        "timestamp": time.time(),
        "data": {
            "status": "success",
            "story_id": manifest.get("original_story_id", STORY_ID),
            "result": story_result,
            "qa_scores": qa_scores,
            "processing_time": processing_time,
            "metadata": {
                "retries": manifest.get("reintentos", {}),
                "warnings": manifest.get("devoluciones", []),
                "pipeline_version": "v2",
                "folder": STORY_ID
            }
        }
    }
    
    # Mostrar resumen
    print(f"\n📊 Resumen del cuento:")
    print(f"  - Título: {story_result.get('titulo', 'Sin título')}")
    print(f"  - Páginas: {len(story_result.get('paginas', {}))}")
    print(f"  - QA Score: {qa_scores['overall']}/5.0")
    print(f"  - Tiempo procesamiento: {processing_time:.1f} segundos")
    print(f"  - Tamaño payload: {len(json.dumps(webhook_payload))} bytes")
    
    # Confirmar envío
    print("\n❓ ¿Deseas enviar este webhook a Supabase? (s/n): ", end="")
    confirm = input().strip().lower()
    
    if confirm != 's':
        print("❌ Envío cancelado")
        return 0
    
    # Enviar webhook
    response = send_webhook(WEBHOOK_URL, webhook_payload)
    
    if response and response.status_code in [200, 201, 202, 204]:
        print("\n🎉 ¡Prueba completada exitosamente!")
        print("El webhook fue recibido por Supabase Edge Function")
        return 0
    else:
        print("\n❌ La prueba falló")
        return 1

if __name__ == "__main__":
    sys.exit(main())