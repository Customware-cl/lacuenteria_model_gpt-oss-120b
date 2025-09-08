#!/usr/bin/env python3
"""
Test del agente loader mejorado con mensajes más inmersivos
"""

import json
import sys
import os

# Agregar el directorio src al path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from agent_runner import AgentRunner
from config import Config

def test_loader_mejorado():
    """Prueba el agente loader con un ejemplo simple"""
    
    # Configuración
    config = Config()
    runner = AgentRunner(config)
    
    # Datos de prueba simulando lo que recibiría el loader
    test_data = {
        "titulo": "La aventura mágica de Luna",
        "personajes": ["Luna", "Estrellita", "El dragón amigable"],
        "mensaje_a_transmitir": "La valentía viene del corazón",
        "character_bible": {
            "objetos_ancla": ["varita mágica", "collar de estrellas"],
            "colores": ["azul nocturno", "dorado"],
            "gestos": ["sonrisa tímida", "abrazo cálido"]
        },
        "guia_de_arte": {
            "color_script": "Atardecer mágico con tonos dorados y púrpuras"
        }
    }
    
    # Crear contexto para el agente
    context = {
        "titulo": test_data["titulo"],
        "personajes": test_data["personajes"],
        "mensaje_a_transmitir": test_data["mensaje_a_transmitir"],
        "character_bible": test_data["character_bible"],
        "guia_de_arte": test_data["guia_de_arte"]
    }
    
    print("🎨 Probando agente loader mejorado...")
    print(f"📖 Título: {test_data['titulo']}")
    print(f"👥 Personajes: {', '.join(test_data['personajes'])}")
    print(f"💫 Mensaje: {test_data['mensaje_a_transmitir']}")
    print("\n" + "="*60 + "\n")
    
    # Ejecutar el agente loader
    try:
        result = runner.run_agent_v2("11_loader", context)
        
        if result and "output" in result:
            output = json.loads(result["output"]) if isinstance(result["output"], str) else result["output"]
            
            if "loader" in output:
                print("✨ MENSAJES GENERADOS:\n")
                for i, mensaje in enumerate(output["loader"], 1):
                    print(f"{i:2}. {mensaje}")
                
                print("\n" + "="*60 + "\n")
                print("📊 ANÁLISIS:")
                print(f"Total de mensajes: {len(output['loader'])}")
                
                # Verificar que no haya términos técnicos
                terminos_prohibidos = ["leitmotiv", "objeto ancla", "character bible", 
                                      "pipeline", "render", "página", "#"]
                mensajes_con_problemas = []
                
                for i, mensaje in enumerate(output["loader"], 1):
                    for termino in terminos_prohibidos:
                        if termino.lower() in mensaje.lower():
                            mensajes_con_problemas.append((i, mensaje, termino))
                
                if mensajes_con_problemas:
                    print("\n⚠️  PROBLEMAS DETECTADOS:")
                    for num, msg, term in mensajes_con_problemas:
                        print(f"   Mensaje {num}: Contiene '{term}'")
                else:
                    print("✅ No se detectaron términos técnicos prohibidos")
                
                # Verificar longitud
                mensajes_largos = [(i, msg) for i, msg in enumerate(output["loader"], 1) 
                                  if len(msg) > 65]
                if mensajes_largos:
                    print(f"\n⚠️  {len(mensajes_largos)} mensajes exceden 65 caracteres")
                else:
                    print("✅ Todos los mensajes tienen 65 caracteres o menos")
                
                # Verificar uso de personajes
                personajes_mencionados = sum(1 for msg in output["loader"] 
                                            if any(p in msg for p in test_data["personajes"]))
                print(f"✅ Personajes mencionados en {personajes_mencionados} mensajes")
                
            else:
                print("❌ Error: No se encontró el campo 'loader' en la respuesta")
                print(f"Respuesta recibida: {json.dumps(output, indent=2, ensure_ascii=False)}")
        else:
            print("❌ Error: No se recibió respuesta del agente")
            
    except Exception as e:
        print(f"❌ Error al ejecutar el agente: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_loader_mejorado()