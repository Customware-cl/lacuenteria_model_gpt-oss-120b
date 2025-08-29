#!/usr/bin/env python3
"""
Script para testear las mejoras en el sistema de reintentos
Específicamente el caso del director con el brief de Emilia
"""
import json
import requests
import time
import sys
import os
from datetime import datetime

def test_retry_improvements():
    """Prueba las mejoras del sistema de reintentos con el brief de Emilia"""
    
    # Cargar el brief de Emilia
    with open('examples/brief_emilia_cumple.json', 'r') as f:
        brief_data = json.load(f)
    
    # Preparar el brief para la API
    brief = {
        "story_id": f"test-retry-improvements-{int(time.time())}",
        "personajes": [p["nombre"] if isinstance(p, dict) else p for p in brief_data.get("personajes", [])],
        "historia": brief_data.get("historia", ""),
        "mensaje_a_transmitir": brief_data.get("mensaje_a_transmitir", "Aprender valores importantes"),
        "edad_objetivo": 3
    }
    
    print("=" * 70)
    print("🧪 TEST DE MEJORAS EN SISTEMA DE REINTENTOS")
    print("=" * 70)
    print(f"\n📖 Historia: {brief['story_id']}")
    print(f"👧 Personajes: {', '.join(brief['personajes'])}")
    print(f"📝 Trama: {brief['historia'][:100]}...")
    print("\n" + "=" * 70)
    
    # Iniciar generación con pipeline v2
    print("\n🚀 Iniciando generación con pipeline v2...")
    response = requests.post(
        'http://localhost:5000/api/v2/stories/create',
        json=brief
    )
    
    if response.status_code != 202:
        print(f"❌ Error al iniciar: {response.text}")
        return
    
    story_id = brief['story_id']
    print(f"✅ Procesamiento iniciado: {story_id}")
    
    # Monitorear progreso con foco en el director
    print("\n📊 Monitoreando progreso del director...")
    print("-" * 50)
    
    start_time = time.time()
    director_attempts = 0
    director_scores = []
    
    while True:
        time.sleep(3)
        
        # Obtener estado
        status_response = requests.get(f'http://localhost:5000/api/stories/{story_id}/status')
        if status_response.status_code != 200:
            continue
            
        status_data = status_response.json()
        current_step = status_data.get('current_step', 'N/A')
        status = status_data.get('status', 'unknown')
        
        # Obtener manifest para más detalles
        try:
            with open(f'runs/{story_id}/manifest.json', 'r') as f:
                manifest = json.load(f)
                
            # Rastrear intentos del director
            if 'reintentos' in manifest and '01_director' in manifest['reintentos']:
                new_attempts = manifest['reintentos']['01_director']
                if new_attempts > director_attempts:
                    director_attempts = new_attempts
                    print(f"\n🔄 Reintento {director_attempts} del director detectado")
                    
                    # Mostrar QA scores si están disponibles
                    if 'qa_historial' in manifest and '01_director' in manifest['qa_historial']:
                        qa_data = manifest['qa_historial']['01_director']
                        score = qa_data.get('promedio', 0)
                        director_scores.append(score)
                        print(f"   📊 Score QA: {score}/5")
                        
                        # Mostrar problemas detectados
                        if 'devoluciones' in manifest:
                            for devolucion in manifest['devoluciones']:
                                if devolucion['paso'] == '01_director':
                                    print(f"   ❌ Problemas detectados:")
                                    for issue in devolucion.get('issues', [])[:3]:
                                        print(f"      - {issue[:80]}...")
        except:
            pass
        
        # Verificar si el director completó o falló
        if current_step != '01_director' and current_step != 'N/A':
            # Verificar si el archivo se guardó
            import os
            director_file = f'runs/{story_id}/01_director.json'
            if os.path.exists(director_file):
                print(f"\n✅ Archivo 01_director.json guardado correctamente")
                
                # Verificar si tiene metadata de QA
                with open(director_file, 'r') as f:
                    director_data = json.load(f)
                    if '_qa_metadata' in director_data:
                        qa_meta = director_data['_qa_metadata']
                        print(f"   📋 Metadata QA incluida:")
                        print(f"      - Status: {qa_meta['status']}")
                        print(f"      - Score final: {qa_meta['scores'].get('promedio', 0)}/5")
                        print(f"      - Reintentos: {qa_meta['retry_count']}")
            else:
                print(f"\n⚠️ Archivo 01_director.json NO se guardó")
            
            print(f"\n📍 Pipeline continuó con: {current_step}")
            break
        
        # Timeout o error
        elapsed = int(time.time() - start_time)
        if elapsed > 180 or status == 'error':
            print(f"\n⏱️ Timeout o error después de {elapsed}s")
            break
        
        # Mostrar progreso
        sys.stdout.write(f"\r⏳ Tiempo: {elapsed}s | Estado: {status} | Paso: {current_step}")
        sys.stdout.flush()
    
    # Análisis final
    print("\n\n" + "=" * 70)
    print("📈 ANÁLISIS DE RESULTADOS")
    print("=" * 70)
    
    if director_scores:
        print(f"\n📊 Evolución de scores QA del director:")
        for i, score in enumerate(director_scores, 1):
            trend = "📈" if i > 1 and score > director_scores[i-2] else "📉" if i > 1 else "➡️"
            print(f"   Intento {i}: {score}/5 {trend}")
        
        if len(director_scores) > 1:
            improvement = director_scores[-1] - director_scores[0]
            if improvement > 0:
                print(f"\n✅ Mejora detectada: +{improvement:.1f} puntos")
            else:
                print(f"\n⚠️ Sin mejora: {improvement:.1f} puntos")
    
    # Verificar si las dependencias se mantuvieron
    print(f"\n🔗 Verificando integridad de dependencias:")
    for agent_file in ['01_director.json', '02_psicoeducador.json', '03_cuentacuentos.json']:
        file_path = f'runs/{story_id}/{agent_file}'
        exists = os.path.exists(file_path)
        print(f"   {'✅' if exists else '❌'} {agent_file}: {'Existe' if exists else 'No existe'}")
    
    print("\n" + "=" * 70)
    print("✨ Test completado")
    print("=" * 70)

if __name__ == "__main__":
    # Verificar que el servidor esté corriendo
    try:
        health = requests.get('http://localhost:5000/health')
        if health.status_code != 200:
            print("❌ El servidor no está respondiendo correctamente")
            sys.exit(1)
    except:
        print("❌ El servidor no está corriendo. Ejecuta: python3 src/api_server.py")
        sys.exit(1)
    
    # Ejecutar test
    test_retry_improvements()