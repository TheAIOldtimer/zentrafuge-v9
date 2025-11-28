#!/usr/bin/env python3
"""
Zentrafuge v9 - Memory Consolidator
Consolidates multiple micro memories into super memories (10 micro → 1 super)
WITH ENCRYPTION AT REST
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from firebase_admin import firestore
from openai import OpenAI

# Import encryption utilities
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from crypto_handler import encrypt_text, decrypt_text

logger = logging.getLogger(__name__)


class MemoryConsolidator:
    """
    Consolidates micro memories into super memories
    WITH ENCRYPTION AT REST
    
    - Waits for 10+ unconsolidated micro memories
    - Uses OpenAI to summarize themes, patterns, and key facts
    - Creates a super memory document (encrypted)
    - Marks source micro memories as consolidated
    """
    
    CONSOLIDATION_THRESHOLD = 10  # Number of micro memories needed
    
    def __init__(
        self,
        db: firestore.Client,
        user_id: str,
        openai_client: OpenAI
    ):
        self.db = db
        self.user_id = user_id
        self.openai_client = openai_client
        self.collection = f'super_memories_{user_id}'
    
    def check_consolidation_ready(self, micro_memory) -> bool:
        """
        Check if there are enough unconsolidated micro memories
        
        Args:
            micro_memory: MicroMemory instance
            
        Returns:
            True if ready to consolidate
        """
        count = micro_memory.get_unconsolidated_count()
        return count >= self.CONSOLIDATION_THRESHOLD
    
    async def consolidate_memories(self, micro_memory) -> Optional[str]:
        """
        Consolidate unconsolidated micro memories into a super memory
        Micro memories are automatically decrypted by MicroMemory.get_recent_micro_memories()
        
        Args:
            micro_memory: MicroMemory instance
            
        Returns:
            super_memory_id or None if consolidation not performed
        """
        try:
            # Get unconsolidated micro memories (ALREADY DECRYPTED by micro_memory module)
            memories_to_consolidate = micro_memory.get_recent_micro_memories(
                limit=self.CONSOLIDATION_THRESHOLD,
                min_importance=2.0,  # Only consolidate meaningful memories
                apply_decay=False  # Use original importance for consolidation
            )
            
            if len(memories_to_consolidate) < self.CONSOLIDATION_THRESHOLD:
                logger.info(
                    f"⏳ Not enough micro memories to consolidate "
                    f"({len(memories_to_consolidate)}/{self.CONSOLIDATION_THRESHOLD})"
                )
                return None
            
            logger.info(
                f"🔄 Starting consolidation of {len(memories_to_consolidate)} micro memories..."
            )
            
            # Generate consolidation summary using OpenAI (works with decrypted data)
            consolidation = await self._generate_consolidation(memories_to_consolidate)
            
            if not consolidation:
                logger.error("❌ Failed to generate consolidation")
                return None
            
            # Create super memory (will be encrypted)
            super_memory_id = self._create_super_memory(
                consolidation,
                memories_to_consolidate
            )
            
            # Mark source micro memories as consolidated
            for memory in memories_to_consolidate:
                micro_memory.mark_as_consolidated(memory['memory_id'])
            
            logger.info(f"✅ Consolidation complete: created super memory {super_memory_id} [encrypted]")
            
            return super_memory_id
            
        except Exception as e:
            logger.error(f"❌ Consolidation failed: {e}")
            return None
    
    async def _generate_consolidation(
        self,
        micro_memories: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Use OpenAI to generate a consolidated summary of micro memories
        Micro memories are already decrypted at this point
        
        Args:
            micro_memories: List of DECRYPTED micro memories to consolidate
            
        Returns:
            Consolidation data or None
        """
        try:
            # Build prompt with micro memory summaries (already decrypted)
            prompt = self._build_consolidation_prompt(micro_memories)
            
            # Call OpenAI
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a memory consolidation system. Analyze conversation summaries "
                            "and extract:\n"
                            "1. Recurring themes and patterns\n"
                            "2. Significant life events or changes\n"
                            "3. Emotional patterns and growth\n"
                            "4. Key facts and preferences\n"
                            "5. Notable topics of interest\n\n"
                            "Provide a concise but comprehensive consolidation."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=500,
                temperature=0.3  # Lower temperature for consistent consolidation
            )
            
            consolidation_text = response.choices[0].message.content
            
            # Extract themes and patterns (simple implementation)
            themes = self._extract_themes(micro_memories)
            topics = self._extract_topics(micro_memories)
            emotional_patterns = self._extract_emotional_patterns(micro_memories)
            
            return {
                'summary': consolidation_text,  # Will be encrypted when saved
                'themes': themes,
                'topics': topics,
                'emotional_patterns': emotional_patterns,
                'source_memory_count': len(micro_memories)
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to generate consolidation: {e}")
            return None
    
    def _build_consolidation_prompt(
        self,
        micro_memories: List[Dict[str, Any]]
    ) -> str:
        """
        Build prompt for OpenAI consolidation
        Micro memories are already decrypted at this point
        """
        lines = [
            f"Consolidate these {len(micro_memories)} conversation summaries into "
            f"a single super memory:\n"
        ]
        
        for i, memory in enumerate(micro_memories, 1):
            lines.append(f"\n=== Session {i} ===")
            lines.append(f"Date: {memory['created_at'][:10]}")
            lines.append(f"Summary: {memory['summary']}")  # Already decrypted
            lines.append(f"Topics: {', '.join(memory.get('topics', []))}")
            
            emotional = memory.get('emotional_context', {})
            if emotional:
                lines.append(
                    f"Emotion: {emotional.get('primary_emotion', 'neutral')} "
                    f"(intensity: {emotional.get('emotional_intensity', 0):.1f})"
                )
        
        lines.append("\n\nProvide a consolidated summary covering:")
        lines.append("- Main themes and patterns")
        lines.append("- Emotional journey")
        lines.append("- Key topics of interest")
        lines.append("- Any notable changes or growth")
        
        return "\n".join(lines)
    
    def _extract_themes(self, micro_memories: List[Dict[str, Any]]) -> List[str]:
        """
        Extract common themes from micro memories
        Summaries are already decrypted at this point
        """
        theme_keywords = {
            'personal_growth': ['growth', 'learning', 'change', 'progress', 'development'],
            'relationships': ['friend', 'family', 'partner', 'relationship', 'social'],
            'work_career': ['work', 'job', 'career', 'project', 'professional'],
            'health_wellness': ['health', 'exercise', 'wellness', 'sleep', 'fitness'],
            'emotions': ['feeling', 'emotion', 'mood', 'stress', 'anxiety', 'happiness'],
            'hobbies_interests': ['hobby', 'interest', 'passion', 'enjoy', 'fun'],
        }
        
        themes = []
        
        # Count keyword occurrences
        theme_counts: Dict[str, int] = {}
        for memory in micro_memories:
            summary_lower = memory['summary'].lower()  # Already decrypted
            
            for theme, keywords in theme_keywords.items():
                if any(keyword in summary_lower for keyword in keywords):
                    theme_counts[theme] = theme_counts.get(theme, 0) + 1
        
        # Get themes that appear in multiple memories
        for theme, count in theme_counts.items():
            if count >= 2:  # Appears in at least 2 memories
                themes.append(theme)
        
        return themes
    
    def _extract_topics(self, micro_memories: List[Dict[str, Any]]) -> List[str]:
        """Extract and count topics from micro memories (topics are plaintext metadata)"""
        topic_counts: Dict[str, int] = {}
        
        for memory in micro_memories:
            for topic in memory.get('topics', []):
                topic_counts[topic] = topic_counts.get(topic, 0) + 1
        
        # Return topics sorted by frequency
        sorted_topics = sorted(
            topic_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return [topic for topic, count in sorted_topics[:10]]  # Top 10 topics
    
    def _extract_emotional_patterns(
        self,
        micro_memories: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze emotional patterns across micro memories (emotional_context is plaintext metadata)"""
        emotions: List[str] = []
        intensities: List[float] = []
        
        for memory in micro_memories:
            emotional = memory.get('emotional_context', {})
            if emotional:
                emotion = emotional.get('primary_emotion', 'neutral')
                intensity = emotional.get('emotional_intensity', 0.0)
                
                emotions.append(emotion)
                intensities.append(intensity)
        
        if not emotions:
            return {}
        
        # Count emotion frequencies
        emotion_counts: Dict[str, int] = {}
        for emotion in emotions:
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        
        # Calculate average intensity
        avg_intensity = sum(intensities) / len(intensities) if intensities else 0.0
        
        # Find dominant emotion
        dominant_emotion = max(emotion_counts.items(), key=lambda x: x[1])[0]
        
        return {
            'dominant_emotion': dominant_emotion,
            'average_intensity': avg_intensity,
            'emotion_distribution': emotion_counts
        }
    
    def _create_super_memory(
        self,
        consolidation: Dict[str, Any],
        source_memories: List[Dict[str, Any]]
    ) -> str:
        """
        Create a super memory document in Firestore
        WITH ENCRYPTION
        
        Args:
            consolidation: Consolidation data from OpenAI (plaintext)
            source_memories: List of source micro memories
            
        Returns:
            super_memory_id
        """
        try:
            timestamp = datetime.utcnow()
            
            # ENCRYPT summary before saving
            encrypted_summary = encrypt_text(consolidation['summary'])
            
            super_memory = {
                'user_id': self.user_id,  # Plaintext (for rules)
                'summary': encrypted_summary,  # ENCRYPTED
                'themes': consolidation['themes'],  # Plaintext metadata
                'topics': consolidation['topics'],  # Plaintext metadata
                'emotional_patterns': consolidation['emotional_patterns'],  # Plaintext metadata
                'source_memory_count': len(source_memories),  # Plaintext metadata
                'source_memory_ids': [m['memory_id'] for m in source_memories],  # Plaintext metadata
                'date_range': {  # Plaintext metadata
                    'start': source_memories[-1]['created_at'],  # Oldest
                    'end': source_memories[0]['created_at']      # Newest
                },
                'created_at': timestamp.isoformat(),  # Plaintext metadata
                'last_accessed': timestamp.isoformat(),  # Plaintext metadata
                'access_count': 0,  # Plaintext metadata
                'importance': 7.0,  # Super memories start at higher importance (plaintext metadata)
                'type': 'super',  # Plaintext metadata
                'schema_version': 1  # Plaintext metadata
            }
            
            # Add to Firestore
            doc_ref = self.db.collection(self.collection).add(super_memory)
            super_memory_id = doc_ref[1].id
            
            logger.info(f"✅ Created super memory {super_memory_id} [encrypted]")
            
            return super_memory_id
            
        except Exception as e:
            logger.error(f"❌ Failed to create super memory: {e}")
            raise
    
    def get_super_memory(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific super memory by ID
        WITH DECRYPTION
        
        Args:
            memory_id: ID of super memory
            
        Returns:
            Decrypted super memory or None
        """
        try:
            doc_ref = self.db.collection(self.collection).document(memory_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                return None
            
            memory = doc.to_dict()
            memory['memory_id'] = memory_id
            
            # DECRYPT summary
            if 'summary' in memory:
                memory['summary'] = decrypt_text(memory['summary'])
            
            # Update access tracking
            doc_ref.update({
                'last_accessed': datetime.utcnow().isoformat(),
                'access_count': firestore.Increment(1)
            })
            
            return memory
            
        except Exception as e:
            logger.error(f"❌ Failed to get super memory {memory_id}: {e}")
            return None
    
    def get_all_super_memories(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get all super memories for user
        WITH DECRYPTION
        
        Args:
            limit: Maximum number of super memories to return
            
        Returns:
            List of decrypted super memories
        """
        try:
            query = self.db.collection(self.collection)\
                          .order_by('created_at', direction=firestore.Query.DESCENDING)\
                          .limit(limit)
            
            memories = []
            for doc in query.stream():
                memory = doc.to_dict()
                memory['memory_id'] = doc.id
                
                # DECRYPT summary
                if 'summary' in memory:
                    memory['summary'] = decrypt_text(memory['summary'])
                
                memories.append(memory)
            
            logger.info(f"📥 Retrieved {len(memories)} super memories [decrypted]")
            return memories
            
        except Exception as e:
            logger.error(f"❌ Failed to get super memories: {e}")
            return []
    
    def search_by_theme(self, theme: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search super memories by theme
        WITH DECRYPTION
        
        Args:
            theme: Theme to search for
            limit: Maximum number of results
            
        Returns:
            List of decrypted super memories
        """
        try:
            query = self.db.collection(self.collection)\
                          .where('themes', 'array_contains', theme)\
                          .order_by('created_at', direction=firestore.Query.DESCENDING)\
                          .limit(limit)
            
            memories = []
            for doc in query.stream():
                memory = doc.to_dict()
                memory['memory_id'] = doc.id
                
                # DECRYPT summary
                if 'summary' in memory:
                    memory['summary'] = decrypt_text(memory['summary'])
                
                memories.append(memory)
            
            return memories
            
        except Exception as e:
            logger.error(f"❌ Failed to search by theme '{theme}': {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about super memories"""
        try:
            query = self.db.collection(self.collection).limit(100)
            
            total = 0
            themes_count: Dict[str, int] = {}
            
            for doc in query.stream():
                total += 1
                memory = doc.to_dict()
                
                # Count themes (themes are plaintext metadata, no decryption needed)
                for theme in memory.get('themes', []):
                    themes_count[theme] = themes_count.get(theme, 0) + 1
            
            return {
                'total_super_memories': total,
                'top_themes': sorted(
                    themes_count.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:10],
                'encryption': 'enabled'
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get super memory stats: {e}")
            return {}
