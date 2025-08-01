#!/usr/bin/env python3
"""
Zentrafuge v9 - Main Flask Backend
Modular, secure, memory-first AI companion architecture
"""

import os
import json
import logging
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import auth, firestore
import openai

# ──────────────── Initialize Flask and Logging ──────────────── #

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ──────────────── Firebase Init ──────────────── #

def init_firebase():
    try:
        if not firebase_admin._apps:
            service_account_json = os.getenv('GOOGLE_APPLICATION_CREDENTIALS') or os.getenv('FIREBASE_SERVICE_ACCOUNT')
            if service_account_json:
                cred = firebase_admin.credentials.Certificate(json.loads(service_account_json))
                firebase_admin.initialize_app(cred)
                logger.info("Firebase initialized from environment")
            else:
                cred_path = 'serviceAccountKey.json'
                if os.path.exists(cred_path):
                    cred = firebase_admin.credentials.Certificate(cred_path)
                    firebase_admin.initialize_app(cred)
                    logger.info("Firebase initialized from file")
                else:
                    raise FileNotFoundError("No Firebase credentials found.")
        return firestore.client()
    except Exception as e:
        logger.error(f"Firebase init failed: {e}")
        return None

db = init_firebase()

# ──────────────── OpenAI Init ──────────────── #

def init_openai():
    try:
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            raise ValueError("OPENAI_API_KEY not set")
        client = openai.OpenAI(api_key=key)
        logger.info("OpenAI client initialized")
        return client
    except Exception as e:
        logger.error(f"OpenAI init failed: {e}")
        return None

openai_client = init_openai()

# ──────────────── Helpers ──────────────── #

def verify_firebase_token(token):
    try:
        return auth.verify_id_token(token)
    except Exception as e:
        logger.error(f"Token verify failed: {e}")
        return None

# ──────────────── ROUTES ──────────────── #

@app.route('/')
def root():
    return jsonify({
        'service': 'Zentrafuge v9 API',
        'status': 'running',
        'version': '9.0.0',
        'timestamp': datetime.utcnow().isoformat(),
        'endpoints': {
            'health': '/health',
            'auth': '/auth/verify',
            'chat': '/chat/message',
            'user': '/user/profile'
        }
    })

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'firebase': db is not None,
        'openai': openai_client is not None,
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/auth/verify', methods=['POST'])
def verify_auth():
    data = request.get_json()
    token = data.get('token')
    if not token:
        return jsonify({'error': 'Token required'}), 400
    user = verify_firebase_token(token)
    if not user:
        return jsonify({'error': 'Invalid token'}), 401
    return jsonify({'valid': True, 'user_id': user['uid'], 'email': user.get('email')})

@app.route('/user/profile', methods=['GET', 'POST'])
def user_profile():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Authorization required'}), 401
    token = auth_header.split(' ')[1]
    user_info = verify_firebase_token(token)
    if not user_info:
        return jsonify({'error': 'Invalid token'}), 401
    user_id = user_info['uid']

    if request.method == 'GET':
        doc = db.collection('users').document(user_id).get()
        if doc.exists:
            return jsonify(doc.to_dict())
        else:
            default_profile = {
                'user_id': user_id,
                'email': user_info.get('email'),
                'created_at': datetime.utcnow().isoformat(),
                'onboarding_complete': False,
                'cael_initialized': False
            }
            db.collection('users').document(user_id).set(default_profile)
            return jsonify(default_profile)

    elif request.method == 'POST':
        data = request.get_json()
        profile = {
            'user_id': user_id,
            'email': user_info.get('email'),
            'full_name': data.get('name', ''),
            'is_veteran': data.get('is_veteran', False),
            'marketing_opt_in': data.get('marketing_opt_in', False),
            'registration_date': data.get('registration_date', datetime.utcnow().isoformat()),
            'created_at': datetime.utcnow().isoformat(),
            'onboarding_complete': False,
            'cael_initialized': False
        }
        db.collection('users').document(user_id).set(profile)
        return jsonify({'success': True, 'profile': profile})

@app.route('/chat/message', methods=['POST'])
def chat():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Authorization required'}), 401
    token = auth_header.split(' ')[1]
    user_info = verify_firebase_token(token)
    if not user_info:
        return jsonify({'error': 'Invalid token'}), 401

    user_id = user_info['uid']
    data = request.get_json()
    message = data.get('message', '').strip()
    if not message:
        return jsonify({'error': 'Message required'}), 400
    if not openai_client:
        return jsonify({'error': 'AI unavailable'}), 503

    db.collection('messages').add({
        'user_id': user_id,
        'role': 'user',
        'content': message,
        'timestamp': datetime.utcnow().isoformat()
    })

    try:
        response = openai_client.chat.comp_
