#!/usr/bin/env python3
"""
Zentrafuge v9 - Main Flask Backend
Modular, secure, memory-first AI companion architecture
"""

import os
import json
import logging
import time
from datetime import datetime

from flask import Flask, request, jsonify
from flask_cors import CORS

import firebase_admin
from firebase_admin import auth, credentials, firestore

from openai import OpenAI  # OpenAI SDK v1.3.0 style

# -----------------------------------------------------------------------------
# Flask + Logging
# -----------------------------------------------------------------------------

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Lazy globals
db = None
openai_client = None


# -----------------------------------------------------------------------------
# Firebase Initialization (using FIREBASE_CREDENTIALS_JSON)
# -----------------------------------------------------------------------------

def init_firebase():
    """
    Lazily initialize Firebase Admin using FIREBASE_CREDENTIALS_JSON.
    Returns a Firestore client or None on failure.
    """
    global db

    if db is not None:
        return db

    firebase_creds = os.getenv("FIREBASE_CREDENTIALS_JSON")
    if not firebase_creds:
        logger.error("Missing FIREBASE_CREDENTIALS_JSON environment variable")
        return None

    try:
        # Only initialize the app once
        if not firebase_admin._apps:
            cred = credentials.Certificate(json.loads(firebase_creds))
            firebase_admin.initialize_app(cred)
            logger.info("✅ Firebase initialized using FIREBASE_CREDENTIALS_JSON")

        db = firestore.client()
        return db
    except Exception as e:
        logger.error(f"❌ Firebase initialization failed: {e}")
        db = None
        return None


# -----------------------------------------------------------------------------
# OpenAI Initialization (SDK v1.3.0)
# -----------------------------------------------------------------------------

def init_openai():
    """
    Lazily initialize the OpenAI client using OPENAI_API_KEY.
    """
    global openai_client

    if openai_client is not None:
        return openai_client

    start_time = time.time()
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.error("OPENAI_API_KEY environment variable is not set")
            return None

        # Ensure the env var is visible to the SDK
        os.environ["OPENAI_API_KEY"] = api_key

        openai_client = OpenAI()
        logger.info(
            "✅ OpenAI client initialized in %.2f seconds",
            time.time() - start_time
        )
        return openai_client

    except Exception as e:
        logger.error(f"❌ OpenAI initialization failed: {e}")
        openai_client = None
        return None


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def verify_firebase_token(token: str):
    """
    Verify a Firebase ID token and return the decoded payload, or None.
    """
    try:
        return auth.verify_id_token(token)
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        return None


