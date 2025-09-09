# Environment Variables Migration Plan

## Problem Statement
The repository currently has hardcoded IP addresses (`69.19.136.204`) and model names (`gpt-oss-120b`) throughout the codebase, making it difficult to deploy on different VMs with different IPs and models (e.g., `gpt-oss-20b`).

## Current State Analysis

### 1. Hardcoded Values Found

#### IP Address (`69.19.136.204`)
- **18 files** contain the hardcoded IP, primarily in:
  - `src/config.py` (line 18): Default fallback value
  - `src/llm_client.py` (line 18): Default fallback value  
  - `src/orchestrator.py` (line 91): Default fallback value
  - Test files: `test_loader_simple.py`, `test_cuentacuentos_debug.py`
  - Documentation files: Various `.md` files

#### Model Name (`gpt-oss-120b`)
- **19 files** contain the hardcoded model name, primarily in:
  - `src/llm_client.py` (line 19): Hardcoded as `self.model = "openai/gpt-oss-120b"`
  - `src/config.py` (line 19): Default fallback value
  - Test files and documentation

### 2. Environment Variable Support

#### Existing Support
- `src/config.py` already uses `os.getenv()` for many values:
  ```python
  "api_url": os.getenv("LLM_API_URL", "http://69.19.136.204:8000/v1/chat/completions")
  "model": os.getenv("LLM_MODEL", "openai/gpt-oss-120b")
  ```
- `python-dotenv` is in `requirements.txt` but NOT being used

#### Inconsistencies
- `.env.example` uses `LLM_ENDPOINT` but code uses `LLM_API_URL`
- `start.sh` exports `LLM_ENDPOINT` but code expects `LLM_API_URL`
- Model name is hardcoded in `llm_client.py` despite config support

### 3. Current .env File
Only contains Supabase key:
```
anon_key=<supabase_key>
```

## Implementation Plan

### Phase 1: Add dotenv Loading

1. **Create initialization module** (`src/__init__.py` or update existing):
   ```python
   from dotenv import load_dotenv
   load_dotenv()
   ```

2. **Update main entry points** to load .env:
   - `src/api_server.py`
   - `src/orchestrator.py`
   - Test files that need environment variables

### Phase 2: Fix Environment Variable Names

1. **Standardize variable names**:
   - Use `LLM_API_URL` (not `LLM_ENDPOINT`)
   - Use `LLM_MODEL` for model name
   
2. **Update files**:
   - `.env.example`: Change `LLM_ENDPOINT` to `LLM_API_URL`
   - `start.sh`: Change `LLM_ENDPOINT` to `LLM_API_URL`

### Phase 3: Remove Hardcoded Values

1. **src/llm_client.py**:
   - Line 19: Change `self.model = "openai/gpt-oss-120b"` to `self.model = LLM_CONFIG["model"]`
   - Line 18: Remove hardcoded fallback from `get()` call

2. **src/config.py**:
   - Line 18: Change default to `""` or raise error if not set
   - Line 19: Change default to `""` or raise error if not set

3. **src/orchestrator.py**:
   - Line 91: Use `LLM_CONFIG["api_url"]` without fallback

4. **Test files**:
   - Import config and use `LLM_CONFIG` values
   - Or load from environment directly

### Phase 4: Create Complete .env Template

Create `.env.template` with all required variables:
```env
# Required LLM Configuration
LLM_API_URL=http://your-ip:8000/v1/chat/completions
LLM_MODEL=openai/gpt-oss-120b

# Optional LLM Configuration  
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=20000
LLM_TIMEOUT=900
LLM_RETRY_ATTEMPTS=3
LLM_RETRY_DELAY=2

# API Configuration
API_HOST=0.0.0.0
API_PORT=5000
API_DEBUG=False
CORS_ORIGINS=https://lacuenteria.cl

# Quality Thresholds
MIN_QA_SCORE=4.0
MAX_RETRIES=2
RETRY_DELAY=5

# Webhook Configuration
WEBHOOK_TIMEOUT=30
WEBHOOK_RETRIES=3
WEBHOOK_RETRY_DELAY=1

# Supabase (if using webhooks)
anon_key=your-supabase-anon-key
```

### Phase 5: Add Validation

1. **Create validation function** in `src/config.py`:
   ```python
   def validate_required_env_vars():
       required = ['LLM_API_URL', 'LLM_MODEL']
       missing = [var for var in required if not os.getenv(var)]
       if missing:
           raise ValueError(f"Missing required environment variables: {missing}")
   ```

2. **Call validation** on startup in:
   - `src/api_server.py`
   - Any standalone scripts

### Phase 6: Update Documentation

1. Update `README.md` with environment setup instructions
2. Update deployment documentation
3. Add migration guide for existing deployments

## Files to Modify

### Critical Code Files (Must Change)
1. `src/llm_client.py` - Fix hardcoded model name
2. `src/config.py` - Remove hardcoded defaults
3. `src/orchestrator.py` - Remove hardcoded fallback
4. `src/api_server.py` - Add dotenv loading
5. `.env.example` - Fix variable names
6. `start.sh` - Fix exported variable names

### Test Files (Should Change)
1. `test_loader_simple.py`
2. `test_cuentacuentos_debug.py`
3. `test_direct_llm_evaluation.sh`
4. Other test files with hardcoded values

### Documentation (Nice to Have)
- Update all `.md` files to use placeholder values instead of specific IPs

## Migration Steps for New VM

1. **Clone repository** on new VM
2. **Copy `.env.template` to `.env`**
3. **Edit `.env`** with your specific values:
   ```bash
   LLM_API_URL=http://your-new-ip:8000/v1/chat/completions
   LLM_MODEL=openai/gpt-oss-20b  # or your model
   ```
4. **Install dependencies**: `pip install -r requirements.txt`
5. **Start server**: `python3 src/api_server.py`

## Testing Plan

1. **Unit Tests**:
   - Test config loading with different .env values
   - Test validation with missing variables

2. **Integration Tests**:
   - Test with different model endpoints
   - Test with different model names

3. **Deployment Test**:
   - Deploy on VM with gpt-oss-20b
   - Verify all components work with new configuration

## Rollback Plan

If issues arise:
1. Keep backup of original files
2. Can temporarily hardcode values in .env while fixing
3. Use environment variable overrides: `LLM_API_URL=http://... python3 src/api_server.py`

## Benefits

1. **Portability**: Easy deployment on different VMs
2. **Security**: No hardcoded IPs in repository
3. **Flexibility**: Support different models (gpt-oss-20b, gpt-oss-120b, etc.)
4. **Configuration Management**: All config in one place (.env)
5. **Multi-environment**: Dev, staging, production with different configs

## Estimated Effort

- **Code changes**: 2-3 hours
- **Testing**: 1-2 hours
- **Documentation**: 1 hour
- **Total**: 4-6 hours

## Risk Assessment

- **Low Risk**: Changes are mostly configuration-related
- **Main Risk**: Breaking existing deployments - mitigated by keeping defaults initially
- **Testing Required**: Thorough testing on both old and new environments