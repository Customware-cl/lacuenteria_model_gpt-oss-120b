"""
Configuración del sistema de orquestación Cuentería
"""
import os
from pathlib import Path

# Rutas base
BASE_DIR = Path(__file__).parent.parent
AGENTES_DIR = BASE_DIR / "agentes"
RUNS_DIR = BASE_DIR / "runs"

# Asegurar que el directorio runs existe
RUNS_DIR.mkdir(exist_ok=True)

# Configuración del modelo LLM local
LLM_CONFIG = {
    "model": "openai/gpt-oss-120b",
    "endpoint": os.getenv("LLM_ENDPOINT", "http://69.19.136.204:8000/v1/chat/completions"),
    "temperature": float(os.getenv("LLM_TEMPERATURE", "0.7")),
    "max_tokens": int(os.getenv("LLM_MAX_TOKENS", "4000")),
    "timeout": int(os.getenv("LLM_TIMEOUT", "60")),
    "retry_attempts": 3,
    "retry_delay": 2
}

# Configuración de la API REST
API_CONFIG = {
    "host": os.getenv("API_HOST", "0.0.0.0"),
    "port": int(os.getenv("API_PORT", "5000")),
    "cors_origins": os.getenv("CORS_ORIGINS", "https://lacuenteria.cl").split(","),
    "debug": os.getenv("DEBUG", "False").lower() == "true"
}

# Umbrales de calidad
QUALITY_THRESHOLDS = {
    "min_qa_score": float(os.getenv("MIN_QA_SCORE", "4.0")),
    "max_retries": int(os.getenv("MAX_RETRIES", "2")),
    "retry_delay": int(os.getenv("RETRY_DELAY", "5"))
}

# Configuración de webhooks
WEBHOOK_CONFIG = {
    "timeout": int(os.getenv("WEBHOOK_TIMEOUT", "30")),
    "max_attempts": int(os.getenv("WEBHOOK_MAX_ATTEMPTS", "3")),
    "retry_delay": int(os.getenv("WEBHOOK_RETRY_DELAY", "10"))
}

# Lista de agentes en orden de ejecución
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

# Temperaturas específicas por agente (sobrescriben la temperatura global)
AGENT_TEMPERATURES = {
    # Agentes creativos - temperatura alta para mayor creatividad
    "director": 0.85,           # Necesita creatividad para el arco narrativo
    "cuentacuentos": 0.9,        # Máxima creatividad para versos líricos
    "diseno_escena": 0.8,        # Creatividad visual
    "direccion_arte": 0.75,      # Balance entre creatividad y coherencia
    "portadista": 0.85,          # Creatividad para títulos memorables
    "loader": 0.9,               # Máxima creatividad para mensajes únicos
    
    # Agentes técnicos - temperatura baja para precisión
    "validador": 0.3,            # Mínima variación, máxima precisión
    "continuidad": 0.4,          # Consistencia estricta en Character Bible
    
    # Agentes de refinamiento - temperatura media
    "editor_claridad": 0.6,      # Balance entre claridad y preservar belleza
    "ritmo_rima": 0.65,          # Ajustes precisos pero con flexibilidad
    "sensibilidad": 0.5,         # Evaluación objetiva de riesgos
    
    # Agentes psicoeducativos - temperatura media-baja
    "psicoeducador": 0.55        # Precisión en recursos pedagógicos
}

# Mapeo de dependencias de agentes (qué archivos necesita cada uno)
AGENT_DEPENDENCIES = {
    "director": ["brief.json"],
    "psicoeducador": ["brief.json", "01_director.json"],
    "cuentacuentos": ["01_director.json", "02_psicoeducador.json"],
    "editor_claridad": ["03_cuentacuentos.json"],
    "ritmo_rima": ["04_editor_claridad.json"],
    "continuidad": ["05_ritmo_rima.json", "brief.json"],
    "diseno_escena": ["05_ritmo_rima.json", "06_continuidad.json"],
    "direccion_arte": ["07_diseno_escena.json", "06_continuidad.json"],
    "sensibilidad": ["05_ritmo_rima.json", "07_diseno_escena.json", "08_direccion_arte.json"],
    "portadista": ["05_ritmo_rima.json", "06_continuidad.json", "08_direccion_arte.json", "01_director.json"],
    "loader": ["10_portadista.json", "brief.json", "01_director.json", "06_continuidad.json", "08_direccion_arte.json"],
    "validador": [f"{str(i).zfill(2)}_{agent}.json" for i, agent in enumerate(AGENT_PIPELINE[:-1], 1)]
}

# Configuración de logging
LOGGING_CONFIG = {
    "level": os.getenv("LOG_LEVEL", "INFO"),
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": "cuenteria.log"
}

# Configuración de procesamiento
PROCESSING_CONFIG = {
    "max_concurrent_stories": int(os.getenv("MAX_CONCURRENT_STORIES", "3")),
    "story_timeout": int(os.getenv("STORY_TIMEOUT", "600")),  # 10 minutos máximo por historia
    "cleanup_after_days": int(os.getenv("CLEANUP_AFTER_DAYS", "30"))
}

# Validación de configuración
def validate_config():
    """Valida que la configuración sea correcta"""
    errors = []
    
    if not AGENTES_DIR.exists():
        errors.append(f"Directorio de agentes no existe: {AGENTES_DIR}")
    
    # Verificar que todos los agentes tienen su archivo JSON
    for agent in AGENT_PIPELINE:
        agent_file = AGENTES_DIR / f"{agent}.json"
        if not agent_file.exists():
            errors.append(f"Archivo de agente no encontrado: {agent_file}")
    
    if errors:
        raise ValueError("Errores de configuración:\n" + "\n".join(errors))
    
    return True

# Función para obtener la ruta de un agente
def get_agent_prompt_path(agent_name):
    """Retorna la ruta al archivo JSON del agente"""
    return AGENTES_DIR / f"{agent_name}.json"

# Función para obtener la ruta de una historia
def get_story_path(story_id):
    """Retorna la ruta al directorio de una historia"""
    return RUNS_DIR / story_id

# Función para obtener la ruta de un artefacto
def get_artifact_path(story_id, artifact_name):
    """Retorna la ruta a un artefacto específico de una historia"""
    return get_story_path(story_id) / artifact_name