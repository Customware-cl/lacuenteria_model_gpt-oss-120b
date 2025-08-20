#!/usr/bin/env python3
"""Prueba rápida del flujo"""

import requests
import time
from datetime import datetime

BASE_URL = "http://localhost:5000"
STORY_ID = f"quick-test-{datetime.now().strftime('%H%M%S')}"

# Brief simplificado
brief = {
    "story_id": STORY_ID,
    "personajes": [{"nombre": "Luna", "descripcion": "Luciérnaga tímida", "rasgos": "Curiosa"}],
    "historia": "Luna debe aprender a brillar",
    "mensaje_a_transmitir": "Vencer miedos",
    "edad_objetivo": "4-6 años"
}

print(f"Creando historia: {STORY_ID}")
r = requests.post(f"{BASE_URL}/api/stories/create", json=brief)
print(f"Respuesta: {r.status_code}")

# Monitorear
for i in range(60):
    r = requests.get(f"{BASE_URL}/api/stories/{STORY_ID}/status")
    data = r.json()
    print(f"[{i*3}s] Estado: {data.get('status')} | Paso: {data.get('current_step')}")
    
    if data.get('status') in ['completo', 'error', 'qa_failed']:
        break
    
    time.sleep(3)

# Resultado
if data.get('status') == 'completo':
    r = requests.get(f"{BASE_URL}/api/stories/{STORY_ID}/result")
    print("\n✓ Historia completada")
    
    # Evaluar
    r = requests.post(f"{BASE_URL}/api/stories/{STORY_ID}/evaluate")
    if r.status_code == 200:
        eval_data = r.json()
        if 'evaluacion_critica' in eval_data:
            critica = eval_data['evaluacion_critica']
            if 'nota_general' in critica:
                print(f"Evaluación crítica: {critica['nota_general'].get('puntuacion')}/5")
                print(f"Comentario: {critica['nota_general'].get('comentario')}")
else:
    print(f"\n✗ Historia falló: {data.get('status')}")