#!/usr/bin/env python3
"""
Test para analizar el problema de truncamiento con logs detallados
"""
import json
import sys
import os
import logging
from datetime import datetime
from pathlib import Path

# Configurar logging más detallado
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'truncation_analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.agent_runner_optimized import OptimizedAgentRunner

def analyze_truncation():
    print("\n" + "="*60)
    print("🔬 ANÁLISIS DE TRUNCAMIENTO")
    print("="*60)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    story_id = f"truncation_test_{timestamp}"
    
    story_path = Path(f"runs/{story_id}")
    story_path.mkdir(parents=True, exist_ok=True)
    
    # Brief simple
    brief = {
        "story_id": story_id,
        "personajes": ["Emilia", "Unicornio"],
        "historia": "Emilia y un unicornio crean luz donde hay oscuridad",
        "mensaje_a_transmitir": "La comunicación trasciende las palabras",
        "edad_objetivo": 5
    }
    
    with open(story_path / "brief.json", 'w', encoding='utf-8') as f:
        json.dump(brief, f, ensure_ascii=False, indent=2)
    
    runner = OptimizedAgentRunner(story_id)
    
    # Probar solo los agentes problemáticos
    problematic_agents = [
        "director",           # Para generar dependencias
        "psicoeducador",      # Para generar dependencias
        "cuentacuentos",      # Problemático - genera 10 páginas
        "editor_claridad",    # Muy problemático - reescribe 10 páginas
        "ritmo_rima"          # Problemático - pule 10 páginas
    ]
    
    results = {}
    
    for i, agent_name in enumerate(problematic_agents, 1):
        print(f"\n{'='*60}")
        print(f"[{i}/{len(problematic_agents)}] ANALIZANDO: {agent_name}")
        print('='*60)
        
        result = runner.run(agent_name)
        
        if result['success']:
            output_file = story_path / f"{agent_name}.json"
            if output_file.exists():
                file_size = output_file.stat().st_size
                
                # Leer y analizar el contenido
                with open(output_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                print(f"\n📊 RESULTADO {agent_name}:")
                print(f"   - Archivo generado: {file_size:,} bytes")
                print(f"   - Longitud JSON: {len(content):,} caracteres")
                
                # Verificar estructura JSON
                try:
                    data = json.loads(content)
                    print(f"   - ✅ JSON válido")
                    
                    # Para agentes de páginas, verificar completitud
                    if "paginas" in data or "paginas_texto_claro" in data or "paginas_texto_pulido" in data:
                        paginas_key = [k for k in data.keys() if "paginas" in k][0]
                        paginas = data[paginas_key]
                        print(f"   - Páginas encontradas: {len(paginas)}/10")
                        
                        # Verificar páginas vacías
                        empty_pages = []
                        for p in range(1, 11):
                            page_key = str(p)
                            if page_key not in paginas or not paginas[page_key]:
                                empty_pages.append(p)
                        
                        if empty_pages:
                            print(f"   - ⚠️ Páginas vacías: {empty_pages}")
                        else:
                            print(f"   - ✅ Todas las páginas tienen contenido")
                            
                except json.JSONDecodeError as e:
                    print(f"   - ❌ JSON inválido: {e}")
                    print(f"   - Últimos 100 chars: ...{content[-100:]}")
                
                results[agent_name] = {
                    'success': True,
                    'file_size': file_size,
                    'char_length': len(content)
                }
            else:
                print(f"   - ❌ Archivo no generado")
                results[agent_name] = {'success': False}
        else:
            print(f"\n❌ ERROR en {agent_name}:")
            print(f"   {result.get('error', 'Unknown')[:200]}")
            results[agent_name] = {'success': False, 'error': result.get('error')}
    
    # Resumen
    print("\n" + "="*60)
    print("📊 RESUMEN DE ANÁLISIS")
    print("="*60)
    
    for agent, info in results.items():
        if info.get('success'):
            print(f"✅ {agent:20} - {info['char_length']:,} chars, {info['file_size']:,} bytes")
        else:
            error = info.get('error', 'No output')[:50]
            print(f"❌ {agent:20} - {error}")
    
    print("\n" + "="*60)
    print("Ver archivo de log para análisis detallado de truncamiento")
    print("="*60)

if __name__ == "__main__":
    analyze_truncation()