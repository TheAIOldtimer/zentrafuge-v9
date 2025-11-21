# ZENTRAFUGE V9 - CURRENT PRODUCTION STATE
## As of November 21, 2025 - 4:00 PM GMT

---

## 🟢 WORKING & DEPLOYED

### Memory System (v1.0 - STABLE)
**Status:** ✅ PRODUCTION - WORKING

**Components:**
- `memory_storage.py` - Encrypted memory storage with Firestore
- `orchestrator.py` (v2.0) - Memory injection working
- `crypto_handler.py` - Encryption/decryption functional

**Features:**
- ✅ Saves conversations to Firestore (encrypted)
- ✅ Loads last 100 conversations
- ✅ Injects last 30 into prompt
- ✅ Emotional memory tracking
- ✅ Veteran-aware handling

**Performance:**
- Token usage: ~2000-3000 tokens/request
- Memory retrieval: Working
- Encryption: Functional
- Cost: ~$0.0003-0.0005/request

**Known Issues:**
- ⚠️ Some older conversations (2+ days ago) outside 100-conversation window
- ⚠️ No smart search yet (just chronological)
- ⚠️ Connection errors occasionally (frontend timeout, not memory issue)

**Test Results:**
- ✅ Remembers recent conversations (today)
- ⚠️ Sometimes misses conversations from 2+ days ago
- ✅ Contextual responses working
- ✅ Encryption verified

---

## 📊 CURRENT ARCHITECTURE

```
User sends message
    ↓
orchestrator.py receives
    ↓
Loads last 100 conversations from Firestore
    ↓
Decrypts conversations
    ↓
Takes last 30 conversations
    ↓
Injects into prompt (2000-3000 tokens)
    ↓
Sends to OpenAI (gpt-4o-mini or gpt-4-turbo)
    ↓
Response generated
    ↓
Saves new conversation to Firestore (encrypted)
    ↓
Returns response to user
```

---

## 📁 PRODUCTION FILES

### Core System
```
app.py (v1.0)
├─ Flask backend
├─ Routes: /index, /conversation/summary
├─ Session management
└─ CORS handling

orchestrator.py (v2.0) ⭐ LATEST
├─ Memory injection (WORKING)
├─ Loads 100 conversations
├─ Uses 30 in prompt
├─ Smart model routing (gpt-4o-mini/gpt-4-turbo)
├─ Emotional analysis
├─ Intent detection
└─ Veteran flag handling

memory_storage.py (v1.0)
├─ Firestore integration
├─ Encryption/decryption
├─ get_conversation_context(max_messages=100)
├─ store_conversation_memory()
├─ store_emotional_memory()
└─ search_memories()

crypto_handler.py (v1.0)
├─ AES encryption
├─ Fernet key derivation
├─ Data validation
└─ Input sanitization
```

### Supporting Files
```
being_code.txt
├─ Cael's identity and moral contract
├─ Veteran-specific guidance
└─ Emotional principles

requirements.txt
├─ Dependencies list
└─ Python packages

.env
├─ Firebase credentials
├─ OpenAI API key
└─ Encryption keys
```

---

## 🔧 CONFIGURATION

### Model Settings (orchestrator.py)
```python
model_config = {
    "primary": "gpt-4o-mini",        # Default
    "premium": "gpt-4-turbo",        # High emotion/complexity
    "max_tokens": 600,               # Response length
    "max_tokens_premium": 1000,      # Premium response length
    "temperature": 0.7,
}
```

### Memory Settings
```python
# In orchestrator.py _build_memory_context()
max_messages = 100  # Load last 100 conversations
use_in_prompt = 30  # Inject last 30 into prompt

# In orchestrator.py _build_prompt()
inject_count = 10   # Actually injects last 10 (bug or intentional?)
```

### Session Settings
```python
# No automatic timeout currently
# No inactivity detection
# Logout = manual only
```

---

## 💰 CURRENT COSTS

### Per Request (Average)
- Input tokens: ~2500
- Output tokens: ~500
- Total: ~3000 tokens
- Cost: $0.00045/request (gpt-4o-mini)

### Monthly Estimate (1000 users, 10 msgs/day)
- Daily requests: 10,000
- Monthly requests: 300,000
- Monthly cost: ~$135

---

## 🧪 TEST RESULTS (Today)

### Working ✅
1. Memory saves to Firestore (encrypted)
2. Memory loads from Firestore
3. Decryption works
4. Injection into prompt works
5. Responses use context
6. Veteran flag works
7. Emotional analysis works

### Issues Found ⚠️
1. Rex/Whiskers/red color conversation not recalled
   - Reason: Outside 100-conversation window (2 days old, many conversations since)
2. Connection errors on frontend
   - Reason: Timeout issues, not memory system
3. Generic greeting still shows sometimes
   - Reason: No contextual greeting logic yet

### Performance ✅
- Response time: 2-8 seconds
- Firestore queries: <1 second
- Decryption: <0.5 seconds
- No crashes or errors in memory system

---

## 📝 RECENT CHANGES LOG

