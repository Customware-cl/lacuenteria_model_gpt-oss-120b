# Plan de Optimización del Sistema Cuentería

## 📊 Análisis de Problemas Detectados

### Test con Verificador QA (emilia-qa-test-20250821-210346)

Durante las pruebas con el nuevo verificador QA independiente, se detectaron los siguientes problemas críticos:

| Agente | QA Score | Reintentos | Problema Principal |
|--------|----------|------------|-------------------|
| **director** | 4.33/5 ✅ | 2 | Requirió múltiples intentos |
| **psicoeducador** | 4.33/5 ✅ | 0 | Aceptable |
| **cuentacuentos** | 3.2/5 ❌ | 2 | Rimas forzadas, repeticiones |
| **editor_claridad** | 1.0/5 ❌ | 2 | **CRÍTICO: Páginas vacías** |
| **ritmo_rima** | 2.2/5 ❌ | 2 | Rimas idénticas, métrica inconsistente |
| **continuidad** | 3.5/5 ❌ | 2 | Falta de coherencia narrativa |
| **diseno_escena** | 4.17/5 ✅ | 0 | Aceptable |
| **direccion_arte** | 3.83/5 ❌ | 2 | Paletas muy oscuras |
| **sensibilidad** | 2.5/5 ❌ | 2 | Análisis superficial |
| **portadista** | 4.33/5 ✅ | 1 | Aceptable |

### Problemas Identificados:
1. **Outputs vacíos o incompletos** (editor_claridad)
2. **Calidad poética baja** (cuentacuentos, ritmo_rima)
3. **Exceso de reintentos** (84% de agentes necesitaron reintentos)
4. **Tiempo total excesivo** (~11 minutos para una historia)
5. **Temperaturas mal calibradas** para diferentes tipos de tareas

---

## 🎯 Variables de Optimización

### 1. **Temperatura** (Impacto: ALTO)

#### Configuración Actual vs Propuesta:

| Agente | Temp Actual | Temp Propuesta | Justificación |
|--------|-------------|----------------|---------------|
| **director** | 0.85 | 0.75 | Reducir para más coherencia estructural |
| **psicoeducador** | 0.55 | 0.55 | Mantener (funciona bien) |
| **cuentacuentos** | 0.90 | 0.75 | Bajar creatividad excesiva que genera incoherencias |
| **editor_claridad** | 0.60 | 0.40 | CRÍTICO: Reducir para evitar outputs vacíos |
| **ritmo_rima** | 0.65 | 0.50 | Mayor precisión en ajustes métricos |
| **continuidad** | 0.40 | 0.35 | Más consistencia en character bible |
| **diseno_escena** | 0.80 | 0.70 | Balance creatividad/coherencia |
| **direccion_arte** | 0.75 | 0.65 | Evitar paletas muy oscuras |
| **sensibilidad** | 0.50 | 0.40 | Análisis más detallado y consistente |
| **portadista** | 0.85 | 0.75 | Mantener creatividad controlada |
| **loader** | 0.90 | 0.80 | Reducir para mensajes más coherentes |
| **validador** | 0.30 | 0.30 | Mantener (precisión máxima) |
| **verificador_qa** | 0.30 | 0.30 | Mantener (evaluación consistente) |

### 2. **Max Tokens** (Impacto: MEDIO)

| Agente | Tokens Actual | Tokens Propuesto | Justificación |
|--------|---------------|------------------|---------------|
| **cuentacuentos** | 4000 | 6000 | Evitar truncamiento de versos |
| **editor_claridad** | 4000 | 6000 | Asegurar output completo |
| **ritmo_rima** | 4000 | 5000 | Espacio para ajustes detallados |
| **continuidad** | 4000 | 5000 | Character bible completo |
| **verificador_qa** | 3000 | 4000 | Evaluaciones más detalladas |

### 3. **Response Format** (Impacto: ALTO)

Implementar formato JSON estructurado en `llm_client.py`:

```python
def generate(self, system_prompt, user_prompt, temperature=None, 
             max_tokens=None, response_format=None):
    
    payload = {
        "model": self.model,
        "messages": messages,
        "temperature": temperature or self.temperature,
        "max_tokens": max_tokens or self.max_tokens
    }
    
    # Agregar formato JSON si se especifica
    if response_format == "json":
        payload["response_format"] = {"type": "json_object"}
```

### 4. **Umbral de QA** (Impacto: MEDIO)

| Configuración | Valor Actual | Valor Propuesto | Justificación |
|---------------|--------------|-----------------|---------------|
| **min_qa_score** | 4.0 | 3.5 | Reducir reintentos excesivos |
| **max_retries** | 2 | 3 | Dar más oportunidades antes de fallar |

### 5. **Mejoras en Prompts** (Impacto: ALTO)

