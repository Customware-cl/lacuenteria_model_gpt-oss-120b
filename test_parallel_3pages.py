#!/usr/bin/env python3
"""
Test del procesamiento paralelo de cuentacuentos con solo 3 páginas
Usa los datos del run anterior de Marte
"""
import json
import os
import sys
from pathlib import Path
from datetime import datetime

# Agregar el directorio src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Temporalmente limitar a 3 páginas para testing
import parallel_cuentacuentos

# Monkey patch para testing con 3 páginas
original_run = parallel_cuentacuentos.ParallelCuentacuentos.run

def run_limited(self):
    """Version limitada del run() que solo procesa 3 páginas"""
    import logging
    import time
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    logger = logging.getLogger(__name__)
    
    logger.info(f"🧪 TEST MODE: Procesando solo 3 páginas")
    logger.info(f"📊 Configuración: {self.config['max_workers']} workers, {self.config['max_retries_per_page']} reintentos por página")
    
    start_time = time.time()
    page_results = []
    
    # Limitar a 3 páginas para el test
    test_pages = [1, 2, 5]  # Incluimos página 2 y 5 que necesitan leitmotiv
    
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {}
        for page_num in test_pages:
            future = executor.submit(self.process_single_page, page_num)
            futures[future] = page_num
        
        for future in as_completed(futures):
            page_num = futures[future]
            try:
                result = future.result(timeout=self.config["page_timeout"])
                page_results.append(result)
                
                self.save_partial_progress(page_num, result)
                
                if result["success"]:
                    logger.info(f"✅ Página {page_num} completada en {result['processing_time']:.2f}s")
                else:
                    logger.warning(f"❌ Página {page_num} falló: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                logger.error(f"❌ Error procesando página {page_num}: {e}")
                page_results.append({
                    "page_num": page_num,
                    "success": False,
                    "error": str(e)
                })
    
    # Consolidar solo las 3 páginas
    logger.info(f"📦 Consolidando resultados de TEST (3 páginas)...")
    final_result = self.consolidate_results(page_results)
    
    # Guardar como archivo de test
    story_path = parallel_cuentacuentos.get_story_path(self.story_id)
    output_file = story_path / "03_cuentacuentos_test_3pages.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_result, f, ensure_ascii=False, indent=2)
    
    total_time = time.time() - start_time
    logger.info(f"✨ TEST completado en {total_time:.2f}s")
    logger.info(f"📊 Páginas exitosas: {len([r for r in page_results if r['success']])}/3")
    
    return {
        "status": "test_completed",
        "agent_output": final_result,
        "total_time": total_time,
        "pages_successful": len([r for r in page_results if r["success"]]),
        "pages_failed": len([r for r in page_results if not r["success"]])
    }

# Aplicar el monkey patch
parallel_cuentacuentos.ParallelCuentacuentos.run = run_limited

def main():
    print("=" * 60)
    print("🧪 TEST: Procesamiento Paralelo de Cuentacuentos (3 páginas)")
    print("=" * 60)
    
    # Usar el story_id del test anterior
    story_id = "test-v2-marte-20250830-004948"
    
    # Verificar que existen las dependencias
    story_path = Path(f"runs/{story_id}")
    if not story_path.exists():
        print(f"❌ No se encontró el directorio {story_path}")
        return 1
    
    director_file = story_path / "01_director.json"
    psico_file = story_path / "02_psicoeducador.json"
    
    if not director_file.exists() or not psico_file.exists():
        print("❌ No se encontraron los archivos de dependencias necesarios")
        return 1
    
    print(f"✅ Usando datos de: {story_id}")
    print(f"📁 Director: {director_file.name}")
    print(f"📁 Psicoeducador: {psico_file.name}")
    print("-" * 60)
    
    # Configurar logging
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Ejecutar test
    print("\n🚀 Iniciando procesamiento paralelo...")
    print("📝 Páginas a procesar: 1, 2, 5")
    print("⚡ Modo: PARALELO (3 threads simultáneos)")
    print("-" * 60)
    
    try:
        processor = parallel_cuentacuentos.ParallelCuentacuentos(story_id, version='v2')
        result = processor.run()  # Usará la versión patcheada
        
        print("\n" + "=" * 60)
        print("📊 RESULTADOS DEL TEST:")
        print("=" * 60)
        
        print(f"Estado: {result['status']}")
        print(f"Tiempo total: {result['total_time']:.2f} segundos")
        print(f"Páginas exitosas: {result['pages_successful']}/3")
        print(f"Páginas fallidas: {result['pages_failed']}/3")
        
        # Mostrar muestra de resultado
        if result['agent_output'].get('paginas_texto'):
            print("\n📖 Muestra de páginas generadas:")
            for page_num, texto in result['agent_output']['paginas_texto'].items():
                print(f"\n--- Página {page_num} ---")
                print(texto[:200] + "..." if len(texto) > 200 else texto)
        
        # Verificar leitmotiv
        if result['agent_output'].get('leitmotiv_usado_en'):
            print(f"\n🌟 Leitmotiv usado en páginas: {result['agent_output']['leitmotiv_usado_en']}")
        
        print("\n✅ Test completado exitosamente")
        print(f"📁 Resultado guardado en: runs/{story_id}/03_cuentacuentos_test_3pages.json")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error durante el test: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())