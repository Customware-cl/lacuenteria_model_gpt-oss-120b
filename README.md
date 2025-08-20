# Cuentería - Sistema de Generación de Cuentos Infantiles

## ⚠️ Estado Actual: En Desarrollo

**Nota Importante**: El sistema presenta limitaciones con respuestas largas del modelo GPT-OSS-120B que afectan algunos agentes. Ver [`docs/LIMITACIONES_MODELO.md`](docs/LIMITACIONES_MODELO.md) para detalles técnicos.

## 📚 Descripción

Cuentería es un sistema multiagente basado en IA para la creación automatizada de cuentos infantiles personalizados. El sistema orquesta 12 agentes especializados que trabajan en conjunto para producir narrativas infantiles completas con texto e indicaciones visuales, garantizando calidad pedagógica, literaria y sensibilidad cultural.

## 🎯 Objetivo

Generar cuentos infantiles de 10 páginas que:
- Transmitan mensajes educativos específicos
- Sean apropiados para la edad objetivo
- Mantengan coherencia narrativa y visual
- Incluyan elementos psicoeducativos
- Garanticen sensibilidad cultural y seguridad infantil

## 🏗️ Arquitectura del Sistema

### Pipeline de Agentes

El sistema ejecuta un flujo secuencial con quality gates entre cada paso:

1. **Director** → Diseña la estructura narrativa (Beat Sheet)
2. **Psicoeducador** → Define metas conductuales y recursos psicológicos
3. **Cuentacuentos** → Convierte la estructura en versos líricos
4. **Editor de Claridad** → Optimiza la comprensibilidad del texto
5. **Ritmo y Rima** → Perfecciona la musicalidad y fluidez
6. **Continuidad** → Garantiza consistencia de personajes y elementos
7. **Diseño de Escena** → Genera prompts visuales detallados
8. **Dirección de Arte** → Define paleta de colores y estilo visual
9. **Sensibilidad** → Audita contenido para seguridad infantil
10. **Portadista** → Crea título y portada
11. **Loader** → Genera mensajes de carga personalizados
12. **Validador** → Ensambla y verifica el JSON final

### Orquestador

El agente **Orquestador** coordina todo el pipeline:
- Ejecuta los agentes en orden secuencial
- Verifica quality gates (QA scores) entre pasos
- Si QA < 4, devuelve al agente anterior con instrucciones específicas
- Mantiene trazabilidad de artefactos

## 📁 Estructura del Proyecto

```
cuenteria/
├── agentes/              # Definiciones de agentes especializados
│   ├── orquestador.json  # Coordinador del pipeline
│   ├── director.json      # Diseñador de estructura narrativa
│   ├── psicoeducador.json # Experto en psicología infantil
│   ├── cuentacuentos.json # Creador de versos
│   ├── editor_claridad.json # Editor de comprensibilidad
│   ├── ritmo_rima.json   # Optimizador de musicalidad
│   ├── continuidad.json  # Responsable de coherencia
│   ├── diseno_escena.json # Diseñador visual
│   ├── sensibilidad.json # Auditor de seguridad
│   ├── portadista.json   # Creador de títulos y portadas
│   ├── loader.json       # Generador de mensajes de carga
│   └── validador.json    # Ensamblador final
└── runs/                 # Ejecuciones y resultados generados
```

## 🔧 Componentes Principales

### Agentes Creativos

#### Director (director.json)
- **Función**: Crear estructura narrativa de 10 escenas
- **Salida**: Beat Sheet con arco emotivo, leitmotiv y variantes
- **QA**: Arco completo, claridad visual, potencia del leitmotiv

#### Cuentacuentos (cuentacuentos.json)
- **Función**: Convertir Beat Sheet en versos líricos
- **Especificaciones**: 
  - 4-5 versos por página
  - 7-12 palabras por verso
  - Rima consonante preferente
  - 6-8 sílabas aproximadas
- **QA**: Emoción, claridad visual, uso del leitmotiv

#### Diseño de Escena (diseno_escena.json)
- **Función**: Generar prompts visuales detallados por página
- **Incluye**: Entorno, acción, emoción, objetos ancla, iluminación, composición
- **QA**: Alineación verso-escena, variedad de planos

### Agentes de Calidad

