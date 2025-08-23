#!/bin/bash

# Test de evaluación directa usando el LLM

echo "Probando evaluación directa con GPT-OSS-120B..."
echo "================================================"

# Preparar el prompt del crítico (versión corta para la prueba)
SYSTEM_PROMPT='Eres un crítico de cuentos infantiles. Evalúa el cuento JSON que recibes.

DEBES responder ÚNICAMENTE con un JSON válido con esta estructura EXACTA:

{
  "evaluacion_critica": {
    "nota_general": {
      "puntuacion": 3.5,
      "nivel": "ACEPTABLE",
      "resumen": "Resumen de la evaluación"
    },
    "notas_por_topico": {
      "prompts_imagenes": {
        "puntuacion_promedio": 4.0,
        "nivel": "BUENO"
      },
      "mensajes_carga": {
        "puntuacion_promedio": 3.0,
        "nivel": "ACEPTABLE"
      },
      "texto_narrativo": {
        "puntuacion_promedio": 3.5,
        "nivel": "ACEPTABLE"
      }
    },
    "decision_publicacion": {
      "apto_para_publicar": true,
      "requiere_revision": true,
      "nivel_revision_requerido": "MENOR",
      "justificacion": "Justificación"
    }
  }
}'

# Historia de prueba
USER_PROMPT='Evalúa el siguiente cuento infantil:

{
  "titulo": "Historia de Prueba",
  "paginas": {
    "1": {
      "texto": "Esta es una página de prueba\ncon texto en verso sencillo",
      "prompt": "Imagen de prueba para la página 1"
    },
    "2": {
      "texto": "Segunda página del cuento\ncon más texto para evaluar",
      "prompt": "Imagen de prueba para la página 2"
    }
  },
  "portada": {
    "prompt": "Portada del cuento de prueba"
  },
  "loader": [
    "Cargando historia...",
    "Preparando magia..."
  ]
}

Recuerda responder ÚNICAMENTE con el JSON de evaluación crítica especificado.'

# Ejecutar la petición
echo "Enviando petición al LLM..."
echo ""

curl -X POST http://69.19.136.204:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"openai/gpt-oss-120b\",
    \"messages\": [
      {
        \"role\": \"system\",
        \"content\": $(echo "$SYSTEM_PROMPT" | jq -Rs .)
      },
      {
        \"role\": \"user\",
        \"content\": $(echo "$USER_PROMPT" | jq -Rs .)
      }
    ],
    \"temperature\": 0.4,
    \"max_tokens\": 2000
  }" 2>/dev/null | jq '.'

echo ""
echo "================================================"
echo "Prueba completada"