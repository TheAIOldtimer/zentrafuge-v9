# backend/utils/emotion_parser.py
"""
Zentrafuge v8 Emotion Parser
Detects emotional tone and underlying states for Cael's responses.
Exports:
- parse_emotions(text) -> "label: low|medium|high"  # used by orchestrator
- parse_emotional_tone(text) -> rich formatted context (for legacy callers)
"""

import re
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class EmotionalSignature:
    """Represents detected emotional state"""
    primary_tone: str
    intensity: float  # 0.0 to 1.0
    underlying_states: List[str]
    masked_emotions: List[str]  # emotions hidden behind surface tone
    energy_level: str  # "low", "moderate", "high"
    regulation_state: str  # "regulated", "dysregulated", "recovering"

# Emotional lexicons for pattern matching
TONE_INDICATORS: Dict[str, List[str]] = {
    "distressed": ["overwhelmed", "breaking", "can't handle", "falling apart", "drowning"],
    "weary": ["tired", "exhausted", "drained", "burnt out", "empty", "heavy"],
    "anxious": ["worried", "scared", "nervous", "panicking", "afraid", "stressed", "anxious"],
    "frustrated": ["angry", "irritated", "fed up", "annoyed", "stuck", "blocked", "frustrated"],
    "sad": ["depressed", "down", "blue", "hopeless", "lonely", "isolated", "sad"],
    "reflective": ["thinking", "wondering", "processing", "contemplating", "considering"],
    "hopeful": ["better", "improving", "optimistic", "looking forward", "excited"],
    "grateful": ["thankful", "appreciative", "blessed", "fortunate", "grateful"],
    "calm": ["peaceful", "centered", "grounded", "stable", "balanced", "serene", "calm"],
    "curious": ["interested", "exploring", "learning", "discovering", "questioning", "curious"],
}

MASKING_PATTERNS: Dict[str, List[str]] = {
    "humor_masking_pain": [r"lol.*but", r"haha.*actually", r"funny.*not really"],
    "minimizing": [r"\bit's fine\b", r"\bno big deal\b", r"\bwhatever\b", r"\bdoesn't matter\b"],
    "deflecting": [r"\banyway\b", r"\bmoving on\b", r"\benough about me\b", r"\bbut how are you\b"],
}

ENERGY_INDICATORS: Dict[str, List[str]] = {
    "low": ["can't", "barely", "struggling", "heavy", "dragging", "no energy"],
    "moderate": ["okay", "managing", "getting by", "doing alright", "fine", "alright"],
    "high": ["excited", "energized", "motivated", "pumped", "ready", "charged"],
}

PROFANITY = {"damn", "shit", "fuck", "hell"}  # signal only; not echoed

# ---------- Public API ----------

def parse_emotions(user_input: str) -> str:
    """
    REQUIRED by orchestrator.
    Returns compact label like: "anxious: medium" or "neutral: medium"
    """
    try:
        sig = analyze_emotional_signature(user_input or "")
        # Bucketize intensity
        if sig.intensity >= 0.75:
            bucket = "high"
        elif sig.intensity >= 0.4:
            bucket = "medium"
        else:
            bucket = "low"
        label = sig.primary_tone if sig.primary_tone else "neutral"
        return f"{label}: {bucket}"
    except Exception as e:
        logger.error(f"parse_emotions error: {e}")
        return "neutral: medium"

def parse_emotional_tone(user_input: str) -> str:
    """
    Legacy-friendly call: returns a human-readable context string.
    """
    try:
        signature = analyze_emotional_signature(user_input or "")
        return format_emotional_context(signature)
    except Exception as e:
        logger.error(f"Error in parse_emotional_tone: {e}")
        return "Emotional tone: Unable to analyze - responding with presence"

# ---------- Core analysis ----------

def analyze_emotional_signature(text: str) -> EmotionalSignature:
    """
    Deep analysis of emotional state from text
    """
    text_lower = (text or "").lower()

    primary_tone = detect_primary_tone(text_lower)
    intensity = calculate_emotional_intensity(text_lower)
    underlying_states = detect_underlying_states(text_lower)
    masked_emotions = detect_masked_emotions(text_lower)
    energy_level = assess_energy_level(text_lower)
    regulation_state = assess_regulation_state(text_lower, intensity)

    return EmotionalSignature(
        primary_tone=primary_tone,
        intensity=intensity,
        underlying_states=underlying_states,
        masked_emotions=masked_emotions,
        energy_level=energy_level,
        regulation_state=regulation_state,
    )

