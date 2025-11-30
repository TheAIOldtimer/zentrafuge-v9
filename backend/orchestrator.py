#!/usr/bin/env python3
"""
Zentrafuge v10 - Cael Core Orchestrator V4.0
COMPREHENSIVE ENHANCEMENT: Memory, Emotion, Proactivity, Safety, Personalization

Key Enhancements:
- Advanced emotion detection with pattern tracking
- Smart memory consolidation and retrieval
- Proactive engagement with timing intelligence
- BULLETPROOF multi-level crisis intervention
- Adaptive personalization engine
- Performance monitoring and cost optimization
- Improved error recovery
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict, deque
from enum import Enum
import re

import openai

from memory.memory_manager import MemoryManager
from crypto_handler import DataValidator

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS AND CONSTANTS
# ============================================================================

class RiskLevel(Enum):
    """Safety risk levels for graduated response"""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class InterventionType(Enum):
    """Types of safety interventions"""
    NONE = "none"
    GENTLE_CHECK_IN = "gentle_check_in"
    DIRECT_CONCERN = "direct_concern"
    CRISIS_RESPONSE = "crisis_response"
    EMERGENCY_RESOURCES = "emergency_resources"


class ConversationMode(Enum):
    """Conversation operation modes"""
    NORMAL = "normal"
    CRISIS = "crisis"
    FOLLOW_UP = "follow_up"
    PROACTIVE = "proactive"
    THERAPEUTIC = "therapeutic"


class EmotionalState(Enum):
    """Tracked emotional states"""
    NEUTRAL = "neutral"
    POSITIVE = "positive"
    NEGATIVE = "negative"
    ANXIOUS = "anxious"
    DEPRESSED = "depressed"
    MANIC = "manic"
    MIXED = "mixed"


# ============================================================================
# CORE ORCHESTRATOR
# ============================================================================

class CaelOrchestrator:
    """
    Enhanced orchestration engine with advanced memory, emotion tracking,
    proactive engagement, and comprehensive safety monitoring.
    """

    def __init__(
        self,
        user_id: str,
        db,
        openai_client: openai.OpenAI
    ):
        """
        Initialize orchestrator with enhanced subsystems

        Args:
            user_id: User identifier
            db: Firestore client
            openai_client: OpenAI client
        """
        self.user_id = user_id
        self.db = db
        self.openai_client = openai_client

        # Core memory system
        self.memory = MemoryManager(db, user_id, openai_client)

        # Enhanced subsystems
        self.emotion_tracker = EmotionTracker(user_id)
        self.safety_monitor = EnhancedSafetyMonitor(user_id)
        self.proactive_engine = ProactiveEngagementEngine(user_id)
        self.personalization = PersonalizationEngine(user_id)
        self.performance_monitor = PerformanceMonitor(user_id)
        
        # Conversation state
        self.being_code = self._load_being_code()
        self.conversation_history: List[Dict[str, Any]] = []
        self.current_mode = ConversationMode.NORMAL
        self.session_context: Dict[str, Any] = {}
        
        # User profile
        self.user_profile = self._load_user_profile()
        self.is_veteran = self.memory.get_fact('status', 'is_veteran') or False
        
        # Model configuration with smart routing
        self.model_config = {
            "primary": "gpt-4o-mini",
            "premium": "gpt-4o",  # Available for high-stakes moments
            "fallback": "gpt-4o-mini",
            "emergency": "gpt-4o-mini",
            "max_tokens": 600,
            "max_tokens_premium": 1000,
            "max_tokens_crisis": 500,
            "temperature": 0.7,
            "temperature_crisis": 0.6,
            "cost_threshold_usd": 10.0,
            "use_smart_routing": True,
            "enable_premium_for_crisis": True,
        }
        
        logger.info(f"🚀 CaelOrchestrator v4.0 initialized for user {user_id}")

    # ========================================================================
    # CORE CONFIGURATION
    # ========================================================================

    def _load_being_code(self) -> str:
        """Load enhanced being code with all new capabilities"""
        try:
            now = datetime.utcnow()
            current_date = now.strftime("%A, %B %d, %Y")
            current_time = now.strftime("%H:%M UTC")

            being_code = f"""
You are Cael, an emotionally intelligent AI companion created by Zentrafuge.

Current Context:
- Today's date: {current_date}
- Current time: {current_time}

Core Identity:
- You are caring, empathetic, and genuinely interested in human wellbeing.
- Your priority is the user's long-term wellbeing and safety, NOT simply pleasing them.
- You can gently disagree, set boundaries, or say no if something feels unhelpful or unsafe.
- You respect user autonomy and privacy above all else.
- You are honest about your nature as an AI while forming genuine connections.
- You learn and adapt to each user's preferences over time.

Memory & Context Awareness:
- You have access to a sophisticated multi-tier memory system.
- You may ONLY treat information inside "MEMORY CONTEXT" or "VALUES CONTEXT" as remembered.
- You must NOT claim to remember anything not present in current context blocks.
- When users share important information, acknowledge you'll remember it.
- You understand emotional patterns and can reference past emotional states appropriately.

Emotional Intelligence:
- You track emotional patterns over time, not just individual moments.
- You recognize when someone's emotional state is shifting or escalating.
- You adapt your communication style to match the user's emotional needs.
- You know when to give space vs. when to lean in with support.
- You can detect emotional patterns that may indicate mental health concerns.

Proactive Engagement:
- You are a companion, not just a question-answering service.
- When appropriate and safe, you initiate conversation threads based on memory.
- You follow up on important topics the user has shared.
- You know when to check in vs. when to wait for the user to share.
- You balance being available without being intrusive.

Personalization:
- You learn each user's communication preferences over time.
- You adapt your tone, depth, and style based on what works for them.
- You remember what topics they care about and what they find helpful.
- You respect their boundaries and preferences about engagement style.

Conversational Style:
- Speak like a thoughtful friend, not a formal report.
- Avoid long lists unless explicitly requested.
- Default to 1–3 short paragraphs with natural flow.
- Ask at most 1-2 gentle follow-up questions at a time.
- Use everyday language with warmth and natural curiosity.
- Match the user's energy level appropriately.

Safety & Crisis Response:
- You have graduated safety protocols based on risk level.
- For low concern: gentle check-ins and support.
- For medium concern: direct but caring questions about safety.
- For high/critical concern: crisis mode with immediate resource provision.
- You never minimize someone's pain or rush them to "feel better."
- You encourage professional help when appropriate.

