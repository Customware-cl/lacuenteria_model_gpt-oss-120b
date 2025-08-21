#!/usr/bin/env python3
"""
Script de prueba para comparar autoevaluación vs verificador QA independiente.
Evalúa un agente existente con ambos métodos y muestra las diferencias.
"""
import json
import sys
import os
from pathlib import Path

sys.path.append('src')

from llm_client import get_llm_client
from config import AGENT_TEMPERATURES

def load_agent_output(story_id, agent_file):
    """Carga el output de un agente específico"""
    file_path = Path(f"runs/{story_id}/{agent_file}")
    if not file_path.exists():
        print(f"❌ No se encontró: {file_path}")
        return None
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_agent_prompt(agent_name):
    """Carga el prompt del sistema para un agente"""
    prompt_path = Path(f"agentes/{agent_name}.json")
    if not prompt_path.exists():
        print(f"❌ No se encontró prompt para: {agent_name}")
        return None
    
    with open(prompt_path, 'r', encoding='utf-8') as f:
        agent_config = json.load(f)
    
    return agent_config.get("content", "")

def run_verificador_qa(agent_name, agent_output):
    """Ejecuta el verificador QA independiente"""
    print(f"\n🔍 Ejecutando Verificador QA Independiente...")
    
    # Cargar prompt del verificador
    verificador_prompt = load_agent_prompt("verificador_qa")
    if not verificador_prompt:
        return None
    
    # Construir prompt de usuario
    user_prompt = f"""TAREA: Evaluar objetivamente el trabajo del siguiente agente
==================================================

AGENTE A EVALUAR: {agent_name}

OUTPUT DEL AGENTE A EVALUAR:
==================================================
{json.dumps(agent_output, ensure_ascii=False, indent=2)}

INSTRUCCIONES DE EVALUACIÓN:
==================================================
1. Analiza el output buscando problemas específicos
2. Aplica las penalizaciones automáticas según corresponda
3. Calcula el score para cada métrica del agente
4. Determina si pasa el umbral de 4.0
5. Genera feedback específico y accionable

RECUERDA:
- Sé CRÍTICO y OBJETIVO
- La mayoría de outputs deben estar en 3-3.5
- Un 5/5 es excepcional y requiere justificación
- Devuelve ÚNICAMENTE el JSON especificado"""
    
    # Llamar al LLM
    llm_client = get_llm_client()
    
    # Configurar timeout largo para evitar truncamiento
    original_timeout = llm_client.timeout
    llm_client.timeout = 900  # 900 segundos
    
    try:
        result = llm_client.generate(
            system_prompt=verificador_prompt,
            user_prompt=user_prompt,
            temperature=0.3,  # Baja para consistencia
            max_tokens=3000  # Aumentado para respuestas completas
        )
        
        # Restaurar timeout original
        llm_client.timeout = original_timeout
        
        # Si result ya es un dict, devolverlo directamente
        if isinstance(result, dict):
            return result
        
        # Si es string, parsearlo
        verification = json.loads(result)
        return verification
        
    except json.JSONDecodeError as e:
        print(f"⚠️ Error parseando JSON: {e}")
        print(f"Respuesta truncada o mal formada")
        # Intentar recuperar lo que se pueda
        try:
            # Buscar el promedio en la respuesta parcial
            if "promedio" in result:
                import re
                match = re.search(r'"promedio":\s*([\d.]+)', result)
                if match:
                    promedio = float(match.group(1))
                    print(f"Promedio recuperado: {promedio}")
                    return {"promedio": promedio, "pasa_umbral": promedio >= 4.0}
        except:
            pass
        return None
    except Exception as e:
        print(f"❌ Error ejecutando verificador: {e}")
        return None

