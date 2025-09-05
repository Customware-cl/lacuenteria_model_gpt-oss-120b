#!/usr/bin/env python3
"""
Test completo del pipeline v3 con Sofía y Max - Versión mejorada con crítico
"""

import json
import time
import requests
from pathlib import Path
import sys
from datetime import datetime

def test_flujo_v3_mejorado():
    """Ejecuta prueba completa del flujo v3 con agentes mejorados"""
    
    # Configuración
    base_url = "http://localhost:5000"
    story_id = f"sofia-max-v3-mejorado-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Brief completo de Sofía y Max
    payload = {
        "story_id": story_id,
        "personajes": ["Sofía (niña valiente, 7 años, curiosa)", "Max (niño creativo, 6 años, soñador)"],
        "historia": "Sofía y Max encuentran una puerta mágica en el bosque que los lleva a un reino donde las emociones tienen forma física. Deben ayudar al Rey Alegría a recuperar su risa robada por la Bruja del Olvido, aprendiendo que todas las emociones son importantes.",
        "mensaje_a_transmitir": "Validar y expresar todas las emociones es saludable. La tristeza, el miedo y la alegría son parte de nosotros.",
        "edad_objetivo": 5,
        "relacion_personajes": ["Sofía y Max son mejores amigos del vecindario"],
        "valores": ["valentía", "amistad", "aceptación emocional"],
        "comportamientos": ["trabajo en equipo", "expresar sentimientos", "pedir ayuda cuando la necesitan"],
        "numero_paginas": 10,
        "pipeline_version": "v3"
    }
    
    print(f"\n{'='*60}")
    print(f"🚀 INICIANDO TEST V3 MEJORADO")
    print(f"{'='*60}")
    print(f"📚 Story ID: {story_id}")
    print(f"👥 Personajes: Sofía y Max")
    print(f"🎯 Pipeline: v3 con agentes mejorados")
    
    # 1. Crear historia
    print("\n📤 Enviando request de creación...")
    try:
        response = requests.post(
            f"{base_url}/api/stories/create",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code != 202:
            print(f"❌ Error creando historia: {response.status_code}")
            print(response.text)
            return None
            
        print("✅ Historia iniciada correctamente")
        
    except Exception as e:
        print(f"❌ Error conectando con servidor: {e}")
        return None
    
    # 2. Monitorear progreso
    print("\n⏳ Procesando historia...")
    print("-" * 40)
    
    max_wait = 600  # 10 minutos máximo
    check_interval = 5
    elapsed = 0
    last_agent = None
    
    while elapsed < max_wait:
        try:
            status_response = requests.get(f"{base_url}/api/stories/{story_id}/status")
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                current_status = status_data.get("status", "unknown")
                current_agent = status_data.get("current_agent", "")
                
                # Mostrar progreso por agente
                if current_agent and current_agent != last_agent:
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    print(f"[{timestamp}] 🔄 Agente: {current_agent}")
                    last_agent = current_agent
                
                if current_status == "completed":
                    print("\n✅ Historia completada exitosamente!")
                    break
                elif current_status == "error":
                    error_msg = status_data.get("error", "Error desconocido")
                    print(f"\n❌ Error en el procesamiento: {error_msg}")
                    return None
                    
            time.sleep(check_interval)
            elapsed += check_interval
            
        except Exception as e:
            print(f"⚠️ Error verificando estado: {e}")
            time.sleep(check_interval)
            elapsed += check_interval
    
    if elapsed >= max_wait:
        print("\n⏰ Timeout esperando completación")
        return None
    
    # 3. Obtener resultado
    print("\n📥 Obteniendo resultado final...")
    try:
        result_response = requests.get(f"{base_url}/api/stories/{story_id}/result")
        
        if result_response.status_code == 200:
            result_data = result_response.json()
            
            # Mostrar resumen
            print("\n" + "="*60)
            print("📖 HISTORIA GENERADA")
            print("="*60)
            
            if "titulo" in result_data:
                print(f"\n📚 Título: {result_data['titulo']}")
            
            # Contar páginas
            paginas = result_data.get("paginas", {})
            print(f"📄 Páginas generadas: {len(paginas)}")
            
            # Verificar AMC
            if paginas:
                primera_pagina = paginas.get("1", {})
                prompt = primera_pagina.get("prompt", {})
                if "amc" in prompt:
                    print(f"🦋 AMC detectado: Sí")
                    print(f"   - Acción: {prompt['amc'].get('accion', 'N/A')}")
                    print(f"   - Posición: {prompt['amc'].get('posicion', 'N/A')}")
            
            # Verificar musicalidad en texto
            if paginas:
                muestra_texto = paginas.get("1", {}).get("texto", "")
                tiene_saltos = "\\n" in muestra_texto or "\n" in muestra_texto
                print(f"🎵 Saltos de línea en texto: {'Sí' if tiene_saltos else 'No'}")
            
            # Guardar resultado
            output_dir = Path(f"runs/{story_id}")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            with open(output_dir / "04_consolidador_v3.json", "w", encoding="utf-8") as f:
                json.dump(result_data, f, ensure_ascii=False, indent=2)
            
            print(f"\n💾 Resultado guardado en: {output_dir}/04_consolidador_v3.json")
            
            return story_id
            
        else:
            print(f"❌ Error obteniendo resultado: {result_response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Error obteniendo resultado: {e}")
        return None

def evaluar_con_critico(story_id):
    """Ejecuta el agente crítico sobre la historia generada"""
    
    print("\n" + "="*60)
    print("🔍 EVALUACIÓN CON CRÍTICO V2")
    print("="*60)
    
    # Cargar la historia generada
    story_path = Path(f"runs/{story_id}/04_consolidador_v3.json")
    
    if not story_path.exists():
        print("❌ No se encontró el archivo de la historia")
        return None
    
    with open(story_path, "r", encoding="utf-8") as f:
        historia_data = json.load(f)
    
    print(f"📚 Evaluando: {historia_data.get('titulo', 'Sin título')}")
    print(f"📄 Páginas: {len(historia_data.get('paginas', {}))}")
    
    # Preparar payload para el crítico
    payload = {
        "titulo": historia_data.get("titulo", "Sin título"),
        "paginas": historia_data.get("paginas", {}),
        "portada": historia_data.get("portada", {}),
        "loader": historia_data.get("loader", [])
    }
    
    # Llamar al endpoint de evaluación
    url = f"http://localhost:5000/api/stories/{story_id}/evaluate"
    
    try:
        print("\n⏳ Ejecutando evaluación crítica...")
        response = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=120
        )
        
        if response.status_code == 200:
            evaluacion = response.json()
            
            # Verificar estructura
            if "evaluacion_critica" in evaluacion:
                eval_data = evaluacion["evaluacion_critica"]
            else:
                eval_data = evaluacion
            
            print("\n" + "-"*40)
            print("📊 RESULTADOS DE EVALUACIÓN")
            print("-"*40)
            
            # Nota general
            if "nota_general" in eval_data:
                nota = eval_data["nota_general"]
                print(f"\n🎯 PUNTUACIÓN GENERAL: {nota.get('puntuacion', 'N/A')}/5")
                print(f"📝 Nivel: {nota.get('nivel', 'N/A')}")
                print(f"💭 Resumen: {nota.get('resumen', 'N/A')}")
            
            # Puntuaciones por tópico
            if "notas_por_topico" in eval_data:
                print("\n📈 DETALLES POR ÁREA:")
                
                # Texto narrativo
                texto = eval_data["notas_por_topico"].get("texto_narrativo", {})
                if texto:
                    print(f"\n📖 Texto Narrativo: {texto.get('puntuacion_promedio', 'N/A')}/5")
                    contenido = texto.get("contenido_narrativo", {})
                    if contenido and "notas_por_ambito" in contenido:
                        for ambito, nota in contenido["notas_por_ambito"].items():
                            print(f"   • {ambito}: {nota}/5")
                    
                    # Estructura poética (crítica anterior)
                    poetica = texto.get("estructura_poetica", {})
                    if poetica:
                        print(f"\n🎵 Estructura Poética: {poetica.get('puntuacion_promedio', 'N/A')}/5")
                        if "notas_por_ambito" in poetica:
                            for ambito, nota in poetica["notas_por_ambito"].items():
                                print(f"   • {ambito}: {nota}/5")
                
                # Prompts de imágenes
                prompts = eval_data["notas_por_topico"].get("prompts_imagenes", {})
                if prompts:
                    print(f"\n🎨 Prompts de Imágenes: {prompts.get('puntuacion_promedio', 'N/A')}/5")
                    if "notas_por_ambito" in prompts:
                        for ambito, nota in prompts["notas_por_ambito"].items():
                            print(f"   • {ambito}: {nota}/5")
                
                # Mensajes de carga
                loaders = eval_data["notas_por_topico"].get("mensajes_carga", {})
                if loaders:
                    print(f"\n⏳ Mensajes de Carga: {loaders.get('puntuacion_promedio', 'N/A')}/5")
                    if "notas_por_ambito" in loaders:
                        for ambito, nota in loaders["notas_por_ambito"].items():
                            print(f"   • {ambito}: {nota}/5")
            
            # Recomendaciones
            if "recomendaciones_mejora" in eval_data:
                recom = eval_data["recomendaciones_mejora"]
                if "mejoras_prioritarias" in recom:
                    print("\n💡 MEJORAS PRIORITARIAS:")
                    for mejora in recom["mejoras_prioritarias"]:
                        print(f"   → {mejora}")
            
            # Decisión de publicación
            if "decision_publicacion" in eval_data:
                decision = eval_data["decision_publicacion"]
                print(f"\n📚 DECISIÓN FINAL:")
                print(f"   Apto para publicar: {decision.get('apto_para_publicar', 'N/A')}")
                print(f"   Nivel de revisión: {decision.get('nivel_revision_requerido', 'N/A')}")
                print(f"   Justificación: {decision.get('justificacion', 'N/A')}")
            
            # Guardar evaluación
            output_file = Path(f"runs/{story_id}/13_critico_evaluation.json")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(evaluacion, f, ensure_ascii=False, indent=2)
            
            print(f"\n💾 Evaluación guardada en: {output_file}")
            
            return eval_data.get("nota_general", {}).get("puntuacion", 0)
            
        else:
            print(f"❌ Error en evaluación: {response.status_code}")
            print(response.text)
            return None
            
    except Exception as e:
        print(f"❌ Error ejecutando crítico: {e}")
        return None

