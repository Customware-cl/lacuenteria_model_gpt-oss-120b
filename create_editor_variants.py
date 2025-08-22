#!/usr/bin/env python3
"""
Script para crear variantes del prompt de editor_claridad
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.prompt_version_manager import get_prompt_manager

def create_editor_claridad_variants():
    """Crea 4 variantes del prompt de editor_claridad para testing"""
    
    manager = get_prompt_manager()
    agent_name = "editor_claridad"
    
    print(f"📝 Creando variantes para {agent_name}")
    print("=" * 50)
    
    # Variante 1: Con ejemplos concretos
    print("\n1️⃣ Creando variante: with_examples")
    manager.create_variant(
        agent_name=agent_name,
        variant_name="with_examples",
        modifications={
            "append": """EJEMPLO DE SALIDA ESPERADA:
{
  "paginas_texto_claro": {
    "1": "Bajo el árbol grande suena el viento suave\\nLas hojas verdes bailan con alegría\\nEl sol dorado brilla entre las ramas\\nY todo el jardín canta su melodía",
    "2": "[TEXTO COMPLETO DE LA PÁGINA 2]",
    "3": "[CONTINUAR CON TODAS LAS PÁGINAS...]",
    "10": "[TEXTO COMPLETO DE LA PÁGINA 10]"
  },
  "glosario": [
    {"original": "destella", "simple": "brilla"},
    {"original": "penumbra", "simple": "sombra"}
  ],
  "cambios_clave": [
    "Simplificación de vocabulario complejo",
    "Clarificación de imágenes ambiguas"
  ],
  "qa": {"comprensibilidad": 5, "imagen_inequivoca": 5}
}

IMPORTANTE: INCLUIR TEXTO COMPLETO EN TODAS LAS 10 PÁGINAS."""
        }
    )
    
    # Variante 2: Con proceso estructurado paso a paso
    print("2️⃣ Creando variante: structured_process")
    manager.create_variant(
        agent_name=agent_name,
        variant_name="structured_process",
        modifications={
            "prepend": """PROCESO ESTRUCTURADO DE EDICIÓN:
1. LEER: Analiza cada página del texto original
2. IDENTIFICAR: Marca palabras complejas y ambigüedades
3. SIMPLIFICAR: Reemplaza con vocabulario de 5 años
4. VERIFICAR: Asegura una imagen clara por verso
5. VALIDAR: Confirma que cada página tiene texto completo

REGLA CRÍTICA: NO DEJAR NINGUNA PÁGINA VACÍA O INCOMPLETA.""",
            "replace": {
                "Tu objetivo:": "Tu misión CRÍTICA:",
                "Devuelve únicamente ese JSON.": "GENERA JSON COMPLETO CON LAS 10 PÁGINAS. NO TRUNCAR."
            }
        }
    )
    
    # Variante 3: Anti-truncamiento enfático
    print("3️⃣ Creando variante: anti_truncation")
    manager.create_variant(
        agent_name=agent_name,
        variant_name="anti_truncation",
        modifications={
            "append": """
INSTRUCCIONES ANTI-TRUNCAMIENTO:
⚠️ DEBES generar texto para TODAS las 10 páginas
⚠️ NUNCA dejes campos vacíos o con placeholder
⚠️ USA todos los tokens necesarios (tienes 8000 disponibles)
⚠️ Si una página queda vacía, el trabajo será RECHAZADO
⚠️ Completa TODO el JSON antes de terminar

VERIFICACIÓN FINAL:
✓ ¿Página 1 tiene texto? 
✓ ¿Página 2 tiene texto?
✓ ¿Página 3 tiene texto?
✓ ¿Página 4 tiene texto?
✓ ¿Página 5 tiene texto?
✓ ¿Página 6 tiene texto?
✓ ¿Página 7 tiene texto?
✓ ¿Página 8 tiene texto?
✓ ¿Página 9 tiene texto?
✓ ¿Página 10 tiene texto?

SI ALGUNA RESPUESTA ES NO, COMPLÉTALA ANTES DE TERMINAR."""
        }
    )
    
    # Variante 4: Con criterios de simplificación específicos
    print("4️⃣ Creando variante: detailed_criteria")
    manager.create_variant(
        agent_name=agent_name,
        variant_name="detailed_criteria",
        modifications={
            "replace": {
                "hacer el texto cristalino sin perder belleza": """hacer el texto PERFECTAMENTE CLARO para niños de 5 años, manteniendo la belleza poética.

CRITERIOS DE SIMPLIFICACIÓN:
• Vocabulario: Máximo nivel preescolar (5-6 años)
• Sintaxis: Oraciones simples, máximo 10 palabras
• Imágenes: Una acción concreta por verso
• Causalidad: Relaciones causa-efecto explícitas
• Temporalidad: Secuencia clara (primero, después, al final)

PALABRAS A EVITAR: destella, penumbra, resplandor, emanar, susurrar, vislumbrar
PREFERIR: brilla, sombra, luz, salir, hablar bajito, ver"""
            },
            "append": """
FORMATO ESTRICTO DEL JSON:
Cada página DEBE tener 4 versos de 8-10 sílabas.
Ninguna página puede quedar vacía.
El glosario debe tener al menos 5 entradas.
Los cambios_clave deben listar al menos 3 mejoras específicas."""
        }
    )
    
    print("\n" + "=" * 50)
    print("✅ Variantes creadas exitosamente")
    
    # Listar variantes
    print("\n📋 Variantes disponibles:")
    variants = manager.list_variants(agent_name)
    for v in variants:
        print(f"  • {v['name']}: {v['file']}")
    
    print("\n💡 Para probar una variante:")
    print(f"   python test_prompt_optimization.py --agent {agent_name} --variant with_examples")
    
    return variants

if __name__ == "__main__":
    create_editor_claridad_variants()