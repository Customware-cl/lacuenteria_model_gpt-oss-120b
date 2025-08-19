# Ejemplos de Ejecución - Sistema Cuentería

## Sobre esta carpeta

La carpeta `runs/` contiene las historias procesadas por el sistema. Normalmente esta carpeta está excluida del repositorio (en .gitignore), pero incluimos un ejemplo completo para demostración.

## Ejemplo: emilia-test-001

Historia completa procesada exitosamente el 19 de agosto de 2025.

### Brief original

**Personaje principal:** Emilia, niña de 2 años con pelo castaño ondulado
**Compañero:** Triki, peluche de triceratops púrpura
**Escenario:** Desierto florido
**Mensaje:** Apoyo para que Emilia deje el chupete
**Edad objetivo:** 2-6 años

### Resultado

- **Título final:** "Emilia y Triki: La Aventura del Desierto Florido"
- **Leitmotiv:** "¡Vamos, Triki, a explorar!"
- **Páginas:** 10 páginas con versos rimados
- **Quality scores:** 5.0/5.0 en todos los agentes

### Archivos generados

1. **brief.json** - Brief original de entrada
2. **01_director.json** - Beat sheet y estructura narrativa
3. **02_psicoeducador.json** - Mapa psico-narrativo con recursos pedagógicos
4. **03_cuentacuentos.json** - Texto en versos para cada página
5. **04_editor_claridad.json** - Texto simplificado para comprensión infantil
6. **05_ritmo_rima.json** - Texto con ritmo y rima perfeccionados
7. **06_continuidad.json** - Character Bible con consistencia visual
8. **07_diseno_escena.json** - Prompts visuales detallados por página
9. **08_direccion_arte.json** - Paleta de colores y estilo visual
10. **09_sensibilidad.json** - Auditoría de seguridad infantil
11. **10_portadista.json** - Opciones de título y prompt de portada
12. **11_loader.json** - Mensajes personalizados de carga
13. **12_validador.json** - **JSON FINAL con el cuento completo**
14. **manifest.json** - Estado y metadatos del procesamiento
15. **logs/** - Registros detallados de cada agente

### Cómo usar este ejemplo

Para ver el resultado final del cuento:

```bash
cat runs/emilia-test-001/12_validador.json | python -m json.tool
```

Para ver el progreso del procesamiento:

```bash
cat runs/emilia-test-001/manifest.json | python -m json.tool
```

### Mensaje psicoeducativo integrado

El cuento ayuda a Emilia a dejar el chupete de forma gradual mediante:
- Una "cajita mágica" donde puede guardarlo cuando quiera explorar
- Refuerzo positivo de su valentía
- Disponibilidad del chupete cuando lo necesite
- Celebración de nuevas experiencias sensoriales

### Fragmento del resultado

**Página 1:**
```
Emilia con pelo rizado
camina con Triki a su lado
Por desierto con mil flores
donde brillan los colores
```

**Página 10 (final):**
```
¡Vamos, Triki, a explorar!
El sol se va a descansar
Emilia creció un poquito
hoy fue día muy bonito
```

## Notas técnicas

- Procesamiento exitoso con modelo `gpt-oss-120b`
- Tiempo total: ~3 minutos
- Todos los quality gates pasados (QA >= 4.0)
- Sin errores críticos en el pipeline

Este ejemplo demuestra la capacidad del sistema para generar cuentos personalizados coherentes, educativos y apropiados para la edad objetivo.