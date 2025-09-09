# Plan de Manejo de Payloads desde lacuenteria.cl

## Situación Actual

### Payload Actual Soportado
```json
{
  "story_id": "identificador-único",
  "personajes": ["lista", "de", "personajes"],
  "historia": "trama principal",
  "mensaje_a_transmitir": "objetivo educativo",
  "edad_objetivo": 5,
  "pipeline_version": "v3",  // Opcional: v1, v2, v3
  "webhook_url": "https://lacuenteria.cl/webhook",
  "mode_verificador_qa": true,  // Opcional
  "prompt_metrics_id": "uuid-metrics",  // Opcional
  "pipeline_request_id": "uuid-request"  // Opcional
}
```

### Problema Identificado
- **NO existe** campo para especificar el modelo LLM
- El modelo está hardcodeado: `openai/gpt-oss-120b`
- El LLMClient es un singleton que no acepta parámetros
- No hay forma de cambiar el modelo por request

## Solución Propuesta

### Opción A: Modelo en el Payload (RECOMENDADA)

#### 1. Nuevo Campo en Payload
```json
{
  // ... campos existentes ...
  "llm_config": {
    "model": "openai/gpt-oss-20b",  // Opcional
    "endpoint": "http://nueva-ip:8000/v1/chat/completions",  // Opcional
    "temperature": 0.7,  // Opcional
    "max_tokens": 20000  // Opcional
  }
}
```

#### 2. Implementación

**Fase 1: Modificar api_server.py**
```python
# En create_story()
llm_config = data.get('llm_config', {})
if llm_config:
    logger.info(f"LLM config recibido: {llm_config}")

# Pasar a process_story_async
thread = threading.Thread(
    target=process_story_async,
    args=(story_id, brief, webhook_url, mode_verificador_qa, 
          pipeline_version, prompt_metrics_id, pipeline_request_id, llm_config)
)
```

**Fase 2: Modificar LLMClient para ser configurable**
```python
class LLMClient:
    def __init__(self, config_override=None):
        base_config = LLM_CONFIG.copy()
        if config_override:
            base_config.update(config_override)
        
        self.endpoint = base_config.get("api_url", os.getenv("LLM_API_URL"))
        self.model = base_config.get("model", os.getenv("LLM_MODEL"))
        self.temperature = base_config.get("temperature", 0.7)
        self.max_tokens = base_config.get("max_tokens", 20000)
```

**Fase 3: Modificar Orchestrator**
```python
class StoryOrchestrator:
    def __init__(self, story_id, llm_config=None, **kwargs):
        # ...
        self.llm_config = llm_config
        self.agent_runner = AgentRunner(
            self.story_id, 
            llm_config=llm_config,
            **kwargs
        )
```

**Fase 4: Modificar AgentRunner**
```python
class AgentRunner:
    def __init__(self, story_id, llm_config=None, **kwargs):
        # En lugar de singleton, crear instancia con config
        if llm_config:
            self.llm_client = LLMClient(llm_config)
        else:
            self.llm_client = get_llm_client()
```

### Opción B: Mapeo por Pipeline Version

#### Configuración en .env
```env
# Modelos por versión
LLM_MODEL_V1=openai/gpt-oss-120b
LLM_MODEL_V2=openai/gpt-oss-120b
LLM_MODEL_V3=openai/gpt-oss-20b

# Endpoints por versión
LLM_ENDPOINT_V1=http://69.19.136.204:8000/v1/chat/completions
LLM_ENDPOINT_V2=http://69.19.136.204:8000/v1/chat/completions
LLM_ENDPOINT_V3=http://nueva-ip:8000/v1/chat/completions
```

#### Implementación
```python
# En config.py
def get_llm_config_for_version(version):
    return {
        "model": os.getenv(f"LLM_MODEL_{version.upper()}", LLM_CONFIG["model"]),
        "api_url": os.getenv(f"LLM_ENDPOINT_{version.upper()}", LLM_CONFIG["api_url"])
    }
```

### Opción C: Header HTTP para Modelo

#### Request con Headers
```bash
curl -X POST http://localhost:5000/api/stories/create \
  -H "Content-Type: application/json" \
  -H "X-LLM-Model: openai/gpt-oss-20b" \
  -H "X-LLM-Endpoint: http://nueva-ip:8000/v1/chat/completions" \
  -d '{ ... payload ... }'
```

#### Implementación
```python
# En api_server.py
@app.route('/api/stories/create', methods=['POST'])
def create_story():
    llm_config = {}
    if 'X-LLM-Model' in request.headers:
        llm_config['model'] = request.headers['X-LLM-Model']
    if 'X-LLM-Endpoint' in request.headers:
        llm_config['api_url'] = request.headers['X-LLM-Endpoint']
```

## Recomendación Final

### Estrategia Híbrida (MEJOR OPCIÓN)

1. **Prioridad de configuración** (de mayor a menor):
   - Payload `llm_config` (más específico)
   - Headers HTTP `X-LLM-*`
   - Variables de entorno por versión
   - Variables de entorno globales
   - Valores por defecto

2. **Implementación gradual**:
   - **Fase 1**: Soporte de variables de entorno (ya documentado en ENV_MIGRATION_PLAN.md)
   - **Fase 2**: Agregar soporte para `llm_config` en payload
   - **Fase 3**: Agregar soporte para headers HTTP
   - **Fase 4**: Documentar y probar todas las opciones

