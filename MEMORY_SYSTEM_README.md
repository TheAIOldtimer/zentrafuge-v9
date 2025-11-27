# Zentrafuge v9 - Enhanced Multi-Tier Memory System

## 🎯 Overview

This is a complete rewrite of Zentrafuge's memory architecture with three tiers:

1. **Persistent Facts** - Never forgotten (name, pets, veteran status, values)
2. **Micro Memories** - Session summaries with 14-day half-life forgetting curve
3. **Super Memories** - Consolidated long-term patterns (10 micro → 1 super)

## 📁 Files Created

### Memory System (backend/memory/)
```
memory/
├── __init__.py                 # Package initialization
├── persistent_facts.py         # Facts that NEVER decay (361 lines)
├── micro_memory.py            # Session summaries with forgetting (355 lines)
├── memory_consolidator.py     # 10 micro → 1 super (422 lines)
└── memory_manager.py          # Central orchestrator (377 lines)
```

### Core Updates
```
backend/
├── orchestrator_v2.py         # New 3-arg constructor (replaces orchestrator.py)
├── app_v2.py                  # Integration changes (see INTEGRATION_CHANGES.md)
└── memory_storage.py          # DEPRECATED (keep for safety, can remove after testing)
```

## 🔄 Key Changes from Old System

| Aspect | Old System | New System |
|--------|-----------|------------|
| **Architecture** | Single-tier encrypted blobs | 3-tier hierarchy (facts/micro/super) |
| **Forgetting** | None | 14-day half-life exponential decay |
| **Fact persistence** | Manual only | Auto-extracted + manual |
| **Consolidation** | None | Automatic (10 micro → 1 super) |
| **Orchestrator args** | 4 (user_id, db, openai, memory_storage) | 3 (user_id, db, openai) |
| **Memory creation** | External (passed in) | Internal (created automatically) |
| **Session end** | Just clears cache | Creates micro memory summary |
| **Onboarding** | Saves to Firestore only | Also imports to persistent facts |

## 🚀 Installation

### Step 1: Backup Current Files
```bash
cd backend
cp app.py app_backup.py
cp orchestrator.py orchestrator_backup.py
```

### Step 2: Create Memory Folder
```bash
mkdir -p backend/memory
```

### Step 3: Copy New Files
```bash
# Copy memory system files
cp /path/to/memory/__init__.py backend/memory/
cp /path/to/memory/persistent_facts.py backend/memory/
cp /path/to/memory/micro_memory.py backend/memory/
cp /path/to/memory/memory_consolidator.py backend/memory/
cp /path/to/memory/memory_manager.py backend/memory/

# Replace orchestrator
cp /path/to/orchestrator_v2.py backend/orchestrator.py

# Update app.py (see INTEGRATION_CHANGES.md)
```

### Step 4: Update app.py
Follow the changes documented in `INTEGRATION_CHANGES.md`:
1. Remove `from memory_storage import MemoryStorage`
2. Update `get_user_orchestrator()` to use 3 args
3. Add fact import in `/user/onboarding` endpoint
4. Add `end_session()` call in `/session/clear` endpoint

### Step 5: Update Firestore Rules
Deploy the new `firestore.rules` to allow access to new collections:
- `user_facts/{userId}`
- `micro_memories_{userId}/{memoryId}`
- `super_memories_{userId}/{memoryId}`

### Step 6: Deploy
```bash
git add backend/memory backend/orchestrator.py backend/app.py
git commit -m "feat: Enhanced multi-tier memory system with persistent facts"
git push origin v9-TEST-AREA
```

## 📊 How It Works

### 1. Persistent Facts (Never Forgotten)

**Storage:** `user_facts/{userId}`

**Categories:**
- `identity`: name, age, location
- `relationships`: pets, family members  
- `status`: veteran status, occupation
- `values`: core beliefs, life context
- `preferences`: communication style, boundaries

**Example:**
```python
# Auto-extracted from "My name is Ant"
facts.set_fact('identity', 'name', 'Ant', 'conversation')

# Auto-extracted from "I have a dog named Duke"
facts.set_fact('relationships', 'pet_dog_duke', {
    'type': 'dog',
    'name': 'Duke'
}, 'conversation')

# Imported from onboarding
facts.set_fact('status', 'is_veteran', True, 'onboarding')
```

### 2. Micro Memories (14-Day Half-Life)

**Storage:** `micro_memories_{userId}/{memoryId}`

**Created:** At end of each session (logout, timeout)

**Decay Formula:**
```
I(t) = I₀ × (0.5)^(t / 14 days)

Where:
- I(t) = current importance
- I₀ = initial importance (1-10)
- t = days elapsed
```

**Example:**
```
Day 0:  importance = 8.0
Day 7:  importance = 5.7  (71% of original)
Day 14: importance = 4.0  (50% of original)
Day 28: importance = 2.0  (25% of original)
Day 60: importance < 1.0  (deleted)
```

**Content:**
```json
{
  "summary": "User discussed career change and asked for advice",
  "message_count": 15,
  "messages": [...],
  "emotional_context": {
    "primary_emotion": "anxious",
    "emotional_intensity": 0.7
  },
  "topics": ["work", "career", "goals"],
  "importance": 7.5,
  "created_at": "2025-11-26T10:00:00Z"
}
```