def detect_primary_tone(text: str) -> str:
    """
    Identify the dominant emotional tone (best-match count heuristic)
    """
    tone_scores: Dict[str, int] = {}
    for tone, indicators in TONE_INDICATORS.items():
        score = 0
        for indicator in indicators:
            # word/phrase contains — use substring (fast) plus simple boundaries for single words
            if (" " in indicator and indicator in text) or re.search(rf"\b{re.escape(indicator)}\b", text):
                score += 1
        tone_scores[tone] = score

    if not tone_scores or max(tone_scores.values()) == 0:
        return "neutral"
    # prefer non-neutral over reflective if tied (simple bias)
    best = max(tone_scores, key=tone_scores.get)
    if best == "reflective":
        # look for any non-neutral with the same score
        max_score = tone_scores[best]
        for k, v in tone_scores.items():
            if k != "reflective" and v == max_score:
                return k
    return best

def calculate_emotional_intensity(text: str) -> float:
    """
    Calculate emotional intensity based on language patterns
    """
    high_markers = ["extremely", "incredibly", "totally", "completely", "absolutely", "really really", "so"]
    caps = bool(re.search(r"[A-Z]{2,}", text))
    exclam = text.count("!")
    repetition = bool(re.search(r"(.)\1{2,}", text))  # repeated characters
    swearing = any(w in text for w in PROFANITY)

    base = 0.3
    if any(m in text for m in high_markers):
        base += 0.25
    if caps:
        base += 0.15
    if exclam > 0:
        base += min(0.2, exclam * 0.08)
    if repetition:
        base += 0.1
    if swearing:
        base += 0.15

    return min(1.0, base)

def detect_underlying_states(text: str) -> List[str]:
    """
    Identify underlying emotional states that may not be the primary tone
    """
    states: List[str] = []
    for tone, indicators in TONE_INDICATORS.items():
        if any(((" " in ind and ind in text) or re.search(rf"\b{re.escape(ind)}\b", text)) for ind in indicators):
            states.append(tone)
    # Preserve order by score density but cap to 3 to avoid noise
    return states[:3]

def detect_masked_emotions(text: str) -> List[str]:
    """Detect when someone might be hiding emotions behind surface expressions"""
    masked: List[str] = []
    for pattern_type, patterns in MASKING_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text, flags=re.IGNORECASE):
                masked.append(pattern_type)
                break
    return masked

def assess_energy_level(text: str) -> str:
    """Determine energy level from language patterns"""
    scores: Dict[str, int] = {}
    for level, indicators in ENERGY_INDICATORS.items():
        scores[level] = sum(1 for ind in indicators if ((" " in ind and ind in text) or re.search(rf"\b{re.escape(ind)}\b", text)))
    if not scores or max(scores.values()) == 0:
        return "moderate"
    return max(scores, key=scores.get)

def assess_regulation_state(text: str, intensity: float) -> str:
    """Determine emotional regulation state"""
    dysregulation_indicators = [
        "can't think", "losing it", "falling apart", "out of control",
        "spiraling", "breaking down", "overwhelmed",
    ]
    recovery_indicators = [
        "getting better", "working on", "trying to", "learning to",
        "slowly", "step by step", "taking time",
    ]

    if any(ind in text for ind in dysregulation_indicators) or intensity > 0.8:
        return "dysregulated"
    if any(ind in text for ind in recovery_indicators):
        return "recovering"
    return "regulated"

def format_emotional_context(signature: EmotionalSignature) -> str:
    """
    Format emotional signature into context string for Cael
    """
    # Intensity bucket for readability
    if signature.intensity >= 0.75:
        intensity_bucket = "high"
    elif signature.intensity >= 0.4:
        intensity_bucket = "medium"
    else:
        intensity_bucket = "low"

    parts = [
        f"Primary tone: {signature.primary_tone}",
        f"Intensity: {intensity_bucket} ({signature.intensity:.2f})",
        f"Energy: {signature.energy_level}",
        f"Regulation: {signature.regulation_state}",
    ]

    if signature.underlying_states:
        parts.append(f"Underlying: {', '.join(signature.underlying_states[:2])}")
    if signature.masked_emotions:
        parts.append(f"Possible masking: {', '.join(signature.masked_emotions)}")

    return " | ".join(parts)

# Utility function for debugging
def get_detailed_analysis(text: str) -> Dict[str, Any]:
    """
    Return detailed emotional analysis for debugging and QA
    """
    sig = analyze_emotional_signature(text or "")
    raw_scores = {
        tone: sum(1 for ind in indicators if ((" " in ind and ind in text.lower()) or re.search(rf"\b{re.escape(ind)}\b", text.lower())))
        for tone, indicators in TONE_INDICATORS.items()
    }
    return {
        "text": text,
        "signature": {
            "primary_tone": sig.primary_tone,
            "intensity": sig.intensity,
            "underlying_states": sig.underlying_states,
            "masked_emotions": sig.masked_emotions,
            "energy_level": sig.energy_level,
            "regulation_state": sig.regulation_state,
        },
        "formatted_context": format_emotional_context(sig),
        "raw_tone_scores": raw_scores,
    }
