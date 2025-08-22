#!/usr/bin/env python3
"""
Optimización de cuentacuentos - reducir repeticiones y mejorar calidad poética
"""
import json
import time
import sys
import os
from datetime import datetime
from pathlib import Path
import re

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from prompt_version_manager import get_prompt_manager
from llm_client_optimized import get_optimized_llm_client

def analyze_repetitions(text):
    """Analiza repeticiones en el texto"""
    words = re.findall(r'\b\w+\b', text.lower())
    word_count = {}
    for word in words:
        if len(word) > 3:  # Ignorar palabras cortas
            word_count[word] = word_count.get(word, 0) + 1
    
    # Contar palabras repetidas más de 4 veces
    excessive_repetitions = {w: c for w, c in word_count.items() if c > 4}
    return excessive_repetitions, sum(word_count.values())

def test_cuentacuentos():
    """Prueba de optimización para cuentacuentos"""
    
    print("🧪 OPTIMIZACIÓN DE cuentacuentos")
    print("=" * 60)
    print("Objetivo: Reducir repeticiones (actual: 'brilla' 5x, 'luz' 8x)")
    print("=" * 60)
    
    prompt_manager = get_prompt_manager()
    llm_client = get_optimized_llm_client()
    
    # Dependencias de cuentacuentos
    dependencies = {
        "director": {
            "leitmotiv": "¡Juntos brillamos más!",  # Cambiado para evitar repetir "luz"
            "beat_sheet": [
                {"pagina": 1, "objetivo": "Presentar a Emilia en el jardín", "conflicto": "soledad inicial", "emocion": "curiosidad", "imagen_nuclear": "Niña bajo árbol mirando cielo"},
                {"pagina": 2, "objetivo": "Aparece el unicornio", "conflicto": "encuentro inesperado", "emocion": "asombro", "imagen_nuclear": "Unicornio con cuerno brillante en neblina"},
                {"pagina": 3, "objetivo": "Primer contacto sin palabras", "conflicto": "barrera de comunicación", "emocion": "ternura", "imagen_nuclear": "Manos extendidas encontrándose"},
                {"pagina": 4, "objetivo": "Desarrollan lenguaje gestual", "conflicto": "torpeza inicial", "emocion": "diversión", "imagen_nuclear": "Danza de gestos y movimientos"},
                {"pagina": 5, "objetivo": "Descubren poder conjunto", "conflicto": "coordinación", "emocion": "emoción", "imagen_nuclear": "Chispas de luz al tocarse"},
                {"pagina": 6, "objetivo": "Bailan creando magia", "conflicto": "ninguno", "emocion": "alegría", "imagen_nuclear": "Giros bajo constelaciones"},
                {"pagina": 7, "objetivo": "Aparece sombra amenazante", "conflicto": "miedo", "emocion": "tensión", "imagen_nuclear": "Sombra gris sobre unicornio"},
                {"pagina": 8, "objetivo": "Vencen oscuridad juntos", "conflicto": "enfrentamiento", "emocion": "valentía", "resolucion": "luz vence", "imagen_nuclear": "Explosión de luz rosa"},
                {"pagina": 9, "objetivo": "Celebran victoria", "conflicto": "ninguno", "emocion": "júbilo", "imagen_nuclear": "Abrazo luminoso"},
                {"pagina": 10, "objetivo": "Amistad eterna", "conflicto": "ninguno", "resolucion": "unión permanente", "emocion": "paz", "imagen_nuclear": "Atardecer dorado juntos"}
            ]
        },
        "psicoeducador": {
            "recursos_psicologicos": ["comunicación no verbal", "empatía", "trabajo en equipo", "valentía compartida"],
            "metas_conductuales": ["expresar sin palabras", "comprender al diferente", "colaborar", "enfrentar miedos juntos"],
            "elementos_terapeuticos": ["validación emocional", "modelado de coraje", "refuerzo de vínculos"]
        }
    }
    
    # Matriz de configuraciones
    test_configs = [
        {
            "name": "baseline_original",
            "variant": "original",
            "params": {
                "temperature": 0.90,
                "max_tokens": 4000
            }
        },
        {
            "name": "anti_repetition_controlled",
            "variant": "anti_repetition",
            "params": {
                "temperature": 0.75,
                "top_p": 0.85,
                "repetition_penalty": 1.25,  # Alto para evitar repeticiones
                "frequency_penalty": 0.5,     # Penaliza palabras frecuentes
                "presence_penalty": 0.3,      # Incentiva vocabulario nuevo
                "max_tokens": 6000
            }
        },
        {
            "name": "structured_metrics_balanced",
            "variant": "structured_metrics",
            "params": {
                "temperature": 0.70,
                "top_p": 0.80,
                "repetition_penalty": 1.20,
                "frequency_penalty": 0.4,
                "max_tokens": 6000,
                "seed": 42
            }
        },
        {
            "name": "with_examples_creative",
            "variant": "with_verse_examples",
            "params": {
                "temperature": 0.78,
                "top_p": 0.88,
                "top_k": 40,
                "repetition_penalty": 1.18,
                "frequency_penalty": 0.35,
                "max_tokens": 6500
            }
        },
        {
            "name": "narrative_flow_optimal",
            "variant": "narrative_flow",
            "params": {
                "temperature": 0.72,
                "top_p": 0.82,
                "top_k": 35,
                "repetition_penalty": 1.22,
                "frequency_penalty": 0.45,
                "presence_penalty": 0.25,
                "max_tokens": 6000,
                "seed": 42
            }
        }
    ]
    
    results = []
    
    for i, config in enumerate(test_configs, 1):
        print(f"\n[{i}/{len(test_configs)}] Testing: {config['name']}")
        print("-" * 40)
        
        try:
            # Cargar variante
            prompt_data = prompt_manager.load_variant("cuentacuentos", config["variant"])
            system_prompt = prompt_data["content"]
            
            # User prompt con dependencias
            user_prompt = f"""Crea los versos para el cuento basándote en:

Director (beat sheet):
{json.dumps(dependencies["director"], ensure_ascii=False, indent=2)}

Psicoeducador (recursos):
{json.dumps(dependencies["psicoeducador"], ensure_ascii=False, indent=2)}

IMPORTANTE:
- 10 páginas con 4 versos cada una
- Evita repetir palabras (especialmente "brilla", "luz", "magia")
- Usa vocabulario variado y sinónimos
- Mantén musicalidad y rima natural"""
            
            print(f"  Variante: {config['variant']}")
            print(f"  Repetition penalty: {config['params'].get('repetition_penalty', 'N/A')}")
            print(f"  Frequency penalty: {config['params'].get('frequency_penalty', 'N/A')}")
            
            start_time = time.time()
            
            # Ejecutar
            result = llm_client.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                **config['params']
            )
            
            execution_time = time.time() - start_time
            
            # Analizar resultado
            pages = result.get("paginas", {}) or result.get("paginas_texto", {})
            if pages:
                all_text = " ".join(pages.values())
                repetitions, total_words = analyze_repetitions(all_text)
                
                # QA Score basado en repeticiones
                qa_score = 5.0
                repetition_penalty = sum(0.2 for count in repetitions.values() if count > 5)
                qa_score = max(2.0, qa_score - repetition_penalty)
                
                # Verificar rimas forzadas
                forced_rhymes = 0
                for page_text in pages.values():
                    lines = page_text.split('\\n')
                    if len(lines) >= 2:
                        # Detectar rimas idénticas
                        for j in range(0, len(lines)-1, 2):
                            if j+1 < len(lines):
                                word1 = lines[j].split()[-1] if lines[j].split() else ""
                                word2 = lines[j+1].split()[-1] if lines[j+1].split() else ""
                                if word1.lower() == word2.lower():
                                    forced_rhymes += 1
                
                qa_score = max(2.0, qa_score - (forced_rhymes * 0.1))
                
                test_result = {
                    "config_name": config["name"],
                    "variant": config["variant"],
                    "execution_time": execution_time,
                    "qa_score": round(qa_score, 2),
                    "repetitions": repetitions,
                    "worst_repetition": max(repetitions.items(), key=lambda x: x[1]) if repetitions else None,
                    "total_unique_words": len(set(re.findall(r'\b\w+\b', all_text.lower()))),
                    "forced_rhymes": forced_rhymes,
                    "pages_count": len(pages),
                    "sample": pages.get("1", "")[:150] if pages else ""
                }
                
                results.append(test_result)
                
                print(f"  ✅ Success!")
                print(f"     QA: {qa_score:.2f}/5")
                print(f"     Repeticiones excesivas: {len(repetitions)}")
                if repetitions:
                    worst = max(repetitions.items(), key=lambda x: x[1])
                    print(f"     Peor repetición: '{worst[0]}' ({worst[1]}x)")
                print(f"     Rimas forzadas: {forced_rhymes}")
                print(f"     Tiempo: {execution_time:.1f}s")
            else:
                print(f"  ❌ No pages generated")
                
        except Exception as e:
            print(f"  ❌ Error: {str(e)[:100]}")
            results.append({
                "config_name": config["name"],
                "variant": config["variant"],
                "error": str(e)[:200]
            })
        
        time.sleep(3)
    
    # Análisis final
    print("\n" + "=" * 60)
    print("📊 ANÁLISIS DE RESULTADOS - cuentacuentos")
    print("=" * 60)
    
    successful = [r for r in results if "error" not in r]
    ranked = []
    if successful:
        # Ranking por QA y repeticiones
        ranked = sorted(successful, key=lambda x: (x["qa_score"], -len(x.get("repetitions", {})), -x["execution_time"]), reverse=True)
        
        print("\n🏆 MEJOR CONFIGURACIÓN:")
        best = ranked[0]
        print(f"   {best['config_name']}")
        print(f"   • Variante: {best['variant']}")
        print(f"   • QA Score: {best['qa_score']}/5")
        print(f"   • Repeticiones excesivas: {len(best.get('repetitions', {}))}")
        if best.get('worst_repetition'):
            print(f"   • Peor repetición: '{best['worst_repetition'][0]}' ({best['worst_repetition'][1]}x)")
        print(f"   • Rimas forzadas: {best.get('forced_rhymes', 0)}")
        print(f"   • Vocabulario único: {best.get('total_unique_words', 0)} palabras")
        print(f"   • Tiempo: {best['execution_time']:.1f}s")
        
        print("\n📈 Comparación completa:")
        print(f"{'Config':<30} {'QA':<6} {'Rep':<5} {'Rimas':<6} {'Vocab':<6} {'Time':<6}")
        print("-" * 60)
        for r in ranked:
            print(f"{r['config_name']:<30} {r['qa_score']:<6.1f} {len(r.get('repetitions', {})):<5} "
                  f"{r.get('forced_rhymes', 0):<6} {r.get('total_unique_words', 0):<6} {r['execution_time']:<6.1f}")
    
    # Guardar resultados
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = Path(f"optimization_results/cuentacuentos_{timestamp}.json")
    results_file.parent.mkdir(exist_ok=True)
    
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": timestamp,
            "results": results,
            "best_config": ranked[0] if ranked else None
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Resultados guardados: {results_file}")
    
    return results

if __name__ == "__main__":
    test_cuentacuentos()