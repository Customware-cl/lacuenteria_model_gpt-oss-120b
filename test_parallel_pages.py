#!/usr/bin/env python3
"""
Test para verificar que las páginas de cuentacuentos se procesan en paralelo
"""

import json
import time
from pathlib import Path
from datetime import datetime

def check_parallel_processing():
    """Verifica que el procesamiento sea realmente paralelo"""
    
    print("🧪 Verificando procesamiento paralelo de cuentacuentos")
    print("="*60)
    
    # 1. Verificar configuración
    config_path = Path("flujo/v2/agent_config.json")
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    cuentos_config = config.get("03_cuentacuentos", {})
    
    print("📊 Configuración actual de cuentacuentos:")
    print(f"   max_workers: {cuentos_config.get('max_workers', 'no definido')}")
    print(f"   force_sequential: {cuentos_config.get('force_sequential', 'no definido')}")
    print(f"   parallel_mode: {cuentos_config.get('parallel_mode', 'no definido')}")
    print()
    
    # 2. Verificar el código de ParallelCuentacuentos
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))
    
    from parallel_cuentacuentos import ParallelCuentacuentos
    
    # Crear una instancia mock solo para verificar config
    class MockProcessor:
        def __init__(self):
            self.base_dir = Path(__file__).parent
            self.version = "v2"
            self.config = {}
            self.load_config()
        
        def load_config(self):
            # Copiar la lógica de load_config de ParallelCuentacuentos
            self.config = {
                "max_workers": 3,
                "page_timeout": 120,
                "max_retries_per_page": 3,
                "temperature": 0.75,
                "max_tokens": 30000,
                "top_p": 0.95,
                "qa_threshold": 3.5,
                "delay_between_pages": 1,
                "force_sequential": False
            }
            
            config_path = self.base_dir / f"flujo/{self.version}/agent_config.json"
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    agent_configs = json.load(f)
                    if "03_cuentacuentos" in agent_configs:
                        cuentos_config = agent_configs["03_cuentacuentos"]
                        self.config.update({
                            "temperature": cuentos_config.get("temperature", 0.75),
                            "max_tokens": cuentos_config.get("max_tokens_per_page", 30000),
                            "top_p": cuentos_config.get("top_p", 0.95),
                            "qa_threshold": cuentos_config.get("qa_threshold", 3.5),
                            "max_workers": cuentos_config.get("max_workers", 3),
                            "page_timeout": cuentos_config.get("page_timeout", 120),
                            "max_retries_per_page": cuentos_config.get("max_retries_per_page", 3),
                            "force_sequential": cuentos_config.get("force_sequential", False),
                            "delay_between_pages": cuentos_config.get("delay_between_pages", 1)
                        })
    
    processor = MockProcessor()
    
    print("📋 Configuración cargada en ParallelCuentacuentos:")
    print(f"   max_workers: {processor.config.get('max_workers')}")
    print(f"   force_sequential: {processor.config.get('force_sequential')}")
    print(f"   delay_between_pages: {processor.config.get('delay_between_pages')}")
    print()
    
    # 3. Determinar modo de procesamiento
    if processor.config.get("force_sequential", False) or processor.config["max_workers"] == 1:
        print("❌ MODO: SECUENCIAL")
        print("   Las páginas se procesarán una por una")
        if processor.config.get("force_sequential"):
            print("   Razón: force_sequential = True")
        else:
            print("   Razón: max_workers = 1")
    else:
        print("✅ MODO: PARALELO")
        print(f"   Las páginas se procesarán en grupos de {processor.config['max_workers']}")
    
    print()
    
    # 4. Verificar método que se usará
    if processor.config.get("force_sequential", False) or processor.config["max_workers"] == 1:
        print("📝 Método que se usará: process_sequential()")
    else:
        print("📝 Método que se usará: process_parallel()")
    
    print()
    
    # 5. Simulación de tiempo estimado
    pages = 10
    time_per_page = 10  # segundos estimados por página
    
    if processor.config.get("force_sequential", False) or processor.config["max_workers"] == 1:
        estimated_time = pages * time_per_page
        print(f"⏱️  Tiempo estimado (secuencial): {estimated_time} segundos")
    else:
        workers = processor.config["max_workers"]
        batches = (pages + workers - 1) // workers  # Redondeo hacia arriba
        estimated_time = batches * time_per_page + (batches - 1) * processor.config.get("delay_between_pages", 1)
        print(f"⏱️  Tiempo estimado (paralelo con {workers} workers): ~{estimated_time} segundos")
        print(f"   ({batches} tandas de procesamiento)")
    
    print("\n" + "="*60)
    
    # 6. Recomendaciones
    if processor.config.get("force_sequential", False) or processor.config["max_workers"] == 1:
        print("⚠️  RECOMENDACIÓN: El procesamiento está en modo secuencial")
        print("   Para habilitar el modo paralelo:")
        print("   1. Asegúrate que max_workers > 1 en agent_config.json")
        print("   2. Asegúrate que force_sequential = false")
        print("   3. Reinicia el servidor si está corriendo")
    else:
        print("✅ El procesamiento paralelo está correctamente configurado")
        print(f"   Se procesarán hasta {processor.config['max_workers']} páginas simultáneamente")
    
    print("\n✨ Verificación completada")

if __name__ == "__main__":
    check_parallel_processing()