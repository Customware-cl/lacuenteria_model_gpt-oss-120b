#!/bin/bash

# Script para probar el sistema localmente sin API

echo "========================================="
echo "   Test Local - Sistema Cuentería       "
echo "========================================="

# Verificar que existe el brief de ejemplo
if [ ! -f "examples/brief_example.json" ]; then
    echo "Error: No se encuentra examples/brief_example.json"
    echo "Ejecuta primero: ./create_example.sh"
    exit 1
fi

# Configurar variables de entorno
export LLM_ENDPOINT="${LLM_ENDPOINT:-http://localhost:8080/v1/completions}"
export LOG_LEVEL="${LOG_LEVEL:-INFO}"

echo ""
echo "Ejecutando pipeline con brief de ejemplo..."
echo ""

# Ejecutar orquestador directamente
cd src && python3 orchestrator.py --brief ../examples/brief_example.json --log-level $LOG_LEVEL

echo ""
echo "========================================="
echo "Procesamiento completado"
echo ""
echo "Revisa los resultados en:"
echo "  runs/<story_id>/12_validador.json"
echo "========================================="