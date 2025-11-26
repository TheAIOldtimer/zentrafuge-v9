#!/usr/bin/env python3
"""
Zentrafuge v9 - Persistent Facts Storage
Facts that NEVER get forgotten (name, pets, veteran status, core values)
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from firebase_admin import firestore

logger = logging.getLogger(__name__)


class PersistentFacts:
    """
    Persistent facts that never decay or get forgotten
    
    Fact Categories:
    - Identity: name, age, location
    - Relationships: pets, family members
    - Status: veteran status, occupation
    - Values: core beliefs, important life context
    - Preferences: communication style, boundaries
    """
    
    def __init__(self, db: firestore.Client, user_id: str):
        self.db = db
        self.user_id = user_id
        self.collection = 'user_facts'
        
        # Load existing facts on initialization
        self.facts = self._load_facts()
    
    def _load_facts(self) -> Dict[str, Any]:
        """Load all persistent facts from Firestore"""
        try:
            doc_ref = self.db.collection(self.collection).document(self.user_id)
            doc = doc_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                logger.info(f"✅ Loaded {len(data.get('facts', {}))} persistent facts for user {self.user_id}")
                return data.get('facts', {})
            else:
                logger.info(f"📝 No persistent facts found for user {self.user_id}, starting fresh")
                return {}
                
        except Exception as e:
            logger.error(f"❌ Failed to load persistent facts: {e}")
            return {}
    
    def set_fact(self, category: str, key: str, value: Any, source: str = "user") -> bool:
        """
        Set a persistent fact
        
        Args:
            category: Fact category (identity, relationships, status, values, preferences)
            key: Fact key (e.g., "name", "pet_dog", "is_veteran")
            value: Fact value
            source: Where this fact came from (user, onboarding, conversation, system)
        
        Returns:
            True if successful
        """
        try:
            # Ensure category exists in facts
            if category not in self.facts:
                self.facts[category] = {}
            
            # Store fact with metadata
            self.facts[category][key] = {
                'value': value,
                'source': source,
                'created_at': datetime.utcnow().isoformat(),
                'last_updated': datetime.utcnow().isoformat()
            }
            
            # Save to Firestore
            self._save_facts()
            
            logger.info(f"✅ Set fact: {category}.{key} = {value} (source: {source})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to set fact {category}.{key}: {e}")
            return False
    
    def get_fact(self, category: str, key: str) -> Optional[Any]:
        """
        Get a persistent fact value
        
        Args:
            category: Fact category
            key: Fact key
            
        Returns:
            Fact value or None if not found
        """
        try:
            if category in self.facts and key in self.facts[category]:
                return self.facts[category][key]['value']
            return None
        except Exception as e:
            logger.error(f"❌ Failed to get fact {category}.{key}: {e}")
            return None
    
    def get_all_facts(self) -> Dict[str, Any]:
        """Get all persistent facts organized by category"""
        return self.facts
    
    def get_category(self, category: str) -> Dict[str, Any]:
        """Get all facts in a specific category"""
        return self.facts.get(category, {})
    
    def delete_fact(self, category: str, key: str) -> bool:
        """
        Delete a persistent fact (use sparingly - these are meant to persist!)
        
        Args:
            category: Fact category
            key: Fact key
            
        Returns:
            True if successful
        """
        try:
            if category in self.facts and key in self.facts[category]:
                del self.facts[category][key]
                self._save_facts()
                logger.info(f"🗑️ Deleted fact: {category}.{key}")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Failed to delete fact {category}.{key}: {e}")
            return False
    
    def import_from_onboarding(self, onboarding_data: Dict[str, Any]) -> int:
        """
        Import facts from onboarding data
        
        Args:
            onboarding_data: User's onboarding responses
            
        Returns:
            Number of facts imported
        """
        imported_count = 0
        
        try:
            # Import companion name preference
            if 'companion_name' in onboarding_data or 'cael_name' in onboarding_data:
                name = onboarding_data.get('companion_name') or onboarding_data.get('cael_name')
                if name:
                    self.set_fact('preferences', 'companion_name', name, 'onboarding')
                    imported_count += 1
            
            # Import communication preferences
            if 'communication_style' in onboarding_data:
                self.set_fact('preferences', 'communication_style', 
                            onboarding_data['communication_style'], 'onboarding')
                imported_count += 1
            
            if 'emotional_pacing' in onboarding_data:
                self.set_fact('preferences', 'emotional_pacing',
                            onboarding_data['emotional_pacing'], 'onboarding')
                imported_count += 1
            
            # Import veteran status
            veteran_profile = onboarding_data.get('veteran_profile', {})
            if isinstance(veteran_profile, dict):
                is_veteran = veteran_profile.get('is_veteran', False)
                self.set_fact('status', 'is_veteran', is_veteran, 'onboarding')
                imported_count += 1
                
                if is_veteran:
                    # Import veteran details
                    if veteran_profile.get('service_branch'):
                        self.set_fact('status', 'service_branch', 
                                    veteran_profile['service_branch'], 'onboarding')
                        imported_count += 1
                    
                    if veteran_profile.get('service_country'):
                        self.set_fact('status', 'service_country',
                                    veteran_profile['service_country'], 'onboarding')
                        imported_count += 1
            
            # Import life context
            if 'life_chapter' in onboarding_data and onboarding_data['life_chapter']:
                self.set_fact('values', 'life_chapter',
                            onboarding_data['life_chapter'], 'onboarding')
                imported_count += 1
            
            # Import sources of meaning
            if 'sources_of_meaning' in onboarding_data:
                meanings = onboarding_data['sources_of_meaning']
                if isinstance(meanings, list) and meanings:
                    self.set_fact('values', 'sources_of_meaning', meanings, 'onboarding')
                    imported_count += 1
            
            # Import effective support types
            if 'effective_support' in onboarding_data:
                support = onboarding_data['effective_support']
                if isinstance(support, list) and support:
                    self.set_fact('preferences', 'effective_support', support, 'onboarding')
                    imported_count += 1
            
            logger.info(f"✅ Imported {imported_count} facts from onboarding for user {self.user_id}")
            return imported_count
            
        except Exception as e:
            logger.error(f"❌ Failed to import onboarding data: {e}")
            return imported_count
    
    def extract_facts_from_message(self, user_message: str, ai_response: str) -> int:
        """
        Auto-extract facts from conversation messages
        ENHANCED: Comprehensive pattern matching for names, pets, locations, relationships, etc.
        
        Args:
            user_message: What the user said
            ai_response: How Cael responded
            
        Returns:
            Number of facts extracted
        """
        extracted_count = 0
        message_lower = user_message.lower()
        
        try:
            # ============================================================
            # EXTRACT NAME (with nickname support)
            # ============================================================
            name_patterns = [
                "my name is ",
                "i'm called ",
                "call me ",
                "i am ",
                "name's ",
                "i'm "  # Added for "I'm Anthony"
            ]
            for pattern in name_patterns:
                if pattern in message_lower:
                    start_idx = message_lower.index(pattern) + len(pattern)
                    rest = user_message[start_idx:].strip()
                    name = rest.split()[0].strip('.,!?').capitalize()
                    
                    if name and len(name) > 1 and name.isalpha():
                        self.set_fact('identity', 'name', name, 'conversation')
                        extracted_count += 1
                        logger.info(f"📝 Auto-extracted name: {name}")
                        break
            
            # Extract nickname
            nickname_patterns = [
                "my nickname is ",
                "but call me ",
                "nickname is ",
                "people call me ",
                "but my nickname is "
            ]
            for pattern in nickname_patterns:
                if pattern in message_lower:
                    start_idx = message_lower.index(pattern) + len(pattern)
                    rest = user_message[start_idx:].strip()
                    nickname = rest.split()[0].strip('.,!?').capitalize()
                    
                    if nickname and len(nickname) > 1 and nickname.isalpha():
                        self.set_fact('identity', 'nickname', nickname, 'conversation')
                        extracted_count += 1
                        logger.info(f"📝 Auto-extracted nickname: {nickname}")
                        break
            
            # ============================================================
            # EXTRACT PETS (comprehensive patterns)
            # ============================================================
            pet_patterns = [
                ("dog", [
                    "my dog", "i have a dog", "got a dog", "and a dog",
                    "a dog called", "a dog named", "dog called", "dog named"
                ]),
                ("cat", [
                    "my cat", "i have a cat", "got a cat", "and a cat",
                    "a cat called", "a cat named", "cat called", "cat named"
                ]),
                ("pet", ["my pet", "i have a pet", "got a pet"])
            ]
            
            for pet_type, patterns in pet_patterns:
                for pattern in patterns:
                    if pattern in message_lower:
                        pet_name = None
                        
                        # Look for "named X" or "called X" (handles commas)
                        if "named " in message_lower or "called " in message_lower:
                            keyword = "named " if "named " in message_lower else "called "
                            start_idx = message_lower.index(keyword) + len(keyword)
                            rest = user_message[start_idx:].strip()
                            pet_name = rest.split(',')[0].split()[0].strip('.,!?').capitalize()
                        
                        # Store pet with name
                        if pet_name and len(pet_name) > 1 and pet_name.isalpha():
                            key = f"pet_{pet_type}_{pet_name.lower()}"
                            self.set_fact('relationships', key, {
                                'type': pet_type,
                                'name': pet_name
                            }, 'conversation')
                            extracted_count += 1
                            logger.info(f"🐾 Auto-extracted pet: {pet_type} named {pet_name}")
                        else:
                            # Just store that they have this pet type
                            key = f"has_{pet_type}"
                            self.set_fact('relationships', key, True, 'conversation')
                            extracted_count += 1
                            logger.info(f"🐾 Auto-extracted pet ownership: {pet_type}")
                        break
            
            # ============================================================
            # EXTRACT FAVORITE COLOR (UK + US spelling)
            # ============================================================
            color_keywords = [
                "red", "blue", "green", "yellow", "purple", "orange", 
                "pink", "black", "white", "brown", "gray", "grey", "silver", "gold"
            ]
            if "favorite color" in message_lower or "favourite color" in message_lower:
                for color in color_keywords:
                    if color in message_lower:
                        self.set_fact('preferences', 'favorite_color', color, 'conversation')
                        extracted_count += 1
                        logger.info(f"🎨 Auto-extracted favorite color: {color}")
                        break
            
            # ============================================================
            # EXTRACT LOCATION (city/country)
            # ============================================================
            location_patterns = [
                "i live in ",
                "i'm from ",
                "i'm in ",
                "living in ",
                "based in ",
                "i'm based in "
            ]
            for pattern in location_patterns:
                if pattern in message_lower:
                    start_idx = message_lower.index(pattern) + len(pattern)
                    rest = user_message[start_idx:].strip()
                    # Extract up to comma or period (city names can be multi-word)
                    location = rest.split(',')[0].split('.')[0].strip()
                    
                    if location and len(location) > 2:
                        self.set_fact('identity', 'location', location.title(), 'conversation')
                        extracted_count += 1
                        logger.info(f"📍 Auto-extracted location: {location}")
                        break
            
            # ============================================================
            # EXTRACT RELATIONSHIPS (spouse, partner, family)
            # ============================================================
            # Spouse/Partner
            spouse_patterns = [
                ("wife", ["my wife", "my wife is", "my wife's name is"]),
                ("husband", ["my husband", "my husband is", "my husband's name is"]),
                ("partner", ["my partner", "my partner is", "my partner's name is"]),
                ("spouse", ["my spouse", "my spouse is", "my spouse's name is"])
            ]
            
            for relationship_type, patterns in spouse_patterns:
                for pattern in patterns:
                    if pattern in message_lower:
                        # Look for name after "called" or "is"
                        name = None
                        if "called " in message_lower:
                            start_idx = message_lower.index("called ") + 7
                            rest = user_message[start_idx:].strip()
                            name = rest.split(',')[0].split()[0].strip('.,!?').capitalize()
                        elif "is " in message_lower:
                            start_idx = message_lower.index("is ") + 3
                            rest = user_message[start_idx:].strip()
                            name = rest.split(',')[0].split()[0].strip('.,!?').capitalize()
                        
                        if name and len(name) > 1 and name.isalpha():
                            self.set_fact('relationships', relationship_type, name, 'conversation')
                            extracted_count += 1
                            logger.info(f"💑 Auto-extracted {relationship_type}: {name}")
                            break
            
            # Marriage duration
            if "married" in message_lower and ("year" in message_lower or "month" in message_lower):
                import re
                # Look for patterns like "married 3 years" or "married for three years"
                match = re.search(r'married.*?(\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s*(year|month)', message_lower)
                if match:
                    duration = match.group(1)
                    unit = match.group(2)
                    self.set_fact('relationships', 'married_duration', f"{duration} {unit}s", 'conversation')
                    extracted_count += 1
                    logger.info(f"💍 Auto-extracted marriage duration: {duration} {unit}s")
            
            # ============================================================
            # EXTRACT OCCUPATION & WORK STATUS
            # ============================================================
            occupation_patterns = [
                "i'm a ", "i am a ", "i work as ", "i work as a ",
                "my job is ", "i'm an ", "i am an ", "working as "
            ]
            for pattern in occupation_patterns:
                if pattern in message_lower:
                    start_idx = message_lower.index(pattern) + len(pattern)
                    rest = user_message[start_idx:].strip()
                    # Extract until comma, period, or exclamation
                    occupation = rest.split(',')[0].split('.')[0].split('!')[0].strip()
                    
                    if occupation and len(occupation) > 2:
                        self.set_fact('status', 'occupation', occupation, 'conversation')
                        extracted_count += 1
                        logger.info(f"💼 Auto-extracted occupation: {occupation}")
                        break
            
            # Retirement status
            if "retired" in message_lower or "i'm retired" in message_lower:
                self.set_fact('status', 'retired', True, 'conversation')
                extracted_count += 1
                logger.info(f"🏖️ Auto-extracted retirement status: retired")
            
            # ============================================================
            # EXTRACT BIRTH INFO (month, star sign, age)
            # ============================================================
            # Star sign
            star_signs = [
                "aries", "taurus", "gemini", "cancer", "leo", "virgo",
                "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"
            ]
            if "star sign" in message_lower or "zodiac" in message_lower:
                for sign in star_signs:
                    if sign in message_lower:
                        self.set_fact('identity', 'star_sign', sign.capitalize(), 'conversation')
                        extracted_count += 1
                        logger.info(f"♈ Auto-extracted star sign: {sign}")
                        break
            
            # Birth month
            months = [
                "january", "february", "march", "april", "may", "june",
                "july", "august", "september", "october", "november", "december"
            ]
            if "born in " in message_lower or "birthday" in message_lower:
                for month in months:
                    if month in message_lower:
                        self.set_fact('identity', 'birth_month', month.capitalize(), 'conversation')
                        extracted_count += 1
                        logger.info(f"🎂 Auto-extracted birth month: {month}")
                        break
            
            # Age
            if "i'm " in message_lower or "i am " in message_lower:
                import re
                # Look for "I'm 25" or "I am 30 years old"
                match = re.search(r"i'?m?\s+(\d{1,3})(\s+years?\s+old)?", message_lower)
                if match:
                    age = match.group(1)
                    if 1 <= int(age) <= 120:  # Sanity check
                        self.set_fact('identity', 'age', int(age), 'conversation')
                        extracted_count += 1
                        logger.info(f"🎂 Auto-extracted age: {age}")
            
            return extracted_count
            
        except Exception as e:
            logger.error(f"❌ Failed to extract facts from message: {e}")
            return extracted_count
    
    def _save_facts(self):
        """Save all facts to Firestore"""
        try:
            doc_ref = self.db.collection(self.collection).document(self.user_id)
            doc_ref.set({
                'user_id': self.user_id,
                'facts': self.facts,
                'last_updated': datetime.utcnow().isoformat()
            }, merge=True)
            
        except Exception as e:
            logger.error(f"❌ Failed to save facts to Firestore: {e}")
            raise
    
    def get_facts_for_prompt(self) -> str:
        """
        Format facts as a string for inclusion in AI prompts
        
        Returns:
            Formatted string of all persistent facts
        """
        if not self.facts:
            return "No persistent facts stored yet."
        
        lines = ["=== PERSISTENT FACTS (Never Forget) ==="]
        
        for category, facts in self.facts.items():
            if facts:
                lines.append(f"\n{category.upper()}:")
                for key, fact_data in facts.items():
                    value = fact_data['value']
                    
                    # Format different value types
                    if isinstance(value, dict):
                        # Handle pet dictionaries
                        if 'type' in value and 'name' in value:
                            lines.append(f"  - {key}: {value['type']} named {value['name']}")
                        else:
                            lines.append(f"  - {key}: {value}")
                    elif isinstance(value, list):
                        lines.append(f"  - {key}: {', '.join(str(v) for v in value)}")
                    else:
                        lines.append(f"  - {key}: {value}")
        
        return "\n".join(lines)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about stored facts"""
        total_facts = sum(len(facts) for facts in self.facts.values())
        
        return {
            'total_facts': total_facts,
            'categories': list(self.facts.keys()),
            'facts_by_category': {
                cat: len(facts) for cat, facts in self.facts.items()
            }
        }
