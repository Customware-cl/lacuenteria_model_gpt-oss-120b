# Arquitectura del Sistema Cuentería

## Visión General

Cuentería es un sistema de generación automatizada de cuentos infantiles que utiliza un pipeline de 12 agentes especializados, cada uno con un rol específico en la creación de narrativas educativas y entretenidas.

## Diagrama de Arquitectura

```
┌─────────────────────────────────────────────────────────────────┐
│                         lacuenteria.cl                           │
│                    (Frontend / Aplicación Web)                   │
└────────────────────┬───────────────────┬────────────────────────┘
                     │                   │
                     ▼                   ▼
              POST /api/stories    Webhook Response
                     │                   ▲
┌────────────────────┼───────────────────┼────────────────────────┐
│                    ▼                   │                         │
│            ┌──────────────┐     ┌──────────────┐                │
│            │  API Server  │────▶│   Webhook    │                │
│            │  (Flask)     │     │   Client     │                │
│            └──────┬───────┘     └──────────────┘                │
│                   │                                              │
│                   ▼                                              │
│         ┌──────────────────┐                                    │
│         │   Orchestrator   │                                    │
│         │                  │                                    │
│         └────────┬─────────┘                                    │
│                  │                                               │
│                  ▼                                               │
│         ┌──────────────────┐     ┌──────────────────┐          │
│         │  Agent Runner    │────▶│  Quality Gates   │          │
│         │                  │     │    Checker       │          │
│         └────────┬─────────┘     └──────────────────┘          │
│                  │                                               │
│                  ▼                                               │
│         ┌──────────────────┐                                    │
│         │   LLM Client     │                                    │
│         │                  │                                    │
│         └────────┬─────────┘                                    │
│                  │                                               │
│    Sistema       ▼                                               │
│    Cuentería  ┌─────────────────────────────────┐               │
│               │     gpt-oss-120b Model          │               │
│               │   (Local LLM Instance)          │               │
│               └─────────────────────────────────┘               │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐     │
│  │                  12 Agentes Pipeline                    │     │
│  │                                                         │     │
│  │  1.Director → 2.Psico → 3.Cuentos → 4.Claridad        │     │
│  │       ↓          ↓          ↓           ↓              │     │
│  │  5.Ritmo → 6.Continuidad → 7.Escena → 8.Arte          │     │
│  │       ↓          ↓             ↓         ↓             │     │
│  │  9.Sensibilidad → 10.Portada → 11.Loader              │     │
│  │                        ↓                                │     │
│  │                  12.Validador                           │     │
│  └────────────────────────────────────────────────────────┘     │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐     │
│  │                    File System                          │     │
│  │                                                         │     │
│  │  /runs/{story_id}/                                     │     │
│  │    ├── brief.json                                      │     │
│  │    ├── 01_director.json                                │     │
│  │    ├── ...                                             │     │
│  │    ├── 12_validador.json                               │     │
│  │    ├── manifest.json                                   │     │
│  │    └── logs/                                           │     │
│  └────────────────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────────────────┘
```

## Componentes Principales

### 1. API Server (`api_server.py`)

**Responsabilidad:** Interfaz REST para comunicación externa

**Funciones:**
- Recibir solicitudes de lacuenteria.cl
- Validar datos de entrada
- Gestionar cola de procesamiento
- Servir resultados y estados

**Endpoints principales:**
- `POST /api/stories/create` - Crear nueva historia
- `GET /api/stories/{id}/status` - Estado de procesamiento
- `GET /api/stories/{id}/result` - Obtener resultado final

**Tecnologías:**
- Flask (framework web)
- Flask-CORS (manejo de CORS)
- Threading (procesamiento asíncrono básico)

### 2. Orchestrator (`orchestrator.py`)

**Responsabilidad:** Coordinación del pipeline de agentes

**Funciones:**
- Gestionar el flujo secuencial de agentes
- Mantener el estado en `manifest.json`
- Manejar reintentos y recuperación
- Calcular métricas agregadas

**Flujo de trabajo:**
1. Inicializar story_id y directorios
2. Guardar brief.json
3. Ejecutar cada agente en secuencia
4. Verificar quality gates
5. Manejar devoluciones si QA < 4
6. Guardar resultado final

