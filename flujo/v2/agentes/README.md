# Documentación de Agentes - Sistema Cuentería

## 📋 Índice de Agentes

Este directorio contiene las definiciones JSON de los 12 agentes especializados que conforman el pipeline de generación de cuentos infantiles.

## 🎭 Agentes del Pipeline

### 1. Orquestador (`orquestador.json`)
**Rol**: Coordinador maestro del pipeline editorial  
**Responsabilidades**:
- Ejecutar el flujo secuencial de agentes
- Verificar quality gates (QA ≥ 4) entre pasos
- Gestionar retrocesos cuando QA < 4
- Mantener trazabilidad de artefactos

**Flujo de ejecución**:
1. Director → 2. Psicoeducador → 3. Cuentacuentos → 4. Editor Claridad → 5. Ritmo/Rima → 6. Continuidad → 7. Diseño Escena → 8. Dirección Arte → 9. Sensibilidad → 10. Portadista → 11. Loader → 12. Validador

---

### 2. Director (`director.json`)
**Rol**: Director creativo de narrativa infantil  
**Entrada**: `{personajes}`, `{historia}`, `{mensaje_a_transmitir}`, `edad_objetivo`  
**Salida JSON**:
```json
{
  "leitmotiv": "frase musical repetible",
  "beat_sheet": [
    {
      "pagina": 1,
      "objetivo": "qué busca el personaje",
      "conflicto": "obstáculo o tensión",
      "emocion": "sentimiento dominante",
      "imagen_nuclear": "escena visual clave"
    }
  ],
  "variantes": [
    {
      "climax_alternativo": "opción A",
      "resolucion_alternativa": "desenlace A"
    }
  ],
  "qa": {
    "arco_completo": 1-5,
    "claridad_visual": 1-5,
    "potencia_leitmotiv": 1-5
  }
}
```

**Principios**:
- Claridad visual (escenas filmables)
- Emoción creciente hasta clímax
- Resolución cálida y esperanzadora
- Leitmotiv repetible 3-4 veces
- Evitar sermones y metáforas oscuras

---

### 3. Psicoeducador (`psicoeducador.json`)
**Rol**: Psicólogo infantil/psicoeducador  
**Entrada**: Beat Sheet, `{mensaje_a_transmitir}`, `edad_objetivo`  
**Salida JSON**:
```json
{
  "metas_generales": ["meta 1", "meta 2"],
  "mapa_psico_narrativo": [
    {
      "pagina": 1,
      "micro_habilidad": "habilidad específica",
      "frase_modelo": "ejemplo de diálogo",
      "recurso": "técnica psicoeducativa",
      "evitar": "qué no hacer"
    }
  ],
  "banderas": ["alerta 1", "alerta 2"],
  "qa": {
    "ajuste_edad": 1-5,
    "alineacion_mensaje": 1-5,
    "tono_amable": 1-5
  }
}
```

**Recursos psicoeducativos**:
- Respiración consciente
- Etiquetado emocional
- Autocontrol por pasos
- Pedir ayuda
- Sustituciones conductuales

---

### 4. Cuentacuentos (`cuentacuentos.json`)
**Rol**: Experto en lírica infantil  
**Entrada**: Beat Sheet, Mapa psico-narrativo  
**Salida JSON**:
```json
{
  "paginas_texto": {
    "1": "Verso uno aquí\nVerso dos aquí\nVerso tres aquí\nVerso cuatro aquí",
    "2": "..."
  },
  "leitmotiv_usado_en": [2, 4, 7, 10],
  "qa": {
    "emocion": 1-5,
    "claridad_visual": 1-5,
    "uso_leitmotiv": 1-5
  }
}
```

**Especificaciones técnicas**:
- 4-5 versos por página
- 7-12 palabras por verso
- 6-8 sílabas aproximadas
- Rima consonante preferente
- Esquemas variados (ABAB, AABB)
- Prohibido repetir palabra final en versos consecutivos

---

