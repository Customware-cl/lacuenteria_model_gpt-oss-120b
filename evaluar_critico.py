#!/usr/bin/env python3
"""
Script para ejecutar el agente crítico sobre archivos JSON de validación
"""

import json
import sys
import argparse
from pathlib import Path
from datetime import datetime
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from llm_client import get_llm_client
from agent_runner import AgentRunner

def evaluar_con_critico(json_path: str, story_id: str = None) -> dict:
    """
    Evalúa un archivo JSON usando el agente crítico
    
    Args:
        json_path: Ruta al archivo JSON a evaluar
        story_id: ID opcional de la historia
        
    Returns:
        Diccionario con la evaluación
    """
    # Si no se proporciona story_id, usar timestamp
    if not story_id:
        story_id = f"eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Crear directorio temporal para la evaluación
    from config import get_story_path, get_artifact_path
    story_path = get_story_path(story_id)
    story_path.mkdir(parents=True, exist_ok=True)
    
    # Copiar el archivo a evaluar como si fuera el validador
    import shutil
    validador_path = get_artifact_path(story_id, "12_validador.json")
    shutil.copy(json_path, validador_path)
    
    # Inicializar el runner
    runner = AgentRunner(story_id)
    
    # Ejecutar el agente crítico
    print(f"🔍 Evaluando archivo: {json_path}")
    print("⏳ Ejecutando análisis crítico...")
    
    result = runner.run_agent("critico")
    
    if result["status"] == "success":
        # Leer el archivo de salida del crítico
        critico_path = get_artifact_path(story_id, "13_critico.json")
        if critico_path.exists():
            with open(critico_path, 'r', encoding='utf-8') as f:
                evaluacion = json.load(f)
            return evaluacion
        else:
            print("❌ No se encontró archivo de salida del crítico")
            return None
    else:
        print(f"❌ Error en la evaluación: {result.get('error', 'Error desconocido')}")
        # Si hay QA scores, mostrarlos
        if "qa_scores" in result:
            print("\n📊 Puntuaciones QA obtenidas:")
            for key, value in result["qa_scores"].items():
                print(f"  - {key}: {value}")
        return None

