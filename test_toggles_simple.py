#!/usr/bin/env python3
"""
Test simple para verificar la funcionalidad de agent_toggles
"""
import json
from pathlib import Path

def verificar_toggles():
    """Verifica la configuración de toggles en el archivo config"""
    
    config_path = Path("flujo/v2/config.json")
    
    print("🔍 Verificando configuración de agent_toggles\n")
    print("=" * 60)
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Verificar que existe la sección agent_toggles
    if 'agent_toggles' not in config:
        print("❌ ERROR: No se encontró la sección 'agent_toggles'")
        return False
    
    print("✅ Sección 'agent_toggles' encontrada\n")
    
    # Mostrar estado de cada agente
    toggles = config['agent_toggles']
    pipeline = config.get('pipeline', [])
    
    print("📋 Estado de los agentes:")
    print("-" * 40)
    
    agentes_habilitados = []
    agentes_deshabilitados = []
    
    for agent in pipeline:
        enabled = toggles.get(agent, True)
        status = "✅ HABILITADO" if enabled else "❌ DESHABILITADO"
        print(f"  {agent:20s} : {status}")
        
        if enabled:
            agentes_habilitados.append(agent)
        else:
            agentes_deshabilitados.append(agent)
    
    print("\n" + "=" * 60)
    print(f"\n📊 Resumen:")
    print(f"  Total agentes: {len(pipeline)}")
    print(f"  Habilitados:   {len(agentes_habilitados)}")
    print(f"  Deshabilitados: {len(agentes_deshabilitados)}")
    
    if agentes_deshabilitados:
        print(f"\n🚫 Agentes que serán saltados:")
        for agent in agentes_deshabilitados:
            print(f"  - {agent}")
            
            # Verificar dependencias
            if agent == "04_editor_claridad":
                print(f"    → 05_ritmo_rima usará 03_cuentacuentos.json")
            elif agent == "05_ritmo_rima":
                print(f"    → 06_continuidad usará 03_cuentacuentos.json (o 04_editor_claridad si existe)")
    
    print("\n" + "=" * 60)
    print("\n✅ Verificación completada")
    
    # Mostrar cómo cambiar toggles
    print("\n💡 Para cambiar el estado de un agente, edita:")
    print(f"   {config_path}")
    print("   En la sección 'agent_toggles', cambia true/false según necesites")
    
    return True

if __name__ == "__main__":
    verificar_toggles()