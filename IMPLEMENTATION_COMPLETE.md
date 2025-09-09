# ✅ Implementación Completada: Variables de Entorno

## Cambios Realizados

### 1. ✅ Soporte para dotenv agregado
- `src/api_server.py` - Agregado `load_dotenv()`
- `src/orchestrator.py` - Agregado `load_dotenv()`

### 2. ✅ Eliminado hardcoding del modelo
- `src/llm_client.py` línea 19 - Ahora usa `LLM_CONFIG["model"]`
- `src/llm_client.py` línea 18 - Ahora usa `LLM_CONFIG["api_url"]`

### 3. ✅ Archivos de configuración creados/actualizados
- `.env.template` - Plantilla completa con todas las variables
- `.env.example` - Actualizado para usar `LLM_API_URL` en vez de `LLM_ENDPOINT`
- `.env` - Configurado con valores actuales
- `start.sh` - Actualizado para exportar `LLM_API_URL` y `LLM_MODEL`

## Configuración por VM

### VM1 - gpt-oss-120b (actual)
```env
LLM_API_URL=http://69.19.136.204:8000/v1/chat/completions
LLM_MODEL=openai/gpt-oss-120b
```

### VM2 - gpt-oss-20b (nueva)
```env
LLM_API_URL=http://localhost:8000/v1/chat/completions
LLM_MODEL=openai/gpt-oss-20b
```

## Instrucciones de Uso

### Para configurar una nueva VM:

1. **Clonar el repositorio**
```bash
git clone <repo-url>
cd cuenteria
```

2. **Crear archivo .env**
```bash
cp .env.template .env
```

3. **Editar .env con tu configuración**
```bash
nano .env
# Cambiar LLM_MODEL y LLM_API_URL según tu modelo
```

4. **Iniciar el servidor**
```bash
python3 src/api_server.py
# o
./start.sh
```

## Pruebas Realizadas

✅ Variables de entorno se cargan correctamente desde .env
✅ LLM_CONFIG usa los valores del .env
✅ LLMClient se configura con el modelo especificado
✅ Funciona con diferentes configuraciones de modelo

## Comportamiento

- **Sin .env**: Usa valores por defecto (gpt-oss-120b)
- **Con .env**: Usa los valores especificados
- **lacuenteria.cl**: Envía requests a la IP correcta según el modelo deseado

## Arquitectura Final

```
lacuenteria.cl
    |
    ├── Si quiere gpt-oss-120b → http://ip1:5000/api/stories/create
    └── Si quiere gpt-oss-20b  → http://ip2:5000/api/stories/create
    
VM1 (ip1)                    VM2 (ip2)
.env:                        .env:
  LLM_MODEL=gpt-oss-120b       LLM_MODEL=gpt-oss-20b
```

## Beneficios

1. ✅ **Simplicidad**: Solo configurar .env por VM
2. ✅ **Sin cambios en payloads**: lacuenteria.cl no necesita cambios
3. ✅ **Portabilidad**: Fácil desplegar en cualquier VM
4. ✅ **Mantenibilidad**: No hay IPs hardcodeadas en el código

## Próximos Pasos (Opcional)

Si en el futuro se necesita mayor flexibilidad:
1. Agregar soporte para `llm_config` en el payload
2. Permitir override del modelo por request
3. Implementar validación de modelos permitidos

Por ahora, la solución simple está completamente funcional.