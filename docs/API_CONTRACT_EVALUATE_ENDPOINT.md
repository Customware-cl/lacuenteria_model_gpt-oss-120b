# 📄 Contrato API - Endpoint de Evaluación Crítica

## Información General

| Campo | Valor |
|-------|-------|
| **Endpoint Principal** | `/v1/chat/completions` |
| **Método HTTP** | `POST` |
| **Content-Type** | `application/json` |
| **URL Base** | `http://69.19.136.204:8000` |
| **Modelo** | `openai/gpt-oss-120b` |
| **Timeout Recomendado** | 60 segundos |
| **Disponibilidad** | ✅ ACTIVO Y FUNCIONAL |

## Descripción

Este endpoint ejecuta una evaluación crítica profesional sobre cualquier historia/cuento infantil usando el modelo GPT-OSS-120B directamente. El agente crítico analiza aspectos narrativos, poéticos, visuales y pedagógicos.

## Request Headers

```http
Content-Type: application/json
```

## Request Body

### Estructura JSON para Evaluación

```json
{
  "model": "openai/gpt-oss-120b",
  "messages": [
    {
      "role": "system",
      "content": "[PROMPT_CRITICO - ver sección abajo]"
    },
    {
      "role": "user",
      "content": "Evalúa el siguiente cuento infantil:\n\n[HISTORIA_JSON]\n\nRecuerda responder ÚNICAMENTE con el JSON de evaluación crítica especificado."
    }
  ],
  "temperature": 0.4,
  "max_tokens": 4000
}
```

### Estructura de Historia a Evaluar

```json
{
  "titulo": "string",
  "paginas": {
    "[clave]": {
      "texto": "string",
      "prompt": "string"
    }
  },
  "portada": {
    "prompt": "string"
  },
  "loader": ["string"]
}
```

### Campos de la Historia

| Campo | Tipo | Requerido | Descripción | Validaciones |
|-------|------|-----------|-------------|--------------|
| `titulo` | string | ✅ Sí | Título principal de la historia | Máximo 200 caracteres recomendado |
| `paginas` | object | ✅ Sí | Diccionario con las páginas del cuento | Mínimo 1 página |
| `paginas.[clave]` | object | ✅ Sí | Cada página individual | Clave puede ser cualquier string |
| `paginas.[clave].texto` | string | ✅ Sí | Texto/verso de la página | Sin límite específico |
| `paginas.[clave].prompt` | string | ✅ Sí | Descripción detallada para ilustración | Sin límite específico |
| `portada` | object | ✅ Sí | Información de la portada | - |
| `portada.prompt` | string | ✅ Sí | Descripción de imagen de portada | Sin límite específico |
| `loader` | array | ✅ Sí | Lista de mensajes de carga | Mínimo 1 mensaje |

### Validaciones

- **Tamaño máximo del JSON**: 1 MB
- **Número de páginas**: Flexible (mínimo 1, sin máximo específico)
- **Claves de páginas**: Pueden ser numéricas ("1", "2") o descriptivas ("intro", "nudo", "desenlace")
- **Orden de páginas**: El crítico evaluará en el orden que aparezcan en el JSON

## Prompt del Crítico (System Message)

```javascript
const PROMPT_CRITICO = `Eres un crítico de cuentos infantiles. Evalúa el cuento JSON que recibes.

DEBES responder ÚNICAMENTE con un JSON válido con esta estructura EXACTA:

