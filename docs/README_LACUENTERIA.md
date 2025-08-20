# Documentación para Integración con lacuenteria.cl

## Estado Actual del Sistema

### ✅ Funcionalidades Completadas

1. **API REST Funcional**
   - Endpoints principales implementados y probados
   - CORS configurado para lacuenteria.cl
   - Sistema de webhooks para notificaciones asíncronas

2. **Pipeline de Generación**
   - 12 agentes especializados configurados
   - Sistema de Quality Assurance (QA) con umbrales
   - Generación exitosa hasta el agente `editor_claridad`

3. **Agente Crítico**
   - Evaluación independiente de historias
   - Genera JSON en cascada con puntuaciones y comentarios
   - Endpoint `/api/stories/{story_id}/evaluate` disponible

### ⚠️ Limitaciones Actuales

1. **Truncamiento de Respuestas Largas**
   - El modelo GPT-OSS-120B trunca respuestas > 2000-3000 caracteres
   - Afecta a los agentes `ritmo_rima` y `validador`
   - Ver `LIMITACIONES_MODELO.md` para detalles técnicos

2. **Pipeline Incompleto**
   - El flujo se detiene en `ritmo_rima` debido al truncamiento
   - Los últimos 7 agentes no se ejecutan completamente

## Archivos de Documentación Importantes

### Para el Desarrollador de lacuenteria.cl:

1. **`docs/API_DOCUMENTATION.md`**
   - Documentación completa de los 6 endpoints principales
   - Ejemplos de código en cURL, Python y JavaScript
   - Estructura de webhooks

2. **`docs/API_DOCUMENTATION_COMPLETE.md`**
   - Incluye el endpoint del agente crítico
   - Estructura del JSON de evaluación en cascada

3. **`docs/LIMITACIONES_MODELO.md`**
   - Explicación técnica del problema de truncamiento
   - Estado actual de cada agente
   - Soluciones propuestas

4. **`examples/emilia_completa.json`**
   - Ejemplo completo de una historia generada
   - Útil para entender la estructura esperada

5. **`critico_resultado_*.json`**
   - Ejemplos de evaluaciones críticas
   - Muestra la estructura en cascada del JSON

## Endpoints Disponibles

### Principales
- `POST /api/stories/create` - Crear nueva historia
- `GET /api/stories/{story_id}/status` - Estado del procesamiento
- `GET /api/stories/{story_id}/result` - Obtener resultado final
- `GET /api/stories/{story_id}/logs` - Ver logs detallados
- `POST /api/stories/{story_id}/retry` - Reintentar historia fallida
- `GET /health` - Verificar estado del sistema

### Evaluación Crítica
- `POST /api/stories/{story_id}/evaluate` - Ejecutar agente crítico

## Configuración Requerida

### Variables de Entorno
```bash
LLM_ENDPOINT=http://69.19.136.204:8000/v1/chat/completions
API_HOST=0.0.0.0
API_PORT=5000
CORS_ORIGINS=https://lacuenteria.cl
```

### Instalación
```bash
# Instalar dependencias
pip install flask flask-cors requests

# Iniciar servidor
python3 src/api_server.py
```

## Integración Sugerida

### 1. Flujo Básico
```javascript
// 1. Crear historia
const response = await fetch('http://api-url/api/stories/create', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    story_id: 'unique-id',
    personajes: [...],
    historia: '...',
    mensaje_a_transmitir: '...',
    edad_objetivo: '4-6 años',
    webhook_url: 'https://lacuenteria.cl/api/webhook/story-complete'
  })
});

// 2. Recibir webhook cuando complete
// El sistema enviará el resultado al webhook_url
```

### 2. Evaluación Crítica
```javascript
// Después de recibir la historia completa
const evaluation = await fetch(`http://api-url/api/stories/${storyId}/evaluate`, {
  method: 'POST'
});
const critica = await evaluation.json();
// Usar critica.evaluacion_critica para mostrar feedback
```

## Próximos Pasos

1. **Resolver limitación de truncamiento**
   - Implementar generación por chunks
   - O configurar servidor para respuestas más largas

2. **Completar pipeline**
   - Una vez resuelto el truncamiento, validar agentes restantes

3. **Pruebas de integración**
   - Probar flujo completo con webhooks
   - Validar manejo de errores y reintentos

## Contacto y Soporte

Para issues o mejoras, usar el repositorio de GitHub.

## Estructura de Respuesta Esperada

Ver `examples/emilia_completa.json` para un ejemplo completo del JSON que debería generar el sistema cuando funcione completamente.