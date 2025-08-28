#!/usr/bin/env python3
"""
Script de prueba para el sistema v2 con feedback loop mejorado
Verifica que el analizador de conflictos y el dashboard funcionan correctamente
"""
import json
import logging
from pathlib import Path
from src.orchestrator import StoryOrchestrator
from src.conflict_analyzer import get_conflict_analyzer

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_v2_system():
    """Prueba el sistema v2 con análisis de conflictos"""
    
    # Brief de prueba
    brief = {
        "personajes": ["Emilia, una niña de 4 años curiosa"],
        "historia": "Emilia aprende a compartir sus juguetes cuando su amigo está triste",
        "mensaje_a_transmitir": "Compartir nos hace más felices",
        "edad_objetivo": 4
    }
    
    print("=" * 60)
    print("PRUEBA DEL SISTEMA V2 CON FEEDBACK LOOP MEJORADO")
    print("=" * 60)
    
    # Crear orquestador con modo v2
    story_id = f"test-v2-feedback"
    orchestrator = StoryOrchestrator(
        story_id=story_id,
        mode_verificador_qa=True,  # Usar verificador QA
        pipeline_version='v2'      # Usar pipeline v2
    )
    
    print(f"\nStory ID: {story_id}")
    print(f"Pipeline: v2")
    print(f"Verificador QA: Activado")
    
    # Procesar solo los primeros 3 agentes para prueba rápida
    print("\nProcesando primeros 3 agentes del pipeline...")
    
    # Modificar temporalmente el pipeline para prueba
    from src.config import load_version_config
    v2_config = load_version_config('v2')
    original_pipeline = v2_config['pipeline'].copy()
    v2_config['pipeline'] = v2_config['pipeline'][:3]  # Solo primeros 3
    
    try:
        # Procesar historia
        result = orchestrator.process_story(brief)
        
        print("\n" + "=" * 60)
        print("RESULTADO DEL PROCESAMIENTO")
        print("=" * 60)
        print(f"Estado: {result.get('status')}")
        
        if result.get('status') == 'success':
            print("✅ Pipeline completado exitosamente")
        else:
            print(f"⚠️ Pipeline completado con estado: {result.get('status')}")
        
        # Mostrar QA scores
        if 'qa_scores' in result:
            print(f"\nQA Scores generales: {result['qa_scores']}")
        
        # Cargar y mostrar análisis de conflictos
        analyzer = get_conflict_analyzer('v2')
        
        print("\n" + "=" * 60)
        print("DASHBOARD DE CONFLICTOS")
        print("=" * 60)
        
        # Cargar dashboard
        dashboard_path = Path(__file__).parent / 'flujo/v2/qa_conflict_dashboard.json'
        if dashboard_path.exists():
            with open(dashboard_path, 'r', encoding='utf-8') as f:
                dashboard = json.load(f)
            
            print(f"Total de conflictos analizados: {dashboard.get('total_conflicts_analyzed', 0)}")
            
            if dashboard.get('conflict_patterns'):
                print("\nPatrones de conflicto detectados:")
                for agent, patterns in dashboard['conflict_patterns'].items():
                    print(f"\n  {agent}:")
                    for pattern_id, data in patterns.items():
                        print(f"    - {pattern_id}: {data.get('count', 0)} ocurrencias")
                        if data.get('recommendation'):
                            print(f"      Recomendación: {data['recommendation']}")
            else:
                print("No se detectaron patrones de conflicto (¡Buena señal!)")
            
            if dashboard.get('agent_conflicts'):
                print("\nConflictos entre agentes:")
                for conflict, data in dashboard['agent_conflicts'].items():
                    print(f"  - {conflict}: {data.get('count', 0)} ocurrencias")
        else:
            print("Dashboard no encontrado (se creará en la primera ejecución)")
        
        # Generar reporte
        print("\n" + "=" * 60)
        print("REPORTE DE MEJORAS SUGERIDAS")
        print("=" * 60)
        report = analyzer.generate_improvement_report()
        print(report)
        
    finally:
        # Restaurar pipeline original
        v2_config['pipeline'] = original_pipeline
    
    print("\n" + "=" * 60)
    print("PRUEBA COMPLETADA")
    print("=" * 60)
    print(f"Revisa los archivos en: runs/{story_id}/")
    print(f"Dashboard en: flujo/v2/qa_conflict_dashboard.json")

if __name__ == "__main__":
    test_v2_system()