def get_authorized_user():
    """
    Helper: read Bearer token from Authorization header and return user_info or error response.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None, (jsonify({"error": "Authorization required"}), 401)

    token = auth_header.split(" ", 1)[1]
    user_info = verify_firebase_token(token)
    if not user_info:
        return None, (jsonify({"error": "Invalid token"}), 401)

    return user_info, None


def run_cael_completion(message: str):
    """
    Shared OpenAI chat call for Cael.
    Returns reply text or raises an exception.
    """
    client = init_openai()
    if not client:
        raise RuntimeError("AI unavailable")

    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are Cael, an emotionally intelligent AI companion for "
                    "UK veterans. Be calm, grounded, and honest. Never make "
                    "clinical claims or promise to replace professional help."
                ),
            },
            {"role": "user", "content": message},
        ],
        max_tokens=500,
        temperature=0.7,
    )
    return completion.choices[0].message.content


# -----------------------------------------------------------------------------
# Routes
# -----------------------------------------------------------------------------

@app.route("/")
def root():
    return jsonify({
        "service": "Zentrafuge v9 API",
        "status": "running",
        "version": "9.0.0",
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
    openai_ok = init_openai() is not None

    status = "healthy" if (firebase_ok and openai_ok) else "degraded"

    return jsonify({
        "status": status,
        "firebase": firebase_ok,
        "openai": openai_ok,
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
        "valid": True,
        "user_id": user["uid"],
        "email": user.get("email"),
    })


@app.route("/user/profile", methods=["GET", "POST"])
def user_profile():
    user_info, error_response = get_authorized_user()
    if error_response:
        return error_response

    user_id = user_info["uid"]
    db_local = init_firebase()
    if not db_local:
        return jsonify({"error": "Database unavailable"}), 503

    if request.method == "GET":
        doc = db_local.collection("users").document(user_id).get()
        if doc.exists:
            return jsonify(doc.to_dict())

        # Default profile if none exists
        default_profile = {
            "user_id": user_id,
            "email": user_info.get("email"),
            "created_at": datetime.utcnow().isoformat(),
            "onboarding_complete": False,
            "cael_initialized": False,
        }
        db_local.collection("users").document(user_id).set(default_profile)
        return jsonify(default_profile)

    # POST: create/update profile
    data = request.get_json(silent=True) or {}
    profile = {
        "user_id": user_id,
        "email": user_info.get("email"),
        "full_name": data.get("name", ""),
        "is_veteran": data.get("is_veteran", False),
        "country": data.get("country", "UK"),  # future-proof for intl rollout
        "marketing_opt_in": data.get("marketing_opt_in", False),
        "registration_date": data.get(
            "registration_date",
            datetime.utcnow().isoformat()
        ),
        "created_at": datetime.utcnow().isoformat(),
        "onboarding_complete": data.get("onboarding_complete", False),
        "cael_initialized": data.get("cael_initialized", False),
    }
    db_local.collection("users").document(user_id).set(profile)
    return jsonify({"success": True, "profile": profile})

@app.route("/user/onboarding", methods=["POST"])
def user_onboarding():
    """
    Complete user onboarding process and save preferences
    """
    user_info, error_response = get_authorized_user()
    if error_response:
        return error_response

    user_id = user_info["uid"]
    db_local = init_firebase()
    if not db_local:
        return jsonify({"error": "Database unavailable"}), 503

    data = request.get_json(silent=True) or {}
    
    # Build comprehensive onboarding profile
    onboarding_data = {
        "user_id": user_id,
        "email": user_info.get("email"),
        "onboarding_complete": True,
        "cael_initialized": True,
        "completed_at": datetime.utcnow().isoformat(),
        
        # Companion settings
        "companion_name": data.get("cael_name", "Cael"),
        
        # Communication preferences
        "communication_style": data.get("communication_style", "balanced"),
        "emotional_pacing": data.get("emotional_pacing", "varies_situation"),
        
        # Life context
        "life_chapter": data.get("life_chapter", ""),
        "sources_of_meaning": data.get("sources_of_meaning", []),
        "effective_support": data.get("effective_support", []),
        
        # Veteran profile (if applicable)
        "veteran_profile": data.get("veteran_profile", {
            "is_veteran": False,
            "service_branch": None,
            "service_country": None,
            "service_years": None,
            "unit_served": None,
            "deployments": None,
            "verification_status": "not_applicable"
        }),
        
        # System metadata
        "onboarding_version": "v9_enhanced",
        "personality_profile": data.get("personality_profile", {}),
    }
    
    try:
        # Save to Firestore
        db_local.collection("users").document(user_id).set(
            onboarding_data, 
            merge=True  # Merge with existing profile data
        )
        
        logger.info(f"✅ Onboarding completed for user {user_id}")
        
        return jsonify({
            "success": True,
            "message": "Onboarding completed successfully",
            "veteran_verified": onboarding_data["veteran_profile"].get("is_veteran", False),
            "companion_name": onboarding_data["companion_name"]
        })
        
    except Exception as e:
        logger.error(f"❌ Onboarding save failed: {e}")
        return jsonify({"error": "Failed to save onboarding data"}), 500

# -------------------------------------------------------------------------
# New: /index – main chat endpoint with {message} -> {response} contract
# -------------------------------------------------------------------------

@app.route("/index", methods=["POST"])
def index_chat():
    """
    Main chat endpoint for the frontend.

    Request:
        { "message": "User says..." }

    Response:
        { "response": "Cael replies..." }

    (Auth required via Firebase ID token in Authorization: Bearer <token>)
    """
    user_info, error_response = get_authorized_user()
    if error_response:
        return error_response

    user_id = user_info["uid"]
    db_local = init_firebase()
    if not db_local:
        return jsonify({"error": "Database unavailable"}), 503

    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify({"error": "Message required"}), 400

    # Log user message (plaintext for now – encryption comes later)
    db_local.collection("messages").add({
        "user_id": user_id,
        "role": "user",
        "content": message,
        "timestamp": datetime.utcnow().isoformat(),
        "via": "index",
    })

    try:
        reply = run_cael_completion(message)

        db_local.collection("messages").add({
            "user_id": user_id,
            "role": "assistant",
            "content": reply,
            "timestamp": datetime.utcnow().isoformat(),
            "model": "gpt-3.5-turbo",
            "via": "index",
        })

        # IMPORTANT: contract: { "response": "Cael replies..." }
        return jsonify({"response": reply})

    except Exception as e:
        logger.error(f"OpenAI error in /index: {e}")
        fallback = (
            "Cael is having trouble responding right now. "
            "Please try again soon."
        )
        return jsonify({"response": fallback})


# -------------------------------------------------------------------------
# Legacy / debugging endpoint: /chat/message
# -------------------------------------------------------------------------

@app.route("/chat/message", methods=["POST"])
def chat_message():
    """
    Legacy chat endpoint.
    Same behaviour as /index, but keeps the older { success, response } shape.
    """
    user_info, error_response = get_authorized_user()
    if error_response:
        return error_response

    user_id = user_info["uid"]
    db_local = init_firebase()
    if not db_local:
        return jsonify({"error": "Database unavailable"}), 503

    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify({"error": "Message required"}), 400

    db_local.collection("messages").add({
        "user_id": user_id,
        "role": "user",
        "content": message,
        "timestamp": datetime.utcnow().isoformat(),
        "via": "chat.message",
    })

    try:
        reply = run_cael_completion(message)

        db_local.collection("messages").add({
            "user_id": user_id,
            "role": "assistant",
            "content": reply,
            "timestamp": datetime.utcnow().isoformat(),
            "model": "gpt-3.5-turbo",
            "via": "chat.message",
        })

        return jsonify({"success": True, "response": reply})

    except Exception as e:
        logger.error(f"OpenAI error in /chat/message: {e}")
        fallback = (
            "Cael is having trouble responding right now. "
            "Please try again soon."
        )
        return jsonify({"success": True, "response": fallback, "fallback": True})


# -----------------------------------------------------------------------------
# Entry point
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False)
