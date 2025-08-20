# 📚 Documentación API Completa - Sistema Cuentería

## 🌐 Información General

- **Base URL**: `http://localhost:5000`
- **Formato**: JSON
- **Encoding**: UTF-8
- **CORS**: Habilitado para orígenes configurados

## 🔐 Autenticación

Actualmente la API no requiere autenticación. En producción se debe implementar API keys o JWT.

---

## 📋 Endpoints Disponibles

### 1. Health Check

Verifica el estado del servicio y la conexión con el modelo LLM.

```http
GET /health
```

#### Respuesta Exitosa (200)
```json
{
  "status": "healthy",
  "service": "cuenteria-api",
  "version": "1.0.0",
  "llm_status": "connected",
  "timestamp": "2024-08-20T00:00:00Z"
}
```

#### Ejemplo cURL
```bash
curl -X GET http://localhost:5000/health
```

---

### 2. Crear Nueva Historia

Inicia el proceso de generación de un cuento completo.

```http
POST /api/stories/create
```

#### Request Body
```json
{
  "personajes": "Emilia, niña de 2 años con pelo rizado, y su peluche Triki",
  "historia": "Emilia explora el desierto florido y aprende a dejar el chupete",
  "mensaje_a_transmitir": "La valentía de crecer y explorar cosas nuevas",
  "edad_objetivo": 3,
  "webhook_url": "https://lacuenteria.cl/webhook/story-complete" // Opcional
}
```

#### Respuesta Exitosa (202 - Accepted)
```json
{
  "story_id": "20240820_123456_abc12345",
  "status": "processing",
  "message": "Historia en proceso. Use el story_id para consultar el estado.",
  "estimated_time": "3-5 minutos",
  "webhook_url": "https://lacuenteria.cl/webhook/story-complete"
}
```

#### Respuesta si ya existe (200)
```json
{
  "story_id": "20240820_123456_abc12345",
  "status": "already_completed",
  "result": {
    "titulo": "Emilia y Triki: La Aventura del Desierto Florido",
    "paginas": { ... },
    "portada": { ... },
    "loader": [ ... ]
  }
}
```

#### Ejemplo cURL
```bash
curl -X POST http://localhost:5000/api/stories/create \
  -H "Content-Type: application/json" \
  -d '{
    "personajes": "Emilia y Triki",
    "historia": "Aventura en el desierto",
    "mensaje_a_transmitir": "Valentía y crecimiento",
    "edad_objetivo": 3
  }'
```

---

### 3. Consultar Estado de Historia

Obtiene el estado actual del procesamiento de una historia.

```http
GET /api/stories/{story_id}/status
```

#### Parámetros
- `story_id` (string): ID único de la historia

#### Respuesta - En Proceso (200)
```json
{
  "story_id": "20240820_123456_abc12345",
  "estado": "en_progreso",
  "paso_actual": "cuentacuentos",
  "pasos_completados": 3,
  "pasos_totales": 12,
  "porcentaje": 25,
  "tiempo_transcurrido": "1m 30s"
}
```

#### Respuesta - Completado (200)
```json
{
  "story_id": "20240820_123456_abc12345",
  "estado": "completo",
  "paso_actual": "validador",
  "pasos_completados": 12,
  "pasos_totales": 12,
  "porcentaje": 100,
  "tiempo_total": "4m 15s"
}
```

#### Ejemplo cURL
```bash
curl -X GET http://localhost:5000/api/stories/20240820_123456_abc12345/status
```

---

### 4. Obtener Resultado Final

Obtiene el cuento completo generado, incluyendo la evaluación crítica si existe.

```http
GET /api/stories/{story_id}/result
```

#### Parámetros
- `story_id` (string): ID único de la historia

