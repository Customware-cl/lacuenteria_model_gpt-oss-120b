#!/usr/bin/env python3
"""
Script de prueba para Pipeline v3 con el brief de Emilia y Felipe
Prueba el nuevo flujo de 4 agentes sin afectar v1 o v2
"""

import requests
import json
import time
import sys
from datetime import datetime

# Configuración
BASE_URL = "http://localhost:5000"
TIMESTAMP = datetime.now().strftime('%Y%m%d-%H%M%S')
STORY_ID = f"test-v3-emilia-felipe-{TIMESTAMP}"

# Brief de Emilia y Felipe
BRIEF = {
    "story_id": STORY_ID,
    "personajes": ["Emilia", "Felipe"],
    "historia": """El gran viaje de Emilia y Felipe por la carretera austral chilena, sobre una bicicleta

Parentesco entre personajes:
• Son Padre e hija

Valores y desarrollo emocional a transmitir:
• desarrollar la autoestima y confianza
• Promover la resolución pacífica de conflictos""",
    "mensaje_a_transmitir": "Desarrollar habilidades de comunicación asertiva y pedir ayuda cuando lo necesite",
    "edad_objetivo": 6,
    "pipeline_version": "v3"  # IMPORTANTE: Especifica v3
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
            print_status(f"Servidor activo - Modelo: {health.get('llm_status', 'Unknown')}", "SUCCESS")
            return True
    except Exception as e:
        print_status(f"Servidor no disponible: {e}", "ERROR")
        return False
    return False

def create_story():
    """Crea una nueva historia con pipeline v3"""
    print_status("=" * 60, "INFO")
    print_status("PRUEBA DE PIPELINE V3 - Emilia y Felipe", "INFO")
    print_status("=" * 60, "INFO")
    
    print_status(f"Story ID: {STORY_ID}", "INFO")
    print_status(f"Pipeline: v3 (4 agentes)", "INFO")
    print_status(f"Personajes: {', '.join(BRIEF['personajes'])}", "INFO")
    print_status(f"Edad objetivo: {BRIEF['edad_objetivo']} años", "INFO")
    
    # Enviar request
    try:
        print_status("\n📤 Enviando historia al servidor...", "INFO")
        response = requests.post(
            f"{BASE_URL}/api/stories/create",
            json=BRIEF,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code in [200, 202]:
            print_status("Historia aceptada para procesamiento", "SUCCESS")
            return True
        else:
            print_status(f"Error al crear historia: {response.status_code}", "ERROR")
            print_status(response.text, "ERROR")
            return False
            
    except Exception as e:
        print_status(f"Error en request: {e}", "ERROR")
        return False

def monitor_status():
    """Monitorea el progreso de la generación"""
    print_status("\n⏳ Monitoreando progreso...", "INFO")
    
    last_agent = None
    agents_v3 = ["01_director_v3", "02_escritor_v3", "03_directorarte_v3", "04_consolidador_v3"]
    start_time = time.time()
    
    while True:
        try:
            response = requests.get(f"{BASE_URL}/api/stories/{STORY_ID}/status", timeout=5)
            
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
                
                # Verificar si terminó
                if current_status == "completed":
                    elapsed = time.time() - start_time
                    print_status(f"✅ Generación completada en {elapsed:.1f} segundos", "SUCCESS")
                    return True
                elif current_status == "error":
                    print_status(f"❌ Error en procesamiento: {status_data.get('error')}", "ERROR")
                    return False
                    
            elif response.status_code == 404:
                print_status("Historia no encontrada", "ERROR")
                return False
                
        except Exception as e:
            print_status(f"Error al verificar estado: {e}", "WARNING")
        
        time.sleep(3)  # Esperar 3 segundos entre verificaciones
        
        # Timeout después de 5 minutos
        if time.time() - start_time > 300:
            print_status("Timeout - Proceso tardó más de 5 minutos", "ERROR")
            return False

def get_result():
    """Obtiene y muestra el resultado final"""
    try:
        response = requests.get(f"{BASE_URL}/api/stories/{STORY_ID}/result", timeout=10)
        
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
                
                # Mostrar primeras líneas de las primeras 2 páginas
                for i in range(1, min(3, len(paginas) + 1)):
                    pagina = paginas.get(str(i), {})
                    texto = pagina.get("texto", "")
                    if texto:
                        preview = texto[:100] + "..." if len(texto) > 100 else texto
                        print_status(f"\nPágina {i}: {preview}", "INFO")
            
            # Mostrar mensajes loader
            loader = result.get("loader", [])
            if loader:
                print_status(f"\n✨ Mensajes loader generados: {len(loader)}", "INFO")
                print_status(f"Ejemplo: \"{loader[0]}\"", "INFO")
            
            # Guardar resultado completo
            output_file = f"runs/{TIMESTAMP}-{STORY_ID}/resultado_completo.json"
            print_status(f"\n💾 Resultado guardado en: {output_file}", "SUCCESS")
            
            # Mostrar ubicación de archivos
            print_status(f"\n📁 Archivos generados en: runs/{TIMESTAMP}-{STORY_ID}/", "SUCCESS")
            print_status("  - 01_director_v3.json", "INFO")
            print_status("  - 02_escritor_v3.json", "INFO")
            print_status("  - 03_directorarte_v3.json", "INFO")
            print_status("  - 04_consolidador_v3.json (resultado final)", "INFO")
            
            return True
        else:
            print_status(f"Error al obtener resultado: {response.status_code}", "ERROR")
            return False
            
    except Exception as e:
        print_status(f"Error: {e}", "ERROR")
        return False

def main():
    """Función principal"""
    print_status("🚀 Iniciando prueba de Pipeline v3", "INFO")
    
    # Verificar servidor
    if not check_health():
        print_status("\n⚠️  El servidor no está activo. Inicia con: python3 src/api_server.py", "WARNING")
        return
    
    # Crear historia
    if not create_story():
        return
    
    # Monitorear progreso
    if not monitor_status():
        return
    
    # Obtener resultado
    get_result()
    
    print_status("\n✨ Prueba completada", "SUCCESS")

if __name__ == "__main__":
    main()