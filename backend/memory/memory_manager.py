#!/usr/bin/env python3
"""
Zentrafuge v9 - Memory Manager
Central orchestrator for the multi-tier memory system
WITH ENCRYPTION AT REST
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
    Central memory management system with encryption
    
    Orchestrates:
    - Persistent facts (never forgotten) - ENCRYPTED
    - Micro memories (session summaries with decay) - ENCRYPTED
    - Super memories (consolidated patterns) - ENCRYPTED
    - Automatic consolidation when thresholds reached
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
        
        logger.info(f"🧠 Memory Manager initialized for user {user_id} (encryption enabled)")
    
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
        """Import facts from onboarding data (will be encrypted)"""
        return self.facts.import_from_onboarding(onboarding_data)
    
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
                if any(word in content_lower for word in ['sad', 'upset', 'depressed']):
                    emotions.append('negative')
                    intensities.append(0.7)
                elif any(word in content_lower for word in ['happy', 'great', 'excited']):
                    emotions.append('positive')
                    intensities.append(0.6)
                elif any(word in content_lower for word in ['worried', 'anxious', 'nervous']):
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
            'goals': ['goal', 'plan', 'dream', 'ambition', 'aspiration']
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
    # MEMORY RETRIEVAL FOR AI CONTEXT (WITH DECRYPTION)
    # =========================================================================
    
    def get_context_for_prompt(self, max_micro_memories: int = 5) -> str:
        """
        Get formatted memory context for AI prompts
        All encrypted data is decrypted before returning
        
        Args:
            max_micro_memories: Maximum number of recent micro memories to include
            
        Returns:
            Formatted string with all relevant context (decrypted)
        """
        try:
            lines = []
            
            # 1. Persistent Facts (Always include) - DECRYPTED
            facts_text = self.facts.get_facts_for_prompt()
            lines.append(facts_text)
            lines.append("")
            
            # 2. Recent Micro Memories (with decay) - DECRYPTED
            recent_micros = self.micro.get_recent_micro_memories(
                limit=max_micro_memories,
                min_importance=2.0,
                apply_decay=True
            )
            
            if recent_micros:
                lines.append("=== RECENT CONVERSATIONS ===")
                for memory in recent_micros:
                    # Decrypt summary
                    summary = decrypt_text(memory.get('summary', ''))
                    
                    lines.append(f"\nDate: {memory['created_at'][:10]}")
                    lines.append(f"Summary: {summary}")
                    lines.append(
                        f"Importance: {memory['current_importance']:.1f}/10 "
                        f"(decaying from {memory['importance']:.1f})"
                    )
                lines.append("")
            
            # 3. Super Memories (Long-term patterns) - DECRYPTED
            super_memories = self.consolidator.get_all_super_memories(limit=3)
            
            if super_memories:
                lines.append("=== LONG-TERM PATTERNS ===")
                for memory in super_memories:
                    # Decrypt summary
                    summary = decrypt_text(memory.get('summary', ''))
                    
                    lines.append(f"\nPeriod: {memory['date_range']['start'][:10]} to {memory['date_range']['end'][:10]}")
                    lines.append(f"Summary: {summary}")
                    if memory.get('themes'):
                        lines.append(f"Themes: {', '.join(memory['themes'])}")
                lines.append("")
            
            return "\n".join(lines)
            
        except Exception as e:
            logger.error(f"❌ Failed to get context for prompt: {e}")
            return "No memory context available."
    
    # =========================================================================
    # STATISTICS & DEBUGGING
    # =========================================================================
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get comprehensive memory statistics"""
        try:
            return {
                'persistent_facts': self.facts.get_stats(),
                'micro_memories': self.micro.get_stats(),
                'super_memories': self.consolidator.get_stats(),
                'current_session': {
                    'message_count': len(self.current_session_messages),
                    'duration_minutes': (
                        datetime.utcnow() - self.session_start_time
                    ).total_seconds() / 60
                },
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