def comparar_evaluaciones(nueva_puntuacion):
    """Compara con la evaluación anterior"""
    
    print("\n" + "="*60)
    print("📊 COMPARACIÓN DE EVALUACIONES")
    print("="*60)
    
    puntuacion_anterior = 3.8
    
    print(f"\n📈 Puntuación anterior: {puntuacion_anterior}/5")
    print(f"📈 Puntuación nueva: {nueva_puntuacion}/5")
    
    diferencia = nueva_puntuacion - puntuacion_anterior
    
    if diferencia > 0:
        print(f"\n✅ MEJORA: +{diferencia:.1f} puntos")
        print("   Las mejoras en musicalidad y variedad visual tuvieron efecto positivo")
    elif diferencia < 0:
        print(f"\n⚠️ DESCENSO: {diferencia:.1f} puntos")
        print("   Revisar si las modificaciones afectaron negativamente otros aspectos")
    else:
        print(f"\n➖ SIN CAMBIOS: Misma puntuación")
        print("   Las mejoras no fueron suficientes o se compensaron con otros aspectos")
    
    print("\n📝 ÁREAS ANTERIORMENTE CRÍTICAS:")
    print("   • Estructura poética: 2.5/5 → Verificar si mejoró")
    print("   • Variedad visual: 3.5/5 → Verificar si mejoró")
    print("   • Mensajes de carga: 3.5/5 → Verificar si mejoró")

def main():
    print("\n🎯 TEST V3 MEJORADO CON EVALUACIÓN CRÍTICA")
    print("="*60)
    
    # Ejecutar prueba v3
    story_id = test_flujo_v3_mejorado()
    
    if story_id:
        # Evaluar con crítico
        nueva_puntuacion = evaluar_con_critico(story_id)
        
        if nueva_puntuacion:
            # Comparar con evaluación anterior
            comparar_evaluaciones(nueva_puntuacion)
            
            print("\n" + "="*60)
            print("✅ TEST COMPLETO FINALIZADO")
            print(f"📁 Todos los archivos en: runs/{story_id}/")
            print("="*60)
        else:
            print("\n❌ No se pudo completar la evaluación crítica")
    else:
        print("\n❌ No se pudo completar la generación de la historia")

if __name__ == "__main__":
    main()