def generar_reporte_markdown(evaluacion: dict, output_path: str = None) -> str:
    """
    Genera un reporte en formato Markdown de la evaluación
    
    Args:
        evaluacion: Diccionario con la evaluación del crítico
        output_path: Ruta opcional para guardar el reporte
        
    Returns:
        String con el reporte en Markdown
    """
    reporte = []
    
    # Encabezado
    reporte.append("# 📊 Reporte de Evaluación Crítica\n")
    reporte.append(f"**Fecha:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Obtener datos de evaluación
    ed = evaluacion.get("evaluacion_detallada", {})
    qa = evaluacion.get("qa", {})
    
    # Evaluación global
    reporte.append("## 🎯 Evaluación Global\n")
    if ed:
        reporte.append(f"- **Puntuación Total:** {ed.get('puntuacion_global', qa.get('promedio', 0))}/5.0")
        reporte.append(f"- **Veredicto:** {ed.get('veredicto', 'N/A')}")
        reporte.append(f"- **Resumen:** {ed.get('resumen', 'N/A')}\n")
    elif qa:
        reporte.append(f"- **Puntuación Promedio:** {qa.get('promedio', 0)}/5.0\n")
    
    # Puntuaciones QA detalladas
    if qa:
        reporte.append("## 📈 Puntuaciones Detalladas\n")
        
        # Prompts de imágenes
        reporte.append("### 🎨 Prompts de Imágenes")
        reporte.append(f"- Claridad descriptiva: {qa.get('prompts_claridad', 0)}/5.0")
        reporte.append(f"- Consistencia: {qa.get('prompts_consistencia', 0)}/5.0")
        reporte.append(f"- Nivel de detalle: {qa.get('prompts_detalle', 0)}/5.0")
        reporte.append(f"- Adecuación infantil: {qa.get('prompts_adecuacion', 0)}/5.0")
        reporte.append(f"- Variedad visual: {qa.get('prompts_variedad', 0)}/5.0")
        reporte.append(f"- Técnica narrativa: {qa.get('prompts_tecnica', 0)}/5.0\n")
        
        # Loaders
        reporte.append("### 💬 Mensajes de Carga (Loaders)")
        reporte.append(f"- Originalidad: {qa.get('loaders_originalidad', 0)}/5.0")
        reporte.append(f"- Brevedad: {qa.get('loaders_brevedad', 0)}/5.0")
        reporte.append(f"- Conexión narrativa: {qa.get('loaders_conexion', 0)}/5.0")
        reporte.append(f"- Emoción: {qa.get('loaders_emocion', 0)}/5.0")
        reporte.append(f"- Lenguaje infantil: {qa.get('loaders_lenguaje', 0)}/5.0\n")
        
        # Texto del cuento
        reporte.append("### 📖 Texto del Cuento")
        reporte.append("**Estructura poética:**")
        reporte.append(f"- Número de versos: {qa.get('texto_versos', 0)}/5.0")
        reporte.append(f"- Longitud de versos: {qa.get('texto_longitud', 0)}/5.0")
        reporte.append(f"- Rima: {qa.get('texto_rima', 0)}/5.0")
        reporte.append(f"- Ritmo: {qa.get('texto_ritmo', 0)}/5.0")
        reporte.append("\n**Contenido narrativo:**")
        reporte.append(f"- Coherencia: {qa.get('texto_coherencia', 0)}/5.0")
        reporte.append(f"- Progresión emocional: {qa.get('texto_progresion', 0)}/5.0")
        reporte.append(f"- Lenguaje apropiado: {qa.get('texto_lenguaje', 0)}/5.0")
        reporte.append(f"- Valores positivos: {qa.get('texto_valores', 0)}/5.0")
        reporte.append(f"- Creatividad: {qa.get('texto_creatividad', 0)}/5.0\n")
    
    # Problemas identificados
    if ed:
        if ed.get("problemas_criticos"):
            reporte.append("## ⚠️ Problemas Críticos Identificados\n")
            for problema in ed["problemas_criticos"]:
                reporte.append(f"- {problema}")
            reporte.append("")
        
        if ed.get("paginas_problematicas"):
            reporte.append("## 📄 Páginas Problemáticas\n")
            reporte.append(f"Páginas que requieren revisión: {', '.join(map(str, ed['paginas_problematicas']))}\n")
        
        if ed.get("versos_sin_rima"):
            reporte.append("## 🔴 Versos Sin Rima Adecuada\n")
            for verso in ed["versos_sin_rima"][:5]:  # Limitar a 5 ejemplos
                reporte.append(f"- \"{verso}\"")
            reporte.append("")
        
        if ed.get("palabras_inadecuadas"):
            reporte.append("## 📝 Palabras Inadecuadas o Complejas\n")
            for palabra in ed["palabras_inadecuadas"]:
                reporte.append(f"- {palabra}")
            reporte.append("")
        
        if ed.get("loaders_problematicos"):
            reporte.append("## 💭 Loaders Problemáticos\n")
            reporte.append(f"Índices: {', '.join(map(str, ed['loaders_problematicos']))}\n")
        
        # Recomendaciones
        if ed.get("recomendaciones"):
            reporte.append("## 💡 Recomendaciones Prioritarias\n")
            for rec in ed["recomendaciones"]:
                reporte.append(f"{rec}")
            reporte.append("")
        
        # Decisión final
        reporte.append("## ✅ Decisión Final\n")
        reporte.append(f"- **Apto para publicación:** {'✅ Sí' if ed.get('apto_publicacion') else '❌ No'}")
        reporte.append(f"- **Nivel de revisión requerido:** {ed.get('nivel_revision', 'N/A')}")
    
    # Unir todo el reporte
    reporte_final = "\n".join(reporte)
    
    # Guardar si se especificó ruta
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(reporte_final)
        print(f"📝 Reporte guardado en: {output_path}")
    
    return reporte_final

def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description="Evaluador crítico de cuentos")
    parser.add_argument("archivo", help="Ruta al archivo JSON a evaluar")
    parser.add_argument("--story-id", help="ID de la historia (opcional)")
    parser.add_argument("--output-md", help="Ruta para guardar reporte en Markdown")
    parser.add_argument("--output-json", help="Ruta para guardar evaluación en JSON")
    parser.add_argument("--show-markdown", action="store_true", help="Mostrar reporte en Markdown")
    
    args = parser.parse_args()
    
    # Verificar que el archivo existe
    if not Path(args.archivo).exists():
        print(f"❌ Error: El archivo {args.archivo} no existe")
        return 1
    
    # Ejecutar evaluación
    evaluacion = evaluar_con_critico(args.archivo, args.story_id)
    
    if evaluacion:
        # Mostrar puntuación global
        print(f"\n✨ Evaluación completada")
        
        qa = evaluacion.get("qa", {})
        ed = evaluacion.get("evaluacion_detallada", {})
        
        if qa:
            print(f"📊 Puntuación promedio QA: {qa.get('promedio', 0)}/5.0")
        if ed:
            print(f"🎯 Veredicto: {ed.get('veredicto', 'N/A')}")
        
        # Guardar JSON si se especificó
        if args.output_json:
            with open(args.output_json, 'w', encoding='utf-8') as f:
                json.dump(evaluacion, f, ensure_ascii=False, indent=2)
            print(f"💾 Evaluación JSON guardada en: {args.output_json}")
        
        # Generar reporte Markdown
        output_md = args.output_md or args.archivo.replace('.json', '_evaluacion_critica.md')
        reporte = generar_reporte_markdown(evaluacion, output_md)
        
        # Mostrar reporte si se solicitó
        if args.show_markdown:
            print("\n" + "="*60)
            print(reporte)
            print("="*60)
        
        # Decisión final
        if ed:
            if ed.get("apto_publicacion"):
                print("\n✅ El cuento está APTO para publicación")
            else:
                print(f"\n⚠️ El cuento REQUIERE REVISIÓN - Nivel: {ed.get('nivel_revision', 'N/A')}")
        
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())