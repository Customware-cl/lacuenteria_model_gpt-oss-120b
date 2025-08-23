# Guía de Evaluación Directa usando GPT-OSS-120B

## Información del Endpoint

- **URL**: `http://69.19.136.204:8000/v1/chat/completions`
- **Método**: POST
- **Content-Type**: `application/json`
- **Modelo**: `openai/gpt-oss-120b`

## Prompt del Crítico

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

## Función JavaScript para Evaluación

```javascript
/**
 * Evalúa una historia usando el agente crítico directamente en el LLM
 * @param {Object} historiaData - JSON con la historia (titulo, paginas, portada, loader)
 * @returns {Promise<Object>} - Evaluación crítica completa
 */
async function evaluarHistoriaDirecta(historiaData) {
    const API_URL = 'http://69.19.136.204:8000/v1/chat/completions';
    
    // Construir el mensaje para el LLM
    const userPrompt = `Evalúa el siguiente cuento infantil:

${JSON.stringify(historiaData, null, 2)}

Recuerda responder ÚNICAMENTE con el JSON de evaluación crítica especificado.`;
    
    try {
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                model: 'openai/gpt-oss-120b',
                messages: [
                    {
                        role: 'system',
                        content: PROMPT_CRITICO
                    },
                    {
                        role: 'user',
                        content: userPrompt
                    }
                ],
                temperature: 0.4,
                max_tokens: 4000,
                response_format: { type: "json_object" }
            }),
            signal: AbortSignal.timeout(60000) // 60 segundos timeout
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        
        // Extraer el contenido de la respuesta
        const evaluacionText = result.choices[0].message.content;
        
        // Parsear el JSON de evaluación
        const evaluacion = JSON.parse(evaluacionText);
        
        // Agregar metadata adicional
        return {
            status: 'success',
            story_id: historiaData.titulo || 'sin-titulo',
            source: 'direct_llm',
            evaluacion_critica: evaluacion.evaluacion_critica,
            timestamp: new Date().toISOString()
        };
        
    } catch (error) {
        console.error('Error evaluando historia:', error);
        return {
            status: 'error',
            message: error.message,
            timestamp: new Date().toISOString()
        };
    }
}

// Ejemplo de uso
const historiaEjemplo = {
    "titulo": "El Viaje de Luna",
    "paginas": {
        "1": {
            "texto": "Luna miraba las estrellas desde su ventana,\nsoñando con tocarlas algún día.",
            "prompt": "Niña de 5 años mirando por ventana nocturna con estrellas brillantes"
        },
        "2": {
            "texto": "Cierra los ojos y respira profundo,\nsiente que flota como una pluma.",
            "prompt": "Luna flotando con ojos cerrados rodeada de luz suave"
        }
    },
    "portada": {
        "prompt": "Luna con capa azul mirando hacia un cielo estrellado mágico"
    },
    "loader": [
        "Preparando el cielo estrellado...",
        "Encendiendo las estrellas..."
    ]
};

// Llamar a la función
evaluarHistoriaDirecta(historiaEjemplo)
    .then(resultado => {
        console.log('Evaluación completa:', resultado);
        if (resultado.status === 'success') {
            console.log('Puntuación:', resultado.evaluacion_critica.nota_general.puntuacion);
            console.log('Nivel:', resultado.evaluacion_critica.nota_general.nivel);
            console.log('Apto para publicar:', resultado.evaluacion_critica.decision_publicacion.apto_para_publicar);
        }
    })
    .catch(error => console.error('Error:', error));
```

## Prueba con cURL

```bash
# Prueba básica
curl -X POST http://69.19.136.204:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openai/gpt-oss-120b",
    "messages": [
      {
        "role": "system",
        "content": "Eres un crítico de cuentos infantiles. Evalúa el cuento JSON que recibes.\n\nDEBES responder ÚNICAMENTE con un JSON válido..."
      },
      {
        "role": "user",
        "content": "Evalúa el siguiente cuento infantil:\n\n{\"titulo\":\"Test\",\"paginas\":{\"1\":{\"texto\":\"Hola mundo\",\"prompt\":\"Imagen test\"}},\"portada\":{\"prompt\":\"Portada\"},\"loader\":[\"Cargando...\"]}\n\nRecuerda responder ÚNICAMENTE con el JSON de evaluación crítica especificado."
      }
    ],
    "temperature": 0.4,
    "max_tokens": 4000
  }'
```

## Estructura de Respuesta Esperada

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

## Notas Importantes

1. **Temperatura**: Usar 0.4 para evaluaciones consistentes
2. **Max Tokens**: 4000 es suficiente para evaluaciones completas
3. **Timeout**: Configurar 60 segundos mínimo
4. **Formato de respuesta**: El LLM devuelve JSON como string, debe parsearse
5. **Estructura de historia**: Debe seguir el formato con campos `titulo`, `paginas`, `portada`, `loader`

## Ventajas de esta Solución

- ✅ No requiere cambios en el servidor
- ✅ Usa infraestructura existente
- ✅ Implementación inmediata
- ✅ Sin exposición de puertos adicionales
- ✅ Compatible con cualquier cliente HTTP

## Soporte

Para dudas sobre el formato o estructura, el prompt del crítico contiene ejemplos completos de la evaluación esperada.