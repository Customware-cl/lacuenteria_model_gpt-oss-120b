#!/usr/bin/env python3
"""
Script simplificado de testing para optimización de editor_claridad
"""
import json
import time
import sys
import os
from datetime import datetime
from pathlib import Path

# Agregar src al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from prompt_version_manager import get_prompt_manager
from llm_client_optimized import get_optimized_llm_client

def test_editor_claridad():
    """Prueba rápida de optimización para editor_claridad"""
    
    print("🧪 PRUEBA DE OPTIMIZACIÓN: editor_claridad")
    print("=" * 60)
    
    # Inicializar componentes
    prompt_manager = get_prompt_manager()
    llm_client = get_optimized_llm_client()
    
    # Input de cuentacuentos para editor_claridad
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
        },
        "leitmotiv": "¡Brilla, brilla, luz de amistad!"
    }
    
    # Configuraciones a probar
    test_configs = [
        {
            "name": "Test 1: Original + Baseline",
            "variant": "original",
            "params": {
                "temperature": 0.60,
                "max_tokens": 4000
            }
        },
        {
            "name": "Test 2: Anti-truncation + Ultra-conservative",
            "variant": "anti_truncation",
            "params": {
                "temperature": 0.30,
                "top_p": 0.30,
                "top_k": 10,
                "repetition_penalty": 1.2,
                "max_tokens": 8000,
                "frequency_penalty": 0.2
            }
        },
        {
            "name": "Test 3: With-examples + Conservative",
            "variant": "with_examples",
            "params": {
                "temperature": 0.40,
                "top_p": 0.50,
                "top_k": 20,
                "repetition_penalty": 1.1,
                "max_tokens": 6000
            }
        },
        {
            "name": "Test 4: Structured + Balanced",
            "variant": "structured_process",
            "params": {
                "temperature": 0.35,
                "top_p": 0.40,
                "top_k": 15,
                "repetition_penalty": 1.15,
                "max_tokens": 7000,
                "seed": 42
            }
        }
    ]
    
    results = []
    
    # Ejecutar pruebas
    for i, config in enumerate(test_configs, 1):
        print(f"\n[{i}/{len(test_configs)}] {config['name']}")
        print("-" * 40)
        
        try:
            # Cargar variante de prompt
            prompt_data = prompt_manager.load_variant("editor_claridad", config["variant"])
            system_prompt = prompt_data["content"]
            
            # Construir user prompt
            user_prompt = f"""Procesa el siguiente texto de cuentacuentos para hacerlo más claro:

{json.dumps(cuentacuentos_output, ensure_ascii=False, indent=2)}

Recuerda:
- Simplificar vocabulario para niños de 5 años
- Mantener la métrica y musicalidad
- Una imagen clara por verso
- COMPLETAR LAS 10 PÁGINAS"""
            
            print(f"Ejecutando con variante: {config['variant']}")
            print(f"Parámetros: temp={config['params']['temperature']}, max_tokens={config['params']['max_tokens']}")
            
            start_time = time.time()
            
            # Llamar al LLM
            result = llm_client.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                **config['params']
            )
            
            execution_time = time.time() - start_time
            
            # Evaluar resultado
            pages = result.get("paginas_texto_claro", {})
            empty_pages = [str(p) for p in range(1, 11) if not pages.get(str(p), "").strip()]
            is_complete = len(empty_pages) == 0
            
            # Calcular QA score simple
            if not pages:
                qa_score = 1.0
            elif empty_pages:
                qa_score = max(1.0, 5.0 - (len(empty_pages) * 0.5))
            else:
                glosario = result.get("glosario", [])
                qa_score = 4.5 if len(glosario) >= 3 else 4.0
            
            # Guardar resultado
            test_result = {
                "config": config["name"],
                "variant": config["variant"],
                "execution_time": execution_time,
                "qa_score": qa_score,
                "is_complete": is_complete,
                "empty_pages": empty_pages,
                "tokens_used": result.get("_metadata_tokens", {}),
                "sample": str(pages.get("1", ""))[:200] if pages else "NO OUTPUT"
            }
            
            results.append(test_result)
            
            # Mostrar resultado
            print(f"✅ Completado en {execution_time:.1f}s")
            print(f"   QA Score: {qa_score}/5")
            print(f"   Páginas completas: {'Sí' if is_complete else f'No (vacías: {empty_pages})'}")
            if pages.get("1"):
                print(f"   Muestra página 1: {pages['1'][:100]}...")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            results.append({
                "config": config["name"],
                "variant": config["variant"],
                "error": str(e)
            })
        
        # Pausa entre pruebas
        time.sleep(3)
    
    # Mostrar resumen
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE RESULTADOS")
    print("=" * 60)
    
    # Encontrar mejor resultado
    successful_results = [r for r in results if "error" not in r]
    if successful_results:
        best = max(successful_results, key=lambda x: (x["qa_score"], x["is_complete"]))
        print(f"\n🏆 MEJOR CONFIGURACIÓN:")
        print(f"   {best['config']}")
        print(f"   • Variante: {best['variant']}")
        print(f"   • QA Score: {best['qa_score']}/5")
        print(f"   • Páginas completas: {'Sí' if best['is_complete'] else 'No'}")
        print(f"   • Tiempo: {best['execution_time']:.1f}s")
    
    print(f"\n📈 Comparación de todas las pruebas:")
    for r in results:
        if "error" not in r:
            status = "✅" if r["is_complete"] else "⚠️"
            print(f"   {status} {r['variant']:<20} QA: {r['qa_score']:.1f}/5  Time: {r['execution_time']:.1f}s")
        else:
            print(f"   ❌ {r['variant']:<20} Error: {r['error'][:30]}")
    
    # Guardar resultados
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = Path(f"optimization_results/editor_claridad_test_{timestamp}.json")
    results_file.parent.mkdir(exist_ok=True)
    
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Resultados guardados en: {results_file}")
    
    return results

if __name__ == "__main__":
    test_editor_claridad()