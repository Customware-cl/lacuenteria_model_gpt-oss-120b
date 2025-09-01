#!/usr/bin/env python3
"""
Test completo del pipeline v2 con historia de Marte
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
    story_id = f"test-v2-marte-{timestamp}"
    
    # Brief de la historia
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
            "test_date": datetime.now().isoformat()
        }
    }
    
    print(f"🚀 Iniciando test de v2 con historia de Marte")
    print(f"📝 Story ID: {story_id}")
    print(f"🎯 Versión: v2 (configuración granular)")
    print(f"👥 Personajes: {', '.join(brief['personajes'])}")
    print(f"🌟 Historia: {brief['historia']}")
    print(f"💡 Mensaje: {brief['mensaje_a_transmitir']}")
    print(f"👶 Edad objetivo: {brief['edad_objetivo']} años")
    print("-" * 50)
    
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
    orchestrator = StoryOrchestrator(
        story_id=story_id,
        mode_verificador_qa=True,
        pipeline_version='v2'  # Usar versión 2
    )
    
    # Ejecutar el pipeline
    print("🎬 Ejecutando pipeline completo...")
    print("⏳ Esto puede tomar varios minutos...\n")
    
    try:
        result = orchestrator.process_story(
            brief=brief
        )
        
        if result.get("status") == "completed":
            print("\n✅ Pipeline completado exitosamente!")
            
            # Mostrar resumen de resultados
            print("\n📊 Resumen de ejecución:")
            print(f"  • Tiempo total: {result.get('total_time', 'N/A')} segundos")
            print(f"  • Agentes ejecutados: {result.get('agents_completed', 'N/A')}")
            
            # Verificar archivo final
            validador_path = story_path / "12_validador.json"
            if validador_path.exists():
                with open(validador_path, 'r', encoding='utf-8') as f:
                    cuento = json.load(f)
                    print(f"\n📖 Cuento generado:")
                    print(f"  • Título: {cuento.get('titulo', 'Sin título')}")
                    print(f"  • Páginas: {len(cuento.get('paginas', []))}")
                    
                    # Mostrar primera página como muestra
                    if cuento.get('paginas'):
                        print(f"\n📄 Primera página (muestra):")
                        print(f"  {cuento['paginas'][0].get('texto', 'Sin texto')[:200]}...")
            
            # Verificar métricas de QA
            manifest_path = story_path / "manifest.json"
            if manifest_path.exists():
                with open(manifest_path, 'r', encoding='utf-8') as f:
                    manifest = json.load(f)
                    if 'agent_metrics' in manifest:
                        print(f"\n📈 Métricas de calidad (QA):")
                        for agent, metrics in manifest['agent_metrics'].items():
                            if 'qa_score' in metrics:
                                score = metrics['qa_score']
                                status = "✅" if score >= 3.5 else "⚠️"
                                print(f"  {status} {agent}: {score}/5")
            
            print(f"\n📁 Resultados guardados en: {story_path}")
            print("🎉 Test completado con éxito!")
            
        else:
            print(f"\n❌ Error en el pipeline: {result.get('error', 'Error desconocido')}")
            print(f"📁 Logs disponibles en: {story_path}/logs/")
            
    except Exception as e:
        print(f"\n❌ Error ejecutando el test: {e}")
        import traceback
        traceback.print_exc()
        print(f"📁 Logs disponibles en: {story_path}/logs/")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())