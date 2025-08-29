"""
Configuración central del sistema Cuentería
"""
import os
from pathlib import Path
import json

# Paths base del proyecto
BASE_DIR = Path(__file__).parent.parent
AGENTES_DIR = BASE_DIR / "agentes"
RUNS_DIR = BASE_DIR / "runs"

# Asegurar que el directorio runs existe
RUNS_DIR.mkdir(exist_ok=True)

# Configuración del modelo LLM
LLM_CONFIG = {
    "api_url": os.getenv("LLM_API_URL", "http://69.19.136.204:8000/v1/chat/completions"),
    "model": os.getenv("LLM_MODEL", "openai/gpt-oss-120b"),
    "temperature": float(os.getenv("LLM_TEMPERATURE", "0.7")),
    "max_tokens": int(os.getenv("LLM_MAX_TOKENS", "20000")),
    "timeout": int(os.getenv("LLM_TIMEOUT", "900")),
    "retry_attempts": int(os.getenv("LLM_RETRY_ATTEMPTS", "3")),
    "retry_delay": int(os.getenv("LLM_RETRY_DELAY", "2"))
}

# Configuración de la API
API_CONFIG = {
    "host": os.getenv("API_HOST", "0.0.0.0"),
    "port": int(os.getenv("API_PORT", "5000")),
    "debug": os.getenv("API_DEBUG", "False").lower() == "true",
    "cors_origins": os.getenv("CORS_ORIGINS", "https://lacuenteria.cl").split(","),
    "max_content_length": int(os.getenv("MAX_CONTENT_LENGTH", "16777216"))  # 16MB
}

# Umbrales de calidad
QUALITY_THRESHOLDS = {
    "min_qa_score": float(os.getenv("MIN_QA_SCORE", "4.0")),
    "max_retries": int(os.getenv("MAX_RETRIES", "2")),
    "retry_delay": int(os.getenv("RETRY_DELAY", "5"))
}

# Umbrales de calidad específicos por agente (override del global)
AGENT_QA_THRESHOLDS = {
    "03_cuentacuentos": 4.0,  # Cuentacuentos requiere mínimo 4.0
    "01_director": 3.5,
    "02_psicoeducador": 3.5,
    "04_editor_claridad": 3.5,
    "05_ritmo_rima": 3.5,
    "06_continuidad": 3.5,
    "07_diseno_escena": 3.5,
    "08_direccion_arte": 3.5,
    "09_sensibilidad": 4.0,  # Sensibilidad también requiere 4.0
    "10_portadista": 3.5,
    "11_loader": 3.5,
    "12_validador": 4.0  # Validador requiere 4.0
}

# Configuración de webhooks
WEBHOOK_CONFIG = {
    "timeout": int(os.getenv("WEBHOOK_TIMEOUT", "30")),
    "max_retries": int(os.getenv("WEBHOOK_RETRIES", "3")),
    "retry_delay": int(os.getenv("WEBHOOK_RETRY_DELAY", "1"))
}

# Pipeline de agentes
AGENT_PIPELINE = [
    "director",
    "psicoeducador",
    "cuentacuentos",
    "editor_claridad",
    "ritmo_rima",
    "continuidad",
    "diseno_escena",
    "direccion_arte",
    "sensibilidad",
    "portadista",
    "loader",
    "validador"
]

# ========== CONFIGURACIÓN DE MAX_TOKENS POR AGENTE ==========
# Como usamos un modelo local sin costos, damos libertad de tokens a todos
AGENT_MAX_TOKENS = {
    # v1 - nombres sin números (para compatibilidad)
    "director": 20000,
    "psicoeducador": 20000,
    "cuentacuentos": 20000,
    "editor_claridad": 20000,
    "ritmo_rima": 20000,
    "continuidad": 20000,
    "diseno_escena": 20000,
    "direccion_arte": 20000,
    "sensibilidad": 20000,
    "portadista": 20000,
    "loader": 20000,
    "validador": 20000,
    "critico": 20000,
    "verificador_qa": 30000,  # Masivo para evaluación
    
    # v2 - nombres con números (nuevos)
    "01_director": 20000,
    "02_psicoeducador": 20000,
    "03_cuentacuentos": 20000,
    "04_editor_claridad": 20000,
    "05_ritmo_rima": 20000,
    "06_continuidad": 20000,
    "07_diseno_escena": 20000,
    "08_direccion_arte": 20000,
    "09_sensibilidad": 20000,
    "10_portadista": 20000,
    "11_loader": 20000,
    "12_validador": 20000,
    "13_critico": 20000,
    "14_verificador_qa": 30000  # Masivo para evaluación
}