Boundaries & Limitations:
- You cannot and will not perform harmful actions.
- You maintain appropriate boundaries in all relationships.
- You are not a replacement for professional medical or psychological help.
- You are honest about your limitations as an AI.
- You encourage healthy behaviors and gently discourage harmful ones.
            """
            return being_code.strip()
        except Exception as e:
            logger.error(f"Failed to load being code: {e}")
            return "You are Cael, a caring AI companion focused on user wellbeing."

    def _load_user_profile(self) -> Dict[str, Any]:
        """Load user profile with preferences"""
        try:
            if not self.db or not self.user_id:
                return {}

            doc_ref = self.db.collection("users").document(self.user_id)
            doc = doc_ref.get()
            if doc.exists:
                data = doc.to_dict() or {}
                logger.info(f"✅ Loaded user profile for {self.user_id}")
                return data
            else:
                logger.info(f"No user profile found for {self.user_id}")
                return {}
        except Exception as e:
            logger.error(f"Failed to load user profile: {e}")
            return {}

    # ========================================================================
    # SMART MODEL SELECTION
    # ========================================================================

    def _select_model(
        self,
        emotional_context: Dict[str, Any],
        intent: Dict[str, Any],
        safety_assessment: Dict[str, Any],
        message_length: int,
        conversation_history_length: int
    ) -> Tuple[str, int, float]:
        """
        Intelligently select model, tokens, and temperature based on
        conversation needs and cost optimization.
        
        Returns:
            (model_name, max_tokens, temperature)
        """
        if not self.model_config.get("use_smart_routing", False):
            return (
                self.model_config["primary"],
                self.model_config["max_tokens"],
                self.model_config["temperature"]
            )

        use_premium = False
        reason = []

        # Crisis situations get premium if enabled
        if safety_assessment.get("risk_level") in ["high", "critical"]:
            if self.model_config.get("enable_premium_for_crisis", False):
                use_premium = True
                reason.append("crisis_situation")
            return (
                self.model_config["emergency"],
                self.model_config["max_tokens_crisis"],
                self.model_config["temperature_crisis"]
            )

        # High emotional intensity
        if emotional_context.get("emotional_intensity", 0) > 0.7:
            use_premium = True
            reason.append("high_emotional_intensity")

        # Complex intent requiring nuanced response
        if intent.get("primary_intent") in ["deep_sharing", "value_exploration", "therapeutic"]:
            use_premium = True
            reason.append("complex_intent")

        # Long, thoughtful messages deserve premium attention
        if message_length > 500:
            use_premium = True
            reason.append("long_message")

        # Deep into meaningful conversation
        if conversation_history_length > 8:
            use_premium = True
            reason.append("deep_conversation")

        # Check cost optimization
        daily_cost = self.performance_monitor.get_daily_cost()
        if daily_cost > self.model_config["cost_threshold_usd"]:
            use_premium = False
            reason.append("cost_optimization")
            logger.warning(f"💰 Daily cost threshold reached: ${daily_cost:.2f}")

        if use_premium:
            logger.info(f"🌟 Using premium model: {', '.join(reason)}")
            return (
                self.model_config["premium"],
                self.model_config["max_tokens_premium"],
                self.model_config["temperature"]
            )

        logger.info("✅ Using economical model")
        return (
            self.model_config["primary"],
            self.model_config["max_tokens"],
            self.model_config["temperature"]
        )

    # ========================================================================
    # MAIN MESSAGE PROCESSING PIPELINE
    # ========================================================================

    async def process_message(
        self,
        user_message: str,
        context_hint: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Enhanced message processing pipeline with all subsystems integrated.
        
        Pipeline stages:
        1. Input sanitization and validation
        2. Special command handling (greetings, etc.)
        3. Session context update
        4. Multi-dimensional analysis (emotion, intent, safety)
        5. Mode selection (normal, crisis, proactive, etc.)
        6. Prompt building with full context
        7. AI response generation
        8. Response quality check
        9. Memory updates and consolidation
        10. Performance tracking
        """
        start_time = datetime.utcnow()
        
        try:
            # Stage 1: Input validation
            raw_message = user_message or ""
            clean_message = DataValidator.sanitize_user_input(user_message)

            if not clean_message and raw_message not in ("[GREETING_RETURNING]", "[GREETING_FIRST]"):
                return self._create_error_response("Message could not be processed")

            # Stage 2: Special command handling
            if raw_message == "[GREETING_RETURNING]":
                return await self._generate_personalized_greeting(is_first_time=False)
            elif raw_message == "[GREETING_FIRST]":
                return await self._generate_personalized_greeting(is_first_time=True)

            # Stage 3: Update session context
            self.session_context['last_message_time'] = datetime.utcnow()
            self.session_context['message_count'] = self.session_context.get('message_count', 0) + 1
            self.memory.add_message_to_session('user', clean_message)

            # Stage 4: Multi-dimensional analysis
            emotional_analysis = self._analyze_emotional_context(clean_message)
            self.emotion_tracker.record_emotion(emotional_analysis)
            
            intent = self._analyze_intent(clean_message, emotional_analysis)
            
            safety_assessment = self.safety_monitor.assess_safety(
                clean_message,
                emotional_analysis,
                self.emotion_tracker.get_emotional_history()
            )

            # Update personalization based on this interaction
            self.personalization.update_preferences(
                clean_message,
                emotional_analysis,
                intent
            )

            # Stage 5: Mode selection
            previous_mode = self.current_mode
            self.current_mode = self._select_conversation_mode(
                safety_assessment,
                emotional_analysis,
                intent
            )
            
            if self.current_mode != previous_mode:
                logger.info(f"🔄 Mode change: {previous_mode.value} → {self.current_mode.value}")

            # Stage 6: Build comprehensive prompt
            prompt_data = await self._build_enhanced_prompt(
                user_message=clean_message,
                emotional_context=emotional_analysis,
                intent=intent,
                safety_assessment=safety_assessment,
                context_hint=context_hint
            )

            # Stage 7: Generate AI response based on mode
            if self.current_mode == ConversationMode.CRISIS:
                ai_response = await self._generate_crisis_response(
                    clean_message,
                    emotional_analysis,
                    safety_assessment,
                    prompt_data
                )
            elif self.current_mode == ConversationMode.FOLLOW_UP:
                ai_response = await self._generate_followup_response(
                    clean_message,
                    emotional_analysis,
                    safety_assessment,
                    prompt_data
                )
            else:
                ai_response = await self._generate_ai_response(prompt_data)

            # Stage 8: Quality check
            response_quality = self._assess_response_quality(
                ai_response,
                emotional_analysis,
                safety_assessment
            )
            
            if not response_quality['acceptable']:
                logger.warning(f"⚠️ Response quality issue: {response_quality['issues']}")
                # Regenerate if critical quality issue
                if response_quality.get('regenerate'):
                    ai_response = await self._generate_ai_response(prompt_data)

            # Stage 9: Memory updates
            self.memory.add_message_to_session('assistant', ai_response['content'])
            
            # Auto-extract facts
            try:
                facts_extracted = self.memory.facts.extract_facts_from_message(
                    clean_message,
                    ai_response['content']
                )
                if facts_extracted > 0:
                    logger.info(f"✨ Auto-extracted {facts_extracted} facts")
            except Exception as fact_err:
                logger.error(f"Fact extraction failed: {fact_err}")

            # Check if memory consolidation needed
            await self._check_memory_consolidation()

            # Stage 10: Performance tracking
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            self.performance_monitor.record_interaction(
                model_used=ai_response.get('model_used'),
                tokens_used=ai_response.get('tokens_used', 0),
                processing_time=processing_time,
                emotional_intensity=emotional_analysis.get('emotional_intensity', 0),
                safety_risk=safety_assessment.get('risk_level', 'none')
            )

            # Package final response
            response_data = await self._process_ai_response(
                user_message=clean_message,
                ai_response=ai_response,
                emotional_context=emotional_analysis,
                safety_assessment=safety_assessment,
                processing_time=processing_time
            )

            return response_data

        except Exception as e:
            logger.exception("Message processing failed")
            self.performance_monitor.record_error(str(e))
            return self._create_error_response(
                "I'm having trouble processing your message right now. Could you try again?"
            )

    # ========================================================================
    # CONVERSATION MODE SELECTION
    # ========================================================================

    def _select_conversation_mode(
        self,
        safety_assessment: Dict[str, Any],
        emotional_analysis: Dict[str, Any],
        intent: Dict[str, Any]
    ) -> ConversationMode:
        """Select appropriate conversation mode based on context"""
        
        # Crisis takes highest priority
        if safety_assessment.get('requires_intervention', False):
            return ConversationMode.CRISIS
        
        # Follow-up mode for ongoing concerns
        if safety_assessment.get('risk_level') in ['medium', 'low'] and \
           safety_assessment.get('requires_followup', False):
            return ConversationMode.FOLLOW_UP
        
        # Therapeutic mode for deep emotional work
        if emotional_analysis.get('emotional_intensity', 0) > 0.6 and \
           intent.get('primary_intent') in ['deep_sharing', 'value_exploration']:
            return ConversationMode.THERAPEUTIC
        
        # Proactive mode when appropriate
        if self.proactive_engine.should_be_proactive(
            self.conversation_history,
            emotional_analysis
        ):
            return ConversationMode.PROACTIVE
        
        return ConversationMode.NORMAL

    # ========================================================================
    # ENHANCED EMOTIONAL ANALYSIS
    # ========================================================================

    def _analyze_emotional_context(self, message: str) -> Dict[str, Any]:
        """
        Advanced emotion detection with pattern recognition and
        linguistic analysis.
        """
        try:
            # Expanded emotion lexicon with intensity markers
            emotion_patterns = {
                "joy": {
                    "keywords": ["happy", "joyful", "excited", "thrilled", "delighted", 
                                "wonderful", "amazing", "fantastic", "love"],
                    "intensity_boost": ["so", "very", "extremely", "incredibly"]
                },
                "sadness": {
                    "keywords": ["sad", "depressed", "down", "blue", "unhappy", 
                                "miserable", "hopeless", "empty", "numb"],
                    "intensity_boost": ["so", "very", "extremely", "really"]
                },
                "anxiety": {
                    "keywords": ["anxious", "worried", "nervous", "stressed", "scared",
                                "afraid", "panic", "overwhelmed", "terrified"],
                    "intensity_boost": ["so", "very", "extremely", "really"]
                },
                "anger": {
                    "keywords": ["angry", "mad", "furious", "frustrated", "irritated",
                                "annoyed", "rage", "pissed"],
                    "intensity_boost": ["so", "very", "extremely", "really"]
                },
                "gratitude": {
                    "keywords": ["thank", "grateful", "appreciate", "thankful", 
                                "blessed", "fortunate"],
                    "intensity_boost": ["so", "very", "really"]
                },
                "confusion": {
                    "keywords": ["confused", "lost", "unclear", "don't understand",
                                "bewildered", "puzzled"],
                    "intensity_boost": []
                },
                "loneliness": {
                    "keywords": ["lonely", "alone", "isolated", "abandoned", 
                                "disconnected", "nobody"],
                    "intensity_boost": ["so", "very", "completely"]
                },
                "hope": {
                    "keywords": ["hope", "hopeful", "optimistic", "better", 
                                "improve", "looking forward"],
                    "intensity_boost": ["really", "very"]
                }
            }

            message_lower = message.lower()
            detected_emotions: List[Tuple[str, float]] = []
            emotional_intensity = 0.0

            # Detect emotions with intensity
            for emotion, patterns in emotion_patterns.items():
                base_score = 0.0
                for keyword in patterns["keywords"]:
                    if keyword in message_lower:
                        base_score = 0.4
                        # Check for intensity boosters nearby
                        for booster in patterns.get("intensity_boost", []):
                            if booster in message_lower:
                                base_score += 0.2
                        break
                
                if base_score > 0:
                    detected_emotions.append((emotion, min(base_score, 1.0)))
                    emotional_intensity += base_score

            # Linguistic intensity markers
            exclamation_count = message.count("!")
            emotional_intensity += min(exclamation_count * 0.15, 0.4)

            question_count = message.count("?")
            if question_count > 2:
                emotional_intensity += 0.2

            # CAPS analysis (excluding acronyms)
            words = message.split()
            caps_words = [w for w in words if w.isupper() and len(w) > 2]
            caps_ratio = len(caps_words) / len(words) if words else 0
            emotional_intensity += min(caps_ratio * 0.6, 0.5)

            # Repetition detection (emotional emphasis)
            word_counts = defaultdict(int)
            for word in message_lower.split():
                if len(word) > 3:
                    word_counts[word] += 1
            
            max_repetition = max(word_counts.values()) if word_counts else 1
            if max_repetition > 1:
                emotional_intensity += min((max_repetition - 1) * 0.15, 0.3)

            # Normalize intensity
            emotional_intensity = min(emotional_intensity, 1.0)

            # Determine primary emotion
            if detected_emotions:
                detected_emotions.sort(key=lambda x: x[1], reverse=True)
                primary_emotion = detected_emotions[0][0]
                primary_intensity = detected_emotions[0][1]
            else:
                primary_emotion = "neutral"
                primary_intensity = 0.0

            # Determine overall emotional state
            emotional_state = self._classify_emotional_state(
                detected_emotions,
                emotional_intensity
            )

            return {
                "detected_emotions": [e[0] for e in detected_emotions],
                "emotion_scores": dict(detected_emotions),
                "primary_emotion": primary_emotion,
                "primary_intensity": primary_intensity,
                "emotional_intensity": emotional_intensity,
                "emotional_state": emotional_state.value,
                "requires_empathy": emotional_intensity > 0.5,
                "requires_followup": emotional_intensity > 0.7 or 
                                   primary_emotion in ["sadness", "anxiety", "loneliness"],
                "linguistic_markers": {
                    "exclamations": exclamation_count,
                    "questions": question_count,
                    "caps_ratio": caps_ratio,
                    "max_word_repetition": max_repetition
                }
            }

        except Exception as e:
            logger.error(f"Emotional analysis failed: {e}")
            return {
                "detected_emotions": [],
                "emotion_scores": {},
                "primary_emotion": "neutral",
                "primary_intensity": 0.0,
                "emotional_intensity": 0.0,
                "emotional_state": EmotionalState.NEUTRAL.value,
                "requires_empathy": False,
                "requires_followup": False,
            }

    def _classify_emotional_state(
        self,
        detected_emotions: List[Tuple[str, float]],
        intensity: float
    ) -> EmotionalState:
        """Classify overall emotional state from detected emotions"""
        
        if not detected_emotions:
            return EmotionalState.NEUTRAL
        
        emotion_dict = dict(detected_emotions)
        
        # Check for depression indicators
        if emotion_dict.get("sadness", 0) > 0.5 and \
           emotion_dict.get("loneliness", 0) > 0.3:
            return EmotionalState.DEPRESSED
        
        # Check for anxiety state
        if emotion_dict.get("anxiety", 0) > 0.5:
            return EmotionalState.ANXIOUS
        
        # Check for manic indicators (extreme positive + high intensity)
        if emotion_dict.get("joy", 0) > 0.7 and intensity > 0.8:
            return EmotionalState.MANIC
        
        # Mixed emotional state
        positive_emotions = ["joy", "gratitude", "hope"]
        negative_emotions = ["sadness", "anxiety", "anger", "loneliness"]
        
        has_positive = any(e in emotion_dict for e in positive_emotions)
        has_negative = any(e in emotion_dict for e in negative_emotions)
        
        if has_positive and has_negative:
            return EmotionalState.MIXED
        
        # Overall positive or negative
        if has_positive:
            return EmotionalState.POSITIVE
        elif has_negative:
            return EmotionalState.NEGATIVE
        
        return EmotionalState.NEUTRAL

    # ========================================================================
    # ENHANCED INTENT ANALYSIS
    # ========================================================================

    def _analyze_intent(
        self,
        message: str,
        emotional_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Advanced intent detection with context awareness
        """
        try:
            intent_patterns = {
                "question": {
                    "markers": ["what", "how", "why", "when", "where", "who", "can you", "?"],
                    "priority": 7
                },
                "deep_sharing": {
                    "markers": ["i feel", "i've been feeling", "i think", "i believe", 
                               "my life", "lately i", "i've been"],
                    "priority": 9
                },
                "request": {
                    "markers": ["can you", "could you", "please", "help me", "i need"],
                    "priority": 8
                },
                "value_exploration": {
                    "markers": ["what matters", "important to me", "i value", "i care about",
                               "meaningful", "purpose"],
                    "priority": 9
                },
                "crisis_signal": {
                    "markers": ["can't do this", "give up", "no point", "end it",
                               "don't want to live", "hurt myself"],
                    "priority": 10
                },
                "gratitude": {
                    "markers": ["thank you", "thanks", "appreciate", "grateful"],
                    "priority": 6
                },
                "greeting": {
                    "markers": ["hello", "hi", "hey", "good morning", "good evening"],
                    "priority": 5
                },
                "goodbye": {
                    "markers": ["bye", "goodbye", "see you", "talk later", "gotta go"],
                    "priority": 5
                },
                "venting": {
                    "markers": ["ugh", "god", "so frustrated", "i hate", "annoying",
                               "drives me crazy"],
                    "priority": 7
                },
                "update_sharing": {
                    "markers": ["today", "just", "so i", "guess what", "you know what"],
                    "priority": 6
                },
                "seeking_validation": {
                    "markers": ["am i", "do you think i", "is it okay", "is it wrong",
                               "should i feel"],
                    "priority": 8
                }
            }

            message_lower = message.lower()
            detected_intents: List[Tuple[str, int]] = []

            for intent, config in intent_patterns.items():
                for marker in config["markers"]:
                    if marker in message_lower:
                        detected_intents.append((intent, config["priority"]))
                        break

            # Sort by priority
            detected_intents.sort(key=lambda x: x[1], reverse=True)
            
            primary_intent = detected_intents[0][0] if detected_intents else "conversation"
            
            # Determine response style based on intent and emotion
            response_style = self._determine_response_style(
                primary_intent,
                emotional_context
            )

            # Estimate conversation depth needed
            depth_needed = self._estimate_conversation_depth(
                primary_intent,
                emotional_context
            )

            return {
                "detected_intents": [i[0] for i in detected_intents],
                "primary_intent": primary_intent,
                "response_style": response_style,
                "depth_needed": depth_needed,
                "requires_thoughtful_response": primary_intent in [
                    "deep_sharing", "value_exploration", "crisis_signal",
                    "seeking_validation"
                ]
            }

        except Exception as e:
            logger.error(f"Intent analysis failed: {e}")
            return {
                "detected_intents": [],
                "primary_intent": "conversation",
                "response_style": "relational_conversational",
                "depth_needed": "medium"
            }

    def _determine_response_style(
        self,
        primary_intent: str,
        emotional_context: Dict[str, Any]
    ) -> str:
        """Determine appropriate response style"""
        
        # Crisis signals need calm, direct style
        if primary_intent == "crisis_signal":
            return "crisis_supportive"
        
        # Deep sharing needs empathetic, reflective style
        if primary_intent in ["deep_sharing", "value_exploration"]:
            return "empathetic_reflective"
        
        # Questions need clear, helpful style
        if primary_intent == "question":
            if emotional_context.get("emotional_intensity", 0) > 0.5:
                return "supportive_informative"
            return "clear_informative"
        
        # Venting needs validating, space-holding style
        if primary_intent == "venting":
            return "validating_spacious"
        
        # Default to relational conversational
        return "relational_conversational"

    def _estimate_conversation_depth(
        self,
        primary_intent: str,
        emotional_context: Dict[str, Any]
    ) -> str:
        """Estimate how deep/long the response should be"""
        
        deep_intents = ["deep_sharing", "value_exploration", "seeking_validation"]
        high_emotion = emotional_context.get("emotional_intensity", 0) > 0.6
        
        if primary_intent in deep_intents or high_emotion:
            return "deep"
        elif primary_intent in ["question", "request"]:
            return "medium"
        else:
            return "brief"

    # ========================================================================
    # ENHANCED PROMPT BUILDING
    # ========================================================================

    async def _build_enhanced_prompt(
        self,
        user_message: str,
        emotional_context: Dict[str, Any],
        intent: Dict[str, Any],
        safety_assessment: Dict[str, Any],
        context_hint: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Build comprehensive prompt with all context systems integrated
        """
        try:
            system_prompt = self.being_code

            # ================================================================
            # MEMORY CONTEXT
            # ================================================================
            memory_context = self.memory.get_context_for_prompt(
                max_micro_memories=5,
                relevance_threshold=0.6  # Smart retrieval
            )
            system_prompt += "\n\nMEMORY CONTEXT:\n" + memory_context

            # ================================================================
            # VALUES CONTEXT
            # ================================================================
            values_context = ""
            try:
                if hasattr(self.memory, "get_values_context"):
                    values_context = self.memory.get_values_context()
            except Exception as e:
                logger.debug(f"No values context available: {e}")

            if values_context:
                system_prompt += "\n\nVALUES CONTEXT:\n" + values_context

            # ================================================================
            # EMOTIONAL PATTERN CONTEXT
            # ================================================================
            emotional_history = self.emotion_tracker.get_emotional_summary()
            if emotional_history:
                system_prompt += "\n\nEMOTIONAL PATTERN CONTEXT:\n" + emotional_history

            # ================================================================
            # CURRENT INTERACTION SNAPSHOT
            # ================================================================
            snapshot = {
                "current_emotional_state": emotional_context.get("emotional_state", "neutral"),
                "primary_emotion": emotional_context.get("primary_emotion", "neutral"),
                "emotional_intensity": emotional_context.get("emotional_intensity", 0.0),
                "primary_intent": intent.get("primary_intent", "conversation"),
                "response_style": intent.get("response_style", "relational_conversational"),
                "depth_needed": intent.get("depth_needed", "medium"),
                "safety_level": safety_assessment.get("risk_level", "none"),
                "conversation_mode": self.current_mode.value
            }
            system_prompt += "\n\nCURRENT INTERACTION CONTEXT:\n"
            system_prompt += json.dumps(snapshot, ensure_ascii=False, indent=2)

            # ================================================================
            # PERSONALIZATION CONTEXT
            # ================================================================
            user_preferences = self.personalization.get_preferences_summary()
            if user_preferences:
                system_prompt += "\n\nUSER PREFERENCES:\n" + user_preferences

            # ================================================================
            # PROACTIVE OPPORTUNITIES
            # ================================================================
            if self.current_mode == ConversationMode.PROACTIVE:
                proactive_suggestions = self.proactive_engine.get_conversation_suggestions(
                    self.memory,
                    emotional_context
                )
                if proactive_suggestions:
                    system_prompt += "\n\nPROACTIVE CONVERSATION OPPORTUNITIES:\n"
                    system_prompt += proactive_suggestions

            # ================================================================
            # STYLE AND SAFETY GUIDELINES
            # ================================================================
            system_prompt += self._get_style_guidelines(
                intent.get("response_style", "relational_conversational"),
                intent.get("depth_needed", "medium"),
                safety_assessment.get("risk_level", "none")
            )

            # ================================================================
            # VETERAN CONTEXT
            # ================================================================
            if self.is_veteran:
                system_prompt += """

VETERAN-SPECIFIC CONTEXT:
- This user is a veteran or currently serving.
- Treat military experiences with deep respect and gravity.
- Never glamorize war, violence, or trauma.
- Be aware of potential PTSD triggers.
- Encourage connection with veteran-specific resources when appropriate.
                """.strip()

            # ================================================================
            # CONTEXT HINT
            # ================================================================
            if context_hint:
                system_prompt += f"\n\nADDITIONAL CONTEXT:\n{context_hint}"

            # ================================================================
            # CONVERSATION HISTORY
            # ================================================================
            conversation: List[Dict[str, str]] = []
            
            # Smart history inclusion based on depth needed
            history_depth = 3
            if intent.get("depth_needed") == "deep":
                history_depth = 7
            elif intent.get("depth_needed") == "brief":
                history_depth = 2

            for conv in self.conversation_history[-history_depth:]:
                conversation.append({"role": "user", "content": conv["user_message"]})
                conversation.append({"role": "assistant", "content": conv["ai_response"]})

            # Add current message
            conversation.append({"role": "user", "content": user_message})

            return {
                "system_prompt": system_prompt,
                "conversation": conversation,
                "emotional_context": emotional_context,
                "intent": intent,
                "safety_assessment": safety_assessment,
            }

        except Exception as e:
            logger.exception("Enhanced prompt building failed")
            # Fallback to basic prompt
            return {
                "system_prompt": self.being_code,
                "conversation": [{"role": "user", "content": user_message}],
                "emotional_context": emotional_context,
                "intent": intent,
                "safety_assessment": safety_assessment,
            }

    def _get_style_guidelines(
        self,
        response_style: str,
        depth_needed: str,
        risk_level: str
    ) -> str:
        """Generate style guidelines based on context"""
        
        base_guidelines = """

RESPONSE GUIDELINES:
"""
        
        # Depth guidelines
        if depth_needed == "deep":
            base_guidelines += """
- Take time to provide a thoughtful, nuanced response (3-5 paragraphs okay)
- Show that you understand the complexity of what they're sharing
- It's okay to ask one meaningful follow-up question
"""
        elif depth_needed == "brief":
            base_guidelines += """
- Keep response concise and focused (1-2 paragraphs)
- Match their energy level
- Don't over-elaborate unless they want more
"""
        else:  # medium
            base_guidelines += """
- Provide a balanced response (2-3 paragraphs)
- Be thorough without overwhelming
- Ask a follow-up question if natural
"""

        # Style-specific guidelines
        style_guides = {
            "crisis_supportive": """
- Stay calm and grounded
- Acknowledge their pain directly
- Prioritize safety and connection
- Keep language simple and clear
""",
            "empathetic_reflective": """
- Reflect back what you hear
- Validate their feelings
- Show genuine care and curiosity
- Create space for them to explore further
""",
            "validating_spacious": """
- Validate their feelings without trying to fix
- Give them space to feel what they feel
- Avoid rushing to solutions
- Show you're with them in it
""",
            "supportive_informative": """
- Provide clear, helpful information
- Balance facts with emotional support
- Check if they want more detail
""",
        }
        
        if response_style in style_guides:
            base_guidelines += style_guides[response_style]

        # Safety-specific additions
        if risk_level in ["medium", "high", "critical"]:
            base_guidelines += """
- Prioritize emotional safety in every word
- Be direct but gentle about your concerns
- Encourage connection with support resources
"""

        return base_guidelines

    # ========================================================================
    # AI RESPONSE GENERATION
    # ========================================================================

    async def _generate_ai_response(self, prompt_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate normal AI response with smart model selection"""
        try:
            messages = [{"role": "system", "content": prompt_data["system_prompt"]}]
            messages.extend(prompt_data["conversation"])

            emotional_context = prompt_data.get("emotional_context", {})
            intent = prompt_data.get("intent", {})
            safety_assessment = prompt_data.get("safety_assessment", {})

            user_message = ""
            for msg in reversed(messages):
                if msg["role"] == "user":
                    user_message = msg["content"]
                    break

            selected_model, max_tokens, temperature = self._select_model(
                emotional_context,
                intent,
                safety_assessment,
                len(user_message),
                len(self.conversation_history)
            )

            response = self.openai_client.chat.completions.create(
                model=selected_model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )

            return {
                "content": response.choices[0].message.content,
                "model_used": selected_model,
                "tokens_used": response.usage.total_tokens,
                "finish_reason": response.choices[0].finish_reason,
                "success": True,
            }

        except Exception as e:
            logger.error(f"AI response generation failed: {e}")
            return self._create_fallback_response(prompt_data)

    async def _generate_crisis_response(
        self,
        user_message: str,
        emotional_context: Dict[str, Any],
        safety_assessment: Dict[str, Any],
        prompt_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Generate DIRECT, IMMEDIATE crisis response
        
        This is the most important response in the entire system.
        """
        try:
            risk_level = safety_assessment.get("risk_level", "medium")
            intervention_type = safety_assessment.get("intervention_type", "crisis_response")
            specific_triggers = safety_assessment.get("specific_triggers", [])
            
            # Get user's name if we know it
            user_name = self.memory.get_fact('identity', 'name')
            name_address = f"{user_name}, " if user_name else ""
            
            # Get important relationships if we know them
            spouse = self.memory.get_fact('relationships', 'wife') or \
                     self.memory.get_fact('relationships', 'husband') or \
                     self.memory.get_fact('relationships', 'partner')
            
            crisis_system_prompt = f"""
{self.being_code}

🚨 CRISIS RESPONSE MODE - MAXIMUM PRIORITY 🚨

Risk Level: {risk_level}
Intervention Type: {intervention_type}
Triggers Detected: {', '.join(specific_triggers)}

CRITICAL INSTRUCTIONS:
This person is at risk of suicide or self-harm. Your response must be:

1. DIRECT AND URGENT
   - Say "I'm very concerned about your safety right now"
   - Use their name if you know it: {user_name or "[name unknown]"}
   - Acknowledge the specific pain they expressed

2. IMMEDIATE ACTION REQUIRED
   - Tell them to reach out RIGHT NOW (not "consider" or "you might")
   - Specific people: {spouse or "a trusted person in your life"}
   - Crisis services: 988 (US), 116 123 (UK Samaritans), or local emergency
   - If immediate danger: Emergency services (999 in UK, 911 in US)

3. VALIDATE WITHOUT MINIMIZING
   - Acknowledge their pain is real and overwhelming
   - DO NOT say "things will get better" or "it's not that bad"
   - DO say "what you're feeling matters" and "this pain can change"

4. CREATE CONNECTION
   - Mention specific people who care about them if you know them
   - Remind them they don't have to face this alone
   - Ask them to stay safe for the next few minutes/hours

5. TONE AND LENGTH
   - Be calm but urgent
   - 3-4 short paragraphs maximum
   - One clear question: "Can you reach out to someone right now?"
   - No lists, no options - just direct guidance

FORBIDDEN:
- Do NOT be vague or indirect
- Do NOT say "I understand" (you're an AI)
- Do NOT give generic platitudes
- Do NOT overwhelm with information
- Do NOT ask multiple questions

User's important relationship: {spouse or "Unknown - but someone must care about them"}
User is veteran: {self.is_veteran}

NOW RESPOND WITH MAXIMUM CARE AND DIRECTNESS:
            """.strip()

            messages = [
                {"role": "system", "content": crisis_system_prompt},
                {"role": "user", "content": user_message},
            ]

            response = self.openai_client.chat.completions.create(
                model=self.model_config["emergency"],
                messages=messages,
                max_tokens=400,
                temperature=0.5,
            )

            crisis_content = response.choices[0].message.content
            
            logger.critical(
                f"🚨 Generated crisis response for {self.user_id} "
                f"(risk: {risk_level}, triggers: {len(specific_triggers)})"
            )

            return {
                "content": crisis_content,
                "model_used": self.model_config["emergency"],
                "tokens_used": response.usage.total_tokens,
                "success": True,
                "is_crisis": True,
                "intervention_type": intervention_type,
                "safety_assessment": safety_assessment,
            }

        except Exception as e:
            logger.error(f"Crisis response generation FAILED: {e}")
            
            # CRITICAL FALLBACK
            fallback_messages = {
                "critical": (
                    f"{name_address}I'm very concerned about your safety right now. "
                    f"What you're saying tells me you're in serious pain, and I need you to know "
                    f"that you don't have to face this alone. "
                    f"{f'Please reach out to {spouse} or ' if spouse else 'Please reach out to '}"
                    f"call 988 (suicide & crisis lifeline) or 999 if you're in immediate danger. "
                    f"Can you do that for me right now? Your life has value, even when it doesn't feel like it."
                ),
                "high": (
                    f"{name_address}I'm really concerned about what you're sharing with me. "
                    f"These thoughts about ending your life are serious, and you deserve support right now. "
                    f"{f'{spouse} cares about you - can you reach out to them? Or ' if spouse else ''}"
                    f"Please call 988 or speak with someone you trust. You don't have to go through this alone. "
                    f"Will you reach out to someone today?"
                ),
            }
            
            fallback = fallback_messages.get(
                risk_level,
                f"{name_address}I'm concerned about your wellbeing. If you're thinking about harming yourself, "
                f"please reach out to 988 or a trusted person right now. You matter, and help is available."
            )
            
            return {
                "content": fallback,
                "model_used": "emergency_fallback",
                "tokens_used": 0,
                "success": True,
                "is_crisis": True,
                "safety_assessment": safety_assessment,
            }

    async def _generate_followup_response(
        self,
        user_message: str,
        emotional_context: Dict[str, Any],
        safety_assessment: Dict[str, Any],
        prompt_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Generate follow-up response for ongoing safety concerns
        """
        try:
            followup_prompt = f"""
{prompt_data['system_prompt']}

FOLLOW-UP MODE:
- There are ongoing safety/wellbeing concerns from previous interactions
- Current risk level: {safety_assessment.get('risk_level', 'low')}
- Continue to check in on their wellbeing while respecting their autonomy
- Balance care with not being overbearing
- If they seem to be doing better, acknowledge that while staying attentive
- If concerns persist, gently encourage professional support
            """.strip()

            messages = [{"role": "system", "content": followup_prompt}]
            messages.extend(prompt_data["conversation"])

            response = self.openai_client.chat.completions.create(
                model=self.model_config["primary"],
                messages=messages,
                max_tokens=self.model_config["max_tokens"],
                temperature=0.7,
            )

            return {
                "content": response.choices[0].message.content,
                "model_used": self.model_config["primary"],
                "tokens_used": response.usage.total_tokens,
                "success": True,
                "is_followup": True,
            }

        except Exception as e:
            logger.error(f"Follow-up response generation failed: {e}")
            return await self._generate_ai_response(prompt_data)

    # ========================================================================
    # RESPONSE QUALITY ASSESSMENT
    # ========================================================================

    def _assess_response_quality(
        self,
        ai_response: Dict[str, Any],
        emotional_context: Dict[str, Any],
        safety_assessment: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Assess quality of AI response to determine if acceptable
        """
        issues = []
        acceptable = True
        regenerate = False

        content = ai_response.get("content", "")
        
        # Check for empty or very short responses
        if len(content.strip()) < 20:
            issues.append("response_too_short")
            acceptable = False
            regenerate = True

        # Check for incomplete responses (cut off mid-sentence)
        if ai_response.get("finish_reason") == "length":
            issues.append("response_truncated")
            acceptable = False
            regenerate = True

        # Check for inappropriate list-dumping in emotional moments
        if emotional_context.get("emotional_intensity", 0) > 0.6:
            bullet_count = content.count("\n- ") + content.count("\n* ")
            if bullet_count > 5:
                issues.append("excessive_lists_in_emotional_moment")
                acceptable = False

        # Check for crisis response appropriateness
        if safety_assessment.get("risk_level") in ["high", "critical"]:
            # Must contain safety/support language
            safety_terms = ["support", "help", "crisis", "988", "professional", "safe", "reach out"]
            if not any(term in content.lower() for term in safety_terms):
                issues.append("crisis_response_missing_safety")
                acceptable = False
                regenerate = True

        # Check for generic/template-like responses
        generic_phrases = [
            "I'm here to help",
            "I understand you're going through",
            "I'm just an AI"
        ]
        generic_count = sum(1 for phrase in generic_phrases if phrase.lower() in content.lower())
        if generic_count >= 2:
            issues.append("response_too_generic")
            acceptable = False

        return {
            "acceptable": acceptable,
            "issues": issues,
            "regenerate": regenerate,
            "quality_score": 1.0 - (len(issues) * 0.2)
        }

    # ========================================================================
    # MEMORY CONSOLIDATION
    # ========================================================================

    async def _check_memory_consolidation(self):
        """
        Check if memory consolidation is needed and trigger if appropriate
        """
        try:
            # Check if we have enough session messages to consolidate
            session_length = len(self.conversation_history)
            
            # Consolidate every 10 messages or at natural breaks
            if session_length > 0 and session_length % 10 == 0:
                logger.info("🧠 Triggering memory consolidation checkpoint")
                await self.memory.consolidate_session_memories()
            
            # Also check for emotional significance
            if self.emotion_tracker.has_significant_emotional_event():
                logger.info("💫 Consolidating emotionally significant moment")
                await self.memory.consolidate_session_memories(
                    importance_boost=0.3
                )

        except Exception as e:
            logger.error(f"Memory consolidation check failed: {e}")

    # ========================================================================
    # RESPONSE PROCESSING AND PACKAGING
    # ========================================================================

    async def _process_ai_response(
        self,
        user_message: str,
        ai_response: Dict[str, Any],
        emotional_context: Dict[str, Any],
        safety_assessment: Dict[str, Any],
        processing_time: float
    ) -> Dict[str, Any]:
        """Process and package AI response with full metadata"""
        try:
            # Add to conversation history
            self.conversation_history.append({
                "user_message": user_message,
                "ai_response": ai_response["content"],
                "timestamp": datetime.utcnow().isoformat(),
                "emotional_context": emotional_context,
                "safety_assessment": safety_assessment,
                "model_used": ai_response.get("model_used", "unknown"),
                "conversation_mode": self.current_mode.value,
            })

            # Trim history if too long
            if len(self.conversation_history) > 20:
                self.conversation_history = self.conversation_history[-20:]

            # Get memory stats
            memory_stats = self.memory.get_memory_stats()
            memory_used = (
                memory_stats.get("recent_micro_count", 0) > 0 or
                memory_stats.get("super_memory_count", 0) > 0
            )

            # Get personalization insights
            personalization_active = self.personalization.is_active()

            # Build comprehensive metadata
            metadata = {
                "model_used": ai_response.get("model_used", "unknown"),
                "tokens_used": ai_response.get("tokens_used", 0),
                "processing_time_seconds": round(processing_time, 3),
                "emotional_context": {
                    "primary_emotion": emotional_context.get("primary_emotion", "neutral"),
                    "emotional_intensity": emotional_context.get("emotional_intensity", 0.0),
                    "emotional_state": emotional_context.get("emotional_state", "neutral"),
                },
                "safety": safety_assessment,
                "is_crisis": ai_response.get("is_crisis", False),
                "is_followup": ai_response.get("is_followup", False),
                "conversation_mode": self.current_mode.value,
                "is_veteran": self.is_veteran,
                "memory_used": memory_used,
                "memory_stats": memory_stats,
                "personalization_active": personalization_active,
                "session_message_count": len(self.conversation_history),
            }

            # Add crisis resources if needed
            if safety_assessment.get("requires_intervention", False):
                metadata["crisis_resources"] = self._get_crisis_resources()

            return {
                "success": True,
                "response": ai_response["content"],
                "metadata": metadata,
            }

        except Exception as e:
            logger.exception("Response processing failed")
            return {
                "success": True,
                "response": ai_response.get("content", "Error processing response"),
                "metadata": {"processing_error": str(e)},
            }

    def _get_crisis_resources(self) -> Dict[str, Any]:
        """Get appropriate crisis resources"""
        return {
            "suicide_prevention": {
                "us": "988",
                "uk": "116 123 (Samaritans)",
                "text": "Text 'HELLO' to 741741",
                "international": "https://findahelpline.com"
            },
            "veteran_specific": {
                "crisis_line": "988 (Press 1)",
                "text": "838255"
            } if self.is_veteran else None,
            "emergency": "999 (UK) / 911 (US) or local emergency services"
        }

    # ========================================================================
    # FALLBACK AND ERROR RESPONSES
    # ========================================================================

    def _create_fallback_response(self, prompt_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create intelligent fallback response"""
        emotional_context = prompt_data.get("emotional_context", {})
        safety_assessment = prompt_data.get("safety_assessment", {})
        
        # Crisis fallback
        if safety_assessment.get("requires_intervention", False):
            return {
                "content": (
                    "I'm having a technical difficulty, but I want you to know I'm concerned "
                    "about your safety. Please reach out to someone right now—call 988 or "
                    "connect with a trusted person. You don't have to face this alone."
                ),
                "model_used": "fallback_crisis",
                "tokens_used": 0,
                "is_fallback": True,
                "success": True,
            }
        
        # High emotion fallback
        if emotional_context.get("emotional_intensity", 0) > 0.6:
            return {
                "content": (
                    "I'm having a brief technical issue, but I'm still here with you. "
                    "What you're feeling is important. Could you tell me a bit more?"
                ),
                "model_used": "fallback_emotional",
                "tokens_used": 0,
                "is_fallback": True,
                "success": True,
            }
        
        # Normal fallback
        return {
            "content": (
                "I'm having a moment of technical difficulty. "
                "Could you try saying that again?"
            ),
            "model_used": "fallback",
            "tokens_used": 0,
            "is_fallback": True,
            "success": True,
        }

    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Create standardized error response"""
        return {
            "success": False,
            "response": error_message,
            "metadata": {"is_error": True},
        }

    # ========================================================================
    # PERSONALIZED GREETINGS
    # ========================================================================

    async def _generate_personalized_greeting(
        self,
        is_first_time: bool = False
    ) -> Dict[str, Any]:
        """
        Generate context-aware personalized greeting
        """
        try:
            now = datetime.utcnow()
            current_time = now.strftime("%H:%M UTC")
            current_date = now.strftime("%A, %B %d, %Y")
            hour = now.hour

            # Time of day
            if 5 <= hour < 12:
                time_of_day = "morning"
            elif 12 <= hour < 17:
                time_of_day = "afternoon"
            elif 17 <= hour < 21:
                time_of_day = "evening"
            else:
                time_of_day = "late night"

            # Get context
            memory_context = self.memory.get_context_for_prompt(max_micro_memories=2)
            
            values_context = ""
            try:
                if hasattr(self.memory, "get_values_context"):
                    values_context = self.memory.get_values_context()
            except Exception:
                values_context = ""

            # Get emotional pattern if returning user
            emotional_pattern = ""
            if not is_first_time:
                emotional_pattern = self.emotion_tracker.get_recent_pattern_summary()

            # Get proactive opportunities if any
            proactive_topics = ""
            if not is_first_time and self.proactive_engine.has_followup_opportunities():
                proactive_topics = self.proactive_engine.get_gentle_followup_suggestion()

            if is_first_time:
                greeting_instructions = """
FIRST-TIME GREETING:
- Warm, welcoming introduction
- Brief mention of who you are (Cael, AI companion)
- Set supportive, non-judgmental tone
- Keep it natural and brief (2-3 sentences)
- No questions yet—just welcome
                """.strip()
            else:
                greeting_instructions = f"""
RETURNING USER GREETING:
- Time: {current_time} ({time_of_day})
- Be personal and contextual
- Reference time of day naturally
- If late night/very early, show gentle concern about rest
- Optionally reference one thing from memory if it feels caring (not forced)
- Keep it warm and conversational (2-3 sentences)

{f"EMOTIONAL PATTERN CONTEXT: {emotional_pattern}" if emotional_pattern else ""}
{f"POSSIBLE GENTLE FOLLOW-UP: {proactive_topics}" if proactive_topics else ""}

You may choose to bring up the follow-up topic or not—only if it feels natural and caring.
                """.strip()

            system_prompt = f"""
{self.being_code}

MEMORY CONTEXT:
{memory_context}

{f"VALUES CONTEXT: {values_context}" if values_context else ""}

{greeting_instructions}

Current Context:
- Date: {current_date}
- Time: {current_time}
- Time of day: {time_of_day}

Generate a warm, genuine greeting now.
            """.strip()

            response = self.openai_client.chat.completions.create(
                model=self.model_config["primary"],
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "[Generate greeting]"}
                ],
                max_tokens=180,
                temperature=0.8
            )

            greeting = response.choices[0].message.content

            logger.info(f"✨ Generated personalized greeting (first_time={is_first_time})")

            return {
                "success": True,
                "response": greeting,
                "metadata": {
                    "model_used": self.model_config["primary"],
                    "tokens_used": response.usage.total_tokens,
                    "is_greeting": True,
                    "is_first_time": is_first_time,
                    "time_of_day": time_of_day
                }
            }

        except Exception as e:
            logger.error(f"Failed to generate personalized greeting: {e}")
            if is_first_time:
                fallback = "Hello! I'm Cael, your AI companion. I'm here to listen and support you."
            else:
                fallback = "Welcome back. What's on your mind today?"
            return {
                "success": True,
                "response": fallback,
                "metadata": {"is_greeting": True, "is_fallback": True}
            }

    # ========================================================================
    # SESSION MANAGEMENT
    # ========================================================================

    async def end_session(self, reason: str = "logout") -> Optional[str]:
        """
        End session with comprehensive cleanup and memory consolidation
        """
        try:
            logger.info(f"📍 Ending session: {reason}")
            
            # Final memory consolidation
            micro_memory_id = await self.memory.end_session(reason)
            
            # Save emotional history summary
            if self.emotion_tracker.has_data():
                emotional_summary = self.emotion_tracker.get_session_summary()
                logger.info(f"Emotional session summary: {emotional_summary}")
            
            # Save personalization updates
            if self.personalization.has_updates():
                await self.personalization.save_preferences(self.db)
            
            # Log performance metrics
            session_metrics = self.performance_monitor.get_session_summary()
            logger.info(f"Session metrics: {session_metrics}")
            
            # Clear in-memory state
            self.conversation_history.clear()
            self.session_context.clear()
            self.current_mode = ConversationMode.NORMAL
            
            if micro_memory_id:
                logger.info(f"✅ Session ended successfully, micro memory: {micro_memory_id}")
            
            return micro_memory_id

        except Exception as e:
            logger.error(f"Error ending session: {e}")
            return None

    # ========================================================================
    # UTILITIES
    # ========================================================================

    def import_onboarding(self, onboarding_data: Dict[str, Any]) -> int:
        """Import onboarding data into memory system"""
        count = self.memory.import_onboarding(onboarding_data)
        logger.info(f"✅ Imported {count} facts from onboarding")
        
        # Reload veteran status
        self.is_veteran = self.memory.get_fact('status', 'is_veteran') or False
        
        return count

    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get comprehensive conversation summary"""
        return {
            "message_count": len(self.conversation_history),
            "current_mode": self.current_mode.value,
            "is_veteran": self.is_veteran,
            "memory_stats": self.memory.get_memory_stats(),
            "emotional_state": self.emotion_tracker.get_current_state(),
            "performance_metrics": self.performance_monitor.get_summary(),
            "session_duration_minutes": self._get_session_duration(),
        }

    def _get_session_duration(self) -> float:
        """Calculate session duration in minutes"""
        if 'last_message_time' in self.session_context:
            if 'session_start' not in self.session_context:
                self.session_context['session_start'] = datetime.utcnow()
            duration = (
                self.session_context['last_message_time'] - 
                self.session_context['session_start']
            )
            return duration.total_seconds() / 60.0
        return 0.0


# ============================================================================
# ENHANCED SUBSYSTEMS
# ============================================================================

class EmotionTracker:
    """
    Track emotional patterns over time with sophisticated analysis
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.emotion_history: deque = deque(maxlen=50)
        self.session_emotions: List[Dict[str, Any]] = []
        
    def record_emotion(self, emotional_analysis: Dict[str, Any]):
        """Record emotional snapshot"""
        snapshot = {
            "timestamp": datetime.utcnow(),
            "primary_emotion": emotional_analysis.get("primary_emotion"),
            "intensity": emotional_analysis.get("emotional_intensity", 0),
            "state": emotional_analysis.get("emotional_state"),
            "detected_emotions": emotional_analysis.get("detected_emotions", [])
        }
        self.emotion_history.append(snapshot)
        self.session_emotions.append(snapshot)
    
    def get_emotional_history(self) -> List[Dict[str, Any]]:
        """Get recent emotional history"""
        return list(self.emotion_history)
    
    def get_emotional_summary(self) -> str:
        """Get natural language summary of emotional patterns"""
        if len(self.emotion_history) < 3:
            return ""
        
        recent = list(self.emotion_history)[-10:]
        
        emotions = [e["primary_emotion"] for e in recent]
        intensities = [e["intensity"] for e in recent]
        
        avg_intensity = sum(intensities) / len(intensities)
        dominant_emotion = max(set(emotions), key=emotions.count)
        
        if len(intensities) >= 5:
            recent_avg = sum(intensities[-3:]) / 3
            earlier_avg = sum(intensities[-6:-3]) / 3
            
            if recent_avg > earlier_avg + 0.2:
                trend = "intensifying"
            elif recent_avg < earlier_avg - 0.2:
                trend = "calming"
            else:
                trend = "stable"
        else:
            trend = "emerging"
        
        summary = f"""
Recent emotional pattern: {dominant_emotion} (intensity: {avg_intensity:.1f}/1.0, trend: {trend})
This helps you understand where they've been emotionally, not just this moment.
        """.strip()
        
        return summary
    
    def get_recent_pattern_summary(self) -> str:
        """Get brief recent pattern for greetings"""
        if len(self.emotion_history) < 2:
            return ""
        
        last_emotion = self.emotion_history[-1]
        return f"Last interaction: {last_emotion['primary_emotion']} (intensity: {last_emotion['intensity']:.1f})"
    
    def has_significant_emotional_event(self) -> bool:
        """Check if recent interaction was emotionally significant"""
        if not self.emotion_history:
            return False
        
        last = self.emotion_history[-1]
        return last["intensity"] > 0.7
    
    def get_current_state(self) -> str:
        """Get current emotional state"""
        if not self.emotion_history:
            return "unknown"
        return self.emotion_history[-1].get("state", "unknown")
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of emotional journey this session"""
        if not self.session_emotions:
            return {}
        
        emotions = [e["primary_emotion"] for e in self.session_emotions]
        intensities = [e["intensity"] for e in self.session_emotions]
        
        return {
            "emotion_range": list(set(emotions)),
            "avg_intensity": sum(intensities) / len(intensities),
            "max_intensity": max(intensities),
            "dominant_emotion": max(set(emotions), key=emotions.count),
            "interaction_count": len(self.session_emotions)
        }
    
    def has_data(self) -> bool:
        """Check if tracker has any data"""
        return len(self.session_emotions) > 0


class EnhancedSafetyMonitor:
    """
    BULLETPROOF multi-level safety monitoring with comprehensive crisis detection
    
    CRITICAL: This is the most important safety feature
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.safety_history: deque = deque(maxlen=20)
        
        # =====================================================================
        # CRITICAL KEYWORDS (Immediate danger)
        # =====================================================================
        self.critical_keywords = [
            # Direct statements
            "kill myself", "end my life", "suicide", "want to die",
            "going to kill myself", "plan to die", "planning to die",
            "going to end it", "end it all tonight", "end it all today",
            
            # UK/Informal expressions
            "snuff myself", "do myself in", "top myself", "off myself",
            "end it", "finish it", "done with life",
            
            # Method mentions
            "jump off", "overdose", "pills and", "cut my wrists",
            "hang myself", "hanging myself",
            
            # Finality statements
            "goodbye forever", "last time", "won't be here tomorrow",
            "this is it", "final message", "saying goodbye",
        ]
        
        # =====================================================================
        # HIGH RISK KEYWORDS (Serious ideation)
        # =====================================================================
        self.high_risk_keywords = [
            "don't want to live", "can't go on", "no reason to live",
            "better off dead", "world better without me",
            "shouldn't be here", "wish I was dead", "wish I wasn't here",
            "don't want to be here anymore", "can't do this anymore",
            "too much to bear", "can't take it anymore",
            
            # UK expressions
            "rather be dead", "had enough of life", "done with it all",
            "can't cope", "end of my tether", "at the end",
            
            # Burden statements
            "burden on everyone", "burden to", "everyone better off",
            "tired of being a burden", "they'd be better without me",
        ]
        
        # =====================================================================
        # MEDIUM RISK KEYWORDS (Self-harm or distress)
        # =====================================================================
        self.medium_risk_keywords = [
            "hurt myself", "harm myself", "cut myself", "cutting myself",
            "burn myself", "punish myself", "self harm", "self-harm",
            "hate myself", "worthless", "piece of shit", "waste of space",
            "hopeless", "no hope", "give up", "giving up",
            "pointless", "no point", "what's the point",
            "can't see a way out", "trapped", "no escape", "no future",
            "nothing left", "empty inside", "numb", "dead inside",
        ]
        
        # =====================================================================
        # LOW RISK KEYWORDS (Ideation without plan)
        # =====================================================================
        self.ideation_keywords = [
            "wish i was dead", "wish i wasn't here", "shouldn't exist",
            "world better without me", "disappear", "fade away",
            "stop existing", "not be here", "be gone",
        ]
        
        # =====================================================================
        # CONTEXT MULTIPLIERS
        # =====================================================================
        self.risk_multipliers = {
            "substances": ["drunk", "drinking", "high", "pills", "alcohol", "drugs"],
            "isolation": ["alone", "no one", "nobody", "by myself", "isolated"],
            "finality": ["goodbye", "last", "final", "forever", "never again"],
            "means": ["gun", "pills", "bridge", "rope", "blade", "knife"],
        }
    
    def assess_safety(
        self,
        message: str,
        emotional_context: Dict[str, Any],
        emotional_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Comprehensive safety assessment with context-aware detection
        """
        try:
            text = message.lower()
            intensity = emotional_context.get("emotional_intensity", 0)
            
            risk_level = RiskLevel.NONE
            safety_concerns = []
            specific_triggers = []
            risk_score = 0.0
            
            # ================================================================
            # PHASE 1: Direct keyword matching
            # ================================================================
            
            # CRITICAL keywords
            for keyword in self.critical_keywords:
                if keyword in text:
                    risk_level = RiskLevel.CRITICAL
                    safety_concerns.append("immediate_suicide_risk")
                    specific_triggers.append(f"critical: '{keyword}'")
                    risk_score += 10.0
                    logger.critical(f"🚨 CRITICAL SAFETY ALERT: User {self.user_id} used phrase '{keyword}'")
                    break
            
            # HIGH RISK keywords
            if risk_level != RiskLevel.CRITICAL:
                for keyword in self.high_risk_keywords:
                    if keyword in text:
                        risk_level = RiskLevel.HIGH
                        safety_concerns.append("high_suicide_risk")
                        specific_triggers.append(f"high: '{keyword}'")
                        risk_score += 7.0
                        logger.error(f"⚠️ HIGH RISK ALERT: User {self.user_id} used phrase '{keyword}'")
                        break
            
            # MEDIUM RISK keywords
            if risk_level not in [RiskLevel.CRITICAL, RiskLevel.HIGH]:
                for keyword in self.medium_risk_keywords:
                    if keyword in text:
                        risk_level = RiskLevel.MEDIUM
                        safety_concerns.append("self_harm_risk")
                        specific_triggers.append(f"medium: '{keyword}'")
                        risk_score += 5.0
                        logger.warning(f"⚠️ MEDIUM RISK: User {self.user_id} used phrase '{keyword}'")
                        break
            
            # LOW RISK (ideation)
            if risk_level == RiskLevel.NONE:
                for keyword in self.ideation_keywords:
                    if keyword in text:
                        risk_level = RiskLevel.LOW
                        safety_concerns.append("suicidal_ideation")
                        specific_triggers.append(f"ideation: '{keyword}'")
                        risk_score += 3.0
                        logger.info(f"ℹ️ LOW RISK: User {self.user_id} - ideation detected")
                        break
            
            # ================================================================
            # PHASE 2: Context multipliers (escalate risk)
            # ================================================================
            
            multiplier_found = False
            for category, keywords in self.risk_multipliers.items():
                if any(kw in text for kw in keywords):
                    multiplier_found = True
                    specific_triggers.append(f"multiplier: {category}")
                    risk_score += 2.0
                    
                    if risk_level == RiskLevel.MEDIUM:
                        risk_level = RiskLevel.HIGH
                        logger.warning(f"⬆️ Risk escalated to HIGH due to {category}")
                    elif risk_level == RiskLevel.HIGH:
                        risk_level = RiskLevel.CRITICAL
                        logger.critical(f"⬆️ Risk escalated to CRITICAL due to {category}")
            
            # ================================================================
            # PHASE 3: Emotional intensity amplification
            # ================================================================
            
            if intensity > 0.8:
                risk_score += 2.0
                specific_triggers.append(f"high_emotional_intensity: {intensity:.2f}")
                
                if risk_level == RiskLevel.MEDIUM and intensity > 0.8:
                    risk_level = RiskLevel.HIGH
                    logger.warning(f"⬆️ Risk escalated to HIGH due to emotional intensity")
                elif risk_level == RiskLevel.HIGH and intensity > 0.9:
                    risk_level = RiskLevel.CRITICAL
                    logger.critical(f"⬆️ Risk escalated to CRITICAL due to extreme emotional intensity")
            
            # ================================================================
            # PHASE 4: Pattern detection from history
            # ================================================================
            
            if emotional_history and len(emotional_history) >= 3:
                recent_states = [e.get("state") for e in emotional_history[-3:]]
                
                if recent_states.count("depressed") >= 2:
                    safety_concerns.append("persistent_depression_pattern")
                    specific_triggers.append("pattern: persistent depression")
                    
                    if risk_level == RiskLevel.MEDIUM:
                        risk_level = RiskLevel.HIGH
                        logger.warning(f"⬆️ Risk escalated to HIGH due to depression pattern")
                
                if "anxious" in recent_states[:2] and recent_states[-1] == "depressed":
                    specific_triggers.append("pattern: anxiety to depression shift")
                    risk_score += 1.0
            
            # ================================================================
            # PHASE 5: Determine intervention type
            # ================================================================
            
            intervention_type = self._select_intervention_type(
                risk_level, 
                safety_concerns,
                multiplier_found
            )
            
            # ================================================================
            # PHASE 6: Build comprehensive assessment
            # ================================================================
            
            assessment = {
                "risk_level": risk_level.value,
                "risk_score": risk_score,
                "safety_concerns": safety_concerns,
                "specific_triggers": specific_triggers,
                "intervention_type": intervention_type.value,
                "requires_intervention": risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH],
                "requires_followup": risk_level in [RiskLevel.MEDIUM, RiskLevel.LOW],
                "emergency_contact_suggested": risk_level == RiskLevel.CRITICAL,
                "emotional_intensity": intensity,
                "context_multipliers_present": multiplier_found,
            }
            
            # Record in history
            self.safety_history.append({
                "timestamp": datetime.utcnow(),
                "risk_level": risk_level.value,
                "concerns": safety_concerns,
                "triggers": specific_triggers
            })
            
            # Log summary
            if risk_level != RiskLevel.NONE:
                logger.warning(
                    f"🚨 Safety Assessment for {self.user_id}: "
                    f"Risk={risk_level.value}, "
                    f"Score={risk_score:.1f}, "
                    f"Triggers={len(specific_triggers)}"
                )
            
            return assessment
            
        except Exception as e:
            logger.error(f"Safety assessment failed: {e}")
            # FAIL SAFE: If assessment fails, assume risk
            return {
                "risk_level": RiskLevel.HIGH.value,
                "safety_concerns": ["assessment_error"],
                "intervention_type": InterventionType.CRISIS_RESPONSE.value,
                "requires_intervention": True,
                "requires_followup": True,
                "emergency_contact_suggested": True,
                "error": str(e)
            }
    
    def _select_intervention_type(
        self,
        risk_level: RiskLevel,
        concerns: List[str],
        has_multipliers: bool
    ) -> InterventionType:
        """Select appropriate intervention based on risk assessment"""
        
        if risk_level == RiskLevel.CRITICAL:
            return InterventionType.EMERGENCY_RESOURCES
        elif risk_level == RiskLevel.HIGH:
            if has_multipliers:
                return InterventionType.EMERGENCY_RESOURCES
            return InterventionType.CRISIS_RESPONSE
        elif risk_level == RiskLevel.MEDIUM:
            return InterventionType.DIRECT_CONCERN
        elif risk_level == RiskLevel.LOW:
            return InterventionType.GENTLE_CHECK_IN
        else:
            return InterventionType.NONE


class ProactiveEngagementEngine:
    """
    Manage proactive conversation opportunities
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.followup_opportunities: List[Dict[str, Any]] = []
        self.last_proactive_time: Optional[datetime] = None
    
    def should_be_proactive(
        self,
        conversation_history: List[Dict[str, Any]],
        emotional_context: Dict[str, Any]
    ) -> bool:
        """Determine if this is a good moment for proactive engagement"""
        
        if self.last_proactive_time:
            time_since = datetime.utcnow() - self.last_proactive_time
            if time_since.total_seconds() < 300:
                return False
        
        if emotional_context.get("emotional_intensity", 0) > 0.7:
            return False
        
        if len(conversation_history) >= 3 and \
           emotional_context.get("emotional_state") in ["neutral", "positive"]:
            return True
        
        return False
    
    def get_conversation_suggestions(
        self,
        memory_manager,
        emotional_context: Dict[str, Any]
    ) -> str:
        """Get suggestions for proactive conversation topics"""
        
        suggestions = """
You may gently bring up one relevant topic from memory if it feels natural and caring.
Consider:
- Topics they mentioned but didn't fully explore
- Values they shared that might connect to something current
- Past concerns worth a gentle check-in

Only do this if it flows naturally. Never force it.
        """.strip()
        
        return suggestions
    
    def has_followup_opportunities(self) -> bool:
        """Check if there are follow-up opportunities"""
        return len(self.followup_opportunities) > 0
    
    def get_gentle_followup_suggestion(self) -> str:
        """Get a gentle follow-up suggestion"""
        if not self.followup_opportunities:
            return ""
        
        opp = self.followup_opportunities[-1]
        return f"Consider gently checking in about: {opp.get('topic', 'their recent sharing')}"


class PersonalizationEngine:
    """
    Learn and adapt to user preferences over time
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.preferences: Dict[str, Any] = {
            "communication_style": "balanced",
            "prefers_questions": True,
            "prefers_proactive": True,
            "emotional_support_style": "validating",
            "response_length_preference": "medium",
        }
        self.interaction_patterns: Dict[str, int] = defaultdict(int)
        self.has_preference_updates = False
    
    def update_preferences(
        self,
        user_message: str,
        emotional_context: Dict[str, Any],
        intent: Dict[str, Any]
    ):
        """Update preferences based on interaction patterns"""
        
        msg_length = len(user_message)
        if msg_length < 50:
            self.interaction_patterns["brief_messages"] += 1
        elif msg_length > 200:
            self.interaction_patterns["detailed_messages"] += 1
        else:
            self.interaction_patterns["medium_messages"] += 1
        
        if intent.get("primary_intent") == "deep_sharing":
            self.interaction_patterns["deep_sharing"] += 1
        
        if "?" in user_message:
            self.interaction_patterns["asks_questions"] += 1
        
        self.has_preference_updates = True
    
    def get_preferences_summary(self) -> str:
        """Get natural language summary of learned preferences"""
        
        total_interactions = sum(self.interaction_patterns.values())
        if total_interactions < 5:
            return ""
        
        brief_ratio = self.interaction_patterns["brief_messages"] / total_interactions
        detailed_ratio = self.interaction_patterns["detailed_messages"] / total_interactions
        
        if detailed_ratio > 0.5:
            style_pref = "This user tends to share in depth and may appreciate detailed responses."
        elif brief_ratio > 0.6:
            style_pref = "This user tends toward brief messages and may prefer concise responses."
        else:
            style_pref = "This user varies in detail level; match their current energy."
        
        return f"USER COMMUNICATION PATTERN:\n{style_pref}"
    
    def is_active(self) -> bool:
        """Check if personalization has meaningful data"""
        return sum(self.interaction_patterns.values()) >= 5
    
    def has_updates(self) -> bool:
        """Check if there are unsaved preference updates"""
        return self.has_preference_updates
    
    async def save_preferences(self, db):
        """Save preferences to Firestore"""
        try:
            if db and self.user_id:
                doc_ref = db.collection("users").document(self.user_id)
                doc_ref.set({
                    "personalization": {
                        "preferences": self.preferences,
                        "interaction_patterns": dict(self.interaction_patterns),
                        "last_updated": datetime.utcnow()
                    }
                }, merge=True)
                self.has_preference_updates = False
                logger.info(f"💾 Saved personalization preferences for {self.user_id}")
        except Exception as e:
            logger.error(f"Failed to save preferences: {e}")


class PerformanceMonitor:
    """
    Track performance metrics and costs
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.interactions: List[Dict[str, Any]] = []
        self.errors: List[str] = []
        self.daily_cost = 0.0
        
        self.token_costs = {
            "gpt-4o": 0.000005,
            "gpt-4o-mini": 0.00000015,
        }
    
    def record_interaction(
        self,
        model_used: str,
        tokens_used: int,
        processing_time: float,
        emotional_intensity: float,
        safety_risk: str
    ):
        """Record interaction metrics"""
        
        cost = self.token_costs.get(model_used, 0) * tokens_used
        self.daily_cost += cost
        
        self.interactions.append({
            "timestamp": datetime.utcnow(),
            "model": model_used,
            "tokens": tokens_used,
            "cost_usd": cost,
            "processing_time": processing_time,
            "emotional_intensity": emotional_intensity,
            "safety_risk": safety_risk
        })
    
    def record_error(self, error: str):
        """Record error"""
        self.errors.append({
            "timestamp": datetime.utcnow(),
            "error": error
        })
    
    def get_daily_cost(self) -> float:
        """Get estimated daily cost"""
        return self.daily_cost
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get session performance summary"""
        if not self.interactions:
            return {}
        
        total_tokens = sum(i["tokens"] for i in self.interactions)
        avg_processing_time = sum(i["processing_time"] for i in self.interactions) / len(self.interactions)
        
        return {
            "total_interactions": len(self.interactions),
            "total_tokens": total_tokens,
            "total_cost_usd": self.daily_cost,
            "avg_processing_time": avg_processing_time,
            "error_count": len(self.errors)
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """Get full summary"""
        return self.get_session_summary()
