# Uso del webhook_url en Cuentería

## ¿Qué es el webhook_url?

El `webhook_url` es una URL proporcionada por lacuenteria.cl para recibir notificaciones en tiempo real sobre el progreso y resultado de la generación de historias.

## Eventos del Webhook

### 1. **story_complete** - Historia Completada Exitosamente
```json
{
  "event": "story_complete",
  "timestamp": 1693245678.123,
  "data": {
    "story_id": "emi-aventura-123",
    "status": "success",
    "titulo": "Emi y la aventura del parque mágico",
    "paginas": {
      "1": {
        "texto": "Emi corre por el parque verde\nMira las flores que se mueven\nSu perro Max ladra contento\nJuegan juntos en el momento",
        "ilustracion": "Niña de 3 años con vestido amarillo..."
      },
      // ... páginas 2-10
    },
    "portada": {
      "titulo": "Emi y la aventura del parque mágico",
      "subtitulo": "Un cuento sobre la amistad",
      "descripcion_visual": "Ilustración vibrante de Emi..."
    },
    "loader_messages": [
      "Emi está preparando su mochila de aventuras...",
      "Max está practicando sus mejores ladridos...",
      "Las flores del parque están ensayando su baile..."
    ],
    "metadata": {
      "duracion_total": 145.2,
      "agentes_ejecutados": 12,
      "qa_promedio": 4.2,
      "version_pipeline": "v2"
    }
  }
}
```

### 2. **story_error** - Error en la Generación
```json
{
  "event": "story_error",
  "timestamp": 1693245678.123,
  "data": {
    "story_id": "emi-aventura-123",
    "status": "error",
    "error": "Timeout en agente 05_ritmo_rima después de 3 reintentos"
  }
}
```

### 3. **story_progress** - Actualización de Progreso (Opcional)
```json
{
  "event": "story_progress",
  "timestamp": 1693245678.123,
  "data": {
    "story_id": "emi-aventura-123",
    "status": "processing",
    "current_agent": "03_cuentacuentos",
    "progress": 25
  }
}
```

## Ejemplos de Implementación

### 1. Endpoint en Node.js/Express (lacuenteria.cl)
```javascript
// Endpoint para recibir webhooks de Cuentería
app.post('/api/webhooks/story-updates', async (req, res) => {
  const { event, timestamp, data } = req.body;
  
  try {
    switch(event) {
      case 'story_complete':
        // Guardar el cuento completo en la base de datos
        await saveCompletedStory(data.story_id, {
          titulo: data.titulo,
          paginas: data.paginas,
          portada: data.portada,
          loader_messages: data.loader_messages,
          metadata: data.metadata
        });
        
        // Notificar al usuario por email/push
        await notifyUser(data.story_id, 'complete');
        
        // Actualizar UI en tiempo real (WebSocket)
        io.to(data.story_id).emit('story_ready', data);
        break;
        
      case 'story_error':
        // Registrar el error
        await logError(data.story_id, data.error);
        
        // Notificar al equipo técnico
        await notifySupport(data);
        
        // Informar al usuario
        io.to(data.story_id).emit('story_failed', data.error);
        break;
        
      case 'story_progress':
        // Actualizar barra de progreso en UI
        io.to(data.story_id).emit('progress_update', {
          agent: data.current_agent,
          progress: data.progress
        });
        break;
    }
    
    res.status(200).json({ received: true });
  } catch (error) {
    console.error('Error procesando webhook:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});
```

### 2. Implementación con Supabase Edge Functions
```typescript
// supabase/functions/story-webhook/index.ts
import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

serve(async (req) => {
  const { event, data } = await req.json()
  
  const supabase = createClient(
    Deno.env.get('SUPABASE_URL')!,
    Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
  )
  
  if (event === 'story_complete') {
    // Guardar el cuento completo
    const { error } = await supabase
      .from('stories')
      .update({
        status: 'completed',
        content: data,
        completed_at: new Date().toISOString()
      })
      .eq('story_id', data.story_id)
    
    if (!error) {
      // Trigger email notification
      await supabase.functions.invoke('send-story-ready-email', {
        body: { story_id: data.story_id }
      })
    }
  }
  
  return new Response(JSON.stringify({ ok: true }), {
    headers: { 'Content-Type': 'application/json' },
  })
})
```

### 3. Llamada Inicial desde lacuenteria.cl
```javascript
// Crear historia con webhook
const response = await fetch('http://69.19.136.204:5000/api/stories/create', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    story_id: 'emi-aventura-123',
    personajes: ['Emi', 'Max el perro'],
    historia: 'Emi y su perro Max descubren un parque mágico...',
    mensaje_a_transmitir: 'La importancia de la amistad y el juego',
    edad_objetivo: 3,
    webhook_url: 'https://lacuenteria.cl/api/webhooks/story-updates',
    pipeline_version: 'v2'
  })
});

// La respuesta inicial solo confirma que se inició el proceso
const { story_id, status } = await response.json();
// status: "processing"

// El webhook recibirá el resultado completo cuando termine
```

## Casos de Uso Prácticos

### 1. **Notificación en Tiempo Real al Usuario**
- Usuario solicita cuento → Se muestra spinner/loader
- Webhooks de progreso actualizan la barra
- Webhook complete → Se muestra el cuento automáticamente

### 2. **Sistema de Reintentos Automáticos**
```javascript
if (event === 'story_error' && data.error.includes('timeout')) {
  // Reintentar automáticamente hasta 3 veces
  await retryStoryGeneration(data.story_id);
}
```

### 3. **Analytics y Monitoreo**
```javascript
// Guardar métricas de cada generación
await saveMetrics({
  story_id: data.story_id,
  duration: data.metadata.duracion_total,
  qa_score: data.metadata.qa_promedio,
  pipeline_version: data.metadata.version_pipeline,
  success: event === 'story_complete'
});
```

### 4. **Generación de PDF Automática**
```javascript
if (event === 'story_complete') {
  // Trigger generación de PDF
  await generatePDF(data);
  
  // Enviar por email
  await sendStoryEmail(getUserEmail(data.story_id), pdfUrl);
}
```

### 5. **Integración con Sistema de Pagos**
```javascript
if (event === 'story_complete') {
  // Marcar orden como completada
  await updateOrder(data.story_id, 'fulfilled');
  
  // Liberar créditos del usuario
  await releaseCredits(getUserId(data.story_id));
}
```

## Ventajas del Sistema de Webhooks

1. **Asíncrono**: No bloquea la UI mientras se genera el cuento
2. **Resiliente**: Si falla la conexión, el cuento sigue generándose
3. **Escalable**: Permite procesar múltiples historias en paralelo
4. **Informativo**: Actualizaciones de progreso en tiempo real
5. **Flexible**: lacuenteria.cl puede procesar el resultado como necesite

## Configuración de Seguridad Recomendada

```javascript
// Validar origen del webhook
const isValidWebhook = (req) => {
  const signature = req.headers['x-cuenteria-signature'];
  const expectedSignature = crypto
    .createHmac('sha256', process.env.WEBHOOK_SECRET)
    .update(JSON.stringify(req.body))
    .digest('hex');
  
  return signature === expectedSignature;
};

// Usar en el endpoint
if (!isValidWebhook(req)) {
  return res.status(401).json({ error: 'Invalid signature' });
}
```

## Notas Importantes

- El webhook se intenta enviar hasta 3 veces con delays de 2 segundos
- Timeout de 30 segundos por intento
- Si el webhook falla, la historia se genera igual (se puede consultar por API)
- Los webhooks incluyen timestamp Unix para ordenamiento
- El campo `event` permite distinguir el tipo de notificación