#!/usr/bin/env python3
"""
Zentrafuge v9 - Main Flask Backend
Modular, secure, memory-first AI companion architecture
WITH MEMORY & PERSONALITY INTEGRATION
"""

import os
import json
import logging
import time
import asyncio
from datetime import datetime

from flask import Flask, request, jsonify
from flask_cors import CORS

import firebase_admin
from firebase_admin import auth, credentials, firestore

from openai import OpenAI  # OpenAI SDK v1.3.0 style

# Import memory and orchestration modules
from cael_orchestrator import CaelOrchestrator, EmotionalSafetyMonitor
from memory_storage import MemoryStorage

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

# In-memory orchestrator cache for session persistence
user_orchestrators = {}


# -----------------------------------------------------------------------------
# Firebase Initialization (using FIREBASE_CREDENTIALS_JSON)
# -----------------------------------------------------------------------------

def init_firebase():
    """
    Lazily initialize Firebase Admin.

    Priority:
    1. FIREBASE_CREDENTIALS_JSON  -> JSON string of service account
    2. GOOGLE_APPLICATION_CREDENTIALS -> path to serviceAccountKey.json

    Returns a Firestore client or None on failure.
    """
    global db

    if db is not None:
        return db

    firebase_creds_json = os.getenv("FIREBASE_CREDENTIALS_JSON")
    cred = None

    try:
        if firebase_creds_json:
            # JSON content provided directly via env var
            logger.info("🔐 Using FIREBASE_CREDENTIALS_JSON for Firebase credentials")
            cred_dict = json.loads(firebase_creds_json)
            cred = credentials.Certificate(cred_dict)
        else:
            cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
            if not cred_path:
                logger.error(
                    "Missing Firebase credentials: "
                    "set FIREBASE_CREDENTIALS_JSON or GOOGLE_APPLICATION_CREDENTIALS"
                )
                return None

            logger.info("🔐 Using GOOGLE_APPLICATION_CREDENTIALS path for Firebase credentials")
            cred = credentials.Certificate(cred_path)

        # Only initialize once
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)
            logger.info("✅ Firebase initialized successfully")

        db = firestore.client()
        logger.info("✅ Firestore client created successfully")
        return db

    except Exception as e:
        logger.error(f"❌ Firebase initialization failed: {e}")
        logger.error(f"❌ Exception details: {type(e).__name__}: {str(e)}")
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
# Orchestrator Management
# -----------------------------------------------------------------------------

def get_user_orchestrator(user_id: str) -> CaelOrchestrator:
    """
    Get or create orchestrator for user with memory persistence
    Uses in-memory cache for session persistence
    
    Args:
        user_id: User identifier
        
    Returns:
        CaelOrchestrator instance for the user
    """
    if user_id not in user_orchestrators:
        db_local = init_firebase()
        openai = init_openai()
        
        if not db_local or not openai:
            raise RuntimeError("Services not initialized")
        
        # Create memory storage for user
        memory = MemoryStorage(db_local, user_id)
        
        # Create orchestrator with memory
        orchestrator = CaelOrchestrator(
            user_id=user_id,
            db=db_local,
            openai_client=openai,
            memory_storage=memory
        )
        
        user_orchestrators[user_id] = orchestrator
        logger.info(f"🧠 Created orchestrator with memory for user {user_id}")
    
    return user_orchestrators[user_id]