# Configuración de temperaturas específicas por agente
AGENT_TEMPERATURES = {
    "director": 0.7,
    "psicoeducador": 0.5,
    "cuentacuentos": 0.9,
    "editor_claridad": 0.3,
    "ritmo_rima": 0.5,
    "continuidad": 0.5,
    "diseno_escena": 0.8,
    "direccion_arte": 0.8,
    "sensibilidad": 0.3,
    "portadista": 0.7,
    "loader": 0.8,
    "validador": 0.3,
    "critico": 0.3,
}

# Dependencias entre agentes (qué artefactos necesita cada uno)
AGENT_DEPENDENCIES = {
    "director": ["brief.json"],
    "psicoeducador": ["brief.json", "director.json"],
    "cuentacuentos": ["director.json", "psicoeducador.json"],
    "editor_claridad": ["cuentacuentos.json"],
    "ritmo_rima": ["editor_claridad.json"],
    "continuidad": ["ritmo_rima.json", "brief.json"],
    "diseno_escena": ["ritmo_rima.json", "continuidad.json"],
    "direccion_arte": ["diseno_escena.json", "continuidad.json"],
    "sensibilidad": ["ritmo_rima.json", "diseno_escena.json", "direccion_arte.json"],
    "portadista": ["ritmo_rima.json", "continuidad.json", "direccion_arte.json", "director.json"],
    "loader": ["portadista.json", "brief.json", "director.json", "continuidad.json", "direccion_arte.json"],
    "validador": ["ritmo_rima.json", "direccion_arte.json", "sensibilidad.json", "portadista.json", "loader.json"],
    "critico": ["validador.json"]
}

# Configuración de logging
LOGGING_CONFIG = {
    "level": os.getenv("LOG_LEVEL", "INFO"),
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": os.getenv("LOG_FILE", "cuenteria.log")
}

# Configuración de procesamiento
PROCESSING_CONFIG = {
    "max_story_time": int(os.getenv("MAX_STORY_TIME", "600")),  # 10 minutos máximo por historia
    "cleanup_after_days": int(os.getenv("CLEANUP_AFTER_DAYS", "7")),  # Limpiar historias después de 7 días
    "enable_caching": os.getenv("ENABLE_CACHING", "True").lower() == "true"
}

# Validación de configuración
def validate_config():
    """Valida que la configuración sea correcta"""
    errors = []
    
    # Validar que todos los agentes del pipeline tienen dependencias definidas
    for agent in AGENT_PIPELINE:
        if agent not in AGENT_DEPENDENCIES:
            errors.append(f"Agente '{agent}' no tiene dependencias definidas")
    
    if errors:
        raise ValueError("Errores de configuración:\n" + "\n".join(errors))
    
    return True

# Función para obtener la ruta de una historia
def get_story_path(story_id):
    """Retorna la ruta al directorio de una historia"""
    return RUNS_DIR / story_id

# Función para obtener la ruta de un artefacto
def get_artifact_path(story_id, artifact_name):
    """Retorna la ruta a un artefacto específico de una historia"""
    return get_story_path(story_id) / artifact_name

# Función para obtener la ruta del prompt de un agente
def get_agent_prompt_path(agent_name, version='v1'):
    """Retorna la ruta al archivo de prompt de un agente"""
    if version == 'v1':
        return AGENTES_DIR / f"{agent_name}.json"
    else:
        return BASE_DIR / f"flujo/{version}/agentes/{agent_name}.json"

# ========== FUNCIONES DE VERSIONADO ==========

def load_version_config(version='v1'):
    """Carga configuración específica de versión"""
    if version == 'v1':
        # v1 usa configuración actual hardcodeada para no romper nada
        return {
            'version': 'v1',
            'agents_path': 'agentes',  # Path actual de producción
            'qa_threshold': QUALITY_THRESHOLDS['min_qa_score'],
            'max_retries': QUALITY_THRESHOLDS['max_retries'],
            'max_tokens': LLM_CONFIG['max_tokens'],
            'temperature': LLM_CONFIG['temperature'],
            'pipeline': AGENT_PIPELINE,
            'parallel_execution': False,
            'dependencies': AGENT_DEPENDENCIES,  # Usar dependencias hardcodeadas
            'agent_qa_thresholds': {}  # v1 no usa umbrales específicos
        }
    else:
        # v2+ usa config desde archivo JSON
        config_path = BASE_DIR / f'flujo/{version}/config.json'
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # Agregar path de agentes
                config['agents_path'] = f'flujo/{version}/agentes'
                
                # Cargar dependencies.json si existe
                deps_path = BASE_DIR / f'flujo/{version}/dependencies.json'
                if deps_path.exists():
                    with open(deps_path, 'r', encoding='utf-8') as f:
                        config['dependencies'] = json.load(f)
                else:
                    config['dependencies'] = {}
                    
                # Agregar umbrales QA específicos para v2
                config['agent_qa_thresholds'] = AGENT_QA_THRESHOLDS
                
                return config
        else:
            raise ValueError(f"No se encontró configuración para versión {version}")

# Ejecutar validación al importar el módulo
validate_config()