{
  "evaluacion_critica": {
    "nota_general": {
      "puntuacion": 3.5,
      "nivel": "ACEPTABLE",
      "resumen": "El cuento cumple con los requisitos básicos pero necesita mejoras en rima y creatividad"
    },
    "notas_por_topico": {
      "prompts_imagenes": {
        "puntuacion_promedio": 4.0,
        "nivel": "BUENO",
        "notas_por_ambito": {
          "claridad_descriptiva": 4.5,
          "consistencia_personajes": 4.0,
          "nivel_detalle": 4.0,
          "adecuacion_infantil": 4.5,
          "variedad_visual": 3.5,
          "tecnica_narrativa": 3.5
        },
        "observaciones": ["Buena descripción de personajes", "Falta variedad en los planos"],
        "problemas_detectados": [],
        "paginas_afectadas": []
      },
      "mensajes_carga": {
        "puntuacion_promedio": 3.0,
        "nivel": "ACEPTABLE",
        "notas_por_ambito": {
          "originalidad": 3.0,
          "brevedad": 4.0,
          "conexion_narrativa": 3.5,
          "transmision_emocion": 3.0,
          "lenguaje_infantil": 3.5
        },
        "observaciones": ["Mensajes genéricos"],
        "loaders_problematicos": [],
        "ejemplos_inadecuados": []
      },
      "texto_narrativo": {
        "puntuacion_promedio": 3.5,
        "nivel": "ACEPTABLE",
        "estructura_poetica": {
          "puntuacion_promedio": 3.0,
          "notas_por_ambito": {
            "numero_versos": 4.0,
            "longitud_versos": 3.5,
            "calidad_rima": 2.5,
            "fluidez_ritmo": 2.5
          },
          "versos_problematicos": ["dolor/desploma no riman bien"]
        },
        "contenido_narrativo": {
          "puntuacion_promedio": 4.0,
          "notas_por_ambito": {
            "coherencia_historia": 4.5,
            "progresion_emocional": 4.0,
            "lenguaje_apropiado": 4.5,
            "transmision_valores": 4.0,
            "originalidad_creatividad": 3.0
          },
          "observaciones": ["Buena progresión del personaje"]
        },
        "palabras_inadecuadas": [],
        "paginas_revisar": [3, 7]
      }
    },
    "recomendaciones_mejora": {
      "criticas": [
        {
          "prioridad": "ALTA",
          "topico": "texto",
          "descripcion": "Mejorar la calidad de las rimas",
          "sugerencia": "Revisar terminaciones para rima consonante consistente"
        }
      ],
      "mejoras_prioritarias": [
        "Mejorar calidad de rimas en páginas 3 y 7",
        "Aumentar variedad en los mensajes de carga",
        "Agregar más creatividad en la narrativa"
      ]
    },
    "decision_publicacion": {
      "apto_para_publicar": true,
      "requiere_revision": true,
      "nivel_revision_requerido": "MENOR",
      "justificacion": "El cuento es publicable pero se beneficiaría de mejoras menores en rima y creatividad"
    },
    "metadata": {
      "fecha_evaluacion": "2024-08-20T00:00:00",
      "version_evaluador": "1.0",
      "criterios_aplicados": 20,
      "paginas_evaluadas": 10,
      "prompts_evaluados": 11,
      "loaders_evaluados": 10
    }
  }
}

Evalúa con puntuaciones entre 1 y 5:
- 1-2: Deficiente
- 3: Aceptable
- 4: Bueno
- 5: Excelente

Sé justo pero crítico. Identifica problemas reales.`;
```

## Response

### Response exitosa (HTTP 200)

```json
{
  "id": "chatcmpl-...",
  "model": "openai/gpt-oss-120b",
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "{\"evaluacion_critica\": {...}}"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 1000,
    "completion_tokens": 2000,
    "total_tokens": 3000
  }
}
```

### Estructura de Evaluación Crítica (en content)

El campo `choices[0].message.content` contiene un string JSON que debe parsearse:

```json
{
  "evaluacion_critica": {
    "nota_general": {
      "puntuacion": 0.0-5.0,
      "nivel": "string",
      "resumen": "string"
    },
    "notas_por_topico": {
      "prompts_imagenes": {...},
      "mensajes_carga": {...},
      "texto_narrativo": {...}
    },
    "recomendaciones_mejora": {
      "criticas": [...],
      "mejoras_prioritarias": [...]
    },
    "decision_publicacion": {
      "apto_para_publicar": boolean,
      "requiere_revision": boolean,
      "nivel_revision_requerido": "MAYOR|MENOR|NINGUNO",
      "justificacion": "string"
    },
    "metadata": {...}
  }
}
```

### Niveles de Evaluación

| Puntuación | Nivel | Descripción |
|------------|-------|-------------|
| 4.5 - 5.0 | EXCELENTE | Historia de calidad excepcional, lista para publicar |
| 3.5 - 4.4 | BUENO | Historia de buena calidad con mejoras menores opcionales |
| 2.5 - 3.4 | ACEPTABLE | Historia funcional que se beneficiaría de mejoras |
| 1.0 - 2.4 | DEFICIENTE | Historia con problemas significativos que requiere revisión |

## Ejemplos de Uso

### JavaScript (Frontend)

```javascript
async function evaluarHistoria(historiaData) {
    const API_URL = 'http://69.19.136.204:8000/v1/chat/completions';
    
    const userPrompt = `Evalúa el siguiente cuento infantil:\n\n${JSON.stringify(historiaData, null, 2)}\n\nRecuerda responder ÚNICAMENTE con el JSON de evaluación crítica especificado.`;
    
    try {
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                model: 'openai/gpt-oss-120b',
                messages: [
                    { role: 'system', content: PROMPT_CRITICO },
                    { role: 'user', content: userPrompt }
                ],
                temperature: 0.4,
                max_tokens: 4000
            }),
            signal: AbortSignal.timeout(60000)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        const evaluacionText = result.choices[0].message.content;
        const evaluacion = JSON.parse(evaluacionText);
        
        return {
            status: 'success',
            evaluacion_critica: evaluacion.evaluacion_critica,
            timestamp: new Date().toISOString()
        };
        
    } catch (error) {
        console.error('Error evaluando historia:', error);
        return {
            status: 'error',
            message: error.message
        };
    }
}
```

