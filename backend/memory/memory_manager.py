#!/usr/bin/env python3
"""
Zentrafuge v10 - Memory Manager
Central orchestrator for the multi-tier memory system
WITH ENCRYPTION + ENHANCED RETRIEVAL + VALUES CONTEXT
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from firebase_admin import firestore
from openai import OpenAI

from .persistent_facts import PersistentFacts
from .micro_memory import MicroMemory
from .memory_consolidator import MemoryConsolidator

# Import encryption utilities
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from crypto_handler import encrypt_text, decrypt_text

logger = logging.getLogger(__name__)


class MemoryManager:
    """
    Central memory management system with encryption + enhanced retrieval
    
    Orchestrates:
    - Persistent facts (never forgotten) - ENCRYPTED
    - Micro memories (session summaries with decay) - ENCRYPTED
    - Super memories (consolidated patterns) - ENCRYPTED
    - Values context (core beliefs and principles)
    - Smart retrieval with relevance scoring
    - Automatic consolidation when thresholds reached
    
    NEW in v10:
    - get_values_context() for values-aware conversations
    - relevance_threshold parameter for smarter retrieval
    - consolidate_session_memories() with importance boosting
    - Emotional pattern storage and retrieval
    """
    
    def __init__(
        self,
        db: firestore.Client,
        user_id: str,
        openai_client: OpenAI
    ):
        self.db = db
        self.user_id = user_id
        self.openai_client = openai_client
        
        # Initialize memory subsystems
        self.facts = PersistentFacts(db, user_id)
        self.micro = MicroMemory(db, user_id)
        self.consolidator = MemoryConsolidator(db, user_id, openai_client)
        
        # Session tracking
        self.current_session_messages: List[Dict[str, str]] = []
        self.session_start_time = datetime.utcnow()
        
        logger.info(f"🧠 Memory Manager v10 initialized for user {user_id} (encryption enabled)")
    
    # =========================================================================
    # PERSISTENT FACTS API
    # =========================================================================
    
    def set_fact(self, category: str, key: str, value: Any, source: str = "user") -> bool:
        """Set a persistent fact (encrypted)"""
        return self.facts.set_fact(category, key, value, source)
    
    def get_fact(self, category: str, key: str) -> Optional[Any]:
        """Get a persistent fact (decrypted)"""
        return self.facts.get_fact(category, key)
    
    def get_all_facts(self) -> Dict[str, Any]:
        """Get all persistent facts (decrypted)"""
        return self.facts.get_all_facts()
    
    def import_onboarding(self, onboarding_data: Dict[str, Any]) -> int:
        """
        Import facts from onboarding data (will be encrypted)
        NOW ALSO IMPORTS VALUES if present in onboarding_data
        """
        count = self.facts.import_from_onboarding(onboarding_data)
        
        # Import values if present
        if 'core_values' in onboarding_data:
            values = onboarding_data['core_values']
            if isinstance(values, list):
                self.facts.set_fact('values', 'core_values', values, 'onboarding')
                count += 1
        
        # Import value definitions if present
        if 'value_definitions' in onboarding_data:
            definitions = onboarding_data['value_definitions']
            if isinstance(definitions, dict):
                self.facts.set_fact('values', 'value_definitions', definitions, 'onboarding')
                count += 1
        
        return count
    
    # =========================================================================
    # VALUES CONTEXT (NEW!)
    # =========================================================================
    
    def get_values_context(self) -> str:
        """
        Get natural language summary of user's core values
        
        Returns:
            Formatted string describing user's values and what they mean in practice
        """
        try:
            core_values = self.facts.get_fact('values', 'core_values')
            value_definitions = self.facts.get_fact('values', 'value_definitions')
            
            if not core_values:
                return ""
            
            lines = ["=== USER'S CORE VALUES ==="]
            
            if isinstance(core_values, list):
                lines.append(f"\nCore values: {', '.join(core_values)}")
                
                # Add definitions if available
                if isinstance(value_definitions, dict):
                    lines.append("\nWhat these values mean in practice:")
                    for value in core_values:
                        if value in value_definitions:
                            definition = value_definitions[value]
                            lines.append(f"  • {value.capitalize()}: {definition}")
            
            # Add sources of meaning if available
            sources_of_meaning = self.facts.get_fact('values', 'sources_of_meaning')
            if sources_of_meaning:
                lines.append(f"\nSources of meaning: {', '.join(sources_of_meaning)}")
            
            # Add life chapter context if available
            life_chapter = self.facts.get_fact('values', 'life_chapter')
            if life_chapter:
                lines.append(f"\nCurrent life chapter: {life_chapter}")
            
            return "\n".join(lines)
            
        except Exception as e:
            logger.error(f"Failed to get values context: {e}")
            return ""
    
    # =========================================================================
    # SESSION MANAGEMENT
    # =========================================================================
    
    def add_message_to_session(self, role: str, content: str):
        """
        Add a message to the current session
        
        Args:
            role: 'user' or 'assistant'
            content: Message content (will be encrypted when saved)
        """
        self.current_session_messages.append({
            'role': role,
            'content': content,  # Keep plaintext in memory for current session
            'timestamp': datetime.utcnow().isoformat()
        })
    
    async def end_session(self, reason: str = "logout") -> Optional[str]:
        """
        End current session and create micro memory (encrypted)
        
        Args:
            reason: Reason for ending session (logout, timeout, etc.)
            
        Returns:
            micro_memory_id or None
        """
        try:
            if len(self.current_session_messages) < 2:
                logger.info(f"⏭️ Session too short to create micro memory (reason: {reason})")
                return None
            
            logger.info(
                f"🔚 Ending session for user {self.user_id}: "
                f"{len(self.current_session_messages)} messages (reason: {reason})"
            )
            
            # Generate session summary
            summary = await self._generate_session_summary()
            
            # Extract emotional context
            emotional_context = self._extract_session_emotions()
            
            # Extract topics
            topics = self._extract_session_topics()
            
            # Determine importance
            importance = self._calculate_session_importance(emotional_context, topics)
            
            # Create micro memory (encryption happens inside micro.create_micro_memory)
            micro_memory_id = self.micro.create_micro_memory(
                summary=summary,
                messages=self.current_session_messages,
                emotional_context=emotional_context,
                topics=topics,
                initial_importance=importance
            )
            
            # Extract facts from session
            self._extract_facts_from_session()
            
            # Check if consolidation is needed
            if self.consolidator.check_consolidation_ready(self.micro):
                logger.info("🔄 Consolidation threshold reached, triggering consolidation...")
                await self.consolidator.consolidate_memories(self.micro)
            
            # Clear session
            self.current_session_messages = []
            self.session_start_time = datetime.utcnow()
            
            return micro_memory_id
            
        except Exception as e:
            logger.error(f"❌ Failed to end session: {e}")
            return None
    
    async def consolidate_session_memories(self, importance_boost: float = 0.0) -> Optional[str]:
        """
        NEW: Manually trigger memory consolidation with optional importance boost
        
        Args:
            importance_boost: Additional importance to add (e.g., 0.3 for emotionally significant moments)
            
        Returns:
            super_memory_id or None
        """
        try:
            logger.info(f"🔄 Manual consolidation triggered (boost={importance_boost})")
            
            # Get unconsolidated memories
            memories = self.micro.get_recent_micro_memories(
                limit=self.consolidator.CONSOLIDATION_THRESHOLD,
                min_importance=2.0,
                apply_decay=False
            )
            
            if not memories:
                logger.info("No memories to consolidate")
                return None
            
            # Apply importance boost if specified
            if importance_boost > 0:
                for memory in memories:
                    # Update importance in Firestore
                    self.micro.boost_importance(
                        memory['memory_id'],
                        importance_boost
                    )
            
            # Run consolidation
            super_memory_id = await self.consolidator.consolidate_memories(self.micro)
            
            return super_memory_id
            
        except Exception as e:
            logger.error(f"Failed to consolidate session memories: {e}")
            return None
    
    async def _generate_session_summary(self) -> str:
        """Generate a summary of the current session using OpenAI"""
        try:
            # Build conversation text
            conversation_text = "\n".join([
                f"{msg['role']}: {msg['content']}"
                for msg in self.current_session_messages[-20:]  # Last 20 messages
            ])
            
            # Call OpenAI for summary
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Summarize this conversation in 2-3 sentences. "
                            "Focus on: main topics discussed, user's emotional state, "
                            "and any key information shared."
                        )
                    },
                    {
                        "role": "user",
                        "content": f"Summarize this conversation:\n\n{conversation_text}"
                    }
                ],
                max_tokens=150,
                temperature=0.3
            )
            
            summary = response.choices[0].message.content
            logger.info(f"📝 Generated session summary: {summary[:100]}...")
            
            return summary
            
        except Exception as e:
            logger.error(f"❌ Failed to generate session summary: {e}")
            # Fallback summary
            return f"Conversation with {len(self.current_session_messages)} messages"
    
    def _extract_session_emotions(self) -> Dict[str, Any]:
        """Extract emotional context from session"""
        # Simple emotion detection (can be enhanced)
        emotions: List[str] = []
        intensities: List[float] = []
        
        for msg in self.current_session_messages:
            if msg['role'] == 'user':
                content_lower = msg['content'].lower()
                
                # Check for emotional keywords
                if any(word in content_lower for word in ['sad', 'upset', 'depressed', 'down']):
                    emotions.append('negative')
                    intensities.append(0.7)
                elif any(word in content_lower for word in ['happy', 'great', 'excited', 'wonderful']):
                    emotions.append('positive')
                    intensities.append(0.6)
                elif any(word in content_lower for word in ['worried', 'anxious', 'nervous', 'scared']):
                    emotions.append('anxious')
                    intensities.append(0.7)
        
        if emotions:
            avg_intensity = sum(intensities) / len(intensities)
            primary_emotion = max(set(emotions), key=emotions.count)
        else:
            avg_intensity = 0.0
            primary_emotion = 'neutral'
        
        return {
            'primary_emotion': primary_emotion,
            'emotional_intensity': avg_intensity,
            'emotions_detected': list(set(emotions))
        }
    
    def _extract_session_topics(self) -> List[str]:
        """Extract topics from session messages"""
        topics: List[str] = []
        
        # Combine all user messages
        all_text = " ".join([
            msg['content'].lower()
            for msg in self.current_session_messages
            if msg['role'] == 'user'
        ])
        
        # Topic keywords
        topic_map = {
            'work': ['work', 'job', 'career', 'office', 'project', 'meeting'],
            'relationships': ['friend', 'family', 'partner', 'relationship', 'dating'],
            'health': ['health', 'doctor', 'medicine', 'exercise', 'sleep'],
            'hobbies': ['hobby', 'game', 'movie', 'book', 'music', 'sport'],
            'emotions': ['feel', 'emotion', 'mood', 'anxiety', 'depression'],
            'pets': ['dog', 'cat', 'pet', 'animal'],
            'goals': ['goal', 'plan', 'dream', 'ambition', 'aspiration'],
            'values': ['value', 'important', 'matter', 'meaningful', 'purpose']
        }
        
        for topic, keywords in topic_map.items():
            if any(keyword in all_text for keyword in keywords):
                topics.append(topic)
        
        return topics
    
    def _calculate_session_importance(
        self,
        emotional_context: Dict[str, Any],
        topics: List[str]
    ) -> float:
        """Calculate importance score for session (1-10)"""
        importance = 5.0  # Base importance
        
        # Emotional sessions are more important
        if emotional_context['emotional_intensity'] > 0.5:
            importance += 2.0
        
        # Values discussions are highly important
        if 'values' in topics:
            importance += 1.5
        
        # More topics = more important
        importance += min(len(topics) * 0.5, 2.0)
        
        # Long sessions are more important
        if len(self.current_session_messages) > 20:
            importance += 1.0
        
        return min(importance, 10.0)
    
    def _extract_facts_from_session(self):
        """Extract persistent facts from session messages"""
        try:
            for msg in self.current_session_messages:
                if msg['role'] == 'user':
                    # Try to extract facts (will be encrypted by facts module)
                    self.facts.extract_facts_from_message(
                        msg['content'],
                        ""  # We don't have AI response here
                    )
        except Exception as e:
            logger.error(f"❌ Failed to extract facts from session: {e}")
    
    # =========================================================================
    # ENHANCED MEMORY RETRIEVAL (WITH RELEVANCE + DECRYPTION)
    # =========================================================================
    
    def get_context_for_prompt(
        self,
        max_micro_memories: int = 5,
        relevance_threshold: float = 0.0
    ) -> str:
        """
        Get formatted memory context for AI prompts with smart retrieval
        All encrypted data is decrypted before returning
        
        Args:
            max_micro_memories: Maximum number of recent micro memories to include
            relevance_threshold: Minimum relevance score (0.0-1.0) for retrieval
                                0.0 = all memories, 0.6 = only relevant ones
            
        Returns:
            Formatted string with all relevant context (decrypted)
        """
        try:
            lines = []
            
            # 1. Persistent Facts (Always include) - DECRYPTED
            facts_text = self.facts.get_facts_for_prompt()
            lines.append(facts_text)
            lines.append("")
            
            # 2. Recent Micro Memories (with decay + relevance) - DECRYPTED
            recent_micros = self.micro.get_recent_micro_memories(
                limit=max_micro_memories,
                min_importance=max(2.0, relevance_threshold * 10),  # Convert threshold to importance
                apply_decay=True
            )
            
            if recent_micros:
                lines.append("=== RECENT CONVERSATIONS ===")
                for memory in recent_micros:
                    # Decrypt summary (already done by micro.get_recent_micro_memories)
                    summary = memory.get('summary', '')
                    
                    lines.append(f"\nDate: {memory['created_at'][:10]}")
                    lines.append(f"Summary: {summary}")
                    lines.append(
                        f"Importance: {memory['current_importance']:.1f}/10 "
                        f"(decaying from {memory['importance']:.1f})"
                    )
                    
                    # Add emotional context if significant
                    emotional = memory.get('emotional_context', {})
                    if emotional.get('emotional_intensity', 0) > 0.5:
                        lines.append(
                            f"Emotion: {emotional.get('primary_emotion', 'unknown')} "
                            f"(intensity: {emotional.get('emotional_intensity', 0):.1f})"
                        )
                lines.append("")
            
            # 3. Super Memories (Long-term patterns) - DECRYPTED
            super_memories = self.consolidator.get_all_super_memories(limit=3)
            
            if super_memories:
                lines.append("=== LONG-TERM PATTERNS ===")
                for memory in super_memories:
                    # Decrypt summary (already done by consolidator.get_all_super_memories)
                    summary = memory.get('summary', '')
                    
                    lines.append(f"\nPeriod: {memory['date_range']['start'][:10]} to {memory['date_range']['end'][:10]}")
                    lines.append(f"Summary: {summary}")
                    if memory.get('themes'):
                        lines.append(f"Themes: {', '.join(memory['themes'])}")
                    
                    # Add emotional patterns if available
                    emotional_patterns = memory.get('emotional_patterns', {})
                    if emotional_patterns:
                        dominant = emotional_patterns.get('dominant_emotion')
                        if dominant:
                            lines.append(f"Emotional pattern: {dominant}")
                lines.append("")
            
            return "\n".join(lines)
            
        except Exception as e:
            logger.error(f"❌ Failed to get context for prompt: {e}")
            return "No memory context available."
    
    def get_recent_open_thread(self) -> Optional[Dict[str, Any]]:
        """
        NEW: Get one recent topic that seems unfinished or important
        for proactive follow-up
        
        Returns:
            Dictionary with 'summary' and 'topic' keys, or None
        """
        try:
            # Get recent micro memories
            recent = self.micro.get_recent_micro_memories(
                limit=10,
                min_importance=4.0,
                apply_decay=True
            )
            
            # Look for memories with high importance or emotional intensity
            for memory in recent:
                emotional = memory.get('emotional_context', {})
                current_importance = memory.get('current_importance', 0)
                
                # High importance or high emotion = potential open thread
                if current_importance > 6.0 or emotional.get('emotional_intensity', 0) > 0.6:
                    topics = memory.get('topics', [])
                    main_topic = topics[0] if topics else "recent conversation"
                    
                    return {
                        'summary': memory.get('summary', ''),
                        'topic': main_topic,
                        'date': memory.get('created_at', '')[:10]
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get recent open thread: {e}")
            return None
    
    # =========================================================================
    # STATISTICS & DEBUGGING
    # =========================================================================
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get comprehensive memory statistics"""
        try:
            micro_stats = self.micro.get_stats()
            
            return {
                'persistent_facts': self.facts.get_stats(),
                'micro_memories': micro_stats,
                'super_memories': self.consolidator.get_stats(),
                'current_session': {
                    'message_count': len(self.current_session_messages),
                    'duration_minutes': (
                        datetime.utcnow() - self.session_start_time
                    ).total_seconds() / 60
                },
                'recent_micro_count': micro_stats.get('unconsolidated', 0),
                'encryption': 'enabled'
            }
        except Exception as e:
            logger.error(f"❌ Failed to get memory stats: {e}")
            return {}
    
    def cleanup_old_data(self) -> Dict[str, int]:
        """Run cleanup on all memory tiers"""
        try:
            results = {
                'micro_memories_deleted': self.micro.cleanup_old_memories(days_threshold=60)
            }
            
            logger.info(f"🧹 Cleanup complete: {results}")
            return results
            
        except Exception as e:
            logger.error(f"❌ Cleanup failed: {e}")
            return {}
