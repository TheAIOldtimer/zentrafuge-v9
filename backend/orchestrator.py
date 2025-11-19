#!/usr/bin/env python3
"""
Zentrafuge v9 - Cael Core Orchestrator
Intelligent prompt assembly, memory integration, and emotional processing
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
    - Assemble context-aware prompts
    - Integrate memory and emotional state
    - Route intents and manage conversation flow
    - Process and store AI responses
    - Handle fallbacks and error recovery
    """
    
    def __init__(self, user_id: str, db, openai_client: openai.OpenAI, 
                 memory_storage: MemoryStorage):
        self.user_id = user_id
        self.db = db
        self.openai_client = openai_client
        self.memory = memory_storage
        self.being_code = self._load_being_code()
        self.conversation_history = []
        
        # Model configuration with fallbacks
        self.model_config = {
            'primary': 'gpt-4',
            'fallback': 'gpt-3.5-turbo',
            'emergency': 'gpt-3.5-turbo',
            'max_tokens': 800,
            'temperature': 0.7,
            'cost_threshold_usd': 10.0  # Daily spending limit
        }
                     
    def _load_being_code(self) -> str:
        """Load Cael's being code (identity and moral contract)"""
        try:
            # Get current date/time for context
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
        
    async def process_message(self, user_message: str, 
                            context_hint: str = None) -> Dict[str, Any]:
        """
        Process incoming user message and generate contextual response
        
        Args:
            user_message: User's input message
            context_hint: Optional context hint for response generation
            
        Returns:
            Dictionary containing response and metadata
        """
        try:
            # Validate and sanitize input
            clean_message = DataValidator.sanitize_user_input(user_message)
            if not clean_message:
                return self._create_error_response("Message could not be processed")
            
            # Analyze emotional context
            emotional_analysis = self._analyze_emotional_context(clean_message)
            
            # Retrieve relevant memories
            memory_context = self._build_memory_context(clean_message, emotional_analysis)
            
            # Detect user intent
            intent_analysis = self._analyze_intent(clean_message, emotional_analysis)
            
            # Build comprehensive prompt
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
            return self._create_error_response("I'm having trouble processing your message right now.")
    
    def _analyze_emotional_context(self, message: str) -> Dict[str, Any]:
        """
        Analyze emotional context of user message
        
        Args:
            message: User message to analyze
            
        Returns:
            Emotional analysis results
        """
        try:
            # Simple emotion detection (in production, use more sophisticated NLP)
            emotions = {
                'positive': ['happy', 'excited', 'great', 'awesome', 'love', 'wonderful'],
                'negative': ['sad', 'angry', 'frustrated', 'upset', 'hate', 'terrible'],
                'anxious': ['worried', 'nervous', 'anxious', 'stressed', 'concerned'],
                'grateful': ['thank', 'grateful', 'appreciate', 'thanks'],
                'confused': ['confused', 'don\'t understand', 'unclear', 'lost']
            }
            
            message_lower = message.lower()
            detected_emotions = []
            emotional_intensity = 0.0
            
            for emotion, keywords in emotions.items():
                if any(keyword in message_lower for keyword in keywords):
                    detected_emotions.append(emotion)
                    emotional_intensity += 0.3
            
            # Detect emotional markers
            exclamation_count = message.count('!')
            question_count = message.count('?')
            caps_ratio = sum(1 for c in message if c.isupper()) / len(message) if message else 0
            
            # Adjust intensity based on markers
            emotional_intensity += min(exclamation_count * 0.1, 0.3)
            emotional_intensity += min(caps_ratio * 0.5, 0.4)
            
            return {
                'detected_emotions': detected_emotions,
                'primary_emotion': detected_emotions[0] if detected_emotions else 'neutral',
                'emotional_intensity': min(emotional_intensity, 1.0),
                'exclamation_count': exclamation_count,
                'question_count': question_count,
                'caps_ratio': caps_ratio,
                'requires_empathy': emotional_intensity > 0.5,
                'requires_followup': any(emotion in ['negative', 'anxious'] for emotion in detected_emotions)
            }
            
        except Exception as e:
            logger.error(f"Emotional analysis failed: {e}")
            return {'detected_emotions': [], 'primary_emotion': 'neutral', 'emotional_intensity': 0.0}
    
    def _analyze_intent(self, message: str, emotional_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze user intent from message
        
        Args:
            message: User message
            emotional_context: Emotional analysis results
            
        Returns:
            Intent analysis results
        """
        try:
            intents = {
                'question': ['what', 'how', 'why', 'when', 'where', 'who', '?'],
                'request': ['can you', 'could you', 'please', 'help me'],
                'sharing': ['i feel', 'i think', 'i want', 'i need', 'my'],
                'greeting': ['hello', 'hi', 'hey', 'good morning', 'good evening'],
                'goodbye': ['bye', 'goodbye', 'see you', 'talk later'],
                'gratitude': ['thank you', 'thanks', 'appreciate'],
                'complaint': ['problem', 'issue', 'wrong', 'broken', 'error'],
                'compliment': ['great', 'awesome', 'amazing', 'wonderful', 'perfect']
            }
            
            message_lower = message.lower()
            detected_intents = []
            
            for intent, keywords in intents.items():
                if any(keyword in message_lower for keyword in keywords):
                    detected_intents.append(intent)
            
            # Determine primary intent
            primary_intent = 'conversation'  # Default
            if detected_intents:
                # Priority order for intents
                intent_priority = ['greeting', 'goodbye', 'gratitude', 'complaint', 
                                 'question', 'request', 'sharing', 'compliment']
                for intent in intent_priority:
                    if intent in detected_intents:
                        primary_intent = intent
                        break
            
            # Determine response style needed
            response_style = 'conversational'
            if primary_intent == 'question':
                response_style = 'informative'
            elif primary_intent in ['complaint', 'sharing'] and emotional_context['requires_empathy']:
                response_style = 'empathetic'
            elif primary_intent == 'request':
                response_style = 'helpful'
            
            return {
                'detected_intents': detected_intents,
                'primary_intent': primary_intent,
                'response_style': response_style,
                'needs_action': primary_intent in ['request', 'complaint'],
                'is_emotional': emotional_context['emotional_intensity'] > 0.3
            }
            
        except Exception as e:
            logger.error(f"Intent analysis failed: {e}")
            return {'primary_intent': 'conversation', 'response_style': 'conversational'}
    
    def _build_memory_context(self, message: str, emotional_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build relevant memory context for response generation
        
        Args:
            message: User message
            emotional_context: Emotional analysis
            
        Returns:
            Memory context for prompt building
        """
        try:
            # Get recent conversation context
            recent_messages = self.memory.get_conversation_context(max_messages=5)
            
            # Get emotional profile
            emotional_profile = self.memory.get_emotional_profile()
            
            # Search for relevant memories based on message content
            relevant_memories = self.memory.search_memories(
                importance_threshold=6,
                limit=3
            )
            
            # Get user preferences if emotional situation
            user_preferences = {}
            if emotional_context['requires_empathy']:
                pref_memories = self.memory.search_memories(
                    memory_type='emotional',
                    tags=['preferences'],
                    limit=5
                )
                for mem in pref_memories:
                    if 'communication_style' in mem['content']:
                        user_preferences['communication_style'] = mem['content']['communication_style']
            
            return {
                'recent_messages': recent_messages[-3:] if recent_messages else [],  # Last 3 messages
                'emotional_profile': emotional_profile,
                'relevant_memories': relevant_memories,
                'user_preferences': user_preferences,
                'conversation_length': len(recent_messages),
                'has_context': len(recent_messages) > 0 or len(relevant_memories) > 0
            }
            
        except Exception as e:
            logger.error(f"Memory context building failed: {e}")
            return {'has_context': False, 'recent_messages': []}
    
    def _build_prompt(self, user_message: str, memory_context: Dict[str, Any],
                     emotional_context: Dict[str, Any], intent: Dict[str, Any],
                     context_hint: str = None) -> Dict[str, Any]:
        """
        Build comprehensive prompt for AI response generation
        
        Args:
            user_message: User's message
            memory_context: Memory and context information
            emotional_context: Emotional analysis
            intent: Intent analysis
            context_hint: Optional context hint
            
        Returns:
            Structured prompt data
        """
        try:
            # Build system prompt
            system_prompt = self.being_code
            
            # Add emotional guidance
            if emotional_context['requires_empathy']:
                system_prompt += f"\n\nThe user is experiencing {emotional_context['primary_emotion']} emotions. Respond with extra empathy and care."
            
            # Add communication style preferences
            user_prefs = memory_context.get('user_preferences', {})
            if 'communication_style' in user_prefs:
                style = user_prefs['communication_style']
                system_prompt += f"\n\nUser prefers {style} communication style. Adapt accordingly."
            
            # Add response style guidance
            style_guidance = {
                'empathetic': "Prioritize emotional validation and support.",
                'informative': "Provide clear, helpful information.",
                'helpful': "Focus on practical assistance and solutions.",
                'conversational': "Maintain natural, engaging conversation."
            }
            
            if intent['response_style'] in style_guidance:
                system_prompt += f"\n\n{style_guidance[intent['response_style']]}"
            
            # Build conversation history
            conversation = []
            
            # Add relevant memories as context (from past sessions)
            if memory_context.get('recent_messages'):
                memory_context_str = "Context from our previous conversations:\n"
                for msg in memory_context['recent_messages'][-3:]:  # Last 3 from database
                    content = msg.get('content', {})
                    if 'messages' in content:
                        for message in content['messages']:
                            role = message.get('role', 'user')
                            text = message.get('content', '')[:150]  # First 150 chars
                            memory_context_str += f"{role.capitalize()}: {text}\n"
                
                if len(memory_context_str) > 50:  # Only add if we have content
                    conversation.append({"role": "system", "content": memory_context_str.strip()})
            
            # Add in-memory conversation history from THIS SESSION
            # This ensures continuity within the current conversation
            for conv in self.conversation_history[-5:]:  # Last 5 from current session
                conversation.append({"role": "user", "content": conv['user_message']})
                conversation.append({"role": "assistant", "content": conv['ai_response']})
            
            # Add current user message
            conversation.append({"role": "user", "content": user_message})
            
            # Log what we're sending (for debugging)
            logger.info(f"Prompt built with {len(conversation)} messages, "
                       f"including {len(self.conversation_history)} from current session, "
                       f"memory_context: {memory_context.get('has_context', False)}")
            
            return {
                'system_prompt': system_prompt,
                'conversation': conversation,
                'emotional_context': emotional_context,
                'intent': intent,
                'context_hint': context_hint,
                'user_preferences': user_prefs,
                'has_memory_context': memory_context['has_context'] or len(self.conversation_history) > 0
            }
            
        except Exception as e:
            logger.error(f"Prompt building failed: {e}")
            return {
                'system_prompt': self.being_code,
                'conversation': [{"role": "user", "content": user_message}],
                'has_memory_context': False
            }
    
    async def _generate_ai_response(self, prompt_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate AI response using OpenAI API with fallback handling
        
        Args:
            prompt_data: Structured prompt data
            
        Returns:
            AI response data
        """
        try:
            # Prepare messages for OpenAI
            messages = [{"role": "system", "content": prompt_data['system_prompt']}]
            messages.extend(prompt_data['conversation'])
            
            # Try primary model first
            models_to_try = [
                self.model_config['primary'],
                self.model_config['fallback'],
                self.model_config['emergency']
            ]
            
            for model in models_to_try:
                try:
                    response = self.openai_client.chat.completions.create(
                        model=model,
                        messages=messages,
                        max_tokens=self.model_config['max_tokens'],
                        temperature=self.model_config['temperature']
                    )
                    
                    return {
                        'content': response.choices[0].message.content,
                        'model_used': model,
                        'tokens_used': response.usage.total_tokens,
                        'finish_reason': response.choices[0].finish_reason,
                        'success': True
                    }
                    
                except Exception as model_error:
                    logger.warning(f"Model {model} failed: {model_error}")
                    continue
            
            # If all models fail, return fallback response
            return self._create_fallback_response(prompt_data)
            
        except Exception as e:
            logger.error(f"AI response generation failed: {e}")
            return self._create_fallback_response(prompt_data)
    
    def _create_fallback_response(self, prompt_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create intelligent fallback response when AI is unavailable"""
        try:
            emotional_context = prompt_data.get('emotional_context', {})
            intent = prompt_data.get('intent', {})
            
            # Emotionally appropriate fallback responses
            if emotional_context.get('requires_empathy', False):
                fallback_content = "I can sense this is important to you, and I want to give you the thoughtful response you deserve. I'm having some technical difficulties right now, but I'm here with you. Could you try again in just a moment?"
            elif intent.get('primary_intent') == 'question':
                fallback_content = "That's a great question, and I want to give you a complete answer. I'm experiencing some connectivity issues right now. Please try asking again in a moment, and I'll do my best to help."
            elif intent.get('primary_intent') == 'greeting':
                fallback_content = "Hello! I'm so glad you're here. I'm having a brief technical hiccup, but I should be back to full capacity in just a moment. How are you doing today?"
            else:
                fallback_content = "I'm having trouble accessing my full capabilities right now, but I'm still here with you. Please try again in a moment, and I'll be ready to continue our conversation."
            
            return {
                'content': fallback_content,
                'model_used': 'fallback',
                'tokens_used': 0,
                'is_fallback': True,
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Fallback response creation failed: {e}")
            return {
                'content': "I'm experiencing technical difficulties. Please try again shortly.",
                'model_used': 'emergency',
                'tokens_used': 0,
                'is_fallback': True,
                'success': False
            }
    
    async def _process_ai_response(self, user_message: str, ai_response: Dict[str, Any],
                                 emotional_context: Dict[str, Any], 
                                 memory_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process AI response and store relevant memories
        
        Args:
            user_message: Original user message
            ai_response: Generated AI response
            emotional_context: Emotional analysis
            memory_context: Memory context used
            
        Returns:
            Processed response data with metadata
        """
        try:
            # Store conversation memory
            conversation_messages = [
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": ai_response['content']}
            ]
            
            # Store conversation with emotional context
            memory_id = self.memory.store_conversation_memory(
                messages=conversation_messages,
                emotional_context=emotional_context
            )
            
            # Store emotional memory if significant
            if emotional_context['emotional_intensity'] > 0.5:
                self.memory.store_emotional_memory(
                    emotion=emotional_context['primary_emotion'],
                    intensity=emotional_context['emotional_intensity'],
                    context=user_message[:200],  # First 200 chars as context
                    trigger=self._extract_emotional_trigger(user_message, emotional_context)
                )
            
            # Update conversation history
            self.conversation_history.append({
                'user_message': user_message,
                'ai_response': ai_response['content'],
                'timestamp': datetime.utcnow().isoformat(),
                'emotional_context': emotional_context,
                'memory_id': memory_id
            })
            
            # Keep only recent history in memory
            if len(self.conversation_history) > 10:
                self.conversation_history = self.conversation_history[-10:]
            
            return {
                'success': True,
                'response': ai_response['content'],
                'metadata': {
                    'model_used': ai_response['model_used'],
                    'tokens_used': ai_response.get('tokens_used', 0),
                    'is_fallback': ai_response.get('is_fallback', False),
                    'emotional_intensity': emotional_context['emotional_intensity'],
                    'primary_emotion': emotional_context['primary_emotion'],
                    'memory_id': memory_id,
                    'response_time': datetime.utcnow().isoformat(),
                    'has_followup': emotional_context.get('requires_followup', False)
                }
            }
            
        except Exception as e:
            logger.error(f"Response processing failed: {e}")
            return {
                'success': True,  # Still return the response even if processing fails
                'response': ai_response['content'],
                'metadata': {
                    'model_used': ai_response['model_used'],
                    'processing_error': str(e)
                }
            }
    
    def _extract_emotional_trigger(self, message: str, emotional_context: Dict[str, Any]) -> Optional[str]:
        """Extract potential emotional triggers from message"""
        try:
            if emotional_context['primary_emotion'] in ['negative', 'anxious']:
                # Look for common trigger patterns
                trigger_patterns = [
                    'because of', 'due to', 'when', 'after', 'since',
                    'makes me', 'caused by', 'resulted from'
                ]
                
                message_lower = message.lower()
                for pattern in trigger_patterns:
                    if pattern in message_lower:
                        # Extract context around the trigger pattern
                        start_idx = message_lower.index(pattern)
                        trigger_context = message[max(0, start_idx-20):start_idx+50]
                        return trigger_context.strip()
            
            return None
            
        except Exception as e:
            logger.error(f"Trigger extraction failed: {e}")
            return None
    
    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Create standardized error response"""
        return {
            'success': False,
            'response': error_message,
            'metadata': {
                'model_used': 'error',
                'tokens_used': 0,
                'is_error': True,
                'response_time': datetime.utcnow().isoformat()
            }
        }
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get summary of current conversation session"""
        try:
            if not self.conversation_history:
                return {'message_count': 0, 'emotions': [], 'topics': []}
            
            # Analyze conversation patterns
            emotions = [msg['emotional_context']['primary_emotion'] for msg in self.conversation_history]
            emotion_counts = {}
            for emotion in emotions:
                emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
            
            # Extract topics (simplified)
            all_messages = ' '.join([msg['user_message'] for msg in self.conversation_history])
            topics = self._extract_topics(all_messages)
            
            return {
                'message_count': len(self.conversation_history),
                'emotions': emotion_counts,
                'topics': topics,
                'average_emotional_intensity': sum(
                    msg['emotional_context']['emotional_intensity'] 
                    for msg in self.conversation_history
                ) / len(self.conversation_history),
                'conversation_duration': self._calculate_duration(),
                'models_used': list(set(msg.get('metadata', {}).get('model_used', 'unknown') 
                                      for msg in self.conversation_history))
            }
            
        except Exception as e:
            logger.error(f"Conversation summary failed: {e}")
            return {'error': str(e)}
    
    def _extract_topics(self, text: str) -> List[str]:
        """Extract conversation topics (simplified implementation)"""
        try:
            topics = []
            topic_keywords = {
                'work': ['job', 'work', 'career', 'office', 'meeting', 'project', 'boss'],
                'relationships': ['friend', 'family', 'partner', 'relationship', 'dating'],
                'health': ['health', 'doctor', 'medicine', 'exercise', 'sleep', 'diet'],
                'hobbies': ['hobby', 'game', 'movie', 'book', 'music', 'sport', 'travel'],
                'technology': ['computer', 'phone', 'app', 'software', 'internet', 'ai'],
                'emotions': ['feel', 'emotion', 'mood', 'anxiety', 'depression', 'happiness']
            }
            
            text_lower = text.lower()
            for topic, keywords in topic_keywords.items():
                if any(keyword in text_lower for keyword in keywords):
                    topics.append(topic)
            
            return topics[:5]  # Return top 5 topics
            
        except Exception as e:
            logger.error(f"Topic extraction failed: {e}")
            return []
    
    def _calculate_duration(self) -> str:
        """Calculate conversation duration"""
        try:
            if len(self.conversation_history) < 2:
                return "0 minutes"
            
            first_timestamp = datetime.fromisoformat(self.conversation_history[0]['timestamp'])
            last_timestamp = datetime.fromisoformat(self.conversation_history[-1]['timestamp'])
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
            # Store preferences as emotional memory
            self.memory.store_memory(
                memory_type='emotional',
                content={
                    'preferences': preferences,
                    'updated_at': datetime.utcnow().isoformat(),
                    'source': 'user_feedback'
                },
                importance=8,
                tags=['preferences', 'user_settings']
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
                'user_id': self.user_id,
                'conversation_length': len(self.conversation_history),
                'memory_stats': self.memory.get_memory_stats(),
                'model_config': self.model_config,
                'being_code_length': len(self.being_code),
                'last_activity': self.conversation_history[-1]['timestamp'] if self.conversation_history else None
            }
            
        except Exception as e:
            logger.error(f"Debug info generation failed: {e}")
            return {'error': str(e)}


class EmotionalSafetyMonitor:
    """
    Monitor conversations for emotional safety and intervention needs
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.safety_flags = {
            'suicide_risk': 0,
            'self_harm': 0,
            'crisis_state': 0,
            'severe_depression': 0,
            'aggressive_behavior': 0
        }
        
        # Safety keywords that trigger monitoring
        self.crisis_keywords = {
            'suicide_risk': ['kill myself', 'end my life', 'suicide', 'not worth living', 'better off dead'],
            'self_harm': ['cut myself', 'hurt myself', 'self harm', 'punish myself'],
            'crisis_state': ['emergency', 'crisis', 'can\'t cope', 'losing control', 'breakdown'],
            'severe_depression': ['hopeless', 'worthless', 'pointless', 'give up', 'nothing matters'],
            'aggressive_behavior': ['want to hurt', 'kill them', 'violence', 'rage', 'destroy']
        }
    
    def assess_safety(self, message: str, emotional_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess emotional safety of user message
        
        Args:
            message: User message to assess
            emotional_context: Emotional analysis of message
            
        Returns:
            Safety assessment results
        """
        try:
            message_lower = message.lower()
            safety_concerns = []
            risk_level = 'low'
            
            # Check for crisis keywords
            for flag_type, keywords in self.crisis_keywords.items():
                if any(keyword in message_lower for keyword in keywords):
                    safety_concerns.append(flag_type)
                    self.safety_flags[flag_type] += 1
            
            # Assess overall risk level
            if safety_concerns:
                if any(concern in ['suicide_risk', 'self_harm'] for concern in safety_concerns):
                    risk_level = 'high'
                elif len(safety_concerns) > 2 or emotional_context['emotional_intensity'] > 0.8:
                    risk_level = 'medium'
                else:
                    risk_level = 'elevated'
            
            # Check for escalating patterns
            total_flags = sum(self.safety_flags.values())
            if total_flags > 3:
                risk_level = 'escalating'
            
            return {
                'risk_level': risk_level,
                'safety_concerns': safety_concerns,
                'requires_intervention': risk_level in ['high', 'escalating'],
                'requires_professional_help': 'suicide_risk' in safety_concerns or 'self_harm' in safety_concerns,
                'flag_counts': self.safety_flags.copy(),
                'assessment_time': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Safety assessment failed: {e}")
            return {'risk_level': 'unknown', 'error': str(e)}
    
    def get_safety_response_guidance(self, safety_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get guidance for responding to safety concerns
        
        Args:
            safety_assessment: Results from assess_safety()
            
        Returns:
            Response guidance for the AI
        """
        try:
            risk_level = safety_assessment['risk_level']
            concerns = safety_assessment['safety_concerns']
            
            if risk_level == 'high' or safety_assessment.get('requires_professional_help'):
                return {
                    'response_tone': 'caring_urgent',
                    'include_resources': True,
                    'suggest_professional_help': True,
                    'avoid_dismissal': True,
                    'priority_message': "I'm very concerned about you right now. Your wellbeing matters deeply to me.",
                    'resources': [
                        "National Suicide Prevention Lifeline: 988",
                        "Crisis Text Line: Text HOME to 741741",
                        "International Association for Suicide Prevention: https://www.iasp.info/resources/Crisis_Centres/"
                    ]
                }
            
            elif risk_level in ['medium', 'elevated']:
                return {
                    'response_tone': 'caring_supportive',
                    'include_resources': False,
                    'suggest_professional_help': False,
                    'avoid_dismissal': True,
                    'priority_message': "I can hear that you're going through a difficult time.",
                    'guidance': "Acknowledge their feelings, offer support, gently suggest healthy coping strategies."
                }
            
            else:
                return {
                    'response_tone': 'normal',
                    'include_resources': False,
                    'suggest_professional_help': False,
                    'avoid_dismissal': False
                }
                
        except Exception as e:
            logger.error(f"Safety response guidance failed: {e}")
            return {'response_tone': 'normal'}


# Utility functions
def create_orchestrator(user_id: str, db, openai_client: openai.OpenAI, 
                       memory_storage: MemoryStorage) -> CaelOrchestrator:
    """
    Factory function to create Cael orchestrator
    
    Args:
        user_id: User identifier
        db: Firestore database client
        openai_client: OpenAI client instance
        memory_storage: Memory storage instance
        
    Returns:
        Configured CaelOrchestrator
    """
    return CaelOrchestrator(user_id, db, openai_client, memory_storage)


def create_safety_monitor(user_id: str) -> EmotionalSafetyMonitor:
    """
    Factory function to create emotional safety monitor
    
    Args:
        user_id: User identifier
        
    Returns:
        Configured EmotionalSafetyMonitor
    """
    return EmotionalSafetyMonitor(user_id)


if __name__ == "__main__":
    # Test emotional analysis
    test_messages = [
        "I'm feeling really happy today!",
        "I'm so frustrated with everything...",
        "Can you help me understand this?",
        "Thank you for being there for me",
        "I don't know what to do anymore"
    ]
    
    # This would require actual initialization in a real test
    print("Zentrafuge v9 Orchestrator - Test Suite")
    print("Note: Full testing requires database and OpenAI connections")
    
    for msg in test_messages:
        print(f"\nMessage: {msg}")
        # Would test emotional analysis, intent detection, etc.
        print("  (Analysis would appear here with full setup)")
