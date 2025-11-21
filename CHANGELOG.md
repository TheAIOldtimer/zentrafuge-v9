# ZENTRAFUGE V9 - CHANGELOG

All notable changes to this project will be documented in this file.

---

## [v2.0-stable] - 2025-11-21

### Summary
Memory system working with 100-conversation window. Ready for micro-memory development.

### Backend Changes

#### orchestrator.py
- **UPDATED**: Increased memory window from 5 to 100 conversations
- **UPDATED**: Uses last 30 conversations in prompt (up from 3)
- **UPDATED**: Added contextual greeting logic (first visit vs returning)
- **UPDATED**: Increased max_tokens from 500 to 600
- **UPDATED**: Added memory injection logging

#### memory_storage.py
- **UPDATED**: Increased query limit multiplier for better coverage
- **UPDATED**: Lowered importance threshold from 3 to 2

#### crypto_handler.py
- **VERIFIED**: Working correctly with ZENTRAFUGE_MASTER_KEY
- No changes needed

#### app.py
- **UPDATED**: Added `cd backend` to Render start command
- **VERIFIED**: All routes working

### Frontend Changes

#### chat.html
- **UPDATED**: [Describe your changes here]
- Date: 2025-11-21

#### chat.js
- **UPDATED**: [Describe your changes here]
- Date: 2025-11-21

#### auth.js
- **UPDATED**: [Describe your changes here]
- Date: 2025-11-21

### Configuration Changes

#### Render.com (v9 Main)
- Start command updated to include `cd backend`
- Environment: ZENTRAFUGE_MASTER_KEY (verified working)

#### Firebase
- Note: Currently pointing to v9-veterans Firebase (may need update)

### Known Issues
- Old memories for user Jor41jOY6dQPy0NVlGFYxsPSekn1 won't decrypt (different key era)
- New accounts work perfectly

### Testing Results
- ✅ New account created and tested
- ✅ Memory saves correctly
- ✅ Memory retrieves correctly
- ✅ No decryption errors for new users
- ✅ Cael remembers: blue (color), Duke (cat)

---

## [v1.0] - Pre-2025-11-21

### Summary
Original memory system with 5-conversation window.

### Known Issues
- Memory window too small (5 conversations)
- Older memories not accessible
- Generic greetings every session

---

## Template for Future Entries

```
## [vX.X] - YYYY-MM-DD

### Summary
Brief description of this version.

### Backend Changes
#### filename.py
- **ADDED/UPDATED/REMOVED**: Description
- **REASON**: Why this change was made

### Frontend Changes
#### filename.html/js
- **ADDED/UPDATED/REMOVED**: Description

### Configuration Changes
- Environment variables
- Deployment settings

### Database Changes
- Schema updates
- Migration notes

### Testing Results
- ✅ What was tested and passed
- ❌ What failed (if any)

### Known Issues
- List any known problems

### Breaking Changes
- List any changes that break backward compatibility

### Migration Notes
- Steps needed to upgrade from previous version
```

---

## File Inventory

### Backend (/backend)
| File | Purpose | Last Updated |
|------|---------|--------------|
| app.py | Flask API routes | 2025-11-21 |
| orchestrator.py | AI conversation engine | 2025-11-21 |
| memory_storage.py | Firestore memory layer | 2025-11-21 |
| crypto_handler.py | Encryption/decryption | 2025-11-21 |
| being_code.txt | Cael's identity | - |
| requirements.txt | Python dependencies | - |

### Frontend (/frontend or root)
| File | Purpose | Last Updated |
|------|---------|--------------|
| chat.html | Chat interface | 2025-11-21 |
| chat.js | Chat functionality | 2025-11-21 |
| auth.js | Authentication | 2025-11-21 |
| index.html | Landing page | - |
| onboarding.html | User onboarding | - |
| styles.css | Styling | - |

### Configuration
| File/Setting | Location | Last Updated |
|--------------|----------|--------------|
| ZENTRAFUGE_MASTER_KEY | Render ENV | - |
| FIREBASE_CREDENTIALS | Render ENV | - |
| Start command | Render Settings | 2025-11-21 |

---

## Quick Reference

### Current Production Versions
- **Backend**: v2.0-stable
- **Frontend**: v2.0-stable
- **Database**: Firebase (v9-veterans project)

### Deployment URLs
- **Frontend**: https://zentrafuge-v9.netlify.app/
- **Backend**: https://zentrafuge-v9.onrender.com/
- **Test Frontend**: https://v9-test-area--zentrafuge-v9.netlify.app/
- **Test Backend**: https://zentrafuge-test-area.onrender.com/

### Git Tags
- `v2.0-stable` - Memory system working (2025-11-21)

---

## How to Update This File

1. Before making changes, note what you're changing
2. After changes work, add entry to this file
3. Include: file name, what changed, why, date
4. Commit changelog with your changes

### Example Entry:
```
#### chat.js
- **UPDATED**: Removed timestamp display from message bubbles
- **REASON**: Cleaner UI, timestamps not needed
- **DATE**: 2025-11-21
```

---

**Last Updated**: 2025-11-21 18:50 GMT
**Maintained By**: Ant / Claude
