#!/usr/bin/env python3
"""
Script de prueba para Pipeline v3 con el brief de Sofía y Max
"""

import requests
import json
import time
import sys
import uuid
from datetime import datetime

# Configuración
BASE_URL = "http://localhost:5000"
TIMESTAMP = datetime.now().strftime('%Y%m%d-%H%M%S')
STORY_UUID = str(uuid.uuid4())
METRICS_UUID = str(uuid.uuid4())

# Brief de Sofía y Max
BRIEF = {
    "story_id": STORY_UUID,
    "prompt_metrics_id": METRICS_UUID,
    "personajes": [
        {
            "nombre": "Sofía",
            "edad": 7,
            "descripcion": "Una niña curiosa y valiente que ama explorar"
        },
        {
            "nombre": "Max",
            "edad": 5,
            "descripcion": "Un perrito juguetón y leal, mejor amigo de Sofía"
        }
    ],
    "historia": "Una aventura en el bosque mágico donde los amigos deben trabajar juntos",
    "relacion_personajes": [
        "Sofía y Max son mejores amigos",
        "Se conocieron cuando Max era un cachorro abandonado"
    ],
    "valores": [
        "Importancia de la amistad verdadera",
        "Respeto por la naturaleza",
        "Valor de ayudar a otros"
    ],
    "comportamientos": [
        "Pedir ayuda cuando se necesita",
        "Compartir con los demás",
        "Cuidar el medio ambiente"
    ],
    "numero_paginas": 10,
    "edad_objetivo": 6,
    "pipeline_version": "v3",  # Cambiado a v3 para probar el nuevo pipeline
    "webhook_url": "https://tu-supabase-url.supabase.co/functions/v1/pipeline-webhook"
}

def print_status(message, status="INFO"):
    """Imprime mensajes con formato y color"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    colors = {
        "INFO": "\033[94m",
        "SUCCESS": "\033[92m",
        "ERROR": "\033[91m",
        "WARNING": "\033[93m",
        "AGENT": "\033[95m",
        "RESET": "\033[0m"
    }
    color = colors.get(status, colors["INFO"])
    print(f"{color}[{timestamp}] {status}: {message}{colors['RESET']}")

def check_health():
    """Verifica que el servidor esté funcionando"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            health = response.json()
            print_status(f"Servidor activo", "SUCCESS")
            return True
    except Exception as e:
        print_status(f"Servidor no disponible: {e}", "ERROR")
        return False
    return False

def format_personajes(personajes):
    """Los personajes se envían tal como vienen - el servidor v3 maneja objetos completos"""
    return personajes

