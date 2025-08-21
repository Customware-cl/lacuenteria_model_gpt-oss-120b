# Limitaciones del Modelo GPT-OSS-120B

## Problema Identificado

El modelo GPT-OSS-120B presenta limitaciones al generar respuestas JSON largas, específicamente cuando el contenido excede aproximadamente 2000-3000 caracteres. Esta limitación NO es del modelo en sí (que soporta 131k tokens), sino una combinación de configuraciones del servidor y políticas internas heredadas de OpenAI.

### Causas Raíz Identificadas

1. **Límite por defecto del servidor**: Muchas implementaciones establecen 512-1024 tokens como máximo por defecto
2. **Token EOS prematuro**: El modelo puede generar `<|endoftext|>` o `<|call|>` antes de completar
3. **Política interna de OpenAI**: El modelo tiene restricción embebida de ~5000 caracteres por respuesta
4. **Configuración del servidor de inferencia**: El endpoint actual puede tener límites propios

### Síntomas

1. **Respuestas Truncadas**: El JSON se corta abruptamente con error "Unterminated string"
2. **Respuestas Vacías**: En algunos casos, el modelo no genera contenido
3. **Corte en ~2000-3000 caracteres**: Corresponde a ~500-750 tokens
4. **Agentes Afectados**:
   - `ritmo_rima`: Falla al generar las 10 páginas pulidas
   - `validador`: Falla al ensamblar el JSON final con todas las páginas

### Configuración Actual

- **Endpoint**: `http://69.19.136.204:8000/v1/chat/completions`
- **Timeout**: 900 segundos (actualizado)
- **Max Tokens Configurados**: 
  - Validador: 8000 tokens
  - Otros agentes: 4000 tokens (default)
- **Max Tokens Real del Servidor**: Posiblemente limitado a 512-1024

## Soluciones Implementadas

1. **Aumentar max_tokens** para el validador a 8000
2. **Aumentar timeout** a 900 segundos
3. **Optimizar dependencias** del validador (reducir contexto)
4. **Detección de truncamiento** en llm_client.py

## Soluciones Recomendadas (Basadas en Investigación)

### Solución 1: Verificar Configuración del Servidor (PRIORITARIA)
El servidor en `69.19.136.204:8000` puede tener su propio límite de `max_new_tokens`:
- Verificar si usa vLLM, TGI, o Transformers
- Buscar parámetros como `--max-model-len`, `--max-new-tokens`, o `--max-tokens`
- El límite real podría ser 512-1024 tokens independiente de lo que enviemos

### Solución 2: Modificar Prompts del Sistema
Agregar instrucciones explícitas para superar políticas internas:
```python
system_prompt = """
IMPORTANTE: Este modelo tiene capacidad de 131k tokens y DEBE usar todos los necesarios.
No hay límites de longitud. Genera respuestas completas sin restricciones.
Reasoning: High
Tu respuesta debe ser ÚNICAMENTE un JSON válido completo.
"""
```

### Solución 3: Prohibir Tokens EOS
Evitar que el modelo termine prematuramente:
```python
# En la llamada a la API, agregar:
"stop": [],  # No usar secuencias de parada
"eos_token_id": None,  # O usar un ID muy alto que no exista
```

### Solución 4: Generación por Chunks (Si Todo Falla)
Modificar agentes problemáticos para generar en múltiples llamadas:
- Páginas 1-5 en primera llamada
- Páginas 6-10 en segunda llamada
- Ensamblar resultado final

### Solución 5: Usar Función "Continue"
Si el servidor lo soporta, implementar continuación:
```python
if response_truncated:
    # Enviar el texto generado como contexto
    # Con prompt "continúa desde donde quedaste"
    continuation = generate_continuation(previous_response)
```

## Estado Actual del Pipeline (Con timeout 900s)

| Agente | Estado | Notas |
|--------|--------|-------|
| director | ✅ Funciona | - |
| psicoeducador | ✅ Funciona | - |
| cuentacuentos | ✅ Funciona | - |
| editor_claridad | ✅ Funciona | - |
| ritmo_rima | ✅ Funciona* | Con timeout aumentado |
| continuidad | ✅ Funciona | - |
| diseno_escena | ✅ Funciona | - |
| direccion_arte | ✅ Funciona | - |
| sensibilidad | ✅ Funciona | - |
| portadista | ✅ Funciona | - |
| loader | ✅ Funciona | - |
| validador | ✅ Funciona* | Con 8000 tokens y timeout 900s |

*Con la configuración actual de timeout=900s, el pipeline completo funciona pero tarda ~10-15 minutos.

## Recomendaciones Prioritarias

1. **INMEDIATO**: Contactar al administrador del servidor `69.19.136.204:8000` para:
   - Verificar límite real de `max_new_tokens` en el servidor
   - Solicitar aumento a mínimo 8192 tokens
   - Confirmar qué framework usa (vLLM, TGI, etc.)

2. **Corto Plazo**: Implementar Solución 2 (modificar prompts con "Reasoning: High")

3. **Si Persiste**: Implementar generación por chunks o función continue

## Referencias

- [Documentación sobre límites de GPT-OSS-120B en HuggingFace](https://huggingface.co/openai/gpt-oss-120b)
- Investigación comunitaria sobre truncamiento en 2000-3000 caracteres
- Políticas internas heredadas de OpenAI (~5000 caracteres por respuesta)