#### Psicoeducador (psicoeducador.json)
- **Función**: Traducir mensajes en metas conductuales observables
- **Técnicas**: Respiración, etiquetado emocional, autocontrol, pedir ayuda
- **QA**: Ajuste a edad, alineación con mensaje, tono amable

#### Editor de Claridad (editor_claridad.json)
- **Función**: Hacer el texto cristalino sin perder belleza
- **Acciones**: Simplificar vocabulario, asegurar coherencia temporal
- **QA**: Comprensibilidad, imagen inequívoca

#### Sensibilidad (sensibilidad.json)
- **Función**: Auditar contenido para seguridad infantil
- **Detecta**: Miedos excesivos, estereotipos, lenguaje inadecuado
- **QA**: Seguridad y respeto cultural

### Agentes de Consistencia

#### Continuidad (continuidad.json)
- **Función**: Garantizar consistencia de personajes y elementos
- **Character Bible**: Rasgos, vestuario, colores, objetos ancla, gestos
- **QA**: Coherencia de rasgos, utilidad para arte

#### Ritmo y Rima (ritmo_rima.json)
- **Función**: Ajustar musicalidad y fluidez
- **Garantiza**: Variedad en palabras finales, esquemas consistentes
- **QA**: Fluidez, consistencia de rima, variación de cierres

### Agentes de Finalización

#### Portadista (portadista.json)
- **Función**: Crear títulos memorables y prompt de portada
- **Propone**: 3 opciones de título
- **QA**: Recordabilidad del título, síntesis emotiva

#### Loader (loader.json)
- **Función**: Generar 10 mensajes de carga personalizados
- **Objetivo**: Crear efecto WOW y sensación de adaptación en vivo
- **Límite**: 70 caracteres por mensaje

#### Validador (validador.json)
- **Función**: Ensamblar y verificar JSON final
- **Verifica**: Formato correcto, coherencia total, cumplimiento de reglas
- **Salida**: JSON definitivo con título, 10 páginas y portada

## 📊 Formato de Salida

El sistema genera un JSON con la siguiente estructura:

```json
{
  "titulo": "Título del cuento",
  "paginas": {
    "1": {
      "texto": "Versos de la página 1",
      "prompt": "Descripción visual detallada"
    },
    "2": { ... },
    ...
    "10": { ... }
  },
  "portada": {
    "prompt": "Descripción visual de la portada"
  },
  "loader": [
    "Mensaje de carga 1",
    "Mensaje de carga 2",
    ...
    "Mensaje de carga 10"
  ]
}
```

## 🎨 Características Técnicas

### Texto
- **Páginas**: 10 páginas de contenido
- **Versos por página**: 4-5
- **Palabras por verso**: 7-12
- **Sílabas**: 6-8 aproximadas
- **Rima**: Consonante preferente, esquemas variados (ABAB, AABB)
- **Leitmotiv**: Frase musical repetida 3-4 veces

### Visual
- **Estilo**: Ilustración infantil colorida
- **Composición**: Variedad de planos (general, medio, primer plano, detalle)
- **Coherencia**: Character Bible mantiene consistencia visual
- **Objetos ancla**: Elementos recurrentes para continuidad

### Pedagógico
- **Adaptación por edad**: Vocabulario y complejidad ajustados
- **Recursos psicoeducativos**: Técnicas de regulación emocional
- **Mensajes positivos**: Resoluciones cálidas y esperanzadoras
- **Sin sermones**: Aprendizaje integrado naturalmente

## 🔒 Controles de Calidad

Cada agente incluye autoevaluación QA (1-5):
- Si QA < 4: El orquestador devuelve al agente anterior
- Múltiples iteraciones hasta alcanzar calidad deseada
- Validación final de formato y coherencia

## 🚀 Uso

El sistema requiere:
1. **Personajes**: Definición de protagonistas
2. **Historia**: Trama base
3. **Mensaje a transmitir**: Objetivo educativo
4. **Edad objetivo**: Para adaptar complejidad

## 📝 Notas

- Todos los agentes operan en español
- Salidas estrictamente en formato JSON
- Sin texto fuera de las estructuras JSON definidas
- Trazabilidad completa del proceso creativo

## 🤝 Contribución

Este es un sistema de orquestación multiagente diseñado para ser extensible. Nuevos agentes pueden agregarse al pipeline siguiendo el formato de contrato establecido.