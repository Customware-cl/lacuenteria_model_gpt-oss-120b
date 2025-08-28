#!/usr/bin/env python3
import requests
import json
import time
import sys
from datetime import datetime

# Configuración con QA
story_id = f"emilia-con-qa-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
brief = {
    "personajes": [
        {
            "nombre": "Emilia",
            "descripcion": "Hermosa niña de 2 años, de pelo castaño ondulado, muy alegre y de personalidad fuerte",
            "rasgos": "Tímida, curiosa, valiente cuando es necesario"
        }
    ],
    "historia": "El día en que Emilia celebró su cumpleaños en el jardín infantil y todos los niños se disfrazaron",
    "mensaje_a_transmitir": None,
    "edad_objetivo": "2-6 años"
}

print(f"\n🎭 Iniciando prueba CON QA - ID: {story_id}")
print("="*60)

# Crear historia con QA
payload = {
    "story_id": story_id,
    **brief,
    "skip_qa": False  # Habilitar QA (default)
}

response = requests.post("http://localhost:5000/api/stories/create", json=payload)
if response.status_code != 202:
    print(f"❌ Error creando historia: {response.text}")
    sys.exit(1)

print(f"✅ Historia creada, procesando con verificación QA...")

# Monitorear progreso
last_agent = None
qa_scores = []
retries_count = 0

while True:
    time.sleep(2)
    status_response = requests.get(f"http://localhost:5000/api/stories/{story_id}/status")
    if status_response.status_code == 200:
        status_data = status_response.json()
        current_agent = status_data.get("current_agent", "")
        
        if current_agent != last_agent and current_agent:
            print(f"📝 Procesando: {current_agent}")
            last_agent = current_agent
        
        if status_data["status"] == "completed":
            print("\n✅ Historia completada con QA")
            break
        elif status_data["status"] == "error":
            print(f"\n❌ Error: {status_data.get('error', 'Unknown error')}")
            sys.exit(1)

# Obtener resultado
result_response = requests.get(f"http://localhost:5000/api/stories/{story_id}/result")
if result_response.status_code == 200:
    result = result_response.json()
    print(f"\n📖 Título: {result.get('titulo', 'Sin título')}")
    print(f"📄 Páginas generadas: {len(result.get('paginas', []))}")
    
    # Guardar resultado
    output_file = f"runs/{story_id}/resultado_con_qa.json"
    print(f"\n💾 Resultado guardado en: {output_file}")
    
    # Obtener métricas detalladas con QA
    logs_response = requests.get(f"http://localhost:5000/api/stories/{story_id}/logs")
    if logs_response.status_code == 200:
        logs = logs_response.json()
        print("\n📊 Métricas (Con QA):")
        print(f"  - Tiempo total: {logs.get('total_time', 'N/A')} segundos")
        print(f"  - Agentes ejecutados: {len(logs.get('agents', []))}")
        
        total_retries = 0
        for agent in logs.get('agents', []):
            qa_score = agent.get('qa_score', 'N/A')
            retries = agent.get('retries', 0)
            total_retries += retries
            
            print(f"    • {agent['name']}: {agent.get('execution_time', 0):.2f}s")
            print(f"      QA: {qa_score}/5 | Reintentos: {retries}")
            
            if qa_score != 'N/A':
                qa_scores.append(float(qa_score))
        
        if qa_scores:
            avg_qa = sum(qa_scores) / len(qa_scores)
            print(f"\n  📈 QA Promedio: {avg_qa:.2f}/5")
            print(f"  🔄 Total reintentos: {total_retries}")
else:
    print(f"❌ Error obteniendo resultado: {result_response.text}")

print("\n" + "="*60)
print(f"✅ Prueba CON QA completada - ID: {story_id}")