# Webhook Payload - Historia Completa

## Información del Envío
- **Fecha/Hora del Test**: 2025-09-02 16:44:03 UTC
- **URL Destino**: `https://ogegdctdniijmublbmgy.supabase.co/functions/v1/pipeline-webhook`
- **Story ID Original**: `6534605d-961d-43be-890a-8da9a59bcd94`
- **Carpeta de Procesamiento**: `6534605d-961d-43be-890a-8da9a59bcd94-20250902-155259`
- **Respuesta de Supabase**: Error 500 - "Failed to update story"

## Estructura del Payload Enviado

```json
{
  "event": "story_complete",
  "timestamp": 1756837443.192058,
  "data": {
    "status": "success",
    "story_id": "6534605d-961d-43be-890a-8da9a59bcd94",
    "result": { /* contenido del validador.json */ },
    "qa_scores": {
      "overall": 4.25,
      "by_agent": { /* scores detallados por agente */ }
    },
    "processing_time": 946.5,
    "metadata": {
      "retries": {},
      "warnings": [],
      "pipeline_version": "v2",
      "folder": "6534605d-961d-43be-890a-8da9a59bcd94-20250902-155259"
    }
  }
}
```

## Contenido del Campo `result` (validador.json)

### Título
**"La Gran Aventura de la Burbuja Brillante"**

### Páginas (10 páginas con texto e ilustración)

#### Página 1
**Texto:**
```
Los tres hermanos, pieles distintas, sostienen una burbuja al sol
Franco la empuja, su risa vibra como un tambor alegre
Emilia sonríe, su vestido verde brilla bajo la luz dorada
León aprieta su chupete, mirando el horizonte con esperanza
```

**Prompt de Ilustración:**
```
Ilustración infantil digital vibrante, estilo suave y acuarelado. En la playa bajo el sol, tres hermanos de diferentes tonos de piel sostienen una burbuja brillante. Franco, con una chaqueta roja, empuja la burbuja mientras ríe. Emilia lleva un vestido verde y sonríe. León, con camiseta azul, aprieta su chupete. Ambiente alegre y luminoso.
```

#### Página 2
**Texto:**
```
Suben todos dentro de la burbuja brillante, cantando bajo el agua
¡Burbuja, burbuja, vamos a cantar!, gritan mientras giran en ondas
Los peces curiosos rodean la esfera, formando círculos de colores
La luz del sol se filtra, pintando el fondo de azul brillante
```

**Prompt de Ilustración:**
```
Escena bajo el agua dentro de la burbuja luminosa. Los tres hermanos cantan mientras la burbuja gira entre ondas. Pequeños peces de colores rodean la esfera formando círculos. Luz solar filtrada ilumina el fondo azul brillante. Atmosfera de entusiasmo y burbujeo.
```

#### Página 3
**Texto:**
```
Emilia descubre una grieta en la burbuja que mira al mar
León grita: ¡Ayuda! El aire se escapa por la fisura
Un pez plateado nada cerca y pregunta qué sucede
Franco sopla fuerte, cierra la fuga y salva la burbuja
```

**Prompt de Ilustración:**
```
Dentro de la burbuja se ve una grieta que mira al mar. León grita preocupado, mientras un pez plateado nada cerca. Franco sopla con fuerza para cerrar la fuga. Emoción de tensión y alivio al repararse la burbuja.
```

#### Página 4
**Texto:**
```
Dentro de la burbuja brilla un mapa bioluminiscente verde
El mapa muestra un sendero luminoso que lleva a la luz
Los amigos miran el camino y hacen una pregunta curiosa
Al final del sendero descubren una cruz que guía su rumbo
```

**Prompt de Ilustración:**
```
Mapa bioluminiscente verde flota dentro de la burbuja. Muestra un sendero luminoso que lleva a una cruz brillante. Los tres hermanos observan el mapa y se preguntan el destino. Ambiente de curiosidad iluminada por luz suave.
```

#### Página 5
**Texto:**
```
¡Burbuja, burbuja, vamos a cantar! resuena mientras la esfera sube
Los hermanos ven un arcoíris submarino cruzar por las ondas
Emilia señala el cielo azul que se refleja en el agua
Franco, León y Emilia se abrazan mientras ascienden riendo
```

**Prompt de Ilustración:**
```
Los tres hermanos abrazan mientras la burbuja asciende. Un arcoíris submarino cruza las ondas. Emilia señala el cielo azul reflejado en el agua. Franco, León y Emilia ríen juntos. Momento de alegría y unión.
```

#### Página 6
**Texto:**
```
De repente chocan con un coral gigante de colores brillantes
León suelta el chupete, que sale volando hacia arriba
Emilia lo atrapa rápida y se lo devuelve con una sonrisa
Franco mira al coral y dice: Pasemos por el lado derecho
```

**Prompt de Ilustración:**
```
La burbuja choca con un coral gigante de colores brillantes. El chupete de León vuela hacia arriba. Emilia lo atrapa ágilmente y se lo devuelve sonriendo. Franco señala el lado derecho del coral para pasar. Escena dinámica y colorida.
```

