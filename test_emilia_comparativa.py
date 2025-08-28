#!/usr/bin/env python3
"""
Prueba comparativa: Con QA vs Sin QA
Brief: Emilia cumpleaños
"""
import requests
import json
import time
from datetime import datetime

# Brief común para ambas pruebas
brief_base = {
    "personajes": [{
        "nombre": "Emilia",
        "descripcion": "Hermosa niña de 2 años, de pelo castaño ondulado, muy alegre y de personalidad fuerte",
        "rasgos": "Tímida, curiosa, valiente cuando es necesario"
    }],
    "historia": "El día en que Emilia celebró su cumpleaños en el jardín infantil y todos los niños se disfrazaron",
    "mensaje_a_transmitir": None,
    "edad_objetivo": "2-6 años"
}

# Crear historia SIN QA
story_id_sin = f"emilia-sinqa-{datetime.now().strftime('%H%M%S')}"
payload_sin = {
    "story_id": story_id_sin,
    **brief_base,
    "skip_qa": True  # Deshabilitar QA
}

# Crear historia CON QA  
story_id_con = f"emilia-conqa-{datetime.now().strftime('%H%M%S')}"
payload_con = {
    "story_id": story_id_con,
    **brief_base,
    "skip_qa": False  # Habilitar QA
}

print("="*70)
print("🎭 PRUEBA COMPARATIVA: CON QA vs SIN QA")
print("="*70)

# Iniciar ambas historias
print("\n📚 Iniciando historias:")
r1 = requests.post("http://localhost:5000/api/stories/create", json=payload_sin)
print(f"  • SIN QA: {story_id_sin} - Status {r1.status_code}")

r2 = requests.post("http://localhost:5000/api/stories/create", json=payload_con)
print(f"  • CON QA: {story_id_con} - Status {r2.status_code}")

if r1.status_code != 202 or r2.status_code != 202:
    print("❌ Error iniciando historias")
    exit(1)

# Monitorear progreso
print("\n⏳ Procesando (puede tomar 5-10 minutos)...")
print("-"*70)

completed = {"sin": False, "con": False}
agents = {"sin": [], "con": []}
start_time = time.time()

for i in range(180):  # 15 minutos máximo
    for tipo, sid in [("sin", story_id_sin), ("con", story_id_con)]:
        if completed[tipo]:
            continue
            
        r = requests.get(f"http://localhost:5000/api/stories/{sid}/status")
        if r.status_code == 200:
            data = r.json()
            
            if data.get("current_agent") and data["current_agent"] not in agents[tipo]:
                agents[tipo].append(data["current_agent"])
                label = "SIN QA" if tipo == "sin" else "CON QA"
                print(f"[{label}] Procesando: {data['current_agent']}")
            
            if data["status"] == "completed":
                completed[tipo] = True
                elapsed = int(time.time() - start_time)
                print(f"✅ [{label}] Completado en {elapsed}s")
            elif data["status"] == "error":
                completed[tipo] = True
                print(f"❌ [{label}] Error: {data.get('error', 'Unknown')}")
    
    if all(completed.values()):
        break
    
    time.sleep(5)

# Obtener resultados y métricas
print("\n" + "="*70)
print("📊 RESULTADOS Y MÉTRICAS")
print("="*70)

for tipo, sid in [("sin", story_id_sin), ("con", story_id_con)]:
    label = "SIN QA" if tipo == "sin" else "CON QA"
    print(f"\n### {label} ({sid}) ###")
    
    # Obtener logs
    r_logs = requests.get(f"http://localhost:5000/api/stories/{sid}/logs")
    if r_logs.status_code == 200:
        logs = r_logs.json()
        
        total_time = logs.get("total_time", 0)
        agents_info = logs.get("agents", [])
        
        print(f"Tiempo total: {total_time:.2f}s")
        print(f"Agentes ejecutados: {len(agents_info)}")
        
        if tipo == "con":  # Solo para CON QA mostrar scores
            qa_scores = []
            reintentos = 0
            
            for agent in agents_info:
                if "qa_score" in agent:
                    qa_scores.append(agent["qa_score"])
                    reintentos += agent.get("retries", 0)
            
            if qa_scores:
                avg_qa = sum(qa_scores) / len(qa_scores)
                print(f"QA Promedio: {avg_qa:.2f}/5")
                print(f"Reintentos totales: {reintentos}")
    
    # Obtener resultado
    r_result = requests.get(f"http://localhost:5000/api/stories/{sid}/result")
    if r_result.status_code == 200:
        result = r_result.json()
        titulo = result.get("titulo", "Sin título")
        paginas = len(result.get("paginas", []))
        print(f"Título: '{titulo}'")
        print(f"Páginas: {paginas}")

print("\n" + "="*70)
print("✅ PRUEBA COMPARATIVA COMPLETADA")
print("="*70)