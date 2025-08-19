# Documentación API - Sistema Cuentería

## Descripción General

API REST para el sistema de generación automatizada de cuentos infantiles. Recibe briefs desde lacuenteria.cl y orquesta un pipeline de 12 agentes especializados para producir cuentos completos con texto e indicaciones visuales.

## Base URL

```
http://localhost:5000
```

## Headers Requeridos

```http
Content-Type: application/json
```

## Endpoints

### 1. Health Check

Verifica el estado del sistema y la conectividad con el modelo LLM.

**Endpoint:** `GET /health`

**Response exitosa (200):**
```json
{
  "status": "healthy",
  "timestamp": "2025-08-19T14:30:00Z",
  "checks": {
    "llm_connection": true,
    "config_valid": true
  }
}
```

**Response degradada (503):**
```json
{
  "status": "degraded",
  "timestamp": "2025-08-19T14:30:00Z",
  "checks": {
    "llm_connection": false,
    "config_valid": true
  }
}
```

---

### 2. Crear Historia

Inicia el procesamiento de un nuevo cuento.

**Endpoint:** `POST /api/stories/create`

**Request Body:**
```json
{
  "story_id": "lacuenteria-2025-001",
  "personajes": [
    {
      "nombre": "Luna",
      "descripcion": "Luciérnaga tímida de 5 años",
      "rasgos": "Curiosa, valiente cuando es necesario"
    }
  ],
  "historia": "Luna debe aprender a brillar en la oscuridad...",
  "mensaje_a_transmitir": "Vencer los miedos con valentía y apoyo",
  "edad_objetivo": "4-6 años",
  "webhook_url": "https://lacuenteria.cl/api/stories/callback/lacuenteria-2025-001"
}
```

**Campos requeridos:**
- `story_id` (string): Identificador único proporcionado por lacuenteria.cl
- `personajes` (array): Lista de personajes con nombre, descripción y rasgos
- `historia` (string): Trama principal del cuento
- `mensaje_a_transmitir` (string): Objetivo educativo/valores a transmitir
- `edad_objetivo` (string): Rango de edad ("3-5 años", "6-8 años", "9-11 años")

**Campos opcionales:**
- `webhook_url` (string): URL para notificaciones de progreso y resultado

**Response exitosa (202):**
```json
{
  "story_id": "lacuenteria-2025-001",
  "status": "processing",
  "estimated_time": 180,
  "accepted_at": "2025-08-19T14:30:00Z"
}
```

**Response historia existente completada (200):**
```json
{
  "story_id": "lacuenteria-2025-001",
  "status": "already_completed",
  "result": { /* JSON del cuento completo */ }
}
```

**Response historia en proceso (200):**
```json
{
  "story_id": "lacuenteria-2025-001",
  "status": "already_processing",
  "message": "La historia ya está siendo procesada"
}
```

**Errores posibles:**

- **400 Bad Request:** Campos faltantes o inválidos
```json
{
  "status": "error",
  "error": "Campos faltantes: personajes, historia"
}
```

- **500 Internal Server Error:** Error del servidor
```json
{
  "status": "error",
  "error": "Error interno del servidor"
}
```

---

### 3. Consultar Estado

Obtiene el estado actual del procesamiento de una historia.

**Endpoint:** `GET /api/stories/{story_id}/status`

**Parámetros:**
- `story_id` (path): ID de la historia

**Response exitosa (200):**
```json
{
  "story_id": "lacuenteria-2025-001",
  "status": "en_progreso",
  "current_step": "cuentacuentos",
  "qa_scores": {
    "director": {"arco_completo": 4.5, "claridad_visual": 4.8},
    "psicoeducador": {"ajuste_edad": 4.7, "tono_amable": 4.9}
  },
  "created_at": "2025-08-19T14:30:00Z",
  "updated_at": "2025-08-19T14:32:45Z"
}
```

**Estados posibles:**
- `iniciado`: Pipeline iniciado
- `en_progreso`: Procesando agentes
- `completo`: Historia completada exitosamente
- `error`: Error durante el procesamiento
- `qa_failed`: Falló validación de calidad

**Error 404:**
```json
{
  "status": "not_found",
  "error": "Historia no encontrada"
}
```

---

### 4. Obtener Resultado

Obtiene el JSON final del cuento completado.

**Endpoint:** `GET /api/stories/{story_id}/result`