### Python (Backend)

```python
import requests
import json

def evaluar_historia(historia_data, prompt_critico):
    """
    Evalúa una historia usando el endpoint LLM directamente
    
    Args:
        historia_data: Diccionario con la estructura de la historia
        prompt_critico: String con el prompt del sistema crítico
    
    Returns:
        Dict con la evaluación o None si hay error
    """
    url = 'http://69.19.136.204:8000/v1/chat/completions'
    
    user_prompt = f"""Evalúa el siguiente cuento infantil:

{json.dumps(historia_data, ensure_ascii=False, indent=2)}

Recuerda responder ÚNICAMENTE con el JSON de evaluación crítica especificado."""
    
    try:
        response = requests.post(
            url,
            json={
                'model': 'openai/gpt-oss-120b',
                'messages': [
                    {'role': 'system', 'content': prompt_critico},
                    {'role': 'user', 'content': user_prompt}
                ],
                'temperature': 0.4,
                'max_tokens': 4000
            },
            headers={'Content-Type': 'application/json'},
            timeout=60
        )
        
        response.raise_for_status()
        result = response.json()
        
        # Extraer y parsear la evaluación
        evaluacion_text = result['choices'][0]['message']['content']
        evaluacion = json.loads(evaluacion_text)
        
        return {
            'status': 'success',
            'evaluacion_critica': evaluacion['evaluacion_critica']
        }
        
    except Exception as e:
        print(f"Error evaluando: {e}")
        return None
```

### cURL (Testing)

```bash
# Prueba básica
curl -X POST http://69.19.136.204:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openai/gpt-oss-120b",
    "messages": [
      {"role": "system", "content": "[PROMPT_CRITICO]"},
      {"role": "user", "content": "Evalúa el siguiente cuento infantil:\n\n{\"titulo\":\"Test\",\"paginas\":{\"1\":{\"texto\":\"Hola\",\"prompt\":\"Imagen\"}}\"portada\":{\"prompt\":\"Portada\"},\"loader\":[\"Cargando...\"]}\n\nRecuerda responder ÚNICAMENTE con el JSON de evaluación crítica especificado."}
    ],
    "temperature": 0.4,
    "max_tokens": 4000
  }'
```

## Notas de Implementación

1. **Parsing de respuesta**: El contenido viene como string JSON dentro de `choices[0].message.content`
2. **Temperatura**: Usar 0.4 para evaluaciones consistentes
3. **Max tokens**: 4000 es suficiente para evaluaciones completas
4. **Timeout**: Configurar mínimo 60 segundos
5. **Sin streaming**: Este endpoint no soporta streaming

## Ventajas de esta Solución

✅ **Disponible inmediatamente** - No requiere cambios en infraestructura
✅ **Un solo endpoint** - Simplifica la integración
✅ **Seguro** - No expone puertos adicionales
✅ **Probado** - Verificado y funcionando al 22/08/2025

## Estado Actual

| Aspecto | Estado | Detalles |
|---------|--------|----------|
| Endpoint LLM | ✅ ACTIVO | Funcionando en puerto 8000 |
| Modelo GPT-OSS-120B | ✅ OPERATIVO | Respuestas en ~15 segundos |
| Evaluación crítica | ✅ FUNCIONAL | JSON completo y válido |
| Acceso desde internet | ✅ DISPONIBLE | IP pública accesible |

## Versionado

| Versión | Fecha | Cambios |
|---------|-------|---------|
| 1.0 | 2025-08-22 | Versión inicial con soporte para historias externas |
| 1.1 | 2025-08-22 | Flexibilización en número de páginas |
| 2.0 | 2025-08-22 | Migración a endpoint LLM directo (solución actual) |

## Contacto y Soporte

Para reportar problemas o solicitar mejoras, los archivos de referencia están en:
- `/home/ubuntu/cuenteria/docs/EVALUACION_DIRECTA_LLM.md` - Documentación completa
- `/home/ubuntu/cuenteria/docs/INSTRUCCIONES_LACUENTERIA_CL.md` - Guía rápida

---

*Última actualización: 22 de Agosto 2025 - Solución directa LLM activa y funcional*