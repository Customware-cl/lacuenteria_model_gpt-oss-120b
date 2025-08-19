#!/bin/bash

# Script de inicio para el sistema Cuentería

echo "========================================="
echo "   Sistema de Orquestación Cuentería    "
echo "========================================="

# Activar entorno virtual si existe
if [ -d "venv" ]; then
    echo "Activando entorno virtual..."
    source venv/bin/activate
fi

# Verificar Python
python_version=$(python3 --version 2>&1)
echo "Python detectado: $python_version"

# Instalar dependencias si no están instaladas
echo "Verificando dependencias..."
pip3 install -q -r requirements.txt 2>/dev/null || {
    echo "Instalando dependencias..."
    pip3 install -r requirements.txt
}

# Configurar variables de entorno por defecto
export LLM_ENDPOINT="${LLM_ENDPOINT:-http://localhost:8080/v1/completions}"
export API_HOST="${API_HOST:-0.0.0.0}"
export API_PORT="${API_PORT:-5000}"
export LOG_LEVEL="${LOG_LEVEL:-INFO}"
export DEBUG="${DEBUG:-False}"

echo ""
echo "Configuración:"
echo "  - LLM Endpoint: $LLM_ENDPOINT"
echo "  - API Host: $API_HOST"
echo "  - API Port: $API_PORT"
echo "  - Log Level: $LOG_LEVEL"
echo ""

# Verificar conexión con modelo LLM
echo "Verificando conexión con modelo LLM..."
python3 -c "
import sys
sys.path.insert(0, 'src')
from llm_client import get_llm_client
client = get_llm_client()
if client.validate_connection():
    print('✓ Conexión con LLM establecida')
else:
    print('✗ No se pudo conectar al LLM - Verifica que gpt-oss-120b esté ejecutándose')
    print('  El servidor iniciará pero las historias fallarán')
"

echo ""
echo "Iniciando servidor API..."
echo "========================================="
echo ""

# Iniciar servidor
cd src && python3 api_server.py