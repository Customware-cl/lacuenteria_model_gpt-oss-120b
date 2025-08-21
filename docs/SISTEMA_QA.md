# Sistema de Evaluación de Calidad (QA) - Cuentería

## Resumen Ejecutivo

El sistema Cuentería implementa un **Verificador QA Independiente** que reemplaza la autoevaluación de los agentes, eliminando el conflicto de intereses que causaba que todos los agentes se calificaran con 5/5.

## Problema Original

### Conflicto de Intereses
- Cada agente se autoevaluaba su propio trabajo
- Sabían que QA < 4.0 significaba reintentos (más trabajo)
- **Resultado**: 100% de agentes con scores 5/5 (falsos positivos)

### Evidencia del Problema
```python
# Autoevaluación típica (siempre perfecta)
"qa": {
    "musicalidad": 5,
    "claridad": 5,
    "coherencia": 5
}
```

## Solución Implementada

### Verificador QA Independiente

#### Arquitectura
```
Agente genera output → Verificador QA evalúa → Score realista → Reintentos si < 4.0
```

#### Características
- **Agente separado**: `agentes/verificador_qa.json`
- **Temperatura**: 0.3 (evaluación consistente)
- **Timeout**: 900 segundos (evita truncamiento)
- **Max tokens**: 3000 (respuestas completas)

### Calibración de Evaluación

| Score | Significado | Frecuencia Esperada | Descripción |
|-------|------------|-------------------|-------------|
| 5/5 | Excepcional | <5% | Sin defectos detectables |
| 4/5 | Bueno | 20% | Errores mínimos no críticos |
| 3/5 | Aceptable | 60% | **NORMAL** - Errores notables pero funcional |
| 2/5 | Deficiente | 10% | Problemas serios |
| 1/5 | Inaceptable | 5% | Debe rehacerse |

### Penalizaciones Automáticas

- **Rima forzada**: -0.5 a -1.0 puntos
- **Repetición excesiva** (>3 veces): -0.5 puntos
- **Errores gramaticales**: -0.5 puntos
- **Metro inconsistente**: -0.5 puntos
- **Vocabulario inapropiado**: -0.5 puntos

## Integración en el Pipeline

### Flujo de Ejecución

1. **Agente genera output** con campo "qa" (ignorado)
2. **Verificador QA evalúa** objetivamente el output
3. **Si promedio < 4.0**: Reintento con feedback específico
4. **Máximo 2 reintentos** con evaluación progresivamente más estricta
5. **Logs registran** evaluación real y problemas detectados

### Código de Integración

```python
# src/agent_runner.py (líneas 88-130)
if agent_name not in ["validador", "critico", "verificador_qa"]:
    # Ignorar autoevaluación
    agent_output.pop("qa", None)
    
    # Ejecutar verificador independiente
    verificador_result = self.llm_client.generate(
        system_prompt=load_verificador_qa(),
        user_prompt=build_verification_prompt(agent_output),
        temperature=0.3,
        max_tokens=3000,
        timeout=900
    )
    
    verification = json.loads(verificador_result)
    qa_passed = verification["promedio"] >= 4.0
```

## Métricas Consolidadas

### Módulo: `src/metrics_consolidator.py`

Consolida métricas de todos los agentes ejecutados:

```python
{
    "resumen_global": {
        "total_agentes": 12,
        "tiempo_total_segundos": 240.43,
        "promedio_qa_global": 3.5,  # Realista, no 5.0
        "reintentos_totales": 5
    },
    "detalle_agentes": [...],
    "estadisticas": {
        "temperaturas": {...},
        "tiempos": {...},
        "qa_scores": {...}
    }
}
```

### Endpoint Mejorado

`POST /api/stories/{id}/evaluate` ahora retorna:

```json
{
    "evaluacion_critica": {...},      // Evaluación del contenido
    "metricas_pipeline": {...},        // Métricas consolidadas
    "metricas_disponibles": true       // Flag de disponibilidad
}
```

## Resultados Observados

### Comparación: Autoevaluación vs Verificador QA

| Agente | Autoevaluación | Verificador QA | Inflación |
|--------|---------------|----------------|-----------|
| cuentacuentos | 5.0/5 | 3.0/5 | 66.7% |
| ritmo_rima | 5.0/5 | 2.3/5 | 114.6% |
| director | 5.0/5 | 3.7/5 | 35.1% |

### Problemas Reales Detectados

- **Rimas forzadas**: "mirar/guardará", "triste/persiste"
- **Repeticiones**: "abrazo" 4x, "luz" 4x
- **Errores gramaticales**: "la persiste", "mil color"
- **Metro inconsistente**: Variación de 6-12 sílabas

## Configuración

### En `config.py`
```python
AGENT_TEMPERATURES = {
    "verificador_qa": 0.3,  # Evaluación consistente
}

QUALITY_THRESHOLDS = {
    "min_qa_score": 4.0,    # Umbral para pasar
    "max_retries": 2         # Reintentos máximos
}
```

### En `agent_runner.py`
```python
timeout = 900        # 15 minutos
max_tokens = 3000   # Respuestas completas
temperature = 0.3   # Consistencia
```

## Scripts de Prueba

### `test_verificador_qa.py`
Compara autoevaluación vs verificador para agentes existentes.

```bash
python3 test_verificador_qa.py
```

### `test_metrics_consolidator.py`
Prueba consolidación de métricas con y sin logs.

```bash
python3 test_metrics_consolidator.py
```

## Próximos Pasos

### Calibración Pendiente
- Verificador muy estricto (promedios 2.3-3.7)
- Considerar bajar umbral a 3.5
- O ajustar severidad del verificador

### Mejoras Futuras
1. Métricas objetivas automatizadas (análisis de rima programático)
2. Cache de evaluaciones para análisis
3. Fine-tuning del verificador con ejemplos reales
4. Sistema adaptativo con umbrales por agente

## Impacto

- **Antes**: 100% agentes con 5/5 (falsos positivos)
- **Ahora**: Distribución realista 2.3-3.7 (métricas genuinas)
- **Beneficio**: Feedback real para mejora continua
- **Costo**: +1 llamada LLM por agente (~$0.002)