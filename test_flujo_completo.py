#!/usr/bin/env python3
"""
Script de prueba automatizado para el flujo completo de Cuentería
Usa los endpoints de la API para un proceso sin fricción
"""

import requests
import json
import time
import sys
from datetime import datetime

# Configuración
BASE_URL = "http://localhost:5000"
STORY_ID = f"test-emilia-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

# Brief de Emilia
BRIEF_EMILIA = {
    "story_id": STORY_ID,
    "personajes": [
        {
            "nombre": "Emilia",
            "descripcion": "Niña de 3 años con síndrome de Angelman",
            "rasgos": "No verbal, comunicación gestual y afectiva muy expresiva"
        }
    ],
    "historia": "Emilia descubre el poder de comunicarse sin palabras a través de abrazos, sonrisas y gestos en una aventura mágica donde debe ayudar a un unicornio que ha perdido su voz",
    "mensaje_a_transmitir": "La comunicación va más allá de las palabras. Los gestos, sonrisas y abrazos son formas poderosas de expresar amor y conectar con otros",
    "edad_objetivo": "3-5 años"
}

def print_status(message, status="INFO"):
    """Imprime mensajes con formato"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    colors = {
        "INFO": "\033[94m",
        "SUCCESS": "\033[92m",
        "ERROR": "\033[91m",
        "WAITING": "\033[93m"
    }
    color = colors.get(status, "\033[0m")
    print(f"{color}[{timestamp}] {message}\033[0m")

def check_health():
    """Verifica el estado del servidor"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_status("✓ Servidor saludable", "SUCCESS")
            print_status(f"  - Conexión LLM: {data['checks']['llm_connection']}")
            print_status(f"  - Configuración válida: {data['checks']['config_valid']}")
            return True
        else:
            print_status(f"✗ Servidor no saludable: {response.status_code}", "ERROR")
            return False
    except requests.exceptions.RequestException as e:
        print_status(f"✗ No se puede conectar al servidor: {e}", "ERROR")
        return False

