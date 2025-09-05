#!/usr/bin/env python3
"""
Evalúa la historia recién generada con el crítico v2
"""

import json
import requests
from pathlib import Path

def main():
    # Cargar la historia correcta
    story_path = Path("/home/ubuntu/cuenteria/runs/20250905-030832-sofia-max-v3-mejorado-20250905030832/outputs/agents/04_consolidador_v3.json")
    
    if not story_path.exists():
        print("❌ No se encontró el archivo")
        return
    
    with open(story_path, "r", encoding="utf-8") as f:
        historia = json.load(f)
    
    print(f"📚 Evaluando: {historia.get('titulo', 'Sin título')}")
    print(f"📄 Páginas: {len(historia.get('paginas', {}))}")
    
    # Preparar payload
    payload = {
        "titulo": historia.get("titulo", "Sin título"),
        "paginas": historia.get("paginas", {}),
        "portada": historia.get("portada", {}),
        "loader": historia.get("loader", [])
    }
    
    # Llamar al crítico
    url = "http://localhost:5000/api/stories/new-story-v3/evaluate"
    
    response = requests.post(
        url,
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=120
    )
    
    if response.status_code == 200:
        evaluacion = response.json()
        
        # Extraer datos
        if "evaluacion_critica" in evaluacion:
            eval_data = evaluacion["evaluacion_critica"]
        else:
            eval_data = evaluacion
        
        print("\n" + "="*60)
        print("📊 EVALUACIÓN CRÍTICA V2 - HISTORIA MEJORADA")
        print("="*60)
        
        # Puntuación general
        if "nota_general" in eval_data:
            nota = eval_data["nota_general"]
            print(f"\n🎯 PUNTUACIÓN GENERAL: {nota.get('puntuacion', 'N/A')}/5")
            print(f"   Nivel: {nota.get('nivel', 'N/A')}")
            print(f"   Resumen: {nota.get('resumen', 'N/A')}")
        
        # Detalles por área
        if "notas_por_topico" in eval_data:
            print("\n📈 PUNTUACIONES POR ÁREA:")
            
            # Texto narrativo
            texto = eval_data["notas_por_topico"].get("texto_narrativo", {})
            if texto:
                print(f"\n📖 Texto Narrativo: {texto.get('puntuacion_promedio', 'N/A')}/5")
                
                # Estructura poética (crítica anterior: 2.5/5)
                poetica = texto.get("estructura_poetica", {})
                if poetica:
                    print(f"   🎵 Estructura Poética: {poetica.get('puntuacion_promedio', 'N/A')}/5")
                    if "notas_por_ambito" in poetica:
                        for ambito, nota in poetica["notas_por_ambito"].items():
                            print(f"      • {ambito}: {nota}/5")
            
            # Prompts de imágenes (crítica anterior: 4.0/5, variedad: 3.5/5)
            prompts = eval_data["notas_por_topico"].get("prompts_imagenes", {})
            if prompts:
                print(f"\n🎨 Prompts de Imágenes: {prompts.get('puntuacion_promedio', 'N/A')}/5")
                if "notas_por_ambito" in prompts:
                    print(f"   • Variedad visual: {prompts['notas_por_ambito'].get('variedad_visual', 'N/A')}/5")
            
            # Loaders (crítica anterior: 3.5/5)
            loaders = eval_data["notas_por_topico"].get("mensajes_carga", {})
            if loaders:
                print(f"\n⏳ Mensajes de Carga: {loaders.get('puntuacion_promedio', 'N/A')}/5")
        
        # Comparación con evaluación anterior
        print("\n" + "="*60)
        print("📊 COMPARACIÓN CON EVALUACIÓN ANTERIOR")
        print("="*60)
        
        nueva_puntuacion = eval_data.get("nota_general", {}).get("puntuacion", 0)
        print(f"\n📈 Puntuación anterior: 3.8/5")
        print(f"📈 Puntuación nueva: {nueva_puntuacion}/5")
        
        diferencia = nueva_puntuacion - 3.8
        if diferencia > 0:
            print(f"\n✅ MEJORA: +{diferencia:.1f} puntos")
        elif diferencia < 0:
            print(f"\n⚠️ DESCENSO: {diferencia:.1f} puntos")
        else:
            print(f"\n➖ SIN CAMBIOS")
        
        print("\n📝 CRÍTICAS ANTERIORES VS NUEVAS:")
        print("   • Estructura poética: 2.5/5 → ", end="")
        nueva_poetica = texto.get("estructura_poetica", {}).get("puntuacion_promedio", "N/A")
        print(f"{nueva_poetica}/5")
        
        print("   • Variedad visual: 3.5/5 → ", end="")
        nueva_variedad = prompts.get("notas_por_ambito", {}).get("variedad_visual", "N/A")
        print(f"{nueva_variedad}/5")
        
        print("   • Mensajes de carga: 3.5/5 → ", end="")
        nueva_loaders = loaders.get("puntuacion_promedio", "N/A")
        print(f"{nueva_loaders}/5")
        
        # Guardar evaluación
        output_file = Path("/home/ubuntu/cuenteria/runs/20250905-030832-sofia-max-v3-mejorado-20250905030832/13_critico_evaluation.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(evaluacion, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Evaluación guardada en: {output_file}")
        
    else:
        print(f"❌ Error: {response.status_code}")

if __name__ == "__main__":
    main()