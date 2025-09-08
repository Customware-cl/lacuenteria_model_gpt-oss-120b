#!/usr/bin/env python3
"""
Test del agente cuentacuentos con mode_verificador_qa deshabilitado
Verifica que NO se ejecute el verificador QA para páginas individuales
"""

import json
import sys
import os
from datetime import datetime
from pathlib import Path

# Agregar src al path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

def test_cuentacuentos_sin_qa():
    """Prueba que cuentacuentos respete mode_verificador_qa=False"""
    
    print("🧪 Test de cuentacuentos SIN verificador QA")
    print("="*60)
    
    # Verificar configuración
    config_path = Path("flujo/v2/config.json")
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    mode_qa = config.get("mode_verificador_qa", True)
    print(f"📊 mode_verificador_qa actual: {mode_qa}")
    
    if mode_qa:
        print("⚠️  ADVERTENCIA: mode_verificador_qa está en True")
        print("   El test esperaba que esté en False")
        print("   Puedes cambiarlo en flujo/v2/config.json")
    else:
        print("✅ mode_verificador_qa está correctamente en False")
    
    print("\n📝 Configuración del test:")
    print("   - Pipeline: v2")
    print("   - Agente: 03_cuentacuentos")
    print("   - Verificador QA: DESHABILITADO")
    print()
    
    # Crear una prueba simple
    from agent_runner import AgentRunner
    
    test_story_id = f"test-cuentacuentos-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    print(f"📖 Story ID de prueba: {test_story_id}")
    
    # Crear estructura mínima necesaria
    story_path = Path("runs") / test_story_id
    story_path.mkdir(parents=True, exist_ok=True)
    (story_path / "inputs").mkdir(exist_ok=True)
    (story_path / "outputs").mkdir(exist_ok=True)
    (story_path / "outputs" / "agents").mkdir(exist_ok=True)
    (story_path / "logs").mkdir(exist_ok=True)
    
    # Crear dependencias mínimas para cuentacuentos
    director_output = {
        "beat_sheet": {
            "1": {"momento_emocional": "inicio", "descripcion": "Luna conoce al sol"},
            "2": {"momento_emocional": "desarrollo", "descripcion": "Aventura juntos"},
            "3": {"momento_emocional": "climax", "descripcion": "Desafío de la noche"},
            "4": {"momento_emocional": "resolucion", "descripcion": "Amistad eterna"},
            "5": {"momento_emocional": "paz", "descripcion": "Cielo en armonía"},
            "6": {"momento_emocional": "alegria", "descripcion": "Celebración"},
            "7": {"momento_emocional": "reflexion", "descripcion": "Aprendizaje"},
            "8": {"momento_emocional": "calma", "descripcion": "Tranquilidad"},
            "9": {"momento_emocional": "esperanza", "descripcion": "Futuro brillante"},
            "10": {"momento_emocional": "cierre", "descripcion": "Final feliz"}
        },
        "leitmotiv": "brilla tu luz"
    }
    
    psicoeducador_output = {
        "metas_conductuales": ["aceptación", "amistad", "valentía"],
        "recursos_psicologicos": ["empatía", "colaboración", "resiliencia"]
    }
    
    # Guardar dependencias
    with open(story_path / "outputs" / "agents" / "01_director.json", 'w') as f:
        json.dump(director_output, f, ensure_ascii=False, indent=2)
    
    with open(story_path / "outputs" / "agents" / "02_psicoeducador.json", 'w') as f:
        json.dump(psicoeducador_output, f, ensure_ascii=False, indent=2)
    
    # Brief mínimo
    brief = {
        "personajes": ["Luna", "Sol"],
        "historia": "Una historia de amistad entre la luna y el sol",
        "mensaje_a_transmitir": "La amistad supera las diferencias",
        "edad_objetivo": 5
    }
    
    with open(story_path / "brief.json", 'w') as f:
        json.dump(brief, f, ensure_ascii=False, indent=2)
    
    print("\n🚀 Ejecutando cuentacuentos con verificador QA deshabilitado...")
    print("-"*60)
    
    try:
        # Crear runner con mode_verificador_qa=False
        runner = AgentRunner(test_story_id, mode_verificador_qa=False, version="v2")
        
        # Ejecutar cuentacuentos
        result = runner.run_agent("03_cuentacuentos")
        
        print("\n📊 Resultado:")
        print(f"   Status: {result.get('status')}")
        print(f"   Processing mode: {result.get('processing_mode')}")
        
        # Verificar que NO se hayan creado archivos de verificador_qa
        qa_files = list(story_path.glob("**/verificador_qa*.json"))
        
        if qa_files:
            print(f"\n⚠️  Se encontraron {len(qa_files)} archivos de verificador_qa:")
            for f in qa_files[:3]:
                print(f"   - {f.name}")
            print("   Esto NO debería pasar con mode_verificador_qa=False")
        else:
            print("\n✅ No se encontraron archivos de verificador_qa (correcto)")
        
        # Verificar logs
        log_files = list((story_path / "logs").glob("*.log"))
        has_qa_logs = any("verificador" in f.read_text() for f in log_files if f.stat().st_size < 100000)
        
        if has_qa_logs:
            print("\n⚠️  Los logs mencionan 'verificador' (verificar si es esperado)")
        else:
            print("✅ Los logs no mencionan verificador QA")
        
        # Verificar el output
        cuentacuentos_file = story_path / "outputs" / "agents" / "03_cuentacuentos.json"
        if cuentacuentos_file.exists():
            with open(cuentacuentos_file, 'r') as f:
                output = json.load(f)
            
            print(f"\n📝 Output generado:")
            print(f"   Páginas: {len(output.get('paginas', {}))}")
            
            # Verificar metadata
            metadata = output.get('metadata', {})
            if 'average_qa_score' in metadata:
                print(f"   QA Score promedio: {metadata['average_qa_score']}")
                if metadata['average_qa_score'] == 4.5:
                    print("   ✅ Score 4.5 indica QA automático (sin verificador)")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60)
    print("✨ Test completado")
    print("\nNOTA: Con mode_verificador_qa=False:")
    print("- NO debe ejecutar verificador_qa para páginas individuales")
    print("- Las páginas deben aprobarse automáticamente con score 4.5")
    print("- El procesamiento debe ser más rápido")

if __name__ == "__main__":
    test_cuentacuentos_sin_qa()