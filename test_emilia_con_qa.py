#!/usr/bin/env python3
"""
Prueba completa del sistema con verificador QA usando el brief de Emilia.
Ejecuta el pipeline completo y muestra el progreso con las evaluaciones QA reales.
"""
import requests
import json
import time
from datetime import datetime

def crear_historia_emilia():
    """Crea una nueva historia con el brief de Emilia"""
    
    url = "http://localhost:5000/api/stories/create"
    
    payload = {
        "story_id": f"emilia-qa-test-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        "personajes": ["Emilia", "Unicornio"],
        "historia": "Emilia juega sola en su jardín cuando descubre un unicornio mágico. El unicornio ha perdido su voz y no puede hablar. Emilia, que también es no verbal, le enseña a comunicarse con gestos y señas. Juntos descubren que pueden crear magia cuando combinan sus formas únicas de expresión. La sombra del silencio que seguía al unicornio se desvanece cuando aprende que hay muchas formas de decir 'te quiero'.",
        "mensaje_a_transmitir": "La comunicación va más allá de las palabras habladas, y cada forma de expresión es válida y hermosa",
        "edad_objetivo": 5
    }
    
    print("\n🚀 INICIANDO GENERACIÓN CON VERIFICADOR QA")
    print("=" * 60)
    print(f"Story ID: {payload['story_id']}")
    print(f"Personajes: {', '.join(payload['personajes'])}")
    print(f"Edad objetivo: {payload['edad_objetivo']} años")
    print("=" * 60)
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 202:
            print("✅ Historia iniciada correctamente")
            return payload["story_id"]
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def monitorear_progreso(story_id):
    """Monitorea el progreso mostrando las evaluaciones QA"""
    
    url = f"http://localhost:5000/api/stories/{story_id}/status"
    
    print("\n📊 MONITOREANDO PROGRESO CON VERIFICADOR QA")
    print("-" * 60)
    
    agentes_procesados = set()
    ultimo_estado = None
    intentos_sin_cambio = 0
    max_intentos = 180  # 15 minutos máximo
    
    while intentos_sin_cambio < max_intentos:
        try:
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                estado = data.get("status")
                agente_actual = data.get("current_agent", "")
                
                # Detectar cambio de agente
                if agente_actual and agente_actual not in agentes_procesados:
                    agentes_procesados.add(agente_actual)
                    print(f"\n🤖 Agente: {agente_actual}")
                    print(f"   Estado: Ejecutando...")
                
                # Si el estado cambió, mostrar info
                if estado != ultimo_estado:
                    ultimo_estado = estado
                    intentos_sin_cambio = 0
                    
                    if estado == "completed":
                        print("\n✅ GENERACIÓN COMPLETADA")
                        return True
                    elif estado == "error":
                        print(f"\n❌ ERROR: {data.get('error', 'Desconocido')}")
                        return False
                else:
                    intentos_sin_cambio += 1
                
                # Mostrar punto de progreso cada 10 segundos
                if intentos_sin_cambio % 2 == 0:
                    print(".", end="", flush=True)
                
            time.sleep(5)
            
        except KeyboardInterrupt:
            print("\n\n⚠️ Interrumpido por usuario")
            return False
        except Exception as e:
            print(f"\n❌ Error monitoreando: {e}")
            intentos_sin_cambio += 1
            time.sleep(5)
    
    print("\n⏱️ Timeout - La generación está tomando demasiado tiempo")
    return False

