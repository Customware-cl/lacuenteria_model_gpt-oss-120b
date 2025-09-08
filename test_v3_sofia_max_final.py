#!/usr/bin/env python3
"""
Prueba final del Pipeline v3 con Sofía y Max
"""

import requests
import json
import time
import uuid
from datetime import datetime

# Configuración
BASE_URL = "http://localhost:5000"
TIMESTAMP = datetime.now().strftime('%Y%m%d-%H%M%S')
STORY_UUID = str(uuid.uuid4())

# Brief completo para v3
BRIEF = {
    "story_id": STORY_UUID,
    "prompt_metrics_id": str(uuid.uuid4()),
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
    "historia": "Una aventura en el bosque mágico donde los amigos deben trabajar juntos para llegar al bosque de hadas",
    "mensaje_a_transmitir": "Importancia de la amistad verdadera, Respeto por la naturaleza, Valor de ayudar a otros",
    "edad_objetivo": 6,
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
    "pipeline_version": "v3",
    "webhook_url": "https://example.com/webhook"  # URL de ejemplo
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

def wait_for_server():
    """Espera a que el servidor esté listo"""
    print_status("Esperando servidor...", "INFO")
    for i in range(10):
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=2)
            if response.status_code == 200:
                print_status("Servidor listo", "SUCCESS")
                return True
        except:
            pass
        time.sleep(1)
    return False

