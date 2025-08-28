#!/usr/bin/env python3
"""Debug v2 agent loading"""
import sys
sys.path.append('src')

from config import load_version_config
from agent_runner import AgentRunner
import json

# Cargar configuración v2
v2_config = load_version_config('v2')
print("V2 Config loaded:")
print(f"  Pipeline: {v2_config.get('pipeline', [])[:3]}...")
print(f"  Agents path: {v2_config.get('agents_path')}")
print(f"  Dependencies keys: {list(v2_config.get('dependencies', {}).keys())[:3]}...")

# Crear runner con v2
runner = AgentRunner("test-debug", version='v2')
print(f"\nRunner version: {runner.version}")
print(f"Runner config pipeline: {runner.version_config.get('pipeline', [])[:3]}...")

# Probar cargar el primer agente
first_agent = v2_config['pipeline'][0]
print(f"\nTrying to load agent: {first_agent}")

try:
    from config import get_agent_prompt_path
    path = get_agent_prompt_path(first_agent, 'v2')
    print(f"Agent path: {path}")
    print(f"Path exists: {path.exists()}")
    
    if path.exists():
        with open(path, 'r') as f:
            agent_data = json.load(f)
        print(f"Agent loaded successfully, content length: {len(agent_data.get('content', ''))}")
except Exception as e:
    print(f"Error loading agent: {e}")
    import traceback
    traceback.print_exc()