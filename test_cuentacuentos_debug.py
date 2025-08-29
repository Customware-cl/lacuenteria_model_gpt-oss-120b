#!/usr/bin/env python3
"""
Test de diagnóstico específico para el agente cuentacuentos
Prueba diferentes configuraciones para entender qué falla
"""
import json
import sys
import time
from datetime import datetime
import logging

# Configurar logging detallado
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Agregar paths necesarios
sys.path.append('/home/ubuntu/cuenteria/src')

from llm_client import LLMClient
from config import get_agent_prompt_path, get_artifact_path

def cargar_dependencias(story_id="test-v2-emilia-1756440401"):
    """Carga las dependencias del director y psicoeducador"""
    dependencies = {}
    
    try:
        # Cargar director
        director_path = f"runs/{story_id}/01_director.json"
        with open(director_path, 'r') as f:
            dependencies['director'] = json.load(f)
        logger.info(f"✓ Director cargado: {len(json.dumps(dependencies['director']))} caracteres")
        
        # Cargar psicoeducador
        psico_path = f"runs/{story_id}/02_psicoeducador.json"
        with open(psico_path, 'r') as f:
            dependencies['psicoeducador'] = json.load(f)
        logger.info(f"✓ Psicoeducador cargado: {len(json.dumps(dependencies['psicoeducador']))} caracteres")
        
    except FileNotFoundError as e:
        logger.warning(f"No se encontraron dependencias previas: {e}")
        # Usar dependencias mínimas de prueba
        dependencies = {
            "director": {
                "leitmotiv": "¡Tic, tac, la canción del pastel!",
                "beat_sheet": [
                    {"pagina": i, "objetivo": f"Objetivo página {i}", 
                     "conflicto": f"Conflicto página {i}" if i < 10 else None,
                     "resolucion": f"Resolución página {i}" if i == 10 else None,
                     "emocion": "alegría", "imagen_nuclear": f"Imagen página {i}"}
                    for i in range(1, 11)
                ]
            },
            "psicoeducador": {
                "mapa_psico_narrativo": {
                    str(i): {"micro_habilidades": ["habilidad1"], "recursos": ["recurso1"]}
                    for i in range(1, 11)
                }
            }
        }
    
    return dependencies

def construir_prompt_usuario(dependencies):
    """Construye el prompt del usuario para cuentacuentos"""
    prompt = "Aquí están los artefactos previos que debes usar:\n\n"
    
    # Agregar director
    prompt += "=== DIRECTOR (Beat Sheet) ===\n"
    prompt += json.dumps(dependencies['director'], ensure_ascii=False, indent=2)
    
    prompt += "\n\n=== PSICOEDUCADOR (Mapa Psico-Narrativo) ===\n"
    prompt += json.dumps(dependencies['psicoeducador'], ensure_ascii=False, indent=2)
    
    prompt += "\n\n=== TU TAREA ===\n"
    prompt += "Transforma el beat sheet en versos líricos para niños de 3-5 años.\n"
    prompt += "IMPORTANTE: Debes generar EXACTAMENTE 10 páginas con 4 versos cada una.\n"
    prompt += "El leitmotiv debe aparecer en las páginas indicadas.\n"
    prompt += "Devuelve ÚNICAMENTE el JSON con el formato especificado."
    
    return prompt

