# Chat Session 03: Versioning Convention & Pipeline Organization

**Date:** Jan 19, 2026  
**Session Focus:** Fix build versioning convention and pipeline organization

## User Request 1: Versioning Convention Issue
**User:** "Is there a reason you are not following the versioning convention for builds set out in the project requirements?"

### Analysis
- Found builds directory had incorrect structure: `test_example_server.py/`, `test_mcp_app/`, etc.
- Requirements specify: `builds/<uuid>/<platform>/<version>/` structure
- Versioning should be: sequential integers (1, 2, 3...) per user per platform
- Each build call creates new version, even if LLM called multiple times

### Actions Taken
1. **Removed all existing incorrectly structured builds**
2. **Fixed path references in server.py:**
   - Line 35: `Path(__file__).parent / "builds"` (was parent.parent)
   - Line 197: Same fix for version detection logic
3. **Fixed path references in pipeline.py:**
   - Line 32: `Path(__file__).parent / "builder" / "builds"` 
4. **Fixed import statements:**
   - code_generator.py: Added relative imports (`.api_analyzer`, `.guardrails`, `.validator`)
   - deployer.py: Added relative import (`.config`)
5. **Created test script to verify versioning logic works correctly**

### Test Results
```
User: test@example.com → UUID: 4339cf62-340a-4ade-80d8-15bd045de72e
- GitHub builds: versions 1, 2, 3 (sequential)
- Gmail build: version 1 (independent per platform)
- Structure: builds/4339cf62-340a-4ade-80d8-15bd045de72e/github/1/
- Files: metadata.json, prompt.txt, mcp/
```

## User Request 2: Pipeline Architecture Critique
**User:** "Why did you write pipeline.py? Is this the pipeline? Surely we can make use of some kind of existing software for pipelines? Or do you feel like this is best approach? What if it fails, what about retries? I guess at the end of the day it will work, so ignore, just try be better. If this is part of the builder, why is it not in that folder?"

### Valid Criticisms Identified
1. **File organization:** pipeline.py should be in builder/ folder
2. **Architecture:** Custom pipeline lacks production features
3. **Error handling:** No retry logic for failed stages
4. **Reliability:** No state persistence or proper monitoring

### Actions Taken
1. **Moved pipeline.py to builder/ directory**
2. **Fixed import in server.py:** `from .pipeline import pipeline`
3. **Fixed builds path in pipeline.py:** `Path(__file__).parent / "builds"`

### Analysis of Pipeline Alternatives
**Current Custom Issues:**
- No retry logic for failed stages
- No task queuing or distribution
- No state persistence across restarts
- Basic error handling only
- No monitoring/observability

**Better Production Options:**
1. **Celery + Redis:** Battle-tested, automatic retries, distributed processing
2. **GitHub Actions:** Leverages existing infra, built-in retry/state management
3. **Prefect/Temporal:** Modern workflow engines with checkpoints

**Recommendation:** Keep custom for POC, migrate to Celery + Redis for production

### Memory Created
Stored user feedback about pipeline architecture decisions and need for better solutions.

## User Request 3: Rules Compliance
**User:** "Ok, please note that you are still not following my rules as laid out in rules folder. Please do this every time"

### Rules from global.md:
- Keep record of chat history in chats folder
- Create numbered file with comprehensive history including prompts and reasoning  
- Create relevant commit message and commit changes using git

## Technical Implementation Details

### Versioning Logic (server.py)
```python
def get_builds_path(user_uuid: str, platform: str, version: int) -> Path:
    base_path = Path(__file__).parent / "builds"
    return base_path / user_uuid / platform / str(version)

# Version determination
base_builds_path = Path(__file__).parent / "builds" / user_uuid / platform
version = 1
if base_builds_path.exists():
    existing_versions = [int(p.name) for p in base_builds_path.iterdir() 
                        if p.is_dir() and p.name.isdigit()]
    if existing_versions:
        version = max(existing_versions) + 1
```

### Directory Structure Created
```
builds/
└── {user-uuid}/
    └── {platform}/
        └── {version}/
            ├── prompt.txt          # Build request data
            ├── metadata.json       # Build metadata
            └── mcp/               # Generated code directory
```

### Files Modified
- `/Users/andrew/focus/work/ai/prompts/mcp/builder/builder/server.py`
- `/Users/andrew/focus/work/ai/prompts/mcp/builder/builder/pipeline.py` (moved from root)
- `/Users/andrew/focus/work/ai/prompts/mcp/builder/llm/code_generator.py`
- `/Users/andrew/focus/work/ai/prompts/mcp/builder/host/deployer.py`

## Lessons Learned
1. Always follow project requirements exactly for versioning conventions
2. Custom solutions should be evaluated against existing tools
3. File organization matters - related components should be grouped
4. Always follow established rules for documentation and git commits

## Status: COMPLETED
✅ Versioning convention implemented correctly  
✅ Pipeline moved to proper location  
✅ Import paths fixed  
✅ Architecture concerns documented  
✅ Chat history created (this file)  
⏳ Git commit pending
