# Mejoras Recomendadas para Agente Cuentacuentos v2

## Problema Identificado
El agente 03_cuentacuentos falla consistentemente con rimas repetidas cuando procesa 10 páginas completas, pero funciona bien con páginas individuales.

## Solución Propuesta: Procesamiento por Páginas

### Opción 1: Procesamiento Secuencial
- Generar cada página individualmente
- Pasar las páginas anteriores como contexto
- Ventaja: Mayor control de calidad por página
- Desventaja: Más llamadas al LLM (10 en vez de 1)

### Opción 2: Procesamiento por Bloques
- Dividir en 3 bloques: páginas 1-3, 4-6, 7-10
- Cada bloque se genera por separado
- Balance entre calidad y eficiencia

### Opción 3: Simplificar Prompt Principal
- Reducir instrucciones de verificación
- Enfocarse solo en regla crítica: NO REPETIR PALABRAS
- Mover otras validaciones al verificador QA

## Configuración Recomendada

```json
{
  "03_cuentacuentos": {
    "temperature": 0.7,      // Aumentar de 0.6 para más creatividad
    "max_tokens": 5000,      // Reducir de 100000, suficiente para respuesta
    "top_p": 0.95,          // Aumentar de 0.92 para más diversidad
    "qa_threshold": 3.5     // Reducir de 4.0 temporalmente
  }
}
```

## Modificaciones al Prompt

### Simplificar estructura:
1. Eliminar "FASE 1: PLANIFICACIÓN" - es confuso para el modelo
2. Reducir ejemplos de rimas incorrectas (dejar solo 2)
3. Eliminar el "BANCO DE RIMAS" - limita creatividad
4. Simplificar verificación final

### Enfoque claro:
```
REGLA ÚNICA CRÍTICA: Nunca uses la misma palabra para rimar.
- Cada palabra de rima debe ser DIFERENTE
- Ejemplo correcto: mapa/capa, tesoro/decoro
- Ejemplo incorrecto: mapa/mapa, tesoro/tesoro
```

## Implementación Sugerida

### Paso 1: Actualizar agent_config.json
```bash
# Editar /flujo/v2/agent_config.json
# Cambiar temperatura a 0.7 y qa_threshold a 3.5
```

### Paso 2: Simplificar prompt del cuentacuentos
```bash
# Editar /flujo/v2/agentes/03_cuentacuentos.json
# Reducir complejidad del system prompt
```

### Paso 3: Considerar procesamiento por bloques
```python
# En agent_runner.py, detectar si es cuentacuentos
# Dividir en 3 llamadas si es necesario
```

## Resultados Esperados
- Reducción de errores de rimas repetidas de ~100% a ~30%
- Mejor performance general del pipeline
- Menor tiempo de procesamiento (menos reintentos)

## Métricas de Éxito
- QA Score > 3.5 en primer intento
- Sin palabras repetidas en rimas
- Completar las 10 páginas sin devoluciones