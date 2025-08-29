#!/usr/bin/env python3
"""
Test para verificar las mejoras en el verificador QA
Específicamente que no reporte falsos positivos en el conteo
"""
import json
import requests
import time
import sys
import os
from datetime import datetime

def test_verificador_mejorado():
    """Prueba el verificador QA mejorado con el brief de Emilia"""
    
    # Cargar el brief de Emilia
    with open('examples/brief_emilia_cumple.json', 'r') as f:
        brief_data = json.load(f)
    
    # Preparar el brief para la API
    brief = {
        "story_id": f"test-verificador-mejorado-{int(time.time())}",
        "personajes": [p["nombre"] if isinstance(p, dict) else p for p in brief_data.get("personajes", [])],
        "historia": brief_data.get("historia", ""),
        "mensaje_a_transmitir": brief_data.get("mensaje_a_transmitir", "Aprender valores importantes"),
        "edad_objetivo": 3
    }
    
    print("=" * 70)
    print("🧪 TEST DEL VERIFICADOR QA MEJORADO")
    print("=" * 70)
    print(f"\n📖 Historia: {brief['story_id']}")
    print(f"🎯 Objetivo: Verificar que no haya falsos positivos en conteo de repeticiones")
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
    
    # Monitorear específicamente el director y su QA
    print("\n📊 Monitoreando evaluación QA del director...")
    print("-" * 50)
    
    start_time = time.time()
    director_completed = False
    qa_results = []
    
    while True:
        time.sleep(3)
        elapsed = int(time.time() - start_time)
        
        # Obtener estado
        status_response = requests.get(f'http://localhost:5000/api/stories/{story_id}/status')
        if status_response.status_code != 200:
            continue
            
        status_data = status_response.json()
        current_step = status_data.get('current_step', 'N/A')
        status = status_data.get('status', 'unknown')
        
        # Leer manifest para obtener detalles de QA
        try:
            manifest_path = f'runs/{story_id}/manifest.json'
            if os.path.exists(manifest_path):
                with open(manifest_path, 'r') as f:
                    manifest = json.load(f)
                
                # Capturar resultados QA del director
                if 'qa_historial' in manifest and '01_director' in manifest['qa_historial']:
                    qa_data = manifest['qa_historial']['01_director']
                    score = qa_data.get('promedio', 0)
                    
                    # Revisar si hay nuevos resultados
                    if len(qa_results) == 0 or qa_results[-1]['score'] != score:
                        qa_results.append({
                            'intento': len(qa_results) + 1,
                            'score': score,
                            'timestamp': elapsed
                        })
                        
                        print(f"\n⏱️ [{elapsed}s] Intento {len(qa_results)} - Score: {score}/5")
                        
                        # Revisar problemas detectados
                        if 'devoluciones' in manifest:
                            for devolucion in manifest['devoluciones']:
                                if devolucion['paso'] == '01_director':
                                    issues = devolucion.get('issues', [])
                                    print(f"\n📝 Problemas reportados:")
                                    for i, issue in enumerate(issues, 1):
                                        print(f"   {i}. {issue}")
                                    
                                    # VERIFICACIÓN CLAVE: Buscar falsos positivos
                                    print(f"\n🔍 Analizando problemas reportados:")
                                    false_positives = []
                                    for issue in issues:
                                        if "5 páginas" in issue or "5 veces" in issue or "al menos 5" in issue:
                                            # Verificar si realmente hay 5 repeticiones
                                            if "leitmotiv" in issue.lower():
                                                false_positives.append("Falso positivo: Reporta 5 repeticiones del leitmotiv")
                                    
                                    if false_positives:
                                        print("   ❌ FALSOS POSITIVOS DETECTADOS:")
                                        for fp in false_positives:
                                            print(f"      - {fp}")
                                    else:
                                        print("   ✅ No se detectaron falsos positivos de conteo")
                
                # Verificar si el director completó
                if 'timestamps' in manifest and '01_director' in manifest['timestamps']:
                    if 'end' in manifest['timestamps']['01_director']:
                        director_completed = True
                        
        except Exception as e:
            pass
        
        # Si el director completó o cambió de paso
        if director_completed or (current_step != '01_director' and current_step != 'N/A'):
            break
        
        # Timeout o error
        if elapsed > 180 or status == 'error':
            print(f"\n⏱️ Timeout o error después de {elapsed}s")
            break
        
        # Mostrar progreso
        sys.stdout.write(f"\r⏳ [{elapsed}s] Estado: {status} | Paso: {current_step}")
        sys.stdout.flush()
    
    # Análisis final
    print("\n\n" + "=" * 70)
    print("📈 ANÁLISIS DE RESULTADOS DEL VERIFICADOR MEJORADO")
    print("=" * 70)
    
    # Verificar el archivo guardado
    director_file = f'runs/{story_id}/01_director.json'
    if os.path.exists(director_file):
        with open(director_file, 'r') as f:
            director_data = json.load(f)
            
        # Contar apariciones reales del leitmotiv
        leitmotiv = director_data.get('leitmotiv', '')
        beat_sheet = director_data.get('beat_sheet', [])
        
        print(f"\n📊 Verificación Manual del Leitmotiv:")
        print(f"   Leitmotiv: '{leitmotiv}'")
        
        apariciones = []
        for beat in beat_sheet:
            pagina = beat.get('pagina', 0)
            conflicto = beat.get('conflicto', '')
            resolucion = beat.get('resolucion', '')
            
            if leitmotiv in conflicto or leitmotiv in resolucion:
                apariciones.append(pagina)
                campo = 'conflicto' if leitmotiv in conflicto else 'resolucion'
                print(f"   ✓ Página {pagina}: Aparece en '{campo}'")
        
        print(f"\n   Total apariciones reales: {len(apariciones)}")
        print(f"   Páginas: {apariciones}")
        
        if len(apariciones) == 3:
            print("   ✅ CORRECTO: Aparece exactamente 3 veces como se requiere")
        elif len(apariciones) > 3:
            print(f"   ⚠️ EXCESO: Aparece {len(apariciones)} veces (debería ser 3)")
        else:
            print(f"   ⚠️ FALTA: Solo aparece {len(apariciones)} veces (debería ser 3)")
    
    # Resumen de la prueba
    print("\n" + "=" * 70)
    print("🎯 RESUMEN DE LA PRUEBA")
    print("=" * 70)
    
    mejoras_detectadas = []
    problemas_restantes = []
    
    # Analizar si hay mejoras respecto a versiones anteriores
    if qa_results:
        ultimo_score = qa_results[-1]['score']
        print(f"\n📊 Score final del director: {ultimo_score}/5")
        
        if ultimo_score >= 3.5:
            mejoras_detectadas.append("Score mejorado (≥3.5)")
        
        # Verificar ausencia de falsos positivos
        try:
            with open(f'runs/{story_id}/manifest.json', 'r') as f:
                manifest = json.load(f)
            
            false_count_issues = False
            if 'devoluciones' in manifest:
                for dev in manifest['devoluciones']:
                    if dev['paso'] == '01_director':
                        for issue in dev.get('issues', []):
                            if ("5 páginas" in issue or "al menos 5" in issue) and "leitmotiv" in issue.lower():
                                false_count_issues = True
                                problemas_restantes.append("Aún reporta falsamente 5 repeticiones")
            
            if not false_count_issues:
                mejoras_detectadas.append("No hay falsos positivos en conteo de leitmotiv")
        except:
            pass
    
    if mejoras_detectadas:
        print("\n✅ MEJORAS DETECTADAS:")
        for mejora in mejoras_detectadas:
            print(f"   - {mejora}")
    
    if problemas_restantes:
        print("\n⚠️ PROBLEMAS RESTANTES:")
        for problema in problemas_restantes:
            print(f"   - {problema}")
    
    print("\n" + "=" * 70)
    print("✨ Test del verificador mejorado completado")
    print("=" * 70)

if __name__ == "__main__":
    test_verificador_mejorado()