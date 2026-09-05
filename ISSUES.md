# Qicdock Marketing Calendar - Current Issues (Aug 29, 2026)

## Summary
The backend server starts successfully but becomes unreachable immediately after startup. The uvicorn process appears to run but the HTTP endpoint is not accessible.

## What Works
- Database initialization (SQLite)
- ChromaDB connection
- Knowledge base ingestion (brand story + 10 products)
- Queue worker startup
- All imports and code structure

## What Fails
- **HTTP server not accessible** - uvicorn logs "Uvicorn running on http://0.0.0.0:8000" but `requests.get('http://localhost:8000/api/health')` returns connection refused
- Process appears to hang after startup - no logs after "Application startup complete"

## Key Technical Changes Made Today

### LLM Provider Architecture
1. **Switched to Groq (OpenAI-compatible)** - Using `openai/gpt-oss-120b` model via Groq API
2. **Removed fallback providers** - Simplified to single Groq provider with retry logic
3. **Fixed API key configuration** - Using `GROQ_API_KEY` in .env

### Configuration Updates
- `.env` uses `GROQ_API_KEY` and `GROQ_MODEL` 
- `config.py` reads these settings
- `llm_provider.py` uses OpenAI client with Groq base_url

### Schema Fixes
- Added `PRODUCT_INSIGHT` to `ContentType` enum
- Added `follows_entry` and `supports_entry` to `CalendarEntryPlan` model

## Suspected Root Causes

1. **Blocking operation in lifespan** - The `init_db()` or knowledge base ingestion might be blocking the event loop
2. **Threading issue with queue worker** - Local queue uses threading which may conflict with uvicorn
3. **httpx version conflict** - ChromaDB requires httpx>=0.27 but OpenAI client had issues with newer versions
4. **Port binding issue** - Server binds but doesn't accept connections

## Next Steps for Tomorrow

1. **Debug server binding**:
   ```python
   # Add to main.py to debug
   import socket
   s = socket.socket()
   s.bind(('0.0.0.0', 8000))
   print("Port 8000 bindable")
   ```

2. **Check if queue worker blocks** - Comment out `queue.start()` temporarily

3. **Run without reload** - Use `uvicorn.run()` directly instead of CLI

4. **Test minimal FastAPI app** - Strip down to just `/health` endpoint

5. **Check Windows firewall/antivirus** - May be blocking localhost connections

## Files Modified Today
- `backend/app/core/config.py` - Simplified to Groq-only config
- `backend/app/services/llm_provider.py` - Groq provider with retry logic
- `backend/app/agents/market_research.py` - Tavily integration for web search
- `backend/app/schemas/__init__.py` - Added PRODUCT_INSIGHT content type
- `backend/app/agents/calendar_planner.py` - Added follows_entry/supports_entry
- `backend/.env` - Groq API key configuration

## Working Commands for Testing
```bash
# Start backend (run in separate terminal)
cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# Test health
python -c "import requests; print(requests.get('http://localhost:8000/api/health', timeout=10).json())"

# Check knowledge base
python -c "import requests; print(requests.post('http://localhost:8000/api/knowledge/update', json={'force_reingest': True}).json())"
```