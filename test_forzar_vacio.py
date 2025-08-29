#!/usr/bin/env python3
"""
Test para forzar respuesta vacía del modelo y verificar que se detiene sin reintentos
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from llm_client import LLMClient
import json

def test_respuesta_vacia():
    """Test directo del cliente LLM con prompt que fuerza respuesta vacía"""
    
    print("=" * 70)
    print("🧪 TEST DE RESPUESTA VACÍA FORZADA")
    print("=" * 70)
    
    client = LLMClient()
    
    # Prompt diseñado para causar respuesta vacía o error
    system_prompt = "Solo responde con JSON válido"
    user_prompt = """
    INSTRUCCIÓN IMPOSIBLE: Genera un JSON con 1000000 campos únicos, 
    cada uno con una historia completa de 5000 palabras.
    Esto excede los límites del modelo y debería causar truncamiento o fallo.
    
    {
        "campo_1": "historia de 5000 palabras aquí...",
        "campo_2": "otra historia de 5000 palabras...",
        ... (continuar hasta 1000000 campos)
    }
    """
    
    print("\n📝 Enviando prompt diseñado para causar fallo...")
    print("🎯 Expectativa: Detención inmediata sin reintentos")
    
    try:
        response = client.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=8000,
            temperature=0.7
        )
        
        if response and response.get('content'):
            print(f"\n❌ El modelo generó contenido: {len(response['content'])} caracteres")
            print(f"Primeros 200 caracteres: {response['content'][:200]}")
        else:
            print("\n✅ Respuesta vacía detectada correctamente")
            
    except ValueError as e:
        if "STOP:" in str(e):
            print(f"\n✅ Sistema detenido correctamente: {e}")
            print("✅ NO se realizaron reintentos")
        else:
            print(f"\n❌ Error inesperado: {e}")
    except Exception as e:
        print(f"\n❌ Error no manejado: {e}")

if __name__ == "__main__":
    test_respuesta_vacia()