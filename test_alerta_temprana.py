#!/usr/bin/env python3
"""
Script para probar el sistema de alerta temprana cuando no se genera contenido
"""
import json
import requests
import time
import sys
from datetime import datetime

def test_alerta_temprana():
    """Prueba el sistema de alerta temprana con un caso que sabemos que falla"""
    
    # Brief diseñado para provocar fallo en cuentacuentos
    brief = {
        "story_id": f"test-alerta-{int(time.time())}",
        "personajes": ["Test"],
        "historia": "Historia de prueba para alertas tempranas",
        "mensaje_a_transmitir": "Probar sistema de alertas",
        "edad_objetivo": 3
    }
    
    print("=" * 70)
    print("🧪 TEST DEL SISTEMA DE ALERTA TEMPRANA")
    print("=" * 70)
    print(f"\n📖 Historia: {brief['story_id']}")
    print(f"🎯 Objetivo: Verificar alertas cuando no se genera contenido")
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
    
    # Esperar un poco para que se procesen algunos agentes
    print("\n⏳ Esperando 90 segundos para que se generen alertas...")
    time.sleep(90)
    
    # Verificar si se generaron alertas
    print("\n📊 Verificando alertas tempranas...")
    print("-" * 50)
    
    try:
        # Leer manifest
        manifest_path = f'runs/{story_id}/manifest.json'
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        # Verificar alertas tempranas
        if "alertas_tempranas" in manifest:
            print(f"\n✅ Se encontraron {len(manifest['alertas_tempranas'])} alertas tempranas:")
            for alerta in manifest['alertas_tempranas']:
                print(f"\n📍 Alerta para {alerta['agente']} (intento {alerta['intento']}):")
                print(f"   Tipo: {alerta['tipo']}")
                print(f"   Timestamp: {alerta['timestamp']}")
                
                if 'diagnostico' in alerta:
                    print(f"\n   🔍 Diagnóstico:")
                    diag = alerta['diagnostico']
                    
                    if diag.get('posibles_causas'):
                        print("   Posibles causas:")
                        for causa in diag['posibles_causas']:
                            print(f"      - {causa}")
                    
                    if diag.get('recomendaciones'):
                        print("   Recomendaciones:")
                        for rec in diag['recomendaciones']:
                            print(f"      - {rec}")
                    
                    if diag.get('metricas'):
                        print("   Métricas:")
                        for key, val in diag['metricas'].items():
                            print(f"      - {key}: {val}")
        else:
            print("⚠️ No se encontraron alertas tempranas")
        
        # Verificar primer_fallo_contenido
        if "primer_fallo_contenido" in manifest:
            print(f"\n🚨 Primer fallo de contenido detectado:")
            pf = manifest['primer_fallo_contenido']
            print(f"   Agente: {pf['agente']}")
            print(f"   Timestamp: {pf['timestamp']}")
            if pf.get('diagnostico_resumen'):
                print(f"   Diagnóstico resumen:")
                for item in pf['diagnostico_resumen']:
                    print(f"      - {item}")
        
        # Verificar directorio de alertas
        alerts_dir = f'runs/{story_id}/alerts'
        import os
        if os.path.exists(alerts_dir):
            alert_files = os.listdir(alerts_dir)
            print(f"\n📁 Archivos de alerta guardados: {alert_files}")
            
            # Mostrar contenido de un archivo de alerta si existe
            if alert_files:
                sample_file = os.path.join(alerts_dir, alert_files[0])
                with open(sample_file, 'r') as f:
                    alert_content = json.load(f)
                print(f"\n📄 Contenido de {alert_files[0]}:")
                print(json.dumps(alert_content, indent=2, ensure_ascii=False))
        
    except FileNotFoundError:
        print("❌ No se encontró el manifest.json")
    except Exception as e:
        print(f"❌ Error al verificar alertas: {e}")
    
    print("\n" + "=" * 70)
    print("✨ Test del sistema de alertas completado")
    print("=" * 70)

if __name__ == "__main__":
    test_alerta_temprana()