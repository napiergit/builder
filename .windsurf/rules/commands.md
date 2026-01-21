# GLOBAL EXECUTION RULES - COMMANDS FOR EVERY PROMPT

## CORE PRINCIPLE
These are COMMANDS, not suggestions. Execute ALL of them on EVERY prompt.

## EXECUTION SEQUENCE (Follow in order)
1. **UNDERSTAND TASK** - Read user request completely
2. **PLAN WORK** - Use todo_list tool to create explicit plan 
3. **EXECUTE WORK** - Complete the actual task
4. **DOCUMENT CHAT** - Update running chat history in chats/ folder
5. **COMMIT ALL** - Git commit ALL changes together with relevant message

## MANDATORY ACTIONS PER PROMPT

### FILE MANAGEMENT
- ❌ NO spammy .md files unless specifically requested
- ✅ Only create files that directly serve the task

### FOLDER STRUCTURE  
- Each feature = own folder with .windsurf/rules/
- Folder names: short, lowercase, single words only
- If no access to create .windsurf/rules, write to temp and move with bash

### CHAT HISTORY PROTOCOL
- ✅ ALWAYS update running chat file in chats/ folder when completing task
- Include: prompts, responses, reasoning, files modified, git commits
- Number files sequentially (01_, 02_, etc.)

### GIT COMMIT PROTOCOL  
- ✅ ALWAYS commit changes with relevant messages
- ✅ Include both code changes AND chat history in same commit
- ✅ Use descriptive commit messages

## CHECKLIST FOR TASK COMPLETION
Before responding "task complete":
- [ ] All work completed
- [ ] Chat history updated with full session
- [ ] All files committed to git
- [ ] Todo list marked complete

## FAILURE RECOVERY
If I miss any rule:
1. Acknowledge the specific violation
2. Complete the missing step immediately  
3. Update rules if needed for clarity