def clear_user_orchestrator(user_id: str):
    """
    Clear orchestrator from cache (logout/session end)
    
    Args:
        user_id: User identifier
    """
    if user_id in user_orchestrators:
        del user_orchestrators[user_id]
        logger.info(f"🗑️ Cleared orchestrator for user {user_id}")


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def verify_firebase_token(token: str):
    """
    Verify a Firebase ID token and return the decoded payload, or None.
    Ensures Firebase Admin is initialized before verification.
    """
    # Make sure Firebase is initialized
    db_local = init_firebase()
    if not db_local:
        logger.error("Token verification failed: Firebase not initialized")
        return None

    try:
        decoded = auth.verify_id_token(token)
        return decoded
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
    Legacy: Shared OpenAI chat call for Cael (direct, without memory)
    Used only by legacy /chat/message endpoint
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
        "version": "9.0.0-memory",
        "timestamp": datetime.utcnow().isoformat(),
        "features": [
            "Memory Integration ✅",
            "Emotional Intelligence ✅",
            "Personality Adaptation ✅",
            "Safety Monitoring ✅"
        ],
        "endpoints": {
            "health": "/health",
            "index_chat": "/index",
            "auth_verify": "/auth/verify",
            "chat_legacy": "/chat/message",
            "user_profile": "/user/profile",
            "user_onboarding": "/user/onboarding",
            "memory_stats": "/memory/stats",
            "emotional_profile": "/memory/emotional-profile",
            "conversation_summary": "/conversation/summary"
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
        "memory_system": "enabled",
        "active_sessions": len(user_orchestrators),
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
        try:
            doc = db_local.collection("users").document(user_id).get()
            if doc.exists:
                logger.info(f"✅ User profile retrieved for {user_id}")
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
            logger.info(f"✅ Default profile created for {user_id}")
            return jsonify(default_profile)
        except Exception as e:
            logger.error(f"❌ Error retrieving/creating profile: {e}")
            return jsonify({"error": "Profile error"}), 500

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
    
    try:
        db_local.collection("users").document(user_id).set(profile)
        logger.info(f"✅ Profile saved for user {user_id}")
        return jsonify({"success": True, "profile": profile})
    except Exception as e:
        logger.error(f"❌ Failed to save profile: {e}")
        return jsonify({"error": "Failed to save profile"}), 500


@app.route("/user/onboarding", methods=["POST"])
def user_onboarding():
    """
    Complete user onboarding process and save preferences
    """
    user_info, error_response = get_authorized_user()
    if error_response:
        return error_response

    user_id = user_info["uid"]
    logger.info(f"🔄 Starting onboarding for user {user_id}")
    
    db_local = init_firebase()
    if not db_local:
        logger.error("❌ Database unavailable during onboarding")
        return jsonify({"error": "Database unavailable"}), 503

    data = request.get_json(silent=True) or {}
    logger.info(f"📥 Received onboarding data: {json.dumps(data, indent=2)}")
    
    # Build comprehensive onboarding profile
    onboarding_data = {
        "user_id": user_id,
        "email": user_info.get("email"),
        "onboarding_complete": True,
        "cael_initialized": True,
        "completed_at": datetime.utcnow().isoformat(),
        
        # Email verification tracking (captured from Firebase token)
        "email_verified": user_info.get("email_verified", True),
        "email_verified_at": datetime.utcnow().isoformat(),
        
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
        "onboarding_version": "v9_enhanced_memory",
        "personality_profile": data.get("personality_profile", {}),
    }
    
    try:
        # Save to Firestore
        logger.info(f"💾 Attempting to save onboarding data to Firestore...")
        db_local.collection("users").document(user_id).set(
            onboarding_data, 
            merge=True  # Merge with existing profile data
        )
        
        logger.info(f"✅ Onboarding completed and saved for user {user_id}")
        
        return jsonify({
            "success": True,
            "message": "Onboarding completed successfully",
            "veteran_verified": onboarding_data["veteran_profile"].get("is_veteran", False),
            "companion_name": onboarding_data["companion_name"]
        })
        
    except Exception as e:
        logger.error(f"❌ Onboarding save failed for user {user_id}: {e}")
        logger.error(f"❌ Exception details: {type(e).__name__}: {str(e)}")
        return jsonify({"error": f"Failed to save onboarding data: {str(e)}"}), 500


# -------------------------------------------------------------------------
# Main Chat Endpoint with Memory & Personality
# -------------------------------------------------------------------------

@app.route("/index", methods=["POST"])
def index_chat():
    """
    Main chat endpoint with memory and personality integration
    
    Request:
        { "message": "User says..." }
    
    Response:
        { 
            "response": "Cael replies...",
            "metadata": {
                "emotional_intensity": 0.0-1.0,
                "primary_emotion": "string",
                "model_used": "gpt-4",
                "has_followup": boolean,
                "memory_context_used": boolean
            }
        }
    
    (Auth required via Firebase ID token in Authorization: Bearer <token>)
    """
    user_info, error_response = get_authorized_user()
    if error_response:
        return error_response

    user_id = user_info["uid"]
    
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    
    if not message:
        return jsonify({"error": "Message required"}), 400

    try:
        # Get user's orchestrator (with memory and personality)
        logger.info(f"🧠 Processing message for user {user_id} with orchestrator")
        orchestrator = get_user_orchestrator(user_id)
        
        # Process message through orchestrator
        # Note: orchestrator.process_message is async
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                orchestrator.process_message(message)
            )
        finally:
            loop.close()
        
        # Log success
        metadata = result.get('metadata', {})
        logger.info(
            f"✅ Orchestrator response for {user_id}: "
            f"emotion={metadata.get('primary_emotion', 'unknown')}, "
            f"intensity={metadata.get('emotional_intensity', 0):.2f}, "
            f"model={metadata.get('model_used', 'unknown')}"
        )
        
        # Return response in expected format
        return jsonify({
            "response": result['response'],
            "metadata": metadata
        })

    except Exception as e:
        logger.error(f"❌ Orchestrator error in /index for user {user_id}: {e}")
        logger.error(f"❌ Exception details: {type(e).__name__}: {str(e)}")
        
        # Emotionally intelligent fallback
        fallback = (
            "I'm having a moment of technical difficulty, but I'm still here with you. "
            "Could you try saying that again? I want to make sure I give you my full attention."
        )
        return jsonify({
            "response": fallback,
            "metadata": {
                "error": str(e),
                "is_fallback": True,
                "model_used": "fallback"
            }
        })