### 5. Editor de Claridad (`editor_claridad.json`)
**Rol**: Editor de comprensibilidad  
**Entrada**: Texto del cuentacuentos  
**Salida JSON**:
```json
{
  "paginas_texto_claro": {
    "1": "texto clarificado",
    "2": "..."
  },
  "glosario": [
    {
      "original": "palabra compleja",
      "simple": "sinónimo simple"
    }
  ],
  "cambios_clave": ["cambio 1", "cambio 2"],
  "qa": {
    "comprensibilidad": 1-5,
    "imagen_inequivoca": 1-5
  }
}
```

**Objetivos**:
- Una idea visual por verso
- Eliminar ambigüedades
- Simplificar vocabulario
- Mantener coherencia temporal/causal

---

### 6. Ritmo y Rima (`ritmo_rima.json`)
**Rol**: Entrenador de musicalidad  
**Entrada**: Texto clarificado  
**Salida JSON**:
```json
{
  "paginas_texto_pulido": {
    "1": "texto con ritmo mejorado",
    "2": "..."
  },
  "esquema_rima": {
    "1": "ABAB",
    "2": "AABB"
  },
  "finales_de_verso": {
    "1": ["palabra1", "palabra2", "palabra3", "palabra4"]
  },
  "qa": {
    "fluidez": 1-5,
    "consistencia_rima": 1-5,
    "variacion_cierres": 1-5
  }
}
```

**Criterios**:
- Garantizar variedad en palabras finales
- Consistencia de esquema
- Evitar rimas pobres/forzadas
- Mantener naturalidad

---

### 7. Continuidad (`continuidad.json`)
**Rol**: Responsable de Character Bible  
**Entrada**: Texto pulido, personajes  
**Salida JSON**:
```json
{
  "character_bible": [
    {
      "nombre": "protagonista",
      "edad": "6 años",
      "rasgos_visibles": "cabello rizado, ojos grandes",
      "vestuario": "camiseta azul, pantalón corto",
      "colores_clave": ["azul", "amarillo"],
      "objeto_ancla": "mochila roja",
      "gestos": "sonrisa tímida, manos en bolsillos",
      "no_haria": "gritar, ser agresivo"
    }
  ],
  "continuidad_narrativa": {
    "relaciones": "descripción de vínculos",
    "evolucion_emocional": "arco de transformación",
    "objeto_ancla_reapariciones": [
      {
        "personaje": "protagonista",
        "paginas": [2, 5, 9]
      }
    ]
  },
  "qa": {
    "coherencia_rasgos": 1-5,
    "utilidad_arte": 1-5
  }
}
```

**Requisitos**:
- Cada protagonista tiene 1 objeto ancla
- Objeto ancla aparece en mínimo 3 páginas
- Consistencia visual completa

---

### 8. Diseño de Escena (`diseno_escena.json`)
**Rol**: Prompt Engineer Visual  
**Entrada**: Texto final, Character Bible  
**Salida JSON**:
```json
{
  "prompts_paginas": {
    "1": "Descripción visual detallada con entorno, acción, emoción, objetos, iluminación, composición",
    "2": "..."
  },
  "anotaciones": [
    "p1 plano general luminoso",
    "p2 primer plano gesto emocional"
  ],
  "qa": {
    "alineacion_verso_escena": 1-5,
    "variedad_planos": 1-5
  }
}
```

**Elementos obligatorios por prompt**:
- Entorno/locación
- Acción principal
- Emoción dominante
- 1-2 objetos ancla
- Momento del día/iluminación
- Composición (tipo de plano, ángulo)
- Estilo: "ilustración infantil colorida"

---

### 9. Sensibilidad (`sensibilidad.json`)
**Rol**: Auditor de seguridad infantil  
**Entrada**: Texto y prompts visuales  
**Salida JSON**:
```json
{
  "riesgos_detectados": [
    {
      "pagina": 1,
      "detalle": "descripción específica",
      "riesgo": "tipo de riesgo"
    }
  ],
  "correcciones_sugeridas": [
    {
      "pagina": 1,
      "texto_o_prompt": "versión corregida"
    }
  ],
  "apto_para_ninos": true,
  "qa": {
    "seguridad_respecto": 1-5
  }
}
```

