#!/usr/bin/env python3
"""
PRUEBA COMPARATIVA FINAL: Con QA vs Sin QA
"""
import requests
import json
import time
from datetime import datetime

def crear_historia(story_id, brief, con_qa=True):
    """Crear una historia con o sin verificador QA"""
    payload = {
        "story_id": story_id,
        **brief,
        "mode_verificador_qa": con_qa  # True = con QA, False = sin QA
    }
    
    response = requests.post("http://localhost:5000/api/stories/create", json=payload)
    return response.status_code == 202

def monitorear_historia(story_id, label):
    """Monitorear el progreso de una historia"""
    start_time = time.time()
    last_agent = None
    agents = []
    
    print(f"\n[{label}] Procesando...")
    
    for i in range(240):  # 20 minutos máximo
        r = requests.get(f"http://localhost:5000/api/stories/{story_id}/status")
        if r.status_code == 200:
            data = r.json()
            
            # Mostrar agente actual
            if data.get("current_agent") and data["current_agent"] != last_agent:
                last_agent = data["current_agent"]
                agents.append(last_agent)
                elapsed = int(time.time() - start_time)
                print(f"[{label}] [{elapsed:3d}s] {last_agent}")
            
            # Verificar estado final
            if data.get("status") in ["completed", "success"]:
                total_time = time.time() - start_time
                print(f"[{label}] ✅ Completado en {total_time:.1f}s")
                return True, total_time, agents
            elif data.get("status") == "error":
                print(f"[{label}] ❌ Error: {data.get('error', 'Unknown')[:100]}")
                return False, time.time() - start_time, agents
        
        time.sleep(5)
    
    print(f"[{label}] ⏱️ Timeout")
    return False, 1200, agents

# Brief común
brief = {
    "personajes": [{
        "nombre": "Emilia",
        "descripcion": "Niña de 2 años, pelo castaño ondulado",
        "rasgos": "Alegre, curiosa"
    }],
    "historia": "Emilia celebra su cumpleaños en el jardín con amigos",
    "mensaje_a_transmitir": "La alegría de compartir",
    "edad_objetivo": "2-4 años"
}

print("="*70)
print("🔬 PRUEBA COMPARATIVA: CON QA vs SIN QA")
print("="*70)

# Crear ambas historias
story_sin = f"sin-qa-{datetime.now().strftime('%H%M%S')}"
story_con = f"con-qa-{datetime.now().strftime('%H%M%S')}"

print(f"\n📚 Iniciando historias:")
print(f"  • SIN QA: {story_sin}")
print(f"  • CON QA: {story_con}")

# Iniciar SIN QA
if not crear_historia(story_sin, brief, con_qa=False):
    print("❌ Error creando historia sin QA")
    exit(1)

# Iniciar CON QA  
if not crear_historia(story_con, brief, con_qa=True):
    print("❌ Error creando historia con QA")
    exit(1)

print("\n⏳ Procesando ambas historias...")
print("-"*70)

# Monitorear en paralelo (simplificado)
success_sin, time_sin, agents_sin = monitorear_historia(story_sin, "SIN QA")
success_con, time_con, agents_con = monitorear_historia(story_con, "CON QA")

# Resultados
print("\n" + "="*70)
print("📊 RESULTADOS COMPARATIVOS")
print("="*70)

print(f"\n### SIN VERIFICADOR QA ({story_sin}) ###")
print(f"Estado: {'✅ Éxito' if success_sin else '❌ Error'}")
print(f"Tiempo: {time_sin:.1f} segundos")
print(f"Agentes: {len(agents_sin)}")

if success_sin:
    r = requests.get(f"http://localhost:5000/api/stories/{story_sin}/logs")
    if r.status_code == 200:
        logs = r.json()
        # Verificar si hay QA scores
        qa_scores = []
        for agent, data in logs.items():
            if isinstance(data, dict) and 'qa_scores' in data:
                if data['qa_scores'].get('promedio'):
                    qa_scores.append(data['qa_scores']['promedio'])
        
        if qa_scores:
            print(f"QA detectado: {len(qa_scores)} agentes con scores")
            print(f"Promedio QA: {sum(qa_scores)/len(qa_scores):.2f}")
        else:
            print("✅ Sin verificador QA (correcto)")

print(f"\n### CON VERIFICADOR QA ({story_con}) ###")
print(f"Estado: {'✅ Éxito' if success_con else '❌ Error'}")
print(f"Tiempo: {time_con:.1f} segundos")
print(f"Agentes: {len(agents_con)}")

if success_con:
    r = requests.get(f"http://localhost:5000/api/stories/{story_con}/logs")
    if r.status_code == 200:
        logs = r.json()
        # Contar reintentos
        reintentos = 0
        qa_scores = []
        
        if 'agents' in logs:
            for agent in logs['agents']:
                if 'retries' in agent:
                    reintentos += agent['retries']
                if 'qa_score' in agent:
                    qa_scores.append(agent['qa_score'])
        
        print(f"Reintentos totales: {reintentos}")
        if qa_scores:
            print(f"QA Promedio: {sum(qa_scores)/len(qa_scores):.2f}/5")

# Comparación
print("\n" + "="*70)
print("📈 COMPARACIÓN")
print("="*70)

if success_sin and success_con:
    diff_time = time_con - time_sin
    pct_diff = (diff_time / time_sin) * 100
    
    print(f"Diferencia de tiempo: {diff_time:.1f}s ({pct_diff:+.1f}%)")
    print(f"El QA agregó aproximadamente {diff_time:.1f} segundos al proceso")
elif success_sin and not success_con:
    print("✅ Sin QA completó, Con QA falló")
elif not success_sin and success_con:
    print("❌ Sin QA falló, Con QA completó")
else:
    print("❌ Ambas pruebas fallaron")

print("\n" + "="*70)
print("✅ PRUEBA COMPARATIVA COMPLETADA")
print("="*70)