#!/usr/bin/env python3
"""
Zentrafuge v9 - Micro Memory Storage
Session summaries with 14-day half-life forgetting curve
"""

import logging
import math
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from firebase_admin import firestore

logger = logging.getLogger(__name__)


class MicroMemory:
    """
    Micro memories: Short conversation summaries with forgetting curve
    
    - Created at end of each session
    - Importance decays over 14 days (half-life)
    - Can be consolidated into super memories
    """
    
    # Forgetting curve parameters
    HALF_LIFE_DAYS = 14  # Importance drops to 50% after 14 days
    MIN_IMPORTANCE = 1.0  # Minimum importance before deletion
    
    def __init__(self, db: firestore.Client, user_id: str):
        self.db = db
        self.user_id = user_id
        self.collection = f'micro_memories_{user_id}'
    
    def create_micro_memory(
        self,
        summary: str,
        messages: List[Dict[str, str]],
        emotional_context: Dict[str, Any],
        topics: List[str],
        initial_importance: float = 5.0
    ) -> str:
        """
        Create a new micro memory from a conversation session
        
        Args:
            summary: Brief summary of the session
            messages: List of messages in the session
            emotional_context: Emotional analysis of the session
            topics: Topics discussed
            initial_importance: Starting importance (1-10)
            
        Returns:
            memory_id: ID of created micro memory
        """
        try:
            timestamp = datetime.utcnow()
            
            micro_memory = {
                'user_id': self.user_id,
                'summary': summary,
                'message_count': len(messages),
                'messages': messages[:10],  # Store up to 10 messages
                'emotional_context': emotional_context,
                'topics': topics,
                'importance': initial_importance,
                'initial_importance': initial_importance,
                'created_at': timestamp.isoformat(),
                'last_accessed': timestamp.isoformat(),
                'access_count': 0,
                'consolidated': False,  # Whether this has been consolidated into super memory
                'type': 'micro'
            }
            
            # Add to Firestore
            doc_ref = self.db.collection(self.collection).add(micro_memory)
            memory_id = doc_ref[1].id
            
            logger.info(
                f"✅ Created micro memory {memory_id}: {len(messages)} messages, "
                f"importance={initial_importance:.1f}"
            )
            
            return memory_id
            
        except Exception as e:
            logger.error(f"❌ Failed to create micro memory: {e}")
            raise
    
    def get_micro_memory(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific micro memory by ID"""
        try:
            doc_ref = self.db.collection(self.collection).document(memory_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                return None
            
            memory = doc.to_dict()
            memory['memory_id'] = memory_id
            
            # Update access tracking
            doc_ref.update({
                'last_accessed': datetime.utcnow().isoformat(),
                'access_count': firestore.Increment(1)
            })
            
            return memory
            
        except Exception as e:
            logger.error(f"❌ Failed to get micro memory {memory_id}: {e}")
            return None
    
    def get_recent_micro_memories(
        self,
        limit: int = 20,
        min_importance: float = 1.0,
        apply_decay: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get recent micro memories with optional importance decay
        
        Args:
            limit: Maximum number of memories to return
            min_importance: Minimum importance threshold (after decay)
            apply_decay: Whether to apply forgetting curve
            
        Returns:
            List of micro memories sorted by decayed importance
        """
        try:
            # Query recent memories
            query = self.db.collection(self.collection)\
                          .where('consolidated', '==', False)\
                          .order_by('created_at', direction=firestore.Query.DESCENDING)\
                          .limit(limit * 2)  # Get extra to filter after decay
            
            memories = []
            
            for doc in query.stream():
                memory = doc.to_dict()
                memory['memory_id'] = doc.id
                
                if apply_decay:
                    # Calculate current importance with decay
                    memory['current_importance'] = self._calculate_decayed_importance(
                        memory['importance'],
                        memory['created_at']
                    )
                else:
                    memory['current_importance'] = memory['importance']
                
                # Only include if above threshold
                if memory['current_importance'] >= min_importance:
                    memories.append(memory)
            
            # Sort by current importance (highest first)
            memories.sort(key=lambda m: m['current_importance'], reverse=True)
            
            logger.info(
                f"📥 Retrieved {len(memories)} micro memories "
                f"(filtered from query, min_importance={min_importance:.1f})"
            )
            
            return memories[:limit]
            
        except Exception as e:
            logger.error(f"❌ Failed to get recent micro memories: {e}")
            return []
    
    def _calculate_decayed_importance(
        self,
        initial_importance: float,
        created_at_iso: str
    ) -> float:
        """
        Calculate current importance using exponential decay (half-life formula)
        
        Formula: I(t) = I₀ × (0.5)^(t / t_half)
        Where:
            I(t) = importance at time t
            I₀ = initial importance
            t = time elapsed (days)
            t_half = half-life (14 days)
        """
        try:
            created_at = datetime.fromisoformat(created_at_iso)
            now = datetime.utcnow()
            
            # Calculate days elapsed
            elapsed_days = (now - created_at).total_seconds() / 86400
            
            # Apply exponential decay
            decay_factor = math.pow(0.5, elapsed_days / self.HALF_LIFE_DAYS)
            decayed_importance = initial_importance * decay_factor
            
            return max(decayed_importance, 0.1)  # Minimum 0.1
            
        except Exception as e:
            logger.error(f"❌ Failed to calculate decayed importance: {e}")
            return initial_importance  # Return original if calculation fails
    
    def mark_as_consolidated(self, memory_id: str) -> bool:
        """
        Mark a micro memory as consolidated into a super memory
        
        Args:
            memory_id: ID of micro memory to mark
            
        Returns:
            True if successful
        """
        try:
            doc_ref = self.db.collection(self.collection).document(memory_id)
            doc_ref.update({
                'consolidated': True,
                'consolidated_at': datetime.utcnow().isoformat()
            })
            
            logger.info(f"✅ Marked micro memory {memory_id} as consolidated")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to mark micro memory as consolidated: {e}")
            return False
    
    def cleanup_old_memories(self, days_threshold: int = 60) -> int:
        """
        Delete very old, low-importance micro memories
        
        Args:
            days_threshold: Delete memories older than this many days
            
        Returns:
            Number of memories deleted
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_threshold)
            
            # Query old memories
            query = self.db.collection(self.collection)\
                          .where('created_at', '<', cutoff_date.isoformat())\
                          .where('consolidated', '==', True)\
                          .limit(100)
            
            deleted_count = 0
            batch = self.db.batch()
            
            for doc in query.stream():
                memory = doc.to_dict()
                
                # Only delete if importance has decayed below threshold
                current_importance = self._calculate_decayed_importance(
                    memory['importance'],
                    memory['created_at']
                )
                
                if current_importance < self.MIN_IMPORTANCE:
                    batch.delete(doc.reference)
                    deleted_count += 1
            
            if deleted_count > 0:
                batch.commit()
                logger.info(f"🗑️ Deleted {deleted_count} old micro memories")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"❌ Failed to cleanup old micro memories: {e}")
            return 0
    
    def get_unconsolidated_count(self) -> int:
        """Get count of micro memories ready for consolidation"""
        try:
            query = self.db.collection(self.collection)\
                          .where('consolidated', '==', False)
            
            # Count documents
            count = len(list(query.stream()))
            return count
            
        except Exception as e:
            logger.error(f"❌ Failed to count unconsolidated memories: {e}")
            return 0
    
    def search_by_topic(self, topic: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search micro memories by topic
        
        Args:
            topic: Topic to search for
            limit: Maximum number of results
            
        Returns:
            List of matching micro memories
        """
        try:
            query = self.db.collection(self.collection)\
                          .where('topics', 'array_contains', topic)\
                          .order_by('created_at', direction=firestore.Query.DESCENDING)\
                          .limit(limit)
            
            memories = []
            for doc in query.stream():
                memory = doc.to_dict()
                memory['memory_id'] = doc.id
                
                # Calculate current importance
                memory['current_importance'] = self._calculate_decayed_importance(
                    memory['importance'],
                    memory['created_at']
                )
                
                memories.append(memory)
            
            return memories
            
        except Exception as e:
            logger.error(f"❌ Failed to search by topic '{topic}': {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about micro memories"""
        try:
            # Get all memories (limited sample)
            query = self.db.collection(self.collection).limit(1000)
            
            total = 0
            consolidated = 0
            topics_count: Dict[str, int] = {}
            
            for doc in query.stream():
                total += 1
                memory = doc.to_dict()
                
                if memory.get('consolidated', False):
                    consolidated += 1
                
                # Count topics
                for topic in memory.get('topics', []):
                    topics_count[topic] = topics_count.get(topic, 0) + 1
            
            return {
                'total_micro_memories': total,
                'consolidated': consolidated,
                'unconsolidated': total - consolidated,
                'top_topics': sorted(
                    topics_count.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:10]
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get micro memory stats: {e}")
            return {}
