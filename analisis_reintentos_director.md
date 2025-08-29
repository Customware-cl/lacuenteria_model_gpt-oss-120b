# Análisis del Sistema de Reintentos - Caso Director (test-v2-emilia-1756417877)

## 📊 Flujo de Reintentos del Director

### 🔄 **INTENTO 1** (21:51:17 - 21:52:06)
```
1. EJECUCIÓN INICIAL
   ├── Carga prompt: flujo/v2/agentes/01_director.json
   ├── Carga dependencias: brief.json
   └── Genera Beat Sheet inicial
   
2. VERIFICACIÓN QA
   ├── verificador_qa evalúa el output
   ├── Detecta 5 problemas:
   │   • "Repetición excesiva del leitmotiv '¡Tiritán, tiritán!'"
   │   • "Variante 2 introduce lesión ligera (contenido sensible)"
   │   • "Inconsistencia en campos del beat_sheet"
   │   • "Conflictos sin resolución clara"
   │   • "Clímax poco marcado"
   └── Score: 2.7/5 ❌ (umbral: 3.5)
```

### 🔄 **INTENTO 2** (21:52:06 - 21:52:19)
```
1. PREPARACIÓN DEL REINTENTO
   ├── Llama a _retry_with_improvements()
   ├── Carga mismo system_prompt
   ├── Carga mismas dependencias
   └── CONSTRUYE PROMPT MEJORADO:
   
   [Prompt Original]
   + 
   ========================================
   ⚠️ RETROALIMENTACIÓN DEL VERIFICADOR DE CALIDAD ⚠️
   ========================================
   
   📊 PROBLEMAS DETECTADOS Y SOLUCIONES:
   1. Evitar repetición excesiva del leitmotiv
   2. No incluir contenido sensible para preescolares
   3. Mantener consistencia en estructura JSON
   
   📚 ERRORES COMUNES A EVITAR:
   - Ambigüedad en número de repeticiones
   - Estructura JSON inconsistente
   - Conflictos no visualizables
   
   ❌ PROBLEMAS ESPECÍFICOS ENCONTRADOS:
   - Repetición excesiva del leitmotiv "¡Tiritán, tiritán!"
   - Variante 2 introduce lesión ligera
   - Inconsistencia en campos del beat_sheet
   - Conflictos sin resolución clara
   - Clímax poco marcado
   
   🎯 IMPORTANTE: Genera nueva versión que ESPECÍFICAMENTE 
   resuelva los problemas mencionados arriba.
   ========================================

2. NUEVA GENERACIÓN
   └── Director genera nuevo Beat Sheet
   
3. NUEVA VERIFICACIÓN QA
   ├── Detecta NUEVOS problemas (diferentes):
   │   • "Repetición de '¡Brilla la fiesta!' más de 3 veces"
   │   • "Arco narrativo sin clímax claramente definido"
   │   • "Usa 'resolucion' en lugar de 'conflicto'"
   └── Score: 2.5/5 ❌ (EMPEORÓ)
```

### 🔄 **INTENTO 3** (21:52:19 - 21:52:34)
```
1. SEGUNDO REINTENTO
   ├── Mismo proceso que intento 2
   ├── Ahora con feedback ACUMULADO de ambos intentos
   └── Incluye todos los problemas detectados
   
2. TERCERA GENERACIÓN
   └── Director intenta nuevamente
   
3. VERIFICACIÓN FINAL
   ├── Mismos problemas persisten:
   │   • "Repetición de '¡Brilla la fiesta!'"
   │   • "Arco narrativo sin clímax"
   │   • "Escalada de tensión poco evidente"
   └── Score: 2.7/5 ❌
   
4. DECISIÓN FINAL
   └── max_retries (1 en v2) alcanzado
   └── Se marca como "devolución"
   └── ⚠️ NO SE GUARDA 01_director.json
```

## 🔍 Análisis del Problema

### ¿Por qué fallan los reintentos?

1. **El modelo no procesa correctamente el feedback**
   - A pesar de recibir instrucciones específicas, genera nuevos problemas
   - No mantiene las mejoras del intento anterior

2. **Cambio de contexto entre intentos**
   - Cada llamada al LLM es independiente
   - El modelo no "recuerda" sus intentos anteriores
   - Solo ve el prompt mejorado, no su output previo

3. **Problemas estructurales del prompt v2**
   - El prompt del director puede tener ambigüedades
   - Las restricciones pueden estar en conflicto

4. **Limitaciones del modelo GPT-OSS-120B**
   - Dificultad para seguir instrucciones complejas
   - Tendencia a generar patrones repetitivos
   - Problemas con estructuras JSON consistentes

## 🐛 Bug Crítico Identificado

**Cuando un agente falla QA después de reintentos:**
- El sistema NO guarda el archivo de salida (01_director.json)
- Esto rompe las dependencias de agentes posteriores
- El cuentacuentos necesita 01_director.json pero no existe
- El pipeline continúa pero está condenado a fallar

## 💡 Soluciones Propuestas

1. **Guardar output aunque falle QA**
   ```python
   # En agent_runner.py, línea ~201
   if not qa_passed:
       # SIEMPRE guardar output para no romper dependencias
       self._save_output(output_file, agent_output)
   ```

2. **Incluir output previo en reintentos**
   ```python
   # En _retry_with_improvements()
   user_prompt += "\nTU OUTPUT ANTERIOR (que falló):\n"
   user_prompt += json.dumps(previous_output, indent=2)
   user_prompt += "\n\nGENERA UNA VERSIÓN MEJORADA basándote en el feedback"
   ```

3. **Reducir complejidad del feedback**
   - Limitar a 3 problemas más críticos
   - Instrucciones más simples y directas
   - Un solo cambio por reintento

4. **Ajustar umbrales para v2**
   - Bajar umbral a 3.0 (ya está en 3.5)
   - O aceptar "mejora parcial" como éxito