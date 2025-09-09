# V3 Pipeline Troubleshooting Guide

## Table of Contents
1. [Pre-Flight Checklist](#pre-flight-checklist)
2. [Common Error Messages](#common-error-messages)
3. [Diagnostic Procedures](#diagnostic-procedures)
4. [Agent-Specific Issues](#agent-specific-issues)
5. [Performance Problems](#performance-problems)
6. [Recovery Procedures](#recovery-procedures)
7. [Log Analysis Guide](#log-analysis-guide)
8. [Emergency Fixes](#emergency-fixes)

---

## Pre-Flight Checklist

Before troubleshooting, verify these basics:

### System Requirements
```bash
# Check Python version (must be 3.8+)
python3 --version

# Check available disk space (need 2GB minimum)
df -h /home/ubuntu/cuenteria/runs

# Check memory availability (need 1GB minimum)
free -h

# Verify network connectivity to LLM
ping -c 1 69.19.136.204
curl -s http://69.19.136.204:8000/v1/models | head -n 1
```

### File Permissions
```bash
# Check write permissions
touch /home/ubuntu/cuenteria/runs/test.txt && rm /home/ubuntu/cuenteria/runs/test.txt
# If fails: sudo chmod -R 755 /home/ubuntu/cuenteria/runs

# Check read permissions for config
ls -la /home/ubuntu/cuenteria/flujo/v3/config.json
# If fails: sudo chmod 644 /home/ubuntu/cuenteria/flujo/v3/*.json
```

### Configuration Integrity
```bash
# Validate JSON syntax
python3 -m json.tool /home/ubuntu/cuenteria/flujo/v3/config.json > /dev/null
echo "Config JSON: $?"  # Should output 0

# Check all required files exist
for file in config.json dependencies.json agent_config.json; do
  [ -f "/home/ubuntu/cuenteria/flujo/v3/$file" ] && echo "✓ $file" || echo "✗ $file MISSING"
done

# Verify all 4 agents present
ls /home/ubuntu/cuenteria/flujo/v3/agentes/*.json | wc -l
# Should output: 4
```

---

## Common Error Messages

### Error: "No se encontró configuración para versión v3"

**Symptom**: Server rejects v3 pipeline requests

**Root Causes**:
1. Missing v3 configuration directory
2. Corrupted config files
3. Server using old code

**Solution**:
```bash
# Step 1: Verify v3 directory exists
ls -la /home/ubuntu/cuenteria/flujo/v3/
# If missing, restore from git:
git checkout -- flujo/v3/

# Step 2: Restart server with fresh code
pkill -f api_server.py
cd /home/ubuntu/cuenteria
python3 src/api_server.py

# Step 3: Test with simple request
curl -X POST http://localhost:5000/api/stories/create \
  -H "Content-Type: application/json" \
  -d '{"story_id":"test-v3-config","personajes":["Test"],"historia":"Test","edad_objetivo":5,"pipeline_version":"v3"}'
```

### Error: "Agent 01_director_v3 not found"

**Symptom**: Pipeline fails at first agent

**Root Causes**:
1. Missing agent definition file
2. Incorrect file naming
3. Permission issues

**Solution**:
```bash
# Step 1: Check exact filename
ls -la /home/ubuntu/cuenteria/flujo/v3/agentes/01_director_v3.json

# Step 2: If missing, check for typos
ls /home/ubuntu/cuenteria/flujo/v3/agentes/

# Step 3: Restore if deleted
git status flujo/v3/agentes/
git checkout -- flujo/v3/agentes/01_director_v3.json

# Step 4: Verify content is valid JSON
python3 -c "import json; json.load(open('/home/ubuntu/cuenteria/flujo/v3/agentes/01_director_v3.json'))"
```

### Error: "JSONDecodeError: Expecting value"

**Symptom**: Agent output cannot be parsed

**Root Causes**:
1. LLM response truncated
2. Invalid JSON in response
3. Encoding issues

**Solution**:
```bash
# Step 1: Identify which agent failed
grep -l "JSONDecodeError" runs/*/logs/*.log | tail -1

# Step 2: Check the problematic output
STORY_ID="your-story-id"
AGENT="02_escritor_v3"  # Example
cat runs/*${STORY_ID}*/${AGENT}.json | python3 -m json.tool

# Step 3: If truncated, check token limits
grep "max_tokens" /home/ubuntu/cuenteria/flujo/v3/agent_config.json

# Step 4: Increase token limit for problematic agent
python3 -c "
import json
config = json.load(open('/home/ubuntu/cuenteria/flujo/v3/agent_config.json'))
config['${AGENT}']['max_tokens'] = 5000  # Increase
json.dump(config, open('/home/ubuntu/cuenteria/flujo/v3/agent_config.json', 'w'), indent=2)
"

# Step 5: Retry the story
curl -X POST http://localhost:5000/api/stories/${STORY_ID}/retry
```

### Error: "Connection timeout after 900 seconds"

**Symptom**: LLM request times out

**Root Causes**:
1. Network issues
2. LLM server overloaded
3. Request too complex

**Solution**:
```bash
# Step 1: Test LLM connectivity
time curl -X POST http://69.19.136.204:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-oss-120b","messages":[{"role":"user","content":"Hi"}],"max_tokens":10}'

# Step 2: If slow, reduce complexity
# Simplify story brief - fewer characters, simpler plot

# Step 3: Increase timeout (if network is slow but working)
sed -i 's/"timeout": 900/"timeout": 1200/' /home/ubuntu/cuenteria/flujo/v3/config.json

# Step 4: Restart and retry
pkill -f api_server.py && python3 src/api_server.py
```

---

## Diagnostic Procedures

### Complete System Health Check

Create and run `diagnose_v3.py`:
```python
#!/usr/bin/env python3
"""Complete V3 System Diagnostic"""

import os
import json
import requests
import subprocess
from pathlib import Path

def check_status(name, command):
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=5)
        success = result.returncode == 0
        print(f"{'✓' if success else '✗'} {name}")
        if not success and result.stderr:
            print(f"  Error: {result.stderr[:100]}")
        return success
    except Exception as e:
        print(f"✗ {name}: {str(e)[:100]}")
        return False

print("=" * 50)
print("V3 PIPELINE DIAGNOSTIC")
print("=" * 50)

# Check Python version
import sys
py_version = sys.version_info
print(f"{'✓' if py_version >= (3, 8) else '✗'} Python {py_version.major}.{py_version.minor}.{py_version.micro}")

# Check API server
try:
    response = requests.get("http://localhost:5000/health", timeout=2)
    api_running = response.status_code == 200
    print(f"{'✓' if api_running else '✗'} API Server")
    if api_running:
        health = response.json()
        print(f"  LLM Status: {health.get('llm_status', 'unknown')}")
except:
    print("✗ API Server (not running)")
    api_running = False

# Check LLM endpoint
check_status("LLM Endpoint", "curl -s http://69.19.136.204:8000/v1/models | grep -q model")

# Check v3 configuration files
v3_path = Path("/home/ubuntu/cuenteria/flujo/v3")
config_files = ["config.json", "dependencies.json", "agent_config.json"]
for file in config_files:
    file_path = v3_path / file
    if file_path.exists():
        try:
            with open(file_path) as f:
                json.load(f)
            print(f"✓ {file} (valid JSON)")
        except json.JSONDecodeError:
            print(f"✗ {file} (invalid JSON)")
    else:
        print(f"✗ {file} (missing)")

# Check v3 agents
agents_path = v3_path / "agentes"
expected_agents = ["01_director_v3.json", "02_escritor_v3.json", 
                   "03_directorarte_v3.json", "04_consolidador_v3.json"]
for agent in expected_agents:
    agent_path = agents_path / agent
    if agent_path.exists():
        print(f"✓ Agent: {agent}")
    else:
        print(f"✗ Agent: {agent} (missing)")

# Check disk space
stat = os.statvfs("/home/ubuntu/cuenteria/runs")
free_gb = (stat.f_bavail * stat.f_bsize) / (1024**3)
print(f"{'✓' if free_gb > 1 else '✗'} Disk Space: {free_gb:.1f}GB free")

# Check recent runs
runs_dir = Path("/home/ubuntu/cuenteria/runs")
recent_runs = sorted(runs_dir.glob("*v3*"), key=lambda p: p.stat().st_mtime, reverse=True)[:3]
if recent_runs:
    print(f"\nRecent v3 runs:")
    for run in recent_runs:
        manifest_path = run / "manifest.json"
        if manifest_path.exists():
            with open(manifest_path) as f:
                manifest = json.load(f)
                status = manifest.get("estado", "unknown")
                print(f"  {run.name}: {status}")

print("\n" + "=" * 50)
print("DIAGNOSTIC COMPLETE")
print("=" * 50)
```

Run with:
```bash
python3 diagnose_v3.py
```

### Tracing a Failed Story

```bash
#!/bin/bash
# trace_story.sh - Trace what happened to a story

STORY_ID=$1
if [ -z "$STORY_ID" ]; then
    echo "Usage: ./trace_story.sh <story_id>"
    exit 1
fi

echo "Tracing story: $STORY_ID"
echo "=" 

# Find story directory
STORY_DIR=$(find /home/ubuntu/cuenteria/runs -name "*${STORY_ID}*" -type d | head -1)

if [ -z "$STORY_DIR" ]; then
    echo "Story directory not found"
    exit 1
fi

echo "Directory: $STORY_DIR"
echo

# Check manifest
if [ -f "$STORY_DIR/manifest.json" ]; then
    echo "Manifest Status:"
    python3 -c "import json; m=json.load(open('$STORY_DIR/manifest.json')); print(f\"  State: {m.get('estado')}\"); print(f\"  Last Agent: {m.get('paso_actual')}\"); print(f\"  Error: {m.get('error', {}).get('message', 'None')}\")"
    echo
fi

# Check which agents completed
echo "Agents Completed:"
for agent in 01_director_v3 02_escritor_v3 03_directorarte_v3 04_consolidador_v3; do
    if [ -f "$STORY_DIR/${agent}.json" ]; then
        SIZE=$(stat -c%s "$STORY_DIR/${agent}.json" 2>/dev/null || stat -f%z "$STORY_DIR/${agent}.json" 2>/dev/null)
        echo "  ✓ $agent (${SIZE} bytes)"
    else
        echo "  ✗ $agent (not found)"
    fi
done
echo

# Check for errors in logs
echo "Errors in Logs:"
grep -l ERROR "$STORY_DIR/logs/"*.log 2>/dev/null | while read log; do
    echo "  $(basename $log):"
    grep ERROR "$log" | head -2 | sed 's/^/    /'
done

# Check last lines of most recent log
LAST_LOG=$(ls -t "$STORY_DIR/logs/"*.log 2>/dev/null | head -1)
if [ -f "$LAST_LOG" ]; then
    echo
    echo "Last Log Entry ($(basename $LAST_LOG)):"
    tail -3 "$LAST_LOG" | sed 's/^/  /'
fi
```

---

## Agent-Specific Issues

### 01_director_v3 Issues

**Problem**: Director generates structure in wrong language

**Diagnosis**:
```bash
# Check detected language
cat runs/*/01_director_v3.json | grep -o '"idioma":[^,]*' | head -1
```

**Solution**:
```python
# Force language in brief
brief = {
    "historia": "Story in desired language here",
    # Director auto-detects from historia field
}
```

**Problem**: Missing pedagogical elements

**Diagnosis**:
```bash
# Check if triada_eer exists
cat runs/*/01_director_v3.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
for p in data.get('paginas', []):
    if 'triada_eer' not in p:
        print(f'Page {p[\"numero\"]} missing triada_eer')
"
```

**Solution**: Update prompt temperature for more comprehensive output
```bash
# Increase temperature for more creative/complete responses
sed -i 's/"temperature": 0.7/"temperature": 0.8/' flujo/v3/agent_config.json
```

### 02_escritor_v3 Issues

**Problem**: Text not in verse format

**Diagnosis**:
```bash
# Check text structure
cat runs/*/02_escritor_v3.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
for num, page in data.get('paginas', {}).items():
    text = page.get('texto', '')
    if '\\n' not in text:
        print(f'Page {num}: No line breaks (not in verse)')
"
```

**Solution**: Ensure director output emphasizes verse requirement
```bash
# Check director instructions
cat runs/*/01_director_v3.json | grep -i "verso\|verse\|rima\|rhyme"
```

### 03_directorarte_v3 Issues

**Problem**: Inconsistent character descriptions

**Diagnosis**:
```bash
# Extract character descriptions across pages
cat runs/*/03_directorarte_v3.json | python3 -c "
import json, sys, re
data = json.load(sys.stdin)
characters = set()
for num, page in data.get('paginas', {}).items():
    prompt = page.get('prompt_ilustracion', '')
    # Extract character mentions
    names = re.findall(r'[A-Z][a-z]+', prompt)
    characters.update(names)
print('Characters mentioned:', characters)
"
```

**Solution**: Ensure character continuity from director
```bash
# Verify character descriptions in director
cat runs/*/01_director_v3.json | grep -A5 '"personajes"'
```

### 04_consolidador_v3 Issues

**Problem**: Missing or incomplete final output

**Diagnosis**:
```bash
# Check output size and structure
STORY_DIR="runs/*your-story*"
if [ -f "$STORY_DIR/04_consolidador_v3.json" ]; then
    python3 -c "
import json
data = json.load(open('$STORY_DIR/04_consolidador_v3.json'))
print(f'Title: {bool(data.get(\"titulo\"))}')
print(f'Cover: {bool(data.get(\"portada\"))}')
print(f'Pages: {len(data.get(\"paginas\", {}))}')
print(f'Loader: {len(data.get(\"loader\", []))}')
"
fi
```

**Solution**: Increase token limit for consolidador
```python
import json
config = json.load(open('flujo/v3/agent_config.json'))
config['04_consolidador_v3']['max_tokens'] = 10000  # Increase from 8000
json.dump(config, open('flujo/v3/agent_config.json', 'w'), indent=2)
```

---

## Performance Problems

### Slow Generation (>90 seconds)

**Diagnosis Script**:
```python
#!/usr/bin/env python3
# performance_check.py
import json
from pathlib import Path
from datetime import datetime

def analyze_performance(story_id):
    # Find story directory
    runs_dir = Path("/home/ubuntu/cuenteria/runs")
    story_dirs = list(runs_dir.glob(f"*{story_id}*"))
    
    if not story_dirs:
        print(f"Story {story_id} not found")
        return
    
    story_dir = story_dirs[0]
    manifest_path = story_dir / "manifest.json"
    
    if not manifest_path.exists():
        print("No manifest found")
        return
    
    with open(manifest_path) as f:
        manifest = json.load(f)
    
    print(f"Story: {story_id}")
    print(f"Status: {manifest.get('estado')}")
    print("\nAgent Performance:")
    print("-" * 40)
    
    timestamps = manifest.get("timestamps", {})
    total_time = 0
    
    for agent, times in timestamps.items():
        duration = times.get("duration", 0)
        total_time += duration
        
        # Flag slow agents (>30s)
        flag = "⚠️ SLOW" if duration > 30 else "✓"
        print(f"{agent:20} {duration:6.1f}s {flag}")
    
    print("-" * 40)
    print(f"{'Total:':20} {total_time:6.1f}s")
    
    # Recommendations
    print("\nRecommendations:")
    if total_time > 90:
        print("- Consider reducing story complexity")
        print("- Check LLM endpoint latency")
        print("- Review token limits in agent_config.json")
    
    # Check retries
    retries = manifest.get("reintentos", {})
    if retries:
        print("\nRetries detected:")
        for agent, count in retries.items():
            print(f"  {agent}: {count} retries")

# Usage
if __name__ == "__main__":
    import sys
    story_id = sys.argv[1] if len(sys.argv) > 1 else input("Enter story ID: ")
    analyze_performance(story_id)
```

**Optimization Steps**:

1. **Reduce Token Limits** (faster but may truncate):
```bash
# Conservative token limits for speed
cat > /tmp/fast_config.json << 'EOF'
{
  "01_director_v3": {"max_tokens": 3000},
  "02_escritor_v3": {"max_tokens": 2500},
  "03_directorarte_v3": {"max_tokens": 2500},
  "04_consolidador_v3": {"max_tokens": 6000}
}
EOF

# Apply (backup first!)
cp flujo/v3/agent_config.json flujo/v3/agent_config.json.bak
python3 -c "
import json
current = json.load(open('flujo/v3/agent_config.json'))
fast = json.load(open('/tmp/fast_config.json'))
for agent, settings in fast.items():
    current[agent].update(settings)
json.dump(current, open('flujo/v3/agent_config.json', 'w'), indent=2)
"
```

2. **Simplify Input**:
```python
# Simpler brief = faster processing
brief = {
    "personajes": ["Max", "Luna"],  # Just 2 characters
    "historia": "Simple adventure story",  # Brief description
    "edad_objetivo": 4,  # Middle age range
    "pipeline_version": "v3"
    # Omit valores, mensaje_a_transmitir for speed
}
```

### Memory Issues

**Check Memory Usage**:
```bash
# Monitor memory during generation
watch -n 1 'ps aux | grep -E "python3|api_server" | grep -v grep'

# Check system memory
free -h

# If low on memory, restart server
pkill -f api_server.py
sleep 2
python3 src/api_server.py
```

**Reduce Memory Footprint**:
```python
# In src/api_server.py, add before starting:
import gc
gc.collect()  # Force garbage collection

# Limit concurrent requests
MAX_CONCURRENT = 1  # Process one story at a time
```

---

## Recovery Procedures

### Resuming a Failed Story

**Automatic Resume**:
```bash
# Resume from last successful agent
curl -X POST http://localhost:5000/api/stories/{story_id}/retry
```

**Manual Resume** (if automatic fails):
```python
#!/usr/bin/env python3
# manual_resume.py
import json
import shutil
from pathlib import Path
from datetime import datetime

def manual_resume(story_id):
    # Find story directory
    runs_dir = Path("/home/ubuntu/cuenteria/runs")
    story_dirs = list(runs_dir.glob(f"*{story_id}*"))
    
    if not story_dirs:
        print(f"Story {story_id} not found")
        return
    
    story_dir = story_dirs[0]
    
    # Determine last successful agent
    agents = ["01_director_v3", "02_escritor_v3", "03_directorarte_v3", "04_consolidador_v3"]
    last_successful = None
    
    for agent in agents:
        if (story_dir / f"{agent}.json").exists():
            last_successful = agent
        else:
            break
    
    if not last_successful:
        print("No successful agents found")
        return
    
    print(f"Last successful: {last_successful}")
    
    # Create resume request
    next_agent_idx = agents.index(last_successful) + 1
    if next_agent_idx >= len(agents):
        print("Story already complete")
        return
    
    next_agent = agents[next_agent_idx]
    print(f"Resuming from: {next_agent}")
    
    # Update manifest
    manifest_path = story_dir / "manifest.json"
    with open(manifest_path) as f:
        manifest = json.load(f)
    
    manifest["estado"] = "resuming"
    manifest["paso_actual"] = next_agent
    manifest["updated_at"] = datetime.now().isoformat()
    
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    
    print(f"Manifest updated. Run: curl -X POST http://localhost:5000/api/stories/{story_id}/retry")

# Usage
if __name__ == "__main__":
    import sys
    story_id = sys.argv[1] if len(sys.argv) > 1 else input("Enter story ID: ")
    manual_resume(story_id)
```

### Cleaning Up Failed Runs

```bash
#!/bin/bash
# cleanup_failed.sh - Remove failed v3 runs older than 24 hours

echo "Finding failed v3 runs older than 24 hours..."

find /home/ubuntu/cuenteria/runs -name "*v3*" -type d -mtime +1 | while read dir; do
    if [ -f "$dir/manifest.json" ]; then
        STATUS=$(python3 -c "import json; print(json.load(open('$dir/manifest.json')).get('estado', ''))" 2>/dev/null)
        if [ "$STATUS" = "error" ] || [ "$STATUS" = "qa_failed" ]; then
            echo "Removing failed run: $(basename $dir)"
            rm -rf "$dir"
        fi
    fi
done

echo "Cleanup complete"
```

### Backing Up Successful Stories

```bash
#!/bin/bash
# backup_successful.sh - Archive successful v3 stories

BACKUP_DIR="/home/ubuntu/cuenteria/backups/v3_stories"
mkdir -p "$BACKUP_DIR"

find /home/ubuntu/cuenteria/runs -name "*v3*" -type d | while read dir; do
    if [ -f "$dir/manifest.json" ]; then
        STATUS=$(python3 -c "import json; print(json.load(open('$dir/manifest.json')).get('estado', ''))" 2>/dev/null)
        if [ "$STATUS" = "completado" ] || [ "$STATUS" = "completed" ]; then
            STORY_NAME=$(basename "$dir")
            if [ ! -f "$BACKUP_DIR/${STORY_NAME}.tar.gz" ]; then
                echo "Backing up: $STORY_NAME"
                tar -czf "$BACKUP_DIR/${STORY_NAME}.tar.gz" -C "$(dirname $dir)" "$STORY_NAME"
            fi
        fi
    fi
done

echo "Backup complete. Files in: $BACKUP_DIR"
ls -lh "$BACKUP_DIR" | tail -5
```

---

## Log Analysis Guide

### Understanding Log Entries

**Log Format**:
```
[TIMESTAMP] LEVEL - MESSAGE
[2024-09-05 10:30:15] INFO - Starting agent: 01_director_v3
[2024-09-05 10:30:16] DEBUG - Temperature: 0.7, Max tokens: 4000
[2024-09-05 10:30:25] INFO - LLM response: 3456 tokens
[2024-09-05 10:30:25] INFO - Output saved successfully
```

### Common Log Patterns

**Successful Execution**:
```bash
grep -E "Starting agent|completed successfully" runs/*/logs/*.log
```

**Timeout Issues**:
```bash
grep -i "timeout\|timed out" runs/*/logs/*.log
```

**JSON Errors**:
```bash
grep -E "JSONDecodeError|Expecting value|Invalid JSON" runs/*/logs/*.log
```

**Retries**:
```bash
grep -i "retry\|retrying\|attempt" runs/*/logs/*.log
```

### Log Analysis Script

```python
#!/usr/bin/env python3
# analyze_logs.py - Comprehensive log analysis

import re
import sys
from pathlib import Path
from collections import defaultdict

def analyze_story_logs(story_id):
    runs_dir = Path("/home/ubuntu/cuenteria/runs")
    story_dirs = list(runs_dir.glob(f"*{story_id}*"))
    
    if not story_dirs:
        print(f"Story {story_id} not found")
        return
    
    logs_dir = story_dirs[0] / "logs"
    if not logs_dir.exists():
        print("No logs directory found")
        return
    
    stats = defaultdict(lambda: {
        "errors": [],
        "warnings": [],
        "duration": 0,
        "tokens": 0,
        "retries": 0
    })
    
    for log_file in logs_dir.glob("*.log"):
        agent = log_file.stem
        
        with open(log_file) as f:
            content = f.read()
            
            # Count errors
            stats[agent]["errors"] = re.findall(r'ERROR.*', content)
            
            # Count warnings  
            stats[agent]["warnings"] = re.findall(r'WARNING.*', content)
            
            # Find duration
            duration_match = re.search(r'duration["\s:]+(\d+\.?\d*)', content, re.I)
            if duration_match:
                stats[agent]["duration"] = float(duration_match.group(1))
            
            # Find token count
            token_match = re.search(r'(\d+)\s+tokens', content, re.I)
            if token_match:
                stats[agent]["tokens"] = int(token_match.group(1))
            
            # Count retries
            stats[agent]["retries"] = len(re.findall(r'retry|attempt \d+', content, re.I))
    
    # Print report
    print(f"\nLog Analysis for: {story_id}")
    print("=" * 60)
    
    for agent in ["01_director_v3", "02_escritor_v3", "03_directorarte_v3", "04_consolidador_v3"]:
        if agent in stats:
            s = stats[agent]
            print(f"\n{agent}:")
            print(f"  Duration: {s['duration']:.1f}s")
            print(f"  Tokens: {s['tokens']}")
            print(f"  Errors: {len(s['errors'])}")
            print(f"  Warnings: {len(s['warnings'])}")
            print(f"  Retries: {s['retries']}")
            
            if s['errors']:
                print(f"  First error: {s['errors'][0][:80]}...")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    story_id = sys.argv[1] if len(sys.argv) > 1 else input("Enter story ID: ")
    analyze_story_logs(story_id)
```

---

## Emergency Fixes

### Server Won't Start

```bash
#!/bin/bash
# emergency_restart.sh

echo "Performing emergency restart..."

# Kill any hanging processes
pkill -9 -f api_server.py
pkill -9 -f python3

# Clear any lock files
rm -f /tmp/*.lock

# Check port availability
if lsof -i :5000 > /dev/null; then
    echo "Port 5000 still in use, killing process..."
    kill -9 $(lsof -t -i :5000)
fi

# Clear Python cache
find /home/ubuntu/cuenteria -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null

# Restart with minimal logging
cd /home/ubuntu/cuenteria
nohup python3 src/api_server.py > api_server.log 2>&1 &

sleep 3

# Verify it started
if curl -s http://localhost:5000/health > /dev/null; then
    echo "✓ Server restarted successfully"
else
    echo "✗ Server failed to start. Check api_server.log"
fi
```

### Corrupted Configuration

```bash
#!/bin/bash
# restore_v3_config.sh

echo "Restoring v3 configuration from git..."

cd /home/ubuntu/cuenteria

# Backup current (possibly corrupted) config
cp -r flujo/v3 flujo/v3.backup.$(date +%s)

# Restore from git
git checkout -- flujo/v3/

# Verify restoration
python3 -c "
import json
try:
    json.load(open('flujo/v3/config.json'))
    json.load(open('flujo/v3/dependencies.json'))
    json.load(open('flujo/v3/agent_config.json'))
    print('✓ Configuration restored successfully')
except Exception as e:
    print(f'✗ Configuration still corrupted: {e}')
"
```

### Complete Reset

```bash
#!/bin/bash
# factory_reset_v3.sh

echo "WARNING: This will reset v3 to factory settings"
read -p "Continue? (y/n) " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    cd /home/ubuntu/cuenteria
    
    # Stop server
    pkill -f api_server.py
    
    # Backup current state
    tar -czf v3_backup_$(date +%Y%m%d_%H%M%S).tar.gz flujo/v3 runs/*v3*
    
    # Reset configuration
    git checkout -- flujo/v3/
    
    # Clear test runs
    rm -rf runs/*test*v3*
    
    # Restart server
    python3 src/api_server.py &
    
    echo "Reset complete. Test with:"
    echo "python3 test_v3_emilia_felipe.py"
fi
```

---

## Quick Reference - Emergency Commands

```bash
# Check if server is running
ps aux | grep api_server

# Kill server
pkill -f api_server.py

# Start server
python3 src/api_server.py

# Test health
curl http://localhost:5000/health

# Quick v3 test
curl -X POST http://localhost:5000/api/stories/create \
  -H "Content-Type: application/json" \
  -d '{"story_id":"quick-test","personajes":["A"],"historia":"Test","edad_objetivo":5,"pipeline_version":"v3"}'

# Check last error
find runs -name "*.log" -exec grep -l ERROR {} \; | xargs tail -n 20

# Clear old runs
find runs -name "*test*" -mtime +7 -exec rm -rf {} \;

# Validate all JSON configs
for f in flujo/v3/*.json flujo/v3/agentes/*.json; do
  python3 -m json.tool "$f" > /dev/null && echo "✓ $f" || echo "✗ $f"
done
```

---

*Troubleshooting Guide v1.0 - September 2024*