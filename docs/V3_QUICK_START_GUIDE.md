# V3 Pipeline Quick Start Guide

## 5-Minute Setup

### Prerequisites Checklist
- [ ] Python 3.8+ installed
- [ ] Access to `/home/ubuntu/cuenteria` directory  
- [ ] Network access to LLM endpoint (69.19.136.204:8000)

### Step 1: Start the Server
```bash
cd /home/ubuntu/cuenteria
python3 src/api_server.py
```
Wait for: `* Running on http://127.0.0.1:5000`

### Step 2: Verify Server Health
Open new terminal:
```bash
curl http://localhost:5000/health
```
Expected: `{"status": "healthy", "llm_status": "connected"}`

### Step 3: Run Your First V3 Story
```bash
python3 test_v3_emilia_felipe.py
```

## Creating Custom V3 Stories

### Method 1: Using Python Script

Create file `my_story.py`:
```python
#!/usr/bin/env python3
import requests
import json
import time
from datetime import datetime

# Configuration
API_URL = "http://localhost:5000/api/stories/create"
STORY_ID = f"my-story-{datetime.now().strftime('%H%M%S')}"

# Your story details
story_brief = {
    "story_id": STORY_ID,
    "personajes": ["Sophie", "Oliver"],  # Your characters
    "historia": "Sophie and Oliver discover a magical garden where they learn about taking care of nature",
    "edad_objetivo": 5,  # Target age: 2-8
    "pipeline_version": "v3"  # IMPORTANT: Must be "v3"
}

print(f"📚 Creating story: {STORY_ID}")

# Send request
response = requests.post(API_URL, json=story_brief)

if response.status_code in [200, 202]:
    print("✅ Story accepted! Waiting for completion...")
    
    # Monitor progress
    while True:
        status = requests.get(f"http://localhost:5000/api/stories/{STORY_ID}/status")
        data = status.json()
        
        print(f"  Status: {data.get('status')} - Agent: {data.get('current_agent', 'waiting')}")
        
        if data.get('status') == 'completed':
            print("🎉 Story complete!")
            
            # Get result
            result = requests.get(f"http://localhost:5000/api/stories/{STORY_ID}/result")
            story = result.json()
            
            print(f"\n📖 Title: {story.get('titulo')}")
            print(f"📄 Pages: {len(story.get('paginas', {}))}")
            print(f"💾 Saved to: runs/*{STORY_ID}/")
            break
        elif data.get('status') == 'error':
            print(f"❌ Error: {data.get('error')}")
            break
            
        time.sleep(3)
else:
    print(f"❌ Failed: {response.text}")
```

Run with:
```bash
python3 my_story.py
```

### Method 2: Using cURL

```bash
# Create story
curl -X POST http://localhost:5000/api/stories/create \
  -H "Content-Type: application/json" \
  -d '{
    "story_id": "curl-test-v3",
    "personajes": ["Luna", "Sol"],
    "historia": "Luna y Sol aprenden sobre el día y la noche",
    "edad_objetivo": 4,
    "pipeline_version": "v3"
  }'

# Check status (repeat until completed)
curl http://localhost:5000/api/stories/curl-test-v3/status

# Get result
curl http://localhost:5000/api/stories/curl-test-v3/result > story_result.json
```

### Method 3: Using the Sync Endpoint (Blocking)

```python
import requests
import json

# This will wait until story is complete (up to 90 seconds)
response = requests.post(
    "http://localhost:5000/api/stories/create-sync",
    json={
        "story_id": "sync-test-v3",
        "personajes": ["Emma", "Leo"],
        "historia": "Emma and Leo learn about sharing toys",
        "edad_objetivo": 3,
        "pipeline_version": "v3"
    },
    timeout=120  # Wait up to 2 minutes
)

if response.status_code == 200:
    story = response.json()
    print(f"Story created: {story['titulo']}")
    with open("my_story.json", "w") as f:
        json.dump(story, f, indent=2, ensure_ascii=False)
```

## Testing Different Features

### Test 1: Multilingual Support (Auto-Detection)

```python
# English story
english_brief = {
    "story_id": "test-english",
    "personajes": ["Alice", "Bob"],
    "historia": "Alice and Bob explore the enchanted forest",
    "edad_objetivo": 6,
    "pipeline_version": "v3"
}

# Spanish story  
spanish_brief = {
    "story_id": "test-spanish",
    "personajes": ["Carlos", "María"],
    "historia": "Carlos y María descubren un tesoro en la playa",
    "edad_objetivo": 5,
    "pipeline_version": "v3"
}

# French story
french_brief = {
    "story_id": "test-french",
    "personajes": ["Pierre", "Marie"],
    "historia": "Pierre et Marie apprennent à faire du vélo",
    "edad_objetivo": 4,
    "pipeline_version": "v3"
}
```

### Test 2: Different Age Groups

```python
# For toddlers (2-3 years)
toddler_story = {
    "story_id": "toddler-test",
    "personajes": ["Bunny", "Bear"],
    "historia": "Bunny and Bear learn to say please and thank you",
    "edad_objetivo": 2,
    "pipeline_version": "v3"
}

# For preschoolers (4-5 years)
preschool_story = {
    "story_id": "preschool-test",
    "personajes": ["Dragon", "Princess"],
    "historia": "Dragon and Princess become unlikely friends",
    "edad_objetivo": 5,
    "pipeline_version": "v3"
}

# For early elementary (6-8 years)
elementary_story = {
    "story_id": "elementary-test",
    "personajes": ["Sam", "Alex"],
    "historia": "Sam and Alex start a recycling club at school",
    "edad_objetivo": 7,
    "pipeline_version": "v3"
}
```

### Test 3: With Educational Values

