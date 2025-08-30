# Configuración v2 - Sistema Autocontenido

## Descripción
La versión v2 del pipeline de Cuentería está diseñada para ser completamente autocontenida, con toda su configuración almacenada dentro del directorio `/flujo/v2/`. Esto garantiza que los cambios en otras versiones (v1, v3, etc.) nunca afecten el funcionamiento de v2.

## Estructura de Archivos

```
flujo/v2/
├── agentes/              # Definiciones de agentes (prompts)
├── criterios_evaluacion/ # Criterios de evaluación QA
├── agent_config.json     # ⭐ Configuración granular por agente
├── config.json          # Configuración del pipeline
├── dependencies.json    # Dependencias entre agentes
└── README.md           # Esta documentación
```

## Configuración Granular por Agente

### Archivo: `agent_config.json`

Este archivo contiene la configuración específica para cada agente del pipeline. Cada agente puede tener los siguientes parámetros configurables:

```json
{
  "01_director": {
    "temperature": 0.7,      // Creatividad (0.0 = determinista, 1.0 = muy creativo)
    "max_tokens": 20000,     // Límite de tokens de respuesta
    "top_p": 0.95,          // Nucleus sampling (diversidad de vocabulario)
    "qa_threshold": 3.5     // Umbral mínimo de calidad (1-5)
  },
  ...
}
```

### Parámetros Configurables

#### `temperature` (0.0 - 1.0)
- **Bajo (0.3)**: Respuestas más predecibles y consistentes. Ideal para validación y análisis.
- **Medio (0.5-0.7)**: Balance entre creatividad y coherencia. Bueno para narrativa.
- **Alto (0.8-1.0)**: Mayor creatividad y variabilidad. Útil para diseño visual y arte.

#### `max_tokens`
- Define el límite máximo de tokens que el modelo puede generar
- Valor típico: 20000 (suficiente para respuestas JSON complejas)
- Verificador QA usa 30000 por la naturaleza extensa de sus evaluaciones

#### `top_p` (0.0 - 1.0)
- Controla el nucleus sampling (conjunto de palabras más probables a considerar)
- **0.85**: Más conservador, vocabulario más limitado
- **0.95**: Más diverso, considera más opciones de vocabulario
- Complementa a `temperature` para control fino de la generación

#### `qa_threshold` (1.0 - 5.0)
- Define el puntaje mínimo de calidad para que el output sea aceptado
- Si el QA score < threshold, el agente reintenta (máx 2 veces)
- **3.5**: Estándar para mayoría de agentes
- **4.0**: Más estricto para agentes críticos (cuentacuentos, sensibilidad, validador)
- **null**: Para verificador_qa (no se autoevalúa)

## Valores Recomendados por Tipo de Agente

### Agentes Creativos/Artísticos
- `07_diseno_escena`, `08_direccion_arte`, `11_loader`
- **temperature**: 0.8
- **top_p**: 0.95
- **Razón**: Necesitan mayor libertad creativa para generar descripciones visuales y artísticas

### Agentes Narrativos
- `01_director`, `03_cuentacuentos`, `10_portadista`
- **temperature**: 0.6-0.7
- **top_p**: 0.92-0.95
- **Razón**: Balance entre creatividad narrativa y coherencia estructural

### Agentes Técnicos/Editoriales
- `04_editor_claridad`, `05_ritmo_rima`, `06_continuidad`
- **temperature**: 0.3-0.5
- **top_p**: 0.85-0.9
- **Razón**: Requieren precisión y consistencia en sus ajustes

### Agentes de Validación
- `09_sensibilidad`, `12_validador`, `13_critico`, `14_verificador_qa`
- **temperature**: 0.3
- **top_p**: 0.85
- **Razón**: Necesitan evaluaciones consistentes y objetivas

## Cómo Modificar la Configuración

1. **Editar el archivo**: Abre `/flujo/v2/agent_config.json`
2. **Modificar valores**: Ajusta los parámetros del agente deseado
3. **Guardar**: Los cambios se aplicarán automáticamente en la próxima ejecución

### Ejemplo: Hacer al cuentacuentos más creativo

```json
"03_cuentacuentos": {
  "temperature": 0.8,      // Aumentado de 0.6
  "max_tokens": 20000,
  "top_p": 0.98,          // Aumentado de 0.92
  "qa_threshold": 4.0
}
```

### Ejemplo: Hacer al validador más estricto

```json
"12_validador": {
  "temperature": 0.2,      // Reducido de 0.3
  "max_tokens": 25000,    // Aumentado para JSONs grandes
  "top_p": 0.8,           // Reducido de 0.85
  "qa_threshold": 4.5     // Aumentado de 4.0
}
```

## Ventajas del Sistema Autocontenido

1. **Aislamiento Total**: Los cambios en v1 o v3 nunca afectan v2
2. **Versionado Claro**: Cada versión tiene su propia configuración completa
3. **Experimentación Segura**: Puedes probar configuraciones sin afectar producción
4. **Trazabilidad**: Toda la configuración de v2 está en un solo lugar
5. **Migración Simple**: Para crear v3, solo copia `/flujo/v2/` y ajusta

## Notas Técnicas

- La configuración se carga automáticamente desde `load_version_config('v2')` en `src/config.py`
- `AgentRunner` detecta automáticamente si está ejecutando v2 y usa la configuración granular
- El sistema mantiene compatibilidad con v1 que usa configuración hardcodeada
- Los valores de `agent_config.json` tienen prioridad sobre cualquier valor global

## Troubleshooting

### El agente no usa mi configuración
- Verifica que el nombre del agente en `agent_config.json` coincida exactamente (ej: `01_director`)
- Confirma que estás ejecutando con `pipeline_version='v2'`

### Quiero valores por defecto diferentes
- Modifica los valores en `agent_config.json`
- No hay valores "globales" en v2, cada agente debe configurarse individualmente

### Error al cargar configuración
- Verifica que `agent_config.json` sea JSON válido (sin comas finales, comillas correctas)
- Usa un validador JSON online si tienes dudas

## Contacto
Para preguntas o sugerencias sobre la configuración v2, crear un issue en el repositorio.