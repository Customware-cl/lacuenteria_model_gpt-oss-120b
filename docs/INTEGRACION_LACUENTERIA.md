# Guía de Integración - lacuenteria.cl

## Introducción

Este documento describe cómo integrar lacuenteria.cl con el sistema de orquestación Cuentería para la generación automatizada de cuentos infantiles.

## Información de Conexión

### Endpoint Base
```
http://[IP_VM]:5000/api
```

### Headers Requeridos
```http
Content-Type: application/json
```

## Flujo de Integración

### 1. Enviar Historia para Procesamiento

**Endpoint:** `POST /api/stories/create`

**Request desde lacuenteria.cl:**

```javascript
const crearHistoria = async (datosHistoria) => {
  const response = await fetch('http://[IP_VM]:5000/api/stories/create', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      story_id: 'lacuenteria-2025-001',  // ID único generado por lacuenteria.cl
      personajes: [
        {
          nombre: 'Luna',
          descripcion: 'Una pequeña luciérnaga de 5 años con luz tenue',
          rasgos: 'Tímida, curiosa, valiente cuando es necesario'
        },
        {
          nombre: 'Estrellín',
          descripcion: 'Un grillo sabio y anciano que toca el violín',
          rasgos: 'Paciente, sabio, motivador'
        }
      ],
      historia: 'Luna es una luciérnaga que teme a la oscuridad...',
      mensaje_a_transmitir: 'Los miedos se vencen poco a poco con valentía',
      edad_objetivo: '4-6 años',
      webhook_url: 'https://lacuenteria.cl/api/webhook/story-complete'
    })
  });

  const result = await response.json();
  console.log('Historia en proceso:', result.story_id);
  // Guardar story_id para consultas posteriores
};
```

**Response:**
```json
{
  "story_id": "lacuenteria-2025-001",
  "status": "processing",
  "estimated_time": 180,
  "accepted_at": "2025-08-19T14:30:00Z"
}
```

### 2. Recibir Notificación por Webhook

El sistema enviará una notificación POST a la URL especificada cuando complete el procesamiento.

**Webhook Endpoint en lacuenteria.cl:**

```javascript
// POST https://lacuenteria.cl/api/webhook/story-complete
app.post('/api/webhook/story-complete', async (req, res) => {
  const { event, timestamp, data } = req.body;
  
  if (event === 'story_complete') {
    const { story_id, status, result } = data;
    
    if (status === 'success') {
      // Guardar el cuento completo
      await guardarCuento(story_id, result);
      
      // El resultado contiene:
      // - titulo: String con el título del cuento
      // - paginas: Objeto con 10 páginas (texto + prompt)
      // - portada: Objeto con prompt de portada
      // - loader: Array con 10 mensajes de carga
      
      console.log('Cuento recibido:', result.titulo);
      
      // Procesar páginas
      Object.entries(result.paginas).forEach(([num, pagina]) => {
        console.log(`Página ${num}:`, pagina.texto);
        console.log(`Prompt visual:`, pagina.prompt);
      });
    }
  } else if (event === 'story_error') {
    const { story_id, error } = data;
    console.error(`Error en historia ${story_id}:`, error);
    // Manejar error
  }
  
  res.status(200).json({ received: true });
});
```

### 3. Consultar Estado (Opcional)

Si no se recibe webhook o se necesita verificar el estado:

```javascript
const consultarEstado = async (storyId) => {
  const response = await fetch(`http://[IP_VM]:5000/api/stories/${storyId}/status`);
  const status = await response.json();
  
  console.log('Estado:', status.status);
  console.log('Paso actual:', status.current_step);
  
  return status;
};
```

### 4. Obtener Resultado Directamente

Si se prefiere polling en lugar de webhooks:

```javascript
const obtenerResultado = async (storyId) => {
  const response = await fetch(`http://[IP_VM]:5000/api/stories/${storyId}/result`);
  
  if (response.status === 200) {
    const data = await response.json();
    return data.result; // Cuento completo
  } else if (response.status === 202) {
    // Aún procesando
    return null;
  }
};

