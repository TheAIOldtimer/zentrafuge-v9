# backend/utils/memory_engine.py
"""
Zentrafuge v8 Memory Engine
Handles user-scoped memory storage and retrieval with emotional context
+ ZP-1 move awareness (optional fields, non-breaking)
"""

import logging
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

# ----------------------------
# Data models
# ----------------------------

@dataclass
class ConversationMemory:
    """Represents a stored conversation with emotional + ZP-1 context"""
    message_id: str
    timestamp: str
    user_message: str
    cael_reply: str
    emotional_tone: str
    time_since_last: str
    mood_score: Optional[float] = None
    themes: List[str] = None

    # ZP-1 optional metadata (non-breaking)
    zp1_move: Optional[str] = None              # e.g., "reflective_echo"
    zp1_detected_move: Optional[str] = None     # detector output, if different
    feedback_signal: Optional[str] = None       # e.g., 'perfect'|'helpful'|'not_quite'|'unhelpful'

    def __post_init__(self):
        if self.themes is None:
            self.themes = []


@dataclass
class UserProfile:
    """Persistent user identity and preferences"""
    user_id: str
    preferred_name: str
    support_style: str          # "gentle", "direct", "exploratory"
    communication_pace: str     # "slow", "moderate", "responsive"
    trigger_topics: List[str]
    growth_areas: List[str]
    created_at: str
    last_active: str


# ----------------------------
# Public API
# ----------------------------

def retrieve_relevant_memories(
    user_id: str,
    current_message: str,
    firestore_client=None,
    limit: int = 10,
) -> str:
    """
    Returns a short natural-language recall string for the orchestrator.
    Uses 'current_message' (fixed) and biases toward:
      - keyword/theme overlap
      - recency
      - emotion continuity
      - prior memories where the same ZP-1 move got positive feedback
    """
    try:
        if not firestore_client:
            logger.warning("No firestore_client provided to retrieve_relevant_memories")
            return "Memory system temporarily unavailable"

        # Fetch recent memories
        memories = get_user_memories(user_id, firestore_client, limit=limit)
        if not memories:
            return "No previous conversation context found"

        # Score and select top matches
        selected = find_relevant_memories(memories, current_message, limit=3)

        # Format into a concise recall string
        recall = format_memory_recall(selected, current_message=current_message)
        return recall or "No relevant memories found - this feels like a fresh conversation."

    except Exception as e:
        logger.error(f"Memory retrieval error: {e}")
        return "Memory temporarily unavailable"


def store_conversation(
    user_id: str,
    user_message: str,
    cael_reply: str,
    firestore_client,
    emotional_tone: str = "neutral",
    zp1_move: Optional[str] = None,
    zp1_detected_move: Optional[str] = None,
    feedback_signal: Optional[str] = None,
) -> None:
    """
    Store a conversation in user-scoped memory (users/{uid}/messages/{message_id})
    Adds optional ZP-1 fields if provided. Safe no-op if firestore is missing.
    """
    try:
        if not firestore_client:
            logger.warning("No firestore client - conversation not stored")
            return

        # Calculate time since last message for UX context
        time_since_last = calculate_time_since_last(user_id, firestore_client)

        # Create message ID
        now = datetime.utcnow()
        message_id = generate_message_id(user_message, now)

        # Extract themes from the conversation
        themes = extract_conversation_themes(user_message, cael_reply)

        # Build memory object (includes optional ZP-1 metadata)
        memory = ConversationMemory(
            message_id=message_id,
            timestamp=now.isoformat() + "Z",
            user_message=user_message,
            cael_reply=cael_reply,
            emotional_tone=emotional_tone,
            time_since_last=time_since_last,
            themes=themes,
            zp1_move=zp1_move,
            zp1_detected_move=zp1_detected_move,
            feedback_signal=feedback_signal,
        )

        # Persist
        doc_ref = (
            firestore_client.collection("users")
            .document(user_id)
            .collection("messages")
            .document(message_id)
        )
        doc_ref.set(asdict(memory), merge=True)

        logger.info(f"Stored conversation for user {user_id} (msg={message_id})")

    except Exception as e:
        logger.error(f"Error storing conversation: {e}")


def get_user_memories(user_id: str, firestore_client, limit: int = 10) -> List[ConversationMemory]:
    """
    Retrieve recent memories for a user from users/{uid}/messages ordered by timestamp desc
    """
    try:
        messages_ref = (
            firestore_client.collection("users")
            .document(user_id)
            .collection("messages")
        )
        query = messages_ref.order_by("timestamp", direction="DESCENDING").limit(limit)

        memories: List[ConversationMemory] = []
        for doc in query.stream():
            data = doc.to_dict() or {}
            # Backward compatibility: ensure all dataclass fields exist
            cm = ConversationMemory(
                message_id=data.get("message_id", doc.id),
                timestamp=data.get("timestamp", datetime.utcnow().isoformat() + "Z"),
                user_message=data.get("user_message", ""),
                cael_reply=data.get("cael_reply", ""),
                emotional_tone=data.get("emotional_tone", "neutral"),
                time_since_last=data.get("time_since_last", "unknown"),
                mood_score=data.get("mood_score"),
                themes=data.get("themes", []),

                # ZP-1 optional fields
                zp1_move=data.get("zp1_move"),
                zp1_detected_move=data.get("zp1_detected_move"),
                feedback_signal=data.get("feedback_signal"),
            )
            memories.append(cm)

        return memories

    except Exception as e:
        logger.error(f"Error getting user memories: {e}")
        return []