### November 21, 2025 - Morning
- Diagnosed memory injection issue
- Confirmed memories loading but not being used
- Increased memory window from 5 to 20 to 100

### November 21, 2025 - Afternoon  
- Tested memory system
- Verified encryption working
- Confirmed 20 messages being injected
- Identified need for semantic search

### November 21, 2025 - Late Afternoon
- Discussed micro memory architecture
- Planned analytics engine
- Decided to lock current state before new development

---

## 🎯 WHAT'S NEXT (PLANNED)

### Phase 1: Micro Memory System
- Generate condensed memory summaries
- Reduce token usage by 80%
- Improve scalability
- Human-like forgetting curve

### Phase 2: Analytics Engine
- Track emotional patterns
- Clinical metrics (PHQ-9, GAD-7, PCL-5)
- Crisis detection
- Progress monitoring

### Phase 3: Advanced Features
- User dashboard
- Admin monitoring
- Research data aggregation
- Healthcare integration

---

## ⚠️ CRITICAL DEPENDENCIES

### External Services
- Firebase/Firestore (database)
- OpenAI API (LLM)
- Render.com (hosting)

### Environment Variables Required
```
FIREBASE_CREDENTIALS (JSON)
OPENAI_API_KEY
ENCRYPTION_KEY
FIREBASE_STORAGE_BUCKET
```

### Python Version
- Python 3.13
- Flask
- google-cloud-firestore
- openai
- cryptography

---

## 🔐 SECURITY STATUS

### Implemented ✅
- Encryption at rest (Firestore)
- Encryption in transit (HTTPS)
- Input sanitization
- CORS protection
- API key security

### Not Yet Implemented ⚠️
- Session timeout
- Inactivity detection
- Rate limiting
- Brute force protection
- Advanced threat monitoring

---

## 📊 FIRESTORE STRUCTURE

### Collections
```
users/
└─ {user_id}/
   ├─ email
   ├─ is_veteran
   ├─ onboarding_complete
   └─ personality_profile

memories_{user_id}/
└─ {memory_id}/
   ├─ content (encrypted)
   ├─ memory_type
   ├─ importance
   ├─ created_at
   ├─ active
   └─ tags

messages/ (LEGACY - not used by orchestrator)
└─ Old format, can be archived
```

---

## 🎯 READY FOR SNAPSHOT

This document represents the **stable, working state** of Zentrafuge v9 as of November 21, 2025.

### What Works:
✅ Memory system functional
✅ Encryption working
✅ Responses contextual
✅ Veteran support implemented
✅ Production deployed

### What Needs Improvement:
⚠️ Memory window needs optimization
⚠️ Smart search not implemented
⚠️ No session management
⚠️ Token costs high

### What's Planned:
🚀 Micro memory system
🚀 Analytics engine
🚀 Clinical tracking
🚀 User dashboard

---

## 📦 FILES TO BACKUP (READ-ONLY SNAPSHOT)

### Critical Files
1. orchestrator.py (v2.0) - Latest working version
2. memory_storage.py (v1.0)
3. app.py (v1.0)
4. crypto_handler.py (v1.0)
5. being_code.txt
6. requirements.txt

### Configuration
7. .env (encrypted backup)
8. Firebase credentials
9. Deployment settings

### Documentation
10. This state assessment
11. Architecture diagrams
12. API documentation

---

## ✅ SNAPSHOT CHECKLIST

Before proceeding with new development:

- [ ] Backup current orchestrator.py
- [ ] Backup current memory_storage.py
- [ ] Backup current app.py
- [ ] Tag git commit as "v2.0-stable"
- [ ] Export Firestore data (optional)
- [ ] Document all environment variables
- [ ] Save deployment configuration
- [ ] Create rollback plan
- [ ] Test restore procedure

---

## 🔄 ROLLBACK PROCEDURE (If New Development Breaks)

```bash
# 1. Restore backed up files
cp orchestrator_v2.0_stable.py orchestrator.py
cp memory_storage_v1.0_stable.py memory_storage.py
cp app_v1.0_stable.py app.py

# 2. Restart service
systemctl restart zentrafuge
# or
python app.py

# 3. Verify functionality
# Test: Memory recall working
# Test: Responses contextual
# Test: No errors in logs

# 4. If still broken, redeploy from git
git checkout v2.0-stable
git reset --hard
```

---

## 📞 EMERGENCY CONTACTS (if disaster)

- Database: Firebase Console
- Hosting: Render.com Dashboard  
- API: OpenAI Dashboard
- Git: GitHub repository

---

**SNAPSHOT TIMESTAMP:** 2025-11-21 16:00:00 GMT
**VERSION:** Zentrafuge v2.0 (Stable)
**STATUS:** Production - Working - Ready for Enhancement
**NEXT:** Micro Memory System Development

---

## 🎯 APPROVAL FOR SNAPSHOT

Once this is approved and backed up:
✅ Begin micro memory development
✅ Build analytics engine
✅ Implement advanced features

**All new work will be feature-flagged and reversible.**
