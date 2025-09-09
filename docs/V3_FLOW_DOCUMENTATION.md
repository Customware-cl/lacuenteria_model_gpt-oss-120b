# Cuentería v3 Flow - Complete Documentation Guide

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [Context & Background](#context--background)
3. [Architecture Overview](#architecture-overview)
4. [Getting Started Guide](#getting-started-guide)
5. [Core Concepts](#core-concepts)
6. [V3 vs V2 Comparison](#v3-vs-v2-comparison)
7. [Agent Pipeline Details](#agent-pipeline-details)
8. [Testing Guide](#testing-guide)
9. [API Reference](#api-reference)
10. [Troubleshooting](#troubleshooting)
11. [Configuration Reference](#configuration-reference)

---

## Executive Summary

**What is v3?** 
V3 is a streamlined, optimized version of the Cuentería story generation pipeline that reduces the process from 12 agents (v2) to just 4 essential agents, resulting in faster generation times while maintaining quality.

**Why v3 exists:**
- **Speed**: Reduces generation time from ~180 seconds to ~60-90 seconds
- **Simplicity**: Consolidates overlapping agent responsibilities 
- **Quality**: Removes QA verification overhead while maintaining output quality through optimized prompts
- **Efficiency**: Eliminates redundant processing steps

**Who uses it:**
- Production environments requiring faster response times
- Testing environments for rapid iteration
- Users who need quick story generation without compromising essential quality

**When to use v3:**
- When generation speed is a priority
- For testing new story concepts quickly
- When the simplified 4-agent pipeline meets all requirements

---

## Context & Background

### Problem Being Solved
The original v1 pipeline with 12 agents was comprehensive but slow, taking 3-5 minutes per story. V2 added optimizations and parallel processing but still maintained all 12 agents. V3 represents a fundamental rethinking: what if we could achieve similar quality with fewer, more focused agents?

### Key Decisions Made
1. **Agent Consolidation**: Combined related agents into unified roles
2. **QA Removal**: Eliminated separate QA verification step (QA is now built into prompts)
3. **Direct Output**: Each agent produces immediately usable output without multiple iterations
4. **Multilingual Support**: Native support for multiple languages detected from input

### Relationship to Other Systems
- **v1**: The original 12-agent sequential pipeline (production legacy)
- **v2**: Optimized 12-agent pipeline with parallel processing and toggles
- **v3**: Streamlined 4-agent pipeline (current focus)

---

## Architecture Overview

### High-Level System Flow

```
User Input (Brief)
    ↓
[API Server] → Detects v3 request
    ↓
[Orchestrator] → Loads v3 configuration
    ↓
[Agent Pipeline - 4 Sequential Steps]
    ├── 01_director_v3 → Story structure & pedagogy
    ├── 02_escritor_v3 → Story text in verses
    ├── 03_directorarte_v3 → Visual prompts & art direction
    └── 04_consolidador_v3 → Final assembly & validation
    ↓
[Output] → Complete story JSON
```

### Component Responsibilities

| Component | v3 Responsibility | Replaces from v2 |
|-----------|------------------|------------------|
| director_v3 | Story structure, pedagogy, character development | director + psicoeducador + continuidad |
| escritor_v3 | Complete story text in verses | cuentacuentos + editor_claridad + ritmo_rima |
| directorarte_v3 | Visual prompts and art style | diseno_escena + direccion_arte + sensibilidad |
| consolidador_v3 | Final assembly and formatting | portadista + loader + validador |

### Technology Stack
- **LLM Model**: GPT-OSS-120B (endpoint: `http://69.19.136.204:8000`)
- **Framework**: Flask (Python 3.8+)
- **Configuration**: JSON-based per version
- **Storage**: File-based in `runs/` directory

---

## Getting Started Guide

### Prerequisites

#### Required Tools
- Python 3.8 or higher
- pip (Python package manager)
- Access to the GPT-OSS-120B endpoint
- 2GB free disk space for story outputs

#### Required Knowledge
- Basic understanding of REST APIs
- Command line/terminal usage
- JSON data format familiarity

#### Required Access
- Network access to port 5000 (API server)
- Write permissions to `runs/` directory
- Read permissions to `flujo/v3/` directory

### Environment Setup

#### Step 1: Verify Python Installation
```bash
python3 --version
# Should output: Python 3.8.x or higher
```

#### Step 2: Install Dependencies
```bash
cd /home/ubuntu/cuenteria
pip3 install -r requirements.txt
```

#### Step 3: Verify Configuration Files
```bash
# Check v3 configuration exists
ls -la flujo/v3/
# Should show: config.json, dependencies.json, agent_config.json, agentes/
```

#### Step 4: Start the API Server
```bash
python3 src/api_server.py
# Server starts on http://localhost:5000
```

#### Step 5: Verify Server Health
```bash
curl http://localhost:5000/health
# Should return: {"status": "healthy", "llm_status": "connected", ...}
```

### First Successful Interaction

#### Running Your First v3 Story
```bash
# Use the provided test script
python3 test_v3_emilia_felipe.py
```

Expected output:
```
[10:30:00] INFO: Servidor activo - Modelo: connected
[10:30:01] INFO: Historia aceptada para procesamiento
[10:30:05] AGENT: 🎬 Agente 1/4: 01_director_v3
[10:30:20] AGENT: ✍️ Agente 2/4: 02_escritor_v3
[10:30:35] AGENT: 🎨 Agente 3/4: 03_directorarte_v3
[10:30:50] AGENT: 📦 Agente 4/4: 04_consolidador_v3
[10:30:55] SUCCESS: ✅ Generación completada en 54.2 segundos
```

### Common Setup Issues and Solutions

| Issue | Solution |
|-------|----------|
| "Server not found" | Ensure API server is running: `python3 src/api_server.py` |
| "Permission denied" | Check write permissions: `chmod 755 runs/` |
| "Module not found" | Install dependencies: `pip3 install -r requirements.txt` |
| "LLM timeout" | Check network connection to `69.19.136.204:8000` |
| "Config not found" | Ensure you're in the correct directory: `/home/ubuntu/cuenteria` |

---

## Core Concepts

### Domain Terminology Glossary

| Term | Definition | Context |
|------|------------|---------|
| **Brief** | Initial story request containing characters, plot, and educational goals | Input to the system |
| **Pipeline** | Sequential execution of agents to generate a story | v3 has 4 agents |
| **Agent** | Specialized AI component with a specific role | Each handles one aspect |
| **Consolidador** | Final agent that assembles all parts into complete story | Unique to v3 |
| **Manifest** | Metadata file tracking processing state and history | Located in each run folder |
| **Webhook** | Optional URL for progress notifications | Sends updates to external systems |
| **Story ID** | Unique identifier for each story generation | Format: `timestamp-uuid` |

### Key Abstractions

#### Version Configuration System
Each pipeline version (v1, v2, v3) has its own configuration directory:
```
flujo/
  v3/
    config.json         # Main configuration
    dependencies.json   # Agent dependencies
    agent_config.json   # Per-agent settings
    agentes/           # Agent prompt definitions
```

#### Agent Communication Pattern
Agents communicate through JSON files:
1. Each agent reads its dependencies (previous agent outputs)
2. Processes the information with the LLM
3. Writes its output to a JSON file
4. Next agent reads this output as input

### Design Patterns Used

1. **Pipeline Pattern**: Sequential processing with clear input/output contracts
2. **Configuration-Driven**: Behavior controlled by JSON configurations
3. **Stateless Agents**: Each agent is independent and stateless
4. **File-Based Communication**: Robust, debuggable inter-agent communication

### Business Rules and Constraints

1. **Age Groups**: Stories target specific age ranges: 2-3, 4-5, or 6-8 years
2. **Page Count**: Fixed at 10 pages per story
3. **Language**: Automatically detected from input, supports multiple languages
4. **Processing Time**: Target under 90 seconds for v3
5. **No QA in v3**: Quality is built into prompts, not verified separately

---

## V3 vs V2 Comparison

### Agent Count Comparison

| Aspect | V2 (12 agents) | V3 (4 agents) |
|--------|---------------|--------------|
| **Director** | Separate director agent | Combined director + psicoeducador + continuidad |
| **Writing** | 3 agents (cuentacuentos, editor, ritmo) | Single escritor_v3 agent |
| **Art** | 3 agents (diseño, dirección, sensibilidad) | Single directorarte_v3 agent |
| **Final** | 3 agents (portada, loader, validador) | Single consolidador_v3 agent |
| **QA** | Separate verificador_qa agent | Built into prompts |

### Configuration Differences

#### V2 Configuration
```json
{
  "version": "v2",
  "pipeline": [12 agents...],
  "mode_verificador_qa": true,
  "parallel_execution": true,
  "agent_toggles": {
    // Can disable individual agents
  }
}
```

#### V3 Configuration
```json
{
  "version": "v3",
  "pipeline": [4 agents only],
  "mode_verificador_qa": false,
  "skip_qa": true,
  "parallel_execution": false
}
```

### Performance Metrics

| Metric | V2 | V3 | Improvement |
|--------|----|----|-------------|
| Average Time | 180s | 60s | 67% faster |
| Agent Calls | 12 | 4 | 67% fewer |
| LLM Requests | 12-24 (with retries) | 4 | 75-83% fewer |
| File I/O Operations | ~36 | ~12 | 67% fewer |

### Feature Comparison

| Feature | V2 | V3 |
|---------|----|----|
| QA Verification | ✅ Required | ❌ Not needed |
| Parallel Processing | ✅ Supported | ❌ Sequential only |
| Agent Toggles | ✅ Can disable agents | ✅ Supported |
| Retry on Failure | ✅ Up to 2 retries | ✅ Up to 2 retries |
| Multilingual | ❌ Spanish only | ✅ Auto-detects language |
| Psychoeducational Focus | ✅ Separate agent | ✅ Integrated in director |

---

## Agent Pipeline Details

### 01_director_v3 - Story Structure & Pedagogy

**Purpose**: Creates the complete story structure with pedagogical elements integrated

**Input Dependencies**:
- `brief.json` - The initial story request

**Key Responsibilities**:
1. Analyze input and detect language automatically
2. Define story structure across 10 pages
3. Integrate psychological and educational elements
4. Create character continuity guidelines
5. Generate art direction notes for each page
6. Define age-appropriate vocabulary and complexity

**Output Structure**:
```json
{
  "titulo": "Selected title",
  "idioma": "detected language",
  "personajes": [...],
  "edad_objetivo": "4-5",
  "paginas": [
    {
      "numero": 1,
      "objetivo_pedagogico": "...",
      "lineamientos_escritor": "...",
      "prompt_arte": "...",
      "triada_eer": {...}
    }
  ]
}
```

### 02_escritor_v3 - Story Text Creation

**Purpose**: Transforms the structure into actual story text in verse format

**Input Dependencies**:
- `01_director_v3.json` - Story structure and guidelines

**Key Responsibilities**:
1. Write story text in verses for each page
2. Maintain age-appropriate vocabulary
3. Ensure rhythm and rhyme consistency
4. Follow pedagogical objectives per page
5. Create engaging, musical text

**Output Structure**:
```json
{
  "paginas": {
    "1": {
      "texto": "Story text in verses...",
      "notas_ritmo": "Rhythm pattern used"
    }
  }
}
```

### 03_directorarte_v3 - Visual Direction

**Purpose**: Creates detailed visual prompts for illustrations

**Input Dependencies**:
- `01_director_v3.json` - Story structure
- `02_escritor_v3.json` - Story text

**Key Responsibilities**:
1. Generate detailed illustration prompts for each page
2. Define consistent art style across the book
3. Specify color palettes and visual themes
4. Ensure visual continuity of characters
5. Add safety and sensitivity considerations

**Output Structure**:
```json
{
  "estilo_general": "Art style description",
  "paleta_colores": {...},
  "paginas": {
    "1": {
      "prompt_ilustracion": "Detailed visual prompt...",
      "elementos_visuales": [...]
    }
  }
}
```

### 04_consolidador_v3 - Final Assembly

**Purpose**: Assembles all components into the final story format

**Input Dependencies**:
- `01_director_v3.json` - Structure
- `02_escritor_v3.json` - Text
- `03_directorarte_v3.json` - Visuals

**Key Responsibilities**:
1. Combine all elements into final format
2. Generate title and cover design
3. Create loading messages for UI
4. Validate completeness
5. Format for delivery

**Output Structure**:
```json
{
  "titulo": "Final story title",
  "portada": {
    "prompt_imagen": "Cover illustration prompt",
    "paleta_colores": {...}
  },
  "paginas": {
    "1": {
      "texto": "Page text",
      "imagen": "Illustration prompt"
    }
  },
  "loader": ["Loading message 1", "Loading message 2", ...]
}
```

---

## Testing Guide

### Step-by-Step Testing Instructions

#### Test 1: Basic v3 Story Generation

**Purpose**: Verify v3 pipeline works end-to-end

**Steps**:
1. Start the API server:
   ```bash
   python3 src/api_server.py
   ```

2. Run the test script:
   ```bash
   python3 test_v3_emilia_felipe.py
   ```

3. Monitor the output for:
   - All 4 agents completing
   - Total time under 90 seconds
   - No error messages

4. Verify output files:
   ```bash
   ls -la runs/*emilia-felipe*/
   # Should see 4 agent JSON files
   ```

#### Test 2: Custom Story Request

**Purpose**: Test with your own story parameters

**Create a test file** `my_v3_test.py`:
```python
#!/usr/bin/env python3
import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:5000"
STORY_ID = f"my-test-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

brief = {
    "story_id": STORY_ID,
    "personajes": ["Luna", "Estrella"],
    "historia": "Luna and Star learn about friendship in the night sky",
    "mensaje_a_transmitir": "The value of friendship and cooperation",
    "edad_objetivo": 5,
    "pipeline_version": "v3"  # Critical: Must specify v3
}

print(f"Creating story: {STORY_ID}")

# Create story
response = requests.post(
    f"{BASE_URL}/api/stories/create",
    json=brief,
    timeout=10
)

if response.status_code in [200, 202]:
    print("Story accepted!")
    
    # Wait for completion
    time.sleep(5)
    
    # Check status
    for i in range(30):  # Check for up to 90 seconds
        status_response = requests.get(
            f"{BASE_URL}/api/stories/{STORY_ID}/status"
        )
        
        if status_response.status_code == 200:
            status_data = status_response.json()
            print(f"Status: {status_data.get('status')} - Agent: {status_data.get('current_agent')}")
            
            if status_data.get('status') == 'completed':
                print("Story completed successfully!")
                
                # Get result
                result_response = requests.get(
                    f"{BASE_URL}/api/stories/{STORY_ID}/result"
                )
                
                if result_response.status_code == 200:
                    result = result_response.json()
                    print(f"Title: {result.get('titulo')}")
                    print(f"Pages: {len(result.get('paginas', {}))}")
                break
        
        time.sleep(3)
else:
    print(f"Error: {response.status_code}")
    print(response.text)
```

**Run the test**:
```bash
python3 my_v3_test.py
```

#### Test 3: Verify No QA Execution

**Purpose**: Confirm v3 skips QA verification

**Steps**:
1. Run the no-QA test:
   ```bash
   python3 test_v3_sin_qa.py
   ```

2. Check the output confirms:
   - "No se encontraron verificaciones QA"
   - Process completes without QA mentions

3. Verify in logs:
   ```bash
   grep -i "verificador_qa" runs/*test-v3-noqa*/logs/*.log
   # Should return no results
   ```

### Required Configuration Files

#### Essential Files for v3

1. **Main Configuration** (`flujo/v3/config.json`):
   - Defines pipeline order
   - Sets QA skip flag
   - Configures timeouts

2. **Dependencies** (`flujo/v3/dependencies.json`):
   - Maps agent input dependencies
   - Ensures correct data flow

3. **Agent Configs** (`flujo/v3/agent_config.json`):
   - Per-agent temperature settings
   - Token limits
   - Optional parameters

4. **Agent Prompts** (`flujo/v3/agentes/*.json`):
   - System prompts for each agent
   - Must exist for all 4 agents

### Environment Variables

No specific environment variables required for v3, but ensure:
- `.env` file exists with `anon_key` for webhook authentication (optional)
- Python path includes project root

### Sample Test Commands

```bash
# Quick test with default parameters
curl -X POST http://localhost:5000/api/stories/create \
  -H "Content-Type: application/json" \
  -d '{
    "story_id": "quick-test-v3",
    "personajes": ["Max", "Luna"],
    "historia": "Max and Luna go on an adventure",
    "edad_objetivo": 4,
    "pipeline_version": "v3"
  }'

# Check status
curl http://localhost:5000/api/stories/quick-test-v3/status

# Get result
curl http://localhost:5000/api/stories/quick-test-v3/result
```

### Expected Outputs

#### Successful v3 Generation

**Manifest file** (`manifest.json`):
```json
{
  "story_id": "20250905-103000-uuid",
  "pipeline_version": "v3",
  "estado": "completado",
  "timestamps": {
    "01_director_v3": {...},
    "02_escritor_v3": {...},
    "03_directorarte_v3": {...},
    "04_consolidador_v3": {...}
  }
}
```

**Output structure**:
```
runs/
  20250905-103000-story-id/
    manifest.json
    brief.json
    01_director_v3.json
    02_escritor_v3.json
    03_directorarte_v3.json
    04_consolidador_v3.json
    outputs/
      agents/
        [all agent outputs]
    logs/
      [agent logs]
```

### Common Issues and Solutions

| Issue | Symptom | Solution |
|-------|---------|----------|
| Wrong pipeline version | 12 agents run instead of 4 | Ensure `"pipeline_version": "v3"` in request |
| Missing v3 config | "No config for version v3" | Check `flujo/v3/config.json` exists |
| Agent not found | "Agent 01_director_v3 not found" | Verify `flujo/v3/agentes/` contains all 4 agents |
| Timeout errors | Process stops after 900s | Check LLM endpoint is responsive |
| Output incomplete | Missing final JSON | Check `04_consolidador_v3.json` for errors |

---

## API Reference

### Creating a v3 Story

#### Endpoint
`POST /api/stories/create`

#### Request Headers
```
Content-Type: application/json
```

#### Request Body
```json
{
  "story_id": "unique-identifier",
  "personajes": ["Character1", "Character2"],
  "historia": "Main plot of the story",
  "mensaje_a_transmitir": "Educational message (optional for v3)",
  "edad_objetivo": 5,
  "pipeline_version": "v3",
  "webhook_url": "https://optional-webhook.com/notify"
}
```

#### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| story_id | string | Yes | Unique identifier for the story |
| personajes | array | Yes | List of character names |
| historia | string | Yes | Main plot/storyline |
| mensaje_a_transmitir | string | No* | Educational goal (*derived from valores in v3) |
| edad_objetivo | integer | Yes | Target age (2-8) |
| pipeline_version | string | Yes | Must be "v3" for v3 pipeline |
| webhook_url | string | No | URL for progress notifications |
| relacion_personajes | array | No | Character relationships (v3 feature) |
| valores | array | No | Values to emphasize (v3 feature) |

#### Response (202 Accepted)
```json
{
  "status": "accepted",
  "story_id": "20250905-103000-unique-identifier",
  "pipeline_version": "v3",
  "estimated_time": 90,
  "message": "Story queued for processing"
}
```

### Checking Story Status

#### Endpoint
`GET /api/stories/{story_id}/status`

#### Response
```json
{
  "status": "processing|completed|error",
  "current_agent": "02_escritor_v3",
  "progress": "2/4",
  "elapsed_time": 35,
  "pipeline_version": "v3"
}
```

### Getting Story Result

#### Endpoint
`GET /api/stories/{story_id}/result`

#### Response (v3 format)
```json
{
  "titulo": "The Adventure of Max and Luna",
  "portada": {
    "prompt_imagen": "Cover illustration prompt...",
    "paleta_colores": {
      "primario": "#4A90E2",
      "secundario": "#F5A623"
    }
  },
  "paginas": {
    "1": {
      "texto": "Page 1 text in verses...",
      "imagen": "Detailed illustration prompt..."
    },
    "2": {...},
    "...": "up to page 10"
  },
  "loader": [
    "Creating magical moments...",
    "Painting dreams with words..."
  ],
  "metadata": {
    "pipeline_version": "v3",
    "processing_time": 87.3,
    "agents_executed": ["01_director_v3", "02_escritor_v3", "03_directorarte_v3", "04_consolidador_v3"]
  }
}
```

### V3-Specific Features

#### Multilingual Support
V3 automatically detects the language from the `historia` field:
```json
{
  "historia": "Luna y Sol aprenden sobre la amistad",  // Spanish detected
  "historia": "Moon and Sun learn about friendship",    // English detected
  "historia": "Lune et Soleil apprennent l'amitié"     // French detected
}
```

#### Enhanced Character Relationships
```json
{
  "personajes": ["Emma", "David"],
  "relacion_personajes": ["hermanos", "siblings", "frères et soeurs"]
}
```

#### Values-Based Generation
```json
{
  "valores": [
    "desarrollar autoestima",
    "promover comunicación asertiva",
    "fomentar trabajo en equipo"
  ]
}
```

---

## Troubleshooting

### Diagnostic Commands

#### Check Server Status
```bash
# Verify API server is running
curl http://localhost:5000/health

# Check specific story status
curl http://localhost:5000/api/stories/{story_id}/status

# View server logs
tail -f api_server_v3.log
```

#### Verify Configuration
```bash
# Check v3 config exists
cat flujo/v3/config.json | python3 -m json.tool

# Verify all agents present
ls -la flujo/v3/agentes/*.json | wc -l
# Should output: 4

# Check dependencies
cat flujo/v3/dependencies.json | python3 -m json.tool
```

#### Inspect Story Output
```bash
# Find latest v3 run
ls -lt runs/ | grep v3 | head -1

# Check manifest
cat runs/{story_folder}/manifest.json | python3 -m json.tool

# Verify all outputs generated
ls runs/{story_folder}/*.json
# Should show: brief.json + 4 agent JSONs
```

### Common Errors and Solutions

#### Error: "No configuration found for version v3"
**Cause**: Missing v3 configuration files
**Solution**:
```bash
# Verify v3 directory exists
ls -la flujo/v3/
# If missing, check git status
git status flujo/v3/
git checkout flujo/v3/  # Restore if deleted
```

#### Error: "Agent 01_director_v3 not found"
**Cause**: Missing agent definition file
**Solution**:
```bash
# Check agent file exists
ls flujo/v3/agentes/01_director_v3.json
# If missing, restore from git
git checkout flujo/v3/agentes/01_director_v3.json
```

#### Error: "Pipeline version v3 not recognized"
**Cause**: API server using old code
**Solution**:
```bash
# Restart API server
pkill -f api_server.py
python3 src/api_server.py
```

#### Error: "LLM timeout after 900 seconds"
**Cause**: Network issues or LLM overload
**Solution**:
1. Check network connectivity:
   ```bash
   curl http://69.19.136.204:8000/v1/models
   ```
2. Reduce max_tokens in agent_config.json
3. Retry with simpler story brief

#### Error: "JSON decode error in consolidador"
**Cause**: Malformed JSON from previous agent
**Solution**:
1. Check previous agent output:
   ```bash
   python3 -m json.tool runs/{story_id}/03_directorarte_v3.json
   ```
2. If invalid, check logs for truncation:
   ```bash
   tail runs/{story_id}/logs/03_directorarte_v3.log
   ```

### Debugging Strategies

#### Enable Verbose Logging
```python
# In src/api_server.py, set:
logging.basicConfig(level=logging.DEBUG)
```

#### Test Individual Agents
```python
# Create test script: test_single_agent.py
from src.agent_runner import AgentRunner

runner = AgentRunner("test-story", version="v3")
result = runner.run_agent("01_director_v3")
print(result)
```

#### Monitor Real-time Processing
```bash
# Watch logs in real-time
tail -f runs/*/logs/*.log

# Monitor file creation
watch -n 1 'ls -la runs/*/\*.json'
```

### Log Locations and Interpretation

#### Log File Structure
```
runs/{story_id}/logs/
  01_director_v3.log      # Director agent execution
  02_escritor_v3.log      # Writer agent execution  
  03_directorarte_v3.log  # Art director execution
  04_consolidador_v3.log  # Consolidator execution
```

#### Reading Agent Logs
```
[2024-09-05 10:30:15] Starting agent: 01_director_v3
[2024-09-05 10:30:15] Loading dependencies: ['brief.json']
[2024-09-05 10:30:16] Calling LLM with temperature: 0.7
[2024-09-05 10:30:25] LLM response received (3456 tokens)
[2024-09-05 10:30:25] Output saved to: 01_director_v3.json
[2024-09-05 10:30:25] Agent completed successfully
```

#### Key Log Indicators
- `"Starting agent"` - Agent execution began
- `"Loading dependencies"` - Input files being read
- `"Calling LLM"` - Request sent to model
- `"LLM response received"` - Model responded
- `"Output saved"` - Success
- `"ERROR"` - Problem occurred
- `"RETRY"` - Attempting again after failure

### Support Escalation Paths

1. **Level 1: Self-Service**
   - Check this documentation
   - Review log files
   - Try test scripts

2. **Level 2: Configuration Issues**
   - Verify all config files present
   - Check file permissions
   - Validate JSON syntax

3. **Level 3: System Issues**
   - LLM endpoint problems
   - Server resource constraints
   - Code bugs requiring fixes

---

## Configuration Reference

### Main Configuration (`flujo/v3/config.json`)

```json
{
  "version": "v3",                    // Pipeline version identifier
  "max_retries": 2,                   // Max retry attempts per agent
  "pipeline": [                       // Agent execution order
    "01_director_v3",
    "02_escritor_v3", 
    "03_directorarte_v3",
    "04_consolidador_v3"
  ],
  "parallel_execution": false,        // v3 is always sequential
  "parallel_groups": [],              // Not used in v3
  "optimizations": {
    "enable_caching": true,          // Cache LLM responses
    "streaming": false,              // No streaming responses
    "timeout": 900                   // 15-minute timeout
  },
  "mode_verificador_qa": false,      // QA disabled
  "skip_qa": true,                   // Skip QA verification
  "agent_toggles": {                 // Enable/disable agents
    "01_director_v3": true,
    "02_escritor_v3": true,
    "03_directorarte_v3": true,
    "04_consolidador_v3": true
  }
}
```

### Dependencies Configuration (`flujo/v3/dependencies.json`)

```json
{
  "01_director_v3": ["brief.json"],                                        // Only needs initial brief
  "02_escritor_v3": ["01_director_v3.json"],                              // Needs director output
  "03_directorarte_v3": ["01_director_v3.json", "02_escritor_v3.json"],   // Needs structure and text
  "04_consolidador_v3": ["01_director_v3.json", "02_escritor_v3.json", "03_directorarte_v3.json"]  // Needs all
}
```

### Agent Configuration (`flujo/v3/agent_config.json`)

```json
{
  "01_director_v3": {
    "temperature": 0.7,      // Creativity level (0-1)
    "max_tokens": 4000,      // Maximum response length
    "top_p": 0.9,           // Nucleus sampling
    "timeout": 300          // 5-minute timeout
  },
  "02_escritor_v3": {
    "temperature": 0.8,      // Higher for creative writing
    "max_tokens": 3500,
    "top_p": 0.95
  },
  "03_directorarte_v3": {
    "temperature": 0.7,
    "max_tokens": 3500,
    "top_p": 0.9
  },
  "04_consolidador_v3": {
    "temperature": 0.3,      // Lower for structured assembly
    "max_tokens": 8000,      // Larger for complete story
    "top_p": 0.85
  }
}
```

### Customization Options

#### Disabling Specific Agents
```json
// In config.json
"agent_toggles": {
  "03_directorarte_v3": false  // Skip art direction
}
```

#### Adjusting Timeouts
```json
// In config.json
"optimizations": {
  "timeout": 600  // 10 minutes instead of 15
}
```

#### Modifying Temperature
```json
// In agent_config.json
"02_escritor_v3": {
  "temperature": 0.5  // Less creative, more consistent
}
```

---

## Appendix A: Migration from V2 to V3

### Code Changes Required

#### Update Request Payload
```python
# Old (v2)
brief = {
    "story_id": "test",
    "personajes": ["Max"],
    "historia": "...",
    "pipeline_version": "v2"  # or omitted
}

# New (v3)
brief = {
    "story_id": "test",
    "personajes": ["Max"],
    "historia": "...",
    "pipeline_version": "v3"  # Must specify v3
}
```

#### Update Result Parsing
```python
# Old (v2) - 12 separate files
validador = json.load(open("12_validador.json"))

# New (v3) - Single consolidator file
result = json.load(open("04_consolidador_v3.json"))
```

### Performance Expectations

| Metric | V2 Typical | V3 Expected | Notes |
|--------|------------|-------------|-------|
| Total Time | 150-200s | 50-90s | 60-70% reduction |
| Memory Usage | ~500MB | ~200MB | Fewer agents running |
| Disk I/O | ~50MB | ~20MB | Fewer intermediate files |
| LLM Calls | 12-24 | 4 | No retries = exactly 4 |

---

## Appendix B: Extending V3

### Adding a New Agent

1. Create agent definition:
   ```bash
   touch flujo/v3/agentes/05_nuevo_agente.json
   ```

2. Update pipeline in config:
   ```json
   "pipeline": [
     "01_director_v3",
     "02_escritor_v3",
     "03_directorarte_v3",
     "05_nuevo_agente",  // Added
     "04_consolidador_v3"
   ]
   ```

3. Define dependencies:
   ```json
   "05_nuevo_agente": ["03_directorarte_v3.json"]
   ```

4. Add agent config:
   ```json
   "05_nuevo_agente": {
     "temperature": 0.6,
     "max_tokens": 3000
   }
   ```

### Creating a V4 Pipeline

1. Copy v3 as template:
   ```bash
   cp -r flujo/v3 flujo/v4
   ```

2. Modify configuration:
   ```bash
   vim flujo/v4/config.json
   # Change "version": "v3" to "v4"
   ```

3. Update agents as needed

4. Test with:
   ```json
   "pipeline_version": "v4"
   ```

---

## Quick Reference Card

### Essential Commands
```bash
# Start server
python3 src/api_server.py

# Test v3
python3 test_v3_emilia_felipe.py

# Check status
curl http://localhost:5000/api/stories/{story_id}/status

# Get result  
curl http://localhost:5000/api/stories/{story_id}/result

# View logs
tail -f runs/*/logs/*.log
```

### V3 Request Template
```json
{
  "story_id": "unique-id",
  "personajes": ["Name1", "Name2"],
  "historia": "Story plot",
  "edad_objetivo": 5,
  "pipeline_version": "v3"
}
```

### File Locations
- Config: `flujo/v3/config.json`
- Agents: `flujo/v3/agentes/*.json`
- Output: `runs/{timestamp}-{story_id}/`
- Logs: `runs/{timestamp}-{story_id}/logs/`

### Success Indicators
- 4 agents complete
- Total time < 90 seconds
- `04_consolidador_v3.json` exists
- `manifest.json` shows "completado"

---

*Document Version: 1.0*  
*Last Updated: September 2024*  
*System Version: Cuentería v3*