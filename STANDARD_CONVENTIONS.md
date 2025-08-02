# Zentrafuge Code Law: Standard Protocols for v9 and Beyond

This file defines **binding conventions** for all developers, contributors, and AI agents working within the Zentrafuge ecosystem. These standards prevent regressions, enforce clarity, and eliminate past sources of confusion or technical debt.

---

## 🔐 ENVIRONMENT VARIABLES

### ✅ Required Naming

* Use `GOOGLE_` prefix for all cloud, auth, and API credentials.
* ❌ Do **not** use `FIREBASE_`, `KEY_`, or ambiguous formats.

### Examples:

```env
GOOGLE_APPLICATION_CREDENTIALS=...
GOOGLE_FIRESTORE_PROJECT_ID=...
```

---

## 📛 NAMING CONVENTIONS

### 🔹 JavaScript / HTML / CSS

* Use `kebab-case` for:

  * Filenames: `chat-ui.js`, `onboarding-form.css`
  * CSS classes and IDs: `welcome-banner`, `user-avatar`
  * Folder names: `emotion-parser/`, `chat-flow/`

* Use `camelCase` for:

  * JavaScript functions: `handleSubmit()`, `getUserName()`

### 🔸 Python (backend only)

* Use `snake_case` for:

  * Function and variable names
  * Internal file structure is modular but pythonic

* Keep class names in `PascalCase`: `MemoryEngine`, `CaelOrchestrator`

---

## 🌐 ROUTING STANDARDS

### 🔹 URL Paths

* Always lowercase with optional hyphens
* Avoid camelCase in route names

#### ✅ Examples:

* `/chat/message`
* `/user/profile`

#### ❌ Avoid:

* `/ChatMessage`
* `/getUserData`

### 🔹 HTTP Verb Mapping

| Route              | Method | Purpose               |
| ------------------ | ------ | --------------------- |
| `/index`           | POST   | Chat message handler  |
| `/user/profile`    | POST   | Create/update profile |
| `/user/onboarding` | POST   | Submit onboarding     |

---

## 🎨 FRONTEND ARCHITECTURE

### File Structure:

```
frontend/
├── html/
├── css/
├── js/
└── utils/
```

### Fetching Logic:

* All fetch calls **must** use full absolute URLs.
* Reference via `config.js` → `Config.API_BASE`

```js
fetch(`${Config.API_BASE}/index`, { method: 'POST', ... })
```

---

## 🔥 DEPLOYMENT RULES

### Backend (Render):

```bash
cd backend && gunicorn app:app -b 0.0.0.0:$PORT
```

* Only change this if `app.py` moves to root.

### Frontend (Netlify):

* Publish directory: `frontend`
* No build step unless using a bundler
* Uses full backend URL via `config.js`

---

## 🧠 AI AGENT GUIDELINES

Any AI contributing code must:

* Validate conformance to this protocol
* Refuse to introduce violations (e.g., relative fetch paths, snake\_case in JS)
* Log and explain deviations if temporarily necessary
* Tag all PRs or commits that touch convention-sensitive files with: `#protocol-sensitive`

---

## 📅 VERSIONING & CHANGE CONTROL

* This file is binding as of **Zentrafuge v9**.
* All modifications must be approved by the lead dev (human).
* Historical errors that led to this protocol:

  * Snake\_case used in frontend JS → multiple integration bugs
  * `FIREBASE_` used in env → broke Firebase initialization
  * Relative paths to backend → 404 errors on Netlify

> 🔒 "Consistency is clarity. Clarity is safety."
