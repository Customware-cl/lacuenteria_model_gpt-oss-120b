#!/usr/bin/env python3
"""Test para verificar el nombre del agente que se está usando"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

# Simular lo que hace orchestrator
version = "v2"
print(f"Pipeline version: {version}")

# Ver qué pipeline se usa
if version == "v2":
    agentes_dir = f"flujo/{version}/agentes"
    print(f"Directorio de agentes: {agentes_dir}")
    
    # Listar archivos
    import glob
    agent_files = sorted(glob.glob(f"{agentes_dir}/*.json"))
    
    print("\nAgentes encontrados:")
    for file in agent_files:
        agent_name = os.path.basename(file).replace('.json', '')
        print(f"  - {agent_name}")
        
        # Simular lo que haría agent_runner
        from config import AGENT_MAX_TOKENS
        max_tokens = AGENT_MAX_TOKENS.get(agent_name, None)
        if max_tokens:
            print(f"    ✓ max_tokens configurado: {max_tokens}")
        else:
            print(f"    ✗ sin configuración de max_tokens")