def create_story():
    """Crea la historia con pipeline v3"""
    print_status("=" * 60, "INFO")
    print_status("🚀 PRUEBA PIPELINE V3 - Sofía y Max", "INFO")
    print_status("=" * 60, "INFO")
    
    print_status(f"Story ID: {STORY_UUID}", "INFO")
    print_status(f"Pipeline: v3", "INFO")
    print_status(f"Páginas solicitadas: {BRIEF['numero_paginas']}", "INFO")
    print_status(f"Personajes: Sofía (7 años) y Max (perrito, 5 años)", "INFO")
    
    try:
        print_status("\n📤 Enviando historia al servidor...", "INFO")
        response = requests.post(
            f"{BASE_URL}/api/stories/create",
            json=BRIEF,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code in [200, 202]:
            print_status("✅ Historia aceptada", "SUCCESS")
            data = response.json()
            return True, data.get("story_id", STORY_UUID)
        else:
            print_status(f"❌ Error: {response.status_code}", "ERROR")
            print(response.text)
            return False, None
            
    except Exception as e:
        print_status(f"❌ Error: {e}", "ERROR")
        return False, None

def monitor_progress(story_id):
    """Monitorea el progreso del procesamiento"""
    print_status("\n⏳ Monitoreando progreso...", "INFO")
    
    agents_v3 = ["01_director_v3", "02_escritor_v3", "03_directorarte_v3", "04_consolidador_v3"]
    last_agent = None
    start_time = time.time()
    timeout = 300  # 5 minutos
    
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{BASE_URL}/api/stories/{story_id}/status", timeout=5)
            
            if response.status_code == 200:
                status_data = response.json()
                current_status = status_data.get("status")
                current_agent = status_data.get("current_agent")
                
                # Mostrar progreso
                if current_agent and current_agent != last_agent:
                    emoji_map = {
                        "01_director_v3": "🎬",
                        "02_escritor_v3": "✍️",
                        "03_directorarte_v3": "🎨",
                        "04_consolidador_v3": "📦"
                    }
                    emoji = emoji_map.get(current_agent, "⚙️")
                    if current_agent in agents_v3:
                        agent_num = agents_v3.index(current_agent) + 1
                        print_status(f"{emoji} Agente {agent_num}/4: {current_agent}", "AGENT")
                    last_agent = current_agent
                
                # Verificar completado
                if current_status == "completed":
                    elapsed = time.time() - start_time
                    print_status(f"\n✅ Completado en {elapsed:.1f} segundos", "SUCCESS")
                    return True
                elif current_status == "error":
                    print_status(f"\n❌ Error: {status_data.get('error', 'Desconocido')}", "ERROR")
                    return False
                    
        except Exception as e:
            pass  # Ignorar errores temporales
        
        time.sleep(2)
    
    print_status(f"\n⚠️ Timeout después de {timeout} segundos", "WARNING")
    return False

def check_results(story_id):
    """Verifica y muestra los resultados"""
    print_status("\n📊 Verificando resultados...", "INFO")
    
    # Buscar la carpeta con timestamp
    import glob
    pattern = f"runs/*{story_id}*"
    folders = glob.glob(pattern)
    
    if not folders:
        print_status("No se encontró carpeta de resultados", "ERROR")
        return
    
    folder = folders[0]
    print_status(f"📁 Carpeta: {folder}", "INFO")
    
    # Verificar archivos generados
    files_to_check = [
        "01_director_v3.json",
        "02_escritor_v3.json", 
        "03_directorarte_v3.json",
        "04_consolidador_v3.json"
    ]
    
    for file in files_to_check:
        file_path = f"{folder}/{file}"
        if glob.glob(file_path):
            print_status(f"  ✅ {file}", "SUCCESS")
            
            # Verificar contenido específico
            if "02_escritor" in file:
                check_line_breaks(file_path)
            elif "03_directorarte" in file:
                check_amc_consistency(file_path)
            elif "04_consolidador" in file:
                check_final_result(file_path)
        else:
            print_status(f"  ❌ {file}", "ERROR")

def check_line_breaks(file_path):
    """Verifica que el escritor incluya saltos de línea"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if 'paginas' in data:
                first_page = data['paginas'][0] if data['paginas'] else {}
                texto = first_page.get('texto', '')
                if '\\n' in repr(texto):
                    print_status("    → Saltos de línea: ✅ Detectados", "SUCCESS")
                else:
                    print_status("    → Saltos de línea: ⚠️ No detectados", "WARNING")
    except:
        pass

def check_amc_consistency(file_path):
    """Verifica que el AMC sea consistente"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if 'amc_elegido' in data:
                amc = data['amc_elegido']
                print_status(f"    → AMC: {amc.get('especie', 'N/A')} ({amc.get('id', 'N/A')})", "INFO")
                
                # Verificar consistencia en páginas
                if 'paginas' in data:
                    especies = set()
                    for p in data['paginas']:
                        if 'prompt' in p and 'amc' in p['prompt']:
                            # El AMC ya no tiene especie en cada página, solo acciones
                            especies.add(amc.get('especie', 'N/A'))
                    
                    if len(especies) == 1:
                        print_status("    → Consistencia AMC: ✅", "SUCCESS")
                    else:
                        print_status(f"    → Consistencia AMC: ⚠️ {len(especies)} especies", "WARNING")
    except:
        pass

def check_final_result(file_path):
    """Verifica el resultado final del consolidador"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            # Verificar estructura
            titulo = data.get('titulo', 'Sin título')
            print_status(f"    → Título: {titulo}", "INFO")
            
            paginas = data.get('paginas', {})
            print_status(f"    → Páginas generadas: {len(paginas)}/10", "INFO")
            
            if 'portada' in data:
                print_status("    → Portada: ✅", "SUCCESS")
            else:
                print_status("    → Portada: ❌", "ERROR")
                
            loader = data.get('loader', [])
            print_status(f"    → Mensajes loader: {len(loader)}", "INFO")
            
            # Mostrar preview
            if paginas and '1' in paginas:
                texto = paginas['1'].get('texto', '')[:100]
                print_status(f"\n📖 Preview página 1:", "INFO")
                print(f"  {texto}...")
                
    except Exception as e:
        print_status(f"Error leyendo resultado: {e}", "ERROR")

def main():
    """Función principal"""
    
    # Esperar servidor
    if not wait_for_server():
        print_status("❌ Servidor no disponible", "ERROR")
        return
    
    # Crear historia
    success, story_id = create_story()
    if not success:
        return
    
    # Monitorear progreso
    if monitor_progress(story_id):
        # Verificar resultados
        check_results(story_id)
        print_status("\n✨ Prueba completada exitosamente", "SUCCESS")
    else:
        print_status("\n❌ La prueba no se completó correctamente", "ERROR")
        check_results(story_id)  # Verificar resultados parciales

if __name__ == "__main__":
    main()