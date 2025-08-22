#!/bin/bash

# Script para restaurar los prompts originales de los agentes
# Uso: ./restore_originals.sh [backup_dir]

echo "🔄 RESTAURACIÓN DE AGENTES ORIGINALES"
echo "======================================"

# Directorio de backup por defecto (el más reciente)
BACKUP_DIR=${1:-"agentes/backups/original_20250821_2145"}

# Verificar que el directorio de backup existe
if [ ! -d "$BACKUP_DIR" ]; then
    echo "❌ Error: No se encuentra el directorio de backup: $BACKUP_DIR"
    echo ""
    echo "Backups disponibles:"
    ls -la agentes/backups/ 2>/dev/null
    exit 1
fi

echo "📁 Usando backup desde: $BACKUP_DIR"
echo ""

# Confirmar restauración
read -p "⚠️  ¿Estás seguro de que quieres restaurar los agentes originales? (s/n): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Ss]$ ]]; then
    echo "❌ Restauración cancelada"
    exit 1
fi

echo ""
echo "🔄 Restaurando archivos..."
echo ""

# Contador de archivos
restored=0
failed=0

# Restaurar cada archivo JSON
for file in "$BACKUP_DIR"/*.json; do
    if [ -f "$file" ]; then
        filename=$(basename "$file")
        echo -n "  Restaurando $filename... "
        
        if cp "$file" "agentes/$filename"; then
            echo "✅"
            ((restored++))
        else
            echo "❌"
            ((failed++))
        fi
    fi
done

echo ""
echo "======================================"
echo "📊 RESUMEN:"
echo "  ✅ Archivos restaurados: $restored"

if [ $failed -gt 0 ]; then
    echo "  ❌ Archivos con error: $failed"
else
    echo "  🎉 Todos los archivos restaurados exitosamente"
fi

echo ""
echo "💡 Para verificar los cambios:"
echo "   diff -u agentes/editor_claridad.json $BACKUP_DIR/editor_claridad.json"
echo ""
echo "📝 Para crear un nuevo backup antes de modificar:"
echo "   ./scripts/backup_agents.sh"
echo ""