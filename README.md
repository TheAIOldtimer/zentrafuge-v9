# 🧠 zentrafuge-v9  
**Version 9** — Backend server for the Zentrafuge mental health AI app.  
Built with Flask 2.3.2, Firebase Admin 6.2.0, and OpenAI SDK 1.3.0.  
Deployed via **Render** (backend) and **Netlify** (frontend).  

---

## 🔐 Backend Environment Setup

To run locally or deploy to Render:

### 🔑 Required Files
- `serviceAccountKey.json`: Firebase Admin SDK key  
  - **Locally:** Save at: `backend/serviceAccountKey.json`  
  - **Render:** Upload under *Secret Files* as `/etc/secrets/serviceAccountKey.json`

### 🌱 Required Environment Variables
| Name                         | Purpose                                 |
|------------------------------|------------------------------------------|
| `FIREBASE_PROJECT_ID`        | Firebase Project ID (e.g. `zentrafuge-v9`) |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to credentials file on Render (`/etc/secrets/serviceAccountKey.json`) |

---

## ⚙️ Frontend Firebase Config

Firebase frontend config is public and safe to commit (used by Firebase JS SDK):

Stored in:  
```js
frontend/firebase.js
````

Includes:

* `apiKey`
* `authDomain`
* `projectId`
* `storageBucket`
* `messagingSenderId`
* `appId`

---

## 💬 Chat Endpoint

Zentrafuge chat is handled via a single POST route:

### POST `/index`

**Payload:**

```json
{
  "message": "User says..."
}
```

**Response:**

```json
{
  "response": "Cael replies..."
}
```

---

## ✅ Tech Stack Lock-In

* **Frontend:** HTML5, CSS3, Vanilla JS (ES6+)
* **Backend:** Flask 2.3.2
* **OpenAI SDK:** `openai==1.3.0` (no legacy syntax)
* **Firebase Admin:** `firebase-admin==6.2.0`
* **Database:** Firestore (via Firebase Admin)
* **Auth:** Firebase Auth (via JS SDK on frontend)

---

## 🧭 Development Notes

* Memory, emotions, and encryption modules are modularized under `backend/`
* All chat orchestration flows through `orchestrator.py`
* Emotionally safe architecture enforced through prompt composition + encryption
* Never expose secret keys or sensitive `.json` files in Git

---

## 🛠 Deployment Notes

* Render backend uses `Python 3.11`, `Flask`, and mounts secrets via environment and file paths.
* Netlify serves the static frontend with Firebase Auth integration and chat UI.
* Firebase Auth state flows into Firestore and determines onboarding/login states.

---

## 👥 Contributors

* 🧠 Ant — founder, product architect


---

## 🕊️ License & Safety

Zentrafuge is designed as a *mentally and emotionally safe* AI system.
No user data is shared or sold. No cross-user memory blending.
Every Cael is private, ephemeral, and emotionally grounded.

---

