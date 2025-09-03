# Changelog - Cuentería

## [2025-09-03] - Cambios Importantes

### 🔄 Cambios en la Estructura de Carpetas
- **NUEVO**: Las carpetas de runs ahora usan el formato `{YYYYMMDD-HHMMSS}-{story_id}`
- **ANTES**: `{story_id}-{YYYYMMDD-HHMMSS}`
- **DESPUÉS**: `{YYYYMMDD-HHMMSS}-{story_id}`
- Mantiene compatibilidad con formato anterior para búsquedas

### 🔐 Autenticación de Webhooks
- **AGREGADO**: Soporte para autenticación con Supabase Edge Functions
- **NUEVO**: Lectura de `anon_key` desde archivo `.env`
- **HEADERS**: Se incluye `Authorization: Bearer {token}` en webhooks
- **FORMATO**: Webhook envuelve el payload en estructura `{event, timestamp, data}`

### 📊 Gestión de Métricas
- **FIX**: `prompt_metrics_id` ya NO se incluye en `brief.json`
- **CAMBIO**: `prompt_metrics_id` solo se guarda en `manifest.json`
- **WEBHOOK**: `prompt_metrics_id` se incluye en el payload del webhook
- Previene contaminación del contexto de los agentes con IDs internos

### 🛠️ Mejoras en el API
- **MEJORADO**: Manejo de `prompt_metrics_id` en todos los endpoints
- **ENDPOINTS**: `/api/stories/create`, `/api/v1/stories/create`, `/api/v2/stories/create`
- **PARÁMETRO**: `prompt_metrics_id` ahora es opcional y se pasa al orchestrator

### 📝 Archivos Actualizados
- `src/config.py`: Nueva función `generate_timestamped_story_folder()`
- `src/api_server.py`: Manejo correcto de `prompt_metrics_id`
- `src/orchestrator.py`: Acepta `prompt_metrics_id` como parámetro
- `src/webhook_client.py`: Preparado para autenticación (pendiente implementación)

### 🧪 Tests Agregados
- `test_new_folder_structure.py`: Verifica nueva estructura de carpetas
- `test_prompt_metrics_fix.py`: Valida que `prompt_metrics_id` no esté en brief
- `send_webhook_with_auth.py`: Script para envío manual de webhooks con auth

### 📚 Documentación
- Actualizado formato de carpetas en toda la documentación
- Agregado ejemplo de configuración con `.env`
- Documentado el formato correcto del webhook para Supabase

## [2025-08-30] - Versiones del Pipeline

### Pipeline v2
- Procesamiento paralelo del agente cuentacuentos
- Configuración granular por versión
- Toggles para habilitar/deshabilitar agentes

## [2025-08-22] - Sistema de Evaluación

### QA Verificador
- Implementación de verificador QA externo
- Reemplazo de autoevaluación por evaluación crítica
- Calibración de scores (promedio 2.3-3.7)