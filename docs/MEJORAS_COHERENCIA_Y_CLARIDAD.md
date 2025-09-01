# Mejoras de Coherencia Narrativa y Edición Quirúrgica
**Fecha:** 2025-09-01  
**Versión:** v2 Pipeline

## 📋 Resumen Ejecutivo

Se implementaron mejoras significativas en dos agentes críticos del pipeline v2:
1. **Cuentacuentos (03)**: Añadida coherencia narrativa intra-página
2. **Editor de Claridad (04)**: Transformado a edición quirúrgica mínima

## 🎯 Problema Identificado

### Antes de las mejoras:
- **Cuentacuentos**: Generaba 4 versos por página sin garantizar conexión narrativa entre ellos
- **Editor de Claridad**: Reescribía hasta 80% del contenido, destruyendo coherencia y magia poética
- **Resultado**: Páginas con versos desconectados y pérdida de la esencia original

### Ejemplo del problema:
```
Original (Cuentacuentos):
"La nube gris quiere jugar al vuelo"

Editado (Editor viejo):
"Una nube gris sopla al cohete"
→ Cambió completamente el sentido, perdió la personificación
```

## ✅ Soluciones Implementadas

### 1. Cuentacuentos - Coherencia Narrativa

**Archivo modificado:** `/flujo/v2/agentes/03_cuentacuentos.json`

**Cambios principales:**
- Añadida sección "COHERENCIA DE PÁGINA"
- Estructura de 4 versos como mini-historia:
  - Verso 1: Establece escena
  - Verso 2: Desarrolla/añade elemento
  - Verso 3: Muestra reacción/consecuencia
  - Verso 4: Cierra o transiciona

**Nuevas verificaciones:**
```
□ ¿Los 4 versos de cada página fluyen conectadamente?
□ ¿Cada página presenta su beat de forma coherente?
```

### 2. Editor de Claridad - Enfoque Quirúrgico

**Archivo modificado:** `/flujo/v2/agentes/04_editor_claridad.json`

**Cambios principales:**
- MÁXIMO 25% de palabras cambiadas por página
- Preservar metáforas simples y personificaciones
- Editar SOLO lo que realmente confunde
- Nuevo campo: `porcentaje_editado` para transparencia

**Nuevos principios:**
```
CUÁNDO EDITAR (✅):
- Palabras técnicas o filosóficas
- Referencias sin antecedente claro
- Sintaxis enredada

CUÁNDO NO EDITAR (❌):
- Metáforas simples ('la nube quiere jugar')
- Personificaciones apropiadas
- Versos claros en contexto
```

### 3. Criterios de Evaluación Actualizados

**Archivos modificados:**
- `/flujo/v2/criterios_evaluacion/03_cuentacuentos.json`
- `/flujo/v2/criterios_evaluacion/04_editor_claridad.json`

**Nuevas métricas:**

**Cuentacuentos:**
- `coherencia_pagina` (peso 0.15):
  - flujo_interno
  - unidad_tematica
  - progresion_clara
  - contexto_mantenido

**Editor de Claridad:**
- `coherencia_narrativa` (peso 0.4):
  - unidad_narrativa
  - preservacion_sentido
  - metaforas_preservadas
- `edicion_quirurgica` (peso 0.35):
  - porcentaje_editado < 25%
  - cambios_necesarios

## 📊 Resultados de las Mejoras

### Test comparativo (test-v2-paralelo-20250901-192231)

**Cuentacuentos - Coherencia lograda:**
```
Página 1:
Verso 1: Emilia ve el mapa y su cara brilla
Verso 2: Caty corre feliz bajo rosas destella
Verso 3: El viento suelta el papel y sube al cielo
Verso 4: Caty ríe y grita ¡qué vuelo!

✅ Flujo narrativo claro: descubrimiento → acción → evento → reacción
```

**Editor de Claridad - Edición mínima:**
```
Porcentajes de edición por página:
- Página 1: 7%
- Página 6: 4%
- Páginas 9-10: 0%
- Promedio: ~6% (muy por debajo del 25% límite)
```

## 🚀 Impacto

1. **Mayor coherencia narrativa**: Cada página cuenta una historia completa
2. **Preservación poética**: Se mantienen metáforas y personificaciones
3. **Edición precisa**: Solo se cambia lo estrictamente necesario
4. **Mejor flujo de lectura**: Los versos conectan naturalmente

## 📝 Notas Técnicas

### Configuración de tokens:
- 30,000 tokens por página (cuentacuentos)
- 30,000 tokens para verificación QA

### Estructura de carpetas:
```
runs/{story_id}/
  ├── outputs/
  │   ├── agents/     # Salidas de agentes
  │   ├── pages/      # Páginas individuales
  │   ├── qa/         # Verificaciones QA
  │   └── feedback/   # Retroalimentación
```

## 🔄 Próximos Pasos Sugeridos

1. Ajustar agente 05_ritmo_rima para tolerar 8-15 sílabas (consistente con cuentacuentos)
2. Monitorear métricas de coherencia en próximas generaciones
3. Considerar añadir ejemplos de buena coherencia al prompt del cuentacuentos

## 📌 Referencias

- Issue relacionado: Mejora de coherencia narrativa y edición destructiva
- Pipeline: v2
- Fecha de implementación: 2025-09-01