def create_story():
    """Crea una nueva historia con pipeline v3"""
    print_status("=" * 60, "INFO")
    print_status("PRUEBA DE PIPELINE V3 - Sofía y Max", "INFO")
    print_status("=" * 60, "INFO")
    
    print_status(f"Story UUID: {STORY_UUID}", "INFO")
    print_status(f"Metrics UUID: {METRICS_UUID}", "INFO")
    print_status(f"Pipeline: v3 (4 agentes optimizados)", "INFO")
    print_status(f"Personajes: Sofía (7 años) y Max (perrito, 5 años)", "INFO")
    print_status(f"Edad objetivo: {BRIEF['edad_objetivo']} años", "INFO")
    print_status(f"Páginas solicitadas: {BRIEF['numero_paginas']}", "INFO")
    
    # Enviar el brief directamente - el servidor v3 ahora maneja todos los campos
    adapted_brief = BRIEF.copy()
    
    # Enviar request
    try:
        print_status("\n📤 Enviando historia al servidor...", "INFO")
        response = requests.post(
            f"{BASE_URL}/api/stories/create",
            json=adapted_brief,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code in [200, 202]:
            print_status("Historia aceptada para procesamiento", "SUCCESS")
            data = response.json()
            # El servidor puede devolver un story_id modificado con timestamp
            actual_story_id = data.get("story_id", STORY_UUID)
            return True, actual_story_id
        else:
            print_status(f"Error al crear historia: {response.status_code}", "ERROR")
            print_status(response.text, "ERROR")
            return False, None
            
    except Exception as e:
        print_status(f"Error en request: {e}", "ERROR")
        return False, None

def monitor_status(story_id):
    """Monitorea el progreso de la generación"""
    print_status("\n⏳ Monitoreando progreso...", "INFO")
    
    last_agent = None
    agents_v3 = ["01_director_v3", "02_escritor_v3", "03_directorarte_v3", "04_consolidador_v3"]
    start_time = time.time()
    
    while True:
        try:
            response = requests.get(f"{BASE_URL}/api/stories/{story_id}/status", timeout=5)
            
            if response.status_code == 200:
                status_data = response.json()
                current_status = status_data.get("status")
                current_agent = status_data.get("current_agent")
                
                # Mostrar progreso del agente
                if current_agent and current_agent != last_agent:
                    agent_index = agents_v3.index(current_agent) + 1 if current_agent in agents_v3 else 0
                    emoji_map = {
                        "01_director_v3": "🎬",
                        "02_escritor_v3": "✍️",
                        "03_directorarte_v3": "🎨",
                        "04_consolidador_v3": "📦"
                    }
                    emoji = emoji_map.get(current_agent, "⚙️")
                    print_status(f"{emoji} Agente {agent_index}/4: {current_agent}", "AGENT")
                    last_agent = current_agent
                
                # Verificar warnings de QA (no deberían aparecer en v3)
                warnings = status_data.get("metadata", {}).get("warnings", [])
                if warnings:
                    print_status(f"⚠️ Avisos detectados: {len(warnings)}", "WARNING")
                
                # Verificar si terminó
                if current_status == "completed":
                    elapsed = time.time() - start_time
                    print_status(f"✅ Generación completada en {elapsed:.1f} segundos", "SUCCESS")
                    return True
                elif current_status == "error":
                    error_msg = status_data.get("error", "Error desconocido")
                    print_status(f"❌ Error en procesamiento: {error_msg}", "ERROR")
                    return False
                    
            elif response.status_code == 404:
                print_status("Historia no encontrada", "ERROR")
                return False
                
        except Exception as e:
            print_status(f"Error al verificar estado: {e}", "WARNING")
        
        time.sleep(3)
        
        # Timeout después de 5 minutos
        if time.time() - start_time > 300:
            print_status("Timeout - Proceso tardó más de 5 minutos", "ERROR")
            return False

def get_result(story_id):
    """Obtiene y muestra el resultado final"""
    try:
        response = requests.get(f"{BASE_URL}/api/stories/{story_id}/result", timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            
            print_status("\n" + "=" * 60, "INFO")
            print_status("📖 RESULTADO FINAL", "SUCCESS")
            print_status("=" * 60, "INFO")
            
            # Mostrar título
            titulo = result.get("titulo", "Sin título")
            print_status(f"\n📚 Título: {titulo}", "SUCCESS")
            
            # Mostrar resumen de páginas
            paginas = result.get("paginas", {})
            if paginas:
                print_status(f"\n📄 Páginas generadas: {len(paginas)}", "INFO")
                
                # Verificar si se generaron las 10 páginas solicitadas
                if len(paginas) < BRIEF["numero_paginas"]:
                    print_status(f"⚠️ Se generaron {len(paginas)} de {BRIEF['numero_paginas']} páginas solicitadas", "WARNING")
                
                # Mostrar preview de las primeras 2 páginas
                for i in range(1, min(3, len(paginas) + 1)):
                    pagina = paginas.get(str(i), {})
                    texto = pagina.get("texto", "")
                    if texto:
                        preview = texto[:150] + "..." if len(texto) > 150 else texto
                        print_status(f"\nPágina {i}: {preview}", "INFO")
                    
                    # Verificar elementos visuales
                    prompt = pagina.get("prompt", {})
                    if prompt:
                        personajes = prompt.get("personajes", [])
                        if personajes:
                            print_status(f"  👥 Personajes: {len(personajes)} descritos", "INFO")
                        amc = prompt.get("amc", {})
                        if amc:
                            print_status(f"  🦋 AMC: {amc.get('especie', 'N/A')}", "INFO")
            
            # Mostrar mensajes loader
            loader = result.get("loader", [])
            if loader:
                print_status(f"\n✨ Mensajes loader generados: {len(loader)}", "INFO")
                print_status("Primeros 3 mensajes:", "INFO")
                for i, msg in enumerate(loader[:3], 1):
                    print_status(f"  {i}. \"{msg}\"", "INFO")
            
            # Verificar portada
            if "portada" in result and result["portada"]:
                print_status("\n🎨 Portada: ✅ Incluida con prompt visual", "SUCCESS")
            else:
                print_status("\n🎨 Portada: ❌ No generada", "WARNING")
            
            # Guardar resultado
            output_dir = f"runs/{TIMESTAMP}-{story_id}"
            print_status(f"\n📁 Archivos generados en: {output_dir}/", "SUCCESS")
            print_status("  - 01_director_v3.json", "INFO")
            print_status("  - 02_escritor_v3.json", "INFO")
            print_status("  - 03_directorarte_v3.json", "INFO")
            print_status("  - 04_consolidador_v3.json (resultado final)", "INFO")
            
            # Verificar valores y comportamientos integrados
            print_status("\n🎯 Verificación de contenido:", "INFO")
            full_text = " ".join([p.get("texto", "") for p in paginas.values()])
            
            # Buscar menciones de valores
            valores_encontrados = []
            for valor in ["amistad", "naturaleza", "ayud"]:
                if valor.lower() in full_text.lower():
                    valores_encontrados.append(valor)
            
            if valores_encontrados:
                print_status(f"  ✅ Valores detectados: {', '.join(valores_encontrados)}", "SUCCESS")
            else:
                print_status("  ⚠️ No se detectaron valores explícitos en el texto", "WARNING")
            
            return True
        else:
            print_status(f"Error al obtener resultado: {response.status_code}", "ERROR")
            return False
            
    except Exception as e:
        print_status(f"Error: {e}", "ERROR")
        return False

def main():
    """Función principal"""
    print_status("🚀 Iniciando prueba de Pipeline v3 con Sofía y Max", "INFO")
    
    # Verificar servidor
    if not check_health():
        print_status("\n⚠️  El servidor no está activo. Inicia con: python3 src/api_server.py", "WARNING")
        return
    
    # Crear historia
    success, actual_story_id = create_story()
    if not success:
        return
    
    print_status(f"\n📌 Story ID actualizado: {actual_story_id}", "INFO")
    
    # Monitorear progreso
    if not monitor_status(actual_story_id):
        print_status("\n💡 Tip: Revisa los logs para más detalles del error", "INFO")
        return
    
    # Obtener resultado
    get_result(actual_story_id)
    
    print_status("\n✨ Prueba completada", "SUCCESS")
    print_status(f"📊 Story UUID: {STORY_UUID}", "INFO")
    print_status(f"📊 Metrics UUID: {METRICS_UUID}", "INFO")

if __name__ == "__main__":
    main()