# Limitaciones del Modelo GPT-OSS-120B

## Problema Identificado

El modelo GPT-OSS-120B presenta limitaciones al generar respuestas JSON largas, específicamente cuando el contenido excede aproximadamente 2000-3000 caracteres.

### Síntomas

1. **Respuestas Truncadas**: El JSON se corta abruptamente con error "Unterminated string"
2. **Respuestas Vacías**: En algunos casos, el modelo no genera contenido
3. **Agentes Afectados**:
   - `ritmo_rima`: Falla al generar las 10 páginas pulidas
   - `validador`: Falla al ensamblar el JSON final con todas las páginas

### Configuración Actual

- **Endpoint**: `http://69.19.136.204:8000/v1/chat/completions`
- **Timeout**: 120 segundos
- **Max Tokens**: 
  - Validador: 8000 tokens
  - Otros agentes: Sin límite explícito

## Soluciones Implementadas

1. **Aumentar max_tokens** para el validador a 8000
2. **Aumentar timeout** a 120 segundos
3. **Optimizar dependencias** del validador (reducir contexto)
4. **Detección de truncamiento** en llm_client.py

## Soluciones Pendientes

### Opción 1: Generación por Chunks
Modificar agentes problemáticos para generar en múltiples llamadas:
- Páginas 1-5 en primera llamada
- Páginas 6-10 en segunda llamada
- Ensamblar resultado final

### Opción 2: Simplificar Salidas
Reducir la longitud de los prompts de imagen y textos para mantener el JSON bajo el límite.

### Opción 3: Modelo Alternativo
Considerar usar un modelo con mayor capacidad de generación o configurar el servidor actual para permitir respuestas más largas.

## Estado Actual del Pipeline

| Agente | Estado | Notas |
|--------|--------|-------|
| director | ✅ Funciona | - |
| psicoeducador | ✅ Funciona | - |
| cuentacuentos | ✅ Funciona | Sin límite de tokens |
| editor_claridad | ✅ Funciona | - |
| ritmo_rima | ❌ Falla | Respuestas truncadas |
| continuidad | ⚠️ No probado | - |
| diseno_escena | ⚠️ No probado | - |
| direccion_arte | ⚠️ No probado | - |
| sensibilidad | ⚠️ No probado | - |
| portadista | ⚠️ No probado | - |
| loader | ⚠️ No probado | - |
| validador | ❌ Esperado que falle | Necesita generar JSON muy grande |

## Recomendaciones

1. **Corto Plazo**: Implementar generación por chunks para ritmo_rima y validador
2. **Mediano Plazo**: Investigar configuración del servidor vLLM/TGI para aumentar límites
3. **Largo Plazo**: Optimizar el pipeline completo para reducir tamaño de JSONs