#!/usr/bin/env python3
"""
Test simple y directo del cuentacuentos
"""
import json
import sys
import time

sys.path.append('/home/ubuntu/cuenteria/src')

from llm_client import LLMClient

def test_simple():
    print("="*70)
    print("🧪 TEST SIMPLE DEL CUENTACUENTOS")
    print("="*70)
    
    # Cliente LLM - usar el singleton configurado
    from llm_client import get_llm_client
    client = get_llm_client()
    client.timeout = 120  # Timeout más corto para prueba rápida
    
    # Prompt mínimo del sistema
    system_prompt = """Eres un cuentacuentos. Genera un cuento de 10 páginas en verso.
Cada página debe tener exactamente 4 versos.
Devuelve un JSON con este formato exacto:
{
  "paginas_texto": {
    "1": "verso1\\nverso2\\nverso3\\nverso4",
    "2": "verso1\\nverso2\\nverso3\\nverso4",
    ...hasta página 10
  },
  "leitmotiv_usado_en": [2, 5, 10]
}"""

    # Prompt mínimo del usuario
    user_prompt = """Crea un cuento sobre Emilia y un pastel de cumpleaños.
El leitmotiv es: "¡Tic, tac, la canción del pastel!"
Usa el leitmotiv en páginas 2, 5 y 10.
Devuelve SOLO el JSON, sin explicaciones."""

    print(f"\n📊 Tamaños:")
    print(f"   System: {len(system_prompt)} chars")
    print(f"   User: {len(user_prompt)} chars")
    print(f"   Total: {len(system_prompt) + len(user_prompt)} chars")
    
    # Probar diferentes configuraciones
    configs = [
        (2000, 0.7),   # Mínimo
        (4000, 0.7),   # Estándar
        (6000, 0.7),   # Aumentado
        (8000, 0.7),   # Alto
    ]
    
    for max_tokens, temp in configs:
        print(f"\n🔧 Probando max_tokens={max_tokens}, temp={temp}")
        
        try:
            start = time.time()
            result = client.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=temp,
                max_tokens=max_tokens
            )
            elapsed = time.time() - start
            
            print(f"✅ ÉXITO en {elapsed:.1f}s")
            
            # Verificar resultado
            if isinstance(result, str):
                try:
                    result = json.loads(result)
                except:
                    print(f"   ⚠️ Respuesta no es JSON válido")
                    print(f"   Primeros 200 chars: {result[:200]}")
                    continue
            
            if 'paginas_texto' in result:
                num_paginas = len(result['paginas_texto'])
                print(f"   ✓ {num_paginas} páginas generadas")
                
                # Verificar primera página
                if '1' in result['paginas_texto']:
                    p1 = result['paginas_texto']['1']
                    versos = p1.count('\\n') + 1
                    print(f"   ✓ Página 1 tiene {versos} versos")
                    print(f"   Muestra: {p1[:50]}...")
            else:
                print(f"   ⚠️ No tiene campo 'paginas_texto'")
                print(f"   Claves: {list(result.keys())}")
            
            # Guardar el exitoso
            with open(f'cuentacuentos_exitoso_{max_tokens}.json', 'w') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"   💾 Guardado en cuentacuentos_exitoso_{max_tokens}.json")
            
            return True
            
        except ValueError as ve:
            elapsed = time.time() - start
            print(f"❌ FALLO en {elapsed:.1f}s: {ve}")
            if "no generó contenido" in str(ve):
                print(f"   → El modelo devolvió vacío con {max_tokens} tokens")
        except Exception as e:
            print(f"❌ ERROR: {e}")
    
    return False

if __name__ == "__main__":
    success = test_simple()
    if not success:
        print("\n⚠️ Todas las configuraciones fallaron")
        print("El modelo no puede generar el contenido requerido")
    else:
        print("\n✨ Al menos una configuración funcionó")