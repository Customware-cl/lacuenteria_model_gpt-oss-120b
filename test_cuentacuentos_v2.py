#!/usr/bin/env python3
"""
Test directo del cuentacuentos con configuración v2
"""
import sys
import os
import json
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from agent_runner import AgentRunner
from config import AGENT_MAX_TOKENS

def test_cuentacuentos_v2():
    print("=" * 70)
    print("TEST DIRECTO DEL CUENTACUENTOS V2")
    print("=" * 70)
    
    # Verificar configuración
    agent_name = "03_cuentacuentos"
    max_tokens_config = AGENT_MAX_TOKENS.get(agent_name)
    
    print(f"\n📊 Configuración de tokens:")
    print(f"   Agent name: {agent_name}")
    print(f"   Max tokens configurados: {max_tokens_config}")
    print(f"   Configuraciones disponibles: {list(AGENT_MAX_TOKENS.keys())}")
    
    # Crear story_id de prueba
    import time
    story_id = f"test-cuentacuentos-{int(time.time())}"
    print(f"\n📝 Story ID: {story_id}")
    
    # Crear directorio y dependencias simuladas
    story_dir = f"runs/{story_id}"
    os.makedirs(story_dir, exist_ok=True)
    os.makedirs(f"{story_dir}/logs", exist_ok=True)
    
    # Crear brief
    brief = {
        "story_id": story_id,
        "personajes": ["Emilia"],
        "historia": "Emilia celebra su cumpleaños con amigos",
        "mensaje_a_transmitir": "La amistad es importante",
        "edad_objetivo": 3
    }
    
    with open(f"{story_dir}/brief.json", "w") as f:
        json.dump(brief, f, ensure_ascii=False, indent=2)
    
    # Crear dependencias mínimas
    director_output = {
        "beat_sheet": {
            "1": "Emilia se despierta emocionada",
            "2": "Prepara todo para la fiesta",
            "3": "Los amigos empiezan a llegar",
            "4": "Juegan y se divierten",
            "5": "Momento del pastel",
            "6": "Sopla las velas",
            "7": "Abre los regalos",
            "8": "Bailan y cantan",
            "9": "Los amigos se despiden",
            "10": "Emilia agradecida se duerme"
        },
        "leitmotiv": "La amistad hace todo especial"
    }
    
    psicoeducador_output = {
        "metas_conductuales": ["Compartir", "Agradecer", "Expresar alegría"],
        "recursos_psicologicos": ["Empatía", "Gratitud", "Cooperación"]
    }
    
    with open(f"{story_dir}/01_director.json", "w") as f:
        json.dump(director_output, f, ensure_ascii=False, indent=2)
    
    with open(f"{story_dir}/02_psicoeducador.json", "w") as f:
        json.dump(psicoeducador_output, f, ensure_ascii=False, indent=2)
    
    # Ejecutar cuentacuentos
    print("\n🚀 Ejecutando cuentacuentos...")
    print("=" * 70)
    
    runner = AgentRunner(story_id, mode_verificador_qa=True, version="v2")
    result = runner.run_agent("03_cuentacuentos")
    
    print("\n" + "=" * 70)
    print("📊 RESULTADO:")
    print("=" * 70)
    
    if result["status"] == "success":
        print("✅ Éxito!")
        print(f"   Reintentos: {result.get('retry_count', 0)}")
        print(f"   QA Score: {result.get('qa_scores', {}).get('promedio', {}).get('nota_final', 'N/A')}")
        
        # Guardar resultado
        output_file = f"{story_id}_resultado.json"
        with open(output_file, "w") as f:
            json.dump(result["output"], f, ensure_ascii=False, indent=2)
        print(f"\n💾 Resultado guardado en: {output_file}")
    else:
        print(f"❌ Error: {result.get('error')}")
        
        # Ver si hay alerta
        alert_file = f"{story_dir}/alerts/03_cuentacuentos_alert.json"
        if os.path.exists(alert_file):
            with open(alert_file) as f:
                alert = json.load(f)
            print(f"\n🚨 Alerta generada:")
            print(f"   Tipo: {alert.get('tipo')}")
            print(f"   Max tokens usado: {alert.get('contexto', {}).get('max_tokens')}")
            print(f"   Tokens aproximados: {alert.get('contexto', {}).get('approx_tokens')}")

if __name__ == "__main__":
    test_cuentacuentos_v2()