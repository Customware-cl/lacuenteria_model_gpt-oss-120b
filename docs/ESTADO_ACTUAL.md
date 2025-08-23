# Estado Actual del Sistema Cuentería
*Última actualización: 22 de Agosto 2025*

## 🚀 Cambios Recientes Implementados

### 1. Sistema de Evaluación Dual (mode_verificador_qa)
- **Nueva funcionalidad**: Control sobre el tipo de evaluación QA
- **Parámetro**: `mode_verificador_qa` en `AgentRunner` y `StoryOrchestrator`
- **Opciones**:
  - `True` (default): Usa verificador_qa riguroso con métricas específicas por agente
  - `False`: Usa autoevaluación rápida (menos estricta)

### 2. Evaluación Crítica para Historias Externas
- **Endpoint directo LLM**: `http://69.19.136.204:8000/v1/chat/completions`
- **Sin necesidad de puerto 5000**: Usa el modelo GPT-OSS-120B directamente
- **Flexibilidad**: Acepta cualquier número de páginas (no limitado a 10)
- **Documentación completa**: Ver `docs/API_CONTRACT_EVALUATE_ENDPOINT.md`

### 3. Optimizaciones del Pipeline
- **Configuraciones diferenciadas por agente**: Temperaturas y tokens ajustados
- **Manejo de truncamiento**: Detección y recuperación automática
- **Feedback detallado**: Problemas específicos y sugerencias de mejora

## 📊 Métricas de Rendimiento Actuales

### Tiempos Promedio por Agente (con verificador_qa)
- Director: ~8-10s
- Psicoeducador: ~6-8s
- Cuentacuentos: ~10-12s
- Editor_claridad: ~8-10s
- Ritmo_rima: ~8-10s
- Continuidad: ~6-8s
- Diseño_escena: ~10-12s
- Dirección_arte: ~8-10s
- Sensibilidad: ~6-8s
- Portadista: ~6-8s
- Loader: ~6-8s
- Validador: ~12-15s

**Total pipeline**: ~100-130 segundos

### Scores QA Típicos (verificador_qa)
- Promedio general: 2.8-3.5/5
- Tasa de aprobación (≥4.0): ~30%
- Reintentos promedio: 1.5 por agente

## 🔧 Configuración Actual

### Modelo LLM
```python
{
    "model": "openai/gpt-oss-120b",
    "endpoint": "http://69.19.136.204:8000/v1/chat/completions",
    "timeout": 900,  # 15 minutos
    "default_temperature": 0.7,
    "default_max_tokens": 4000
}
```

### Umbrales QA
- **Verificador_qa**: 4.0/5 para aprobar
- **Autoevaluación**: 4.0/5 para aprobar (pero más permisiva)
- **Máximo reintentos**: 2 por agente

## 🐛 Issues Conocidos

### 1. Editor_claridad
- **Problema**: Ocasionalmente genera JSON corrupto o páginas vacías
- **Workaround**: Validación y regeneración automática
- **Estado**: Pendiente de fix definitivo

### 2. Ritmo_rima
- **Problema**: A veces no genera contenido completo
- **Workaround**: Prompt mejorado con instrucciones específicas
- **Estado**: Mejorado pero requiere monitoreo

### 3. Repeticiones en Cuentacuentos
- **Problema**: Uso excesivo de palabras como "mágico", "brillante"
- **Workaround**: Instrucciones específicas en prompt
- **Estado**: Parcialmente resuelto

## 📝 Archivos Clave del Sistema

### Core
- `src/agent_runner_optimized.py` - Ejecutor de agentes con QA
- `src/orchestrator.py` - Coordinador del pipeline
- `src/llm_client_optimized.py` - Cliente LLM con optimizaciones
- `src/api_server.py` - API REST (puerto 5000, solo local)

### Agentes
- `agentes/*.json` - Definiciones de los 12 agentes + crítico + verificador_qa

### Documentación
- `docs/API_CONTRACT_EVALUATE_ENDPOINT.md` - Contrato API actualizado
- `docs/EVALUACION_DIRECTA_LLM.md` - Guía para evaluación directa
- `docs/INSTRUCCIONES_LACUENTERIA_CL.md` - Instrucciones para el cliente

### Tests
- `test_verificador_modes.py` - Prueba ambos modos de verificación
- `test_complete_pipeline.py` - Prueba pipeline completo
- `test_direct_llm_evaluation.sh` - Prueba evaluación directa

## 🎯 Próximos Pasos Recomendados

1. **Calibración de QA**: Ajustar umbrales diferenciados por agente
2. **Fix definitivo editor_claridad**: Resolver problema de JSON corrupto
3. **Optimización de prompts**: Reducir repeticiones y mejorar calidad
4. **Cache de resultados**: Evitar re-procesar agentes exitosos
5. **Métricas consolidadas**: Dashboard de monitoreo en tiempo real

## 🚦 Estado de Servicios

| Servicio | Puerto | Estado | Acceso |
|----------|--------|--------|---------|
| LLM API (GPT-OSS-120B) | 8000 | ✅ Activo | Internet |
| API Cuentería | 5000 | ✅ Activo | Solo local |
| Verificador QA | N/A | ✅ Funcional | Interno |
| Webhook Client | N/A | ✅ Funcional | Saliente |

## 📌 Notas Importantes

1. **Modo Verificador QA**: En producción usar siempre `mode_verificador_qa=True`
2. **Evaluación Externa**: lacuenteria.cl debe usar endpoint directo en puerto 8000
3. **Timeouts**: Configurar mínimo 60s para evaluaciones, 900s para pipeline completo
4. **Estructura JSON**: Campos requeridos: `titulo`, `paginas`, `portada`, `loader`

---

*Para más detalles técnicos, consultar el código fuente y documentación específica de cada componente.*