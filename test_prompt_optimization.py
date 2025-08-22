#!/usr/bin/env python3
"""
Script de testing automatizado para optimización de prompts y parámetros
Ejecuta múltiples combinaciones y encuentra la configuración óptima
"""
import json
import time
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import sys
import os

# Agregar src al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.prompt_version_manager import get_prompt_manager
from src.llm_client_optimized import get_optimized_llm_client
from src.agent_runner import AgentRunner
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PromptOptimizationTester:
    """Ejecuta experimentos de optimización para encontrar la mejor configuración"""
    
    def __init__(self):
        self.prompt_manager = get_prompt_manager()
        self.llm_client = get_optimized_llm_client()
        self.results_dir = Path("optimization_results")
        self.results_dir.mkdir(exist_ok=True)
        
        # Brief de Emilia para pruebas
        self.test_brief = {
            "personajes": ["Emilia", "Unicornio"],
            "historia": "Emilia se comunica con un unicornio mágico a través de gestos y descubre que juntos pueden crear luz donde hay oscuridad",
            "mensaje_a_transmitir": "La comunicación va más allá de las palabras",
            "edad_objetivo": 5
        }
        
        # Configuraciones de parámetros predefinidas
        self.param_configs = {
            "editor_claridad": [
                {
                    "name": "baseline",
                    "temperature": 0.60,
                    "max_tokens": 4000
                },
                {
                    "name": "conservative",
                    "temperature": 0.40,
                    "top_p": 0.50,
                    "top_k": 20,
                    "repetition_penalty": 1.1,
                    "max_tokens": 6000
                },
                {
                    "name": "ultra_conservative",
                    "temperature": 0.30,
                    "top_p": 0.30,
                    "top_k": 10,
                    "repetition_penalty": 1.2,
                    "max_tokens": 8000,
                    "frequency_penalty": 0.2
                },
                {
                    "name": "balanced",
                    "temperature": 0.35,
                    "top_p": 0.40,
                    "top_k": 15,
                    "repetition_penalty": 1.15,
                    "max_tokens": 7000,
                    "seed": 42
                }
            ],
            "cuentacuentos": [
                {
                    "name": "baseline",
                    "temperature": 0.90,
                    "max_tokens": 4000
                },
                {
                    "name": "controlled_creative",
                    "temperature": 0.75,
                    "top_p": 0.85,
                    "repetition_penalty": 1.2,
                    "frequency_penalty": 0.4,
                    "max_tokens": 6000
                },
                {
                    "name": "anti_repetition",
                    "temperature": 0.70,
                    "top_p": 0.80,
                    "repetition_penalty": 1.25,
                    "frequency_penalty": 0.5,
                    "presence_penalty": 0.3,
                    "max_tokens": 6500
                },
                {
                    "name": "structured_creative",
                    "temperature": 0.80,
                    "top_p": 0.90,
                    "top_k": 40,
                    "repetition_penalty": 1.15,
                    "frequency_penalty": 0.3,
                    "max_tokens": 6000,
                    "seed": 42
                }
            ],
            "ritmo_rima": [
                {
                    "name": "baseline",
                    "temperature": 0.65,
                    "max_tokens": 4000
                },
                {
                    "name": "precision",
                    "temperature": 0.50,
                    "top_p": 0.70,
                    "frequency_penalty": 0.5,
                    "presence_penalty": 0.3,
                    "max_tokens": 5000
                },
                {
                    "name": "structured",
                    "temperature": 0.45,
                    "top_p": 0.60,
                    "top_k": 30,
                    "frequency_penalty": 0.6,
                    "presence_penalty": 0.4,
                    "max_tokens": 5500
                },
                {
                    "name": "balanced_precision",
                    "temperature": 0.55,
                    "top_p": 0.75,
                    "repetition_penalty": 1.1,
                    "frequency_penalty": 0.4,
                    "presence_penalty": 0.2,
                    "max_tokens": 5000
                }
            ]
        }
    
    def load_dependencies(self, agent_name: str) -> Dict[str, Any]:
        """Carga las dependencias necesarias para un agente"""
        # Para editor_claridad, necesita el output de cuentacuentos
        if agent_name == "editor_claridad":
            # Usar un output de cuentacuentos pre-generado o mock
            return {
                "03_cuentacuentos.json": {
                    "paginas": {
                        "1": "Emilia bajo el árbol sueña bajo cielo azul\\nSus dedos señalan flores que brotan en tierra brillante\\nEl jardín despliega colores en su alegre danza\\nY siente en su pecho cálida señal de magia",
                        "2": "En el bosque claro niebla ligera danza\\nUn unicornio surge, su cuerno refleja luz\\nRayo rosado ilumina su rostro con consuelo\\nEmilia observa curiosa, corazón late esperanza",
                        "3": "Emilia abre su mano invitando al ser\\nEl unicornio inclina cabeza con ternura\\nSus ojos se encuentran, nace vínculo silencioso\\nSin palabras comparten pulsación como lazos",
                        "4": "Emilia muestra palma como saludo suave\\nEl unicornio inclina oreja comprendiendo\\nMovimiento se vuelve danza sin sonido\\nAl principio confuso, fluye en armonía",
                        "5": "Manos y cuerno rozan, brillo tenue surge\\nCada intento lanza chispas de luz clara\\nMagia vibra en aire como estrellas\\nJardín se ilumina, gestos encienden luces",
                        "6": "Emilia y unicornio giran al compás\\nNotas invisibles flotan, pies bailan\\nLuces forman constelaciones pequeñas\\nNoche se llena de sueños estelares",
                        "7": "Sombra gris pasa sobre el unicornio\\nEmilia extiende mano, luz cálida disipa\\nSobresalto sacude pero se tranquiliza\\nValentía brilla, reemplaza temor con seguridad",
                        "8": "Juntos unen mano y cuerno radiante\\nGesto brilla fuerte con pura energía\\nExplosión rosa como pétalos suaves\\nSombra desvanece bajo luz rosada",
                        "9": "Unicornio y Emilia abrazan con ternura\\nCuerpos vibran compartiendo calor sincero\\nDedos dibujan alas como mariposas\\nJardín celebra bajo brillo de alas",
                        "10": "Bajo dorado atardecer siguen bailando\\nSombras se alejan, tranquilidad llega\\nDibujan corazones luminosos irradiando paz\\nCielo responde con luz eterna abrazando"
                    },
                    "leitmotiv": "¡Brilla, brilla, luz de amistad!"
                }
            }
        elif agent_name == "ritmo_rima":
            # Para ritmo_rima, necesita output de editor_claridad
            return {
                "04_editor_claridad.json": {
                    "paginas_texto_claro": {
                        "1": "Emilia está bajo el árbol grande\\nMira el cielo azul brillante\\nSeñala flores de colores\\nSiente magia en sus amores",
                        "2": "En el bosque hay neblina\\nLlega un unicornio que camina\\nSu cuerno brilla con luz rosa\\nEmilia lo mira curiosa",
                        "3": "Emilia abre su manita\\nEl unicornio se la mira bonita\\nSe miran con cariño\\nNace un lazo sin aliño",
                        "4": "Emilia muestra su palma abierta\\nEl unicornio la oreja despierta\\nBailan sin hacer ruido\\nTodo fluye divertido",
                        "5": "Mano y cuerno se tocan suave\\nSalen chispas como ave\\nLa magia brilla en el aire\\nEl jardín tiene donaire",
                        "6": "Giran juntos al compás\\nBailan más y más y más\\nLas luces forman estrellitas\\nLa noche está de fiestecitas",
                        "7": "Una sombra gris aparece\\nEmilia la mano ofrece\\nCon luz cálida la espanta\\nLa valentía se levanta",
                        "8": "Juntos hacen un corazón\\nBrilla fuerte la unión\\nPétalos rosas vuelan\\nLas sombras se congelan",
                        "9": "Se abrazan con amor\\nComparten su calor\\nDibujan mariposas\\nCon alas luminosas",
                        "10": "Al atardecer dorado\\nSiguen juntos lado a lado\\nHacen luces de colores\\nLlenos de amores"
                    }
                }
            }
        else:
            # Para cuentacuentos, usar director y psicoeducador
            return {
                "01_director.json": {
                    "leitmotiv": "¡Brilla, brilla, luz de amistad!",
                    "beat_sheet": [
                        {"pagina": 1, "objetivo": "Presentar a Emilia", "imagen_nuclear": "Niña bajo árbol mirando cielo"},
                        {"pagina": 2, "objetivo": "Aparece el unicornio", "imagen_nuclear": "Unicornio con cuerno brillante"},
                        {"pagina": 3, "objetivo": "Primer contacto", "imagen_nuclear": "Manos extendidas"},
                        {"pagina": 4, "objetivo": "Comunicación gestual", "imagen_nuclear": "Danza de gestos"},
                        {"pagina": 5, "objetivo": "Magia emerge", "imagen_nuclear": "Chispas de luz"},
                        {"pagina": 6, "objetivo": "Baile conjunto", "imagen_nuclear": "Giros bajo estrellas"},
                        {"pagina": 7, "objetivo": "Aparece sombra", "imagen_nuclear": "Sombra amenazante"},
                        {"pagina": 8, "objetivo": "Vencen oscuridad", "imagen_nuclear": "Explosión de luz"},
                        {"pagina": 9, "objetivo": "Celebración", "imagen_nuclear": "Abrazo luminoso"},
                        {"pagina": 10, "objetivo": "Paz eterna", "imagen_nuclear": "Atardecer dorado"}
                    ]
                },
                "02_psicoeducador.json": {
                    "recursos_psicologicos": ["comunicación no verbal", "empatía", "valentía"],
                    "metas_conductuales": ["expresar sin palabras", "conectar con otros", "enfrentar miedos"]
                }
            }
    
    def execute_single_test(self, agent_name: str, prompt_variant: str, 
                           param_config: Dict, run_number: int) -> Dict:
        """Ejecuta una prueba individual con una combinación específica"""
        
        logger.info(f"Ejecutando: {agent_name} | Variant: {prompt_variant} | "
                   f"Config: {param_config['name']} | Run: {run_number}")
        
        start_time = time.time()
        
        try:
            # Cargar prompt variante
            prompt_data = self.prompt_manager.load_variant(agent_name, prompt_variant)
            system_prompt = prompt_data["content"]
            
            # Preparar dependencias
            dependencies = self.load_dependencies(agent_name)
            
            # Construir user prompt con dependencias
            user_prompt = f"Brief: {json.dumps(self.test_brief, ensure_ascii=False)}\n\n"
            for dep_name, dep_content in dependencies.items():
                user_prompt += f"Dependencia {dep_name}:\n{json.dumps(dep_content, ensure_ascii=False)}\n\n"
            
            # Ejecutar con LLM optimizado
            result = self.llm_client.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                **{k: v for k, v in param_config.items() if k != 'name'}
            )
            
            execution_time = time.time() - start_time
            
            # Evaluar calidad con verificador_qa simulado
            qa_score = self.evaluate_output(agent_name, result)
            
            # Verificar completitud
            is_complete = self.check_completeness(agent_name, result)
            
            return {
                "success": True,
                "prompt_variant": prompt_variant,
                "param_config": param_config['name'],
                "run": run_number,
                "qa_score": qa_score,
                "execution_time": execution_time,
                "output_complete": is_complete,
                "output_sample": str(result)[:500],
                "tokens_used": result.get("_metadata_tokens", {}),
                "error": None
            }
            
        except Exception as e:
            logger.error(f"Error en test: {e}")
            return {
                "success": False,
                "prompt_variant": prompt_variant,
                "param_config": param_config['name'],
                "run": run_number,
                "qa_score": 0,
                "execution_time": time.time() - start_time,
                "output_complete": False,
                "output_sample": None,
                "error": str(e)
            }
    
    def evaluate_output(self, agent_name: str, output: Dict) -> float:
        """Evalúa la calidad del output (simulación del verificador_qa)"""
        
        if agent_name == "editor_claridad":
            # Verificar que todas las páginas tienen contenido
            pages = output.get("paginas_texto_claro", {})
            if not pages:
                return 1.0
            
            empty_pages = sum(1 for p in range(1, 11) if not pages.get(str(p), "").strip())
            if empty_pages > 0:
                return max(1.0, 5.0 - (empty_pages * 0.5))
            
            # Verificar glosario
            glosario = output.get("glosario", [])
            if len(glosario) < 3:
                return 3.5
            
            return 4.5  # Output completo y bien formado
            
        elif agent_name == "cuentacuentos":
            pages = output.get("paginas", {})
            if not pages:
                return 1.0
            
            # Detectar repeticiones
            all_text = " ".join(pages.values())
            word_count = {}
            for word in all_text.split():
                word_count[word] = word_count.get(word, 0) + 1
            
            # Penalizar repeticiones excesivas
            repetitions = sum(1 for count in word_count.values() if count > 5)
            if repetitions > 10:
                return 2.5
            elif repetitions > 5:
                return 3.5
            
            return 4.2
            
        elif agent_name == "ritmo_rima":
            pages = output.get("paginas_rimadas", {})
            if not pages:
                return 1.0
            
            # Verificar estructura de rima básica
            rhyme_quality = 4.0
            for page_text in pages.values():
                lines = page_text.split('\\n')
                if len(lines) != 4:
                    rhyme_quality -= 0.2
            
            return max(2.0, rhyme_quality)
        
        return 3.0  # Default
    
    def check_completeness(self, agent_name: str, output: Dict) -> bool:
        """Verifica si el output está completo"""
        
        if agent_name == "editor_claridad":
            pages = output.get("paginas_texto_claro", {})
            return all(pages.get(str(i), "").strip() for i in range(1, 11))
            
        elif agent_name == "cuentacuentos":
            pages = output.get("paginas", {})
            return len(pages) == 10 and all(v.strip() for v in pages.values())
            
        elif agent_name == "ritmo_rima":
            pages = output.get("paginas_rimadas", {})
            return len(pages) == 10
        
        return True
    
    def run_optimization_experiment(self, agent_name: str, 
                                   prompt_variants: Optional[List[str]] = None,
                                   param_configs: Optional[List[str]] = None,
                                   runs_per_combo: int = 3) -> Dict:
        """
        Ejecuta el experimento completo de optimización
        
        Args:
            agent_name: Nombre del agente a optimizar
            prompt_variants: Lista de variantes a probar (None = todas)
            param_configs: Lista de configuraciones a probar (None = todas)
            runs_per_combo: Número de ejecuciones por combinación
        """
        
        print(f"\n🧪 EXPERIMENTO DE OPTIMIZACIÓN: {agent_name}")
        print("=" * 60)
        
        # Obtener variantes disponibles
        if prompt_variants is None:
            all_variants = self.prompt_manager.list_variants(agent_name)
            prompt_variants = [v['name'] for v in all_variants]
        
        # Obtener configuraciones de parámetros
        if param_configs is None:
            param_configs = self.param_configs.get(agent_name, [
                {"name": "baseline", "temperature": 0.7, "max_tokens": 4000}
            ])
        else:
            # Filtrar configs por nombre
            all_configs = self.param_configs.get(agent_name, [])
            param_configs = [c for c in all_configs if c['name'] in param_configs]
        
        total_tests = len(prompt_variants) * len(param_configs) * runs_per_combo
        print(f"📊 Total de pruebas: {total_tests}")
        print(f"   • Variantes de prompt: {len(prompt_variants)}")
        print(f"   • Configuraciones de params: {len(param_configs)}")
        print(f"   • Runs por combinación: {runs_per_combo}")
        print()
        
        results = []
        test_count = 0
        
        # Ejecutar todas las combinaciones
        for prompt_variant in prompt_variants:
            for param_config in param_configs:
                for run in range(1, runs_per_combo + 1):
                    test_count += 1
                    print(f"[{test_count}/{total_tests}] ", end="")
                    
                    result = self.execute_single_test(
                        agent_name=agent_name,
                        prompt_variant=prompt_variant,
                        param_config=param_config,
                        run_number=run
                    )
                    
                    results.append(result)
                    
                    # Mostrar resultado
                    if result['success']:
                        print(f"✅ QA: {result['qa_score']:.1f}/5 | "
                             f"Time: {result['execution_time']:.1f}s | "
                             f"Complete: {result['output_complete']}")
                    else:
                        print(f"❌ Error: {result['error'][:50]}")
                    
                    # Pequeña pausa entre pruebas
                    time.sleep(2)
        
        # Generar reporte
        report = self.generate_report(agent_name, results)
        
        # Guardar resultados
        self.save_results(agent_name, results, report)
        
        return report
    
    def generate_report(self, agent_name: str, results: List[Dict]) -> Dict:
        """Genera un reporte con análisis de resultados"""
        
        # Agrupar por combinación
        combinations = {}
        for r in results:
            if not r['success']:
                continue
            
            key = f"{r['prompt_variant']}_{r['param_config']}"
            if key not in combinations:
                combinations[key] = []
            combinations[key].append(r)
        
        # Calcular estadísticas por combinación
        combo_stats = {}
        for combo, combo_results in combinations.items():
            qa_scores = [r['qa_score'] for r in combo_results]
            exec_times = [r['execution_time'] for r in combo_results]
            complete_rate = sum(1 for r in combo_results if r['output_complete']) / len(combo_results)
            
            combo_stats[combo] = {
                "prompt_variant": combo_results[0]['prompt_variant'],
                "param_config": combo_results[0]['param_config'],
                "avg_qa_score": sum(qa_scores) / len(qa_scores),
                "min_qa_score": min(qa_scores),
                "max_qa_score": max(qa_scores),
                "avg_execution_time": sum(exec_times) / len(exec_times),
                "completion_rate": complete_rate,
                "num_runs": len(combo_results)
            }
        
        # Encontrar mejor combinación
        if combo_stats:
            best_combo = max(combo_stats.items(), 
                           key=lambda x: (x[1]['avg_qa_score'], x[1]['completion_rate']))
        else:
            best_combo = None
        
        report = {
            "agent_name": agent_name,
            "timestamp": datetime.now().isoformat(),
            "total_tests": len(results),
            "successful_tests": sum(1 for r in results if r['success']),
            "combinations_tested": len(combinations),
            "combination_stats": combo_stats,
            "best_combination": best_combo[0] if best_combo else None,
            "best_stats": best_combo[1] if best_combo else None
        }
        
        # Imprimir resumen
        print("\n" + "=" * 60)
        print("📊 RESUMEN DE RESULTADOS")
        print("=" * 60)
        
        if best_combo:
            print(f"\n🏆 MEJOR COMBINACIÓN: {best_combo[0]}")
            print(f"   • Prompt: {best_combo[1]['prompt_variant']}")
            print(f"   • Config: {best_combo[1]['param_config']}")
            print(f"   • QA Score: {best_combo[1]['avg_qa_score']:.2f}/5")
            print(f"   • Completion Rate: {best_combo[1]['completion_rate']*100:.0f}%")
            print(f"   • Avg Time: {best_combo[1]['avg_execution_time']:.1f}s")
        
        print(f"\n📈 Estadísticas Generales:")
        print(f"   • Tests exitosos: {report['successful_tests']}/{report['total_tests']}")
        print(f"   • Combinaciones probadas: {report['combinations_tested']}")
        
        return report
    
    def save_results(self, agent_name: str, results: List[Dict], report: Dict):
        """Guarda los resultados en archivos"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Guardar resultados detallados
        results_file = self.results_dir / f"{agent_name}_results_{timestamp}.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        # Guardar reporte
        report_file = self.results_dir / f"{agent_name}_report_{timestamp}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Resultados guardados:")
        print(f"   • {results_file}")
        print(f"   • {report_file}")
    
    def apply_best_configuration(self, agent_name: str, report: Dict):
        """Aplica la mejor configuración encontrada"""
        
        if not report.get('best_combination'):
            print("❌ No se encontró una configuración óptima")
            return
        
        best_stats = report['best_stats']
        print(f"\n🎯 Aplicando configuración óptima para {agent_name}:")
        print(f"   • Prompt variant: {best_stats['prompt_variant']}")
        print(f"   • Param config: {best_stats['param_config']}")
        
        # TODO: Implementar aplicación de configuración
        # 1. Aplicar variante de prompt
        # 2. Guardar configuración de parámetros en config/


def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description='Optimización de prompts y parámetros')
    parser.add_argument('--agent', required=True, help='Nombre del agente a optimizar')
    parser.add_argument('--variants', nargs='+', help='Variantes de prompt a probar')
    parser.add_argument('--configs', nargs='+', help='Configuraciones de params a probar')
    parser.add_argument('--runs', type=int, default=3, help='Runs por combinación')
    parser.add_argument('--apply-best', action='store_true', help='Aplicar mejor config al final')
    
    args = parser.parse_args()
    
    tester = PromptOptimizationTester()
    
    # Ejecutar experimento
    report = tester.run_optimization_experiment(
        agent_name=args.agent,
        prompt_variants=args.variants,
        param_configs=args.configs,
        runs_per_combo=args.runs
    )
    
    # Aplicar mejor configuración si se solicita
    if args.apply_best and report.get('best_combination'):
        tester.apply_best_configuration(args.agent, report)


if __name__ == "__main__":
    main()