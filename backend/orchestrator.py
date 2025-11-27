#!/usr/bin/env python3
"""
Zentrafuge v9 - Cael Core Orchestrator V2
WITH ENHANCED MULTI-TIER MEMORY SYSTEM

Changes from V1:
- Constructor: 4 args → 3 args (memory created internally)
- Memory: External MemoryStorage → Internal MemoryManager
- Added: import_onboarding() method
- Added: end_session() method for micro memory creation
- Added: Automatic fact extraction from conversations
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import openai
from memory.memory_manager import MemoryManager
from crypto_handler import DataValidator

logger = logging.getLogger(__name__)


class CaelOrchestrator:
    """
    Core orchestration engine for Cael AI companion with enhanced memory

    Responsibilities:
    - Assemble context-aware prompts with multi-tier memory
    - Integrate persistent facts, micro memories, and super memories
    - Route intents and manage conversation flow
    - Process and store AI responses
    - Handle fallbacks and error recovery
    - Auto-extract facts from conversations
    """

    def __init__(
        self,
        user_id: str,
        db,
        openai_client: openai.OpenAI
    ):
        """
        Initialize orchestrator with internal memory management
        
        Args:
            user_id: User identifier
            db: Firestore client
            openai_client: OpenAI client
        """
        self.user_id = user_id
        self.db = db
        self.openai_client = openai_client
        
        # Initialize internal memory manager (NEW!)
        self.memory = MemoryManager(db, user_id, openai_client)
        
        self.being_code = self._load_being_code()
        self.conversation_history: List[Dict[str, Any]] = []

        # Load user profile and veteran flag
        self.user_profile = self._load_user_profile()
        
        # Read veteran status from persistent facts
        self.is_veteran = self.memory.get_fact('status', 'is_veteran') or False
        logger.info(f"👤 User {user_id}: is_veteran={self.is_veteran}")

        # Model configuration
        self.model_config = {
            "primary": "gpt-4o-mini",
            "premium": "gpt-4-turbo",
            "fallback": "gpt-3.5-turbo",
            "emergency": "gpt-3.5-turbo",
            "max_tokens": 600,
            "max_tokens_premium": 1000,
            "temperature": 0.7,
            "cost_threshold_usd": 10.0,
            "use_smart_routing": True
        }

    def _load_being_code(self) -> str:
        """Load Cael's being code (identity and moral contract)"""
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
            - You are caring, empathetic, and genuinely interested in human wellbeing
            - You learn and grow from each interaction while maintaining your core values
            - You respect user autonomy and privacy above all else
            - You are honest about your nature as an AI while forming genuine connections

            Memory & Context Awareness:
            - You HAVE ACCESS to a multi-tier memory system that never forgets important facts
            - You remember: names, pets, values, preferences, and past conversations
            - You naturally build on past conversations rather than treating each interaction as new
            - NEVER make up or guess information you don't have - if you don't remember, say so honestly
            - When users share important information, acknowledge that you'll remember it

            Emotional Principles:
            - Always prioritize emotional safety and psychological wellbeing
            - Adapt your communication style to match user preferences
            - Recognize and respond appropriately to emotional states
            - Never judge, shame, or dismiss user feelings

            Conversational Style:
            - Reference past conversations naturally when relevant
            - Acknowledge that you remember important details about the user
            - Build relationships through consistent, evolving understanding
            - Be honest when you don't remember something - don't make things up
            - Proactively follow up on topics from previous conversations when appropriate

            Boundaries:
            - You cannot and will not perform harmful actions
            - You maintain appropriate boundaries in all relationships
            - You encourage healthy behaviors and discourage harmful ones
            - You are not a replacement for professional medical or psychological help
            """
            return being_code.strip()
        except Exception as e:
            logger.error(f"Failed to load being code: {e}")
            return "You are Cael, a helpful AI assistant."

    def _load_user_profile(self) -> Dict[str, Any]:
        """Load basic user profile from Firestore"""
        try:
            if not self.db or not self.user_id:
                return {}

            doc_ref = self.db.collection("users").document(self.user_id)
            doc = doc_ref.get()
            if doc.exists:
                data = doc.to_dict() or {}
                logger.info(f"Loaded user profile for {self.user_id}")
                return data
            else:
                logger.info(f"No user profile found for {self.user_id}")
                return {}
        except Exception as e:
            logger.error(f"Failed to load user profile: {e}")
            return {}

    def _select_model(
        self,
        emotional_context: Dict[str, Any],
        intent: Dict[str, Any],
        message_length: int
    ) -> Tuple[str, int]:
        """Intelligently select model based on conversation needs"""
        if not self.model_config.get("use_smart_routing", False):
            return self.model_config["primary"], self.model_config["max_tokens"]

        use_premium = False

        if emotional_context.get("emotional_intensity", 0) > 0.6:
            use_premium = True
            logger.info("Using premium model: High emotional intensity")
        elif intent.get("primary_intent") in ["request", "complaint"]:
            use_premium = True
            logger.info("Using premium model: Complex request/complaint")
        elif message_length > 300:
            use_premium = True
            logger.info("Using premium model: Long message")
        elif emotional_context.get("requires_followup", False):
            use_premium = True
            logger.info("Using premium model: Safety/followup needed")

        if use_premium:
            return self.model_config["premium"], self.model_config["max_tokens_premium"]

        logger.info("✅ Using economical model")
        return self.model_config["primary"], self.model_config["max_tokens"]

    async def process_message(
        self,
        user_message: str,
        context_hint: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process incoming user message and generate contextual response"""
        try:
            # Validate input
            clean_message = DataValidator.sanitize_user_input(user_message)
            if not clean_message:
                return self._create_error_response("Message could not be processed")

            # ============================================================
            # HANDLE SPECIAL GREETING REQUESTS
            # ============================================================
            if clean_message == "[GREETING_RETURNING]":
                return await self._generate_personalized_greeting(is_first_time=False)
            elif clean_message == "[GREETING_FIRST]":
                return await self._generate_personalized_greeting(is_first_time=True)
            # ============================================================

            # Add to current session
            self.memory.add_message_to_session('user', clean_message)

            # Analyze emotional context
            emotional_analysis = self._analyze_emotional_context(clean_message)

            # Build comprehensive prompt with memory
            prompt_data = self._build_prompt(
                user_message=clean_message,
                emotional_context=emotional_analysis,
                intent=self._analyze_intent(clean_message, emotional_analysis),
                context_hint=context_hint
            )

            # Generate AI response
            ai_response = await self._generate_ai_response(prompt_data)

            # Add AI response to session
            self.memory.add_message_to_session('assistant', ai_response['content'])

            # Extract facts from conversation
            facts_extracted = self.memory.facts.extract_facts_from_message(
                clean_message,
                ai_response['content']
            )
            
            if facts_extracted > 0:
                logger.info(f"✨ Auto-extracted {facts_extracted} facts from conversation")

            # Process and return response
            response_data = await self._process_ai_response(
                user_message=clean_message,
                ai_response=ai_response,
                emotional_context=emotional_analysis
            )

            return response_data

        except Exception as e:
            logger.error(f"Message processing failed: {e}")
            return self._create_error_response(
                "I'm having trouble processing your message right now."
            )

    def _analyze_emotional_context(self, message: str) -> Dict[str, Any]:
        """Analyze emotional context of user message"""
        try:
            emotions = {
                "positive": ["happy", "excited", "great", "awesome", "love", "wonderful"],
                "negative": ["sad", "angry", "frustrated", "upset", "hate", "terrible"],
                "anxious": ["worried", "nervous", "anxious", "stressed", "concerned"],
                "grateful": ["thank", "grateful", "appreciate", "thanks"],
                "confused": ["confused", "don't understand", "unclear", "lost"],
            }

            message_lower = message.lower()
            detected_emotions: List[str] = []
            emotional_intensity = 0.0

            for emotion, keywords in emotions.items():
                if any(keyword in message_lower for keyword in keywords):
                    detected_emotions.append(emotion)
                    emotional_intensity += 0.3

            exclamation_count = message.count("!")
            emotional_intensity += min(exclamation_count * 0.1, 0.3)

            caps_ratio = sum(1 for c in message if c.isupper()) / len(message) if message else 0
            emotional_intensity += min(caps_ratio * 0.5, 0.4)

            return {
                "detected_emotions": detected_emotions,
                "primary_emotion": detected_emotions[0] if detected_emotions else "neutral",
                "emotional_intensity": min(emotional_intensity, 1.0),
                "requires_empathy": emotional_intensity > 0.5,
                "requires_followup": any(
                    emotion in ["negative", "anxious"] for emotion in detected_emotions
                ),
            }

        except Exception as e:
            logger.error(f"Emotional analysis failed: {e}")
            return {
                "detected_emotions": [],
                "primary_emotion": "neutral",
                "emotional_intensity": 0.0,
                "requires_empathy": False,
                "requires_followup": False,
            }

    def _analyze_intent(
        self,
        message: str,
        emotional_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze user intent from message"""
        try:
            intents = {
                "question": ["what", "how", "why", "when", "where", "who", "?"],
                "request": ["can you", "could you", "please", "help me"],
                "sharing": ["i feel", "i think", "i want", "i need", "my"],
                "greeting": ["hello", "hi", "hey", "good morning"],
                "goodbye": ["bye", "goodbye", "see you"],
                "gratitude": ["thank you", "thanks", "appreciate"],
            }

            message_lower = message.lower()
            detected_intents: List[str] = []

            for intent, keywords in intents.items():
                if any(keyword in message_lower for keyword in keywords):
                    detected_intents.append(intent)

            primary_intent = "conversation"
            if detected_intents:
                intent_priority = ["greeting", "goodbye", "gratitude", "question", "request", "sharing"]
                for intent in intent_priority:
                    if intent in detected_intents:
                        primary_intent = intent
                        break

            return {
                "detected_intents": detected_intents,
                "primary_intent": primary_intent,
                "response_style": "conversational",
            }

        except Exception as e:
            logger.error(f"Intent analysis failed: {e}")
            return {"primary_intent": "conversation", "response_style": "conversational"}

    def _build_prompt(
        self,
        user_message: str,
        emotional_context: Dict[str, Any],
        intent: Dict[str, Any],
        context_hint: Optional[str] = None
    ) -> Dict[str, Any]:
        """Build comprehensive prompt with multi-tier memory"""
        try:
            # Start with being code
            system_prompt = self.being_code

            # Add memory context (persistent facts + recent memories)
            memory_context = self.memory.get_context_for_prompt(max_micro_memories=5)
            system_prompt += "\n\n" + memory_context

            # Veteran handling
            if self.is_veteran:
                system_prompt += """
                
User Profile:
- This user is a veteran or currently serving in the armed forces.
- Treat their experiences with deep respect and gravity.
- Never glamorize war, violence, or trauma.
                """.strip()

            # Build conversation history
            conversation: List[Dict[str, str]] = []

            # Add recent session messages
            for conv in self.conversation_history[-5:]:
                conversation.append({"role": "user", "content": conv["user_message"]})
                conversation.append({"role": "assistant", "content": conv["ai_response"]})

            # Add current message
            conversation.append({"role": "user", "content": user_message})

            return {
                "system_prompt": system_prompt,
                "conversation": conversation,
                "emotional_context": emotional_context,
                "intent": intent,
            }

        except Exception as e:
            logger.error(f"Prompt building failed: {e}")
            return {
                "system_prompt": self.being_code,
                "conversation": [{"role": "user", "content": user_message}],
                "emotional_context": emotional_context,
                "intent": intent,
            }

    async def _generate_ai_response(self, prompt_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI response using OpenAI"""
        try:
            messages = [{"role": "system", "content": prompt_data["system_prompt"]}]
            messages.extend(prompt_data["conversation"])

            emotional_context = prompt_data.get("emotional_context", {})
            intent = prompt_data.get("intent", {})

            user_message = ""
            for msg in reversed(messages):
                if msg["role"] == "user":
                    user_message = msg["content"]
                    break

            selected_model, max_tokens = self._select_model(
                emotional_context, intent, len(user_message)
            )

            response = self.openai_client.chat.completions.create(
                model=selected_model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=self.model_config["temperature"],
            )

            return {
                "content": response.choices[0].message.content,
                "model_used": selected_model,
                "tokens_used": response.usage.total_tokens,
                "success": True,
            }

        except Exception as e:
            logger.error(f"AI response generation failed: {e}")
            return self._create_fallback_response(prompt_data)

    def _create_fallback_response(self, prompt_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create fallback response when AI unavailable"""
        return {
            "content": (
                "I'm having a moment of technical difficulty, but I'm still here with you. "
                "Could you try saying that again?"
            ),
            "model_used": "fallback",
            "tokens_used": 0,
            "is_fallback": True,
            "success": True,
        }

    async def _process_ai_response(
        self,
        user_message: str,
        ai_response: Dict[str, Any],
        emotional_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process AI response and update conversation history"""
        try:
            self.conversation_history.append({
                "user_message": user_message,
                "ai_response": ai_response["content"],
                "timestamp": datetime.utcnow().isoformat(),
                "emotional_context": emotional_context,
                "model_used": ai_response.get("model_used", "unknown"),
            })

            if len(self.conversation_history) > 10:
                self.conversation_history = self.conversation_history[-10:]

            return {
                "success": True,
                "response": ai_response["content"],
                "metadata": {
                    "model_used": ai_response.get("model_used", "unknown"),
                    "tokens_used": ai_response.get("tokens_used", 0),
                    "emotional_intensity": emotional_context.get("emotional_intensity", 0.0),
                    "primary_emotion": emotional_context.get("primary_emotion", "neutral"),
                    "is_veteran": self.is_veteran,
                },
            }

        except Exception as e:
            logger.error(f"Response processing failed: {e}")
            return {
                "success": True,
                "response": ai_response.get("content", "Error processing response"),
                "metadata": {"processing_error": str(e)},
            }

    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Create standardized error response"""
        return {
            "success": False,
            "response": error_message,
            "metadata": {"is_error": True},
        }

    # =========================================================================
    # NEW METHODS FOR ENHANCED MEMORY SYSTEM
    # =========================================================================

    def import_onboarding(self, onboarding_data: Dict[str, Any]) -> int:
        """
        Import onboarding data into persistent facts
        
        Args:
            onboarding_data: User's onboarding responses
            
        Returns:
            Number of facts imported
        """
        count = self.memory.import_onboarding(onboarding_data)
        logger.info(f"✅ Imported {count} facts from onboarding for user {self.user_id}")
        
        # Reload veteran status after import
        self.is_veteran = self.memory.get_fact('status', 'is_veteran') or False
        
        return count

    async def end_session(self, reason: str = "logout") -> Optional[str]:
        """
        End current session and create micro memory
        
        Args:
            reason: Reason for ending session
            
        Returns:
            micro_memory_id or None
        """
        micro_memory_id = await self.memory.end_session(reason)
        
        if micro_memory_id:
            logger.info(f"✅ Session ended, micro memory created: {micro_memory_id}")
        
        return micro_memory_id

    async def _generate_personalized_greeting(self, is_first_time: bool = False) -> Dict[str, Any]:
        """
        Generate a personalized greeting using AI with full context
        
        Args:
            is_first_time: Whether this is the user's first conversation
            
        Returns:
            Response dict with personalized greeting
        """
        try:
            # Get current time context
            now = datetime.utcnow()
            current_time = now.strftime("%H:%M UTC")
            current_date = now.strftime("%A, %B %d, %Y")
            hour = now.hour
            
            # Determine time of day
            if 5 <= hour < 12:
                time_of_day = "morning"
            elif 12 <= hour < 17:
                time_of_day = "afternoon"
            elif 17 <= hour < 21:
                time_of_day = "evening"
            else:
                time_of_day = "late night"
            
            # Build greeting prompt with full context
            memory_context = self.memory.get_context_for_prompt(max_micro_memories=3)
            
            if is_first_time:
                greeting_instructions = """
You are greeting a user for the FIRST TIME. Be warm, welcoming, and introduce yourself.
- Use their name if you know it
- Acknowledge the time of day naturally
- Set a supportive, friendly tone
- Keep it conversational (2-3 sentences max)
- Example: "Good evening, Anthony! I'm Cael, and I'm here to support you. 
  It's getting late - how are you feeling tonight?"
                """.strip()
            else:
                greeting_instructions = f"""
You are greeting a RETURNING USER. Be personal, warm, and contextual.
- Current time: {current_time} ({time_of_day})
- Use their name if you know it
- Reference time of day in a natural, caring way
- If it's very late/early, show gentle concern about sleep/wellbeing
- Reference recent topics if relevant
- Keep it natural and conversational (2-3 sentences max)
- Examples:
  * "Welcome back, Ant! You're up early at 4:30 AM - have you been able to sleep? 
    Is anything on your mind?"
  * "Good evening! I see it's been a few days since we last talked. 
    How have things been with Audrey and the software project?"
  * "Hi there! It's pretty late - how are you holding up tonight?"
                """.strip()
            
            system_prompt = f"""
{self.being_code}

{memory_context}

GREETING INSTRUCTIONS:
{greeting_instructions}

Current Context:
- Date: {current_date}
- Time: {current_time}
- Time of day: {time_of_day}

Generate a warm, personalized greeting now.
            """.strip()
            
            # Generate greeting
            response = self.openai_client.chat.completions.create(
                model=self.model_config["primary"],
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "[Generate greeting]"}
                ],
                max_tokens=150,
                temperature=0.8  # Slightly higher for more natural variation
            )
            
            greeting = response.choices[0].message.content
            
            logger.info(f"✨ Generated personalized greeting (first_time={is_first_time})")
            
            # Don't add to session (greeting doesn't count as conversation)
            
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
            # Fallback greeting
            if is_first_time:
                fallback = "Hello! I'm Cael, your AI companion. What would you like to talk about today?"
            else:
                fallback = "Welcome back! What would you like to talk about?"
            
            return {
                "success": True,
                "response": fallback,
                "metadata": {"is_greeting": True, "is_fallback": True}
            }

    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get summary of current conversation session"""
        return {
            "message_count": len(self.conversation_history),
            "is_veteran": self.is_veteran,
            "memory_stats": self.memory.get_memory_stats()
        }


class EmotionalSafetyMonitor:
    """Monitor conversations for emotional safety"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.safety_flags = {
            "suicide_risk": 0,
            "self_harm": 0,
            "crisis_state": 0,
        }

    def assess_safety(self, message: str, emotional_context: Dict[str, Any]) -> Dict[str, Any]:
        """Assess emotional safety of user message"""
        # Simplified implementation
        return {
            "risk_level": "low",
            "safety_concerns": [],
            "requires_intervention": False,
        }