### 3. Super Memories (Consolidated Patterns)

**Storage:** `super_memories_{userId}/{memoryId}`

**Created:** When 10+ unconsolidated micro memories exist

**Process:**
1. Gather 10 unconsolidated micro memories
2. Send to OpenAI for consolidation
3. Extract themes, patterns, emotional journey
4. Create super memory
5. Mark source micros as consolidated

**Example:**
```json
{
  "summary": "User showed consistent interest in career development...",
  "themes": ["personal_growth", "work_career"],
  "topics": ["career", "learning", "goals"],
  "emotional_patterns": {
    "dominant_emotion": "hopeful",
    "average_intensity": 0.5
  },
  "source_memory_count": 10,
  "date_range": {
    "start": "2025-10-01",
    "end": "2025-11-26"
  }
}
```

## 🔧 API Usage

### In Orchestrator

```python
# Orchestrator now creates memory internally
orchestrator = CaelOrchestrator(
    user_id=user_id,
    db=db,
    openai_client=openai
    # No memory_storage argument!
)

# Import onboarding data
orchestrator.import_onboarding(onboarding_data)

# End session (creates micro memory)
await orchestrator.end_session(reason="logout")
```

### Direct Memory Access

```python
# Access memory subsystems
orchestrator.memory.facts.set_fact('identity', 'favorite_color', 'blue', 'user')
orchestrator.memory.facts.get_fact('identity', 'name')

# Get memory stats
stats = orchestrator.memory.get_memory_stats()
```

## 🧪 Testing

### Test 1: Fact Extraction
```python
# User says: "My name is Ant"
# Expected: facts['identity']['name'] = 'Ant'

# User says: "I have a dog named Duke"
# Expected: facts['relationships']['pet_dog_duke'] = {'type': 'dog', 'name': 'Duke'}
```

### Test 2: Onboarding Import
```python
# Complete onboarding with veteran status
# Expected: facts['status']['is_veteran'] = True
# Expected: facts['preferences']['communication_style'] = 'direct'
```

### Test 3: Micro Memory Creation
```python
# Have a conversation with 10+ messages
# Logout
# Expected: New document in micro_memories_{userId}
# Expected: Summary generated by OpenAI
```

### Test 4: Memory Decay
```python
# Create micro memory
# Wait 14 days (or adjust HALF_LIFE_DAYS for testing)
# Expected: Importance drops to 50%
```

### Test 5: Consolidation
```python
# Complete 10+ sessions
# Expected: Super memory created
# Expected: Source micros marked as consolidated
```

## 📈 Monitoring

### Check Memory Stats
```bash
# GET /memory/stats
{
  "persistent_facts": {
    "total_facts": 12,
    "categories": ["identity", "relationships", "status"]
  },
  "micro_memories": {
    "total_micro_memories": 25,
    "consolidated": 10,
    "unconsolidated": 15
  },
  "super_memories": {
    "total_super_memories": 1
  }
}
```

### Check Firestore Collections
```
user_facts/
  └── {userId}/
      └── facts: {...}

micro_memories_{userId}/
  ├── {microMemoryId1}
  ├── {microMemoryId2}
  └── ...

super_memories_{userId}/
  └── {superMemoryId1}
```

## 🔒 Security

All memory tiers respect Firestore security rules:
- Users can only access their own memories
- Backend uses Admin SDK (bypasses rules)
- Frontend must authenticate to read

## 🐛 Troubleshooting

### Issue: "No module named 'memory'"
**Solution:** Ensure `backend/memory/__init__.py` exists

### Issue: Orchestrator fails with "takes 3 positional arguments"
**Solution:** Update app.py to remove `memory_storage` argument

### Issue: Facts not auto-extracting
**Solution:** Check logs for "Auto-extracted N facts" messages

### Issue: Micro memories not created on logout
**Solution:** Ensure `/session/clear` endpoint calls `end_session()`

### Issue: Consolidation not happening
**Solution:** Check `get_unconsolidated_count()` >= 10

## 📚 Further Reading

- `INTEGRATION_CHANGES.md` - Detailed integration steps
- `firestore.rules` - Security rules for new collections
- `persistent_facts.py` - Fact extraction patterns
- `micro_memory.py` - Forgetting curve implementation
- `memory_consolidator.py` - Consolidation logic

## 🎉 Benefits

1. **Better Context** - Multi-tier system provides richer context to AI
2. **Natural Forgetting** - 14-day half-life mimics human memory
3. **Long-Term Patterns** - Super memories capture themes over time
4. **Auto-Extraction** - Facts automatically captured from conversations
5. **Scalable** - Consolidation prevents memory explosion
6. **Persistent** - Important facts never forgotten

## 📞 Support

If you encounter issues, check:
1. Backend logs for error messages
2. Firestore console for collection structure
3. Browser console for frontend errors
4. `/memory/stats` endpoint for memory state

---

**Version:** 2.0.0  
**Date:** November 26, 2025  
**Author:** Zentrafuge Team
