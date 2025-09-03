#!/usr/bin/env python3
"""
Test del API con la nueva estructura de carpetas
"""

import requests
import json
import time
from pathlib import Path
import sys
import os

# Agregar el directorio src al path  
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config import RUNS_DIR

def test_api_with_new_structure():
    """Test que verifica que el API crea carpetas con la nueva estructura"""
    
    print("Testing API con nueva estructura de carpetas...")
    
    # URL del API local
    base_url = "http://localhost:5000"
    
    # Verificar que el servidor está activo
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code != 200:
            print("❌ El servidor no está activo. Por favor inicia el servidor con: python3 src/api_server.py")
            return False
    except:
        print("❌ No se puede conectar al servidor. Por favor inicia el servidor con: python3 src/api_server.py")
        return False
    
    print("✓ Servidor activo")
    
    # Crear una historia de prueba
    story_id = "test-api-structure"
    prompt_metrics_id = "metrics-test-123"
    
    payload = {
        "story_id": story_id,
        "personajes": ["Prueba"],
        "historia": "Historia de prueba para verificar estructura de carpetas",
        "mensaje_a_transmitir": "Test",
        "edad_objetivo": 5,
        "prompt_metrics_id": prompt_metrics_id
    }
    
    # Enviar request
    print(f"Enviando request para crear historia: {story_id}")
    response = requests.post(
        f"{base_url}/api/stories/create",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code != 202:
        print(f"❌ Error al crear historia: {response.text}")
        return False
    
    print("✓ Historia creada, esperando 2 segundos para que se cree la carpeta...")
    time.sleep(2)
    
    # Buscar la carpeta creada
    pattern = f"*-{story_id}*"
    folders = list(RUNS_DIR.glob(pattern))
    
    if not folders:
        print(f"❌ No se encontró ninguna carpeta para {story_id}")
        return False
    
    # Obtener la carpeta más reciente
    latest_folder = sorted(folders)[-1]
    folder_name = latest_folder.name
    
    print(f"✓ Carpeta creada: {folder_name}")
    
    # Verificar que cumple con el nuevo formato
    # Debe empezar con YYYYMMDD-HHMMSS
    import re
    pattern_regex = r'^\d{8}-\d{6}-.*'
    if re.match(pattern_regex, folder_name):
        print(f"✓ La carpeta cumple con el nuevo formato: {folder_name}")
    else:
        print(f"❌ La carpeta NO cumple con el nuevo formato: {folder_name}")
        return False
    
    # Verificar que el brief NO contiene prompt_metrics_id
    brief_path = latest_folder / "brief.json"
    if brief_path.exists():
        with open(brief_path, 'r') as f:
            brief = json.load(f)
        if "prompt_metrics_id" in brief:
            print("❌ El brief contiene prompt_metrics_id (no debería)")
            return False
        else:
            print("✓ El brief NO contiene prompt_metrics_id (correcto)")
    
    # Verificar que el manifest SÍ contiene prompt_metrics_id
    manifest_path = latest_folder / "manifest.json"
    if manifest_path.exists():
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        if "prompt_metrics_id" in manifest:
            print(f"✓ El manifest SÍ contiene prompt_metrics_id: {manifest['prompt_metrics_id']}")
        else:
            print("❌ El manifest NO contiene prompt_metrics_id (debería)")
            return False
    
    print("\n✅ TEST DEL API EXITOSO")
    print(f"   - Nueva estructura aplicada: {folder_name}")
    print("   - prompt_metrics_id correctamente manejado")
    return True

if __name__ == "__main__":
    # Nota: Este test requiere que el servidor esté corriendo
    print("NOTA: Este test requiere que el servidor esté corriendo")
    print("Si no está activo, ejecuta en otra terminal: python3 src/api_server.py\n")
    
    success = test_api_with_new_structure()
    if not success:
        sys.exit(1)