// Polling cada 30 segundos
const esperarCuento = async (storyId) => {
  let resultado = null;
  while (!resultado) {
    resultado = await obtenerResultado(storyId);
    if (!resultado) {
      await new Promise(resolve => setTimeout(resolve, 30000));
    }
  }
  return resultado;
};
```

## Estructura del Resultado

### Formato del Cuento Completo

```json
{
  "titulo": "Luna la Luciérnaga Valiente",
  "paginas": {
    "1": {
      "texto": "Luna era pequeñita\ncon luz muy suavecita\nCuando el miedo la invadía\nsu brillo se escondía",
      "prompt": "Ilustración infantil colorida: Una pequeña luciérnaga tímida con luz tenue en un claro del bosque al atardecer. Luna tiene ojitos grandes expresivos y alas delicadas translúcidas. El ambiente es cálido con tonos dorados y verdes suaves. Plano medio mostrando a Luna entre hojas gigantes que la hacen ver muy pequeñita. Estilo acuarela suave con brillos mágicos."
    },
    "2": {
      "texto": "...",
      "prompt": "..."
    },
    // ... páginas 3-10
  },
  "portada": {
    "prompt": "Ilustración de portada vibrante y mágica: Luna la luciérnaga en primer plano con su luz brillando valientemente, rodeada por Estrellín el grillo con su violín y la misteriosa Sombra en el fondo como un abrazo protector. Bosque nocturno estrellado con tonos azules profundos y dorados cálidos. El título 'Luna la Luciérnaga Valiente' en letras juguetonas y luminosas. Estilo ilustración infantil digital con texturas suaves y brillos mágicos."
  },
  "loader": [
    "Luna prepara su luz mágica ✨",
    "Estrellín afina su violín musical 🎻",
    "Las estrellas iluminan el bosque",
    "Respiramos profundo con Luna",
    "La valentía crece poquito a poco",
    "Sombra extiende su manto protector",
    "Los grillos preparan su sinfonía",
    "El bosque cobra vida con color",
    "Luna descubre su brillo interior",
    "¡Tu cuento casi está listo!"
  ]
}
```

### Uso de los Componentes

#### Texto de las Páginas
- 4-5 versos por página
- Rima consonante o asonante
- Vocabulario adaptado a la edad
- Separados por `\n` (salto de línea)

#### Prompts Visuales
- Descripción detallada para generar ilustraciones
- Incluye: escenario, personajes, acción, emoción, paleta de colores
- Estilo consistente: "ilustración infantil colorida"
- Pueden usarse con DALL-E, Midjourney, Stable Diffusion, etc.

#### Mensajes del Loader
- 10 mensajes cortos (máx 70 caracteres)
- Personalizados con elementos de la historia
- Para mostrar mientras se generan las imágenes
- Crean expectativa y conexión emocional

## Manejo de Errores

### Códigos de Error Comunes

| Código | Significado | Acción Recomendada |
|--------|-------------|-------------------|
| 400 | Datos inválidos | Verificar campos requeridos |
| 404 | Historia no encontrada | Verificar story_id |
| 500 | Error del servidor | Reintentar después |
| 503 | Servicio no disponible | Sistema en mantenimiento |

### Ejemplo de Manejo de Errores

```javascript
const manejarError = (error, storyId) => {
  console.error(`Error procesando historia ${storyId}:`, error);
  
  // Notificar al usuario
  notificarUsuario({
    tipo: 'error',
    mensaje: 'Hubo un problema generando tu cuento. Estamos trabajando en ello.',
    storyId: storyId
  });
  
  // Registrar para reintento manual
  registrarParaReintento(storyId);
};
```

## Consideraciones de Rendimiento

### Tiempos Estimados
- **Procesamiento completo:** 2-3 minutos promedio
- **Timeout máximo:** 10 minutos
- **Webhook retry:** 3 intentos con 10 segundos entre cada uno

### Límites
- **Historias concurrentes:** 3 máximo
- **Tamaño del brief:** 50KB máximo
- **Longitud de historia:** 2000 caracteres recomendado

### Optimizaciones Recomendadas

1. **Implementar cola en lacuenteria.cl:**
```javascript
// Sistema de cola para manejar múltiples solicitudes
const procesarCola = async () => {
  const pendientes = await obtenerHistoriasPendientes();
  
  for (const historia of pendientes) {
    if (historiasEnProceso < 3) {
      await crearHistoria(historia);
      historiasEnProceso++;
    }
  }
};
```

2. **Cache de resultados:**
```javascript
// Cachear cuentos completados
const cache = new Map();

