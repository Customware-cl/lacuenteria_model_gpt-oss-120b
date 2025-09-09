# Cuentería v3 - Story Generation Brief

## Executive Summary

Cuentería v3 is a streamlined AI-powered story generation pipeline that creates personalized children's stories in 60-90 seconds using only 4 specialized agents, compared to 12 agents in v2.

## Required Input Brief

To generate a story using v3, provide the following JSON structure:

```json
{
  "story_id": "unique-identifier",
  "personajes": ["Character1", "Character2"],
  "historia": "Main plot or story premise",
  "mensaje_a_transmitir": "Educational message (optional)",
  "edad_objetivo": 5,
  "pipeline_version": "v3"
}
```

### Brief Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `story_id` | string | Yes | Unique identifier for the story |
| `personajes` | array | Yes | List of main characters (1-3 recommended) |
| `historia` | string | Yes | Core narrative or plot (50-200 words) |
| `mensaje_a_transmitir` | string | Optional | Educational/behavioral goal |
| `edad_objetivo` | integer | Yes | Target age (3-8 years) |
| `pipeline_version` | string | Yes | Must be "v3" for optimized flow |

## v3 Pipeline Architecture

### Agent Flow (4 Steps)

```mermaid
graph LR
    A[Director v3] --> B[Escritor v3]
    B --> C[Director Arte v3]
    C --> D[Consolidador v3]
```

1. **Director v3** (30s)
   - Creates narrative structure
   - Integrates psychoeducational elements
   - Establishes character continuity
   - Output: Complete beat sheet with emotional arc

2. **Escritor v3** (20s)
   - Writes complete story in verses
   - Ensures clarity and rhythm
   - Maintains age-appropriate language
   - Output: 10 pages of lyrical text

3. **Director Arte v3** (20s)
   - Designs visual scenes
   - Creates art direction
   - Ensures cultural sensitivity
   - Output: Visual prompts for each page

4. **Consolidador v3** (20s)
   - Assembles final JSON
   - Generates title and cover
   - Creates loader messages
   - Output: Complete story package

## Quick Start

### 1. Start the Server

```bash
cd /home/ubuntu/cuenteria
python3 src/api_server.py
```

### 2. Send a Story Request

```bash
curl -X POST http://localhost:5000/api/stories/create \
  -H "Content-Type: application/json" \
  -d '{
    "story_id": "test-001",
    "personajes": ["Luna the Cat", "Sol the Bird"],
    "historia": "Luna and Sol discover that despite their differences, they can be best friends by helping each other reach their dreams",
    "mensaje_a_transmitir": "Friendship transcends differences",
    "edad_objetivo": 5,
    "pipeline_version": "v3"
  }'
```

### 3. Check Status

```bash
curl http://localhost:5000/api/stories/test-001/status
```

### 4. Get Result

```bash
curl http://localhost:5000/api/stories/test-001/result
```

## Output Structure

The v3 pipeline generates a JSON with:

```json
{
  "titulo": "Story Title",
  "paginas": {
    "1": {
      "texto": "Page 1 verses (4-5 lines)",
      "prompt": "Detailed visual description"
    },
    ...
    "10": { ... }
  },
  "portada": {
    "prompt": "Cover visual description"
  },
  "loader": [
    "Loading message 1",
    ...
    "Loading message 10"
  ]
}
```

## Performance Metrics

| Metric | v2 (Classic) | v3 (Optimized) | Improvement |
|--------|--------------|----------------|-------------|
| Total Time | 180 seconds | 60-90 seconds | 67% faster |
| Agent Count | 12 agents | 4 agents | 67% reduction |
| LLM Calls | 12+ calls | 4 calls | 67% fewer |
| QA Verification | Required | Not needed | Eliminated |
| Token Usage | ~48,000 | ~16,000 | 67% less |

## Key Features

### Multilingual Support
- Automatic language detection
- Native support for Spanish, English, Portuguese
- Consistent quality across languages

### Integrated Quality
- No separate QA verification needed
- Quality criteria built into prompts
- Consistent output format

### Psychoeducational Elements
- Age-appropriate behavioral goals
- Emotional regulation techniques
- Natural integration without preaching

## API Endpoints

### Create Story
```
POST /api/stories/create
```

### Check Status
```
GET /api/stories/{story_id}/status
```

### Get Result
```
GET /api/stories/{story_id}/result
```

### View Logs
```
GET /api/stories/{story_id}/logs
```

## Testing Scripts

```bash
# Run v3 test with predefined story
python3 test_v3_emilia_felipe.py

# Run custom v3 test
python3 test_v3_custom.py --characters "Dragon,Knight" --plot "Learning courage"
```

## Configuration Files

```
flujo/v3/
├── config.json           # Main v3 configuration
├── dependencies.json     # Agent dependencies
├── agent_config.json     # Per-agent settings
└── agentes/             # Agent prompts
    ├── 01_director_v3.json
    ├── 02_escritor_v3.json
    ├── 03_directorarte_v3.json
    └── 04_consolidador_v3.json
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Version v3 not found" | Ensure `"pipeline_version": "v3"` in request |
| Slow generation | Check LLM endpoint connectivity |
| Missing output | Verify all 4 v3 agents are present |
| Server errors | Restart with `pkill -f api_server.py && python3 src/api_server.py` |

## Best Practices

1. **Character Count**: Use 2-3 characters for optimal narrative focus
2. **Plot Length**: Keep historia between 50-200 words
3. **Age Targeting**: Ages 4-6 produce best results
4. **Language**: System auto-detects, but consistent language in brief helps
5. **Educational Goals**: Optional but enhances story depth when included

## Support

- Documentation: `/home/ubuntu/cuenteria/docs/`
- Logs: `/home/ubuntu/cuenteria/runs/{story_id}/logs/`
- Issues: Check `V3_TROUBLESHOOTING_GUIDE.md`