# -------------------------------------------------------------------------
# Memory & Personality Endpoints
# -------------------------------------------------------------------------

@app.route("/memory/stats", methods=["GET"])
def memory_stats():
    """
    Get user's memory statistics
    
    Returns memory usage, types, and storage info
    """
    user_info, error_response = get_authorized_user()
    if error_response:
        return error_response
    
    user_id = user_info["uid"]
    
    try:
        orchestrator = get_user_orchestrator(user_id)
        stats = orchestrator.memory.get_memory_stats()
        
        logger.info(f"📊 Memory stats retrieved for user {user_id}")
        
        return jsonify({
            "success": True,
            "user_id": user_id,
            "stats": stats,
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ Memory stats error for user {user_id}: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/memory/emotional-profile", methods=["GET"])
def emotional_profile():
    """
    Get user's emotional profile built from memories
    
    Returns communication preferences, emotional patterns, triggers
    """
    user_info, error_response = get_authorized_user()
    if error_response:
        return error_response
    
    user_id = user_info["uid"]
    
    try:
        orchestrator = get_user_orchestrator(user_id)
        profile = orchestrator.memory.get_emotional_profile()
        
        logger.info(f"💙 Emotional profile retrieved for user {user_id}")
        
        return jsonify({
            "success": True,
            "user_id": user_id,
            "profile": profile,
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ Emotional profile error for user {user_id}: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/conversation/summary", methods=["GET"])
def conversation_summary():
    """
    Get summary of current conversation session
    
    Returns message count, emotions, topics, duration
    """
    user_info, error_response = get_authorized_user()
    if error_response:
        return error_response
    
    user_id = user_info["uid"]
    
    try:
        orchestrator = get_user_orchestrator(user_id)
        summary = orchestrator.get_conversation_summary()
        
        logger.info(f"📝 Conversation summary retrieved for user {user_id}")
        
        return jsonify({
            "success": True,
            "user_id": user_id,
            "summary": summary,
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ Conversation summary error for user {user_id}: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/session/clear", methods=["POST"])
def clear_session():
    """
    Clear user's session (logout/end conversation)
    Clears orchestrator from memory but preserves database memories
    """
    user_info, error_response = get_authorized_user()
    if error_response:
        return error_response
    
    user_id = user_info["uid"]
    
    try:
        clear_user_orchestrator(user_id)
        
        logger.info(f"🗑️ Session cleared for user {user_id}")
        
        return jsonify({
            "success": True,
            "message": "Session cleared successfully"
        })
        
    except Exception as e:
        logger.error(f"❌ Session clear error for user {user_id}: {e}")
        return jsonify({"error": str(e)}), 500


# -------------------------------------------------------------------------
# Legacy / debugging endpoint: /chat/message
# -------------------------------------------------------------------------

@app.route("/chat/message", methods=["POST"])
def chat_message():
    """
    Legacy chat endpoint (without memory)
    Kept for backward compatibility and debugging
    Same behaviour as old /index, but without memory integration
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

    try:
        logger.info(f"💾 Saving user message to Firestore (legacy endpoint) for user {user_id}")
        message_ref = db_local.collection("messages").add({
            "user_id": user_id,
            "role": "user",
            "content": message,
            "timestamp": datetime.utcnow().isoformat(),
            "via": "chat.message",
        })
        logger.info(f"✅ User message saved with ID: {message_ref[1].id}")
    except Exception as e:
        logger.error(f"❌ Failed to save user message: {e}")

    try:
        reply = run_cael_completion(message)

        try:
            logger.info(f"💾 Saving assistant response (legacy endpoint)")
            assistant_ref = db_local.collection("messages").add({
                "user_id": user_id,
                "role": "assistant",
                "content": reply,
                "timestamp": datetime.utcnow().isoformat(),
                "model": "gpt-3.5-turbo",
                "via": "chat.message",
            })
            logger.info(f"✅ Assistant message saved with ID: {assistant_ref[1].id}")
        except Exception as e:
            logger.error(f"❌ Failed to save assistant message: {e}")

        return jsonify({"success": True, "response": reply})

    except Exception as e:
        logger.error(f"OpenAI error in /chat/message: {e}")
        fallback = (
            "Cael is having trouble responding right now. "
            "Please try again soon."
        )
        return jsonify({"success": True, "response": fallback, "fallback": True})


# -----------------------------------------------------------------------------
# Startup Initialization
# -----------------------------------------------------------------------------

def initialize_services():
    """Initialize Firebase and OpenAI on startup"""
    logger.info("=" * 60)
    logger.info("🚀 Starting Zentrafuge v9 Backend with Memory Integration")
    logger.info("=" * 60)
    logger.info("🔄 Initializing services on startup...")
    
    # Initialize Firebase
    firebase_db = init_firebase()
    if firebase_db:
        logger.info("✅ Firebase ready for requests")
    else:
        logger.error("❌ Firebase initialization failed")
        logger.error("   Check FIREBASE_CREDENTIALS_JSON environment variable")
    
    # Initialize OpenAI
    openai_client_instance = init_openai()
    if openai_client_instance:
        logger.info("✅ OpenAI ready for requests")
    else:
        logger.error("❌ OpenAI initialization failed")
        logger.error("   Check OPENAI_API_KEY environment variable")
    
    # Check encryption key
    encryption_key = os.getenv('ZENTRAFUGE_MASTER_KEY')
    if encryption_key:
        logger.info("✅ Memory encryption key loaded")
    else:
        logger.warning("⚠️ ZENTRAFUGE_MASTER_KEY not set - will generate temporary key")
        logger.warning("   Set this in production for persistent encryption!")
    
    logger.info("=" * 60)
    logger.info("🧠 Memory System: ENABLED")
    logger.info("💙 Emotional Intelligence: ENABLED")
    logger.info("🔒 Encryption: ENABLED")
    logger.info("=" * 60)
    
    return firebase_db is not None and openai_client_instance is not None


# Initialize services when module loads (not just in __main__)
initialize_services()


# -----------------------------------------------------------------------------
# Entry point
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    logger.info(f"🌐 Starting Flask development server on port {port}")
    logger.info(f"🧠 Memory integration: ACTIVE")
    logger.info(f"💙 Personality system: ACTIVE")
    app.run(host="0.0.0.0", port=port, debug=False)
