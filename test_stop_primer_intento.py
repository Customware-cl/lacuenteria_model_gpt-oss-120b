#!/usr/bin/env python3
"""
Test para verificar que el sistema se detiene en el primer intento vacío
"""
import json
import requests
import time
from datetime import datetime

def test_stop_primer_intento():
    """Prueba que el sistema se detiene sin reintentar cuando el primer intento falla"""
    
    brief = {
        "story_id": f"test-stop-{int(time.time())}",
        "personajes": ["Emilia"],
        "historia": "Historia de prueba para verificar detención en primer intento",
        "mensaje_a_transmitir": "Test de sistema de detención",
        "edad_objetivo": 3
    }
    
    print("=" * 70)
    print("🧪 TEST DE DETENCIÓN EN PRIMER INTENTO VACÍO")
    print("=" * 70)
    print(f"\n📖 Historia: {brief['story_id']}")
    print(f"🎯 Objetivo: Verificar que NO se realizan reintentos innecesarios")
    print("\n" + "=" * 70)
    
    # Iniciar generación
    print("\n🚀 Iniciando generación con pipeline v2...")
    start_time = time.time()
    
    response = requests.post(
        'http://localhost:5000/api/v2/stories/create',
        json=brief
    )
    
    if response.status_code != 202:
        print(f"❌ Error al iniciar: {response.text}")
        return
    
    story_id = brief['story_id']
    print(f"✅ Procesamiento iniciado: {story_id}")
    
    # Monitorear el proceso
    print("\n⏳ Monitoreando proceso...")
    print("-" * 50)
    
    for i in range(30):  # Monitorear por 150 segundos máximo
        time.sleep(5)
        
        # Verificar estado
        status_response = requests.get(f'http://localhost:5000/api/stories/{story_id}/status')
        if status_response.status_code == 200:
            data = status_response.json()
            status = data.get('status', 'unknown')
            
            elapsed = int(time.time() - start_time)
            print(f"[{elapsed}s] Estado: {status}")
            
            if status in ['completed', 'error']:
                break
    
    # Analizar resultados
    print("\n" + "=" * 70)
    print("📊 ANÁLISIS DE RESULTADOS")
    print("=" * 70)
    
    try:
        # Leer manifest
        manifest_path = f'runs/{story_id}/manifest.json'
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        # Verificar alertas tempranas
        if "alertas_tempranas" in manifest:
            print(f"\n✅ Alertas tempranas registradas: {len(manifest['alertas_tempranas'])}")
            
            for alerta in manifest['alertas_tempranas']:
                print(f"\n📍 Alerta: {alerta['tipo']}")
                print(f"   Agente: {alerta['agente']}")
                print(f"   Intento: {alerta['intento']}")
                
                if alerta.get('critico'):
                    print(f"   🔴 CRÍTICO: {alerta.get('accion', 'N/A')}")
                
                if 'contexto' in alerta:
                    ctx = alerta['contexto']
                    if 'approx_tokens' in ctx:
                        print(f"   Tokens aproximados: {ctx['approx_tokens']}")
                    if 'total_chars' in ctx:
                        print(f"   Total caracteres: {ctx['total_chars']}")
        
        # Verificar reintentos
        if "reintentos" in manifest:
            print(f"\n📈 Reintentos por agente:")
            for agente, intentos in manifest['reintentos'].items():
                print(f"   {agente}: {intentos} reintentos")
        
        # Verificar el error específico del cuentacuentos
        if manifest.get('estado') == 'error':
            error_info = manifest.get('error', {})
            print(f"\n❌ Error detectado:")
            print(f"   Agente: {error_info.get('agent')}")
            print(f"   Mensaje: {error_info.get('message')}")
            
            # Verificar si se detuvo correctamente
            if "03_cuentacuentos" in error_info.get('agent', ''):
                message = error_info.get('message', '')
                if "Fallo después de 3 intentos" in message:
                    print("\n⚠️ PROBLEMA: Se realizaron 3 intentos (no debería)")
                elif "Contexto excedido" in message or "STOP" in message:
                    print("\n✅ CORRECTO: Se detuvo en el primer intento")
                else:
                    print(f"\n❓ Resultado inesperado: {message}")
        
        # Verificar duración
        if "timestamps" in manifest:
            if "03_cuentacuentos" in manifest['timestamps']:
                duracion = manifest['timestamps']['03_cuentacuentos'].get('duration', 0)
                print(f"\n⏱️ Duración cuentacuentos: {duracion:.1f} segundos")
                
                if duracion < 30:
                    print("   ✅ Duración corta - indica detención temprana")
                elif duracion > 60:
                    print("   ⚠️ Duración larga - posibles reintentos")
        
    except Exception as e:
        print(f"❌ Error analizando resultados: {e}")
    
    print("\n" + "=" * 70)
    elapsed_total = int(time.time() - start_time)
    print(f"✨ Test completado en {elapsed_total} segundos")
    print("=" * 70)

if __name__ == "__main__":
    test_stop_primer_intento()