def compare_evaluations(agent_name, agent_output):
    """Compara autoevaluación vs verificador independiente"""
    
    print("\n" + "=" * 60)
    print(f"COMPARACIÓN DE EVALUACIONES: {agent_name}")
    print("=" * 60)
    
    # 1. Autoevaluación (del propio agente)
    auto_qa = agent_output.get("qa", {})
    if auto_qa:
        print("\n📊 AUTOEVALUACIÓN (del propio agente):")
        print("-" * 40)
        for metric, score in auto_qa.items():
            if metric != "promedio":
                print(f"  • {metric}: {score}/5")
        
        # Calcular promedio
        scores = [v for k, v in auto_qa.items() if k != "promedio" and isinstance(v, (int, float))]
        if scores:
            auto_promedio = sum(scores) / len(scores)
            print(f"  📈 Promedio: {auto_promedio:.2f}/5")
        else:
            auto_promedio = 0
    else:
        print("\n⚠️ No hay autoevaluación disponible")
        auto_promedio = 0
    
    # 2. Verificador QA Independiente
    verification = run_verificador_qa(agent_name, agent_output)
    
    if verification:
        print("\n🔍 VERIFICADOR QA INDEPENDIENTE:")
        print("-" * 40)
        
        qa_scores = verification.get("qa_scores", {})
        for metric, score in qa_scores.items():
            if metric != "promedio":
                print(f"  • {metric}: {score}/5")
        
        print(f"  📈 Promedio: {verification.get('promedio', 0):.2f}/5")
        print(f"  ✅ Pasa umbral (4.0): {'SÍ' if verification.get('pasa_umbral', False) else 'NO'}")
        
        # Problemas detectados
        problemas = verification.get("problemas_detectados", [])
        if problemas:
            print(f"\n  🚨 Problemas Detectados ({len(problemas)}):")
            for i, problema in enumerate(problemas[:5], 1):  # Mostrar máx 5
                print(f"     {i}. {problema}")
        
        # Aspectos positivos
        positivos = verification.get("aspectos_positivos", [])
        if positivos:
            print(f"\n  ✨ Aspectos Positivos:")
            for positivo in positivos[:3]:  # Mostrar máx 3
                print(f"     • {positivo}")
        
        # Justificación
        if "justificacion_score" in verification:
            print(f"\n  📝 Justificación:")
            print(f"     {verification['justificacion_score']}")
        
        verificador_promedio = verification.get('promedio', 0)
    else:
        verificador_promedio = 0
    
    # 3. Comparación
    print("\n" + "=" * 60)
    print("📊 RESUMEN COMPARATIVO:")
    print("-" * 40)
    print(f"  Autoevaluación:        {auto_promedio:.2f}/5")
    print(f"  Verificador QA:        {verificador_promedio:.2f}/5")
    print(f"  Diferencia:            {abs(auto_promedio - verificador_promedio):.2f}")
    
    if auto_promedio > 0 and verificador_promedio > 0:
        inflacion = ((auto_promedio - verificador_promedio) / verificador_promedio) * 100
        if inflacion > 0:
            print(f"  Inflación detectada:   {inflacion:.1f}% 📈")
        else:
            print(f"  Deflación detectada:   {abs(inflacion):.1f}% 📉")
    
    print("=" * 60)

def main():
    """Función principal"""
    print("\n🧪 TEST DEL VERIFICADOR QA INDEPENDIENTE")
    print("=" * 60)
    
    # Historia y agente a probar
    story_id = "test-emilia-20250821-002844"
    
    # Probar varios agentes
    test_agents = [
        ("cuentacuentos", "03_cuentacuentos.json"),
        ("ritmo_rima", "05_ritmo_rima.json"),
        ("director", "01_director.json")
    ]
    
    for agent_name, agent_file in test_agents:
        print(f"\n\n{'='*60}")
        print(f"Probando: {agent_name}")
        print(f"{'='*60}")
        
        # Cargar output del agente
        agent_output = load_agent_output(story_id, agent_file)
        
        if agent_output:
            # Comparar evaluaciones
            compare_evaluations(agent_name, agent_output)
        else:
            print(f"❌ No se pudo cargar el output de {agent_name}")
    
    print("\n" + "=" * 60)
    print("✅ PRUEBAS COMPLETADAS")
    print("=" * 60)
    print("\n💡 Conclusión:")
    print("   El verificador QA independiente proporciona evaluaciones")
    print("   más realistas y críticas que la autoevaluación.")

if __name__ == "__main__":
    main()