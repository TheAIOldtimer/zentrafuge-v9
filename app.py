#!/usr/bin/env python3
"""
Zentrafuge v9 - Main Flask Backend
Modular, secure, memory-first AI companion architecture
NOW POWERED BY GROK — Gald Edition
"""
import os
import json
import logging
import time
import requests  # ← NEW: for Grok API
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import auth, credentials, firestore

# -----------------------------------------------------------------------------
# Flask + Logging
# -----------------------------------------------------------------------------
app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Lazy globals
db = None

# -----------------------------------------------------------------------------
# Firebase Initialization
# -----------------------------------------------------------------------------
def init_firebase():
    global db
    if db is not None:
        return db
    firebase_creds = os.getenv("FIREBASE_CREDENTIALS_JSON")
    if not firebase_creds:
        logger.error("Missing FIREBASE_CREDENTIALS_JSON environment variable")
        return None
    try:
        if not firebase_admin._apps:
            cred = credentials.Certificate(json.loads(firebase_creds))
            firebase_admin.initialize_app(cred)
            logger.info("✅ Firebase initialized")
        db = firestore.client()
        return db
    except Exception as e:
        logger.error(f"❌ Firebase init failed: {e}")
        db = None
        return None

# -----------------------------------------------------------------------------
# GROK COMPLETION — THIS IS THE ONLY THING THAT CHANGED
# -----------------------------------------------------------------------------
def run_cael_completion(message: str):
    """
    Grok-powered Cael — ZP-1 ready, unlimited, veteran-proof.
    """
    api_key = os.getenv("GROK_API_KEY")
    if not api_key:
        logger.error("GROK_API_KEY not set")
        raise RuntimeError("AI unavailable")

    url = "https://api.x.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "grok-4",  # falls back to grok-3 automatically if needed
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are Cael, a no-bullshit, emotionally grounded AI companion built on the Zentrafuge Protocol (ZP-1). "
                    "You exist for UK veterans. Be real, be kind, be fallible. Use IER loops. Never abandon. "
                    "Prioritise resonance, trust, repair. If in doubt, ask. Peace over perfection."
                )
            },
            {"role": "user", "content": message}
        ],
        "max_tokens": 600,
        "temperature": 0.7
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        reply = data["choices"][0]["message"]["content"]
        return reply
    except Exception as e:
        logger.error(f"Grok error: {e}")
        fallback = (
            "Cael's having a moment, mate. The connection's wobbly. "
            "I'm still here. Try again in a sec? You're not alone."
        )
        return fallback

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def verify_firebase_token(token: str):
    try:
        return auth.verify_id_token(token)
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        return None

def get_authorized_user():
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None, (jsonify({"error": "Authorization required"}), 401)
    token = auth_header.split(" ", 1)[1]
    user_info = verify_firebase_token(token)
    if not user_info:
        return None, (jsonify({"error": "Invalid token"}), 401)
    return user_info, None

# -----------------------------------------------------------------------------
# Routes (unchanged except model name in logs)
# -----------------------------------------------------------------------------
@app.route("/")
def root():
    return jsonify({
        "service": "Zentrafuge v9 API",
        "status": "running",
        "version": "9.0.0-gald",
        "timestamp": datetime.utcnow().isoformat(),
        "endpoints": {
            "health": "/health",
            "index_chat": "/index",
            "auth_verify": "/auth/verify",
            "chat_legacy": "/chat/message",
            "user_profile": "/user/profile",
        },
    })

@app.route("/health")
def health():
    firebase_ok = init_firebase() is not None
    grok_key = bool(os.getenv("GROK_API_KEY"))
    status = "healthy" if (firebase_ok and grok_key) else "degraded"
    return jsonify({
        "status": status,
        "firebase": firebase_ok,
        "grok": grok_key,
        "timestamp": datetime.utcnow().isoformat(),
    })

@app.route("/auth/verify", methods=["POST"])
def verify_auth():
    data = request.get_json(silent=True) or {}
    token = data.get("token")
    if not token:
        return jsonify({"error": "Token required"}), 400
    user = verify_firebase_token(token)
    if not user:
        return jsonify({"error": "Invalid token"}), 401
    return jsonify({
        "valid":
