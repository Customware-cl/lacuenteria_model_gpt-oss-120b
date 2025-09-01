#!/usr/bin/env python3
"""
Test específico para el agente cuentacuentos - Solo página 1
Usa los datos del run anterior de director y psicoeducador
"""
import json
import os
import sys
from pathlib import Path

# Agregar el directorio src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from llm_client import get_llm_client
from datetime import datetime

def test_cuentacuentos_pagina1():
    # Cargar datos del run anterior
    run_dir = Path("runs/test-v2-marte-20250830-004948")
    
    # Cargar director y psicoeducador
    with open(run_dir / "01_director.json", 'r', encoding='utf-8') as f:
        director_data = json.load(f)
    
    with open(run_dir / "02_psicoeducador.json", 'r', encoding='utf-8') as f:
        psicoeducador_data = json.load(f)
    
    # Extraer solo la primera página de cada uno
    director_pagina1 = {
        "leitmotiv": director_data["leitmotiv"],
        "beat_sheet": [director_data["beat_sheet"][0]]  # Solo página 1
    }
    
    psicoeducador_pagina1 = {
        "edad_objetivo": psicoeducador_data["edad_objetivo"],
        "mapa_psico_narrativo": [psicoeducador_data["mapa_psico_narrativo"][0]]  # Solo página 1
    }
    
    # Prompt simplificado para una sola página
    system_prompt = """Eres un experto en versos infantiles. Tu tarea es crear 4 versos para la página 1 del cuento.

REGLAS CRÍTICAS:
1. NUNCA uses la misma palabra para rimar
2. Esquema AABB (versos 1-2 riman, versos 3-4 riman)
3. Cada verso: 8-15 sílabas
4. Lenguaje simple para niños de 2 años

PALABRAS PROHIBIDAS PARA RIMAR (no uses la misma palabra dos veces):
❌ "mapa"..."mapa"
❌ "brillante"..."brillante"
❌ "mirar"..."mirar"

EJEMPLO DE RIMAS CORRECTAS:
✅ "mapa"..."papa" o "tapa" o "capa"
✅ "brillante"..."gigante" o "elegante" o "adelante"
✅ "mirar"..."caminar" o "soñar" o "jugar"

Responde SOLO con JSON:
{
  "pagina_1": {
    "verso1": "texto del verso 1",
    "verso2": "texto del verso 2 (rima con verso1)",
    "verso3": "texto del verso 3",
    "verso4": "texto del verso 4 (rima con verso3)",
    "palabras_rima": {
      "par_1": ["palabra_final_verso1", "palabra_final_verso2"],
      "par_2": ["palabra_final_verso3", "palabra_final_verso4"]
    }
  }
}"""

    user_prompt = f"""Crea los 4 versos para la página 1 basándote en:

DIRECTOR (Página 1):
- Objetivo: {director_pagina1['beat_sheet'][0]['objetivo']}
- Conflicto: {director_pagina1['beat_sheet'][0]['conflicto']}
- Emoción: {director_pagina1['beat_sheet'][0]['emocion']}
- Imagen: {director_pagina1['beat_sheet'][0]['imagen_nuclear']}

PSICOEDUCADOR (Página 1):
- Micro-habilidad: {psicoeducador_pagina1['mapa_psico_narrativo'][0]['micro_habilidad']}
- Frase modelo: {psicoeducador_pagina1['mapa_psico_narrativo'][0]['frase_modelo']}

CONTEXTO:
- Personajes: Emilia (2 años) y Caty (su mamá)
- Situación: Descubren un mapa misterioso brillante bajo la manta

Crea 4 versos que:
1. Muestren a Emilia y Caty descubriendo el mapa
2. Expresen curiosidad y emoción positiva
3. NO repitan palabras para rimar
4. Sean comprensibles para un niño de 2 años"""

    # Configuración específica del agente desde v2
    llm_config = {
        "temperature": 0.7,  # Aumentamos un poco para más creatividad
        "max_tokens": 2000,  # Suficiente para una página
        "top_p": 0.95
    }
    
    print("🎭 Test de Cuentacuentos - Solo Página 1")
    print("=" * 50)
    print(f"📊 Configuración:")
    print(f"  • Temperature: {llm_config['temperature']}")
    print(f"  • Max tokens: {llm_config['max_tokens']}")
    print(f"  • Top-p: {llm_config['top_p']}")
    print("=" * 50)
    
    # Inicializar cliente LLM
    llm_client = get_llm_client()
    
    # Ejecutar 3 intentos para ver variaciones
    for intento in range(3):
        print(f"\n🎲 Intento {intento + 1}/3:")
        print("-" * 30)
        
        try:
            response = llm_client.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=llm_config['temperature'],
                max_tokens=llm_config['max_tokens'],
                top_p=llm_config['top_p']
            )
            
            # Parsear respuesta
            if isinstance(response, dict):
                result = response
            else:
                result = json.loads(response)
            
            # Mostrar resultado
            if 'pagina_1' in result:
                pagina = result['pagina_1']
                print(f"📝 Versos generados:")
                print(f"  1: {pagina.get('verso1', 'N/A')}")
                print(f"  2: {pagina.get('verso2', 'N/A')}")
                print(f"  3: {pagina.get('verso3', 'N/A')}")
                print(f"  4: {pagina.get('verso4', 'N/A')}")
                
                if 'palabras_rima' in pagina:
                    rimas = pagina['palabras_rima']
                    print(f"\n🎵 Análisis de rimas:")
                    par1 = rimas.get('par_1', [])
                    par2 = rimas.get('par_2', [])
                    
                    # Verificar si repite palabras
                    repite_1 = len(par1) == 2 and par1[0] == par1[1]
                    repite_2 = len(par2) == 2 and par2[0] == par2[1]
                    
                    estado_1 = "❌ REPITE" if repite_1 else "✅ OK"
                    estado_2 = "❌ REPITE" if repite_2 else "✅ OK"
                    
                    print(f"  • Par 1-2: {par1[0] if par1 else 'N/A'} / {par1[1] if len(par1) > 1 else 'N/A'} {estado_1}")
                    print(f"  • Par 3-4: {par2[0] if par2 else 'N/A'} / {par2[1] if len(par2) > 1 else 'N/A'} {estado_2}")
                    
                    # Calificación
                    if not repite_1 and not repite_2:
                        print("\n✅ ¡ÉXITO! Rimas correctas sin repetición")
                    else:
                        print("\n⚠️ Problemas detectados en las rimas")
            else:
                print("❌ Respuesta no tiene el formato esperado")
                print(json.dumps(result, indent=2, ensure_ascii=False))
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("✨ Test completado")
    
    # Guardar resultados
    output_file = f"test_cuentacuentos_p1_{datetime.now().strftime('%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "config": llm_config,
            "prompts": {
                "system": system_prompt,
                "user": user_prompt
            }
        }, f, ensure_ascii=False, indent=2)
    
    print(f"📁 Resultados guardados en: {output_file}")

if __name__ == "__main__":
    test_cuentacuentos_pagina1()