```python
values_story = {
    "story_id": "values-test",
    "personajes": ["Maya", "Noah"],
    "historia": "Maya helps Noah overcome his fear of the dark",
    "mensaje_a_transmitir": "Courage and helping friends",
    "valores": [
        "develop self-confidence",
        "promote empathy",
        "encourage problem-solving"
    ],
    "edad_objetivo": 5,
    "pipeline_version": "v3"
}
```

## Verifying Results

### Check Generated Files

```bash
# Find your story directory
ls -la runs/ | grep your-story-id

# View the structure
cd runs/[timestamp]-[your-story-id]/
ls -la

# Expected files:
# - manifest.json          (processing metadata)
# - brief.json            (your input)
# - 01_director_v3.json   (story structure)
# - 02_escritor_v3.json   (story text)
# - 03_directorarte_v3.json (art direction)
# - 04_consolidador_v3.json (final story)
```

### Extract Story Text

```bash
# Quick view of story title and first page
cat 04_consolidador_v3.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(f\"Title: {data.get('titulo', 'No title')}\\n\")
print(f\"Page 1:\\n{data.get('paginas', {}).get('1', {}).get('texto', 'No text')}\\n\")
"
```

### View Processing Metrics

```bash
# Check how long each agent took
cat manifest.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
print('Agent Execution Times:')
for agent, info in data.get('timestamps', {}).items():
    duration = info.get('duration', 0)
    print(f'  {agent}: {duration:.1f}s')
"
```

## Common Issues Quick Fixes

### Issue: "pipeline_version not recognized"
**Fix**: Always include `"pipeline_version": "v3"` in your request

### Issue: Story takes too long (>90 seconds)
**Fix**: Check LLM endpoint status:
```bash
curl http://69.19.136.204:8000/v1/models
```

### Issue: "Agent not found" error
**Fix**: Verify v3 agents exist:
```bash
ls flujo/v3/agentes/*.json
# Should show 4 files
```

### Issue: Server won't start
**Fix**: Check port availability:
```bash
lsof -i :5000
# Kill any existing process
pkill -f api_server.py
# Restart
python3 src/api_server.py
```

## Performance Benchmarks

| Story Complexity | Expected Time | Agents | Token Usage |
|-----------------|---------------|--------|-------------|
| Simple (2 characters, basic plot) | 45-60s | 4 | ~8,000 |
| Medium (3-4 characters, subplot) | 60-75s | 4 | ~12,000 |
| Complex (5+ characters, multiple themes) | 75-90s | 4 | ~16,000 |

## Output Format Reference

### Final Story Structure (04_consolidador_v3.json)

```json
{
  "titulo": "The Magical Garden Adventure",
  "portada": {
    "prompt_imagen": "Vibrant garden scene with Sophie and Oliver...",
    "paleta_colores": {
      "primario": "#2ECC71",
      "secundario": "#3498DB",
      "terciario": "#F39C12"
    }
  },
  "paginas": {
    "1": {
      "texto": "In a corner of the yard so green,\nSophie and Oliver found something they'd never seen...",
      "imagen": "Wide shot of backyard with two children discovering a hidden garden gate..."
    },
    "2": { "..." },
    "...up to 10": { "..." }
  },
  "loader": [
    "Planting seeds of imagination...",
    "Watering the story with magic...",
    "Growing wonderful adventures..."
  ]
}
```

## Advanced Tips

### Tip 1: Batch Processing
```python
stories = [
    {"story_id": "batch-1", "personajes": ["A", "B"], "historia": "..."},
    {"story_id": "batch-2", "personajes": ["C", "D"], "historia": "..."},
    {"story_id": "batch-3", "personajes": ["E", "F"], "historia": "..."}
]

for brief in stories:
    brief["pipeline_version"] = "v3"
    requests.post("http://localhost:5000/api/stories/create", json=brief)
    time.sleep(2)  # Don't overwhelm the server
```

### Tip 2: Webhook Notifications
```python
story_with_webhook = {
    "story_id": "webhook-test",
    "personajes": ["Max", "Ruby"],
    "historia": "Max and Ruby learn about seasons",
    "edad_objetivo": 4,
    "pipeline_version": "v3",
    "webhook_url": "https://your-server.com/story-complete"
}
# Your webhook will receive updates as story processes
```

### Tip 3: Custom Monitoring Script
```python
def monitor_story(story_id, check_interval=2):
    """Monitor story with progress bar"""
    import time
    agents = ["01_director_v3", "02_escritor_v3", 
              "03_directorarte_v3", "04_consolidador_v3"]
    
    print(f"Monitoring: {story_id}")
    while True:
        response = requests.get(f"http://localhost:5000/api/stories/{story_id}/status")
        data = response.json()
        
        current = data.get("current_agent", "")
        if current in agents:
            progress = agents.index(current) + 1
            bar = "█" * progress + "░" * (4 - progress)
            print(f"\r[{bar}] {progress}/4 - {current}", end="")
        
        if data.get("status") in ["completed", "error"]:
            print(f"\n{data.get('status').upper()}!")
            break
            
        time.sleep(check_interval)
```

## Next Steps

1. **Read Full Documentation**: See `/home/ubuntu/cuenteria/docs/V3_FLOW_DOCUMENTATION.md`
2. **Explore Agent Prompts**: Check `flujo/v3/agentes/` directory
3. **Customize Settings**: Modify `flujo/v3/config.json`
4. **Build Integration**: Use the API in your application

## Support Resources

- **Logs**: `runs/*/logs/` for debugging
- **Config**: `flujo/v3/` for customization  
- **Tests**: `test_v3_*.py` for examples
- **API Docs**: `docs/V3_FLOW_DOCUMENTATION.md#api-reference`

---

*Quick Start Guide v1.0 - September 2024*