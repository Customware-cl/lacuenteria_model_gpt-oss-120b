# Sistema de Feedback Loop y Análisis de Conflictos v2

## Descripción General

El sistema v2 implementa un mecanismo inteligente de detección y corrección de conflictos entre prompts de agentes y evaluaciones del verificador QA. Aprende de cada fallo para mejorar los reintentos y generar insights para optimización de prompts.

## Componentes Principales

### 1. **ConflictAnalyzer** (`src/conflict_analyzer.py`)
- Analiza fallos de QA para detectar patrones de conflicto
- Identifica líneas específicas del prompt que causan problemas
- Genera recomendaciones accionables para reintentos
- Mantiene histórico de patrones para análisis estadístico

### 2. **Dashboard de Conflictos** (`flujo/v2/qa_conflict_dashboard.json`)
- Registro persistente de todos los conflictos detectados
- Contador de ocurrencias por patrón
- Lista de historias afectadas
- Recomendaciones específicas por tipo de problema

### 3. **Feedback Loop Mejorado** (`src/agent_runner.py`)
- Inyecta feedback específico del verificador en reintentos
- Consulta patrones conocidos del dashboard
- Aplica recomendaciones basadas en errores frecuentes
- Proporciona contexto detallado al agente para corrección

## Patrones de Conflicto Detectados

### Director
- `leitmotiv_repetition_conflict`: Ambigüedad en número de repeticiones
- `missing_resolution_field`: Estructura JSON inconsistente
- `internal_conflict_not_visual`: Conflictos no visualizables

### Cuentacuentos
- `metro_not_specified`: Falta restricción de sílabas
- `forced_rhyme`: Rimas forzadas o artificiales
- `word_repetition_excessive`: Repetición excesiva de palabras

### Editor Claridad
- `missing_glossary_field`: Campo glosario faltante
- `abstract_language`: Lenguaje demasiado abstracto

### Ritmo Rima
- `poor_rhyme_quality`: Rimas pobres o repetitivas
- `syntactic_inversion`: Inversiones sintácticas forzadas

## Mejoras Implementadas en Prompts v2

1. **Instrucciones más específicas**: Números exactos en lugar de rangos
2. **Restricciones métricas claras**: 8-10 sílabas por verso
3. **Eliminación de QA hardcodeado**: No más autoevaluación 5/5
4. **Campos JSON bien definidos**: Sin ambigüedades en estructura

## Uso del Sistema

### Ejecutar Pipeline v2
```python
from src.orchestrator import StoryOrchestrator

orchestrator = StoryOrchestrator(
    story_id="mi-historia",
    mode_verificador_qa=True,
    pipeline_version='v2'
)

result = orchestrator.process_story(brief)
```

### Analizar Conflictos
```python
from src.conflict_analyzer import get_conflict_analyzer

analyzer = get_conflict_analyzer('v2')
report = analyzer.generate_improvement_report()
print(report)
```

### Consultar Dashboard
```bash
cat flujo/v2/qa_conflict_dashboard.json | jq '.'
```

## Flujo de Trabajo

1. **Ejecución Normal**: Agente genera output
2. **Verificación QA**: verificador_qa evalúa con criterios estrictos
3. **Si falla QA**:
   - ConflictAnalyzer detecta patrones
   - Actualiza dashboard con nuevo patrón o incrementa contador
   - Genera recomendaciones específicas
4. **Reintento Inteligente**:
   - Inyecta feedback del verificador
   - Aplica recomendaciones del dashboard
   - Incluye errores comunes a evitar
5. **Aprendizaje Continuo**: Dashboard acumula conocimiento

## Beneficios del Sistema

- **Evaluaciones Realistas**: Scores entre 2-4 en lugar de siempre 5
- **Reintentos Efectivos**: Feedback específico en lugar de genérico
- **Identificación de Patrones**: Problemas recurrentes se vuelven visibles
- **Mejora Continua**: Base de datos para optimización de prompts
- **Trazabilidad**: Histórico completo de conflictos por historia

## Análisis Manual Regular

El dashboard debe ser revisado periódicamente para:
1. Identificar prompts que necesitan actualización
2. Detectar conflictos entre agentes consecutivos
3. Priorizar mejoras basadas en frecuencia
4. Validar que las correcciones funcionan

## Ejemplo de Dashboard

```json
{
  "conflict_patterns": {
    "cuentacuentos": {
      "metro_not_specified": {
        "count": 5,
        "typical_issue": "metro varía entre 12-16 sílabas",
        "recommendation": "Agregar: 'cada verso 8-10 sílabas máximo'",
        "stories_affected": ["story1", "story2", "story3"]
      }
    }
  }
}
```

## Testing

```bash
# Prueba rápida del sistema v2 con feedback
python test_v2_feedback.py

# Prueba completa
python test_flujo_completo.py --version v2
```

## Notas Importantes

- El sistema NO modifica automáticamente los prompts
- Análisis manual regular es esencial para mejoras
- Dashboard se actualiza en cada fallo de QA
- Recomendaciones se vuelven más precisas con el tiempo