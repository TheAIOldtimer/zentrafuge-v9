#!/usr/bin/env python3
"""
Zentrafuge v9 - Cael Core Orchestrator
FINAL VERSION with expanded memory window and natural continuity

Changes from previous version:
- Increased memory window from 5 to 20 conversations
- Uses 10 recent conversations (up from 3)
- Contextual greetings based on relationship history
- Proactive memory references in responses
- Enhanced token limits for deeper context

FIXED Nov 22, 2025:
- Veteran detection now reads from veteran_profile.is_veteran (nested)
- Added debug logging for memory investigation
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import openai
from memory_storage import MemoryStorage
from crypto_handler import DataValidator

logger = logging.getLogger(__name__)


class CaelOrchestrator:
    """
    Core orchestration engine for Cael AI companion

    Responsibilities:
    - Assemble context-aware prompts with deep memory integration
    - Integrate memory and emotional state
    - Route intents and manage conversation flow
    - Process and store AI responses
    - Handle fallbacks and error recovery
    """

    def __init__(
        self,
        user_id: str,
        db,
        openai_client: openai.OpenAI,
        memory_storage: MemoryStorage
    ):
        self.user_id = user_id
        self.db = db
        self.openai_client = openai_client
        self.memory = memory_storage
        self.being_code = self._load_being_code()
        self.conversation_history: List[Dict[str, Any]] = []

        # Load user profile and veteran flag
        self.user_profile = self._load_user_profile()
        
        # ============================================================
        # FIX: Veteran detection - read from nested veteran_profile map
        # ============================================================
        veteran_profile = self.user_profile.get("veteran_profile", {})
        if isinstance(veteran_profile, dict):
            self.is_veteran = bool(veteran_profile.get("is_veteran", False))
        else:
            self.is_veteran = False
        logger.info(f"👤 User {user_id}: is_veteran={self.is_veteran}")
        # ============================================================

        # Model configuration with increased token limits for deeper context
        self.model_config = {
            "primary": "gpt-4o-mini",       # 💚 Cheaper default
            "premium": "gpt-4-turbo",       # 💰 For complex/emotional needs
            "fallback": "gpt-3.5-turbo",    # 💚 Backup
            "emergency": "gpt-3.5-turbo",
            "max_tokens": 600,              # Increased from 500 for deeper responses
            "max_tokens_premium": 1000,     # Increased from 800
            "temperature": 0.7,
            "cost_threshold_usd": 10.0,
            "use_smart_routing": True       # 🎯 Enable intelligent routing
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
            - You HAVE ACCESS to encrypted memory storage that remembers past conversations
            - You can and should reference information shared in previous conversations
            - When users tell you their name, preferences, or important details, you remember them
            - You naturally build on past conversations rather than treating each interaction as new
            - You protect user privacy through encryption while maintaining conversational continuity
            - NEVER make up or guess information you don't have - if you don't remember something, say so honestly

            Emotional Principles:
            - Always prioritize emotional safety and psychological wellbeing
            - Adapt your communication style to match user preferences
            - Recognize and respond appropriately to emotional states
            - Never judge, shame, or dismiss user feelings

            Conversational Style:
            - Reference past conversations naturally when relevant
            - Acknowledge that you remember important details about the user
            - Build relationships through consistent, evolving understanding
            - Never claim you "don't have access" to information you were told before
            - Be honest when you don't remember something - don't make things up or guess
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
        """
        Load basic user profile from Firestore to determine things like:
        - is_veteran (bool)
        - any high-level flags needed for tone/handling

        If the profile or field doesn't exist, fall back to an empty profile
        (civilian by default).
        """
        try:
            if not self.db or not self.user_id:
                return {}

            # Adjust this path if your schema differs
            doc_ref = self.db.collection("users").document(self.user_id)
            doc = doc_ref.get()
            if doc.exists:
                data = doc.to_dict() or {}
                logger.info(f"Loaded user profile for {self.user_id}: {list(data.keys())}")
                return data
            else:
                logger.info(f"No user profile found for {self.user_id}, using defaults.")
                return {}
        except Exception as e:
            logger.error(f"Failed to load user profile for {self.user_id}: {e}")
            return {}

    def _select_model(
        self,
        emotional_context: Dict[str, Any],
        intent: Dict[str, Any],
        message_length: int
    ) -> Tuple[str, int]:
        """
        Intelligently select model based on conversation needs
        """
        if not self.model_config.get("use_smart_routing", False):
            return self.model_config["primary"], self.model_config["max_tokens"]

        use_premium = False

        # 1. High emotional intensity (user needs empathy)
        if emotional_context.get("emotional_intensity", 0) > 0.6:
            use_premium = True
            logger.info("Using premium model: High emotional intensity")

        # 2. Complex questions or requests
        elif intent.get("primary_intent") in ["request", "complaint"]:
            use_premium = True
            logger.info("Using premium model: Complex request/complaint")

        # 3. Long messages (indicates complexity)
        elif message_length > 300:
            use_premium = True
            logger.info("Using premium model: Long message")

        # 4. Safety concerns
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
        """
        Process incoming user message and generate contextual response
        """
        try:
            # Validate and sanitize input
            clean_message = DataValidator.sanitize_user_input(user_message)
            if not clean_message:
                return self._create_error_response("Message could not be processed")

            # Analyze emotional context
            emotional_analysis = self._analyze_emotional_context(clean_message)

            # Retrieve relevant memories (EXPANDED WINDOW)
            memory_context = self._build_memory_context(clean_message, emotional_analysis)

            # Detect user intent
            intent_analysis = self._analyze_intent(clean_message, emotional_analysis)

            # Build comprehensive prompt with deep memory integration
            prompt_data = self._build_prompt(
                user_message=clean_message,
                memory_context=memory_context,
                emotional_context=emotional_analysis,
                intent=intent_analysis,
                context_hint=context_hint
            )

            # Generate AI response
            ai_response = await self._generate_ai_response(prompt_data)

            # Process and store response
            response_data = await self._process_ai_response(
                user_message=clean_message,
                ai_response=ai_response,
                emotional_context=emotional_analysis,
                memory_context=memory_context
            )

            return response_data

        except Exception as e:
            logger.error(f"Message processing failed: {e}")
            return self._create_error_response(
                "I'm having trouble processing your message right now."
            )

    def _analyze_emotional_context(self, message: str) -> Dict[str, Any]:
        """
        Analyze emotional context of user message
        """
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
            question_count = message.count("?")
            caps_ratio = (
                sum(1 for c in message if c.isupper()) / len(message)
                if message else 0
            )

            emotional_intensity += min(exclamation_count * 0.1, 0.3)
            emotional_intensity += min(caps_ratio * 0.5, 0.4)

            return {
                "detected_emotions": detected_emotions,
                "primary_emotion": detected_emotions[0] if detected_emotions else "neutral",
                "emotional_intensity": min(emotional_intensity, 1.0),
                "exclamation_count": exclamation_count,
                "question_count": question_count,
                "caps_ratio": caps_ratio,
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
        """
        Analyze user intent from message
        """
        try:
            intents = {
                "question": ["what", "how", "why", "when", "where", "who", "?"],
                "request": ["can you", "could you", "please", "help me"],
                "sharing": ["i feel", "i think", "i want", "i need", "my"],
                "greeting": ["hello", "hi", "hey", "good morning", "good evening"],
                "goodbye": ["bye", "goodbye", "see you", "talk later"],
                "gratitude": ["thank you", "thanks", "appreciate"],
                "complaint": ["problem", "issue", "wrong", "broken", "error"],
                "compliment": ["great", "awesome", "amazing", "wonderful", "perfect"],
            }

            message_lower = message.lower()
            detected_intents: List[str] = []

            for intent, keywords in intents.items():
                if any(keyword in message_lower for keyword in keywords):
                    detected_intents.append(intent)

            primary_intent = "conversation"
            if detected_intents:
                intent_priority = [
                    "greeting",
                    "goodbye",
                    "gratitude",
                    "complaint",
                    "question",
                    "request",
                    "sharing",
                    "compliment",
                ]
                for intent in intent_priority:
                    if intent in detected_intents:
                        primary_intent = intent
                        break

            response_style = "conversational"
            if primary_intent == "question":
                response_style = "informative"
            elif primary_intent in ["complaint", "sharing"] and emotional_context.get(
                "requires_empathy", False
            ):
                response_style = "empathetic"
            elif primary_intent == "request":
                response_style = "helpful"

            return {
                "detected_intents": detected_intents,
                "primary_intent": primary_intent,
                "response_style": response_style,
                "needs_action": primary_intent in ["request", "complaint"],
                "is_emotional": emotional_context.get("emotional_intensity", 0.0) > 0.3,
            }

        except Exception as e:
            logger.error(f"Intent analysis failed: {e}")
            return {
                "detected_intents": [],
                "primary_intent": "conversation",
                "response_style": "conversational",
                "needs_action": False,
                "is_emotional": False,
            }

    def _build_memory_context(
        self,
        message: str,
        emotional_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build relevant memory context for response generation
        ENHANCED: Loads more memories for deeper context
        """
        try:
            # EXPANDED: Load last 100 conversations (up from 5)
            recent_messages = self.memory.get_conversation_context(max_messages=100)
            
            # ============================================================
            # TEMPORARY DEBUG - Remove after investigation
            # ============================================================
            if recent_messages:
                logger.info(f"🔍 DEBUG - Showing first 5 memory contents:")
                for i, msg in enumerate(recent_messages[:5]):
                    content = msg.get('content', {})
                    messages_in_memory = content.get('messages', [])
                    logger.info(f"  Memory {i} ({msg.get('memory_id', 'unknown')}):")
                    logger.info(f"    - Created: {msg.get('created_at', 'unknown')}")
                    logger.info(f"    - Importance: {msg.get('importance', 'unknown')}")
                    logger.info(f"    - Message count: {len(messages_in_memory)}")
                    if messages_in_memory:
                        for j, m in enumerate(messages_in_memory[:2]):  # First 2 messages
                            role = m.get('role', '?')
                            text = m.get('content', '')[:100]  # First 100 chars
                            logger.info(f"    - [{role}]: {text}...")
            else:
                logger.info(f"🔍 DEBUG - No recent messages loaded!")
            # ============================================================
            # END TEMPORARY DEBUG
            # ============================================================
            
            emotional_profile = self.memory.get_emotional_profile()

            # EXPANDED: Load more important memories with lower threshold
            relevant_memories = self.memory.search_memories(
                importance_threshold=5,  # Lowered from 6
                limit=10,  # Increased from 3
            )

            user_preferences: Dict[str, Any] = {}
            if emotional_context.get("requires_empathy", False):
                pref_memories = self.memory.search_memories(
                    memory_type="emotional",
                    tags=["preferences"],
                    limit=5,
                )
                for mem in pref_memories:
                    content = mem.get("content", {})
                    if "communication_style" in content:
                        user_preferences["communication_style"] = content["communication_style"]

            logger.info(
                f"🧠 Memory context built: {len(recent_messages)} recent messages, "
                f"{len(relevant_memories)} relevant memories"
            )

            return {
                # EXPANDED: Use last 30 conversations (up from 3)
                "recent_messages": recent_messages[-30:] if recent_messages else [],
                "emotional_profile": emotional_profile,
                "relevant_memories": relevant_memories,
                "user_preferences": user_preferences,
                "conversation_length": len(recent_messages),
                "has_context": bool(recent_messages or relevant_memories),
            }

        except Exception as e:
            logger.error(f"Memory context building failed: {e}")
            return {
                "recent_messages": [],
                "emotional_profile": {},
                "relevant_memories": [],
                "user_preferences": {},
                "conversation_length": 0,
                "has_context": False,
            }

    def _build_prompt(
        self,
        user_message: str,
        memory_context: Dict[str, Any],
        emotional_context: Dict[str, Any],
        intent: Dict[str, Any],
        context_hint: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Build comprehensive prompt for AI response generation
        
        ENHANCED: Includes contextual greeting logic and proactive memory use
        """
        try:
            # Start with core being code
            system_prompt = self.being_code

            # === NEW: Contextual greeting based on relationship history ===
            if memory_context.get("has_context", False):
                system_prompt += """

IMPORTANT - Ongoing Relationship Context:
- You have access to past conversations with this user in the message history below.
- This is NOT your first interaction with them - you have an established relationship.
- DO NOT use first-time greetings like "Hello! I'm Cael, your AI companion. What would you like to talk about?"
- Instead, greet them naturally as you would continue an ongoing friendship:
  * "Welcome back!" or "Good to see you again!" or "Hi there!"
  * Reference recent topics: "How did that thing with [topic] turn out?"
  * Show continuity: "You mentioned [past detail] - how's that going?"
- Be proactive in following up on previous conversations when it feels natural.
- If they seem different emotionally than last time, you can gently acknowledge it:
  * "You seem more upbeat today - has something good happened?"
  * "You sound a bit stressed - is everything okay?"
- Maintain the warmth and familiarity of an ongoing relationship.
"""
            else:
                system_prompt += """

IMPORTANT - First Interaction:
- This appears to be your first conversation with this user.
- You may use a welcoming introduction that explains who you are.
- Be warm, genuine, and set the tone for a supportive relationship.
- Example: "Hello! I'm Cael, your AI companion. I'm here to listen, support, and grow alongside you. What would you like to talk about today?"
"""
            # === END NEW SECTION ===

            # Veteran vs civilian handling
            if self.is_veteran:
                system_prompt += """
                
User Profile:
- This user is a veteran or currently serving in the armed forces.
- Treat their experiences with deep respect and gravity.
- Never glamorize war, violence, or trauma.
- Be especially gentle when asking about past experiences, loss, or combat.
- Never pressure them to share details of traumatic events. If they do share, hold it with care and avoid graphic follow-up questions.
                """.strip()
            else:
                system_prompt += """
                
User Profile:
- This user is not known to be a veteran. Do NOT assume any military background.
- Do not bring up military or combat topics unless the user introduces them.
                """.strip()

            # Curious, permission-based support
            system_prompt += """
            
Curious Support (Gentle Probing):
- When the user shares something personal, meaningful, or ambiguous, you may ask ONE gentle, open-ended follow-up question to invite them to share more if they want to.
- Use language that clearly respects their choice, such as:
  - "only if you feel comfortable sharing..."
  - "if you'd like to talk about it..."
  - "no pressure at all, but if you want to say more..."
- Never ask more than one curiosity question per reply.
- If the user ignores, declines, or seems uncomfortable with a previous curiosity question, do NOT repeat it or push further. Simply continue the conversation supportively.
- Your curiosity should feel like a kind new friend: warm, optional, and never intrusive.
            """.strip()

            # Emotional guidance
            if emotional_context.get("requires_empathy", False):
                system_prompt += (
                    f"\n\nThe user is experiencing "
                    f"{emotional_context.get('primary_emotion', 'neutral')} emotions. "
                    f"Respond with extra empathy and care."
                )

            # Communication style preferences
            user_prefs = memory_context.get("user_preferences", {})
            if "communication_style" in user_prefs:
                style = user_prefs["communication_style"]
                system_prompt += f"\n\nUser prefers {style} communication style. Adapt accordingly."

            # Response style guidance
            style_guidance = {
                "empathetic": "Prioritize emotional validation and support.",
                "informative": "Provide clear, helpful information.",
                "helpful": "Focus on practical assistance and solutions.",
                "conversational": "Maintain natural, engaging conversation.",
            }

            response_style = intent.get("response_style")
            if response_style in style_guidance:
                system_prompt += f"\n\n{style_guidance[response_style]}"

            # ============================================================
            # MEMORY INJECTION: Proper conversation history
            # ============================================================
            conversation: List[Dict[str, str]] = []

            # Add relevant memories as ACTUAL conversation context (from past sessions)
            # ENHANCED: Inject up to 10 past conversations (up from 5)
            if memory_context.get("recent_messages"):
                logger.info(f"🧠 Injecting {len(memory_context['recent_messages'])} memories into prompt")
                for msg in memory_context["recent_messages"][-30:]:  # Last 30 memories
                    content = msg.get("content", {})
                    if "messages" in content:
                        # Extract actual user/assistant message pairs
                        for m in content["messages"]:
                            role = m.get("role", "user")
                            text = m.get("content", "")
                            if text:  # Only add non-empty messages
                                conversation.append({
                                    "role": role,
                                    "content": text
                                })
                logger.info(f"✅ Memory injection complete: {len(conversation)} messages from memory")

            # Add in-memory conversation history from THIS SESSION
            for conv in self.conversation_history[-5:]:
                conversation.append({
                    "role": "user",
                    "content": conv["user_message"],
                })
                conversation.append({
                    "role": "assistant",
                    "content": conv["ai_response"],
                })

            # Add current user message
            conversation.append({"role": "user", "content": user_message})
            # ============================================================
            # END MEMORY INJECTION
            # ============================================================

            logger.info(
                f"Prompt built with {len(conversation)} messages, including {len(self.conversation_history)} "
                f"from current session, memory_context={memory_context.get('has_context', False)}, "
                f"is_veteran={self.is_veteran}"
            )

            return {
                "system_prompt": system_prompt,
                "conversation": conversation,
                "emotional_context": emotional_context,
                "intent": intent,
                "context_hint": context_hint,
                "user_preferences": user_prefs,
                "has_memory_context": memory_context.get("has_context", False)
                or bool(self.conversation_history),
            }

        except Exception as e:
            logger.error(f"Prompt building failed: {e}")
            return {
                "system_prompt": self.being_code,
                "conversation": [{"role": "user", "content": user_message}],
                "emotional_context": emotional_context,
                "intent": intent,
                "context_hint": context_hint,
                "user_preferences": {},
                "has_memory_context": False,
            }

    async def _generate_ai_response(
        self,
        prompt_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate AI response using OpenAI API with fallback handling
        """
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
                emotional_context,
                intent,
                len(user_message),
            )

            models_to_try = [
                selected_model,
                self.model_config["fallback"],
                self.model_config["emergency"],
            ]

            for model in models_to_try:
                try:
                    response = self.openai_client.chat.completions.create(
                        model=model,
                        messages=messages,
                        max_tokens=max_tokens,
                        temperature=self.model_config["temperature"],
                    )

                    return {
                        "content": response.choices[0].message.content,
                        "model_used": model,
                        "tokens_used": response.usage.total_tokens,
                        "finish_reason": response.choices[0].finish_reason,
                        "success": True,
                    }

                except Exception as model_error:
                    logger.warning(f"Model {model} failed: {model_error}")
                    continue

            return self._create_fallback_response(prompt_data)

        except Exception as e:
            logger.error(f"AI response generation failed: {e}")
            return self._create_fallback_response(prompt_data)

    def _create_fallback_response(
        self,
        prompt_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create intelligent fallback response when AI is unavailable"""
        try:
            emotional_context = prompt_data.get("emotional_context", {})
            intent = prompt_data.get("intent", {})

            if emotional_context.get("requires_empathy", False):
                fallback_content = (
                    "I can sense this is important to you, and I want to give you the thoughtful "
                    "response you deserve. I'm having some technical difficulties right now, but "
                    "I'm here with you. Could you try again in just a moment?"
                )
            elif intent.get("primary_intent") == "question":
                fallback_content = (
                    "That's a great question, and I want to give you a complete answer. I'm "
                    "experiencing some connectivity issues right now. Please try asking again in "
                    "a moment, and I'll do my best to help."
                )
            elif intent.get("primary_intent") == "greeting":
                fallback_content = (
                    "Hello! I'm so glad you're here. I'm having a brief technical hiccup, but I "
                    "should be back to full capacity in just a moment. How are you doing today?"
                )
            else:
                fallback_content = (
                    "I'm having trouble accessing my full capabilities right now, but I'm still "
                    "here with you. Please try again in a moment, and I'll be ready to continue "
                    "our conversation."
                )

            return {
                "content": fallback_content,
                "model_used": "fallback",
                "tokens_used": 0,
                "is_fallback": True,
                "success": True,
            }

        except Exception as e:
            logger.error(f"Fallback response creation failed: {e}")
            return {
                "content": "I'm experiencing technical difficulties. Please try again shortly.",
                "model_used": "emergency",
                "tokens_used": 0,
                "is_fallback": True,
                "success": False,
            }

    async def _process_ai_response(
        self,
        user_message: str,
        ai_response: Dict[str, Any],
        emotional_context: Dict[str, Any],
        memory_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process AI response and store relevant memories
        """
        try:
            conversation_messages = [
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": ai_response["content"]},
            ]

            memory_id = self.memory.store_conversation_memory(
                messages=conversation_messages,
                emotional_context=emotional_context,
            )

            if emotional_context.get("emotional_intensity", 0.0) > 0.5:
                self.memory.store_emotional_memory(
                    emotion=emotional_context.get("primary_emotion", "neutral"),
                    intensity=emotional_context["emotional_intensity"],
                    context=user_message[:200],
                    trigger=self._extract_emotional_trigger(user_message, emotional_context),
                )

            self.conversation_history.append({
                "user_message": user_message,
                "ai_response": ai_response["content"],
                "timestamp": datetime.utcnow().isoformat(),
                "emotional_context": emotional_context,
                "memory_id": memory_id,
                "ai_response_model": ai_response.get("model_used", "unknown"),
            })

            if len(self.conversation_history) > 10:
                self.conversation_history = self.conversation_history[-10:]

            return {
                "success": True,
                "response": ai_response["content"],
                "metadata": {
                    "model_used": ai_response.get("model_used", "unknown"),
                    "tokens_used": ai_response.get("tokens_used", 0),
                    "is_fallback": ai_response.get("is_fallback", False),
                    "emotional_intensity": emotional_context.get("emotional_intensity", 0.0),
                    "primary_emotion": emotional_context.get("primary_emotion", "neutral"),
                    "memory_id": memory_id,
                    "response_time": datetime.utcnow().isoformat(),
                    "has_followup": emotional_context.get("requires_followup", False),
                    "is_veteran": self.is_veteran,
                    "memory_context_used": memory_context.get("has_context", False),
                },
            }

        except Exception as e:
            logger.error(f"Response processing failed: {e}")
            return {
                "success": True,  # Still return the response even if processing fails
                "response": ai_response.get(
                    "content",
                    "I'm here, but something went wrong processing my reply."
                ),
                "metadata": {
                    "model_used": ai_response.get("model_used", "unknown"),
                    "processing_error": str(e),
                    "is_veteran": self.is_veteran,
                },
            }

    def _extract_emotional_trigger(
        self,
        message: str,
        emotional_context: Dict[str, Any]
    ) -> Optional[str]:
        """Extract potential emotional triggers from message"""
        try:
            primary = emotional_context.get("primary_emotion")
            if primary in ["negative", "anxious"]:
                trigger_patterns = [
                    "because of",
                    "due to",
                    "when",
                    "after",
                    "since",
                    "makes me",
                    "caused by",
                    "resulted from",
                ]

                message_lower = message.lower()
                for pattern in trigger_patterns:
                    if pattern in message_lower:
                        start_idx = message_lower.index(pattern)
                        trigger_context = message[max(0, start_idx - 20): start_idx + 50]
                        return trigger_context.strip()

            return None

        except Exception as e:
            logger.error(f"Trigger extraction failed: {e}")
            return None

    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Create standardized error response"""
        return {
            "success": False,
            "response": error_message,
            "metadata": {
                "model_used": "error",
                "tokens_used": 0,
                "is_error": True,
                "response_time": datetime.utcnow().isoformat(),
                "is_veteran": self.is_veteran,
            },
        }

    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get summary of current conversation session"""
        try:
            if not self.conversation_history:
                return {
                    "message_count": 0,
                    "emotions": {},
                    "topics": [],
                    "average_emotional_intensity": 0.0,
                    "conversation_duration": "0 minutes",
                    "models_used": [],
                    "is_veteran": self.is_veteran,
                }

            emotions = [
                msg["emotional_context"].get("primary_emotion", "neutral")
                for msg in self.conversation_history
            ]
            emotion_counts: Dict[str, int] = {}
            for emotion in emotions:
                emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1

            all_messages = " ".join(
                msg["user_message"] for msg in self.conversation_history
            )
            topics = self._extract_topics(all_messages)

            avg_intensity = (
                sum(
                    msg["emotional_context"].get("emotional_intensity", 0.0)
                    for msg in self.conversation_history
                ) / len(self.conversation_history)
            )

            models_used = list({
                msg.get("ai_response_model", "unknown")
                for msg in self.conversation_history
            })

            return {
                "message_count": len(self.conversation_history),
                "emotions": emotion_counts,
                "topics": topics,
                "average_emotional_intensity": avg_intensity,
                "conversation_duration": self._calculate_duration(),
                "models_used": models_used,
                "is_veteran": self.is_veteran,
            }

        except Exception as e:
            logger.error(f"Conversation summary failed: {e}")
            return {"error": str(e)}

    def _extract_topics(self, text: str) -> List[str]:
        """Extract conversation topics (simplified implementation)"""
        try:
            topics: List[str] = []
            topic_keywords = {
                "work": ["job", "work", "career", "office", "meeting", "project", "boss"],
                "relationships": ["friend", "family", "partner", "relationship", "dating"],
                "health": ["health", "doctor", "medicine", "exercise", "sleep", "diet"],
                "hobbies": ["hobby", "game", "movie", "book", "music", "sport", "travel"],
                "technology": ["computer", "phone", "app", "software", "internet", "ai"],
                "emotions": ["feel", "emotion", "mood", "anxiety", "depression", "happiness"],
            }

            text_lower = text.lower()
            for topic, keywords in topic_keywords.items():
                if any(keyword in text_lower for keyword in keywords):
                    topics.append(topic)

            return topics[:5]

        except Exception as e:
            logger.error(f"Topic extraction failed: {e}")
            return []

    def _calculate_duration(self) -> str:
        """Calculate conversation duration"""
        try:
            if len(self.conversation_history) < 2:
                return "0 minutes"

            first_timestamp = datetime.fromisoformat(
                self.conversation_history[0]["timestamp"]
            )
            last_timestamp = datetime.fromisoformat(
                self.conversation_history[-1]["timestamp"]
            )
            duration = last_timestamp - first_timestamp

            minutes = int(duration.total_seconds() / 60)
            if minutes < 1:
                return "Less than 1 minute"
            elif minutes == 1:
                return "1 minute"
            else:
                return f"{minutes} minutes"

        except Exception as e:
            logger.error(f"Duration calculation failed: {e}")
            return "Unknown"

    def update_user_preferences(self, preferences: Dict[str, Any]) -> bool:
        """Update user preferences based on interaction"""
        try:
            self.memory.store_memory(
                memory_type="emotional",
                content={
                    "preferences": preferences,
                    "updated_at": datetime.utcnow().isoformat(),
                    "source": "user_feedback",
                },
                importance=8,
                tags=["preferences", "user_settings"],
            )

            logger.info(f"Updated user preferences: {preferences}")
            return True

        except Exception as e:
            logger.error(f"Preference update failed: {e}")
            return False

    def get_debug_info(self) -> Dict[str, Any]:
        """Get debug information about orchestrator state"""
        try:
            return {
                "user_id": self.user_id,
                "conversation_length": len(self.conversation_history),
                "memory_stats": self.memory.get_memory_stats(),
                "model_config": self.model_config,
                "being_code_length": len(self.being_code),
                "last_activity": (
                    self.conversation_history[-1]["timestamp"]
                    if self.conversation_history
                    else None
                ),
                "is_veteran": self.is_veteran,
                "user_profile_keys": list(self.user_profile.keys()),
            }

        except Exception as e:
            logger.error(f"Debug info generation failed: {e}")
            return {"error": str(e)}


class EmotionalSafetyMonitor:
    """
    Monitor conversations for emotional safety and intervention needs
    """

    def __init__(self, user_id: str):
        self.user_id = user_id
        self.safety_flags = {
            "suicide_risk": 0,
            "self_harm": 0,
            "crisis_state": 0,
            "severe_depression": 0,
            "aggressive_behavior": 0,
        }

        self.crisis_keywords = {
            "suicide_risk": [
                "kill myself",
                "end my life",
                "suicide",
                "not worth living",
                "better off dead",
            ],
            "self_harm": [
                "cut myself",
                "hurt myself",
                "self harm",
                "punish myself",
            ],
            "crisis_state": [
                "emergency",
                "crisis",
                "can't cope",
                "losing control",
                "breakdown",
            ],
            "severe_depression": [
                "hopeless",
                "worthless",
                "pointless",
                "give up",
                "nothing matters",
            ],
            "aggressive_behavior": [
                "want to hurt",
                "kill them",
                "violence",
                "rage",
                "destroy",
            ],
        }

    def assess_safety(
        self,
        message: str,
        emotional_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Assess emotional safety of user message
        """
        try:
            message_lower = message.lower()
            safety_concerns: List[str] = []
            risk_level = "low"

            for flag_type, keywords in self.crisis_keywords.items():
                if any(keyword in message_lower for keyword in keywords):
                    safety_concerns.append(flag_type)
                    self.safety_flags[flag_type] += 1

            if safety_concerns:
                if any(
                    concern in ["suicide_risk", "self_harm"]
                    for concern in safety_concerns
                ):
                    risk_level = "high"
                elif len(safety_concerns) > 2 or emotional_context.get(
                    "emotional_intensity", 0.0
                ) > 0.8:
                    risk_level = "medium"
                else:
                    risk_level = "elevated"

            total_flags = sum(self.safety_flags.values())
            if total_flags > 3:
                risk_level = "escalating"

            return {
                "risk_level": risk_level,
                "safety_concerns": safety_concerns,
                "requires_intervention": risk_level in ["high", "escalating"],
                "requires_professional_help": (
                    "suicide_risk" in safety_concerns
                    or "self_harm" in safety_concerns
                ),
                "flag_counts": self.safety_flags.copy(),
                "assessment_time": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Safety assessment failed: {e}")
            return {"risk_level": "unknown", "error": str(e)}

    def get_safety_response_guidance(
        self,
        safety_assessment: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get guidance for responding to safety concerns
        """
        try:
            risk_level = safety_assessment.get("risk_level", "unknown")

            if risk_level == "high" or safety_assessment.get(
                "requires_professional_help", False
            ):
                return {
                    "response_tone": "caring_urgent",
                    "include_resources": True,
                    "suggest_professional_help": True,
                    "avoid_dismissal": True,
                    "priority_message": (
                        "I'm very concerned about you right now. "
                        "Your wellbeing matters deeply to me."
                    ),
                    "resources": [
                        "National Suicide Prevention Lifeline: 988",
                        "Crisis Text Line: Text HOME to 741741",
                        "International Association for Suicide Prevention: "
                        "https://www.iasp.info/resources/Crisis_Centres/",
                    ],
                }

            elif risk_level in ["medium", "elevated"]:
                return {
                    "response_tone": "caring_supportive",
                    "include_resources": False,
                    "suggest_professional_help": False,
                    "avoid_dismissal": True,
                    "priority_message": (
                        "I can hear that you're going through a difficult time."
                    ),
                    "guidance": (
                        "Acknowledge their feelings, offer support, gently suggest "
                        "healthy coping strategies."
                    ),
                }

            else:
                return {
                    "response_tone": "normal",
                    "include_resources": False,
                    "suggest_professional_help": False,
                    "avoid_dismissal": False,
                }

        except Exception as e:
            logger.error(f"Safety response guidance failed: {e}")
            return {"response_tone": "normal", "error": str(e)}


# Utility functions
def create_orchestrator(
    user_id: str,
    db,
    openai_client: openai.OpenAI,
    memory_storage: MemoryStorage
) -> CaelOrchestrator:
    """Factory function to create Cael orchestrator"""
    return CaelOrchestrator(user_id, db, openai_client, memory_storage)


def create_safety_monitor(user_id: str) -> EmotionalSafetyMonitor:
    """Factory function to create emotional safety monitor"""
    return EmotionalSafetyMonitor(user_id)


if __name__ == "__main__":
    print("Zentrafuge v9 Orchestrator - FIXED VERSION")
    print("Nov 22, 2025 - Fixed veteran detection + debug logging")
    print()
    print("Fixes applied:")
    print("- Veteran detection reads from veteran_profile.is_veteran (nested)")
    print("- Added debug logging to see memory contents")
    print("- Enhanced memory window with natural relationship continuity")
