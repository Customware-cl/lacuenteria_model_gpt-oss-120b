#!/usr/bin/env python3
"""
Test del adaptador de brief con el JSON propuesto
"""

import json
import sys
sys.path.append('src')

from brief_adapter import adapt_brief, validate_adapted_brief

# Tu JSON original
brief_original = {
    "edad_objetivo": "2-6 años",
    "personajes": [
        {
            "nombre": "Caty",
            "rol": "madre",
            "relacion": "madre de Emilia"
        },
        {
            "nombre": "Emilia",
            "rol": "hija",
            "relacion": "hija de Caty"
        }
    ],
    "historia": "El día en que Emilia y Caty viajan al centro de un volcán lleno de lava, humo y una cueva llena de dinosaurios vivos",
    "mensaje_a_transmitir": {
        "valores_y_desarrollo_emocional": [
            "Desarrollar habilidades de comunicación asertiva"
        ],
        "comportamientos_a_reforzar": [
            "Dejar el pañal", 
            "Pedir ayuda cuando lo necesite"
        ]
    }
}

print("Brief original:")
print(json.dumps(brief_original, indent=2, ensure_ascii=False))
print("\n" + "="*50 + "\n")

# Adaptar
brief_adaptado = adapt_brief(brief_original)

print("Brief adaptado para el pipeline:")
print(json.dumps(brief_adaptado, indent=2, ensure_ascii=False))
print("\n" + "="*50 + "\n")

# Validar
es_valido, mensaje = validate_adapted_brief(brief_adaptado)
print(f"¿Es válido? {es_valido}")
print(f"Mensaje: {mensaje}")

# Probar con brief ya correcto
print("\n" + "="*50 + "\n")
print("Probando con brief que ya tiene formato correcto:")

brief_correcto = {
    "edad_objetivo": 4,
    "personajes": ["Caty", "Emilia"],
    "historia": "Una aventura en el volcán",
    "mensaje_a_transmitir": "Aprender a pedir ayuda"
}

brief_adaptado2 = adapt_brief(brief_correcto)
print("Brief adaptado (debería ser idéntico):")
print(json.dumps(brief_adaptado2, indent=2, ensure_ascii=False))

es_valido2, mensaje2 = validate_adapted_brief(brief_adaptado2)
print(f"¿Es válido? {es_valido2}")
print(f"Mensaje: {mensaje2}")