**Estados del manifest:**
- `iniciado` - Pipeline comenzado
- `en_progreso` - Procesando agentes
- `completo` - Finalizado exitosamente
- `error` - Fallo fatal
- `qa_failed` - Calidad insuficiente

### 3. Agent Runner (`agent_runner.py`)

**Responsabilidad:** Ejecución individual de agentes

**Funciones:**
- Cargar prompt del sistema desde JSON
- Cargar dependencias (artefactos previos)
- Construir prompt del usuario
- Llamar al LLM con temperatura específica
- Validar estructura de salida
- Verificar quality gates
- Manejar reintentos con mejoras

**Temperaturas por tipo de agente:**
- **Creativos (0.85-0.9):** director, cuentacuentos, portadista, loader
- **Técnicos (0.3-0.4):** validador, continuidad
- **Refinamiento (0.6-0.65):** editor_claridad, ritmo_rima
- **Evaluación (0.5-0.55):** sensibilidad, psicoeducador

### 4. LLM Client (`llm_client.py`)

**Responsabilidad:** Comunicación con modelo gpt-oss-120b

**Funciones:**
- Gestionar conexión con endpoint LLM
- Formatear prompts (system + user)
- Manejar reintentos de red
- Parsear respuestas JSON
- Validar conexión

**Configuración:**
- Endpoint: `http://localhost:8080/v1/completions`
- Timeout: 60 segundos
- Reintentos: 3 intentos
- Max tokens: 4000

### 5. Quality Gates (`quality_gates.py`)

**Responsabilidad:** Validación de calidad de salidas

**Funciones:**
- Verificar scores QA (1-5)
- Validar estructura JSON de salida
- Generar instrucciones de mejora
- Determinar si reintentar

**Reglas de validación:**
- Score promedio >= 4.0 para pasar
- Máximo 2 reintentos por agente
- Instrucciones específicas por tipo de fallo

### 6. Webhook Client (`webhook_client.py`)

**Responsabilidad:** Notificaciones a lacuenteria.cl

**Funciones:**
- Enviar eventos de progreso
- Notificar completación
- Reportar errores
- Manejar reintentos de webhook

**Eventos:**
- `story_complete` - Historia finalizada
- `story_error` - Error en procesamiento
- `story_progress` - Actualización de progreso

## Pipeline de Agentes

### Flujo de Datos

```
Brief → Director → Beat Sheet
         ↓
Beat Sheet + Brief → Psicoeducador → Mapa Psico
                      ↓
Beat Sheet + Mapa → Cuentacuentos → Texto Versos
                     ↓
Texto → Editor Claridad → Texto Claro
         ↓
Texto Claro → Ritmo/Rima → Texto Pulido
               ↓
Texto + Brief → Continuidad → Character Bible
                 ↓
Texto + Bible → Diseño Escena → Prompts Visuales
                  ↓
Prompts + Bible → Dirección Arte → Color Script
                   ↓
Todo → Sensibilidad → Auditoría
        ↓
Todo → Portadista → Títulos + Portada
        ↓
Todo → Loader → Mensajes Carga
        ↓
Todo → Validador → JSON FINAL
```

### Dependencias de Agentes

| Agente | Dependencias | Salida Principal |
|--------|--------------|------------------|
| director | brief | beat_sheet, leitmotiv |
| psicoeducador | brief, director | mapa_psico_narrativo |
| cuentacuentos | director, psicoeducador | paginas_texto |
| editor_claridad | cuentacuentos | paginas_texto_claro |
| ritmo_rima | editor_claridad | paginas_texto_pulido |
| continuidad | ritmo_rima, brief | character_bible |
| diseno_escena | ritmo_rima, continuidad | prompts_paginas |
| direccion_arte | diseno_escena, continuidad | color_script |
| sensibilidad | ritmo_rima, diseno_escena, arte | correcciones |
| portadista | ritmo_rima, continuidad, arte | titulos, portada |
| loader | portadista, brief, director, continuidad | loader (10 mensajes) |
| validador | todos los anteriores | JSON final |

## Patrones de Diseño

### 1. Pipeline Pattern
- Procesamiento secuencial de agentes
- Cada agente transforma y enriquece los datos
- Salida de uno es entrada del siguiente

