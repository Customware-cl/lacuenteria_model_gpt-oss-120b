#!/usr/bin/env python3
"""
Prueba de generación de cuento - Emilia y Caty viajan a Marte
Tema: Dejar el chupete con confianza
"""

import json
import time
import requests
from datetime import datetime

# Configuración
API_URL = "http://localhost:5000"
STORY_ID = f"test-v2-emilia-marte-chupete-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

# Datos del cuento
STORY_DATA = {
    "story_id": STORY_ID,
    "personajes": ["Emilia", "Caty"],
    "historia": "Justo el día en que Emilia y Caty viajan a Marte en búsqueda de la confianza necesaria para que Emilia deje el chupete",
    "parentesco": "Son Madre e hija",
    "mensaje_a_transmitir": "desarrollar la autoestima y confianza",
    "comportamientos_especificos": "adiós chupete",
    "edad_objetivo": 3,
    "pipeline_version": "v2"
}

def crear_cuento():
    """Inicia la generación del cuento"""
    print(f"\n🚀 Iniciando generación del cuento: {STORY_ID}")
    print(f"📖 Historia: {STORY_DATA['historia']}")
    print(f"👥 Personajes: {', '.join(STORY_DATA['personajes'])}")
    print(f"🎯 Objetivo: {STORY_DATA['comportamientos_especificos']}")
    print(f"💫 Valores: {STORY_DATA['mensaje_a_transmitir']}")
    print(f"👶 Edad objetivo: {STORY_DATA['edad_objetivo']} años")
    print(f"🔄 Versión del flujo: {STORY_DATA['pipeline_version']}")
    
    response = requests.post(
        f"{API_URL}/api/stories/create",
        json=STORY_DATA,
        timeout=30
    )
    
    if response.status_code == 202:
        print(f"✅ Cuento iniciado correctamente")
        return True
    else:
        print(f"❌ Error al iniciar: {response.status_code}")
        print(response.text)
        return False

def monitorear_progreso():
    """Monitorea el progreso de generación"""
    print("\n📊 Monitoreando progreso...")
    
    ultimo_agente = None
    errores_consecutivos = 0
    
    while True:
        try:
            response = requests.get(
                f"{API_URL}/api/stories/{STORY_ID}/status",
                timeout=10
            )
            
            if response.status_code == 200:
                status = response.json()
                
                # Mostrar cambio de agente
                if status.get('current_agent') != ultimo_agente:
                    ultimo_agente = status.get('current_agent')
                    tiempo = datetime.now().strftime('%H:%M:%S')
                    print(f"[{tiempo}] 🔄 Agente: {ultimo_agente}")
                
                # Verificar si terminó
                if status['status'] == 'completed':
                    print(f"\n✅ ¡Cuento completado exitosamente!")
                    return True
                elif status['status'] == 'error':
                    print(f"\n❌ Error en la generación: {status.get('error')}")
                    return False
                
                errores_consecutivos = 0
            else:
                errores_consecutivos += 1
                if errores_consecutivos > 5:
                    print(f"\n⚠️ No se puede obtener el estado")
                    return False
        
        except requests.exceptions.RequestException as e:
            errores_consecutivos += 1
            if errores_consecutivos > 5:
                print(f"\n❌ Error de conexión: {e}")
                return False
        
        time.sleep(5)  # Esperar 5 segundos entre chequeos

def obtener_resultado():
    """Obtiene y muestra el resultado final"""
    print("\n📚 Obteniendo resultado final...")
    
    response = requests.get(
        f"{API_URL}/api/stories/{STORY_ID}/result",
        timeout=30
    )
    
    if response.status_code == 200:
        resultado = response.json()
        
        print(f"\n{'='*60}")
        print(f"📖 CUENTO GENERADO: {resultado.get('titulo', 'Sin título')}")
        print(f"{'='*60}")
        
        # Mostrar portada
        if 'portada' in resultado:
            print(f"\n🎨 PORTADA:")
            print(f"Prompt: {resultado['portada'].get('prompt_imagen', 'N/A')}")
        
        # Mostrar cada página
        for i in range(1, 11):
            pagina_key = f"pagina_{i}"
            if pagina_key in resultado:
                pagina = resultado[pagina_key]
                print(f"\n📄 PÁGINA {i}:")
                print(f"Texto: {pagina.get('texto', 'N/A')}")
                print(f"Imagen: {pagina.get('prompt_imagen', 'N/A')[:100]}...")
        
        # Guardar resultado completo
        output_file = f"resultado_{STORY_ID}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(resultado, f, ensure_ascii=False, indent=2)
        print(f"\n💾 Resultado completo guardado en: {output_file}")
        
        return True
    else:
        print(f"❌ Error al obtener resultado: {response.status_code}")
        return False

def main():
    """Función principal"""
    print("🎭 PRUEBA DE GENERACIÓN DE CUENTO - EMILIA Y EL CHUPETE EN MARTE")
    print("="*60)
    
    # Verificar que el servidor esté activo
    try:
        health = requests.get(f"{API_URL}/health", timeout=5)
        if health.status_code != 200:
            print("❌ El servidor no está respondiendo")
            return
    except:
        print("❌ No se puede conectar al servidor. Asegúrate de que esté corriendo.")
        return
    
    # Crear el cuento
    if not crear_cuento():
        return
    
    # Monitorear progreso
    if not monitorear_progreso():
        print("\n⚠️ La generación no se completó correctamente")
        return
    
    # Obtener resultado
    obtener_resultado()
    
    print(f"\n✨ Prueba completada")
    print(f"📁 Story ID: {STORY_ID}")
    print(f"📂 Carpeta de resultados: runs/{STORY_ID}/")

if __name__ == "__main__":
    main()