def find_relevant_memories(
    memories: List[ConversationMemory],
    current_input: str,
    limit: int = 3
) -> List[ConversationMemory]:
    """
    Rank memories using keyword matches, theme overlap, recency, emotion continuity,
    and positive reinforcement for previously effective ZP-1 moves.
    """
    current_input_lower = (current_input or "").lower()
    scored: List[tuple[ConversationMemory, float]] = []

    for memory in memories:
        score = calculate_relevance_score(memory, current_input_lower)
        if score > 0:
            scored.append((memory, score))

    scored.sort(key=lambda x: x[1], reverse=True)
    return [m for m, _ in scored[:limit]]


# ----------------------------
# Scoring + Formatting helpers
# ----------------------------

def calculate_relevance_score(memory: ConversationMemory, current_input: str) -> float:
    """
    Calculate how relevant a memory is to current input
    Components:
      + keyword overlap (0.3 each)
      + theme overlap (0.5 each)
      + recency boost (<=1 day +0.3, <=7 days +0.1)
      + emotion continuity (+0.4)
      + ZP-1 reinforcement: if memory.zp1_move == inferred move and feedback positive (+0.5)
    """
    score = 0.0

    # Keyword overlap
    user_words = set((memory.user_message or "").lower().split())
    current_words = set((current_input or "").split())
    keyword_overlap = len(user_words.intersection(current_words))
    score += keyword_overlap * 0.3

    # Theme overlap
    input_themes = extract_themes_from_text(current_input)
    theme_overlap = len(set(memory.themes or []).intersection(set(input_themes)))
    score += theme_overlap * 0.5

    # Recency
    days_ago = calculate_days_since_timestamp(memory.timestamp)
    if days_ago <= 1:
        score += 0.3
    elif days_ago <= 7:
        score += 0.1

    # Emotion continuity
    current_emotion = extract_emotional_keywords(current_input)
    memory_emotion = extract_emotional_keywords(memory.user_message)
    if current_emotion and memory_emotion and current_emotion == memory_emotion:
        score += 0.4

    # ZP-1 reinforcement (lightly speculative without a full detector at retrieval time)
    # If prior memory used a move that got positive feedback, nudge it up.
    if is_positive_feedback(memory.feedback_signal):
        score += 0.2
        # If we can infer a likely move from current input themes, reward direct match more.
        likely_move = infer_likely_move_from_text(current_input)
        if likely_move and (memory.zp1_move == likely_move or memory.zp1_detected_move == likely_move):
            score += 0.3

    return score


def format_memory_recall(memories: List[ConversationMemory], current_message: Optional[str] = None) -> str:
    """
    Format memories into natural language for Cael.
    Includes timestamp context and (if present) subtle ZP-1 cues.
    """
    if not memories:
        return ""

    parts: List[str] = []
    for m in memories:
        time_context = format_time_context(m.timestamp)
        emotion = f" (feeling {m.emotional_tone})" if (m.emotional_tone and m.emotional_tone != "neutral") else ""
        move_hint = ""
        if m.zp1_move:
            move_hint = f" [move: {m.zp1_move}]"
        elif m.zp1_detected_move:
            move_hint = f" [move: {m.zp1_detected_move}]"

        snippet = (m.user_message or "").strip().replace("\n", " ")
        if len(snippet) > 100:
            snippet = snippet[:100] + "..."

        parts.append(f"{time_context}, you shared: \"{snippet}\"{emotion}{move_hint}")

    header = "Relevant memories:"
    if current_message:
        header = "Relevant memories for this topic:"

    return header + "\n" + "\n".join(parts)


# ----------------------------
# Lightweight NLP helpers
# ----------------------------

def extract_conversation_themes(user_message: str, cael_reply: str) -> List[str]:
    """
    Extract thematic content from conversation (keyword-based, fast)
    """
    theme_keywords: Dict[str, List[str]] = {
        "work_stress": ["job", "work", "boss", "career", "workplace", "colleagues"],
        "relationships": ["relationship", "partner", "friend", "family", "dating", "love"],
        "anxiety": ["anxious", "worry", "scared", "nervous", "panic", "stress"],
        "depression": ["sad", "depressed", "hopeless", "empty", "lonely", "down"],
        "growth": ["learning", "growing", "changing", "improving", "progress", "development"],
        "health": ["tired", "sleep", "energy", "exercise", "health", "physical"],
        "creativity": ["creative", "art", "writing", "music", "project", "inspiration"],
        "identity": ["who am I", "purpose", "meaning", "values", "identity", "self"],
    }

    text = f"{user_message} {cael_reply}".lower()
    detected: List[str] = []

    for theme, keywords in theme_keywords.items():
        if any(k in text for k in keywords):
            detected.append(theme)

    return detected[:3]  # Limit to top 3


