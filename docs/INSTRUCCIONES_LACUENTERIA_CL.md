# Instrucciones para lacuenteria.cl - Evaluación de Historias

## Resumen Ejecutivo

✅ **El endpoint de evaluación YA ESTÁ DISPONIBLE** usando el servidor LLM existente en puerto 8000.

No es necesario esperar a que abramos el puerto 5000. Pueden implementar la evaluación de historias inmediatamente usando el endpoint `/v1/chat/completions` que ya está funcionando.

## Información del Endpoint

```
URL: http://69.19.136.204:8000/v1/chat/completions
Método: POST
Content-Type: application/json
Modelo: openai/gpt-oss-120b
Timeout recomendado: 60 segundos
```

## Implementación Rápida

### 1. Función JavaScript Lista para Usar

```javascript
const PROMPT_CRITICO = `[El prompt completo está en el archivo EVALUACION_DIRECTA_LLM.md]`;

async function evaluarHistoria(historiaData) {
    const response = await fetch('http://69.19.136.204:8000/v1/chat/completions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            model: 'openai/gpt-oss-120b',
            messages: [
                { role: 'system', content: PROMPT_CRITICO },
                { 
                    role: 'user', 
                    content: `Evalúa el siguiente cuento infantil:\n\n${JSON.stringify(historiaData, null, 2)}\n\nRecuerda responder ÚNICAMENTE con el JSON de evaluación crítica especificado.`
                }
            ],
            temperature: 0.4,
            max_tokens: 4000
        })
    });
    
    const result = await response.json();
    const evaluacion = JSON.parse(result.choices[0].message.content);
    return evaluacion;
}
```

### 2. Estructura de Historia Requerida

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

### 3. Estructura de Respuesta

La evaluación incluirá:
- **nota_general**: Puntuación (1-5), nivel (DEFICIENTE/ACEPTABLE/BUENO/EXCELENTE), resumen
- **notas_por_topico**: Evaluación detallada de prompts, mensajes de carga y texto narrativo
- **recomendaciones_mejora**: Críticas priorizadas y sugerencias específicas
- **decision_publicacion**: Si está apto para publicar y qué nivel de revisión requiere

## Verificación Rápida

Pueden probar inmediatamente con:

```bash
curl -X POST http://69.19.136.204:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openai/gpt-oss-120b",
    "messages": [
      {"role": "system", "content": "Eres un crítico. Responde HOLA si funcionas"},
      {"role": "user", "content": "¿Funcionas?"}
    ]
  }'
```

## Ventajas de esta Solución

1. **Disponible AHORA** - No necesitan esperar
2. **Sin cambios de infraestructura** - Usa el endpoint existente
3. **Más seguro** - Un solo puerto expuesto
4. **Más simple** - Llamada directa al LLM
5. **Compatible** - Funciona con cualquier cliente HTTP

## Archivos de Referencia

- `EVALUACION_DIRECTA_LLM.md` - Documentación completa con el prompt del crítico
- `test_direct_llm_evaluation.sh` - Script de prueba funcional
- `test_cami_story.json` - Historia de ejemplo para pruebas

## Soporte

Para cualquier duda sobre la implementación:
1. El prompt completo del crítico está en `EVALUACION_DIRECTA_LLM.md`
2. La función JavaScript está lista para copiar y usar
3. El endpoint está activo y probado

## Confirmación de Funcionamiento

✅ Probado el 22/08/2025 a las 14:32
✅ Respuesta exitosa con evaluación completa
✅ Tiempo de respuesta: ~15 segundos
✅ JSON de evaluación válido y completo

---

**IMPORTANTE**: Esta solución está 100% funcional y lista para usar. No es necesario esperar a que configuremos el puerto 5000.