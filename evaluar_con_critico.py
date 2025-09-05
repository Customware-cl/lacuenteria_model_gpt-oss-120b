#!/usr/bin/env python3
"""
Script para evaluar una historia v3 con el agente crítico v2
"""

import json
import requests
import sys
from pathlib import Path

def cargar_historia_v3(story_id):
    """Carga la historia generada por v3"""
    # Buscar la carpeta
    import glob
    pattern = f"runs/*{story_id}*"
    folders = glob.glob(pattern)
    
    if not folders:
        print(f"❌ No se encontró carpeta para {story_id}")
        return None
    
    folder = Path(folders[0])
    
    # Cargar el consolidador v3
    consolidador_path = folder / "04_consolidador_v3.json"
    if not consolidador_path.exists():
        print(f"❌ No se encontró archivo consolidador")
        return None
    
    with open(consolidador_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def evaluar_con_critico(historia_data):
    """Ejecuta el agente crítico v2 sobre la historia"""
    
    print("🔍 Ejecutando evaluación crítica v2...")
    
    # Preparar el payload para el crítico
    # El crítico espera el formato del validador v2
    payload = {
        "titulo": historia_data.get("titulo", "Sin título"),
        "paginas": historia_data.get("paginas", {}),
        "portada": historia_data.get("portada", {}),
        "loader": historia_data.get("loader", [])
    }
    
    # Llamar al endpoint de evaluación con el story_id
    # Usamos un ID ficticio y enviamos los datos como historia externa
    url = f"http://localhost:5000/api/stories/external-v3-test/evaluate"
    
    try:
        response = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=120
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error ejecutando crítico: {e}")
        return None

def mostrar_resultados(evaluacion):
    """Muestra los resultados de la evaluación"""
    
    print("\n" + "="*60)
    print("📊 EVALUACIÓN CRÍTICA - RESULTADOS")
    print("="*60)
    
    if not evaluacion:
        print("❌ No se pudo obtener evaluación")
        return
    
    # Verificar estructura de la respuesta
    if "evaluacion" in evaluacion:
        eval_data = evaluacion["evaluacion"]
    else:
        eval_data = evaluacion
    
    # Mostrar puntuaciones
    print("\n🎯 PUNTUACIONES:")
    if "puntuaciones" in eval_data:
        puntuaciones = eval_data["puntuaciones"]
        for categoria, valor in puntuaciones.items():
            emoji = "✅" if valor >= 4 else "⚠️" if valor >= 3 else "❌"
            print(f"  {emoji} {categoria}: {valor}/5")
        
        # Promedio
        if puntuaciones:
            promedio = sum(puntuaciones.values()) / len(puntuaciones)
            emoji = "✅" if promedio >= 4 else "⚠️" if promedio >= 3 else "❌"
            print(f"\n  {emoji} PROMEDIO GENERAL: {promedio:.2f}/5")
    
    # Mostrar fortalezas
    print("\n💪 FORTALEZAS:")
    if "fortalezas" in eval_data:
        for fortaleza in eval_data["fortalezas"]:
            print(f"  ✓ {fortaleza}")
    
    # Mostrar debilidades
    print("\n⚠️ ÁREAS DE MEJORA:")
    if "debilidades" in eval_data:
        for debilidad in eval_data["debilidades"]:
            print(f"  • {debilidad}")
    
    # Recomendaciones
    if "recomendaciones_especificas" in eval_data:
        print("\n💡 RECOMENDACIONES:")
        for rec in eval_data["recomendaciones_especificas"]:
            print(f"  → {rec}")
    
    # Veredicto final
    if "veredicto_final" in eval_data:
        veredicto = eval_data["veredicto_final"]
        print(f"\n📝 VEREDICTO FINAL:")
        print(f"  Calidad: {veredicto.get('calidad_general', 'N/A')}")
        print(f"  Listo para producción: {veredicto.get('listo_para_produccion', 'N/A')}")
        if "justificacion" in veredicto:
            print(f"  Justificación: {veredicto['justificacion']}")

def main():
    # Story ID de la prueba v3
    story_id = "0cacfeef-9b8b-4203-9899-efd5828b1481"
    
    print(f"📚 Evaluando historia: {story_id}")
    
    # Cargar historia
    historia = cargar_historia_v3(story_id)
    if not historia:
        return
    
    print(f"✅ Historia cargada: {historia.get('titulo', 'Sin título')}")
    print(f"📄 Páginas: {len(historia.get('paginas', {}))}")
    
    # Evaluar con crítico
    evaluacion = evaluar_con_critico(historia)
    
    # Mostrar resultados
    if evaluacion:
        mostrar_resultados(evaluacion)
        
        # Guardar evaluación
        output_file = f"runs/20250905-020901-{story_id}/13_critico_evaluation.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(evaluacion, f, ensure_ascii=False, indent=2)
        print(f"\n💾 Evaluación guardada en: {output_file}")
    else:
        print("❌ No se pudo completar la evaluación")

if __name__ == "__main__":
    main()