## Ejemplo de Uso Final

### Desde lacuenteria.cl con modelo específico
```json
POST /api/stories/create
{
  "story_id": "cuento-001",
  "personajes": ["Luna", "Sol"],
  "historia": "Una historia de amistad",
  "edad_objetivo": 5,
  "pipeline_version": "v3",
  "llm_config": {
    "model": "openai/gpt-oss-20b",
    "endpoint": "http://10.0.0.5:8000/v1/chat/completions"
  }
}
```

### Desde VM con configuración por defecto
```json
POST /api/stories/create
{
  "story_id": "cuento-002",
  "personajes": ["Luna", "Sol"],
  "historia": "Una historia de amistad",
  "edad_objetivo": 5,
  "pipeline_version": "v3"
  // Usará LLM_MODEL y LLM_API_URL del .env
}
```

## Validación y Seguridad

### Validaciones Necesarias

1. **Lista blanca de modelos permitidos**:
```python
ALLOWED_MODELS = [
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "openai/gpt-4",
    # Agregar modelos permitidos
]

if llm_config.get("model") not in ALLOWED_MODELS:
    return jsonify({"error": "Modelo no permitido"}), 400
```

2. **Validación de endpoints**:
```python
import re
ENDPOINT_PATTERN = re.compile(r'^https?://[\d\w\.\-]+:\d+/v1/chat/completions$')

if not ENDPOINT_PATTERN.match(llm_config.get("api_url", "")):
    return jsonify({"error": "Endpoint inválido"}), 400
```

3. **Límites de configuración**:
```python
if llm_config.get("max_tokens", 0) > 30000:
    return jsonify({"error": "max_tokens excede límite"}), 400

if not 0.0 <= llm_config.get("temperature", 0.7) <= 2.0:
    return jsonify({"error": "temperature fuera de rango"}), 400
```

## Logging y Monitoreo

### Registrar configuración usada
```python
# En manifest.json
{
  "configuracion_modelo": {
    "modelo": "openai/gpt-oss-20b",  // Modelo usado
    "endpoint": "http://...",        // Endpoint usado
    "source": "payload",              // De dónde vino la config
    "temperature": 0.7,
    "max_tokens": 20000
  }
}
```

### Métricas por modelo
- Tiempo de respuesta por modelo
- Tasa de éxito por modelo
- Calidad promedio (QA score) por modelo
- Costo estimado por modelo

## Testing

### Tests necesarios

1. **Test con payload completo**:
```python
def test_create_story_with_llm_config():
    payload = {
        "story_id": "test-001",
        "llm_config": {
            "model": "openai/gpt-oss-20b",
            "endpoint": "http://localhost:8000/v1/chat/completions"
        },
        # ... resto del payload
    }
    response = client.post("/api/stories/create", json=payload)
    assert response.status_code == 202
    # Verificar que se usó la configuración correcta
```

2. **Test de fallback**:
```python
def test_create_story_without_llm_config():
    # Sin llm_config, debe usar valores del .env
    payload = {
        "story_id": "test-002",
        # ... sin llm_config
    }
    response = client.post("/api/stories/create", json=payload)
    # Verificar que usó configuración por defecto
```

3. **Test de validación**:
```python
def test_invalid_model_rejected():
    payload = {
        "llm_config": {
            "model": "modelo-no-permitido"
        }
    }
    response = client.post("/api/stories/create", json=payload)
    assert response.status_code == 400
```

## Migración

### Para lacuenteria.cl

1. **Sin cambios inicialmente** - Todo sigue funcionando
2. **Opcional**: Agregar `llm_config` cuando quieran usar otro modelo
3. **Documentar** endpoints disponibles y modelos soportados

### Para nuevos deployments

1. Configurar `.env` con el modelo y endpoint correctos
2. No necesitan cambiar nada en el código si usan el mismo modelo
3. Pueden override por request si necesitan

## Beneficios

1. **Flexibilidad**: Diferentes modelos por request
2. **Compatibilidad**: No rompe nada existente
3. **Testing**: Fácil probar diferentes modelos
4. **Multi-tenant**: Diferentes clientes, diferentes modelos
5. **Optimización**: Usar modelos más pequeños/rápidos cuando sea posible
6. **Costos**: Controlar uso de modelos caros

## Riesgos y Mitigaciones

| Riesgo | Mitigación |
|--------|------------|
| Uso de modelos no autorizados | Lista blanca de modelos |
| Endpoints maliciosos | Validación de formato y whitelist |
| Sobrecarga del sistema | Límites por modelo y rate limiting |
| Configuración incorrecta | Validación y valores por defecto |
| Incompatibilidad de modelos | Testing con cada modelo soportado |

## Timeline Estimado

- **Semana 1**: Implementar soporte de variables de entorno
- **Semana 2**: Agregar `llm_config` en payload
- **Semana 3**: Testing y documentación
- **Semana 4**: Deploy y monitoreo

## Conclusión

La estrategia híbrida permite máxima flexibilidad mientras mantiene compatibilidad. lacuenteria.cl puede seguir funcionando sin cambios, pero tiene la opción de especificar modelos cuando lo necesite.