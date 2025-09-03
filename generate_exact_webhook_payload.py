#!/usr/bin/env python3
"""
Genera el payload EXACTO como fue enviado al webhook
"""

import json
import time
from pathlib import Path
from datetime import datetime

STORY_ID = "6534605d-961d-43be-890a-8da9a59bcd94-20250902-155259"

# Cargar validador
validador_path = Path(f"/home/ubuntu/cuenteria/runs/{STORY_ID}/outputs/agents/12_validador.json")
with open(validador_path, 'r', encoding='utf-8') as f:
    story_result = json.load(f)

# Cargar manifest
manifest_path = Path(f"/home/ubuntu/cuenteria/runs/{STORY_ID}/manifest.json")
with open(manifest_path, 'r', encoding='utf-8') as f:
    manifest = json.load(f)

# Calcular QA scores
qa_historial = manifest.get("qa_historial", {})
all_scores = []
for agent_scores in qa_historial.values():
    if isinstance(agent_scores, dict):
        if "promedio" in agent_scores:
            score = agent_scores["promedio"].get("nota_final", 0)
            if isinstance(score, (int, float)):
                all_scores.append(score)

overall = sum(all_scores) / len(all_scores) if all_scores else 0.0
qa_scores = {
    "overall": round(overall, 2),
    "by_agent": qa_historial
}

# Calcular tiempo de procesamiento
created_at = manifest.get("created_at", "")
updated_at = manifest.get("updated_at", "")
processing_time = 0

if created_at and updated_at:
    try:
        start = datetime.fromisoformat(created_at)
        end = datetime.fromisoformat(updated_at)
        processing_time = (end - start).total_seconds()
    except:
        pass

# Construir payload EXACTO
webhook_payload = {
    "event": "story_complete",
    "timestamp": time.time(),
    "data": {
        "status": "success",
        "story_id": manifest.get("original_story_id", "6534605d-961d-43be-890a-8da9a59bcd94"),
        "result": story_result,
        "qa_scores": qa_scores,
        "processing_time": processing_time,
        "metadata": {
            "retries": manifest.get("reintentos", {}),
            "warnings": manifest.get("devoluciones", []),
            "pipeline_version": "v2",
            "folder": STORY_ID
        }
    }
}

# Guardar en archivo
output_path = Path("/home/ubuntu/cuenteria/webhook_payload_exact.json")
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(webhook_payload, f, ensure_ascii=False, indent=2)

print(f"✅ Payload exacto guardado en: {output_path}")
print(f"📏 Tamaño: {len(json.dumps(webhook_payload))} bytes")