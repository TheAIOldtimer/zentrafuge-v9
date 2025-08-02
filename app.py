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
from firebase_admin import auth, firestore
import openai

# Initialize Flask and Logging
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables for lazy initialization
db = None
openai_client = None

# Firebase Init
def init_firebase():
    global db
    if db is None:
        start_time = time.time()
        try:
            if not firebase_admin._apps:
                service_account_json = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
                if service_account_json:
                    if service_account_json.strip().startswith('{'):
                        cred = firebase_admin.credentials.Certificate(json.loads(service_account_json))
                    else:
                        cred = firebase_admin.credentials.Certificate(service_account_json)
                    firebase_admin.initialize_app(cred)
                    logger.info(f"Firebase initialized in {time.time() - start_time:.2f} seconds")
                else:
                    raise FileNotFoundError("GOOGLE_APPLICATION_CREDENTIALS not set.")
            db = firestore.client()
        except Exception as e:
            logger.error(f"Firebase init failed: {e}")
            db = None
    return db

# OpenAI Init
def init_openai():
    global openai_client
    if openai_client is None:
        start_time = time.time()
        try:
            key = os.getenv("OPENAI_API_KEY")
            if not key:
                raise ValueError("OPENAI_API_KEY not set")
            openai_client = openai.OpenAI(api_key=key)
            logger.info(f"OpenAI client initialized in {time.time() - start_time:.2f} seconds")
        except Exception as e:
            logger.error(f"OpenAI init failed: {e}")
            openai_client = None
    return openai_client

# Helpers
def verify_firebase_token(token):
    try:
        return auth.verify_id_token(token)
    except Exception as e:
        logger.error(f"Token verify failed: {e}")
        return None

# Routes
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
        'firebase': init_firebase() is not None,
        'openai': init_openai() is not None,
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
    db_local = init_firebase()
    if not db_local:
        return jsonify({'error': 'Database unavailable'}), 503

    if request.method == 'GET':
        doc = db_local.collection('users').document(user_id).get()
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
            db_local.collection('users').document(user_id).set(default_profile)
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
        db_local.collection('users').document(user_id).set(profile)
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
    local_openai = init_openai()
    if not local_openai:
        return jsonify({'error': 'AI unavailable'}), 503
    db_local = init_firebase()
    if not db_local:
        return jsonify({'error': 'Database unavailable'}), 503

    db_local.collection('messages').add({
        'user_id': user_id,
        'role': 'user',
        'content': message,
        'timestamp': datetime.utcnow().isoformat()
    })

    try:
        response = local_openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are Cael, an emotionally intelligent AI companion."},
                {"role": "user", "content": message}
            ],
            max_tokens=500,
            temperature=0.7
        )
        reply = response.choices[0].message.content

        db_local.collection('messages').add({
            'user_id': user_id,
            'role': 'assistant',
            'content': reply,
            'timestamp': datetime.utcnow().isoformat(),
            'model': 'gpt-3.5-turbo'
        })

        return jsonify({'success': True, 'response': reply})

    except Exception as e:
        logger.error(f"OpenAI error: {e}")
        fallback = "Cael is having trouble responding right now. Please try again soon."
        return jsonify({'success': True, 'response': fallback, 'fallback': True})