def extract_themes_from_text(text: str) -> List[str]:
    return extract_conversation_themes(text or "", "")


def extract_emotional_keywords(text: str) -> str:
    """
    Extract a primary emotional keyword from text (keyword-based, deterministic)
    """
    emotional_keywords: Dict[str, List[str]] = {
        "sad": ["sad", "depressed", "down", "blue", "crying"],
        "anxious": ["anxious", "worried", "scared", "nervous", "panic"],
        "angry": ["angry", "mad", "frustrated", "irritated", "furious"],
        "happy": ["happy", "joyful", "excited", "glad", "cheerful"],
        "tired": ["tired", "exhausted", "drained", "weary", "burnout"],
    }

    tl = (text or "").lower()
    for emotion, keywords in emotional_keywords.items():
        if any(k in tl for k in keywords):
            return emotion
    return ""


def infer_likely_move_from_text(text: str) -> Optional[str]:
    """
    Heuristic inference of a candidate move from raw text (fast, optional).
    This is intentionally simple; the proper detector remains in ZP-1 pipeline.
    """
    tl = (text or "").lower()
    if any(k in tl for k in ["confused", "don't get", "not sure", "unclear", "what do you mean"]):
        return "curiosity_bridge"
    if any(k in tl for k in ["anxious", "panic", "overwhelmed", "stressed"]):
        return "grounding_breath"
    if any(k in tl for k in ["thanks", "appreciate", "grateful"]):
        return "gratitude_offering"
    if any(k in tl for k in ["boundary", "can't", "not allowed"]):
        return "gentle_boundary"
    if any(k in tl for k in ["stuck", "loop", "ruminating"]):
        return "compassionate_redirect"
    return None


def is_positive_feedback(signal: Optional[str]) -> bool:
    return (signal or "").lower() in {"perfect", "helpful", "yes", "positive", "good"}


# ----------------------------
# Time helpers
# ----------------------------

def calculate_time_since_last(user_id: str, firestore_client) -> str:
    """
    Calculate time since user's last message
    """
    try:
        messages_ref = (
            firestore_client.collection("users")
            .document(user_id)
            .collection("messages")
        )
        query = messages_ref.order_by("timestamp", direction="DESCENDING").limit(1)
        docs = list(query.stream())
        if not docs:
            return "first_conversation"

        last_ts = (docs[0].to_dict() or {}).get("timestamp")
        if not last_ts:
            return "unknown"

        last_time = datetime.fromisoformat(last_ts.replace('Z', '+00:00'))
        diff = datetime.utcnow() - last_time.replace(tzinfo=None)
        return format_time_difference(diff)

    except Exception as e:
        logger.error(f"Error calculating time since last: {e}")
        return "unknown"


def format_time_difference(time_diff: timedelta) -> str:
    total_seconds = int(time_diff.total_seconds())
    if total_seconds < 60:
        return "just_now"
    if total_seconds < 3600:
        return f"{total_seconds // 60}_minutes_ago"
    if total_seconds < 86400:
        return f"{total_seconds // 3600}_hours_ago"
    return f"{total_seconds // 86400}_days_ago"


def format_time_context(timestamp: str) -> str:
    try:
        t = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        now = datetime.utcnow()
        diff = now - t.replace(tzinfo=None)
        if diff.days == 0:
            return "Earlier today"
        if diff.days == 1:
            return "Yesterday"
        if diff.days < 7:
            return f"{diff.days} days ago"
        return f"{diff.days // 7} weeks ago"
    except Exception:
        return "Recently"


def calculate_days_since_timestamp(timestamp: str) -> int:
    try:
        t = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        now = datetime.utcnow()
        return (now - t.replace(tzinfo=None)).days
    except Exception:
        return 999  # Treat as very old


def generate_message_id(message: str, timestamp: datetime) -> str:
    content = f"{message}_{timestamp.isoformat()}"
    return hashlib.md5(content.encode()).hexdigest()[:12]


# ----------------------------
# User profile helpers
# ----------------------------

def get_user_profile(user_id: str, firestore_client) -> Optional[UserProfile]:
    """
    Retrieve user profile from memory
    """
    try:
        doc_ref = (
            firestore_client.collection("users")
            .document(user_id)
            .collection("memory")
            .document("profile")
        )
        doc = doc_ref.get()
        if doc.exists:
            data = doc.to_dict() or {}
            return UserProfile(**data)
        return None
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        return None


def update_user_profile(profile: UserProfile, firestore_client) -> None:
    """
    Update user profile in memory
    """
    try:
        doc_ref = (
            firestore_client.collection("users")
            .document(profile.user_id)
            .collection("memory")
            .document("profile")
        )
        doc_ref.set(asdict(profile), merge=True)
        logger.info(f"Updated profile for user {profile.user_id}")
    except Exception as e:
        logger.error(f"Error updating user profile: {e}")
