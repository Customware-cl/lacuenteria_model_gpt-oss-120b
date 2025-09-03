#!/usr/bin/env python3
"""
Test para verificar la nueva estructura de carpetas: {aaaammdd-HHMMSS}-{story_id}
"""

import sys
import os
import time
from datetime import datetime
from pathlib import Path
import shutil

# Agregar el directorio src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config import generate_timestamped_story_folder, get_latest_story_path, RUNS_DIR

def test_new_folder_structure():
    """Test que verifica la nueva estructura de carpetas"""
    
    print("Testing nueva estructura de carpetas...")
    
    # Test 1: Generar nombre de carpeta con timestamp
    story_id = "test-story-123"
    timestamp_before = datetime.now().strftime("%Y%m%d-%H%M%S")
    
    folder_name = generate_timestamped_story_folder(story_id)
    
    # Verificar que el formato es correcto: {timestamp}-{story_id}
    assert folder_name.startswith(timestamp_before[:8]), f"Error: El folder debería empezar con la fecha {timestamp_before[:8]}, pero es {folder_name}"
    assert folder_name.endswith(f"-{story_id}"), f"Error: El folder debería terminar con -{story_id}, pero es {folder_name}"
    print(f"✓ Estructura correcta: {folder_name}")
    
    # Test 2: Crear carpetas de prueba y verificar get_latest_story_path
    test_folders = []
    
    # Crear carpetas con el nuevo formato
    for i in range(3):
        time.sleep(1)  # Esperar para tener timestamps diferentes
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        folder_name = f"{timestamp}-{story_id}"
        folder_path = RUNS_DIR / folder_name
        folder_path.mkdir(parents=True, exist_ok=True)
        test_folders.append(folder_path)
        print(f"  Creada carpeta: {folder_name}")
    
    # Obtener la carpeta más reciente
    latest_path = get_latest_story_path(story_id)
    assert latest_path is not None, "Error: No se encontró ninguna carpeta"
    
    # Verificar que es la última creada
    expected_latest = test_folders[-1]
    assert latest_path.name == expected_latest.name, f"Error: Se esperaba {expected_latest.name}, pero se obtuvo {latest_path.name}"
    print(f"✓ Carpeta más reciente encontrada correctamente: {latest_path.name}")
    
    # Test 3: Verificar compatibilidad con formato antiguo
    old_story_id = "old-story-456"
    old_format_folder = f"{old_story_id}-20240101-120000"
    old_path = RUNS_DIR / old_format_folder
    old_path.mkdir(parents=True, exist_ok=True)
    test_folders.append(old_path)
    print(f"  Creada carpeta con formato antiguo: {old_format_folder}")
    
    # Debería encontrar la carpeta con formato antiguo
    found_old = get_latest_story_path(old_story_id)
    assert found_old is not None, "Error: No se encontró carpeta con formato antiguo"
    assert found_old.name == old_format_folder, f"Error: Se esperaba {old_format_folder}, pero se obtuvo {found_old.name}"
    print(f"✓ Compatibilidad con formato antiguo funciona: {found_old.name}")
    
    # Limpiar carpetas de prueba
    for folder in test_folders:
        if folder.exists():
            shutil.rmtree(folder)
    
    print("\n✅ TODOS LOS TESTS PASARON")
    print("   - Nueva estructura: {YYYYMMDD-HHMMSS}-{story_id}")
    print("   - get_latest_story_path funciona correctamente")
    print("   - Compatibilidad con formato antiguo mantenida")

if __name__ == "__main__":
    test_new_folder_structure()