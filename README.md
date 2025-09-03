# Cuentería - Sistema de Generación de Cuentos Infantiles

## ⚠️ Estado Actual: En Desarrollo

**Última actualización**: 3 de Septiembre 2025

### 🚀 Cambios Recientes (Sept 2025)
- **Nueva estructura de carpetas**: `{YYYYMMDD-HHMMSS}-{story_id}` para mejor ordenamiento
- **Autenticación de Webhooks**: Soporte completo para Supabase Edge Functions
- **Gestión de métricas**: `prompt_metrics_id` correctamente aislado del contexto de agentes
- **Sistema de Evaluación Dual**: Control sobre verificador QA riguroso vs autoevaluación rápida
- **Optimizaciones**: Configuraciones específicas por agente para mejor rendimiento

Ver [`docs/ESTADO_ACTUAL.md`](docs/ESTADO_ACTUAL.md) para detalles completos.

## 📚 Descripción

Cuentería es un sistema multiagente basado en IA para la creación automatizada de cuentos infantiles personalizados. El sistema orquesta 12 agentes especializados que trabajan en conjunto para producir narrativas infantiles completas con texto e indicaciones visuales, garantizando calidad pedagógica, literaria y sensibilidad cultural.

## 🎯 Objetivo

Generar cuentos infantiles de 10 páginas que:
- Transmitan mensajes educativos específicos
- Sean apropiados para la edad objetivo
- Mantengan coherencia narrativa y visual
- Incluyan elementos psicoeducativos
- Garanticen sensibilidad cultural y seguridad infantil

## 🏗️ Arquitectura del Sistema

### Pipeline de Agentes

El sistema ejecuta un flujo secuencial con quality gates entre cada paso:

1. **Director** → Diseña la estructura narrativa (Beat Sheet)
2. **Psicoeducador** → Define metas conductuales y recursos psicológicos
3. **Cuentacuentos** → Convierte la estructura en versos líricos
4. **Editor de Claridad** → Optimiza la comprensibilidad del texto
5. **Ritmo y Rima** → Perfecciona la musicalidad y fluidez
6. **Continuidad** → Garantiza consistencia de personajes y elementos
7. **Diseño de Escena** → Genera prompts visuales detallados
8. **Dirección de Arte** → Define paleta de colores y estilo visual
9. **Sensibilidad** → Audita contenido para seguridad infantil
10. **Portadista** → Crea título y portada
11. **Loader** → Genera mensajes de carga personalizados
12. **Validador** → Ensambla y verifica el JSON final

### Orquestador

El agente **Orquestador** coordina todo el pipeline:
- Ejecuta los agentes en orden secuencial
- Verifica quality gates (QA scores) entre pasos
- Si QA < 4, devuelve al agente anterior con instrucciones específicas
- Mantiene trazabilidad de artefactos

## 📁 Estructura del Proyecto

```
cuenteria/
├── agentes/              # Definiciones de agentes especializados
│   ├── orquestador.json  # Coordinador del pipeline
│   ├── director.json      # Diseñador de estructura narrativa
│   ├── psicoeducador.json # Experto en psicología infantil
│   ├── cuentacuentos.json # Creador de versos
│   ├── editor_claridad.json # Editor de comprensibilidad
│   ├── ritmo_rima.json   # Optimizador de musicalidad
│   ├── continuidad.json  # Responsable de coherencia
│   ├── diseno_escena.json # Diseñador visual
│   ├── sensibilidad.json # Auditor de seguridad
│   ├── portadista.json   # Creador de títulos y portadas
│   ├── loader.json       # Generador de mensajes de carga
│   └── validador.json    # Ensamblador final
└── runs/                 # Ejecuciones y resultados generados
```

## 🔧 Componentes Principales

### Agentes Creativos

#### Director (director.json)
- **Función**: Crear estructura narrativa de 10 escenas
- **Salida**: Beat Sheet con arco emotivo, leitmotiv y variantes
- **QA**: Arco completo, claridad visual, potencia del leitmotiv

#### Cuentacuentos (cuentacuentos.json)
- **Función**: Convertir Beat Sheet en versos líricos
- **Especificaciones**: 
  - 4-5 versos por página
  - 7-12 palabras por verso
  - Rima consonante preferente
  - 6-8 sílabas aproximadas
