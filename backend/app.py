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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

# Initialize Firebase Admin SDK
def init_firebase():
    """Initialize Firebase Admin SDK with service account key"""
    try:
        # Check if already initialized
        if not firebase_admin._apps:
            # Try to load from environment variable first (for production)
            service_account_json = os.getenv('FIREBASE_SERVICE_ACCOUNT')
            
            if service_account_json:
                # Parse JSON from environment variable
                service_account_dict = json.loads(service_account_json)
                cred = firebase_admin.credentials.Certificate(service_account_dict)
                firebase_admin.initialize_app(cred)
                logger.info("Firebase Admin SDK initialized from environment variable")
            else:
                # Fall back to file-based approach (for local development)
                service_account_path = 'serviceAccountKey.json'
                if os.path.exists(service_account_path):
                    cred = firebase_admin.credentials.Certificate(service_account_path)
                    firebase_admin.initialize_app(cred)
                    logger.info("Firebase Admin SDK initialized from file")
                else:
                    logger.error("No Firebase credentials found in environment or file")
                    raise FileNotFoundError("Firebase service account key missing")
        
        # Initialize Firestore client
        db = firestore.client()
        return db
    except Exception as e:
        logger.error(f"Firebase initialization failed: {e}")
        raise

# Initialize OpenAI client
def init_openai():
    """Initialize OpenAI client with API key from environment"""
    try:
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        client = openai.OpenAI(api_key=openai_api_key)
        logger.info("OpenAI client initialized successfully")
        return client
    except Exception as e:
        logger.error(f"OpenAI initialization failed: {e}")
        raise

# Global clients
db = None
openai_client = None

# Initialize services on startup
try:
    db = init_firebase()
    openai_client = init_openai()
except Exception as e:
    logger.error(f"Service initialization failed: {e}")
    # App will still start but services won't be available

# Authentication middleware
def verify_firebase_token(token):
    """Verify Firebase ID token and return user info"""
    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        return None

