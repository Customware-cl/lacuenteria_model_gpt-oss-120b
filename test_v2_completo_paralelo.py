#!/usr/bin/env python3
"""
Test completo del pipeline v2 con procesamiento paralelo activado para cuentacuentos
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Agregar el directorio src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from orchestrator import StoryOrchestrator
from config import get_story_path

def main():
    # Configuración del test
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    story_id = f"test-v2-paralelo-{timestamp}"
    
    # Brief de la historia (misma historia de Marte)
    brief = {
        "personajes": ["Emilia de 2 años", "Caty de 35 años"],
        "historia": "Una historia sobre cómo Emilia y Caty caminan hasta Marte para seguir un mapa misterioso",
        "mensaje_a_transmitir": "Aprender a reconocer y expresar emociones de manera saludable. Superar miedos nocturnos y fomentar el sueño independiente",
        "edad_objetivo": 2,
        "metadata": {
            "parentesco": "Caty y Emilia son madre e hija",
            "valores": "Aprender a reconocer y expresar emociones de manera saludable",
            "comportamientos": "Superar miedos nocturnos y fomentar el sueño independiente",
            "version": "v2",
            "features": ["parallel_cuentacuentos"],
            "test_date": datetime.now().isoformat()
        }
    }
    
    print("=" * 70)
    print("🚀 TEST COMPLETO PIPELINE V2 - CON PARALELIZACIÓN")
    print("=" * 70)
    print(f"📝 Story ID: {story_id}")
    print(f"🎯 Versión: v2 (configuración granular + paralelización)")
    print(f"👥 Personajes: {', '.join(brief['personajes'])}")
    print(f"🌟 Historia: {brief['historia'][:60]}...")
    print(f"💡 Mensaje: {brief['mensaje_a_transmitir'][:60]}...")
    print(f"👶 Edad objetivo: {brief['edad_objetivo']} años")
    print(f"⚡ Features: Procesamiento paralelo de cuentacuentos activado")
    print("-" * 70)
    
    # Crear directorio para la historia
    story_path = get_story_path(story_id)
    os.makedirs(story_path, exist_ok=True)
    
    # Guardar el brief
    brief_path = story_path / "brief.json"
    with open(brief_path, 'w', encoding='utf-8') as f:
        json.dump(brief, f, ensure_ascii=False, indent=2)
    print(f"✅ Brief guardado en: {brief_path}")
    
    # Inicializar el orquestador con v2
    print("\n🎭 Iniciando orquestador con configuración v2...")
    print("⚡ Cuentacuentos usará procesamiento PARALELO (10 páginas simultáneas)")
    orchestrator = StoryOrchestrator(
        story_id=story_id,
        mode_verificador_qa=True,
        pipeline_version='v2'
    )
    
    # Ejecutar el pipeline
    print("\n🎬 Ejecutando pipeline completo...")
    print("📊 Agentes a ejecutar:")
    print("  1. Director")
    print("  2. Psicoeducador")
    print("  3. Cuentacuentos (PARALELO)")
    print("  4-12. Resto del pipeline...")
    print("\n⏳ Esto puede tomar varios minutos...\n")
    print("-" * 70)
    
    try:
        # Timestamps para métricas
        pipeline_start = datetime.now()
        
        result = orchestrator.process_story(
            brief=brief
        )
        
        pipeline_end = datetime.now()
        pipeline_duration = (pipeline_end - pipeline_start).total_seconds()
        
        if result.get("status") == "completed":
            print("\n" + "=" * 70)
            print("✅ PIPELINE COMPLETADO EXITOSAMENTE!")
            print("=" * 70)
            
            # Mostrar resumen de resultados
            print("\n📊 RESUMEN DE EJECUCIÓN:")
            print(f"  • Tiempo total: {pipeline_duration:.2f} segundos")
            print(f"  • Agentes ejecutados: {result.get('agents_completed', 'N/A')}")
            print(f"  • Devoluciones: {result.get('devoluciones', 0)}")
            
            # Verificar archivo final
            validador_path = story_path / "12_validador.json"
            if validador_path.exists():
                with open(validador_path, 'r', encoding='utf-8') as f:
                    cuento = json.load(f)
                    print(f"\n📖 CUENTO GENERADO:")
                    print(f"  • Título: {cuento.get('titulo', 'Sin título')}")
                    print(f"  • Páginas: {len(cuento.get('paginas', []))}")
                    print(f"  • Portada: {'✅' if cuento.get('portada') else '❌'}")
                    print(f"  • Mensajes loader: {len(cuento.get('mensajes_loader', []))}")
                    
                    # Mostrar primera página como muestra
                    if cuento.get('paginas'):
                        print(f"\n📄 Primera página (muestra):")
                        primera = cuento['paginas'][0]
                        print(f"  Texto: {primera.get('texto', 'Sin texto')[:150]}...")
                        if primera.get('ilustracion'):
                            print(f"  Ilustración: {primera['ilustracion'].get('descripcion', '')[:100]}...")
            
            # Verificar cuentacuentos paralelo
            cuentacuentos_path = story_path / "03_cuentacuentos.json"
            if cuentacuentos_path.exists():
                with open(cuentacuentos_path, 'r', encoding='utf-8') as f:
                    cuentacuentos = json.load(f)
                    if 'metadata' in cuentacuentos:
                        meta = cuentacuentos['metadata']
                        print(f"\n⚡ MÉTRICAS DE PARALELIZACIÓN (Cuentacuentos):")
                        print(f"  • Modo: {meta.get('processing_mode', 'N/A')}")
                        print(f"  • Páginas procesadas: {meta.get('pages_processed', 'N/A')}")
                        print(f"  • Páginas exitosas: {meta.get('pages_successful', 'N/A')}")
                        print(f"  • Tiempo de procesamiento: {meta.get('total_processing_time', 'N/A'):.2f}s")
                        print(f"  • QA promedio: {meta.get('average_qa_score', 'N/A')}/5")
            
            # Verificar métricas de QA
            manifest_path = story_path / "manifest.json"
            if manifest_path.exists():
                with open(manifest_path, 'r', encoding='utf-8') as f:
                    manifest = json.load(f)
                    if 'agent_metrics' in manifest:
                        print(f"\n📈 MÉTRICAS DE CALIDAD (QA):")
                        scores = []
                        for agent, metrics in sorted(manifest['agent_metrics'].items()):
                            if 'qa_score' in metrics:
                                score = metrics['qa_score']
                                scores.append(score)
                                status = "✅" if score >= 3.5 else "⚠️"
                                mode = " [PARALELO]" if agent == "03_cuentacuentos" and metrics.get('processing_mode') == 'parallel' else ""
                                print(f"  {status} {agent}: {score}/5{mode}")
                        
                        if scores:
                            avg_score = sum(scores) / len(scores)
                            print(f"\n  📊 Promedio general: {avg_score:.2f}/5")
            
            print(f"\n📁 Resultados guardados en: {story_path}")
            print("\n🎉 TEST COMPLETADO CON ÉXITO!")
            
        else:
            print(f"\n❌ Error en el pipeline: {result.get('error', 'Error desconocido')}")
            print(f"📁 Logs disponibles en: {story_path}/logs/")
            
            # Mostrar información de devoluciones si hay
            manifest_path = story_path / "manifest.json"
            if manifest_path.exists():
                with open(manifest_path, 'r', encoding='utf-8') as f:
                    manifest = json.load(f)
                    if manifest.get('devoluciones'):
                        print(f"\n⚠️ Agentes devueltos por baja calidad:")
                        for dev in manifest['devoluciones']:
                            print(f"  • {dev}")
        
        print("\n" + "=" * 70)
        return 0
            
    except Exception as e:
        print(f"\n❌ Error ejecutando el test: {e}")
        import traceback
        traceback.print_exc()
        print(f"📁 Logs disponibles en: {story_path}/logs/")
        return 1

if __name__ == "__main__":
    sys.exit(main())