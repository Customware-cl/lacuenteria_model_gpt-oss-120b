#!/usr/bin/env python3
"""
Script de prueba para el endpoint de evaluación crítica
"""

import requests
import json
import sys
from datetime import datetime

# Configuración
API_BASE_URL = "http://localhost:5000"

def test_evaluate_story(story_id):
    """
    Prueba el endpoint de evaluación crítica
    
    Args:
        story_id: ID de la historia a evaluar
    """
    print(f"🔍 Probando evaluación crítica para historia: {story_id}")
    print("-" * 60)
    
    # Ejecutar evaluación crítica
    url = f"{API_BASE_URL}/api/stories/{story_id}/evaluate"
    
    print(f"📮 POST {url}")
    
    try:
        response = requests.post(url, timeout=120)
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if "evaluacion_critica" in data:
                eval_critica = data["evaluacion_critica"]
                
                # Mostrar estructura en cascada
                print("\n✅ Evaluación Crítica Exitosa!")
                print("=" * 60)
                
                # Nota general
                if "nota_general" in eval_critica:
                    ng = eval_critica["nota_general"]
                    print(f"\n📊 NOTA GENERAL: {ng.get('puntuacion', 0)}/5.0")
                    print(f"   Nivel: {ng.get('nivel', 'N/A')}")
                    print(f"   Resumen: {ng.get('resumen', 'N/A')}")
                
                # Notas por tópico
                if "notas_por_topico" in eval_critica:
                    npt = eval_critica["notas_por_topico"]
                    
                    # Prompts de imágenes
                    if "prompts_imagenes" in npt:
                        pi = npt["prompts_imagenes"]
                        print(f"\n🎨 PROMPTS DE IMÁGENES: {pi.get('puntuacion_promedio', 0)}/5.0")
                        print(f"   Nivel: {pi.get('nivel', 'N/A')}")
                        
                        if "notas_por_ambito" in pi:
                            print("   Desglose:")
                            for ambito, nota in pi["notas_por_ambito"].items():
                                print(f"     - {ambito}: {nota}/5.0")
                    
                    # Mensajes de carga
                    if "mensajes_carga" in npt:
                        mc = npt["mensajes_carga"]
                        print(f"\n💬 MENSAJES DE CARGA: {mc.get('puntuacion_promedio', 0)}/5.0")
                        print(f"   Nivel: {mc.get('nivel', 'N/A')}")
                        
                        if "notas_por_ambito" in mc:
                            print("   Desglose:")
                            for ambito, nota in mc["notas_por_ambito"].items():
                                print(f"     - {ambito}: {nota}/5.0")
                    
                    # Texto narrativo
                    if "texto_narrativo" in npt:
                        tn = npt["texto_narrativo"]
                        print(f"\n📖 TEXTO NARRATIVO: {tn.get('puntuacion_promedio', 0)}/5.0")
                        print(f"   Nivel: {tn.get('nivel', 'N/A')}")
                        
                        if "estructura_poetica" in tn:
                            ep = tn["estructura_poetica"]
                            print(f"\n   📝 Estructura Poética: {ep.get('puntuacion_promedio', 0)}/5.0")
                            if "notas_por_ambito" in ep:
                                for ambito, nota in ep["notas_por_ambito"].items():
                                    print(f"     - {ambito}: {nota}/5.0")
                        
                        if "contenido_narrativo" in tn:
                            cn = tn["contenido_narrativo"]
                            print(f"\n   📚 Contenido Narrativo: {cn.get('puntuacion_promedio', 0)}/5.0")
                            if "notas_por_ambito" in cn:
                                for ambito, nota in cn["notas_por_ambito"].items():
                                    print(f"     - {ambito}: {nota}/5.0")
                
                # Decisión de publicación
                if "decision_publicacion" in eval_critica:
                    dp = eval_critica["decision_publicacion"]
                    print("\n" + "=" * 60)
                    print("📋 DECISIÓN DE PUBLICACIÓN")
                    print(f"   Apto para publicar: {'✅ SÍ' if dp.get('apto_para_publicar') else '❌ NO'}")
                    print(f"   Requiere revisión: {'⚠️ SÍ' if dp.get('requiere_revision') else '✅ NO'}")
                    print(f"   Nivel de revisión: {dp.get('nivel_revision_requerido', 'N/A')}")
                    print(f"   Justificación: {dp.get('justificacion', 'N/A')}")
                
                # Recomendaciones
                if "recomendaciones_mejora" in eval_critica:
                    rm = eval_critica["recomendaciones_mejora"]
                    if "mejoras_prioritarias" in rm:
                        print("\n💡 MEJORAS PRIORITARIAS:")
                        for mejora in rm["mejoras_prioritarias"]:
                            print(f"   • {mejora}")
                
                # Guardar resultado completo
                output_file = f"evaluacion_critica_{story_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print(f"\n💾 Resultado completo guardado en: {output_file}")
                
            else:
                print("\n⚠️ Respuesta sin evaluación crítica:")
                print(json.dumps(data, indent=2))
                
        elif response.status_code == 206:  # Partial Content
            data = response.json()
            print("\n⚠️ Evaluación parcial con observaciones:")
            
            if "qa_scores" in data:
                print("\n📊 Puntuaciones QA:")
                for key, value in data["qa_scores"].items():
                    print(f"   - {key}: {value}")
            
            if "qa_issues" in data:
                print("\n❌ Problemas detectados:")
                for issue in data["qa_issues"]:
                    print(f"   - {issue}")
                    
        else:
            print(f"\n❌ Error: {response.status_code}")
            print(response.text)
            
    except requests.exceptions.Timeout:
        print("⏱️ Timeout - la evaluación está tardando más de lo esperado")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_get_result_with_critic(story_id):
    """
    Prueba obtener el resultado con evaluación crítica incluida
    
    Args:
        story_id: ID de la historia
    """
    print(f"\n📥 Obteniendo resultado con evaluación crítica para: {story_id}")
    print("-" * 60)
    
    url = f"{API_BASE_URL}/api/stories/{story_id}/result"
    
    print(f"📮 GET {url}")
    
    try:
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"✅ Historia: {story_id}")
            print(f"   Estado: {data.get('status')}")
            
            # Verificar si incluye evaluación crítica
            if "evaluacion_critica" in data:
                eval_critica = data["evaluacion_critica"]
                ng = eval_critica.get("nota_general", {})
                print(f"\n📊 Evaluación Crítica Incluida:")
                print(f"   Puntuación: {ng.get('puntuacion', 0)}/5.0")
                print(f"   Nivel: {ng.get('nivel', 'N/A')}")
                print(f"   ✅ La evaluación crítica está integrada en el resultado")
            else:
                print("\n⚠️ No hay evaluación crítica en el resultado")
                
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Función principal"""
    if len(sys.argv) < 2:
        print("Uso: python test_critico_api.py <story_id>")
        print("Ejemplo: python test_critico_api.py emilia-test-001")
        sys.exit(1)
    
    story_id = sys.argv[1]
    
    print("🚀 Prueba de API - Agente Crítico")
    print("=" * 60)
    
    # Probar evaluación crítica
    test_evaluate_story(story_id)
    
    # Esperar un momento y probar obtener resultado con crítica
    print("\n" + "=" * 60)
    test_get_result_with_critic(story_id)
    
    print("\n✨ Pruebas completadas")

if __name__ == "__main__":
    main()