def test_con_configuracion(max_tokens, temperature=0.9, timeout=900):
    """Prueba el cuentacuentos con una configuración específica"""
    print(f"\n{'='*70}")
    print(f"🧪 TEST CON max_tokens={max_tokens}, temp={temperature}, timeout={timeout}")
    print('='*70)
    
    try:
        # Inicializar cliente LLM
        client = LLMClient(
            base_url="http://69.19.136.204:8000/v1",
            model="openai/gpt-oss-120b",
            timeout=timeout
        )
        
        # Cargar prompt del sistema
        with open('flujo/v2/agentes/03_cuentacuentos.json', 'r') as f:
            agent_config = json.load(f)
        system_prompt = agent_config['content']
        
        # Cargar dependencias
        dependencies = cargar_dependencias()
        
        # Construir prompt del usuario
        user_prompt = construir_prompt_usuario(dependencies)
        
        # Información de diagnóstico
        print(f"\n📊 Métricas del prompt:")
        print(f"   - System prompt: {len(system_prompt)} caracteres")
        print(f"   - User prompt: {len(user_prompt)} caracteres")
        print(f"   - Total: {len(system_prompt) + len(user_prompt)} caracteres")
        print(f"   - Tokens aproximados: {(len(system_prompt) + len(user_prompt)) // 4}")
        
        # Intentar generar
        print(f"\n⏳ Llamando al modelo...")
        start_time = time.time()
        
        try:
            result = client.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            elapsed = time.time() - start_time
            print(f"✅ ÉXITO en {elapsed:.2f} segundos")
            
            # Analizar resultado
            if isinstance(result, str):
                try:
                    result = json.loads(result)
                except:
                    pass
            
            if isinstance(result, dict):
                print(f"\n📝 Estructura del resultado:")
                print(f"   - Claves: {list(result.keys())}")
                if 'paginas_texto' in result:
                    paginas = result['paginas_texto']
                    print(f"   - Páginas generadas: {len(paginas)}")
                    if paginas:
                        # Mostrar primera página como muestra
                        primera = list(paginas.values())[0] if paginas else ""
                        print(f"   - Muestra página 1: {primera[:100]}...")
                
                # Guardar resultado para análisis
                with open(f'test_cuentacuentos_{max_tokens}tokens.json', 'w') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                print(f"   - Resultado guardado en test_cuentacuentos_{max_tokens}tokens.json")
            
            return True
            
        except ValueError as ve:
            elapsed = time.time() - start_time
            print(f"❌ ERROR ValueError en {elapsed:.2f} segundos: {ve}")
            
            if "El modelo no generó contenido" in str(ve):
                print("   ⚠️ El modelo devolvió respuesta vacía")
                print("   Posibles causas:")
                print("   - Prompt demasiado largo para el contexto disponible")
                print("   - max_tokens insuficiente para la respuesta requerida")
                print("   - Timeout antes de completar la generación")
            
            return False
            
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"❌ ERROR General en {elapsed:.2f} segundos: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Error en configuración: {e}")
        return False

def main():
    """Ejecuta una serie de pruebas con diferentes configuraciones"""
    print("\n" + "="*70)
    print("🔍 DIAGNÓSTICO DETALLADO DEL AGENTE CUENTACUENTOS")
    print("="*70)
    
    # Probar diferentes configuraciones
    configuraciones = [
        # (max_tokens, temperature, timeout)
        (4000, 0.9, 900),   # Configuración actual
        (6000, 0.9, 900),   # Más tokens
        (8000, 0.9, 900),   # Aún más tokens
        (10000, 0.9, 900),  # Máximo de tokens
        (4000, 0.7, 900),   # Menos temperatura
        (4000, 0.5, 900),   # Temperatura baja
        (8000, 0.7, 900),   # Combinación óptima?
    ]
    
    resultados = []
    
    for max_tokens, temp, timeout in configuraciones:
        exito = test_con_configuracion(max_tokens, temp, timeout)
        resultados.append({
            'max_tokens': max_tokens,
            'temperature': temp,
            'timeout': timeout,
            'exito': exito
        })
        
        # Esperar un poco entre pruebas
        if not exito:
            print("\n⏸️ Esperando 10 segundos antes de la siguiente prueba...")
            time.sleep(10)
    
    # Resumen final
    print("\n" + "="*70)
    print("📊 RESUMEN DE RESULTADOS")
    print("="*70)
    
    for r in resultados:
        status = "✅" if r['exito'] else "❌"
        print(f"{status} max_tokens={r['max_tokens']}, temp={r['temperature']} -> {'ÉXITO' if r['exito'] else 'FALLO'}")
    
    # Recomendaciones
    exitosos = [r for r in resultados if r['exito']]
    if exitosos:
        print(f"\n✨ Configuraciones exitosas: {len(exitosos)}")
        mejor = exitosos[0]
        print(f"📌 Configuración recomendada:")
        print(f"   - max_tokens: {mejor['max_tokens']}")
        print(f"   - temperature: {mejor['temperature']}")
        print(f"   - timeout: {mejor['timeout']}")
    else:
        print("\n⚠️ Ninguna configuración fue exitosa")
        print("Posibles soluciones:")
        print("1. Reducir el tamaño de las dependencias")
        print("2. Simplificar el prompt del sistema")
        print("3. Dividir la tarea en sub-tareas más pequeñas")
        print("4. Usar un modelo con ventana de contexto más grande")

if __name__ == "__main__":
    main()