#### Respuesta Exitosa (200)
```json
{
  "story_id": "20240820_123456_abc12345",
  "status": "completed",
  "result": {
    "titulo": "Emilia y Triki: La Aventura del Desierto Florido",
    "paginas": {
      "1": {
        "texto": "Emilia con pelo rizado\ncamina con Triki a su lado\nPor desierto con mil flores\ndonde brillan los colores",
        "prompt": "Ilustración infantil colorida: Emilia, niña de 2 años..."
      },
      "2": { ... },
      "3": { ... },
      "4": { ... },
      "5": { ... },
      "6": { ... },
      "7": { ... },
      "8": { ... },
      "9": { ... },
      "10": { ... }
    },
    "portada": {
      "prompt": "Ilustración de portada mágica y vibrante..."
    },
    "loader": [
      "Emilia prepara su mochila mágica ✨",
      "Triki afina su valentía púrpura 💜",
      "Las flores del desierto despiertan",
      "¡Vamos, Triki, a explorar!",
      "La cajita mágica brilla con luz",
      "Mariposas pintan el cielo de colores",
      "El perfume de las flores llena el aire",
      "Emilia respira profundo y sonríe",
      "El desierto florido cobra vida",
      "¡Tu cuento está casi listo!"
    ]
  },
  "qa_scores": {
    "overall": 4.2,
    "by_agent": {
      "director": { "coherencia": 4.5, "personajes": 4.3 },
      "cuentacuentos": { "rima": 3.8, "narrativa": 4.5 }
    }
  },
  "evaluacion_critica": {
    "nota_general": {
      "puntuacion": 3.5,
      "nivel": "ACEPTABLE",
      "resumen": "El cuento es adecuado pero necesita mejoras en rima y creatividad"
    },
    "notas_por_topico": { ... }
  },
  "metadata": {
    "created_at": "2024-08-20T12:34:56Z",
    "completed_at": "2024-08-20T12:39:11Z",
    "retries": {},
    "warnings": []
  }
}
```

#### Respuesta - Historia Incompleta (202)
```json
{
  "story_id": "20240820_123456_abc12345",
  "status": "processing",
  "current_state": "en_progreso",
  "message": "La historia aún no está completa"
}
```

#### Ejemplo cURL
```bash
curl -X GET http://localhost:5000/api/stories/20240820_123456_abc12345/result
```

---

### 5. Ejecutar Evaluación Crítica

Ejecuta el agente crítico sobre una historia ya completada para obtener una evaluación detallada.

```http
POST /api/stories/{story_id}/evaluate
```

#### Parámetros
- `story_id` (string): ID único de la historia

#### Respuesta Exitosa (200)
```json
{
  "status": "success",
  "story_id": "20240820_123456_abc12345",
  "evaluacion_critica": {
    "nota_general": {
      "puntuacion": 3.5,
      "nivel": "ACEPTABLE",
      "resumen": "El cuento cumple requisitos básicos pero necesita mejoras"
    },
    "notas_por_topico": {
      "prompts_imagenes": {
        "puntuacion_promedio": 4.0,
        "nivel": "BUENO",
        "notas_por_ambito": {
          "claridad_descriptiva": 4.5,
          "consistencia_personajes": 4.0,
          "nivel_detalle": 4.0,
          "adecuacion_infantil": 4.5,
          "variedad_visual": 3.5,
          "tecnica_narrativa": 3.5
        },
        "observaciones": [
          "Buena descripción de personajes",
          "Falta variedad en los planos"
        ],
        "problemas_detectados": [],
        "paginas_afectadas": []
      },
      "mensajes_carga": {
        "puntuacion_promedio": 3.0,
        "nivel": "ACEPTABLE",
        "notas_por_ambito": {
          "originalidad": 3.0,
          "brevedad": 4.0,
          "conexion_narrativa": 3.5,
          "transmision_emocion": 3.0,
          "lenguaje_infantil": 3.5
        },
        "observaciones": ["Mensajes genéricos"],
        "loaders_problematicos": [],
        "ejemplos_inadecuados": []
      },
      "texto_narrativo": {
        "puntuacion_promedio": 3.5,
        "nivel": "ACEPTABLE",
        "estructura_poetica": {
          "puntuacion_promedio": 3.0,
          "notas_por_ambito": {
            "numero_versos": 4.0,
            "longitud_versos": 3.5,
            "calidad_rima": 2.5,
            "fluidez_ritmo": 2.5
          },
          "versos_problematicos": ["dolor/desploma no riman bien"]
        },
        "contenido_narrativo": {
          "puntuacion_promedio": 4.0,
          "notas_por_ambito": {
            "coherencia_historia": 4.5,
            "progresion_emocional": 4.0,
            "lenguaje_apropiado": 4.5,
            "transmision_valores": 4.0,
            "originalidad_creatividad": 3.0
          },
          "observaciones": ["Buena progresión del personaje"]
        },
        "palabras_inadecuadas": [],
        "paginas_revisar": [3, 7]
      }
    },
    "recomendaciones_mejora": {
      "criticas": [
        {
          "prioridad": "ALTA",
          "topico": "texto",
          "descripcion": "Mejorar la calidad de las rimas",
          "sugerencia": "Revisar terminaciones para rima consonante consistente"
        }
      ],
      "mejoras_prioritarias": [
        "Mejorar calidad de rimas en páginas 3 y 7",
        "Aumentar variedad en los mensajes de carga",
        "Agregar más creatividad en la narrativa"
      ]
    },
    "decision_publicacion": {
      "apto_para_publicar": true,
      "requiere_revision": true,
      "nivel_revision_requerido": "MENOR",
      "justificacion": "El cuento es publicable con mejoras menores"
    },
    "metadata": {
      "fecha_evaluacion": "2024-08-20T00:00:00",
      "version_evaluador": "1.0",
      "criterios_aplicados": 20,
      "paginas_evaluadas": 10,
      "prompts_evaluados": 11,
      "loaders_evaluados": 10
    }
  },
  "timestamp": "2024-08-20T12:45:00Z"
}
```

