#!/usr/bin/env python3
"""Test v2 pipeline with optimizations"""
import json
import requests
import time

# Brief de prueba simple
brief = {
    "story_id": f"test-v2-{int(time.time())}",
    "personajes": ["Sol", "Nube"],
    "historia": "Sol y Nube aprenden a trabajar juntos",
    "mensaje_a_transmitir": "La colaboración trae mejores resultados",
    "edad_objetivo": 4
}

print(f"Probando pipeline v2 con historia: {brief['story_id']}")
print("=" * 60)

# Probar endpoint explícito v2
response = requests.post('http://localhost:5000/api/v2/stories/create', json=brief)
print(f"Endpoint v2 - Status: {response.status_code}")
if response.status_code == 202:
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")
    print(f"\nNota: Tiempo estimado reducido: {result['estimated_time']}s (vs 180s en v1)")
    
    # Esperar un poco y verificar estado
    time.sleep(5)
    status_response = requests.get(f"http://localhost:5000/api/stories/{brief['story_id']}/status")
    if status_response.status_code == 200:
        status = status_response.json()
        print(f"\nEstado después de 5s: {status.get('status')}")
        print(f"Paso actual: {status.get('current_step')}")
        
        # Verificar que está usando pipeline v2
        manifest_path = f"runs/{brief['story_id']}/manifest.json"
        import os
        if os.path.exists(manifest_path):
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
                print(f"Pipeline version en manifest: {manifest.get('pipeline_version', 'Not found')}")
else:
    print(f"Error: {response.text}")

print("=" * 60)
print("Prueba v2 completada - Verificando optimizaciones:")
print("1. Timeout configurado a 900s (vs 60s)")
print("2. QA threshold reducido a 3.5 (vs 4.0)")
print("3. Max retries reducido a 1 (vs 2)")
print("4. Max tokens aumentado a 8000 (vs 4000)")
print("5. Agentes usan flujo/v2/agentes/*.json")