def create_story():
    """Crea una nueva historia"""
    print_status(f"Creando historia con ID: {STORY_ID}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/stories/create",
            json=BRIEF_EMILIA,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code in [200, 202]:
            data = response.json()
            print_status(f"✓ Historia aceptada: {data['status']}", "SUCCESS")
            if 'estimated_time' in data:
                print_status(f"  Tiempo estimado: {data['estimated_time']} segundos")
            return True
        else:
            print_status(f"✗ Error creando historia: {response.status_code}", "ERROR")
            print_status(f"  {response.text}")
            return False
    except Exception as e:
        print_status(f"✗ Error: {e}", "ERROR")
        return False

def monitor_progress():
    """Monitorea el progreso de la historia"""
    print_status("Monitoreando progreso...")
    
    last_step = None
    start_time = time.time()
    
    while True:
        try:
            response = requests.get(f"{BASE_URL}/api/stories/{STORY_ID}/status")
            
            if response.status_code == 200:
                data = response.json()
                status = data.get('status', 'desconocido')
                current_step = data.get('current_step', '')
                
                # Actualizar si cambió el paso
                if current_step != last_step:
                    elapsed = int(time.time() - start_time)
                    print_status(f"  [{elapsed}s] Estado: {status} | Paso: {current_step}", "WAITING")
                    
                    # Mostrar scores QA si existen
                    if 'qa_scores' in data and data['qa_scores']:
                        for agent, scores in data['qa_scores'].items():
                            if isinstance(scores, dict):
                                score_str = ', '.join([f"{k}: {v}" for k, v in scores.items()])
                                print_status(f"    QA {agent}: {score_str}")
                    
                    last_step = current_step
                
                # Verificar si terminó
                if status == 'completo':
                    print_status("✓ Historia completada", "SUCCESS")
                    return True
                elif status == 'error' or status == 'qa_failed':
                    print_status(f"✗ Historia falló con estado: {status}", "ERROR")
                    return False
                
                # Timeout después de 10 minutos
                if time.time() - start_time > 600:
                    print_status("✗ Timeout esperando completar", "ERROR")
                    return False
                
            else:
                print_status(f"Error obteniendo estado: {response.status_code}", "ERROR")
            
            time.sleep(3)  # Esperar 3 segundos entre chequeos
            
        except Exception as e:
            print_status(f"Error monitoreando: {e}", "ERROR")
            time.sleep(3)

def get_result():
    """Obtiene el resultado final"""
    print_status("Obteniendo resultado final...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/stories/{STORY_ID}/result")
        
        if response.status_code == 200:
            data = response.json()
            
            if data['status'] == 'completed':
                print_status("✓ Resultado obtenido exitosamente", "SUCCESS")
                
                # Mostrar resumen del cuento
                result = data['result']
                print("\n" + "="*60)
                print("RESUMEN DEL CUENTO GENERADO")
                print("="*60)
                print(f"Título: {result.get('titulo', 'Sin título')}")
                print(f"Páginas: {len(result.get('paginas', {}))}")
                
                # Mostrar primera página como muestra
                if 'paginas' in result and '1' in result['paginas']:
                    print("\nPrimera página:")
                    print(f"Texto: {result['paginas']['1'].get('texto', '')[:100]}...")
                
                # Mostrar mensajes loader
                if 'loader' in result:
                    print(f"\nMensajes loader: {len(result['loader'])} mensajes")
                    if result['loader']:
                        print(f"Ejemplo: {result['loader'][0]}")
                
                # Mostrar QA scores
                if 'qa_scores' in data:
                    print(f"\nQA Score general: {data['qa_scores'].get('overall', 'N/A')}")
                
                return data
            else:
                print_status(f"Historia no completada: {data['status']}", "ERROR")
                return None
        else:
            print_status(f"Error obteniendo resultado: {response.status_code}", "ERROR")
            return None
            
    except Exception as e:
        print_status(f"Error: {e}", "ERROR")
        return None

def evaluate_story(story_result):
    """Ejecuta el agente crítico sobre la historia"""
    print_status("Ejecutando evaluación crítica...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/stories/{STORY_ID}/evaluate",
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print_status("✓ Evaluación crítica completada", "SUCCESS")
            
            if 'evaluacion_critica' in data:
                eval_data = data['evaluacion_critica']
                
                print("\n" + "="*60)
                print("EVALUACIÓN CRÍTICA")
                print("="*60)
                
                # Nota general
                if 'nota_general' in eval_data:
                    general = eval_data['nota_general']
                    print(f"\nNOTA GENERAL:")
                    print(f"  Puntuación: {general.get('puntuacion', 'N/A')}/5")
                    print(f"  Comentario: {general.get('comentario', 'Sin comentario')}")
                
                # Notas por categoría
                if 'notas_por_categoria' in eval_data:
                    print("\nNOTAS POR CATEGORÍA:")
                    for categoria, detalles in eval_data['notas_por_categoria'].items():
                        print(f"\n  {categoria.upper()}:")
                        print(f"    Puntuación: {detalles.get('puntuacion', 'N/A')}/5")
                        print(f"    Comentario: {detalles.get('comentario', 'Sin comentario')}")
                        
                        # Aspectos específicos
                        if 'aspectos' in detalles:
                            print("    Aspectos:")
                            for aspecto, valor in detalles['aspectos'].items():
                                print(f"      - {aspecto}: {valor}")
                
                return data
            else:
                print_status("Evaluación sin estructura esperada", "ERROR")
                print(json.dumps(data, indent=2, ensure_ascii=False))
                return data
                
        else:
            print_status(f"Error en evaluación: {response.status_code}", "ERROR")
            print(response.text)
            return None
            
    except Exception as e:
        print_status(f"Error: {e}", "ERROR")
        return None

def main():
    """Flujo principal de prueba"""
    print("\n" + "="*60)
    print("PRUEBA AUTOMATIZADA - FLUJO COMPLETO CUENTERÍA")
    print("="*60)
    print(f"Story ID: {STORY_ID}")
    print(f"Personaje: {BRIEF_EMILIA['personajes'][0]['nombre']}")
    print("="*60 + "\n")
    
    # 1. Verificar salud del servidor
    print_status("PASO 1: Verificando servidor...")
    if not check_health():
        print_status("Abortando: servidor no disponible", "ERROR")
        return 1
    
    # 2. Crear historia
    print("\n" + "-"*40)
    print_status("PASO 2: Creando historia...")
    if not create_story():
        print_status("Abortando: no se pudo crear historia", "ERROR")
        return 1
    
    # 3. Monitorear progreso
    print("\n" + "-"*40)
    print_status("PASO 3: Monitoreando progreso...")
    if not monitor_progress():
        print_status("Abortando: historia no completada", "ERROR")
        return 1
    
    # 4. Obtener resultado
    print("\n" + "-"*40)
    print_status("PASO 4: Obteniendo resultado...")
    result = get_result()
    if not result:
        print_status("Abortando: no se pudo obtener resultado", "ERROR")
        return 1
    
    # 5. Ejecutar evaluación crítica
    print("\n" + "-"*40)
    print_status("PASO 5: Ejecutando evaluación crítica...")
    evaluation = evaluate_story(result)
    
    # 6. Resumen final
    print("\n" + "="*60)
    print("PRUEBA COMPLETADA EXITOSAMENTE")
    print("="*60)
    print(f"Story ID: {STORY_ID}")
    print(f"Tiempo total: {time.strftime('%M:%S', time.gmtime(time.time()))}")
    
    # Guardar resultados
    output_file = f"resultado_test_{STORY_ID}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "story_id": STORY_ID,
            "brief": BRIEF_EMILIA,
            "result": result,
            "evaluation": evaluation,
            "timestamp": datetime.now().isoformat()
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\nResultados guardados en: {output_file}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())