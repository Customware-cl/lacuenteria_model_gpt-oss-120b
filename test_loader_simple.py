#!/usr/bin/env python3
"""
Test simple del agente loader mejorado llamando directamente al LLM
"""

import json
import requests
import time

def test_loader_directo():
    """Prueba el prompt del loader directamente con el LLM"""
    
    # Leer el prompt del agente loader
    with open('flujo/v2/agentes/11_loader.json', 'r') as f:
        agent_config = json.load(f)
    
    # Datos de prueba
    test_context = {
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
    
    # Construir el mensaje del usuario con el contexto
    user_message = f"""
Contexto del cuento que se está generando:
- Título: {test_context['titulo']}
- Personajes: {', '.join(test_context['personajes'])}
- Mensaje a transmitir: {test_context['mensaje_a_transmitir']}
- Elementos visuales: colores mágicos y atmosfera de aventura

Genera los 10 mensajes de loader para mostrar mientras se crean las ilustraciones.
"""
    
    # Configurar la llamada al LLM
    url = "http://69.19.136.204:8000/v1/chat/completions"
    headers = {"Content-Type": "application/json"}
    payload = {
        "model": "openai/gpt-oss-120b",
        "messages": [
            {"role": "system", "content": agent_config["content"]},
            {"role": "user", "content": user_message}
        ],
        "temperature": 0.8,
        "max_tokens": 2000
    }
    
    print("🎨 Probando agente loader mejorado...")
    print(f"📖 Título: {test_context['titulo']}")
    print(f"👥 Personajes: {', '.join(test_context['personajes'])}")
    print(f"💫 Mensaje: {test_context['mensaje_a_transmitir']}")
    print("\n" + "="*60 + "\n")
    print("⏳ Llamando al LLM...")
    
    try:
        start_time = time.time()
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0]['message'].get('content')
            else:
                content = None
            print(f"✅ Respuesta recibida en {elapsed:.1f}s\n")
            
            if not content:
                print("❌ No se recibió contenido en la respuesta")
                print(f"Respuesta completa: {json.dumps(result, indent=2)}")
                return
            
            # Parsear el JSON
            try:
                output = json.loads(content)
                if "loader" in output:
                    print("✨ MENSAJES GENERADOS:\n")
                    for i, mensaje in enumerate(output["loader"], 1):
                        print(f"{i:2}. {mensaje}")
                    
                    print("\n" + "="*60 + "\n")
                    print("📊 ANÁLISIS:")
                    print(f"Total de mensajes: {len(output['loader'])}")
                    
                    # Verificar términos prohibidos
                    terminos = ["leitmotiv", "objeto ancla", "character bible", 
                               "pipeline", "render", "página", "#", "loader", 
                               "generando", "procesando", "cargando"]
                    problemas = []
                    
                    for i, msg in enumerate(output["loader"], 1):
                        msg_lower = msg.lower()
                        for term in terminos:
                            if term.lower() in msg_lower:
                                problemas.append(f"   Mensaje {i}: contiene '{term}'")
                    
                    if problemas:
                        print("\n⚠️  PROBLEMAS DETECTADOS:")
                        for p in problemas:
                            print(p)
                    else:
                        print("✅ No se detectaron términos técnicos prohibidos")
                    
                    # Verificar longitud
                    largos = [(i, len(msg)) for i, msg in enumerate(output["loader"], 1) 
                             if len(msg) > 65]
                    if largos:
                        print(f"\n⚠️  Mensajes que exceden 65 caracteres:")
                        for i, length in largos:
                            print(f"   Mensaje {i}: {length} caracteres")
                    else:
                        print("✅ Todos los mensajes ≤ 65 caracteres")
                    
                    # Verificar menciones de personajes
                    con_personajes = sum(1 for msg in output["loader"] 
                                       if any(p in msg for p in test_context["personajes"]))
                    print(f"👥 Personajes mencionados: {con_personajes}/10 mensajes")
                    
                    # Verificar variedad (palabras repetidas)
                    todas_palabras = ' '.join(output["loader"]).lower().split()
                    palabras_clave = [p for p in todas_palabras 
                                    if len(p) > 4 and p not in ['para', 'está', 'como', 'cuando']]
                    repetidas = {p: palabras_clave.count(p) for p in set(palabras_clave) 
                               if palabras_clave.count(p) > 2}
                    if repetidas:
                        print(f"\n⚠️  Palabras muy repetidas: {repetidas}")
                    
                else:
                    print("❌ No se encontró el campo 'loader'")
                    print(f"Respuesta: {content}")
                    
            except json.JSONDecodeError as e:
                print(f"❌ Error parseando JSON: {e}")
                print(f"Respuesta raw: {content}")
                
        else:
            print(f"❌ Error HTTP {response.status_code}")
            print(response.text)
            
    except requests.exceptions.Timeout:
        print("❌ Timeout en la llamada al LLM")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_loader_directo()