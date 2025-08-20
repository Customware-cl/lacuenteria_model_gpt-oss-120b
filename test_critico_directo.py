#!/usr/bin/env python3
"""
Script de prueba directa del crítico sin pasar por AgentRunner
"""

import json
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from llm_client import get_llm_client
from config import get_artifact_path, get_story_path
from datetime import datetime

def evaluar_directo(json_path):
    """
    Evalúa directamente un archivo JSON usando el LLM
    """
    print(f"🔍 Evaluando archivo: {json_path}")
    
    # Cargar el archivo a evaluar
    with open(json_path, 'r', encoding='utf-8') as f:
        contenido = json.load(f)
    
    # Cargar el prompt del crítico
    with open('agentes/critico.json', 'r', encoding='utf-8') as f:
        agente = json.load(f)
    
    # Preparar el prompt
    system_prompt = agente["content"]
    user_prompt = json.dumps(contenido, ensure_ascii=False, indent=2)
    
    print("📤 Enviando al modelo GPT-OSS...")
    print(f"Longitud del prompt: {len(user_prompt)} caracteres")
    
    # Llamar al LLM
    llm_client = get_llm_client()
    
    try:
        respuesta = llm_client.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.7,
            max_tokens=3000
        )
        
        print("\n📥 Respuesta recibida del modelo:")
        print("-" * 60)
        print(respuesta[:500] + "..." if len(respuesta) > 500 else respuesta)
        print("-" * 60)
        
        # Intentar parsear como JSON (o usar directamente si ya es dict)
        try:
            if isinstance(respuesta, dict):
                resultado = respuesta
                print("\n✅ Respuesta ya es un diccionario")
            else:
                resultado = json.loads(respuesta)
                print("\n✅ JSON parseado correctamente")
            
            # Guardar resultado
            output_file = f"critico_resultado_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(resultado, f, ensure_ascii=False, indent=2)
            print(f"💾 Resultado guardado en: {output_file}")
            
            # Mostrar resumen
            if "evaluacion_critica" in resultado:
                ec = resultado["evaluacion_critica"]
                if "nota_general" in ec:
                    ng = ec["nota_general"]
                    print(f"\n📊 EVALUACIÓN:")
                    print(f"  Puntuación: {ng.get('puntuacion', 'N/A')}/5.0")
                    print(f"  Nivel: {ng.get('nivel', 'N/A')}")
                    print(f"  Resumen: {ng.get('resumen', 'N/A')}")
            
            return resultado
            
        except json.JSONDecodeError as e:
            print(f"\n❌ Error parseando JSON: {e}")
            
            # Guardar respuesta cruda para debug
            debug_file = f"critico_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(respuesta)
            print(f"💾 Respuesta cruda guardada en: {debug_file}")
            
            return None
            
    except Exception as e:
        print(f"❌ Error llamando al modelo: {e}")
        return None

def main():
    if len(sys.argv) < 2:
        print("Uso: python test_critico_directo.py <archivo_json>")
        sys.exit(1)
    
    json_path = sys.argv[1]
    
    if not os.path.exists(json_path):
        print(f"❌ El archivo {json_path} no existe")
        sys.exit(1)
    
    resultado = evaluar_directo(json_path)
    
    if resultado:
        print("\n✨ Evaluación completada exitosamente")
    else:
        print("\n❌ La evaluación falló")
        sys.exit(1)

if __name__ == "__main__":
    main()