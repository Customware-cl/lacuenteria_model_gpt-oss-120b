#!/usr/bin/env python3
"""
Script para probar el endpoint /evaluate con métricas consolidadas.
Requiere que el servidor esté corriendo en puerto 5000.
"""
import requests
import json
import sys

def test_evaluate_endpoint(story_id):
    """Prueba el endpoint /evaluate para una historia"""
    url = f"http://localhost:5000/api/stories/{story_id}/evaluate"
    
    print(f"\n🔍 Probando evaluación para: {story_id}")
    print(f"   URL: {url}")
    print("   Ejecutando agente crítico y consolidando métricas...")
    
    try:
        response = requests.post(url, timeout=120)
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"\n✅ Evaluación completada exitosamente")
            print(f"   Status: {data['status']}")
            print(f"   Métricas disponibles: {data.get('metricas_disponibles', False)}")
            
            # Mostrar resumen de evaluación crítica
            if "evaluacion_critica" in data:
                eval_critica = data["evaluacion_critica"]
                if "nota_general" in eval_critica:
                    nota = eval_critica["nota_general"]
                    print(f"\n📝 EVALUACIÓN CRÍTICA:")
                    print(f"   Puntuación: {nota.get('puntuacion', 'N/A')}")
                    print(f"   Nivel: {nota.get('nivel', 'N/A')}")
                    print(f"   Resumen: {nota.get('resumen', 'N/A')}")
            
            # Mostrar métricas consolidadas si están disponibles
            if data.get("metricas_disponibles") and "metricas_pipeline" in data:
                metricas = data["metricas_pipeline"]
                print(f"\n📊 MÉTRICAS CONSOLIDADAS:")
                
                if "resumen_global" in metricas:
                    resumen = metricas["resumen_global"]
                    print(f"\n   Resumen Global:")
                    print(f"   • Agentes ejecutados: {resumen.get('agentes_ejecutados', 'N/A')}/{resumen.get('total_agentes', 'N/A')}")
                    print(f"   • Tiempo total: {resumen.get('tiempo_total_segundos', 'N/A')}s")
                    print(f"   • QA promedio global: {resumen.get('promedio_qa_global', 'N/A')}")
                    print(f"   • Tasa éxito primera: {resumen.get('tasa_exito_primera', 'N/A')}%")
                
                if "estadisticas" in metricas:
                    stats = metricas["estadisticas"]
                    
                    if "temperaturas" in stats:
                        temps = stats["temperaturas"]
                        print(f"\n   Temperaturas:")
                        print(f"   • Rango: {temps.get('min', 'N/A')} - {temps.get('max', 'N/A')}")
                        print(f"   • Promedio: {temps.get('promedio', 'N/A')}")
                    
                    if "tiempos" in stats:
                        tiempos = stats["tiempos"]
                        if tiempos.get("agente_mas_lento"):
                            print(f"\n   Agente más lento: {tiempos['agente_mas_lento']['agente']} ({tiempos['agente_mas_lento']['tiempo']}s)")
                        if tiempos.get("agente_mas_rapido"):
                            print(f"   Agente más rápido: {tiempos['agente_mas_rapido']['agente']} ({tiempos['agente_mas_rapido']['tiempo']}s)")
                    
                    if "qa_scores" in stats:
                        qa = stats["qa_scores"]
                        if qa.get("distribucion"):
                            print(f"\n   Distribución QA Scores: {qa['distribucion']}")
                        if qa.get("agentes_bajo_umbral"):
                            print(f"   Agentes bajo umbral: {qa['agentes_bajo_umbral'] or 'Ninguno'}")
            
            else:
                print(f"\n⚠️ Métricas no disponibles: {data.get('metricas_nota', '')}")
            
            # Guardar resultado completo
            output_file = f"test_evaluate_{story_id}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"\n💾 Resultado completo guardado en: {output_file}")
            
        elif response.status_code == 404:
            print(f"\n❌ Historia no encontrada: {story_id}")
        elif response.status_code == 400:
            print(f"\n❌ Historia no completada (falta validador)")
        else:
            print(f"\n❌ Error: Status {response.status_code}")
            print(f"   Respuesta: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: No se pudo conectar al servidor")
        print("   Asegúrate de que el servidor esté corriendo: python3 src/api_server.py")
    except requests.exceptions.Timeout:
        print("\n❌ Error: Timeout esperando respuesta del servidor")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")


def main():
    """Función principal"""
    print("\n🧪 PRUEBA DEL ENDPOINT /evaluate CON MÉTRICAS CONSOLIDADAS")
    print("=" * 60)
    
    # Historia con ejecución completa
    story_id = "test-emilia-20250821-002844"
    
    # Verificar que el servidor esté corriendo
    try:
        response = requests.get("http://localhost:5000/health", timeout=5)
        server_status = response.json()
        print(f"✅ Servidor activo - Estado: {server_status['status']}")
    except:
        print("❌ El servidor no está respondiendo")
        print("   Ejecuta: python3 src/api_server.py")
        sys.exit(1)
    
    # Ejecutar prueba
    test_evaluate_endpoint(story_id)
    
    print("\n" + "=" * 60)
    print("✅ PRUEBA COMPLETADA")
    print("=" * 60)


if __name__ == "__main__":
    main()