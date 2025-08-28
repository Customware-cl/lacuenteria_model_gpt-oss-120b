#!/usr/bin/env python3
"""Test v1 pipeline with simple brief"""
import json
import requests
import time

# Brief de prueba simple
brief = {
    "story_id": f"test-v1-{int(time.time())}",
    "personajes": ["Luna", "El Sol"],
    "historia": "Luna quiere aprender a brillar como el Sol",
    "mensaje_a_transmitir": "Cada uno tiene su propia luz especial",
    "edad_objetivo": 4
}

print(f"Probando pipeline v1 con historia: {brief['story_id']}")
print("=" * 60)

# Probar endpoint genérico (debe usar v1 por defecto)
response = requests.post('http://localhost:5000/api/stories/create', json=brief)
print(f"Endpoint genérico - Status: {response.status_code}")
if response.status_code == 202:
    print(f"Response: {json.dumps(response.json(), indent=2)}")
else:
    print(f"Error: {response.text}")

print("-" * 60)

# Probar endpoint explícito v1
brief['story_id'] = f"test-v1-explicit-{int(time.time())}"
response = requests.post('http://localhost:5000/api/v1/stories/create', json=brief)
print(f"Endpoint v1 explícito - Status: {response.status_code}")
if response.status_code == 202:
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")
    
    # Esperar un poco y verificar estado
    time.sleep(5)
    status_response = requests.get(f"http://localhost:5000/api/stories/{brief['story_id']}/status")
    if status_response.status_code == 200:
        status = status_response.json()
        print(f"\nEstado después de 5s: {status.get('status')}")
        print(f"Paso actual: {status.get('current_step')}")
else:
    print(f"Error: {response.text}")

print("=" * 60)
print("Prueba v1 completada - El pipeline debe estar procesando")
print("Usa el story_id para verificar el progreso")