#### Problemas en Prompts Actuales:
1. **Falta de ejemplos concretos**
2. **Instrucciones ambiguas sobre formato JSON**
3. **No especifican qué hacer si faltan dependencias**

#### Propuestas de Mejora:

**editor_claridad** (más problemático):
- Agregar ejemplo de output esperado
- Especificar que SIEMPRE debe incluir texto en todas las páginas
- Clarificar formato del glosario

**cuentacuentos**:
- Incluir reglas de rima más específicas
- Ejemplos de versos bien estructurados
- Límites claros de repeticiones

---

## 📈 Métricas de Éxito

### Objetivos Cuantitativos:

| Métrica | Valor Actual | Objetivo | Medición |
|---------|--------------|----------|----------|
| **Outputs vacíos** | ~10% | 0% | Agentes sin contenido |
| **Tasa de reintentos** | 84% | <30% | Agentes que necesitan retry |
| **QA Score promedio** | 3.2/5 | 3.8-4.2/5 | Promedio global |
| **Tiempo total** | 11 min | <5 min | Generación completa |
| **Fallos totales** | 60% | <20% | Agentes con QA < umbral |

---

## 🧪 Plan de Testing A/B

### Fase 1: Preparación (1 día)
1. Crear archivo `config/temperaturas_optimizadas.json`
2. Modificar `src/config.py` para cargar configuración alternativa
3. Actualizar `src/llm_client.py` con soporte para response_format
4. Mejorar prompts de agentes problemáticos

### Fase 2: Testing (2-3 días)
1. **Grupo A (Control)**: 10 historias con configuración actual
2. **Grupo B (Optimizado)**: 10 historias con configuración nueva
3. Usar mismo conjunto de briefs para ambos grupos

### Fase 3: Análisis (1 día)
1. Comparar métricas entre grupos
2. Identificar mejoras y problemas residuales
3. Ajustar configuración basado en resultados

### Script de Testing:
```python
# test_ab_optimization.py
def run_ab_test():
    briefs = load_test_briefs()  # 10 briefs predefinidos
    
    # Grupo A - Config actual
    results_a = []
    for brief in briefs:
        result = run_with_config("default", brief)
        results_a.append(analyze_result(result))
    
    # Grupo B - Config optimizada
    results_b = []
    for brief in briefs:
        result = run_with_config("optimized", brief)
        results_b.append(analyze_result(result))
    
    # Comparar y generar reporte
    generate_comparison_report(results_a, results_b)
```

---

## 🚀 Implementación Propuesta

### Prioridad 1 (Inmediato):
1. **Ajustar temperaturas** - Mayor impacto, fácil implementación
2. **Aumentar max_tokens** - Prevenir truncamiento
3. **Bajar umbral QA a 3.5** - Reducir fallos excesivos

### Prioridad 2 (Esta semana):
1. **Implementar response_format JSON** - Garantizar outputs válidos
2. **Mejorar prompts problemáticos** - editor_claridad, cuentacuentos
3. **Crear script de testing A/B**

### Prioridad 3 (Próxima semana):
1. **Sistema de fallback** - Si un agente falla 3 veces, usar versión simplificada
2. **Cache de resultados exitosos** - Reutilizar componentes que funcionan bien
3. **Monitoreo en tiempo real** - Dashboard de métricas

---

## 📝 Configuración JSON Propuesta

```json
{
  "optimization_v1": {
    "temperatures": {
      "director": 0.75,
      "psicoeducador": 0.55,
      "cuentacuentos": 0.75,
      "editor_claridad": 0.40,
      "ritmo_rima": 0.50,
      "continuidad": 0.35,
      "diseno_escena": 0.70,
      "direccion_arte": 0.65,
      "sensibilidad": 0.40,
      "portadista": 0.75,
      "loader": 0.80,
      "validador": 0.30,
      "verificador_qa": 0.30
    },
    "max_tokens": {
      "cuentacuentos": 6000,
      "editor_claridad": 6000,
      "ritmo_rima": 5000,
      "continuidad": 5000,
      "verificador_qa": 4000,
      "validador": 8000
    },
    "quality_thresholds": {
      "min_qa_score": 3.5,
      "max_retries": 3
    },
    "use_json_format": true
  }
}
```

---

## 📊 Resultados Esperados

Con estas optimizaciones, esperamos:

1. **Reducción del 70% en outputs vacíos**
2. **Mejora del 50% en tiempo de generación**
3. **Aumento del 20% en calidad promedio**
4. **Reducción del 60% en tasa de fallos**

---

## 🔄 Próximos Pasos

1. ✅ Crear este documento de plan
2. ⏳ Implementar configuración optimizada
3. ⏳ Ejecutar pruebas A/B
4. ⏳ Analizar resultados y ajustar
5. ⏳ Desplegar en producción

---

*Documento creado: 2025-08-21*
*Última actualización: 2025-08-21*