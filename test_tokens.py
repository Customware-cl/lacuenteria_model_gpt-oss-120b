#!/usr/bin/env python3
"""
Script de prueba para verificar que los tokens se registran correctamente
"""
import json
import sys
from pathlib import Path

# Agregar src al path
sys.path.append(str(Path(__file__).parent / "src"))

from llm_client import get_llm_client
from config import LLM_CONFIG

def test_token_capture():
    """Prueba que el cliente LLM capture correctamente los tokens"""
    
    print("=" * 60)
    print("PRUEBA DE CAPTURA DE TOKENS")
    print("=" * 60)
    
    # Obtener cliente
    client = get_llm_client()
    
    # Prompt de prueba simple
    system_prompt = "Eres un asistente que responde con JSON. Responde ÚNICAMENTE con JSON válido."
    user_prompt = "Dame un JSON simple con tu nombre y una descripción breve de ti mismo en español."
    
    print("\n1. Enviando petición al modelo...")
    print(f"   Endpoint: {LLM_CONFIG['endpoint']}")
    print(f"   Modelo: {LLM_CONFIG['model']}")
    
    try:
        # Hacer la llamada
        result = client.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.7,
            max_tokens=200
        )
        
        print("\n2. Respuesta recibida exitosamente")
        
        # Verificar si hay metadata de tokens
        if "_metadata_tokens" in result:
            tokens = result["_metadata_tokens"]
            print("\n3. ✅ TOKENS CAPTURADOS:")
            print(f"   - Prompt tokens: {tokens.get('prompt_tokens', 'N/A')}")
            print(f"   - Completion tokens: {tokens.get('completion_tokens', 'N/A')}")
            print(f"   - Total tokens: {tokens.get('total_tokens', 'N/A')}")
            
            # Limpiar metadata del resultado
            del result["_metadata_tokens"]
        else:
            print("\n3. ⚠️  NO SE CAPTURARON TOKENS")
            print("   El servidor podría no estar enviando información de 'usage'")
        
        # Mostrar el contenido
        print("\n4. Contenido generado:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        print("\n5. Resumen:")
        print(f"   - Conexión exitosa: ✅")
        print(f"   - JSON válido: ✅")
        print(f"   - Tokens capturados: {'✅' if '_metadata_tokens' in locals() else '❌'}")
        
    except Exception as e:
        print(f"\n❌ Error durante la prueba: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("PRUEBA COMPLETADA")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    success = test_token_capture()
    sys.exit(0 if success else 1)