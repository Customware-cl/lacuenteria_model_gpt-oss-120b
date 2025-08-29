#!/usr/bin/env python3
"""
Test para verificar las mejoras en el sistema de rimas.
Prueba los agentes modificados: cuentacuentos y ritmo_rima
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Añadir el directorio src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from orchestrator import StoryOrchestrator

def main():
    """Ejecuta test con los primeros 5 agentes para verificar mejoras"""
    
    # Configurar paths
    brief_path = "examples/brief_emilia_cumple.json"
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    story_id = f"test-rimas-{timestamp}"
    
    print(f"\n{'='*60}")
    print(f"TEST DE RIMAS MEJORADAS")
    print(f"Story ID: {story_id}")
    print(f"{'='*60}\n")
    
    # Leer brief
    with open(brief_path, 'r', encoding='utf-8') as f:
        brief = json.load(f)
    
    # Configurar request
    request_data = {
        "story_id": story_id,
        "personajes": brief.get("personajes", []),
        "historia": brief.get("historia", ""),
        "mensaje_a_transmitir": brief.get("mensaje_a_transmitir"),
        "edad_objetivo": brief.get("edad_objetivo", "2-6 años")
    }
    
    # Crear orchestrator con solo 5 agentes
    orchestrator = StoryOrchestrator()
    
    # Modificar temporalmente el pipeline para solo ejecutar 5 agentes
    original_pipeline = orchestrator.agent_pipeline.copy()
    orchestrator.agent_pipeline = [
        "01_director",
        "02_psicoeducador",
        "03_cuentacuentos", 
        "04_editor_claridad",
        "05_ritmo_rima"
    ]
    
    print("Pipeline reducido para test:")
    for agent in orchestrator.agent_pipeline:
        print(f"  - {agent}")
    print()
    
    try:
        # Procesar historia
        result = orchestrator.process_story(request_data)
        
        if result["status"] == "completed":
            print(f"\n✅ Test completado exitosamente")
            analyze_results(story_id)
        else:
            print(f"\n❌ Test falló: {result.get('error', 'Error desconocido')}")
            
    except Exception as e:
        print(f"\n❌ Error durante el test: {e}")
        import traceback
        traceback.print_exc()
    
    # Restaurar pipeline original
    orchestrator.agent_pipeline = original_pipeline
    
    print(f"\n{'='*60}")
    print(f"Resultados guardados en: runs/{story_id}/")
    print(f"{'='*60}\n")

def analyze_results(story_id):
    """Analiza los resultados para detectar rimas repetidas"""
    output_dir = f"runs/{story_id}"
    
    print(f"\n{'='*50}")
    print("ANÁLISIS DE RESULTADOS")
    print(f"{'='*50}")
    
    # Analizar cuentacuentos
    analyze_cuentacuentos(output_dir)
    
    # Analizar ritmo_rima si existe
    if os.path.exists(f"{output_dir}/05_ritmo_rima.json"):
        analyze_ritmo_rima(output_dir)

def analyze_cuentacuentos(output_dir):
    """Analiza el output del cuentacuentos para detectar rimas repetidas"""
    print("\n📊 ANÁLISIS DE CUENTACUENTOS (03):")
    print("-" * 40)
    
    try:
        with open(f"{output_dir}/03_cuentacuentos.json", 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        repetitions_found = []
        good_rhymes = []
        
        for page_num, text in data.get("paginas_texto", {}).items():
            lines = text.strip().split('\n')
            if len(lines) >= 4:
                # Extraer últimas palabras
                word1 = lines[0].split()[-1].lower().rstrip('.,!?:;')
                word2 = lines[1].split()[-1].lower().rstrip('.,!?:;')
                word3 = lines[2].split()[-1].lower().rstrip('.,!?:;')
                word4 = lines[3].split()[-1].lower().rstrip('.,!?:;')
                
                # Verificar rimas 1-2
                if word1 == word2:
                    repetitions_found.append(f"  Página {page_num}: '{word1}'/'{word2}' (versos 1-2)")
                else:
                    good_rhymes.append(f"  Página {page_num}: '{word1}'/'{word2}' ✓")
                
                # Verificar rimas 3-4
                if word3 == word4:
                    repetitions_found.append(f"  Página {page_num}: '{word3}'/'{word4}' (versos 3-4)")
                else:
                    good_rhymes.append(f"  Página {page_num}: '{word3}'/'{word4}' ✓")
        
        # Mostrar resultados
        if repetitions_found:
            print(f"\n❌ PALABRAS REPETIDAS ENCONTRADAS:")
            for rep in repetitions_found:
                print(f"  {rep}")
            print(f"\n  Total: {len(repetitions_found)} repeticiones")
        else:
            print(f"\n✅ ¡EXCELENTE! No se encontraron palabras repetidas")
        
        # Mostrar algunas rimas buenas
        if good_rhymes and len(good_rhymes) <= 10:
            print(f"\n✅ Rimas válidas encontradas:")
            for rhyme in good_rhymes[:5]:
                print(rhyme)
            
    except FileNotFoundError:
        print(f"  ❌ No se encontró el archivo 03_cuentacuentos.json")
    except Exception as e:
        print(f"  ❌ Error analizando cuentacuentos: {e}")

def analyze_ritmo_rima(output_dir):
    """Analiza el output de ritmo_rima para verificar correcciones"""
    print("\n📊 ANÁLISIS DE RITMO_RIMA (05):")
    print("-" * 40)
    
    try:
        with open(f"{output_dir}/05_ritmo_rima.json", 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        with open(f"{output_dir}/03_cuentacuentos.json", 'r', encoding='utf-8') as f:
            original = json.load(f)
        
        repetitions_found = []
        corrections_made = []
        
        for page_num, text in data.get("paginas_texto_pulido", {}).items():
            lines = text.strip().split('\n')
            if len(lines) >= 4:
                # Extraer últimas palabras
                word1 = lines[0].split()[-1].lower().rstrip('.,!?:;')
                word2 = lines[1].split()[-1].lower().rstrip('.,!?:;')
                word3 = lines[2].split()[-1].lower().rstrip('.,!?:;')
                word4 = lines[3].split()[-1].lower().rstrip('.,!?:;')
                
                # Verificar si aún hay repeticiones
                if word1 == word2:
                    repetitions_found.append(f"  Página {page_num}: '{word1}'/'{word2}' (versos 1-2)")
                if word3 == word4:
                    repetitions_found.append(f"  Página {page_num}: '{word3}'/'{word4}' (versos 3-4)")
                
                # Verificar si hubo correcciones
                if page_num in original.get("paginas_texto", {}):
                    orig_lines = original["paginas_texto"][page_num].strip().split('\n')
                    if len(orig_lines) >= 4:
                        orig_word1 = orig_lines[0].split()[-1].lower().rstrip('.,!?:;')
                        orig_word2 = orig_lines[1].split()[-1].lower().rstrip('.,!?:;')
                        orig_word3 = orig_lines[2].split()[-1].lower().rstrip('.,!?:;')
                        orig_word4 = orig_lines[3].split()[-1].lower().rstrip('.,!?:;')
                        
                        # Detectar correcciones
                        if orig_word1 == orig_word2 and word1 != word2:
                            corrections_made.append(f"  Página {page_num}: '{orig_word1}/{orig_word2}' → '{word1}/{word2}'")
                        if orig_word3 == orig_word4 and word3 != word4:
                            corrections_made.append(f"  Página {page_num}: '{orig_word3}/{orig_word4}' → '{word3}/{word4}'")
        
        # Mostrar resultados
        if corrections_made:
            print(f"\n✅ CORRECCIONES REALIZADAS:")
            for corr in corrections_made:
                print(corr)
            print(f"\n  Total: {len(corrections_made)} correcciones")
        
        if repetitions_found:
            print(f"\n❌ REPETICIONES NO CORREGIDAS:")
            for rep in repetitions_found:
                print(rep)
            print(f"\n  Total: {len(repetitions_found)} repeticiones sin corregir")
        else:
            print(f"\n✅ ¡PERFECTO! Todas las repeticiones fueron corregidas")
            
        # Verificar finales documentados
        if "finales_de_verso" in data:
            print(f"\n📝 Finales de verso documentados: ✓")
            
    except FileNotFoundError:
        print(f"  ℹ️ No se encontró 05_ritmo_rima.json (agente no ejecutado)")
    except Exception as e:
        print(f"  ❌ Error analizando ritmo_rima: {e}")

if __name__ == "__main__":
    main()