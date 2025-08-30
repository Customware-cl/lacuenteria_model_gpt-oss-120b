"""
Módulo especializado para procesamiento paralelo del agente Cuentacuentos
Procesa cada página de manera autónoma con verificación QA individual
"""
import json
import logging
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Set, Optional, Tuple
import time

from llm_client import get_llm_client
from config import get_story_path, get_artifact_path

logger = logging.getLogger(__name__)


class ParallelCuentacuentos:
    """Procesador paralelo para el agente cuentacuentos"""
    
    def __init__(self, story_id: str, version: str = 'v2'):
        self.story_id = story_id
        self.version = version
        self.llm_client = get_llm_client()
        
        # Thread-safe para tracking de rimas usadas
        self.used_rimas_lock = threading.Lock()
        self.used_rimas: Set[str] = set()
        
        # Para consolidación progresiva
        self.pages_completed = {}
        self.pages_lock = threading.Lock()
        
        # Cargar configuración específica
        self.base_dir = Path(__file__).parent.parent
        self.load_config()
        
        # Cargar dependencias
        self.director_data = None
        self.psicoeducador_data = None
        self.brief_data = None
        self.load_dependencies()
        
    def load_config(self):
        """Carga configuración para procesamiento paralelo"""
        # Configuración por defecto
        self.config = {
            "max_workers": 10,
            "page_timeout": 60,
            "max_retries_per_page": 2,
            "temperature": 0.75,
            "max_tokens": 1500,
            "top_p": 0.95,
            "qa_threshold": 3.5
        }
        
        # Intentar cargar configuración específica de v2
        config_path = self.base_dir / f"flujo/{self.version}/agent_config.json"
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                agent_configs = json.load(f)
                if "03_cuentacuentos" in agent_configs:
                    cuentos_config = agent_configs["03_cuentacuentos"]
                    self.config.update({
                        "temperature": cuentos_config.get("temperature", 0.75),
                        "max_tokens": cuentos_config.get("max_tokens_per_page", 1500),
                        "top_p": cuentos_config.get("top_p", 0.95),
                        "qa_threshold": cuentos_config.get("qa_threshold", 3.5)
                    })
        
        logger.info(f"📊 Configuración paralela cargada: {self.config}")
        
    def load_dependencies(self):
        """Carga los artefactos necesarios del director y psicoeducador"""
        story_path = get_story_path(self.story_id)
        
        # Cargar director
        director_path = story_path / "01_director.json"
        if director_path.exists():
            with open(director_path, 'r', encoding='utf-8') as f:
                self.director_data = json.load(f)
        else:
            raise FileNotFoundError(f"No se encontró {director_path}")
        
        # Cargar psicoeducador
        psico_path = story_path / "02_psicoeducador.json"
        if psico_path.exists():
            with open(psico_path, 'r', encoding='utf-8') as f:
                self.psicoeducador_data = json.load(f)
        else:
            raise FileNotFoundError(f"No se encontró {psico_path}")
        
        # Cargar brief
        brief_path = story_path / "brief.json"
        if brief_path.exists():
            with open(brief_path, 'r', encoding='utf-8') as f:
                self.brief_data = json.load(f)
        
        logger.info(f"✅ Dependencias cargadas para {self.story_id}")
        
    def create_page_prompt(self, page_num: int, retry_num: int = 0) -> Tuple[str, str]:
        """
        Crea prompts específicos para una página individual
        
        Returns:
            Tuple de (system_prompt, user_prompt)
        """
        # Obtener datos específicos de la página
        beat = self.director_data["beat_sheet"][page_num - 1]
        psico = self.psicoeducador_data["mapa_psico_narrativo"][page_num - 1]
        leitmotiv = self.director_data.get("leitmotiv", "")
        edad = self.psicoeducador_data.get("edad_objetivo", 3)
        
        # Determinar si esta página necesita el leitmotiv
        include_leitmotiv = page_num in [2, 5, 10]
        
        # Obtener rimas ya usadas (thread-safe)
        with self.used_rimas_lock:
            rimas_prohibidas = list(self.used_rimas)
        
        # System prompt simplificado y enfocado
        system_prompt = f"""Eres un experto en versos infantiles. Tu tarea es crear EXACTAMENTE 4 versos para la página {page_num} del cuento.

REGLA ABSOLUTA #1: NUNCA uses la misma palabra para rimar.
REGLA ABSOLUTA #2: Esquema AABB (versos 1-2 riman, versos 3-4 riman).
REGLA ABSOLUTA #3: Cada verso debe tener entre 8-15 sílabas.

Edad objetivo: {edad} años (usa vocabulario muy simple).

{"INCLUYE EL LEITMOTIV: '" + leitmotiv + "' en algún verso." if include_leitmotiv else ""}

Responde ÚNICAMENTE con este JSON:
{{
  "pagina": {page_num},
  "versos": [
    "verso 1 aquí",
    "verso 2 aquí (rima con verso 1)",
    "verso 3 aquí", 
    "verso 4 aquí (rima con verso 3)"
  ],
  "palabras_finales": ["palabra1", "palabra2", "palabra3", "palabra4"]
}}"""

        # User prompt con contexto específico
        user_prompt = f"""PÁGINA {page_num} - CONTEXTO:

NARRATIVA (Director):
- Objetivo: {beat.get('objetivo', '')}
- {"Conflicto" if page_num < 10 else "Resolución"}: {beat.get('conflicto' if page_num < 10 else 'resolucion', '')}
- Emoción: {beat.get('emocion', '')}
- Imagen: {beat.get('imagen_nuclear', '')}

PSICOEDUCACIÓN:
- Habilidad: {psico.get('micro_habilidad', '')}
- Frase modelo: {psico.get('frase_modelo', '')}

PERSONAJES: {', '.join(self.brief_data.get('personajes', [])) if self.brief_data else 'Emilia y Caty'}

{"PALABRAS YA USADAS PARA RIMAR (NO REPETIR): " + ', '.join(rimas_prohibidas) if rimas_prohibidas else ""}

Crea 4 versos que:
1. Cuenten esta parte de la historia
2. {"Incluyan el leitmotiv '" + leitmotiv + "'" if include_leitmotiv else "Mantengan fluidez narrativa"}
3. NO repitan ninguna palabra para rimar
4. Sean comprensibles para {edad} años"""
        
        return system_prompt, user_prompt
    
    def process_single_page(self, page_num: int) -> Dict[str, Any]:
        """
        Procesa una página individual con reintentos si es necesario
        
        Returns:
            Diccionario con el resultado de la página
        """
        logger.info(f"🎭 Procesando página {page_num}...")
        start_time = time.time()
        
        for retry in range(self.config["max_retries_per_page"]):
            try:
                # Crear prompts para esta página
                system_prompt, user_prompt = self.create_page_prompt(page_num, retry)
                
                # Llamar al LLM
                response = self.llm_client.generate(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    temperature=self.config["temperature"],
                    max_tokens=self.config["max_tokens"],
                    top_p=self.config["top_p"]
                )
                
                # Parsear respuesta
                if isinstance(response, str):
                    result = json.loads(response)
                else:
                    result = response
                
                # Validar QA básico
                qa_passed, qa_issues = self.validate_page(result, page_num)
                
                if qa_passed:
                    # Agregar palabras finales a la lista global (thread-safe)
                    if "palabras_finales" in result:
                        with self.used_rimas_lock:
                            self.used_rimas.update(result["palabras_finales"])
                    
                    # Preparar resultado exitoso
                    return {
                        "page_num": page_num,
                        "success": True,
                        "versos": result.get("versos", []),
                        "palabras_finales": result.get("palabras_finales", []),
                        "qa_score": 4.0,  # Por ahora fijo, luego calcular
                        "retry_count": retry,
                        "processing_time": time.time() - start_time
                    }
                else:
                    logger.warning(f"⚠️ Página {page_num} falló QA (intento {retry + 1}): {qa_issues}")
                    if retry == self.config["max_retries_per_page"] - 1:
                        # Último intento fallido
                        return {
                            "page_num": page_num,
                            "success": False,
                            "error": f"QA failed after {retry + 1} attempts",
                            "qa_issues": qa_issues,
                            "processing_time": time.time() - start_time
                        }
                    
            except Exception as e:
                logger.error(f"❌ Error procesando página {page_num}: {e}")
                if retry == self.config["max_retries_per_page"] - 1:
                    return {
                        "page_num": page_num,
                        "success": False,
                        "error": str(e),
                        "processing_time": time.time() - start_time
                    }
        
        return {
            "page_num": page_num,
            "success": False,
            "error": "Max retries exceeded",
            "processing_time": time.time() - start_time
        }
    
    def validate_page(self, page_result: Dict, page_num: int) -> Tuple[bool, List[str]]:
        """
        Valida QA básico para una página individual
        
        Returns:
            Tuple de (passed: bool, issues: List[str])
        """
        issues = []
        
        # Verificar estructura básica
        if "versos" not in page_result:
            issues.append("No se encontraron versos")
            return False, issues
        
        versos = page_result["versos"]
        if len(versos) != 4:
            issues.append(f"Se esperaban 4 versos, se encontraron {len(versos)}")
            return False, issues
        
        # Verificar palabras finales
        if "palabras_finales" in page_result:
            palabras = page_result["palabras_finales"]
            if len(palabras) == 4:
                # Verificar que no se repiten palabras para rimar
                if palabras[0].lower() == palabras[1].lower():
                    issues.append(f"Repite palabra para rimar: {palabras[0]}/{palabras[1]}")
                if palabras[2].lower() == palabras[3].lower():
                    issues.append(f"Repite palabra para rimar: {palabras[2]}/{palabras[3]}")
        
        # Verificar leitmotiv si es necesario
        if page_num in [2, 5, 10]:
            leitmotiv = self.director_data.get("leitmotiv", "")
            texto_completo = " ".join(versos)
            if leitmotiv and leitmotiv.lower() not in texto_completo.lower():
                issues.append(f"Falta el leitmotiv '{leitmotiv}' en página {page_num}")
        
        # Verificar longitud de versos (aproximado)
        for i, verso in enumerate(versos):
            palabras_verso = len(verso.split())
            if palabras_verso < 3 or palabras_verso > 10:
                issues.append(f"Verso {i+1} parece muy corto o largo ({palabras_verso} palabras)")
        
        return len(issues) == 0, issues
    
    def consolidate_results(self, page_results: List[Dict]) -> Dict[str, Any]:
        """
        Consolida los resultados de todas las páginas en el formato final
        """
        # Ordenar por número de página
        page_results.sort(key=lambda x: x["page_num"])
        
        # Construir el JSON final
        paginas_texto = {}
        leitmotiv_usado_en = []
        qa_scores = []
        total_time = 0
        
        for result in page_results:
            if result["success"]:
                page_num = str(result["page_num"])
                # Unir versos con saltos de línea
                paginas_texto[page_num] = "\n".join(result["versos"])
                
                # Verificar si se usó el leitmotiv
                if result["page_num"] in [2, 5, 10]:
                    leitmotiv_usado_en.append(result["page_num"])
                
                # Agregar QA score
                qa_scores.append(result.get("qa_score", 3.5))
                
                # Sumar tiempo
                total_time += result.get("processing_time", 0)
        
        # Calcular QA promedio
        qa_promedio = sum(qa_scores) / len(qa_scores) if qa_scores else 0
        
        return {
            "paginas_texto": paginas_texto,
            "leitmotiv_usado_en": leitmotiv_usado_en,
            "metadata": {
                "processing_mode": "parallel",
                "pages_processed": len(page_results),
                "pages_successful": len([r for r in page_results if r["success"]]),
                "total_processing_time": total_time,
                "average_qa_score": qa_promedio,
                "timestamp": datetime.now().isoformat()
            }
        }
    
    def save_partial_progress(self, page_num: int, result: Dict):
        """Guarda progreso parcial para monitoreo en tiempo real"""
        story_path = get_story_path(self.story_id)
        partial_file = story_path / "03_cuentacuentos_partial.json"
        
        with self.pages_lock:
            self.pages_completed[page_num] = result
            
            # Escribir archivo parcial
            with open(partial_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "pages_completed": list(self.pages_completed.keys()),
                    "total_pages": 10,
                    "status": "processing",
                    "timestamp": datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=2)
    
    def run(self) -> Dict[str, Any]:
        """
        Ejecuta el procesamiento paralelo de todas las páginas
        
        Returns:
            Diccionario con el resultado consolidado
        """
        logger.info(f"🚀 Iniciando procesamiento paralelo de Cuentacuentos")
        logger.info(f"📊 Configuración: {self.config['max_workers']} workers, {self.config['max_retries_per_page']} reintentos por página")
        
        start_time = time.time()
        page_results = []
        
        # Crear ThreadPool y procesar páginas en paralelo
        with ThreadPoolExecutor(max_workers=self.config["max_workers"]) as executor:
            # Lanzar todas las tareas
            futures = {}
            for page_num in range(1, 11):
                future = executor.submit(self.process_single_page, page_num)
                futures[future] = page_num
            
            # Procesar resultados conforme se completan
            for future in as_completed(futures):
                page_num = futures[future]
                try:
                    result = future.result(timeout=self.config["page_timeout"])
                    page_results.append(result)
                    
                    # Guardar progreso parcial
                    self.save_partial_progress(page_num, result)
                    
                    # Log de progreso
                    if result["success"]:
                        logger.info(f"✅ Página {page_num} completada en {result['processing_time']:.2f}s")
                    else:
                        logger.warning(f"❌ Página {page_num} falló: {result.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    logger.error(f"❌ Error procesando página {page_num}: {e}")
                    page_results.append({
                        "page_num": page_num,
                        "success": False,
                        "error": str(e)
                    })
        
        # Consolidar resultados
        logger.info(f"📦 Consolidando resultados...")
        final_result = self.consolidate_results(page_results)
        
        # Guardar resultado final
        story_path = get_story_path(self.story_id)
        output_file = story_path / "03_cuentacuentos.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(final_result, f, ensure_ascii=False, indent=2)
        
        # Limpiar archivo parcial
        partial_file = story_path / "03_cuentacuentos_partial.json"
        if partial_file.exists():
            partial_file.unlink()
        
        total_time = time.time() - start_time
        logger.info(f"✨ Procesamiento paralelo completado en {total_time:.2f}s")
        logger.info(f"📊 Páginas exitosas: {len([r for r in page_results if r['success']])}/10")
        
        return {
            "status": "completed" if all(r["success"] for r in page_results) else "partial",
            "agent_output": final_result,
            "total_time": total_time,
            "pages_successful": len([r for r in page_results if r["success"]]),
            "pages_failed": len([r for r in page_results if not r["success"]])
        }


# Función de utilidad para testing
def test_parallel_cuentacuentos(story_id: str):
    """Función de prueba para el procesamiento paralelo"""
    processor = ParallelCuentacuentos(story_id)
    return processor.run()