#### Respuesta - Historia No Encontrada (404)
```json
{
  "status": "error",
  "message": "Historia no encontrada"
}
```

#### Respuesta - Historia Incompleta (400)
```json
{
  "status": "error",
  "message": "Historia no completada. Falta archivo validador."
}
```

#### Ejemplo cURL
```bash
curl -X POST http://localhost:5000/api/stories/20240820_123456_abc12345/evaluate
```

---

### 6. Obtener Logs de Procesamiento

Obtiene los logs detallados del procesamiento de una historia.

```http
GET /api/stories/{story_id}/logs
```

#### Parámetros
- `story_id` (string): ID único de la historia

#### Respuesta Exitosa (200)
```json
{
  "story_id": "20240820_123456_abc12345",
  "logs": {
    "director.log": "2024-08-20 12:34:56 - Iniciando director...\n2024-08-20 12:35:01 - Generando estructura narrativa...",
    "cuentacuentos.log": "2024-08-20 12:35:15 - Creando versos...",
    "validador.log": "2024-08-20 12:39:00 - Validando estructura final..."
  }
}
```

#### Ejemplo cURL
```bash
curl -X GET http://localhost:5000/api/stories/20240820_123456_abc12345/logs
```

---

### 7. Reintentar Historia Fallida

Reintenta el procesamiento de una historia desde donde falló.

```http
POST /api/stories/{story_id}/retry
```

#### Parámetros
- `story_id` (string): ID único de la historia

#### Respuesta Exitosa (202)
```json
{
  "story_id": "20240820_123456_abc12345",
  "status": "retrying",
  "message": "Reintentando desde el paso: editor_claridad",
  "resumed_from": "editor_claridad"
}
```

#### Ejemplo cURL
```bash
curl -X POST http://localhost:5000/api/stories/20240820_123456_abc12345/retry
```

---

## 🧪 Guía de Pruebas para lacuenteria.cl

### Flujo Completo de Prueba

#### 1. Crear una nueva historia
```bash
# Crear historia
curl -X POST http://localhost:5000/api/stories/create \
  -H "Content-Type: application/json" \
  -d '{
    "personajes": "Luna, una niña de 4 años curiosa",
    "historia": "Luna descubre un jardín mágico donde las flores cantan",
    "mensaje_a_transmitir": "La importancia de la curiosidad y el respeto a la naturaleza",
    "edad_objetivo": 4,
    "webhook_url": "https://lacuenteria.cl/webhook/story-complete"
  }'
```

#### 2. Consultar estado periódicamente
```bash
# Consultar estado cada 30 segundos
curl -X GET http://localhost:5000/api/stories/{story_id}/status
```

#### 3. Obtener resultado cuando esté completo
```bash
# Obtener cuento completo
curl -X GET http://localhost:5000/api/stories/{story_id}/result
```

#### 4. Ejecutar evaluación crítica
```bash
# Evaluar calidad del cuento
curl -X POST http://localhost:5000/api/stories/{story_id}/evaluate
```

### Script de Prueba Completo

