#!/bin/bash

# Script para crear backups de los agentes antes de modificaciones
# Uso: ./backup_agents.sh [nombre_opcional]

echo "💾 BACKUP DE AGENTES"
echo "===================="

# Generar timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Nombre del backup (con timestamp o personalizado)
if [ -n "$1" ]; then
    BACKUP_NAME="$1_$TIMESTAMP"
else
    BACKUP_NAME="backup_$TIMESTAMP"
fi

BACKUP_DIR="agentes/backups/$BACKUP_NAME"

echo "📁 Creando backup en: $BACKUP_DIR"
echo ""

# Crear directorio
mkdir -p "$BACKUP_DIR"

# Copiar archivos
echo "📋 Copiando archivos..."
copied=0
for file in agentes/*.json; do
    if [ -f "$file" ]; then
        filename=$(basename "$file")
        echo -n "  • $filename"
        if cp "$file" "$BACKUP_DIR/"; then
            echo " ✅"
            ((copied++))
        else
            echo " ❌"
        fi
    fi
done

echo ""
echo "===================="
echo "📊 RESUMEN:"
echo "  ✅ Archivos respaldados: $copied"
echo "  📁 Ubicación: $BACKUP_DIR"
echo ""
echo "💡 Para restaurar este backup:"
echo "   ./scripts/restore_originals.sh $BACKUP_DIR"
echo ""

# Crear archivo de metadata
echo "{
  \"timestamp\": \"$TIMESTAMP\",
  \"date\": \"$(date)\",
  \"files_count\": $copied,
  \"purpose\": \"$1\"
}" > "$BACKUP_DIR/metadata.json"

echo "📝 Metadata guardada en: $BACKUP_DIR/metadata.json"
echo ""