# Root endpoint
@app.route('/', methods=['GET'])
def root():
    """Root endpoint with API information"""
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
        },
        'documentation': 'https://github.com/TheAIOldtimer/zentrafuge-v9'
    })

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring"""
    status = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'services': {
            'firebase': db is not None,
            'openai': openai_client is not None
        }
    }
    return jsonify(status)

# Authentication endpoints
@app.route('/auth/verify', methods=['POST'])
def verify_auth():
    """Verify user authentication token"""
    try:
        data = request.get_json()
        token = data.get('token')
        
        if not token:
            return jsonify({'error': 'Token required'}), 400
        
        user_info = verify_firebase_token(token)
        if not user_info:
            return jsonify({'error': 'Invalid token'}), 401
        
        return jsonify({
            'valid': True,
            'user_id': user_info['uid'],
            'email': user_info.get('email')
        })
    
    except Exception as e:
        logger.error(f"Auth verification error: {e}")
        return jsonify({'error': 'Authentication failed'}), 500

# User profile endpoints
@app.route('/user/profile', methods=['GET'])
def get_user_profile():
    """Get user profile and onboarding state"""
    try:
        # Get auth token from header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authorization token required'}), 401
        
        token = auth_header.split('Bearer ')[1]
        user_info = verify_firebase_token(token)
        if not user_info:
            return jsonify({'error': 'Invalid token'}), 401
        
        user_id = user_info['uid']
        
        # Get user profile from Firestore
        user_doc = db.collection('users').document(user_id).get()
        
        if user_doc.exists:
            profile = user_doc.to_dict()
        else:
            # Create new user profile
            profile = {
                'user_id': user_id,
                'email': user_info.get('email'),
                'created_at': datetime.utcnow().isoformat(),
                'onboarding_complete': False,
                'cael_initialized': False
            }
            db.collection('users').document(user_id).set(profile)
        
        return jsonify(profile)
    
    except Exception as e:
        logger.error(f"Profile retrieval error: {e}")
        return jsonify({'error': 'Failed to get profile'}), 500

@app.route('/user/onboarding', methods=['POST'])
def complete_onboarding():
    """Complete user onboarding process"""
    try:
        # Verify auth
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authorization token required'}), 401
        
        token = auth_header.split('Bearer ')[1]
        user_info = verify_firebase_token(token)
        if not user_info:
            return jsonify({'error': 'Invalid token'}), 401
        
        user_id = user_info['uid']
        data = request.get_json()
        
        # Update user profile with onboarding data
        onboarding_data = {
            'onboarding_complete': True,
            'onboarded_at': datetime.utcnow().isoformat(),
            'preferences': data.get('preferences', {}),
            'cael_name': data.get('cael_name', 'Cael'),
            'communication_style': data.get('communication_style', 'balanced')
        }
        
        db.collection('users').document(user_id).update(onboarding_data)
        
        return jsonify({'success': True, 'message': 'Onboarding completed'})
    
    except Exception as e:
        logger.error(f"Onboarding error: {e}")
        return jsonify({'error': 'Onboarding failed'}), 500

# Chat endpoints
@app.route('/chat/message', methods=['POST'])
def handle_chat_message():
    """Handle incoming chat message and generate AI response"""
    try:
        # Verify auth
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authorization token required'}), 401
        
        token = auth_header.split('Bearer ')[1]
        user_info = verify_firebase_token(token)
        if not user_info:
            return jsonify({'error': 'Invalid token'}), 401
        
        user_id = user_info['uid']
        data = request.get_json()
        message = data.get('message', '').strip()
        
        if not message:
            return jsonify({'error': 'Message required'}), 400
        
        if not openai_client:
            return jsonify({'error': 'AI service unavailable'}), 503
        
        # Store user message
        user_message_doc = {
            'user_id': user_id,
            'role': 'user',
            'content': message,
            'timestamp': datetime.utcnow().isoformat(),
            'message_id': f"user_{datetime.utcnow().timestamp()}"
        }
        
        db.collection('messages').add(user_message_doc)
        
        # Generate AI response (simplified for now)
        try:
            response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",  # Cost-effective fallback model
                messages=[
                    {
                        "role": "system", 
                        "content": "You are Cael, an emotionally intelligent AI companion. You are caring, thoughtful, and focused on the user's wellbeing. Keep responses conversational and supportive."
                    },
                    {"role": "user", "content": message}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            ai_response = response.choices[0].message.content
            
            # Store AI response
            ai_message_doc = {
                'user_id': user_id,
                'role': 'assistant',
                'content': ai_response,
                'timestamp': datetime.utcnow().isoformat(),
                'message_id': f"cael_{datetime.utcnow().timestamp()}",
                'model_used': 'gpt-3.5-turbo',
                'tokens_used': response.usage.total_tokens
            }
            
            db.collection('messages').add(ai_message_doc)
            
            return jsonify({
                'success': True,
                'response': ai_response,
                'message_id': ai_message_doc['message_id'],
                'tokens_used': response.usage.total_tokens
            })
        
        except Exception as openai_error:
            logger.error(f"OpenAI API error: {openai_error}")
            
            # Fallback response
            fallback_response = "I'm having trouble connecting to my AI systems right now. Please try again in a moment."
            
            ai_message_doc = {
                'user_id': user_id,
                'role': 'assistant',
                'content': fallback_response,
                'timestamp': datetime.utcnow().isoformat(),
                'message_id': f"fallback_{datetime.utcnow().timestamp()}",
                'is_fallback': True
            }
            
            db.collection('messages').add(ai_message_doc)
            
            return jsonify({
                'success': True,
                'response': fallback_response,
                'message_id': ai_message_doc['message_id'],
                'is_fallback': True
            })
    
    except Exception as e:
        logger.error(f"Chat message error: {e}")
        return jsonify({'error': 'Failed to process message'}), 500

@app.route('/chat/history', methods=['GET'])
def get_chat_history():
    """Get user's chat history"""
    try:
        # Verify auth
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authorization token required'}), 401
        
        token = auth_header.split('Bearer ')[1]
        user_info = verify_firebase_token(token)
        if not user_info:
            return jsonify({'error': 'Invalid token'}), 401
        
        user_id = user_info['uid']
        
        # Get recent messages (limit to last 50)
        messages_ref = db.collection('messages')\
                        .where('user_id', '==', user_id)\
                        .order_by('timestamp', direction=firestore.Query.DESCENDING)\
                        .limit(50)
        
        messages = []
        for doc in messages_ref.stream():
            message_data = doc.to_dict()
            messages.append(message_data)
        
        # Reverse to get chronological order
        messages.reverse()
        
        return jsonify({
            'success': True,
            'messages': messages,
            'count': len(messages)
        })
    
    except Exception as e:
        logger.error(f"Chat history error: {e}")
        return jsonify({'error': 'Failed to get chat history'}), 500

# Debug and admin endpoints
@app.route('/admin/debug', methods=['GET'])
def debug_info():
    """Debug endpoint for system status"""
    try:
        debug_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'environment': {
                'openai_key_set': bool(os.getenv('OPENAI_API_KEY')),
                'firebase_key_exists': os.path.exists('serviceAccountKey.json'),
                'firebase_env_set': bool(os.getenv('FIREBASE_SERVICE_ACCOUNT'))
            },
            'services': {
                'firebase_initialized': db is not None,
                'openai_initialized': openai_client is not None
            }
        }
        
        return jsonify(debug_data)
    
    except Exception as e:
        logger.error(f"Debug info error: {e}")
        return jsonify({'error': 'Debug info failed'}), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Development server
    app.run(debug=True, host='0.0.0.0', port=5000)
