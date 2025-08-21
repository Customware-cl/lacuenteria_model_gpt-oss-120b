#!/usr/bin/env python3
"""
Script de prueba para el consolidador de métricas.
Prueba con una historia que tiene logs completos y con una que no tiene logs.
"""
import json
import sys
import os
sys.path.append('src')

from metrics_consolidator import consolidate_agent_metrics

def test_with_complete_logs():
    """Prueba con una historia que tiene logs completos"""
    print("=" * 60)
    print("TEST 1: Historia con logs completos")
    print("=" * 60)
    
    # Usar una historia que sabemos que tiene logs completos
    story_id = "test-emilia-20250821-002844"
    
    print(f"\nConsolidando métricas para: {story_id}")
    metrics = consolidate_agent_metrics(story_id)
    
    if metrics:
        print("\n✅ Métricas consolidadas exitosamente")
        print("\n📊 RESUMEN GLOBAL:")
        print(json.dumps(metrics["resumen_global"], indent=2, ensure_ascii=False))
        
        print("\n📈 ESTADÍSTICAS DE TEMPERATURAS:")
        print(json.dumps(metrics["estadisticas"]["temperaturas"], indent=2, ensure_ascii=False))
        
        print("\n⏱️ ESTADÍSTICAS DE TIEMPOS:")
        print(json.dumps(metrics["estadisticas"]["tiempos"], indent=2, ensure_ascii=False))
        
        print("\n⭐ ESTADÍSTICAS DE QA SCORES:")
        print(json.dumps(metrics["estadisticas"]["qa_scores"], indent=2, ensure_ascii=False))
        
        print("\n📋 DETALLE POR AGENTE (primeros 3):")
        for agent in metrics["detalle_agentes"][:3]:
            if agent["disponible"]:
                print(f"\n  • {agent['agente']}:")
                print(f"    - Temperatura: {agent['temperatura']}")
                print(f"    - Tiempo: {agent['tiempo_ejecucion']}s")
                print(f"    - QA Promedio: {agent['qa_promedio']}")
                print(f"    - Reintentos: {agent['reintentos']}")
    else:
        print("\n❌ No se pudieron consolidar métricas")


def test_without_logs():
    """Prueba con una historia que no tiene logs"""
    print("\n" + "=" * 60)
    print("TEST 2: Historia sin logs")
    print("=" * 60)
    
    # Usar una historia inexistente
    story_id = "historia-inexistente-123"
    
    print(f"\nConsolidando métricas para: {story_id}")
    metrics = consolidate_agent_metrics(story_id)
    
    if metrics:
        print("\n❌ Error: Se esperaba None pero se obtuvieron métricas")
        print(json.dumps(metrics, indent=2, ensure_ascii=False))
    else:
        print("\n✅ Correcto: Retornó None para historia sin logs")


def test_partial_logs():
    """Prueba con una historia que tiene logs parciales"""
    print("\n" + "=" * 60)
    print("TEST 3: Historia con logs parciales")
    print("=" * 60)
    
    # Usar una historia con pocos agentes ejecutados
    story_id = "quick-test-020844"
    
    print(f"\nConsolidando métricas para: {story_id}")
    metrics = consolidate_agent_metrics(story_id)
    
    if metrics:
        print("\n✅ Métricas consolidadas (parciales)")
        print(f"Agentes ejecutados: {metrics['resumen_global']['agentes_ejecutados']}/{metrics['resumen_global']['total_agentes']}")
        print(f"Agentes faltantes: {metrics['metadata']['agentes_faltantes']}")
        
        print("\n📋 Agentes disponibles:")
        for agent in metrics["detalle_agentes"]:
            status = "✓" if agent["disponible"] else "✗"
            print(f"  [{status}] {agent['agente']}")
    else:
        print("\n⚠️ No hay suficientes datos para consolidar (menos de 3 agentes)")


def main():
    """Ejecuta todas las pruebas"""
    print("\n🧪 PRUEBAS DEL CONSOLIDADOR DE MÉTRICAS")
    print("=" * 60)
    
    try:
        test_with_complete_logs()
        test_without_logs()
        test_partial_logs()
        
        print("\n" + "=" * 60)
        print("✅ TODAS LAS PRUEBAS COMPLETADAS")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error durante las pruebas: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()