const obtenerCuento = async (storyId) => {
  if (cache.has(storyId)) {
    return cache.get(storyId);
  }
  
  const resultado = await obtenerResultado(storyId);
  if (resultado) {
    cache.set(storyId, resultado);
  }
  return resultado;
};
```

## Seguridad

### Recomendaciones

1. **Validar webhook origen:**
```javascript
// Verificar que el webhook viene del servidor Cuentería
const verificarWebhook = (req) => {
  const ip = req.ip;
  const allowedIPs = ['IP_VM_CUENTERIA'];
  return allowedIPs.includes(ip);
};
```

2. **Sanitizar entrada de usuarios:**
```javascript
const sanitizarBrief = (brief) => {
  // Eliminar HTML/scripts
  brief.historia = DOMPurify.sanitize(brief.historia, { ALLOWED_TAGS: [] });
  brief.personajes.forEach(p => {
    p.nombre = DOMPurify.sanitize(p.nombre, { ALLOWED_TAGS: [] });
    p.descripcion = DOMPurify.sanitize(p.descripcion, { ALLOWED_TAGS: [] });
  });
  return brief;
};
```

3. **Rate limiting:**
```javascript
// Limitar solicitudes por usuario
const rateLimiter = rateLimit({
  windowMs: 60 * 60 * 1000, // 1 hora
  max: 10, // máximo 10 cuentos por hora
  message: 'Demasiadas solicitudes, intenta más tarde'
});
```

## Monitoreo

### Métricas a Trackear

```javascript
// Métricas recomendadas
const metricas = {
  cuentosCreados: 0,
  cuentosCompletados: 0,
  cuentosFallidos: 0,
  tiempoPromedioGeneracion: 0,
  qaScorePromedio: 0
};

// Actualizar métricas
const actualizarMetricas = (resultado) => {
  if (resultado.status === 'success') {
    metricas.cuentosCompletados++;
    metricas.qaScorePromedio = 
      (metricas.qaScorePromedio * (metricas.cuentosCompletados - 1) + 
       resultado.qa_scores.overall) / metricas.cuentosCompletados;
  }
};
```

### Logs Recomendados

```javascript
// Estructura de logging
const logger = winston.createLogger({
  format: winston.format.json(),
  transports: [
    new winston.transports.File({ filename: 'cuenteria.log' })
  ]
});

// Log de eventos
logger.info('Cuento solicitado', { storyId, userId, timestamp });
logger.info('Cuento completado', { storyId, qaScore, tiempo });
logger.error('Error en generación', { storyId, error });
```

## Soporte

### Contacto Técnico
- **Email:** soporte@customware.cl
- **GitHub Issues:** https://github.com/Customware-cl/lacuenteria_model_gpt-oss-120b/issues

### Información de Debug

Para reportar problemas, incluir:
1. `story_id` afectado
2. Timestamp de la solicitud
3. Response del servidor
4. Logs relevantes

### FAQ

**P: ¿Qué pasa si el webhook falla?**
R: El sistema reintenta 3 veces. Si falla, puedes consultar el resultado con GET /api/stories/{id}/result

**P: ¿Puedo procesar múltiples historias del mismo usuario?**
R: Sí, pero respetando el límite de 3 historias concurrentes en total.

**P: ¿Los story_id deben ser únicos globalmente?**
R: Sí, recomendamos usar UUID o prefijo + timestamp.

**P: ¿Cuánto tiempo se guardan las historias?**
R: 30 días por defecto, configurable en el servidor.

## Ejemplo Completo de Integración

```javascript
// servicio-cuenteria.js
class ServicioCuenteria {
  constructor(baseUrl) {
    this.baseUrl = baseUrl;
  }

  async crearCuento(datos) {
    try {
      const response = await fetch(`${this.baseUrl}/api/stories/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          story_id: this.generarId(),
          ...datos,
          webhook_url: 'https://lacuenteria.cl/api/webhook/story'
        })
      });

      if (!response.ok) {
        throw new Error(`Error ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error creando cuento:', error);
      throw error;
    }
  }

  async obtenerEstado(storyId) {
    const response = await fetch(`${this.baseUrl}/api/stories/${storyId}/status`);
    return await response.json();
  }

  async obtenerResultado(storyId) {
    const response = await fetch(`${this.baseUrl}/api/stories/${storyId}/result`);
    if (response.status === 200) {
      const data = await response.json();
      return data.result;
    }
    return null;
  }

  generarId() {
    return `lacuenteria-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }
}

// Uso
const cuenteria = new ServicioCuenteria('http://[IP_VM]:5000');

const nuevoCuento = await cuenteria.crearCuento({
  personajes: [...],
  historia: '...',
  mensaje_a_transmitir: '...',
  edad_objetivo: '4-6 años'
});

console.log('Cuento en proceso:', nuevoCuento.story_id);
```

## Checklist de Integración

- [ ] Configurar endpoint base con IP del servidor
- [ ] Implementar creación de story_id únicos
- [ ] Configurar endpoint para recibir webhooks
- [ ] Implementar manejo de estados (processing, completed, error)
- [ ] Agregar validación de datos antes de enviar
- [ ] Implementar sistema de reintentos
- [ ] Configurar logging de eventos
- [ ] Agregar rate limiting
- [ ] Implementar cache de resultados
- [ ] Configurar monitoreo de métricas
- [ ] Pruebas end-to-end con historia de ejemplo