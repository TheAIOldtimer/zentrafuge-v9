# zentrafuge-v9
Version 9: server repository for the zentrafuge mental health app.

## 🔐 Backend Environment Requirements (Secrets Not Included)

To run the backend (`Flask 2.3.2`):

### Required Files
- `serviceAccountKey.json`: Firebase Admin SDK key (not committed)
  - Stored locally at: `backend/serviceAccountKey.json`
  - On Render: upload via “Secret Files” as `/etc/secrets/serviceAccountKey.json`

### Required Env Vars
- `FIREBASE_PROJECT_ID=zentrafuge-v9`
- `GOOGLE_APPLICATION_CREDENTIALS=/etc/secrets/serviceAccountKey.json`