#### Página 7
**Texto:**
```
Navegan alrededor del coral, maravillados por su belleza dorada
Pequeños cangrejos bailan en las rocas, haciendo música marina
Los hermanos aplauden el espectáculo mientras flotan despacio
La burbuja refleja los colores del coral como un espejo mágico
```

**Prompt de Ilustración:**
```
La burbuja rodea el coral dorado. Pequeños cangrejos bailan en las rocas creando música marina. Los hermanos aplauden desde dentro de la burbuja. La superficie de la burbuja refleja los colores del coral como un espejo mágico. Escena festiva y luminosa.
```

#### Página 8
**Texto:**
```
Llegan a una cueva oscura donde la luz apenas entra tímida
Franco dice valiente: No teman, juntos podemos atravesarla
León abraza su chupete mientras Emilia toma su mano suave
Unidos cruzan la cueva, sus voces eco en las paredes
```

**Prompt de Ilustración:**
```
La burbuja entra en una cueva oscura con poca luz. Franco lidera con valentía. León abraza su chupete mientras Emilia le toma la mano. Unidos atraviesan la cueva, sus siluetas iluminadas dentro de la burbuja. Atmósfera de misterio y unión.
```

#### Página 9
**Texto:**
```
Al salir de la cueva encuentran un jardín submarino resplandeciente
Flores marinas de todos los colores danzan con la corriente suave
La burbuja se llena de luz dorada mientras flotan entre las plantas
Los hermanos se miran felices, han superado juntos la aventura
```

**Prompt de Ilustración:**
```
La burbuja emerge en un jardín submarino resplandeciente. Flores marinas multicolores danzan con la corriente. La burbuja brilla con luz dorada entre las plantas. Los tres hermanos se miran felices y orgullosos. Escena de triunfo y belleza natural.
```

#### Página 10
**Texto:**
```
¡Burbuja, burbuja, vamos a cantar! entonan mientras suben a la playa
La burbuja se posa suave en la arena dorada del atardecer
Los tres hermanos salen riendo, el sol pinta sus sombras largas
Se abrazan fuerte y prometen: Mañana otra aventura comenzar
```

**Prompt de Ilustración:**
```
La burbuja se posa en la playa al atardecer. Los hermanos salen riendo mientras el sol crea sombras largas en la arena dorada. Se abrazan los tres prometiendo nuevas aventuras. Cierre cálido y esperanzador con luz dorada del atardecer.
```

### Portada

**Título:** "La Gran Aventura de la Burbuja Brillante"

**Subtítulo:** "Un viaje mágico de tres hermanos valientes"

**Descripción Visual:**
```
Ilustración de portada vibrante y mágica. Los tres hermanos (Franco con chaqueta roja, Emilia con vestido verde, León con camiseta azul y chupete) están dentro de una burbuja brillante flotando sobre el mar. La burbuja refleja un arcoíris. El fondo muestra un atardecer dorado con nubes suaves. El título "La Gran Aventura de la Burbuja Brillante" aparece en letras grandes y coloridas en la parte superior. Estilo infantil, cálido y aventurero. Composición equilibrada y llamativa para niños de 3 años.
```

### Mensajes de Carga (Loader Messages)
*No se generaron mensajes de carga para esta historia*

## Métricas de Calidad (QA Scores)

### Score General: **4.25/5.0**

### Desglose por Agente:
- **01_director**: 5.0/5.0
- **02_psicoeducador**: 4.5/5.0
- **03_cuentacuentos**: 3.5/5.0
- **04_editor_claridad**: 4.0/5.0
- **05_ritmo_rima**: 4.0/5.0
- **06_continuidad**: 4.5/5.0
- **07_diseno_escena**: 4.5/5.0
- **08_direccion_arte**: 4.0/5.0
- **09_sensibilidad**: 4.5/5.0
- **10_portadista**: 4.0/5.0
- **11_loader**: N/A (no generó mensajes)
- **12_validador**: 4.5/5.0

## Metadata Adicional

- **Tiempo de Procesamiento**: 946.5 segundos (15.8 minutos)
- **Pipeline Version**: v2
- **Reintentos**: Ninguno
- **Advertencias**: Ninguna
- **Estado Final**: Completo
- **Tamaño del Payload**: 22,527 bytes

## Notas sobre el Error de Supabase

La Edge Function de Supabase devolvió:
```json
{
  "error": "Failed to update story"
}
```

Esto indica que la función está intentando actualizar un registro que no existe en la base de datos. El webhook fue recibido correctamente pero la lógica de la Edge Function necesita manejar el caso de historias nuevas (crear en lugar de actualizar).

## Recomendaciones para la Edge Function

1. Implementar lógica de "upsert" (insert o update según exista)
2. Validar el evento antes de buscar en la base de datos
3. Para eventos `story_complete`, crear el registro si no existe
4. Manejar diferentes eventos de forma específica:
   - `story_complete`: Crear o actualizar historia completa
   - `story_error`: Registrar error sin requerir que exista el registro
   - `story_progress`: Actualizar solo si existe, ignorar si no

---

*Documento generado el 2025-09-02 desde el sistema de orquestación Cuentería v2*