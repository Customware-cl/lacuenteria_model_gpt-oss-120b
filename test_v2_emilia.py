#!/usr/bin/env python3
"""
Test completo del pipeline v2 con todas las mejoras implementadas:
- Criterios de evaluación por página para cuentacuentos
- Sin rimas repetidas
- Integración explícita director/psicoeducador
- Umbral QA mínimo 4.0 para cuentacuentos
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
    """Ejecuta test completo con pipeline v2"""
    
    # Configurar paths
    brief_path = "examples/brief_emilia_cumple.json"
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    story_id = f"test-v2-emilia-{timestamp}"
    
    print(f"\n{'='*70}")
    print(f"TEST COMPLETO PIPELINE V2 - EMILIA CUMPLEAÑOS")
    print(f"Story ID: {story_id}")
    print(f"{'='*70}\n")
    
    print("Mejoras implementadas en este test:")
    print("✓ Evaluación página por página (musicalidad, imaginería, fluidez)")
    print("✓ Prohibición estricta de rimas repetidas (rojo/rojo)")
    print("✓ Integración explícita director/psicoeducador")
    print("✓ Umbral QA mínimo 4.0 para cuentacuentos")
    print("✓ Tokens ilimitados (20000 por agente)")
    print()
    
    # Leer brief
    with open(brief_path, 'r', encoding='utf-8') as f:
        brief = json.load(f)
    
    print("📖 Brief cargado:")
    print(f"  - Personaje: {brief['personajes'][0]['nombre']}")
    print(f"  - Historia: {brief['historia']}")
    print(f"  - Edad objetivo: {brief['edad_objetivo']}")
    print()
    
    # Configurar request
    request_data = {
        "story_id": story_id,
        "personajes": brief.get("personajes", []),
        "historia": brief.get("historia", ""),
        "mensaje_a_transmitir": brief.get("mensaje_a_transmitir"),
        "edad_objetivo": brief.get("edad_objetivo", "2-6 años")
    }
    
    # Crear orchestrator con pipeline v2
    orchestrator = StoryOrchestrator(
        story_id=story_id,
        mode_verificador_qa=True,  # Usar verificador QA
        pipeline_version='v2'
    )
    
    print("🚀 Iniciando procesamiento con pipeline v2...")
    print("-" * 70)
    
    try:
        # Procesar historia
        result = orchestrator.process_story(request_data)
        
        if result["status"] == "completed":
            print(f"\n{'='*70}")
            print("✅ TEST COMPLETADO EXITOSAMENTE")
            print(f"{'='*70}")
            
            # Analizar resultados
            analyze_results(story_id)
            
            # Mostrar resumen de QA
            show_qa_summary(story_id)
            
        else:
            print(f"\n{'='*70}")
            print(f"❌ TEST FALLÓ")
            print(f"{'='*70}")
            print(f"Error: {result.get('error', 'Error desconocido')}")
            
            # Mostrar agentes completados
            if 'agents_completed' in result:
                print(f"\nAgentes completados: {result['agents_completed']}")
            if 'failed_agent' in result:
                print(f"Agente que falló: {result['failed_agent']}")
            
    except Exception as e:
        print(f"\n❌ Error durante el test: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n{'='*70}")
    print(f"📁 Resultados guardados en: runs/{story_id}/")
    print(f"{'='*70}\n")

def analyze_results(story_id):
    """Analiza los resultados clave del test"""
    output_dir = f"runs/{story_id}"
    
    print(f"\n{'='*60}")
    print("📊 ANÁLISIS DE RESULTADOS CLAVE")
    print(f"{'='*60}")
    
    # 1. Verificar cuentacuentos - rimas
    print("\n1️⃣ ANÁLISIS DE CUENTACUENTOS (Rimas):")
    print("-" * 40)
    analyze_cuentacuentos_rhymes(output_dir)
    
    # 2. Verificar ritmo_rima - correcciones
    print("\n2️⃣ ANÁLISIS DE RITMO_RIMA (Correcciones):")
    print("-" * 40)
    analyze_ritmo_rima_corrections(output_dir)
    
    # 3. Verificar integración director/psicoeducador
    print("\n3️⃣ INTEGRACIÓN DIRECTOR/PSICOEDUCADOR:")
    print("-" * 40)
    analyze_integration(output_dir)

def analyze_cuentacuentos_rhymes(output_dir):
    """Analiza rimas del cuentacuentos"""
    try:
        with open(f"{output_dir}/03_cuentacuentos.json", 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        repetitions = []
        valid_rhymes = 0
        total_rhymes = 0
        
        for page_num, text in data.get("paginas_texto", {}).items():
            lines = text.strip().split('\n')
            if len(lines) >= 4:
                # Extraer últimas palabras
                words = []
                for line in lines[:4]:
                    if line.strip():
                        last_word = line.split()[-1].lower().rstrip('.,!?:;')
                        words.append(last_word)
                
                if len(words) >= 4:
                    total_rhymes += 2
                    # Verificar rimas 1-2
                    if words[0] == words[1]:
                        repetitions.append(f"Pág {page_num}: '{words[0]}'/'{words[1]}'")
                    else:
                        valid_rhymes += 1
                    
                    # Verificar rimas 3-4
                    if words[2] == words[3]:
                        repetitions.append(f"Pág {page_num}: '{words[2]}'/'{words[3]}'")
                    else:
                        valid_rhymes += 1
        
        if repetitions:
            print(f"❌ Palabras repetidas encontradas:")
            for rep in repetitions:
                print(f"   {rep}")
        else:
            print(f"✅ ¡EXCELENTE! No hay palabras repetidas")
        
        print(f"\n📈 Estadísticas:")
        print(f"   - Rimas válidas: {valid_rhymes}/{total_rhymes}")
        print(f"   - Porcentaje: {(valid_rhymes/total_rhymes*100):.1f}%")
        
    except FileNotFoundError:
        print("❌ No se encontró 03_cuentacuentos.json")
    except Exception as e:
        print(f"❌ Error: {e}")

def analyze_ritmo_rima_corrections(output_dir):
    """Analiza las correcciones de ritmo_rima"""
    try:
        with open(f"{output_dir}/05_ritmo_rima.json", 'r', encoding='utf-8') as f:
            ritmo = json.load(f)
        
        with open(f"{output_dir}/04_editor_claridad.json", 'r', encoding='utf-8') as f:
            editor = json.load(f)
        
        corrections = 0
        for page in ritmo.get("paginas_texto_pulido", {}):
            if page in editor.get("paginas_texto_simplificado", {}):
                if ritmo["paginas_texto_pulido"][page] != editor["paginas_texto_simplificado"][page]:
                    corrections += 1
        
        if corrections > 0:
            print(f"✅ Se realizaron correcciones en {corrections} páginas")
        else:
            print(f"ℹ️ No se necesitaron correcciones")
        
        # Verificar finales documentados
        if "finales_de_verso" in ritmo:
            documented = len(ritmo["finales_de_verso"])
            print(f"✅ Finales documentados: {documented}/10 páginas")
        
    except FileNotFoundError as e:
        print(f"ℹ️ Archivo no encontrado: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

def analyze_integration(output_dir):
    """Verifica integración con director y psicoeducador"""
    try:
        with open(f"{output_dir}/03_cuentacuentos.json", 'r', encoding='utf-8') as f:
            cuento = json.load(f)
        
        with open(f"{output_dir}/01_director.json", 'r', encoding='utf-8') as f:
            director = json.load(f)
        
        # Verificar leitmotiv
        leitmotiv = director.get("leitmotiv", "")
        leitmotiv_pages = cuento.get("leitmotiv_usado_en", [])
        
        if leitmotiv and leitmotiv_pages == [2, 5, 10]:
            print(f"✅ Leitmotiv correctamente en páginas 2, 5, 10")
            print(f"   '{leitmotiv}'")
        else:
            print(f"❌ Problema con leitmotiv")
            print(f"   Esperado en: [2, 5, 10]")
            print(f"   Encontrado en: {leitmotiv_pages}")
        
        # Verificar que usa elementos del director
        beat_sheet = director.get("beat_sheet", [])
        if beat_sheet and len(beat_sheet) > 0:
            # Verificar página 1 como ejemplo
            if "busca" in cuento.get("paginas_texto", {}).get("1", "").lower():
                print(f"✅ Integra conflicto del director (ej: 'busca')")
            else:
                print(f"⚠️ Verificar integración con beat sheet")
        
    except FileNotFoundError as e:
        print(f"❌ Archivo no encontrado: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

def show_qa_summary(story_id):
    """Muestra resumen de scores QA"""
    output_dir = f"runs/{story_id}"
    
    print(f"\n{'='*60}")
    print("📊 RESUMEN DE EVALUACIÓN QA")
    print(f"{'='*60}")
    
    try:
        with open(f"{output_dir}/manifest.json", 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        
        agents = manifest.get("agents_completed", [])
        
        print("\n📈 Scores QA por agente:")
        print("-" * 40)
        
        for agent in agents:
            # Buscar en logs
            log_file = f"{output_dir}/logs/{agent}.log"
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
                    if isinstance(logs, list) and len(logs) > 0:
                        last_log = logs[-1]
                        qa_scores = last_log.get("qa_scores", {})
                        promedio = qa_scores.get("promedio", {})
                        
                        if isinstance(promedio, dict):
                            score = promedio.get("nota_final", 0)
                        else:
                            score = promedio
                        
                        # Determinar umbral requerido
                        if agent == "03_cuentacuentos":
                            threshold = 4.0
                            emoji = "🎯" if score >= 4.0 else "❌"
                        else:
                            threshold = 3.5
                            emoji = "✅" if score >= 3.5 else "⚠️"
                        
                        print(f"{emoji} {agent}: {score:.2f}/5 (min: {threshold})")
        
        # Mostrar estadísticas finales
        print("\n📊 Estadísticas finales:")
        print("-" * 40)
        
        total_time = 0
        if "start_time" in manifest and "end_time" in manifest:
            from datetime import datetime
            start = datetime.fromisoformat(manifest["start_time"])
            end = datetime.fromisoformat(manifest["end_time"])
            total_time = (end - start).total_seconds()
            
            print(f"⏱️ Tiempo total: {total_time:.1f} segundos")
            print(f"📝 Agentes completados: {len(agents)}/12")
        
        if manifest.get("status") == "completed":
            print(f"✅ Pipeline completado exitosamente")
        else:
            print(f"⚠️ Estado: {manifest.get('status')}")
            
    except Exception as e:
        print(f"❌ Error leyendo manifest: {e}")

if __name__ == "__main__":
    main()