### 2. Chain of Responsibility
- Quality gates verifican cada salida
- Decisión de continuar o devolver
- Manejo de reintentos automático

### 3. Strategy Pattern
- Diferentes temperaturas por tipo de agente
- Instrucciones de mejora específicas
- Validaciones personalizadas

### 4. Singleton Pattern
- LLM Client único
- Quality Checker compartido
- Webhook Client reutilizable

### 5. Observer Pattern
- Webhooks notifican eventos
- Logs registran cada acción
- Manifest mantiene estado global

## Persistencia de Datos

### Estructura de Archivos

```
runs/
└── {story_id}/
    ├── brief.json              # Entrada original
    ├── manifest.json           # Estado y metadatos
    ├── 01_director.json        # Salida director
    ├── 02_psicoeducador.json   # Salida psicoeducador
    ├── ...                     # Demás agentes
    ├── 12_validador.json       # Resultado final
    └── logs/
        ├── director.log        # Logs del director
        ├── psicoeducador.log   # Logs del psico
        └── ...                 # Logs de cada agente
```

### Manifest Structure

```json
{
  "story_id": "uuid",
  "source": "lacuenteria.cl",
  "created_at": "ISO-8601",
  "updated_at": "ISO-8601",
  "estado": "en_progreso",
  "paso_actual": "cuentacuentos",
  "qa_historial": {
    "director": {"promedio": 4.5},
    "psicoeducador": {"promedio": 4.7}
  },
  "devoluciones": [],
  "reintentos": {"cuentacuentos": 1},
  "timestamps": {},
  "webhook_url": "https://...",
  "webhook_attempts": 0
}
```

## Consideraciones de Escalabilidad

### Actual (MVP)
- Threading básico para concurrencia
- Máximo 3 historias concurrentes
- Procesamiento en memoria
- File system para persistencia

### Futuro (Producción)
- Celery + Redis para cola de tareas
- PostgreSQL para metadatos
- S3/MinIO para archivos
- Kubernetes para orquestación
- Cache distribuido
- Balanceo de carga

## Seguridad

### Implementado
- CORS configurado
- Validación de entrada
- Sanitización de JSON
- Timeouts configurados

### Recomendado
- Autenticación API Key
- Rate limiting
- HTTPS obligatorio
- Validación de webhooks
- Logs de auditoría
- Encriptación en reposo

## Monitoreo y Observabilidad

### Logs
- Por agente y por historia
- Niveles configurables (INFO, DEBUG, ERROR)
- Timestamps y duración
- QA scores y reintentos

### Métricas Clave
- Tiempo total de procesamiento
- QA score promedio
- Tasa de éxito/fallo
- Reintentos por agente
- Uso de tokens LLM

### Health Checks
- `/health` - Estado del sistema
- Verificación LLM disponible
- Validación de configuración

## Optimizaciones Implementadas

1. **Temperaturas Específicas:** Cada agente usa temperatura óptima para su función
2. **Reintentos Inteligentes:** Instrucciones de mejora específicas
3. **Validación Temprana:** Estructura verificada antes de QA
4. **Cache de Configuración:** Singleton patterns para objetos reutilizables
5. **Logs Estructurados:** JSON para fácil análisis

## Limitaciones Conocidas

1. **Concurrencia:** Threading básico, no óptimo para alta carga
2. **Persistencia:** File system, no ideal para distribución
3. **Cola:** En memoria, se pierde si el servidor cae
4. **Recuperación:** Manual mediante endpoint retry
5. **Escalabilidad:** Vertical solamente (más recursos en mismo servidor)

## Roadmap Técnico

### Corto Plazo
- [ ] Tests unitarios y de integración
- [ ] Documentación de API con OpenAPI/Swagger
- [ ] Docker compose para desarrollo
- [ ] CI/CD con GitHub Actions

### Mediano Plazo
- [ ] Migración a Celery para tareas asíncronas
- [ ] Base de datos para metadatos
- [ ] Autenticación y autorización
- [ ] Métricas con Prometheus

### Largo Plazo
- [ ] Microservicios por agente
- [ ] Orquestación con Kubernetes
- [ ] ML para optimización de prompts
- [ ] A/B testing de pipelines