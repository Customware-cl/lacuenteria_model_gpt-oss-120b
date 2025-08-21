# Contexto del Proyecto Cuentería para Claude

## Descripción General
Cuentería es un sistema de orquestación multiagente para la generación automatizada de cuentos infantiles personalizados utilizando el modelo GPT-OSS-120B. El sistema coordina 12 agentes especializados que trabajan secuencialmente para producir cuentos de 10 páginas con texto en verso y prompts para ilustraciones.

## Arquitectura de Endpoints

### 1. Modelo LLM GPT-OSS-120B
- **Endpoint Principal**: `http://69.19.136.204:8000/v1/chat/completions`
- **Endpoint de Modelos**: `http://69.19.136.204:8000/v1/models`
- **Timeout**: 900 segundos (configurado en `src/llm_client.py`)
- **Función**: Procesamiento de IA para todos los agentes del pipeline
- **API**: Compatible con OpenAI Chat Completions (no usa streaming)

### 2. API REST de Cuentería (Puerto 5000)

#### Endpoints Disponibles:

##### `/health` (GET)
- Verifica estado del servidor y conexión con el modelo LLM
- Retorna información de configuración y disponibilidad

##### `/api/stories/create` (POST)
- **Función Principal**: Inicia la generación de un nuevo cuento
- **Proceso**: Ejecuta los 12 agentes secuencialmente en background
- **Payload Requerido**:
  ```json
  {
    "story_id": "identificador-único",
    "personajes": ["lista de personajes"],
    "historia": "trama principal",
    "mensaje_a_transmitir": "objetivo educativo",
    "edad_objetivo": 3,
    "webhook_url": "URL opcional para notificaciones"
  }
  ```
- **Respuesta**: Status 202 (Accepted) - Procesamiento asíncrono

##### `/api/stories/{story_id}/status` (GET)
- Consulta el estado actual del procesamiento
- Retorna: estado (queued/processing/completed/error), agente actual, timestamps

##### `/api/stories/{story_id}/result` (GET)
- Obtiene el cuento completo una vez generado
- Retorna: JSON con título, 10 páginas, portada y mensajes loader

##### `/api/stories/{story_id}/logs` (GET)
- Accede a logs detallados de cada agente
- Incluye métricas de QA, tiempos de ejecución y reintentos

##### `/api/stories/{story_id}/evaluate` (POST)
- **Agente Crítico** (OPCIONAL - No parte del flujo principal)
- Ejecuta evaluación post-generación sobre calidad del cuento
- Genera archivo `13_critico.json` con análisis detallado

##### `/api/stories/{story_id}/retry` (POST)
- Reintenta procesamiento desde el último punto de fallo
- Útil para recuperación de errores transitorios

### 3. Webhooks hacia lacuenteria.cl
- **Configuración**: URL dinámica por request
- **Eventos Notificados**:
  - Progreso de procesamiento (cada agente completado)
  - Completación exitosa con resultado
  - Errores durante procesamiento
- **CORS**: Habilitado para `https://lacuenteria.cl`

## Pipeline de Agentes (Orden de Ejecución)

1. **director** - Estructura narrativa (Beat Sheet)
2. **psicoeducador** - Recursos psicológicos y metas conductuales
3. **cuentacuentos** - Conversión a versos líricos
4. **editor_claridad** - Optimización de comprensibilidad
5. **ritmo_rima** - Ajuste de musicalidad
6. **continuidad** - Character Bible y coherencia
7. **diseno_escena** - Prompts visuales detallados
8. **direccion_arte** - Paleta de colores y estilo
9. **sensibilidad** - Auditoría de seguridad infantil
10. **portadista** - Título y portada
11. **loader** - Mensajes de carga personalizados
12. **validador** - Ensamblaje final del JSON

**Nota**: El agente **crítico** NO es parte del pipeline principal. Se ejecuta opcionalmente vía endpoint `/evaluate`.

## Flujo de Comunicación

```
1. lacuenteria.cl → POST /api/stories/create → API Cuentería
2. API Cuentería → Ejecuta 12 agentes → Cada uno llama a GPT-OSS-120B
3. API Cuentería → Notifica progreso → lacuenteria.cl (webhook)
4. lacuenteria.cl → GET /api/stories/{id}/result → Obtiene cuento final
```

## Configuración Importante

### Timeouts
- **LLM Client**: 900 segundos (`src/llm_client.py:22`)
- **Webhook**: 30 segundos
- **Historia completa**: 600 segundos máximo

### Tokens por Agente
- **Default**: 4000 tokens
- **Validador**: 8000 tokens (genera JSON más grande)
- **Temperaturas**: Varían de 0.3 (validador) a 0.9 (cuentacuentos)

### Quality Gates
- Cada agente autoevalúa con QA score (1-5)
- Si QA < 4.0: Se reintenta hasta 2 veces
- Si falla después de reintentos: Se marca como devolución

## Archivos Clave

### Configuración
- `src/config.py` - Configuración central del sistema
- `src/llm_client.py` - Cliente para GPT-OSS-120B
- `src/api_server.py` - Servidor Flask con endpoints REST
- `src/orchestrator.py` - Coordinador del pipeline
- `src/agent_runner.py` - Ejecutor individual de agentes

### Agentes
- `agentes/*.json` - Definición de cada agente (prompts, QA, dependencias)

### Resultados
- `runs/{story_id}/` - Carpeta con todos los artefactos generados
- `runs/{story_id}/manifest.json` - Metadata y estado del procesamiento
- `runs/{story_id}/12_validador.json` - Cuento final completo

## Limitaciones Conocidas

- **Truncamiento de respuestas**: El modelo puede truncar respuestas largas (>3000 caracteres en JSON)
- **Solución implementada**: Timeout aumentado a 900s, max_tokens específicos por agente
- **Documentación**: Ver `docs/LIMITACIONES_MODELO.md` para detalles

## Comandos de Prueba

```bash
# Prueba completa del flujo
python3 test_flujo_completo.py

# Prueba rápida (solo primeros 4 agentes)
python3 test_rapido.py

# Servidor API
python3 src/api_server.py

# Verificar estado del servidor
curl http://localhost:5000/health
```

## Notas para el Desarrollo

- El sistema es stateless entre agentes (cada uno lee archivos previos)
- Los logs se guardan en `runs/{story_id}/logs/`
- Cada agente genera un archivo numerado (01_director.json, 02_psicoeducador.json, etc.)
- El manifest.json mantiene el estado completo del procesamiento
- Los webhooks son opcionales pero recomendados para UX en tiempo real