def obtener_metricas_qa(story_id):
    """Obtiene las métricas QA consolidadas"""
    
    print("\n📈 OBTENIENDO MÉTRICAS QA DEL VERIFICADOR")
    print("-" * 60)
    
    # Primero intentar obtener logs para ver QA scores
    url_logs = f"http://localhost:5000/api/stories/{story_id}/logs"
    
    try:
        response = requests.get(url_logs, timeout=10)
        
        if response.status_code == 200:
            logs = response.json()
            
            print("\n📊 QA SCORES POR AGENTE (Verificador Independiente):")
            print("-" * 40)
            
            for agente, log_data in logs.items():
                if isinstance(log_data, list) and log_data:
                    ultimo_log = log_data[-1]
                    qa_scores = ultimo_log.get("qa_scores", {})
                    
                    if qa_scores and "promedio" in qa_scores:
                        promedio = qa_scores["promedio"]
                        status = "✅" if promedio >= 4.0 else "❌"
                        reintentos = ultimo_log.get("retry_count", 0)
                        
                        print(f"\n{agente}:")
                        print(f"  Promedio QA: {promedio}/5 {status}")
                        print(f"  Reintentos: {reintentos}")
                        
                        # Mostrar métricas individuales
                        for metrica, valor in qa_scores.items():
                            if metrica != "promedio":
                                print(f"    • {metrica}: {valor}")
    
    except Exception as e:
        print(f"⚠️ No se pudieron obtener logs: {e}")
    
    # Ahora obtener el resultado final
    print("\n📄 OBTENIENDO CUENTO GENERADO")
    print("-" * 60)
    
    url_result = f"http://localhost:5000/api/stories/{story_id}/result"
    
    try:
        response = requests.get(url_result, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            
            # Mostrar resumen de calidad
            if "qa_scores" in result:
                qa_summary = result["qa_scores"]
                
                print("\n🎯 RESUMEN DE CALIDAD FINAL:")
                print("-" * 40)
                
                # Calcular promedio global
                promedios = []
                for agente, scores in qa_summary.get("by_agent", {}).items():
                    if "promedio" in scores:
                        promedios.append(scores["promedio"])
                
                if promedios:
                    promedio_global = sum(promedios) / len(promedios)
                    print(f"Promedio Global QA: {promedio_global:.2f}/5")
                    
                    if promedio_global >= 4.0:
                        print("✅ Calidad APROBADA por verificador")
                    elif promedio_global >= 3.5:
                        print("⚠️ Calidad ACEPTABLE con observaciones")
                    else:
                        print("❌ Calidad BAJA según verificador")
            
            # Mostrar título si existe
            if "story" in result and "titulo" in result["story"]:
                print(f"\n📖 Título generado: \"{result['story']['titulo']}\"")
            
            return result
        else:
            print(f"❌ Error obteniendo resultado: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def main():
    """Función principal"""
    
    print("\n🧪 PRUEBA COMPLETA DEL SISTEMA CON VERIFICADOR QA")
    print("=" * 60)
    print("Esta prueba ejecutará el pipeline completo con el nuevo")
    print("sistema de evaluación QA independiente.")
    print("=" * 60)
    
    # Verificar que el servidor esté corriendo
    try:
        response = requests.get("http://localhost:5000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Servidor activo y listo")
        else:
            print("❌ Servidor no responde correctamente")
            return
    except:
        print("❌ No se puede conectar al servidor")
        print("   Ejecuta: python3 src/api_server.py")
        return
    
    # Crear historia
    story_id = crear_historia_emilia()
    
    if not story_id:
        print("❌ No se pudo crear la historia")
        return
    
    # Monitorear progreso
    print("\n⏳ Procesando... (esto puede tomar varios minutos)")
    print("   El verificador QA evaluará cada agente")
    print("   Los agentes con QA < 4.0 se reintentarán")
    
    completado = monitorear_progreso(story_id)
    
    if completado:
        # Obtener métricas finales
        resultado = obtener_metricas_qa(story_id)
        
        if resultado:
            print("\n" + "=" * 60)
            print("✅ PRUEBA COMPLETADA EXITOSAMENTE")
            print(f"   Story ID: {story_id}")
            print("=" * 60)
            
            # Guardar resultado
            filename = f"resultado_qa_{story_id}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(resultado, f, ensure_ascii=False, indent=2)
            print(f"\n💾 Resultado guardado en: {filename}")
    else:
        print("\n" + "=" * 60)
        print("❌ LA PRUEBA NO SE COMPLETÓ")
        print("=" * 60)

if __name__ == "__main__":
    main()