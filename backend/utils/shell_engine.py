# shell_engine.py
"""
Shell Engine: Manages the symbolic shell for emotional growth visualization.
Trauma-informed design - no forced progression, user-controlled emergence.

SAFE MODE: Set SHELL_ENABLED = False to stub out all Firestore calls.
"""

import firebase_admin
from firebase_admin import firestore
from datetime import datetime, timedelta
import logging

# TOGGLE THIS TO ENABLE/DISABLE SHELL FEATURES
SHELL_ENABLED = False  # Set to True when ready to go live

db = firestore.client() if SHELL_ENABLED else None
logger = logging.getLogger(__name__)


def _safe_firestore_call(func):
    """Decorator to stub out Firestore calls when disabled."""
    def wrapper(*args, **kwargs):
        if not SHELL_ENABLED:
            logger.info(f"Shell Engine (STUB): {func.__name__} called but disabled")
            return None
        return func(*args, **kwargs)
    return wrapper


# Then wrap all functions with @_safe_firestore_call
@_safe_firestore_call
def initialize_shell(user_id):
    """Initialize shell state for new user."""
    # ... rest of code stays the same


@_safe_firestore_call
def update_shell_stage(user_id):
    """Update shell visual stage based on growth score."""
    # ... rest of code stays the same

  # shell_engine.py
"""
Shell Engine: Manages the symbolic shell/egg for emotional growth visualization.
Trauma-informed design - no forced progression, user-controlled emergence.
"""

import firebase_admin
from firebase_admin import firestore
from datetime import datetime, timedelta
import logging

db = firestore.client()
logger = logging.getLogger(__name__)


def initialize_shell(user_id):
    """Initialize shell state for new user."""
    user_ref = db.collection('users').document(user_id)
    user_ref.update({
        'shell_state': {
            'stage': 0,
            'texture': 'sealed',
            'cracks': [],
            'glow_intensity': 0.0,
            'last_touch': None,
            'created_at': datetime.now()
        },
        'emergence_ready': False,
        'emergence_offered': False,
        'emergence_accepted': False
    })
    logger.info(f"Shell initialized for user {user_id}")


def calculate_growth_score(user_id):
    """
    Calculate emotional growth score from sentiment history.
    Returns float 0.0-100.0.
    """
    user_ref = db.collection('users').document(user_id)
    doc = user_ref.get()
    
    if not doc.exists:
        return 0.0
    
    data = doc.to_dict()
    sentiment_history = data.get('sentiment_history', [])
    
    if len(sentiment_history) == 0:
        return 0.0
    
    # Weight recent interactions more heavily
    if len(sentiment_history) <= 5:
        # Early boost for engagement
        return min(len(sentiment_history) * 15.0, 100.0)
    
    # Take last 20 interactions
    recent = sentiment_history[-20:]
    
    # Calculate weighted average (more recent = more weight)
    weights = [i / len(recent) for i in range(1, len(recent) + 1)]
    weighted_sum = sum(s * w for s, w in zip(recent, weights))
    weight_total = sum(weights)
    
    avg_sentiment = weighted_sum / weight_total
    
    # Map sentiment (-1 to 1) to growth score (0 to 100)
    # Add baseline for sustained engagement
    engagement_bonus = min(len(sentiment_history) * 2, 30)
    growth = ((avg_sentiment + 1) / 2) * 70 + engagement_bonus
    
    return min(growth, 100.0)


def update_shell_stage(user_id):
    """
    Update shell visual stage based on growth score.
    Returns (stage, growth_score, changed).
    """
    user_ref = db.collection('users').document(user_id)
    doc = user_ref.get()
    data = doc.to_dict()
    
    current_stage = data.get('shell_state', {}).get('stage', 0)
    emergence_accepted = data.get('emergence_accepted', False)
    
    growth = calculate_growth_score(user_id)
    
    # Don't progress past stage 4 until user accepts emergence
    if emergence_accepted:
        max_stage = 5
    else:
        max_stage = 4
    
    # Map growth to stage
    if growth < 20:
        new_stage = 0
    elif growth < 40:
        new_stage = 1
    elif growth < 60:
        new_stage = 2
    elif growth < 80:
        new_stage = 3
    else:
        new_stage = 4
    
    new_stage = min(new_stage, max_stage)
    
    # Update if changed
    changed = new_stage != current_stage
    
    if changed or growth != data.get('growth_score', 0):
        # Calculate glow intensity
        glow = min(growth / 100.0, 1.0)
        
        user_ref.update({
            'shell_state.stage': new_stage,
            'shell_state.glow_intensity': glow,
            'growth_score': growth
        })
        
        logger.info(f"Shell updated for {user_id}: stage {new_stage}, growth {growth:.1f}")
    
    return new_stage, growth, changed


def check_emergence_readiness(user_id):
    """
    Check if user is ready for emergence moment.
    Criteria:
    - Growth score > 75
    - At least 14 days since shell creation
    - Shell touched at least once (user acknowledged it)
    - No recent crisis flags
    - Not already offered
    """
    user_ref = db.collection('users').document(user_id)
    doc = user_ref.get()
    
    if not doc.exists:
        return False
    
    data = doc.to_dict()
    shell_state = data.get('shell_state', {})
    
    # Check if already offered
    if data.get('emergence_offered', False):
        return False
    
    # Check growth score
    growth = data.get('growth_score', 0)
    if growth < 75:
        return False
    
    # Check time since creation
    created_at = shell_state.get('created_at')
    if created_at:
        days_active = (datetime.now() - created_at).days
        if days_active < 14:
            return False
    else:
        return False
    
    # Check if shell acknowledged
    if not shell_state.get('last_touch'):
        return False
    
    # Check for recent crisis flags
    if data.get('recent_crisis', False):
        return False
    
    return True


def offer_emergence(user_id):
    """Mark that emergence has been offered to user."""
    user_ref = db.collection('users').document(user_id)
    user_ref.update({
        'emergence_ready': True,
        'emergence_offered': True,
        'emergence_offer_date': datetime.now()
    })
    logger.info(f"Emergence offered to user {user_id}")


def accept_emergence(user_id):
    """User has accepted emergence - open the shell."""
    user_ref = db.collection('users').document(user_id)
    user_ref.update({
        'emergence_accepted': True,
        'emergence_date': datetime.now(),
        'shell_state.stage': 5,
        'shell_state.texture': 'open'
    })
    logger.info(f"Emergence accepted by user {user_id}")


def touch_shell(user_id):
    """Record that user acknowledged/interacted with shell."""
    user_ref = db.collection('users').document(user_id)
    user_ref.update({
        'shell_state.last_touch': datetime.now()
    })


def set_dedication(user_id, dedicated_to, message=""):
    """Allow user to dedicate their shell to someone/something."""
    user_ref = db.collection('users').document(user_id)
    user_ref.update({
        'dedication': {
            'dedicated_to': dedicated_to,
            'message': message,
            'date': datetime.now()
        }
    })
    logger.info(f"Shell dedicated by user {user_id}")


def get_shell_state(user_id):
    """Get current shell state for display."""
    user_ref = db.collection('users').document(user_id)
    doc = user_ref.get()
    
    if not doc.exists:
        return None
    
    data = doc.to_dict()
    return {
        'stage': data.get('shell_state', {}).get('stage', 0),
        'glow_intensity': data.get('shell_state', {}).get('glow_intensity', 0.0),
        'growth_score': data.get('growth_score', 0.0),
        'emergence_ready': data.get('emergence_ready', False),
        'emergence_accepted': data.get('emergence_accepted', False),
        'dedication': data.get('dedication', {})
    }

# ... etc for all functions
