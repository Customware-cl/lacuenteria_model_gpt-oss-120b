#!/usr/bin/env python3
"""
Test del cuentacuentos con dependencias reales
"""
import json
import sys
import time

sys.path.append('/home/ubuntu/cuenteria/src')

from llm_client import get_llm_client

def test_con_dependencias_reales():
    print("="*70)
    print("🧪 TEST CUENTACUENTOS CON DEPENDENCIAS REALES")
    print("="*70)
    
    client = get_llm_client()
    client.timeout = 300  # 5 minutos
    
    # Cargar el prompt real del sistema
    with open('flujo/v2/agentes/03_cuentacuentos.json', 'r') as f:
        agent_config = json.load(f)
    system_prompt = agent_config['content']
    
    # Cargar dependencias reales
    try:
        with open('runs/test-v2-emilia-1756440401/01_director.json', 'r') as f:
            director = json.load(f)
        with open('runs/test-v2-emilia-1756440401/02_psicoeducador.json', 'r') as f:
            psico = json.load(f)
        print("✓ Dependencias reales cargadas")
    except:
        print("⚠️ Usando dependencias mínimas de prueba")
        director = {
            "leitmotiv": "¡Tic, tac, la canción del pastel!",
            "beat_sheet": [{"pagina": i, "objetivo": f"Obj {i}", 
                          "conflicto": f"Conf {i}" if i<10 else None,
                          "resolucion": f"Res {i}" if i==10 else None,
                          "emocion": "alegría", 
                          "imagen_nuclear": f"Img {i}"} for i in range(1,11)]
        }
        psico = {"mapa_psico_narrativo": {str(i): {"micro_habilidades": ["hab1"]} for i in range(1,11)}}
    
    # Construir prompt del usuario con diferentes tamaños
    versiones = [
        ("MÍNIMO", "Genera el cuento. Usa el leitmotiv en páginas 2, 5 y 10."),
        ("REDUCIDO", f"Usa este beat sheet:\n{json.dumps(director['beat_sheet'], ensure_ascii=False)}\nLeitmotiv: {director['leitmotiv']}"),
        ("COMPLETO", f"=== DIRECTOR ===\n{json.dumps(director, ensure_ascii=False, indent=2)}\n\n=== PSICOEDUCADOR ===\n{json.dumps(psico, ensure_ascii=False, indent=2)}")
    ]
    
    print(f"\n📊 Tamaño del system prompt: {len(system_prompt)} chars")
    
    for nombre, user_prompt in versiones:
        print(f"\n{'='*50}")
        print(f"🔧 Probando versión: {nombre}")
        print(f"   User prompt: {len(user_prompt)} chars")
        print(f"   Total: {len(system_prompt) + len(user_prompt)} chars")
        print(f"   Tokens aprox: {(len(system_prompt) + len(user_prompt)) // 4}")
        
        # Probar con diferentes max_tokens
        for max_tokens in [4000, 6000, 8000]:
            print(f"\n   → max_tokens={max_tokens}")
            
            try:
                start = time.time()
                result = client.generate(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    temperature=0.7,
                    max_tokens=max_tokens
                )
                elapsed = time.time() - start
                
                print(f"   ✅ ÉXITO en {elapsed:.1f}s")
                
                # Verificar estructura
                if isinstance(result, str):
                    try:
                        result = json.loads(result)
                    except:
                        print(f"      ⚠️ No es JSON válido")
                        continue
                
                if 'paginas_texto' in result:
                    print(f"      ✓ {len(result['paginas_texto'])} páginas generadas")
                    
                    # Guardar resultado exitoso
                    filename = f'cuentacuentos_{nombre}_{max_tokens}.json'
                    with open(filename, 'w') as f:
                        json.dump(result, f, ensure_ascii=False, indent=2)
                    print(f"      💾 Guardado: {filename}")
                    
                    # Si funciona, no probar más tokens
                    break
                else:
                    print(f"      ⚠️ Estructura incorrecta")
                    
            except ValueError as ve:
                elapsed = time.time() - start
                if "no generó contenido" in str(ve):
                    print(f"   ❌ Modelo devolvió vacío en {elapsed:.1f}s")
                else:
                    print(f"   ❌ Error: {ve}")
            except Exception as e:
                print(f"   ❌ Error: {str(e)[:100]}")
    
    print("\n" + "="*70)
    print("📊 ANÁLISIS FINAL")
    print("="*70)
    
    import os
    exitosos = [f for f in os.listdir('.') if f.startswith('cuentacuentos_') and f.endswith('.json')]
    
    if exitosos:
        print(f"\n✅ Configuraciones exitosas: {len(exitosos)}")
        for f in exitosos:
            size = os.path.getsize(f)
            print(f"   - {f} ({size} bytes)")
            
        # Analizar el más exitoso
        with open(exitosos[0], 'r') as f:
            data = json.load(f)
            if 'paginas_texto' in data:
                total_chars = sum(len(v) for v in data['paginas_texto'].values())
                print(f"\n📝 Análisis del exitoso:")
                print(f"   - Total caracteres generados: {total_chars}")
                print(f"   - Promedio por página: {total_chars//10}")
    else:
        print("\n❌ Ninguna configuración funcionó con dependencias reales")
        print("\n🔍 DIAGNÓSTICO:")
        print("1. El prompt simple (512 chars) funciona ✓")
        print("2. El prompt con dependencias reales probablemente excede el contexto")
        print("3. Soluciones posibles:")
        print("   - Reducir el tamaño de las dependencias")
        print("   - Resumir beat_sheet y mapa_psico")
        print("   - Dividir en sub-tareas (5 páginas cada una)")
        print("   - Usar un prompt más conciso")

if __name__ == "__main__":
    test_con_dependencias_reales()