**Detecta y corrige**:
- Miedo excesivo
- Estereotipos
- Lenguaje adulto
- Culpabilización
- Medicalización
- Duelo complejo

---

### 10. Portadista (`portadista.json`)
**Rol**: Creador de títulos y portadas  
**Entrada**: Cuento completo  
**Salida JSON**:
```json
{
  "titulos": [
    "Opción 1",
    "Opción 2",
    "Opción 3"
  ],
  "portada": {
    "prompt": "Descripción visual de portada con personajes, objeto ancla, atmósfera, composición"
  },
  "qa": {
    "recordabilidad_titulo": 1-5,
    "sintesis_emotiva": 1-5
  }
}
```

**Criterios para títulos**:
- Memorables y musicales
- Claros para edad objetivo
- Reflejan esencia emocional

---

### 11. Loader (`loader.json`)
**Rol**: Generador de mensajes de carga  
**Entrada**: Elementos del cuento (título, personajes, leitmotiv, etc.)  
**Salida JSON**:
```json
{
  "loader": [
    "Mensaje personalizado 1",
    "Mensaje personalizado 2",
    "...",
    "Mensaje personalizado 10"
  ],
  "qa": {
    "pertinencia": 1-5,
    "brevedad_tono": 1-5,
    "sensacion_adaptativa": 1-5
  }
}
```

**Especificaciones**:
- 10 mensajes exactos
- Máximo 70 caracteres
- Efecto WOW
- Sensación de adaptación en vivo
- Referencias concretas a la historia
- Tono cálido y mágico

---

### 12. Validador (`validador.json`)
**Rol**: Ensamblador y verificador final  
**Entrada**: Todos los artefactos previos  
**Salida JSON** (FINAL):
```json
{
  "titulo": "Título elegido",
  "paginas": {
    "1": {
      "texto": "4-5 versos\nseparados por \\n",
      "prompt": "descripción visual completa"
    },
    "2": { "..." },
    "10": { "..." }
  },
  "portada": {
    "prompt": "descripción de portada"
  },
  "loader": [
    "mensaje 1",
    "mensaje 2",
    "...",
    "mensaje 10"
  ]
}
```

**Verificaciones**:
- JSON válido y bien formateado
- Claves exactas ("1" a "10" como strings)
- 4-5 versos por página
- Sin numeración ni viñetas
- Leitmotiv aparece 3-4 veces máximo
- No repetir palabra final en versos consecutivos
- Coherencia total con Character Bible
- Todo en español correcto

---

## 🔄 Flujo de Quality Gates

Cada agente autoevalúa su trabajo con puntajes QA (1-5):
- **QA ≥ 4**: Continúa al siguiente agente
- **QA < 4**: Retorna al agente anterior con instrucciones específicas
- **Iteraciones**: Hasta alcanzar calidad deseada

## 📝 Notas de Implementación

1. **Formato estricto**: Todos los agentes devuelven únicamente JSON
2. **Sin texto adicional**: Nada fuera de la estructura JSON definida
3. **Idioma**: Español en todos los contenidos
4. **Trazabilidad**: Cada artefacto mantiene referencia a su origen
5. **Modularidad**: Cada agente es independiente y reemplazable

## 🚀 Extensibilidad

Para agregar un nuevo agente:
1. Crear archivo JSON con estructura de rol y contrato
2. Definir entrada/salida clara
3. Incluir autoevaluación QA
4. Actualizar orquestador con nueva posición en pipeline
5. Documentar en este README

## 💡 Mejores Prácticas

- **Especificidad**: Prompts claros y accionables
- **Medibilidad**: QA scores objetivos
- **Coherencia**: Respetar contratos entre agentes
- **Iteración**: Permitir mejoras incrementales
- **Documentación**: Mantener ejemplos actualizados