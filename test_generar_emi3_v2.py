#!/usr/bin/env python3
"""
Genera un cuento usando brief_emi3.json con el flujo v2
"""

import json
import requests
import time
import sys
from datetime import datetime

sys.path.append('src')
from brief_adapter import adapt_brief

# Cargar y adaptar el brief
with open('examples/brief_emi3.json', 'r', encoding='utf-8') as f:
    brief_original = json.load(f)

print("Brief original:")
print(json.dumps(brief_original, indent=2, ensure_ascii=False))
print("\n" + "="*50 + "\n")

# Adaptar al formato esperado
brief_adaptado = adapt_brief(brief_original)
print("Brief adaptado:")
print(json.dumps(brief_adaptado, indent=2, ensure_ascii=False))
print("\n" + "="*50 + "\n")

# Generar story_id único
story_id = f"emi3-v2-{datetime.now().strftime('%Y%m%d%H%M%S')}"
print(f"Story ID: {story_id}")

# Preparar payload para la API
payload = {
    "story_id": story_id,
    **brief_adaptado,  # Expandir el brief adaptado
    "pipeline_version": "v2"  # IMPORTANTE: Especificar v2
}

print("\nPayload para API:")
print(json.dumps(payload, indent=2, ensure_ascii=False))
print("\n" + "="*50 + "\n")

# Enviar a la API
api_url = "http://localhost:5000/api/stories/create"
print(f"Enviando a {api_url}...")

try:
    response = requests.post(api_url, json=payload)
    response.raise_for_status()
    
    result = response.json()
    print(f"Respuesta: {result}")
    
    if result.get('status') == 'processing':
        print(f"\n✅ Historia creada exitosamente")
        print(f"Story ID: {result.get('story_id')}")
        print(f"Estado: {result.get('status')}")
        print(f"Mensaje: {result.get('message')}")
        
        # Monitorear progreso
        print("\nMonitoreando progreso...")
        status_url = f"http://localhost:5000/api/stories/{story_id}/status"
        
        last_step = None
        while True:
            time.sleep(5)
            status_response = requests.get(status_url)
            if status_response.ok:
                status_data = status_response.json()
                current_step = status_data.get('current_step', 'unknown')
                status = status_data.get('status', 'unknown')
                
                if current_step != last_step:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Estado: {status} | Paso: {current_step}")
                    last_step = current_step
                
                if status in ['completado', 'error', 'devolucion']:
                    print(f"\n{'='*50}")
                    print(f"Procesamiento finalizado con estado: {status}")
                    
                    if status == 'completado':
                        # Obtener resultado
                        result_url = f"http://localhost:5000/api/stories/{story_id}/result"
                        result_response = requests.get(result_url)
                        if result_response.ok:
                            story_result = result_response.json()
                            print(f"\n✅ Historia completada exitosamente")
                            print(f"Título: {story_result.get('titulo', 'Sin título')}")
                            print(f"Páginas generadas: {len(story_result.get('paginas', {}))}")
                            print(f"QA Score promedio: {story_result.get('qa_scores', {}).get('overall', 'N/A')}")
                            print(f"\nHistoria guardada en: runs/{story_id}/")
                        else:
                            print(f"Error obteniendo resultado: {result_response.text}")
                    break
            else:
                print(f"Error obteniendo estado: {status_response.text}")
                break
                
except requests.exceptions.RequestException as e:
    print(f"❌ Error conectando con la API: {e}")
    print("Asegúrate de que el servidor API esté corriendo: python3 src/api_server.py")
except Exception as e:
    print(f"❌ Error inesperado: {e}")