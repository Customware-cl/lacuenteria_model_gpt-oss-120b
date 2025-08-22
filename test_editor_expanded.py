#!/usr/bin/env python3
"""
Prueba expandida para encontrar la configuración óptima de editor_claridad
"""
import json
import time
import sys
import os
from datetime import datetime
from pathlib import Path

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from prompt_version_manager import get_prompt_manager
from llm_client_optimized import get_optimized_llm_client

def test_editor_expanded():
    """Prueba expandida con más combinaciones"""
    
    print("🧪 PRUEBA EXPANDIDA: editor_claridad")
    print("=" * 60)
    
    prompt_manager = get_prompt_manager()
    llm_client = get_optimized_llm_client()
    
    # Input estándar
    cuentacuentos_output = {
        "paginas": {
            "1": "Emilia bajo el árbol sueña bajo cielo azul\\nSus dedos señalan flores que brotan en tierra brillante\\nEl jardín despliega colores en su alegre danza\\nY siente en su pecho cálida señal de magia",
            "2": "En el bosque claro niebla ligera danza\\nUn unicornio surge, su cuerno refleja luz\\nRayo rosado ilumina su rostro con consuelo\\nEmilia observa curiosa, corazón late esperanza",
            "3": "Emilia abre su mano invitando al ser\\nEl unicornio inclina cabeza con ternura\\nSus ojos se encuentran, nace vínculo silencioso\\nSin palabras comparten pulsación como lazos",
            "4": "Emilia muestra palma como saludo suave\\nEl unicornio inclina oreja comprendiendo\\nMovimiento se vuelve danza sin sonido\\nAl principio confuso, fluye en armonía",
            "5": "Manos y cuerno rozan, brillo tenue surge\\nCada intento lanza chispas de luz clara\\nMagia vibra en aire como estrellas\\nJardín se ilumina, gestos encienden luces",
            "6": "Emilia y unicornio giran al compás\\nNotas invisibles flotan, pies bailan\\nLuces forman constelaciones pequeñas\\nNoche se llena de sueños estelares",
            "7": "Sombra gris pasa sobre el unicornio\\nEmilia extiende mano, luz cálida disipa\\nSobresalto sacude pero se tranquiliza\\nValentía brilla, reemplaza temor con seguridad",
            "8": "Juntos unen mano y cuerno radiante\\nGesto brilla fuerte con pura energía\\nExplosión rosa como pétalos suaves\\nSombra desvanece bajo luz rosada",
            "9": "Unicornio y Emilia abrazan con ternura\\nCuerpos vibran compartiendo calor sincero\\nDedos dibujan alas como mariposas\\nJardín celebra bajo brillo de alas",
            "10": "Bajo dorado atardecer siguen bailando\\nSombras se alejan, tranquilidad llega\\nDibujan corazones luminosos irradiando paz\\nCielo responde con luz eterna abrazando"
        }
    }
    
    # Matriz de configuraciones expandida
    # Variantes más exitosas + nuevos parámetros
    test_matrix = [
        # Configuraciones base que funcionaron
        {
            "name": "original_baseline",
            "variant": "original",
            "params": {"temperature": 0.60, "max_tokens": 4000}
        },
        {
            "name": "with_examples_conservative",
            "variant": "with_examples",
            "params": {"temperature": 0.40, "top_p": 0.50, "top_k": 20, "repetition_penalty": 1.1, "max_tokens": 6000}
        },
        
        # Nuevas combinaciones optimizadas
        {
            "name": "with_examples_optimized_v1",
            "variant": "with_examples",
            "params": {
                "temperature": 0.45,
                "top_p": 0.60,
                "top_k": 25,
                "repetition_penalty": 1.05,
                "frequency_penalty": 0.1,
                "max_tokens": 6000,
                "seed": 42
            }
        },
        {
            "name": "structured_optimized_v1",
            "variant": "structured_process",
            "params": {
                "temperature": 0.38,
                "top_p": 0.45,
                "top_k": 18,
                "repetition_penalty": 1.12,
                "frequency_penalty": 0.15,
                "presence_penalty": 0.1,
                "max_tokens": 7000,
                "seed": 42
            }
        },
        {
            "name": "detailed_balanced",
            "variant": "detailed_criteria",
            "params": {
                "temperature": 0.42,
                "top_p": 0.55,
                "top_k": 22,
                "repetition_penalty": 1.08,
                "max_tokens": 6500
            }
        },
        
        # Anti-truncation con ajustes menos agresivos
        {
            "name": "anti_truncation_adjusted",
            "variant": "anti_truncation",
            "params": {
                "temperature": 0.35,  # Más alto que 0.30
                "top_p": 0.40,       # Más alto que 0.30
                "top_k": 15,         # Más alto que 10
                "repetition_penalty": 1.15,  # Menos agresivo que 1.2
                "max_tokens": 7500,
                "stop": []  # Sin stop sequences que puedan cortar
            }
        },
        
        # Configuración "ganadora" potencial
        {
            "name": "optimal_candidate",
            "variant": "with_examples",
            "params": {
                "temperature": 0.40,
                "top_p": 0.50,
                "top_k": 20,
                "repetition_penalty": 1.1,
                "frequency_penalty": 0.2,
                "presence_penalty": 0.1,
                "max_tokens": 6500,
                "seed": 42,
                "response_format": "json"  # Forzar formato JSON
            }
        }
    ]
    
    results = []
    successful_count = 0
    
    for i, config in enumerate(test_matrix, 1):
        print(f"\n[{i}/{len(test_matrix)}] Testing: {config['name']}")
        print("-" * 40)
        
        try:
            # Cargar prompt
            prompt_data = prompt_manager.load_variant("editor_claridad", config["variant"])
            system_prompt = prompt_data["content"]
            
            # User prompt
            user_prompt = f"""Procesa el siguiente texto para hacerlo más claro para niños de 5 años:

{json.dumps(cuentacuentos_output, ensure_ascii=False, indent=2)}

IMPORTANTE: Genera JSON completo con las 10 páginas editadas."""
            
            print(f"  Variante: {config['variant']}")
            print(f"  Temp: {config['params'].get('temperature')}, MaxTokens: {config['params'].get('max_tokens')}")
            
            start_time = time.time()
            
            # Ejecutar
            result = llm_client.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                **config['params']
            )
            
            execution_time = time.time() - start_time
            
            # Evaluar
            pages = result.get("paginas_texto_claro", {})
            empty_pages = [str(p) for p in range(1, 11) if not pages.get(str(p), "").strip()]
            is_complete = len(empty_pages) == 0
            
            # QA Score mejorado
            qa_score = 5.0
            if not pages:
                qa_score = 1.0
            elif empty_pages:
                qa_score -= len(empty_pages) * 0.5
            
            # Bonus por features adicionales
            if result.get("glosario") and len(result["glosario"]) >= 5:
                qa_score = min(5.0, qa_score + 0.2)
            if result.get("cambios_clave") and len(result["cambios_clave"]) >= 3:
                qa_score = min(5.0, qa_score + 0.1)
            
            # Evaluar calidad del texto simplificado
            if pages.get("1"):
                sample_text = pages["1"]
                # Penalizar si tiene palabras complejas
                complex_words = ["despliega", "surge", "refleja", "vibra", "constela"]
                complexity_penalty = sum(0.1 for word in complex_words if word in sample_text.lower())
                qa_score = max(1.0, qa_score - complexity_penalty)
            
            test_result = {
                "config_name": config["name"],
                "variant": config["variant"],
                "execution_time": execution_time,
                "qa_score": round(qa_score, 2),
                "is_complete": is_complete,
                "empty_pages": empty_pages,
                "has_glosario": bool(result.get("glosario")),
                "glosario_size": len(result.get("glosario", [])),
                "params_summary": {
                    "temp": config['params'].get('temperature'),
                    "top_p": config['params'].get('top_p'),
                    "max_tokens": config['params'].get('max_tokens')
                }
            }
            
            results.append(test_result)
            successful_count += 1
            
            print(f"  ✅ Success!")
            print(f"     QA: {qa_score:.2f}/5 | Complete: {is_complete} | Time: {execution_time:.1f}s")
            
        except Exception as e:
            print(f"  ❌ Error: {str(e)[:100]}")
            results.append({
                "config_name": config["name"],
                "variant": config["variant"],
                "error": str(e)[:200]
            })
        
        time.sleep(2)
    
    # Análisis de resultados
    print("\n" + "=" * 60)
    print("📊 ANÁLISIS DE RESULTADOS")
    print("=" * 60)
    
    print(f"\nTasa de éxito: {successful_count}/{len(test_matrix)} ({successful_count*100/len(test_matrix):.0f}%)")
    
    # Ranking
    successful = [r for r in results if "error" not in r]
    if successful:
        ranked = sorted(successful, key=lambda x: (x["qa_score"], -x["execution_time"]), reverse=True)
        
        print("\n🏆 TOP 3 CONFIGURACIONES:")
        for i, r in enumerate(ranked[:3], 1):
            print(f"\n{i}. {r['config_name']}")
            print(f"   • Variante: {r['variant']}")
            print(f"   • QA Score: {r['qa_score']}/5")
            print(f"   • Completo: {'Sí' if r['is_complete'] else 'No'}")
            print(f"   • Glosario: {'Sí' if r['has_glosario'] else 'No'} ({r['glosario_size']} items)")
            print(f"   • Tiempo: {r['execution_time']:.1f}s")
            print(f"   • Params: T={r['params_summary']['temp']}, P={r['params_summary']['top_p']}")
    
    # Guardar
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = Path(f"optimization_results/editor_expanded_{timestamp}.json")
    results_file.parent.mkdir(exist_ok=True)
    
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": timestamp,
            "total_tests": len(test_matrix),
            "successful": successful_count,
            "results": results,
            "best_config": ranked[0] if ranked else None
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Resultados guardados: {results_file}")
    
    # Recomendación final
    if ranked:
        best = ranked[0]
        print("\n" + "=" * 60)
        print("🎯 CONFIGURACIÓN RECOMENDADA PARA editor_claridad:")
        print(f"   Variante: {best['variant']}")
        print(f"   Temperatura: {best['params_summary']['temp']}")
        print(f"   Top-p: {best['params_summary']['top_p']}")
        print(f"   Max tokens: {best['params_summary']['max_tokens']}")
        print("=" * 60)
    
    return results

if __name__ == "__main__":
    test_editor_expanded()