#!/usr/bin/env python3
"""
Script de prueba A/B para comparar configuraciones del sistema Cuentería.
Ejecuta historias con configuración actual vs optimizada y compara métricas.
"""
import json
import time
import requests
from datetime import datetime
from pathlib import Path
import statistics
from typing import Dict, List, Optional

class ABTestRunner:
    """Ejecutor de pruebas A/B para optimización de configuración"""
    
    def __init__(self):
        self.api_base = "http://localhost:5000"
        self.results_dir = Path("test_results")
        self.results_dir.mkdir(exist_ok=True)
        
        # Briefs de prueba predefinidos
        self.test_briefs = [
            {
                "personajes": ["Luna", "Estrella"],
                "historia": "Luna se siente sola en el cielo nocturno hasta que descubre que las estrellas son sus amigas",
                "mensaje_a_transmitir": "Nunca estamos solos, siempre hay amigos cerca",
                "edad_objetivo": 5
            },
            {
                "personajes": ["Tomás", "Dragón"],
                "historia": "Tomás tiene miedo a la oscuridad pero descubre que un dragón amigable la ilumina",
                "mensaje_a_transmitir": "Los miedos se vencen con valentía y amistad",
                "edad_objetivo": 6
            },
            {
                "personajes": ["Marina", "Delfín"],
                "historia": "Marina aprende a nadar con ayuda de un delfín mágico que le enseña a confiar",
                "mensaje_a_transmitir": "La confianza en uno mismo es la clave del éxito",
                "edad_objetivo": 4
            }
        ]
    
    def create_story(self, brief: Dict, config_type: str) -> Optional[str]:
        """Crea una historia con la configuración especificada"""
        story_id = f"{config_type}-{int(time.time())}"
        
        payload = {
            "story_id": story_id,
            "config_type": config_type,  # "default" o "optimized"
            **brief
        }
        
        try:
            response = requests.post(
                f"{self.api_base}/api/stories/create",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 202:
                return story_id
            else:
                print(f"Error creando historia: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def wait_for_completion(self, story_id: str, timeout: int = 900) -> Dict:
        """Espera a que se complete una historia y obtiene resultados"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get(
                    f"{self.api_base}/api/stories/{story_id}/status",
                    timeout=5
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get("status") in ["completed", "success", "error", "qa_failed"]:
                        # Obtener resultado completo
                        result_response = requests.get(
                            f"{self.api_base}/api/stories/{story_id}/result",
                            timeout=10
                        )
                        
                        if result_response.status_code == 200:
                            return result_response.json()
                        else:
                            return data
                
                time.sleep(10)  # Esperar 10 segundos entre verificaciones
                
            except Exception as e:
                print(f"Error verificando estado: {e}")
                time.sleep(10)
        
        return {"status": "timeout", "story_id": story_id}
    
    def analyze_result(self, result: Dict) -> Dict:
        """Analiza un resultado y extrae métricas clave"""
        metrics = {
            "story_id": result.get("story_id"),
            "status": result.get("status"),
            "processing_time": result.get("processing_time", 0),
            "qa_scores": {},
            "retries": {},
            "failures": [],
            "empty_outputs": 0
        }
        
        # Extraer QA scores por agente
        qa_data = result.get("qa_scores", {}).get("by_agent", {})
        for agent, scores in qa_data.items():
            if "promedio" in scores:
                metrics["qa_scores"][agent] = scores["promedio"]
        
        # Calcular QA promedio global
        if metrics["qa_scores"]:
            metrics["qa_average"] = statistics.mean(metrics["qa_scores"].values())
        else:
            metrics["qa_average"] = 0
        
        # Contar reintentos
        metadata = result.get("metadata", {})
        retries = metadata.get("retries", {})
        metrics["total_retries"] = sum(retries.values())
        metrics["agents_with_retries"] = len(retries)
        
        # Identificar fallos
        warnings = metadata.get("warnings", [])
        for warning in warnings:
            if "QA bajo umbral" in warning:
                metrics["failures"].append(warning)
        
        # Detectar outputs vacíos (basado en QA scores muy bajos)
        for agent, score in metrics["qa_scores"].items():
            if score <= 1.5:
                metrics["empty_outputs"] += 1
        
        return metrics
    
    def run_test_group(self, config_type: str, num_tests: int = 3) -> List[Dict]:
        """Ejecuta un grupo de pruebas con una configuración específica"""
        print(f"\n{'='*60}")
        print(f"Ejecutando pruebas con configuración: {config_type.upper()}")
        print(f"{'='*60}")
        
        results = []
        
        for i, brief in enumerate(self.test_briefs[:num_tests], 1):
            print(f"\nTest {i}/{num_tests}: {brief['personajes'][0]}...")
            
            # Crear historia
            story_id = self.create_story(brief, config_type)
            if not story_id:
                print(f"  ❌ Error creando historia")
                continue
            
            print(f"  Story ID: {story_id}")
            print(f"  ⏳ Esperando resultado...")
            
            # Esperar resultado
            result = self.wait_for_completion(story_id)
            
            # Analizar resultado
            metrics = self.analyze_result(result)
            results.append(metrics)
            
            # Mostrar resumen
            print(f"  Estado: {metrics['status']}")
            print(f"  Tiempo: {metrics['processing_time']:.2f}s")
            print(f"  QA Promedio: {metrics['qa_average']:.2f}/5")
            print(f"  Reintentos: {metrics['total_retries']}")
            
            # Pausa entre pruebas
            time.sleep(5)
        
        return results
    
    def compare_results(self, results_a: List[Dict], results_b: List[Dict]) -> Dict:
        """Compara resultados entre dos grupos de pruebas"""
        comparison = {
            "group_a": {
                "config": "default",
                "total_tests": len(results_a),
                "successful": sum(1 for r in results_a if r["status"] in ["completed", "success"]),
                "avg_time": statistics.mean([r["processing_time"] for r in results_a if r["processing_time"] > 0]),
                "avg_qa": statistics.mean([r["qa_average"] for r in results_a if r["qa_average"] > 0]),
                "total_retries": sum(r["total_retries"] for r in results_a),
                "empty_outputs": sum(r["empty_outputs"] for r in results_a)
            },
            "group_b": {
                "config": "optimized",
                "total_tests": len(results_b),
                "successful": sum(1 for r in results_b if r["status"] in ["completed", "success"]),
                "avg_time": statistics.mean([r["processing_time"] for r in results_b if r["processing_time"] > 0]),
                "avg_qa": statistics.mean([r["qa_average"] for r in results_b if r["qa_average"] > 0]),
                "total_retries": sum(r["total_retries"] for r in results_b),
                "empty_outputs": sum(r["empty_outputs"] for r in results_b)
            }
        }
        
        # Calcular mejoras
        comparison["improvements"] = {
            "time_reduction": (
                (comparison["group_a"]["avg_time"] - comparison["group_b"]["avg_time"]) 
                / comparison["group_a"]["avg_time"] * 100
            ) if comparison["group_a"]["avg_time"] > 0 else 0,
            
            "quality_increase": (
                (comparison["group_b"]["avg_qa"] - comparison["group_a"]["avg_qa"]) 
                / comparison["group_a"]["avg_qa"] * 100
            ) if comparison["group_a"]["avg_qa"] > 0 else 0,
            
            "retry_reduction": (
                (comparison["group_a"]["total_retries"] - comparison["group_b"]["total_retries"]) 
                / comparison["group_a"]["total_retries"] * 100
            ) if comparison["group_a"]["total_retries"] > 0 else 0,
            
            "empty_output_reduction": (
                (comparison["group_a"]["empty_outputs"] - comparison["group_b"]["empty_outputs"]) 
                / comparison["group_a"]["empty_outputs"] * 100
            ) if comparison["group_a"]["empty_outputs"] > 0 else 0
        }
        
        return comparison
    
    def generate_report(self, comparison: Dict):
        """Genera un reporte detallado de la comparación"""
        print("\n" + "="*60)
        print("📊 REPORTE DE COMPARACIÓN A/B")
        print("="*60)
        
        print("\n🔹 CONFIGURACIÓN DEFAULT:")
        print(f"  Pruebas exitosas: {comparison['group_a']['successful']}/{comparison['group_a']['total_tests']}")
        print(f"  Tiempo promedio: {comparison['group_a']['avg_time']:.2f}s")
        print(f"  QA promedio: {comparison['group_a']['avg_qa']:.2f}/5")
        print(f"  Total reintentos: {comparison['group_a']['total_retries']}")
        print(f"  Outputs vacíos: {comparison['group_a']['empty_outputs']}")
        
        print("\n🔸 CONFIGURACIÓN OPTIMIZADA:")
        print(f"  Pruebas exitosas: {comparison['group_b']['successful']}/{comparison['group_b']['total_tests']}")
        print(f"  Tiempo promedio: {comparison['group_b']['avg_time']:.2f}s")
        print(f"  QA promedio: {comparison['group_b']['avg_qa']:.2f}/5")
        print(f"  Total reintentos: {comparison['group_b']['total_retries']}")
        print(f"  Outputs vacíos: {comparison['group_b']['empty_outputs']}")
        
        print("\n📈 MEJORAS OBSERVADAS:")
        improvements = comparison['improvements']
        
        if improvements['time_reduction'] > 0:
            print(f"  ✅ Reducción de tiempo: {improvements['time_reduction']:.1f}%")
        else:
            print(f"  ❌ Aumento de tiempo: {abs(improvements['time_reduction']):.1f}%")
        
        if improvements['quality_increase'] > 0:
            print(f"  ✅ Mejora en calidad: {improvements['quality_increase']:.1f}%")
        else:
            print(f"  ❌ Reducción en calidad: {abs(improvements['quality_increase']):.1f}%")
        
        if improvements['retry_reduction'] > 0:
            print(f"  ✅ Reducción de reintentos: {improvements['retry_reduction']:.1f}%")
        else:
            print(f"  ❌ Aumento de reintentos: {abs(improvements['retry_reduction']):.1f}%")
        
        if improvements['empty_output_reduction'] > 0:
            print(f"  ✅ Reducción de outputs vacíos: {improvements['empty_output_reduction']:.1f}%")
        else:
            print(f"  ⚠️ Sin cambio en outputs vacíos")
        
        # Guardar reporte en archivo
        report_file = self.results_dir / f"ab_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(comparison, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Reporte guardado en: {report_file}")
    
    def run_full_test(self, num_tests_per_group: int = 3):
        """Ejecuta el test A/B completo"""
        print("\n🧪 INICIANDO TEST A/B DE OPTIMIZACIÓN")
        print("="*60)
        print(f"Ejecutando {num_tests_per_group} pruebas por configuración")
        print("="*60)
        
        # Verificar servidor
        try:
            response = requests.get(f"{self.api_base}/health", timeout=5)
            if response.status_code != 200:
                print("❌ Servidor no disponible")
                return
        except:
            print("❌ No se puede conectar al servidor")
            print("   Ejecuta: python3 src/api_server.py")
            return
        
        # Ejecutar Grupo A (configuración default)
        print("\n📌 GRUPO A - Configuración Default")
        results_a = self.run_test_group("default", num_tests_per_group)
        
        # Pausa entre grupos
        print("\n⏸️ Pausa de 30 segundos entre grupos...")
        time.sleep(30)
        
        # Ejecutar Grupo B (configuración optimizada)
        print("\n📌 GRUPO B - Configuración Optimizada")
        results_b = self.run_test_group("optimized", num_tests_per_group)
        
        # Comparar resultados
        comparison = self.compare_results(results_a, results_b)
        
        # Generar reporte
        self.generate_report(comparison)
        
        print("\n✅ TEST A/B COMPLETADO")

def main():
    """Función principal"""
    runner = ABTestRunner()
    
    # Menú de opciones
    print("\n🧪 TEST A/B DE OPTIMIZACIÓN CUENTERÍA")
    print("="*40)
    print("1. Test rápido (1 historia por grupo)")
    print("2. Test normal (3 historias por grupo)")
    print("3. Test completo (5 historias por grupo)")
    print("="*40)
    
    opcion = input("Selecciona opción (1-3): ").strip()
    
    if opcion == "1":
        runner.run_full_test(num_tests_per_group=1)
    elif opcion == "2":
        runner.run_full_test(num_tests_per_group=3)
    elif opcion == "3":
        runner.run_full_test(num_tests_per_group=5)
    else:
        print("Opción inválida")

if __name__ == "__main__":
    main()