**Response exitosa (200):**
```json
{
  "story_id": "lacuenteria-2025-001",
  "status": "completed",
  "result": {
    "titulo": "Luna la Luciérnaga Valiente",
    "paginas": {
      "1": {
        "texto": "Luna era pequeñita\ncon luz muy suavecita\nCuando el miedo la invadía\nsu brillo se escondía",
        "prompt": "Una pequeña luciérnaga tímida en un claro del bosque..."
      },
      "2": { /* ... */ },
      /* ... páginas 3-10 */
    },
    "portada": {
      "prompt": "Ilustración infantil colorida de Luna la luciérnaga..."
    },
    "loader": [
      "Luna prepara su luz mágica...",
      "Estrellín afina su violín...",
      /* ... 8 mensajes más */
    ]
  },
  "qa_scores": {
    "overall": 4.6,
    "by_agent": { /* scores detallados */ }
  },
  "metadata": {
    "created_at": "2025-08-19T14:30:00Z",
    "completed_at": "2025-08-19T14:35:00Z",
    "retries": {"cuentacuentos": 1},
    "warnings": []
  }
}
```

**Response no completada (202):**
```json
{
  "status": "not_ready",
  "current_state": "en_progreso",
  "message": "La historia aún no está completa"
}
```

---

### 5. Ver Logs

Obtiene los logs detallados del procesamiento.

**Endpoint:** `GET /api/stories/{story_id}/logs`

**Response exitosa (200):**
```json
{
  "story_id": "lacuenteria-2025-001",
  "logs": {
    "director": [
      {
        "timestamp": "2025-08-19T14:30:15Z",
        "retry_count": 0,
        "qa_scores": {"arco_completo": 4.5},
        "execution_time": 12.5,
        "status": "success"
      }
    ],
    "psicoeducador": [ /* ... */ ]
  }
}
```

---

### 6. Reintentar Historia

Reanuda el procesamiento de una historia interrumpida o fallida.

**Endpoint:** `POST /api/stories/{story_id}/retry`

**Response exitosa (202):**
```json
{
  "story_id": "lacuenteria-2025-001",
  "status": "resuming",
  "message": "Procesamiento reanudado"
}
```

---

## Webhooks

### Eventos de Webhook

El sistema envía notificaciones a la URL especificada en `webhook_url`:

#### 1. Historia Completada

**Event:** `story_complete`

```json
{
  "event": "story_complete",
  "timestamp": 1692457800,
  "data": {
    "story_id": "lacuenteria-2025-001",
    "status": "success",
    "result": { /* Cuento completo */ },
    "qa_scores": { /* Scores QA */ },
    "processing_time": 145.3
  }
}
```

#### 2. Error en Historia

**Event:** `story_error`

```json
{
  "event": "story_error",
  "timestamp": 1692457800,
  "data": {
    "story_id": "lacuenteria-2025-001",
    "status": "error",
    "error": "Error en agente cuentacuentos: timeout"
  }
}
```

#### 3. Progreso (opcional)

**Event:** `story_progress`

```json
{
  "event": "story_progress",
  "timestamp": 1692457800,
  "data": {
    "story_id": "lacuenteria-2025-001",
    "status": "processing",
    "current_agent": "cuentacuentos",
    "progress": 25
  }
}
```

---

## Códigos de Estado HTTP

| Código | Descripción |
|--------|-------------|
| 200 | Éxito |
| 202 | Aceptado para procesamiento |
| 400 | Petición inválida |
| 404 | Recurso no encontrado |
| 500 | Error interno del servidor |
| 503 | Servicio no disponible |

---

## Límites y Restricciones

- **Tamaño máximo de request:** 1MB
- **Timeout de procesamiento:** 10 minutos por historia
- **Historias concurrentes:** 3 (configurable)
- **Retención de datos:** 30 días

---

## Ejemplos de Uso

### cURL

```bash
# Crear historia
curl -X POST http://localhost:5000/api/stories/create \
  -H "Content-Type: application/json" \
  -d '{
    "story_id": "test-001",
    "personajes": [...],
    "historia": "...",
    "mensaje_a_transmitir": "...",
    "edad_objetivo": "4-6 años"
  }'

# Consultar estado
curl http://localhost:5000/api/stories/test-001/status

# Obtener resultado
curl http://localhost:5000/api/stories/test-001/result
```

### Python

```python
import requests

# Crear historia
response = requests.post(
    "http://localhost:5000/api/stories/create",
    json={
        "story_id": "test-001",
        "personajes": [...],
        "historia": "...",
        "mensaje_a_transmitir": "...",
        "edad_objetivo": "4-6 años"
    }
)

# Verificar estado
status = requests.get(f"http://localhost:5000/api/stories/test-001/status")
print(status.json())
```

### JavaScript

```javascript
// Crear historia
fetch('http://localhost:5000/api/stories/create', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    story_id: 'test-001',
    personajes: [...],
    historia: '...',
    mensaje_a_transmitir: '...',
    edad_objetivo: '4-6 años'
  })
})
.then(response => response.json())
.then(data => console.log(data));
```