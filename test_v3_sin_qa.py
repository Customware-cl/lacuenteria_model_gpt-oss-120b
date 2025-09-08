#!/usr/bin/env python3
"""
Script rápido para verificar que v3 no ejecuta QA
"""
import requests
import time
from datetime import datetime

BASE_URL = "http://localhost:5000"
STORY_ID = f"test-v3-noqa-{datetime.now().strftime('%H%M%S')}"

brief = {
    "story_id": STORY_ID,
    "personajes": ["Luna", "Sol"],
    "historia": "Luna y Sol aprenden sobre el día y la noche",
    "mensaje_a_transmitir": "La importancia de los ciclos naturales",
    "edad_objetivo": 4,
    "pipeline_version": "v3"
}

print(f"🚀 Probando v3 sin QA - ID: {STORY_ID}")

# Crear historia
r = requests.post(f"{BASE_URL}/api/stories/create", json=brief, timeout=10)
if r.status_code not in [200, 202]:
    print(f"❌ Error creando historia: {r.status_code}")
    exit(1)

print("✅ Historia creada, esperando procesamiento...")

# Monitorear por 30 segundos
start = time.time()
while time.time() - start < 30:
    r = requests.get(f"{BASE_URL}/api/stories/{STORY_ID}/status")
    if r.status_code == 200:
        data = r.json()
        status = data.get("status")
        agent = data.get("current_agent", "")
        
        # Verificar si hay menciones de QA
        warnings = data.get("metadata", {}).get("warnings", [])
        qa_mentions = [w for w in warnings if "qa" in str(w).lower()]
        
        if agent:
            print(f"  📍 Agente actual: {agent}")
        
        if status == "completed" or status == "error":
            print(f"\n{'✅' if status == 'completed' else '❌'} Estado final: {status}")
            
            if qa_mentions:
                print(f"⚠️  Se encontraron {len(qa_mentions)} menciones de QA (deberían ser 0)")
            else:
                print("✅ No se encontraron verificaciones QA - ¡Éxito!")
            
            # Verificar logs
            manifest_path = f"runs/*{STORY_ID}/manifest.json"
            print(f"\n📁 Revisar: {manifest_path} para más detalles")
            break
    
    time.sleep(2)

print("\n✨ Prueba completada")
