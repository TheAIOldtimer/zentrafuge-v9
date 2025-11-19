#!/usr/bin/env python3
"""
Zentrafuge v9 - Memory Storage Engine
Encrypted, minimal, resilient memory management for Cael
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from firebase_admin import firestore
from crypto_handler import MemoryEncryption

logger = logging.getLogger(__name__)

class MemoryStorage:
    """
    Encrypted memory storage engine for Cael's experiences and knowledge
    
    Memory Types:
    - Conversational: Chat history and context
    - Emotional: User preferences, emotional states
    - Factual: Important information about user
    - Growth: Learning progress and development
    """
    
    def __init__(self, db: firestore.Client, user_id: str):
        self.db = db
        self.user_id = user_id
        self.encryption = MemoryEncryption()
        self.memory_collection = f"memories_{user_id}"
        
    def store_memory(self, memory_type: str, content: Dict[Any, Any], 
                    importance: int = 5, tags: List[str] = None) -> str:
        """
        Store encrypted memory with metadata
        
        Args:
            memory_type: Type of memory (conversational, emotional, factual, growth)
            content: Memory content to encrypt and store
            importance: Importance level 1-10 (higher = more important)
            tags: Optional tags for memory categorization
        
        Returns:
            memory_id: Unique identifier for stored memory
        """
        try:
            if tags is None:
                tags = []
            
            # Generate memory ID
            timestamp = datetime.utcnow()
            memory_id = f"{memory_type}_{timestamp.timestamp()}"
            
            # Encrypt sensitive content
            encrypted_content = self.encryption.encrypt_data(json.dumps(content))
            
            # Create memory document
            memory_doc = {
                'memory_id': memory_id,
                'user_id': self.user_id,
                'memory_type': memory_type,
                'encrypted_content': encrypted_content,
                'importance': max(1, min(10, importance)),  # Clamp 1-10
                'tags': tags,
                'created_at': timestamp.isoformat(),
                'last_accessed': timestamp.isoformat(),
                'access_count': 0,
                'decay_factor': 1.0,  # For memory importance decay over time
                'active': True
            }
            
            # Store in Firestore
            self.db.collection(self.memory_collection).document(memory_id).set(memory_doc)
            
            logger.info(f"Memory stored: {memory_id} (type: {memory_type})")
            return memory_id
            
        except Exception as e:
            logger.error(f"Memory storage failed: {e}")
            raise
    
    def retrieve_memory(self, memory_id: str) -> Optional[Dict[Any, Any]]:
        """
        Retrieve and decrypt specific memory by ID
        
        Args:
            memory_id: Unique memory identifier
            
        Returns:
            Decrypted memory content or None if not found
        """
        try:
            doc_ref = self.db.collection(self.memory_collection).document(memory_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                return None
            
            memory_data = doc.to_dict()
            
            # Decrypt content
            encrypted_content = memory_data['encrypted_content']
            decrypted_json = self.encryption.decrypt_data(encrypted_content)
            content = json.loads(decrypted_json)
            
            # Update access metadata
            self._update_access_metadata(memory_id)
            
            return {
                'memory_id': memory_id,
                'memory_type': memory_data['memory_type'],
                'content': content,
                'importance': memory_data['importance'],
                'tags': memory_data['tags'],
                'created_at': memory_data['created_at'],
                'access_count': memory_data['access_count'] + 1
            }
            
        except Exception as e:
            logger.error(f"Memory retrieval failed: {e}")
            return None
    
    def search_memories(self, memory_type: str = None, tags: List[str] = None,
                       importance_threshold: int = 1, limit: int = 20) -> List[Dict[Any, Any]]:
        """
        Search memories with filters (gracefully handles missing indexes)
        
        Args:
            memory_type: Filter by memory type
            tags: Filter by tags (AND logic)
            importance_threshold: Minimum importance level
            limit: Maximum number of results
            
        Returns:
            List of matching decrypted memories
        """
        try:
            # Simple query to avoid index requirements
            query = self.db.collection(self.memory_collection)\
                           .where('active', '==', True)\
                           .limit(limit * 2)  # Get extra to filter in Python
            
            # Execute query
            docs = query.stream()
            
            memories = []
            for doc in docs:
                memory_data = doc.to_dict()
                
                # Filter by memory type if specified
                if memory_type and memory_data.get('memory_type') != memory_type:
                    continue
                
                # Filter by importance threshold
                if memory_data.get('importance', 0) < importance_threshold:
                    continue
                
                # Filter by tags if specified
                if tags and not all(tag in memory_data.get('tags', []) for tag in tags):
                    continue
                
                # Decrypt content
                try:
                    encrypted_content = memory_data['encrypted_content']
                    decrypted_json = self.encryption.decrypt_data(encrypted_content)
                    content = json.loads(decrypted_json)
                    
                    memories.append({
                        'memory_id': memory_data['memory_id'],
                        'memory_type': memory_data['memory_type'],
                        'content': content,
                        'importance': memory_data['importance'],
                        'tags': memory_data['tags'],
                        'created_at': memory_data['created_at']
                    })
                    
                except Exception as decrypt_error:
                    logger.error(f"Failed to decrypt memory {doc.id}: {decrypt_error}")
                    continue
            
            # Sort by importance and creation time in Python
            memories.sort(key=lambda x: (x['importance'], x['created_at']), reverse=True)
            
            return memories[:limit]
            
        except Exception as e:
            logger.error(f"Memory search failed: {e}")
            # Return empty list instead of crashing
            return []
    
    def get_conversation_context(self, max_messages: int = 10) -> List[Dict[Any, Any]]:
        """
        Get recent conversation context for AI prompting
        
        Args:
            max_messages: Maximum number of recent messages to include
            
        Returns:
            List of recent conversation memories
        """
        try:
            # Simple query to avoid index issues
            query = self.db.collection(self.memory_collection)\
                           .where('active', '==', True)\
                           .limit(max_messages * 3)  # Get extra to filter in Python
            
            docs = query.stream()
            
            memories = []
            for doc in docs:
                memory_data = doc.to_dict()
                
                # Filter for conversational memories only
                if memory_data.get('memory_type') != 'conversational':
                    continue
                
                # Filter by importance threshold
                if memory_data.get('importance', 0) < 3:
                    continue
                
                try:
                    encrypted_content = memory_data['encrypted_content']
                    decrypted_json = self.encryption.decrypt_data(encrypted_content)
                    content = json.loads(decrypted_json)
                    
                    memories.append({
                        'memory_id': memory_data['memory_id'],
                        'memory_type': memory_data['memory_type'],
                        'content': content,
                        'importance': memory_data['importance'],
                        'tags': memory_data['tags'],
                        'created_at': memory_data['created_at']
                    })
                    
                except Exception as decrypt_error:
                    logger.error(f"Failed to decrypt memory {doc.id}: {decrypt_error}")
                    continue
            
            # Sort by creation time (newest first)
            memories.sort(key=lambda x: x['created_at'], reverse=True)
            
            return memories[:max_messages]
            
        except Exception as e:
            logger.error(f"Conversation context retrieval failed: {e}")
            return []
    
    def get_emotional_profile(self) -> Dict[str, Any]:
        """
        Build user's emotional profile from stored memories
        
        Returns:
            Aggregated emotional insights and preferences
        """
        try:
            emotional_memories = self.search_memories(
                memory_type='emotional',
                importance_threshold=5,
                limit=50
            )
            
            profile = {
                'communication_preferences': {},
                'emotional_patterns': {},
                'triggers_to_avoid': [],
                'positive_reinforcements': [],
                'last_updated': datetime.utcnow().isoformat()
            }
            
            # Analyze emotional memories to build profile
            for memory in emotional_memories:
                content = memory['content']
                
                # Extract communication preferences
                if 'communication_style' in content:
                    style = content['communication_style']
                    profile['communication_preferences'][style] = \
                        profile['communication_preferences'].get(style, 0) + 1
                
                # Extract emotional patterns
                if 'emotion' in content:
                    emotion = content['emotion']
                    profile['emotional_patterns'][emotion] = \
                        profile['emotional_patterns'].get(emotion, 0) + 1
                
                # Extract triggers and reinforcements
                if 'trigger' in content:
                    trigger = content['trigger']
                    if trigger not in profile['triggers_to_avoid']:
                        profile['triggers_to_avoid'].append(trigger)
                
                if 'positive_response' in content:
                    response = content['positive_response']
                    if response not in profile['positive_reinforcements']:
                        profile['positive_reinforcements'].append(response)
            
            return profile
            
        except Exception as e:
            logger.error(f"Emotional profile generation failed: {e}")
            return {}
    
    def store_conversation_memory(self, messages: List[Dict[str, str]], 
                                 emotional_context: Dict[str, Any] = None) -> str:
        """
        Store conversation memory with emotional context
        
        Args:
            messages: List of conversation messages
            emotional_context: Optional emotional analysis of conversation
            
        Returns:
            memory_id: Stored memory identifier
        """
        content = {
            'messages': messages,
            'message_count': len(messages),
            'emotional_context': emotional_context or {},
            'conversation_topic': self._extract_topic(messages)
        }
        
        # Determine importance based on emotional context and length
        importance = 3  # Default
        if emotional_context:
            if emotional_context.get('emotional_intensity', 0) > 0.7:
                importance = 7
            elif emotional_context.get('contains_personal_info', False):
                importance = 8
        
        if len(messages) > 10:  # Long conversation
            importance += 1
        
        tags = ['conversation']
        if emotional_context:
            if emotional_context.get('positive_sentiment', False):
                tags.append('positive')
            if emotional_context.get('requires_followup', False):
                tags.append('followup')
        
        return self.store_memory('conversational', content, importance, tags)
    
    def store_emotional_memory(self, emotion: str, intensity: float, 
                              context: str, trigger: str = None) -> str:
        """
        Store emotional state memory
        
        Args:
            emotion: Detected emotion name
            intensity: Emotion intensity 0.0-1.0
            context: Context that triggered the emotion
            trigger: Specific trigger if identified
            
        Returns:
            memory_id: Stored memory identifier
        """
        content = {
            'emotion': emotion,
            'intensity': intensity,
            'context': context,
            'trigger': trigger,
            'detected_at': datetime.utcnow().isoformat()
        }
        
        # High intensity emotions are more important
        importance = int(intensity * 10)
        tags = ['emotion', emotion]
        
        if trigger:
            tags.append('has_trigger')
        
        return self.store_memory('emotional', content, importance, tags)
    
    def _update_access_metadata(self, memory_id: str):
        """Update memory access tracking"""
        try:
            doc_ref = self.db.collection(self.memory_collection).document(memory_id)
            doc_ref.update({
                'last_accessed': datetime.utcnow().isoformat(),
                'access_count': firestore.Increment(1)
            })
        except Exception as e:
            logger.error(f"Failed to update access metadata: {e}")
    
    def _extract_topic(self, messages: List[Dict[str, str]]) -> str:
        """
        Extract conversation topic from messages
        Simple keyword extraction for now
        """
        all_text = ' '.join([msg.get('content', '') for msg in messages]).lower()
        
        # Simple topic detection based on keywords
        topics = {
            'work': ['job', 'work', 'career', 'office', 'project'],
            'relationships': ['friend', 'family', 'partner', 'relationship'],
            'health': ['health', 'doctor', 'medicine', 'exercise'],
            'hobbies': ['hobby', 'game', 'movie', 'book', 'music'],
            'emotions': ['feel', 'emotion', 'sad', 'happy', 'angry', 'excited']
        }
        
        for topic, keywords in topics.items():
            if any(keyword in all_text for keyword in keywords):
                return topic
        
        return 'general'
    
    def cleanup_old_memories(self, days_threshold: int = 90, 
                           importance_threshold: int = 3):
        """
        Clean up old, low-importance memories to manage storage
        
        Args:
            days_threshold: Delete memories older than this many days
            importance_threshold: Only delete memories below this importance
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_threshold)
            
            # Query old, low-importance memories (simplified to avoid indexes)
            query = self.db.collection(self.memory_collection)\
                           .where('active', '==', True)\
                           .limit(500)
            
            batch = self.db.batch()
            deleted_count = 0
            
            for doc in query.stream():
                data = doc.to_dict()
                
                # Filter in Python
                if data.get('importance', 10) >= importance_threshold:
                    continue
                    
                created_at = datetime.fromisoformat(data.get('created_at', datetime.utcnow().isoformat()))
                if created_at >= cutoff_date:
                    continue
                
                batch.delete(doc.reference)
                deleted_count += 1
                
                # Commit in batches of 100
                if deleted_count % 100 == 0:
                    batch.commit()
                    batch = self.db.batch()
            
            # Commit remaining deletions
            if deleted_count % 100 != 0:
                batch.commit()
            
            logger.info(f"Cleaned up {deleted_count} old memories")
            
        except Exception as e:
            logger.error(f"Memory cleanup failed: {e}")
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory storage statistics"""
        try:
            # Get counts by type
            stats = {
                'total_memories': 0,
                'by_type': {},
                'by_importance': {},
                'storage_used_mb': 0  # Approximate
            }
            
            docs = self.db.collection(self.memory_collection).stream()
            
            for doc in docs:
                data = doc.to_dict()
                stats['total_memories'] += 1
                
                # Count by type
                mem_type = data.get('memory_type', 'unknown')
                stats['by_type'][mem_type] = stats['by_type'].get(mem_type, 0) + 1
                
                # Count by importance
                importance = data.get('importance', 0)
                stats['by_importance'][importance] = stats['by_importance'].get(importance, 0) + 1
                
                # Estimate storage (rough calculation)
                content_size = len(data.get('encrypted_content', ''))
                stats['storage_used_mb'] += content_size / (1024 * 1024)
            
            return stats
            
        except Exception as e:
            logger.error(f"Memory stats failed: {e}")
            return {}
