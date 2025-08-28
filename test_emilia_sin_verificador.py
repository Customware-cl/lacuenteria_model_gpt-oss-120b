#!/usr/bin/env python3
"""
Prueba SIN verificador QA - Forzando mode_verificador_qa=False
"""
import requests
import json
import time
from datetime import datetime

# Brief de Emilia
brief = {
    "personajes": [{
        "nombre": "Emilia",
        "descripcion": "Hermosa niña de 2 años, de pelo castaño ondulado, muy alegre y de personalidad fuerte",
        "rasgos": "Tímida, curiosa, valiente cuando es necesario"
    }],
    "historia": "El día en que Emilia celebró su cumpleaños en el jardín infantil y todos los niños se disfrazaron",
    "mensaje_a_transmitir": None,
    "edad_objetivo": "2-6 años"
}

# ID único
story_id = f"emilia-noqa-{datetime.now().strftime('%H%M%S')}"

print("="*70)
print("🚫 PRUEBA SIN VERIFICADOR QA")
print("="*70)
print(f"Story ID: {story_id}")
print("mode_verificador_qa: FALSE (deshabilitado)")
print("-"*70)

# Crear historia SIN verificador QA
payload = {
    "story_id": story_id,
    **brief,
    "mode_verificador_qa": False  # Deshabilitar verificador QA
}

print("\n📤 Enviando request con mode_verificador_qa=False...")
response = requests.post("http://localhost:5000/api/stories/create", json=payload)

if response.status_code != 202:
    print(f"❌ Error: {response.text}")
    exit(1)

print(f"✅ Historia iniciada SIN verificador QA")
print("\n⏳ Procesando (debería ser más rápido sin QA)...")
print("-"*70)

# Monitorear progreso
start_time = time.time()
last_agent = None
agents_processed = []

for i in range(180):  # 15 minutos máximo
    r = requests.get(f"http://localhost:5000/api/stories/{story_id}/status")
    
    if r.status_code == 200:
        data = r.json()
        
        # Mostrar agente actual
        if data.get("current_agent") and data["current_agent"] != last_agent:
            last_agent = data["current_agent"]
            agents_processed.append(last_agent)
            elapsed = int(time.time() - start_time)
            print(f"[{elapsed:3d}s] Procesando: {last_agent}")
        
        # Verificar completado
        if data.get("status") == "completed":
            total_time = time.time() - start_time
            print("-"*70)
            print(f"✅ COMPLETADO en {total_time:.2f} segundos")
            break
        elif data.get("status") == "error":
            print(f"\n❌ Error: {data.get('error', 'Unknown')}")
            exit(1)
    
    time.sleep(3)

# Obtener resultado
print("\n📊 RESULTADOS SIN VERIFICADOR QA:")
print("="*70)

# Logs
r_logs = requests.get(f"http://localhost:5000/api/stories/{story_id}/logs")
if r_logs.status_code == 200:
    logs = r_logs.json()
    
    print(f"Tiempo total: {logs.get('total_time', 'N/A')} segundos")
    print(f"Agentes ejecutados: {len(logs.get('agents', []))}")
    
    # NO debería haber QA scores si está deshabilitado
    has_qa = False
    for agent in logs.get('agents', []):
        if 'qa_score' in agent:
            has_qa = True
            break
    
    if has_qa:
        print("⚠️ ADVERTENCIA: Se encontraron QA scores (no debería haber)")
    else:
        print("✅ Confirmado: NO hay QA scores (correcto)")

# Resultado
r_result = requests.get(f"http://localhost:5000/api/stories/{story_id}/result")
if r_result.status_code == 200:
    result = r_result.json()
    print(f"\nTítulo: '{result.get('titulo', 'Sin título')}'")
    print(f"Páginas generadas: {len(result.get('paginas', []))}")
    
    # Guardar resultado
    output_file = f"resultado_sin_qa_{story_id}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n💾 Resultado guardado en: {output_file}")

print("\n" + "="*70)
print("✅ PRUEBA SIN VERIFICADOR QA COMPLETADA")
print("="*70)