- **QA**: Emoción, claridad visual, uso del leitmotiv

#### Diseño de Escena (diseno_escena.json)
- **Función**: Generar prompts visuales detallados por página
- **Incluye**: Entorno, acción, emoción, objetos ancla, iluminación, composición
- **QA**: Alineación verso-escena, variedad de planos

### Agentes de Calidad

#### Psicoeducador (psicoeducador.json)
- **Función**: Traducir mensajes en metas conductuales observables
- **Técnicas**: Respiración, etiquetado emocional, autocontrol, pedir ayuda
- **QA**: Ajuste a edad, alineación con mensaje, tono amable

#### Editor de Claridad (editor_claridad.json)
- **Función**: Hacer el texto cristalino sin perder belleza
- **Acciones**: Simplificar vocabulario, asegurar coherencia temporal
- **QA**: Comprensibilidad, imagen inequívoca

#### Sensibilidad (sensibilidad.json)
- **Función**: Auditar contenido para seguridad infantil
- **Detecta**: Miedos excesivos, estereotipos, lenguaje inadecuado
- **QA**: Seguridad y respeto cultural

### Agentes de Consistencia

#### Continuidad (continuidad.json)
- **Función**: Garantizar consistencia de personajes y elementos
- **Character Bible**: Rasgos, vestuario, colores, objetos ancla, gestos
- **QA**: Coherencia de rasgos, utilidad para arte

#### Ritmo y Rima (ritmo_rima.json)
- **Función**: Ajustar musicalidad y fluidez
- **Garantiza**: Variedad en palabras finales, esquemas consistentes
- **QA**: Fluidez, consistencia de rima, variación de cierres

### Agentes de Finalización

#### Portadista (portadista.json)
- **Función**: Crear títulos memorables y prompt de portada
- **Propone**: 3 opciones de título
- **QA**: Recordabilidad del título, síntesis emotiva

#### Loader (loader.json)
- **Función**: Generar 10 mensajes de carga personalizados
- **Objetivo**: Crear efecto WOW y sensación de adaptación en vivo
- **Límite**: 70 caracteres por mensaje

#### Validador (validador.json)
- **Función**: Ensamblar y verificar JSON final
- **Verifica**: Formato correcto, coherencia total, cumplimiento de reglas
- **Salida**: JSON definitivo con título, 10 páginas y portada

## 📊 Formato de Salida

El sistema genera un JSON con la siguiente estructura:

```json
{
  "titulo": "Título del cuento",
  "paginas": {
    "1": {
      "texto": "Versos de la página 1",
      "prompt": "Descripción visual detallada"
    },
    "2": { ... },
    ...
    "10": { ... }
  },
  "portada": {
    "prompt": "Descripción visual de la portada"
  },
  "loader": [
    "Mensaje de carga 1",
    "Mensaje de carga 2",
    ...
    "Mensaje de carga 10"
  ]
}
```

## 🎨 Características Técnicas

### Texto
- **Páginas**: 10 páginas de contenido
- **Versos por página**: 4-5
- **Palabras por verso**: 7-12
- **Sílabas**: 6-8 aproximadas
- **Rima**: Consonante preferente, esquemas variados (ABAB, AABB)
- **Leitmotiv**: Frase musical repetida 3-4 veces

### Visual
- **Estilo**: Ilustración infantil colorida
- **Composición**: Variedad de planos (general, medio, primer plano, detalle)
- **Coherencia**: Character Bible mantiene consistencia visual
- **Objetos ancla**: Elementos recurrentes para continuidad

### Pedagógico
- **Adaptación por edad**: Vocabulario y complejidad ajustados
- **Recursos psicoeducativos**: Técnicas de regulación emocional
- **Mensajes positivos**: Resoluciones cálidas y esperanzadoras
- **Sin sermones**: Aprendizaje integrado naturalmente

## 🔒 Controles de Calidad

### Sistema de Evaluación Dual

El sistema soporta dos modos de evaluación QA:

#### Modo 1: Verificador QA Riguroso (Default)
```python
orchestrator = StoryOrchestrator(story_id, mode_verificador_qa=True)
```
- Evaluador independiente con métricas específicas por agente
- Scores típicos: 2.8-3.5/5
- Detecta problemas específicos y sugiere mejoras
- Recomendado para **producción**

