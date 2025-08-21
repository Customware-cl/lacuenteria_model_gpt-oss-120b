#!/usr/bin/env python3
"""
Prueba simple y rápida del verificador QA con un solo agente
"""
import requests
import json
import time

def test_verificador():
    """Prueba rápida con solo el director"""
    
    url = "http://localhost:5000/api/stories/create"
    
    payload = {
        "story_id": f"test-verificador-{int(time.time())}",
        "personajes": ["Emilia"],
        "historia": "Una niña descubre un unicornio",
        "mensaje_a_transmitir": "Test rápido",
        "edad_objetivo": 5
    }
    
    print("🚀 INICIANDO TEST RÁPIDO DEL VERIFICADOR QA")
    print("=" * 60)
    print(f"Story ID: {payload['story_id']}")
    
    # Crear historia
    response = requests.post(url, json=payload, timeout=10)
    
    if response.status_code != 202:
        print(f"❌ Error creando historia: {response.status_code}")
        return
    
    print("✅ Historia iniciada")
    print("⏳ Esperando solo al director (primer agente)...")
    
    # Esperar 30 segundos para que complete el director
    time.sleep(30)
    
    # Verificar status
    status_url = f"http://localhost:5000/api/stories/{payload['story_id']}/status"
    response = requests.get(status_url, timeout=5)
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n📊 Estado: {data.get('status')}")
        print(f"   Agente actual: {data.get('current_agent')}")
        
        # Revisar QA scores
        qa_scores = data.get("qa_scores", {}).get("by_agent", {})
        if "director" in qa_scores:
            director_qa = qa_scores["director"]
            print(f"\n✅ QA del Director (via verificador):")
            print(f"   Promedio: {director_qa.get('promedio', 'N/A')}/5")
            for metric, score in director_qa.items():
                if metric != "promedio":
                    print(f"   • {metric}: {score}")
        else:
            print("\n⚠️ Aún no hay QA del director")
            
    print("\n" + "=" * 60)
    print("Test completado - revisar logs del servidor para errores")
    return payload['story_id']

if __name__ == "__main__":
    story_id = test_verificador()
    if story_id:
        print(f"\nPuedes revisar los logs en:")
        print(f"  runs/{story_id}/logs/")