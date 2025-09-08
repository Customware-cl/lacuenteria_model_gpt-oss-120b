#!/usr/bin/env python3
"""
Test del nuevo endpoint síncrono /api/stories/create-sync
"""

import json
import time
import requests
from datetime import datetime

def test_sync_endpoint():
    """Prueba el endpoint síncrono con pipeline v3"""
    
    url = "http://localhost:5000/api/stories/create-sync"
    
    # Payload de prueba v3
    payload = {
        "story_id": f"test-sync-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "personajes": ["Luna (niña curiosa, 5 años)", "Sol (gato mágico)"],
        "historia": "Luna y su gato Sol descubren que pueden viajar por los colores del arcoíris. Cada color les enseña una emoción diferente.",
        "mensaje_a_transmitir": "Todas las emociones son válidas y nos ayudan a crecer",
        "edad_objetivo": 5,
        "relacion_personajes": ["Luna y Sol son mejores amigos"],
        "valores": ["inteligencia emocional", "amistad", "curiosidad"],
        "comportamientos": ["expresar emociones", "escuchar a otros"],
        "numero_paginas": 10,
        "pipeline_version": "v3",
        "prompt_metrics_id": f"test-metrics-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    }
    
    print("="*60)
    print("🚀 TEST ENDPOINT SÍNCRONO")
    print("="*60)
    print(f"📍 URL: {url}")
    print(f"📦 Pipeline: v3")
    print(f"⏱️  Inicio: {datetime.now().strftime('%H:%M:%S')}")
    print("\n⏳ Esperando respuesta completa (esto tomará ~2-3 minutos)...")
    print("   La conexión se mantendrá abierta hasta completar.\n")
    
    start_time = time.time()
    
    try:
        # Hacer request síncrono con timeout alto
        response = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=300  # 5 minutos de timeout
        )
        
        elapsed = time.time() - start_time
        
        print(f"✅ Respuesta recibida en {elapsed:.1f} segundos")
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print("\n" + "="*60)
            print("📋 RESULTADO COMPLETO")
            print("="*60)
            
            print(f"✅ Status: {data.get('status')}")
            print(f"📚 Story ID: {data.get('story_id')}")
            print(f"📁 Folder: {data.get('folder')}")
            print(f"⏱️  Processing Time: {data.get('processing_time')} segundos")
            print(f"🔧 Pipeline: {data.get('pipeline_version')}")
            
            result = data.get('result', {})
            print(f"\n📖 Título: {result.get('titulo', 'Sin título')}")
            print(f"📄 Páginas generadas: {len(result.get('paginas', {}))}")
            
            # Mostrar primera página como muestra
            if 'paginas' in result and '1' in result['paginas']:
                primera = result['paginas']['1']
                texto = primera.get('texto', '')[:150] + "..."
                print(f"\n📝 Muestra Página 1:\n{texto}")
            
            # Verificar loader messages
            if 'loader' in result:
                print(f"\n⏳ Mensajes de carga: {len(result['loader'])}")
            
            print("\n" + "="*60)
            print("✅ TEST EXITOSO")
            print("="*60)
            print(f"💡 El endpoint síncrono funcionó correctamente.")
            print(f"   Tiempo total: {elapsed:.1f} segundos")
            print(f"   Sin necesidad de polling - respuesta completa en una sola llamada.")
            
            return True
            
        else:
            print(f"\n❌ Error: {response.status_code}")
            print(response.json())
            return False
            
    except requests.exceptions.Timeout:
        print(f"\n⏰ Timeout después de {time.time() - start_time:.1f} segundos")
        print("   El servidor no respondió en el tiempo límite.")
        return False
        
    except requests.exceptions.ConnectionError as e:
        print(f"\n❌ Error de conexión: {e}")
        print("   Verifica que el servidor esté ejecutándose.")
        return False
        
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        return False

if __name__ == "__main__":
    success = test_sync_endpoint()
    exit(0 if success else 1)