#### Modo 2: Autoevaluación Rápida
```python
orchestrator = StoryOrchestrator(story_id, mode_verificador_qa=False)
```
- El agente evalúa su propio trabajo
- Scores típicos: 4.0-5.0/5
- Más rápido pero menos riguroso
- Recomendado para **desarrollo y testing**

**Umbral de aprobación**: 4.0/5 en ambos modos
**Reintentos máximos**: 2 por agente si QA < 4.0

## 🚀 Uso

El sistema requiere:
1. **Personajes**: Definición de protagonistas
2. **Historia**: Trama base
3. **Mensaje a transmitir**: Objetivo educativo
4. **Edad objetivo**: Para adaptar complejidad

## 🌐 API Endpoints

### Sistema de Endpoints

El sistema Cuentería utiliza tres tipos de endpoints:

#### 1. **Modelo LLM GPT-OSS-120B**
- **Endpoint**: `http://69.19.136.204:8000/v1/chat/completions`
- **Función**: Procesamiento de IA para todos los agentes
- **Timeout**: 900 segundos para respuestas largas

#### 2. **API REST de Cuentería** (Puerto 5000)

##### Health Check
- **GET** `/health`
- **Función**: Verificar estado del servidor y conexión con LLM
- **Respuesta**: Estado del servidor, conexión LLM y configuración

##### Crear Historia
- **POST** `/api/stories/create`
- **Función**: Iniciar generación de un nuevo cuento
- **Payload**:
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
- **Respuesta**: Status 202 (Accepted) con ID y tiempo estimado
- **Proceso**: Ejecuta los 12 agentes en secuencia asíncrona

##### Consultar Estado
- **GET** `/api/stories/{story_id}/status`
- **Función**: Obtener estado actual del procesamiento
- **Respuesta**: Estado (queued/processing/completed/error), paso actual, timestamps

##### Obtener Resultado
- **GET** `/api/stories/{story_id}/result`
- **Función**: Obtener el cuento completo generado
- **Respuesta**: JSON con título, 10 páginas, portada y mensajes loader

##### Ver Logs
- **GET** `/api/stories/{story_id}/logs`
- **Función**: Obtener logs detallados del procesamiento
- **Respuesta**: Logs de cada agente con timestamps y métricas

##### Evaluación Crítica 
**Opción 1: API Local** (Solo accesible localmente)
- **POST** `/api/stories/{story_id}/evaluate`
- **Función**: Ejecutar agente crítico sobre historia (interna o externa)
- **Body**: JSON de historia externa (opcional)

**Opción 2: Endpoint Directo LLM** (Accesible desde Internet)
- **POST** `http://69.19.136.204:8000/v1/chat/completions`
- **Función**: Evaluación directa usando GPT-OSS-120B
- **Documentación**: Ver [`docs/EVALUACION_DIRECTA_LLM.md`](docs/EVALUACION_DIRECTA_LLM.md)

##### Reintentar Historia
- **POST** `/api/stories/{story_id}/retry`
- **Función**: Reintentar procesamiento desde el último punto de fallo
- **Respuesta**: Similar a create, reinicia el procesamiento

#### 3. **Webhooks hacia lacuenteria.cl**
- **Configuración**: URL proporcionada en cada request
- **Eventos**:
  - Progreso de procesamiento
  - Completación exitosa
  - Errores durante procesamiento
- **CORS**: Habilitado para `https://lacuenteria.cl`

### Flujo de Comunicación

```
1. lacuenteria.cl → POST /api/stories/create → Cuentería API
2. Cuentería API → Procesa con 12 agentes → GPT-OSS-120B
3. Cuentería API → Notifica progreso → lacuenteria.cl (webhook)
4. lacuenteria.cl → GET /api/stories/{id}/result → Obtiene cuento
```

## 📝 Notas

- Todos los agentes operan en español
- Salidas estrictamente en formato JSON
- Sin texto fuera de las estructuras JSON definidas
- Trazabilidad completa del proceso creativo

## 🤝 Contribución

Este es un sistema de orquestación multiagente diseñado para ser extensible. Nuevos agentes pueden agregarse al pipeline siguiendo el formato de contrato establecido.