```javascript
// Ejemplo en JavaScript para lacuenteria.cl
async function testCuenteria() {
    const API_BASE = 'http://localhost:5000';
    
    // 1. Crear historia
    const createResponse = await fetch(`${API_BASE}/api/stories/create`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            personajes: "Luna, niña curiosa de 4 años",
            historia: "Descubre un jardín mágico",
            mensaje_a_transmitir: "Curiosidad y respeto a la naturaleza",
            edad_objetivo: 4
        })
    });
    
    const { story_id } = await createResponse.json();
    console.log(`Historia creada: ${story_id}`);
    
    // 2. Polling del estado
    let completed = false;
    while (!completed) {
        await new Promise(resolve => setTimeout(resolve, 30000)); // 30 segundos
        
        const statusResponse = await fetch(`${API_BASE}/api/stories/${story_id}/status`);
        const status = await statusResponse.json();
        
        console.log(`Estado: ${status.estado} - ${status.porcentaje}%`);
        
        if (status.estado === 'completo') {
            completed = true;
        }
    }
    
    // 3. Obtener resultado
    const resultResponse = await fetch(`${API_BASE}/api/stories/${story_id}/result`);
    const result = await resultResponse.json();
    
    console.log('Cuento generado:', result.result.titulo);
    
    // 4. Evaluación crítica
    const evalResponse = await fetch(`${API_BASE}/api/stories/${story_id}/evaluate`, {
        method: 'POST'
    });
    const evaluation = await evalResponse.json();
    
    console.log('Evaluación:', evaluation.evaluacion_critica.nota_general);
    
    return result;
}

// Ejecutar prueba
testCuenteria().then(result => {
    console.log('Prueba completada exitosamente');
}).catch(error => {
    console.error('Error en la prueba:', error);
});
```

---

## 🔄 Webhook Notifications

Si se proporciona `webhook_url` en la creación, el sistema enviará una notificación POST cuando:

### Estructura del Webhook

```json
{
  "event": "story_completed",
  "story_id": "20240820_123456_abc12345",
  "status": "success",
  "result": {
    "titulo": "...",
    "paginas": { ... },
    "portada": { ... },
    "loader": [ ... ]
  },
  "qa_scores": { ... },
  "processing_time": 255.3,
  "timestamp": "2024-08-20T12:39:11Z"
}
```

### Eventos de Webhook

- `story_completed`: Historia generada exitosamente
- `story_failed`: Error en la generación
- `story_qa_warning`: Historia completada pero con advertencias de calidad

---

## 🚨 Códigos de Error

| Código | Descripción |
|--------|-------------|
| 200 | Éxito |
| 202 | Aceptado - Procesando |
| 206 | Contenido Parcial |
| 400 | Solicitud Incorrecta |
| 404 | No Encontrado |
| 422 | Entidad No Procesable |
| 500 | Error Interno del Servidor |
| 503 | Servicio No Disponible |

### Estructura de Error

```json
{
  "status": "error",
  "error": "Descripción del error",
  "details": "Información adicional",
  "timestamp": "2024-08-20T12:00:00Z"
}
```

---

## 🔧 Configuración CORS

Los siguientes orígenes están permitidos por defecto:

- `http://localhost:3000`
- `http://localhost:3001`
- `https://lacuenteria.cl`
- `https://www.lacuenteria.cl`

Para agregar más orígenes, modificar `API_CONFIG["cors_origins"]` en `src/config.py`.

---

## 📊 Límites y Consideraciones

- **Tiempo de procesamiento**: 3-5 minutos por historia
- **Longitud máxima de personajes**: 500 caracteres
- **Longitud máxima de historia**: 1000 caracteres
- **Edad objetivo**: 2-10 años
- **Páginas generadas**: 10 + portada
- **Mensajes de carga**: 10
- **Timeout de webhook**: 30 segundos
- **Reintentos de webhook**: 3

---

## 🐛 Depuración

Para depurar problemas:

1. Verificar health check: `GET /health`
2. Consultar logs: `GET /api/stories/{story_id}/logs`
3. Verificar estado: `GET /api/stories/{story_id}/status`
4. Los archivos se guardan en: `runs/{story_id}/`

---

## 📞 Soporte

Para soporte técnico o reportar problemas:

- GitHub: https://github.com/customware/cuenteria
- Email: soporte@customware.cl

---

*Última actualización: Agosto 2024 - v1.0.0*