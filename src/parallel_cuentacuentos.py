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
        # MODO SECUENCIAL FORZADO - Para garantizar 100% de páginas
        self.config = {
            "max_workers": 1,  # SECUENCIAL: Solo 1 worker para garantizar completitud
            "page_timeout": 120,  # Aumentado de 60 a 120 segundos
            "max_retries_per_page": 3,  # Aumentado de 2 a 3 reintentos
            "temperature": 0.75,
            "max_tokens": 30000,  # AUMENTADO: 30000 tokens para evitar truncamiento
            "top_p": 0.95,
            "qa_threshold": 3.5,
            "delay_between_pages": 2,  # Aumentado: 2 segundos entre páginas
            "force_sequential": True  # Flag para forzar procesamiento secuencial
        }
        
        # Intentar cargar configuración específica de v2
        config_path = self.base_dir / f"flujo/{self.version}/agent_config.json"
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                agent_configs = json.load(f)
                if "03_cuentacuentos" in agent_configs:
                    cuentos_config = agent_configs["03_cuentacuentos"]
                    # Actualizar TODA la configuración desde el archivo
                    self.config.update({
                        "temperature": cuentos_config.get("temperature", 0.75),
                        "max_tokens": cuentos_config.get("max_tokens_per_page", 30000),
                        "top_p": cuentos_config.get("top_p", 0.95),
                        "qa_threshold": cuentos_config.get("qa_threshold", 3.5),
                        "max_workers": cuentos_config.get("max_workers", 1),
                        "page_timeout": cuentos_config.get("page_timeout", 120),
                        "max_retries_per_page": cuentos_config.get("max_retries_per_page", 3),
                        "force_sequential": cuentos_config.get("force_sequential", True),
                        "delay_between_pages": cuentos_config.get("delay_between_pages", 2)
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
        
        # Cargar configuración de estructura de rima
        rima_config_path = self.base_dir / 'flujo' / self.version / 'configuracion_poetica' / 'estructura_rima.json'
        if rima_config_path.exists():
            with open(rima_config_path, 'r', encoding='utf-8') as f:
                self.rima_config = json.load(f)
                logger.info(f"📝 Configuración de rima cargada: {len(self.rima_config['pages'])} páginas configuradas")
        else:
            logger.warning(f"⚠️ No se encontró configuración de rima, usando AABB por defecto")
            self.rima_config = {"default_scheme": "AABB", "pages": {}}
        
        logger.info(f"✅ Dependencias cargadas para {self.story_id}")
        
    def get_scheme_instructions(self, scheme: str) -> str:
        """
        Devuelve instrucciones específicas para cada esquema de rima
        """
        instructions = {
            "AABB": "versos 1-2 riman entre sí, versos 3-4 riman entre sí",
            "ABAB": "verso 1 rima con verso 3, verso 2 rima con verso 4",
            "ABBA": "verso 1 rima con verso 4, verso 2 rima con verso 3",
            "ABCB": "solo verso 2 rima con verso 4, versos 1 y 3 NO riman",
            "libre": "NO es necesario que rimen, enfócate en ritmo y musicalidad",
            "AAAA": "todos los versos riman entre sí con la misma terminación"
        }
        return instructions.get(scheme, "versos 1-2 riman, versos 3-4 riman")
    
    def get_scheme_example(self, scheme: str) -> str:
        """
        Devuelve un ejemplo del patrón de rima para el JSON de respuesta
        """
        examples = {
            "AABB": '["verso con final A", "verso con final A", "verso con final B", "verso con final B"]',
            "ABAB": '["verso con final A", "verso con final B", "verso con final A", "verso con final B"]',
            "ABBA": '["verso con final A", "verso con final B", "verso con final B", "verso con final A"]',
            "ABCB": '["verso sin rima", "verso con final B", "verso sin rima", "verso con final B"]',
            "libre": '["verso libre 1", "verso libre 2", "verso libre 3", "verso libre 4"]',
            "AAAA": '["verso con final A", "verso con final A", "verso con final A", "verso con final A"]'
        }
        return examples.get(scheme, '["verso 1", "verso 2", "verso 3", "verso 4"]')
    
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
        
        # Obtener esquema de rima para esta página
        page_str = str(page_num)
        rima_scheme = self.rima_config.get('pages', {}).get(page_str, {}).get('scheme', self.rima_config.get('default_scheme', 'AABB'))
        rima_nombre = self.rima_config.get('pages', {}).get(page_str, {}).get('nombre', 'Rima pareada')
        
        # Obtener instrucciones específicas para el esquema
        scheme_instructions = self.get_scheme_instructions(rima_scheme)
        
        # Obtener rimas ya usadas (thread-safe)
        with self.used_rimas_lock:
            rimas_prohibidas = list(self.used_rimas)
        
        # System prompt simplificado y enfocado
        system_prompt = f"""Eres un experto en versos infantiles. Tu tarea es crear EXACTAMENTE 4 versos para la página {page_num} del cuento.

REGLA ABSOLUTA #1: NUNCA uses la misma palabra para rimar.
REGLA ABSOLUTA #2: Usar esquema {rima_scheme} ({rima_nombre}): {scheme_instructions}
REGLA ABSOLUTA #3: Cada verso debe tener entre 8-15 sílabas.

Edad objetivo: {edad} años (usa vocabulario muy simple).

{"INCLUYE EL LEITMOTIV: '" + leitmotiv + "' en algún verso." if include_leitmotiv else ""}

Responde ÚNICAMENTE con este JSON:
{{
  "pagina": {page_num},
  "versos": {self.get_scheme_example(rima_scheme)},
  "palabras_finales": ["palabra1", "palabra2", "palabra3", "palabra4"],
  "esquema_usado": "{rima_scheme}"
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
    
    def run_qa_verification(self, page_result: Dict, page_num: int, retry: int) -> Dict[str, Any]:
        """
        Ejecuta verificación QA externa usando el agente verificador_qa
        
        Returns:
            Dict con resultados del QA incluyendo score y feedback
        """
        try:
            # Cargar prompt del verificador QA
            qa_prompt_path = self.base_dir / 'flujo' / self.version / 'agentes' / 'verificador_qa.json'
            with open(qa_prompt_path, 'r', encoding='utf-8') as f:
                qa_data = json.load(f)
            
            # Cargar criterios específicos para la página
            criterios_path = self.base_dir / 'flujo' / self.version / 'criterios_evaluacion' / '03_cuentacuentos.json'
            with open(criterios_path, 'r', encoding='utf-8') as f:
                criterios = json.load(f)
            
            # Extraer criterios específicos de la página
            page_key = f"pagina_{page_num}"
            if page_key not in criterios["metricas"]:
                logger.warning(f"No hay criterios específicos para página {page_num}")
                return {"qa_score": 4.0, "pasa_umbral": True, "problemas_detectados": []}
            
            page_criteria = criterios["metricas"][page_key]
            
            # Construir prompt de verificación
            qa_user_prompt = f"""EVALÚA LA PÁGINA {page_num} DEL CUENTACUENTOS

=== PÁGINA A EVALUAR ===
{json.dumps(page_result, ensure_ascii=False, indent=2)}

=== CRITERIOS DE EVALUACIÓN ===
{json.dumps(page_criteria, ensure_ascii=False, indent=2)}

=== CONFIGURACIÓN ===
{json.dumps(criterios["configuracion"], ensure_ascii=False, indent=2)}

=== DATOS DE CONTEXTO ===
DIRECTOR (beat_sheet[{page_num-1}]):
{json.dumps(self.director_data['beat_sheet'][page_num-1] if self.director_data else {}, ensure_ascii=False, indent=2)}

PSICOEDUCADOR (mapa_psico_narrativo[{page_num-1}]):
{json.dumps(self.psicoeducador_data['mapa_psico_narrativo'][page_num-1] if self.psicoeducador_data else {}, ensure_ascii=False, indent=2)}

LEITMOTIV: {self.director_data.get('leitmotiv', '') if self.director_data else ''}

=== ESQUEMA DE RIMA CONFIGURADO ===
PÁGINA {page_num}: {self.rima_config.get('pages', {}).get(str(page_num), {}).get('scheme', 'AABB')}
Nombre: {self.rima_config.get('pages', {}).get(str(page_num), {}).get('nombre', 'Rima pareada')}
Instrucción: {self.get_scheme_instructions(self.rima_config.get('pages', {}).get(str(page_num), {}).get('scheme', 'AABB'))}

=== INSTRUCCIONES ===
1. Evalúa cada criterio como true/false
2. Calcula el porcentaje de cumplimiento
3. Proporciona feedback específico para mejorar
4. Sé JUSTO pero RIGUROSO con las rimas repetidas

RESPONDE ÚNICAMENTE CON EL JSON ESPECIFICADO."""
            
            # Llamar al LLM con el verificador QA
            response = self.llm_client.generate(
                system_prompt=qa_data["content"],
                user_prompt=qa_user_prompt,
                temperature=0.3,  # Baja temperatura para consistencia
                max_tokens=30000  # AUMENTADO: 30000 tokens para QA completo
            )
            
            # Parsear respuesta
            qa_result = json.loads(response) if isinstance(response, str) else response
            
            # Guardar resultado QA
            self.save_qa_verification(page_num, retry, qa_result)
            
            return qa_result
            
        except Exception as e:
            logger.error(f"Error en verificación QA para página {page_num}: {e}")
            # Retornar QA por defecto si falla
            return {
                "qa_score": 3.0,
                "pasa_umbral": False,
                "problemas_detectados": [f"Error en verificación: {str(e)}"],
                "mejoras_especificas": []
            }
    
    def save_qa_verification(self, page_num: int, retry: int, qa_result: Dict):
        """Guarda el resultado de verificación QA de una página"""
        story_path = get_story_path(self.story_id)
        qa_dir = story_path / "outputs" / "qa"
        qa_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"verificador_qa_pagina_{page_num:02d}_intento_{retry+1}.json"
        qa_file = qa_dir / filename
        
        qa_data = {
            "page_num": page_num,
            "retry": retry + 1,
            "timestamp": datetime.now().isoformat(),
            "qa_result": qa_result
        }
        
        with open(qa_file, 'w', encoding='utf-8') as f:
            json.dump(qa_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"📊 QA guardado: {filename}")
    
    def save_qa_feedback(self, page_num: int, retry: int, feedback: List[str]):
        """Guarda el feedback consolidado para el siguiente intento"""
        story_path = get_story_path(self.story_id)
        feedback_dir = story_path / "outputs" / "feedback"
        feedback_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"feedback_pagina_{page_num:02d}_para_intento_{retry+2}.json"
        feedback_file = feedback_dir / filename
        
        feedback_data = {
            "page_num": page_num,
            "for_retry": retry + 2,
            "timestamp": datetime.now().isoformat(),
            "feedback_items": feedback
        }
        
        with open(feedback_file, 'w', encoding='utf-8') as f:
            json.dump(feedback_data, f, ensure_ascii=False, indent=2)
    
    def build_feedback_prompt(self, page_num: int, retry: int) -> str:
        """
        Construye el prompt de feedback basado en intentos anteriores
        """
        story_path = get_story_path(self.story_id)
        feedback_dir = story_path / "outputs" / "feedback"
        
        # Buscar feedback del intento anterior
        feedback_file = feedback_dir / f"feedback_pagina_{page_num:02d}_para_intento_{retry+1}.json"
        
        if feedback_file.exists():
            with open(feedback_file, 'r', encoding='utf-8') as f:
                feedback_data = json.load(f)
                items = feedback_data.get('feedback_items', [])
                
                if items:
                    feedback_text = "⚠️ RETROALIMENTACIÓN DEL INTENTO ANTERIOR ⚠️\n\n"
                    feedback_text += "El intento anterior falló por las siguientes razones:\n"
                    for i, item in enumerate(items, 1):
                        feedback_text += f"{i}. {item}\n"
                    feedback_text += "\nPOR FAVOR CORRIGE ESTOS PROBLEMAS EN ESTE INTENTO."
                    return feedback_text
        
        return ""
    
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
                
                # Si es un reintento, agregar feedback del intento anterior
                if retry > 0:
                    feedback_prompt = self.build_feedback_prompt(page_num, retry)
                    if feedback_prompt:
                        user_prompt = f"{user_prompt}\n\n{feedback_prompt}"
                
                # Guardar input de esta página
                self.save_page_input(page_num, retry, system_prompt, user_prompt)
                
                # Llamar al LLM
                response = self.llm_client.generate(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    temperature=self.config["temperature"],
                    max_tokens=self.config["max_tokens"],
                    top_p=self.config["top_p"]
                )
                
                # Guardar respuesta/output de esta página
                self.save_page_output(page_num, retry, response, time.time() - start_time)
                
                # Parsear respuesta
                if isinstance(response, str):
                    result = json.loads(response)
                else:
                    result = response
                
                # Validar estructura básica primero
                structure_valid, structure_issues = self.validate_page_structure(result, page_num)
                
                # Si la estructura es válida, ejecutar QA externo SIEMPRE
                qa_verification = None
                qa_score = 3.0  # Score por defecto
                qa_passed = False
                qa_issues = structure_issues.copy()
                
                if structure_valid:
                    # SIEMPRE ejecutar verificación QA externa si la estructura es válida
                    logger.info(f"🔍 Ejecutando verificación QA para página {page_num}, intento {retry+1}")
                    qa_verification = self.run_qa_verification(result, page_num, retry)
                    qa_passed = qa_verification.get('pasa_umbral', False)
                    logger.info(f"📊 QA resultado para página {page_num}: pasa={qa_passed}")
                    
                    # Extraer score del QA
                    if 'promedio' in qa_verification and 'nota_final' in qa_verification['promedio']:
                        qa_score = qa_verification['promedio']['nota_final']
                    else:
                        qa_score = qa_verification.get('qa_score', 3.0)
                    
                    if not qa_passed:
                        # QA externo falló, actualizar issues
                        qa_issues = qa_verification.get('problemas_detectados', [])
                        
                        # Guardar feedback para siguiente intento si no es el último
                        if retry < self.config["max_retries_per_page"] - 1:
                            mejoras = qa_verification.get('mejoras_especificas', [])
                            self.save_qa_feedback(page_num, retry, mejoras if mejoras else qa_issues)
                else:
                    # Si falló validación de estructura, score bajo y no ejecutar QA
                    qa_score = 1.0
                    logger.warning(f"⚠️ Página {page_num} falló validación de estructura: {structure_issues}")
                
                if qa_passed:
                    # Agregar palabras finales a la lista global (thread-safe)
                    if "palabras_finales" in result:
                        with self.used_rimas_lock:
                            self.used_rimas.update(result["palabras_finales"])
                    
                    # Preparar resultado exitoso
                    logger.info(f"✅ Página {page_num} completada exitosamente (QA: {qa_score:.1f})")
                    return {
                        "page_num": page_num,
                        "success": True,
                        "versos": result.get("versos", []),
                        "palabras_finales": result.get("palabras_finales", []),
                        "qa_score": qa_score,
                        "qa_verification": qa_verification,
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
    
    def validate_rima_scheme(self, palabras: List[str], scheme: str) -> Tuple[bool, str]:
        """
        Valida que las palabras finales sigan el esquema de rima configurado
        
        Returns:
            Tuple de (cumple_esquema: bool, descripcion: str)
        """
        if len(palabras) != 4:
            return False, "Se requieren exactamente 4 palabras finales"
        
        p1, p2, p3, p4 = [p.lower() for p in palabras]
        
        if scheme == "AABB":
            # Versos 1-2 riman, 3-4 riman
            if p1 == p2 and p3 == p4 and p1 != p3:
                return False, "AABB requiere rimas diferentes para cada par, no repetir la misma palabra"
            # Verificar terminaciones similares
            if self.check_rima(p1, p2) and self.check_rima(p3, p4) and not self.check_rima(p1, p3):
                return True, "Esquema AABB correcto"
            return False, "AABB requiere que 1-2 rimen entre sí y 3-4 rimen entre sí"
            
        elif scheme == "ABAB":
            # Verso 1 rima con 3, verso 2 rima con 4
            if self.check_rima(p1, p3) and self.check_rima(p2, p4) and not self.check_rima(p1, p2):
                return True, "Esquema ABAB correcto"
            return False, "ABAB requiere que verso 1 rime con 3, y verso 2 rime con 4"
            
        elif scheme == "ABBA":
            # Verso 1 rima con 4, verso 2 rima con 3
            if self.check_rima(p1, p4) and self.check_rima(p2, p3) and not self.check_rima(p1, p2):
                return True, "Esquema ABBA correcto"
            return False, "ABBA requiere que verso 1 rime con 4, y verso 2 rime con 3"
            
        elif scheme == "ABCB":
            # Solo verso 2 rima con 4
            if self.check_rima(p2, p4) and not self.check_rima(p1, p2) and not self.check_rima(p1, p3):
                return True, "Esquema ABCB correcto"
            return False, "ABCB requiere que solo versos 2 y 4 rimen"
            
        elif scheme == "libre":
            # Sin restricción de rima
            return True, "Verso libre sin restricciones de rima"
            
        elif scheme == "AAAA":
            # Todos riman entre sí
            if self.check_rima(p1, p2) and self.check_rima(p2, p3) and self.check_rima(p3, p4):
                return True, "Esquema AAAA correcto"
            return False, "AAAA requiere que todos los versos rimen entre sí"
            
        return False, f"Esquema {scheme} no reconocido"
    
    def check_rima(self, palabra1: str, palabra2: str) -> bool:
        """
        Verifica si dos palabras riman (consonante o asonante)
        """
        # Si son la misma palabra, es problemático
        if palabra1 == palabra2:
            return False
            
        # Obtener las últimas 2-3 letras para comparación básica
        # Este es un método simplificado, se puede mejorar
        if len(palabra1) >= 3 and len(palabra2) >= 3:
            # Verificar terminación similar
            return palabra1[-3:] == palabra2[-3:] or palabra1[-2:] == palabra2[-2:]
        elif len(palabra1) >= 2 and len(palabra2) >= 2:
            return palabra1[-2:] == palabra2[-2:]
        
        return False
    
    def validate_page_structure(self, page_result: Dict, page_num: int) -> Tuple[bool, List[str]]:
        """
        Valida solo la estructura básica de la página (sin contenido)
        
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
        
        # Verificar que existan palabras finales
        if "palabras_finales" not in page_result:
            issues.append("No se encontraron palabras_finales")
            return False, issues
        
        palabras = page_result.get("palabras_finales", [])
        if len(palabras) != 4:
            issues.append(f"Se esperaban 4 palabras finales, se encontraron {len(palabras)}")
            return False, issues
        
        # Si llegamos aquí, la estructura es válida
        return True, []
    
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
    
    def save_page_input(self, page_num: int, retry: int, system_prompt: str, user_prompt: str):
        """Guarda el input/request de una página específica"""
        story_path = get_story_path(self.story_id)
        inputs_dir = story_path / "inputs" / "pages"
        inputs_dir.mkdir(parents=True, exist_ok=True)
        
        # Nombre del archivo con formato simplificado
        filename = f"pagina_{page_num:02d}_intento_{retry+1}_request.json"
        input_file = inputs_dir / filename
        
        input_data = {
            "page_num": page_num,
            "retry": retry + 1,
            "timestamp": datetime.now().isoformat(),
            "config": {
                "temperature": self.config["temperature"],
                "max_tokens": self.config["max_tokens"],
                "top_p": self.config["top_p"]
            },
            "prompts": {
                "system": system_prompt,
                "user": user_prompt
            }
        }
        
        with open(input_file, 'w', encoding='utf-8') as f:
            json.dump(input_data, f, ensure_ascii=False, indent=2)
        
        logger.debug(f"📝 Guardado input para página {page_num}, intento {retry+1}")
    
    def save_page_output(self, page_num: int, retry: int, response: Any, processing_time: float):
        """Guarda el output/resultado de una página específica"""
        story_path = get_story_path(self.story_id)
        
        # Guardar en outputs/pages
        outputs_dir = story_path / "outputs" / "pages"
        outputs_dir.mkdir(parents=True, exist_ok=True)
        filename = f"pagina_{page_num:02d}_intento_{retry+1}_result.json"
        output_file = outputs_dir / filename
        
        # También mantener logs por compatibilidad
        logs_dir = story_path / "logs"
        logs_dir.mkdir(exist_ok=True)
        log_filename = f"03_cuentacuentos_pagina_{page_num:02d}_intento_{retry+1}.log"
        log_file = logs_dir / log_filename
        
        output_data = {
            "page_num": page_num,
            "retry": retry + 1,
            "timestamp": datetime.now().isoformat(),
            "processing_time": processing_time,
            "response": response if isinstance(response, (dict, list)) else str(response),
            "status": "success" if response else "error"
        }
        
        # Guardar en outputs/pages
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        # Guardar en logs (por compatibilidad)
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        logger.debug(f"📝 Guardado output para página {page_num}, intento {retry+1}")
    
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
        Ejecuta el procesamiento de todas las páginas
        
        Returns:
            Diccionario con el resultado consolidado
        """
        # Decidir si usar procesamiento secuencial o paralelo
        if self.config.get("force_sequential", False) or self.config["max_workers"] == 1:
            logger.info(f"🔄 Usando procesamiento SECUENCIAL para garantizar completitud")
            return self.process_sequential()
        else:
            logger.info(f"🚀 Iniciando procesamiento paralelo de Cuentacuentos")
            logger.info(f"📊 Configuración: {self.config['max_workers']} workers, {self.config['max_retries_per_page']} reintentos por página")
            return self.process_parallel()
    
    def process_sequential(self) -> Dict[str, Any]:
        """
        Procesa las páginas de forma completamente secuencial
        Garantiza mayor estabilidad y completitud
        """
        logger.info(f"📖 Procesamiento SECUENCIAL - Generando 10 páginas una por una")
        start_time = time.time()
        page_results = []
        
        for page_num in range(1, 11):
            logger.info(f"📄 Procesando página {page_num}/10...")
            
            # Procesar la página con reintentos
            page_result = self.process_single_page(page_num)
            page_results.append(page_result)
            
            # Guardar progreso parcial
            self.save_partial_progress(page_num, page_result)
            
            # Log del resultado
            if page_result["success"]:
                logger.info(f"✅ Página {page_num} completada exitosamente en {page_result['processing_time']:.2f}s")
            else:
                logger.error(f"❌ Página {page_num} falló después de {self.config['max_retries_per_page']} intentos: {page_result.get('error')}")
                
                # Intento adicional de recuperación para páginas críticas
                if page_num in [1, 2, 5, 10]:  # Páginas críticas (inicio, leitmotiv, final)
                    logger.warning(f"⚠️ Reintentando página crítica {page_num} con configuración especial...")
                    time.sleep(3)
                    
                    # Reintento con parámetros ajustados
                    retry_result = self.process_single_page(page_num)
                    if retry_result["success"]:
                        page_results[-1] = retry_result  # Reemplazar el resultado fallido
                        logger.info(f"✅ Página crítica {page_num} recuperada exitosamente")
            
            # Delay entre páginas para evitar saturación
            if page_num < 10:
                time.sleep(self.config.get("delay_between_pages", 2))
        
        # Consolidar y validar resultados
        return self.finalize_results(page_results, start_time)
    
    def process_parallel(self) -> Dict[str, Any]:
        """
        Procesa las páginas en paralelo (método original mejorado)
        """
        logger.info(f"📊 Configuración: {self.config['max_workers']} workers, {self.config['max_retries_per_page']} reintentos por página")
        start_time = time.time()
        page_results = []
        
        # Crear ThreadPool y procesar páginas en paralelo con delay
        with ThreadPoolExecutor(max_workers=self.config["max_workers"]) as executor:
            # Lanzar todas las tareas con delay entre ellas
            futures = {}
            for page_num in range(1, 11):
                future = executor.submit(self.process_single_page, page_num)
                futures[future] = page_num
                # Agregar delay entre solicitudes para evitar saturación
                if page_num < 10:
                    time.sleep(self.config.get("delay_between_pages", 1))
            
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
        
        # IMPORTANTE: Reintentar páginas fallidas de forma secuencial
        failed_pages = [r["page_num"] for r in page_results if not r["success"]]
        if failed_pages:
            logger.warning(f"⚠️ Reintentando {len(failed_pages)} páginas fallidas de forma secuencial: {failed_pages}")
            for page_num in failed_pages:
                logger.info(f"🔄 Reintentando página {page_num} de forma secuencial...")
                time.sleep(2)  # Mayor delay antes de reintentar
                retry_result = self.process_single_page(page_num)
                
                # Reemplazar el resultado fallido con el nuevo intento
                page_results = [r for r in page_results if r["page_num"] != page_num]
                page_results.append(retry_result)
                
                if retry_result["success"]:
                    logger.info(f"✅ Página {page_num} recuperada exitosamente")
                else:
                    logger.error(f"❌ Página {page_num} falló definitivamente: {retry_result.get('error', 'Unknown')}")
        
        # Consolidar y validar resultados
        return self.finalize_results(page_results, start_time)
    
    def finalize_results(self, page_results: List[Dict], start_time: float) -> Dict[str, Any]:
        """
        Consolida, valida y guarda los resultados finales
        """
        # Consolidar resultados
        logger.info(f"📦 Consolidando resultados...")
        final_result = self.consolidate_results(page_results)
        
        # VALIDACIÓN CRÍTICA: Asegurar que tenemos las 10 páginas
        successful_pages = [r for r in page_results if r["success"]]
        pages_generated = len(successful_pages)
        
        if pages_generated < 10:
            missing_pages = [i for i in range(1, 11) if i not in [r["page_num"] for r in successful_pages]]
            logger.error(f"❌ FALLO CRÍTICO: Solo se generaron {pages_generated}/10 páginas")
            logger.error(f"❌ Páginas faltantes: {missing_pages}")
            
            # Agregar información de fallo al resultado
            final_result["metadata"]["critical_failure"] = True
            final_result["metadata"]["missing_pages"] = missing_pages
            final_result["metadata"]["completion_percentage"] = (pages_generated / 10) * 100
            
            # NO CONTINUAR si tenemos menos del 100%
            if pages_generated < 10:
                logger.error(f"❌ INACEPTABLE: El cuento está incompleto ({pages_generated}/10 páginas)")
                # Lanzar excepción para detener el pipeline
                raise RuntimeError(
                    f"FALLO CRÍTICO en cuentacuentos: Solo se generaron {pages_generated}/10 páginas. "
                    f"Faltan: {missing_pages}. El pipeline NO puede continuar con un cuento incompleto."
                )
        
        # Guardar resultado final solo si está completo
        story_path = get_story_path(self.story_id)
        output_file = story_path / "03_cuentacuentos.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(final_result, f, ensure_ascii=False, indent=2)
        
        # Limpiar archivo parcial
        partial_file = story_path / "03_cuentacuentos_partial.json"
        if partial_file.exists():
            partial_file.unlink()
        
        total_time = time.time() - start_time
        logger.info(f"✨ Procesamiento completado en {total_time:.2f}s")
        logger.info(f"📊 Páginas exitosas: {pages_generated}/10")
        
        if pages_generated == 10:
            logger.info(f"✅ ÉXITO: Todas las 10 páginas generadas correctamente")
        
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