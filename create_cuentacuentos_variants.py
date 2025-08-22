#!/usr/bin/env python3
"""
Script para crear variantes del prompt de cuentacuentos
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.prompt_version_manager import get_prompt_manager

def create_cuentacuentos_variants():
    """Crea variantes optimizadas para cuentacuentos"""
    
    manager = get_prompt_manager()
    agent_name = "cuentacuentos"
    
    print(f"📝 Creando variantes para {agent_name}")
    print("=" * 50)
    
    # Variante 1: Anti-repetición explícita
    print("\n1️⃣ Creando variante: anti_repetition")
    manager.create_variant(
        agent_name=agent_name,
        variant_name="anti_repetition",
        modifications={
            "append": """
REGLAS ANTI-REPETICIÓN:
• NO uses la misma palabra más de 3 veces en todo el cuento
• Usa SINÓNIMOS variados (brilla → resplandece, ilumina, destella)
• Evita repetir el leitmotiv más de 3 veces total
• Cada página debe tener vocabulario único
• Penalización: -1 punto QA por cada repetición excesiva

VOCABULARIO VARIADO SUGERIDO:
- Para "luz": brillo, destello, fulgor, resplandor, claridad
- Para "magia": encanto, hechizo, sortilegio, milagro
- Para "baila": danza, gira, se mueve, flota
- Para "brilla": ilumina, destella, resplandece, reluce"""
        }
    )
    
    # Variante 2: Estructura métrica estricta
    print("2️⃣ Creando variante: structured_metrics")
    manager.create_variant(
        agent_name=agent_name,
        variant_name="structured_metrics",
        modifications={
            "prepend": """ESTRUCTURA MÉTRICA OBLIGATORIA:
Cada página = 4 versos de 8-10 sílabas
Esquema de rima: ABAB o ABCB
NO forzar rimas idénticas (amor/amor)
Ritmo constante: acentos en sílabas 3, 6, 9""",
            "replace": {
                "ritmo envolvente": "ritmo CONSISTENTE de 8-10 sílabas por verso",
                "musicalidad": "métrica regular sin forzar rimas"
            }
        }
    )
    
    # Variante 3: Ejemplos de versos bien construidos
    print("3️⃣ Creando variante: with_verse_examples")
    manager.create_variant(
        agent_name=agent_name,
        variant_name="with_verse_examples",
        modifications={
            "append": """
EJEMPLOS DE VERSOS BIEN CONSTRUIDOS:
✅ "El unicornio blanco camina despacio" (11 sílabas, imagen clara)
✅ "Sus ojos como estrellas en la noche" (11 sílabas, metáfora simple)
✅ "Emilia extiende su mano pequeñita" (11 sílabas, acción concreta)
✅ "Y juntos forman luz donde hay sombras" (10 sílabas, transformación)

EVITAR:
❌ "Brilla brilla luz de amistad brilla" (repetitivo)
❌ "El unicornio mágico es mágico" (redundante)
❌ "Destella resplandece ilumina brilla" (exceso de sinónimos)"""
        }
    )
    
    # Variante 4: Narrativa fluida
    print("4️⃣ Creando variante: narrative_flow")
    manager.create_variant(
        agent_name=agent_name,
        variant_name="narrative_flow",
        modifications={
            "replace": {
                "emoción in crescendo": "progresión narrativa clara: inicio→desarrollo→clímax→resolución",
                "leitmotiv": "estribillo (usar máximo 3 veces, en páginas 1, 5 y 10)"
            },
            "append": """
FLUIDEZ NARRATIVA:
• Página 1-3: Presentación (tono suave)
• Página 4-6: Desarrollo (aumenta tensión)
• Página 7-8: Clímax (máxima emoción)
• Página 9-10: Resolución (calma y cierre)

CONECTORES ENTRE PÁGINAS:
- Usar "Entonces...", "De pronto...", "Mientras tanto..."
- Cada página debe fluir naturalmente a la siguiente
- No cortes abruptos en la narrativa"""
        }
    )
    
    print("\n" + "=" * 50)
    print("✅ Variantes creadas exitosamente")
    
    # Listar variantes
    variants = manager.list_variants(agent_name)
    print("\n📋 Variantes disponibles para cuentacuentos:")
    for v in variants:
        print(f"  • {v['name']}: {v['file']}")
    
    return variants

if __name__ == "__main__":
    create_cuentacuentos_variants()