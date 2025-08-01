// js/veteran-verification.js - Veteran verification and military knowledge access

import Config from './config.js';

class VeteranVerificationSystem {
    constructor() {
        this.isVerified = false;
        this.veteranProfile = null;
        this.militaryKnowledge = null;
        this.supportedCountries = ['US', 'UK', 'CA', 'NZ', 'AU'];
    }

    // Verify veteran status through backend
    async verifyVeteranStatus(userId, token) {
        try {
            const response = await fetch(`${Config.API_BASE}/veteran/verify`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ user_id: userId })
            });

            if (response.ok) {
                const data = await response.json();
                this.isVerified = data.verified;
                this.veteranProfile = data.profile;
                
                if (this.isVerified) {
                    await this.loadMilitaryKnowledge(data.profile.country);
                }
                
                return this.isVerified;
            }
            
            return false;
        } catch (error) {
            console.error('Veteran verification failed:', error);
            return false;
        }
    }

    // Load appropriate military knowledge base
    async loadMilitaryKnowledge(country = 'US') {
        if (!this.isVerified) {
            console.warn('❌ Attempted to access military knowledge without verification');
            return null;
        }

        try {
            const knowledgeFiles = {
                'US': '/utils/military_knowledge_us.js',
                'UK': '/utils/military_knowledge_uk.js', 
                'CA': '/utils/military_knowledge_ca.js',
                'NZ': '/utils/military_knowledge_nz.js',
                'AU': '/utils/military_knowledge_au.js'
            };

            const filePath = knowledgeFiles[country] || knowledgeFiles['US'];
            
            // Dynamically import the military knowledge
            const module = await import(filePath);
            this.militaryKnowledge = module.default || module;
            
            console.log(`✅ Military knowledge loaded for ${country}`);
            return this.militaryKnowledge;
            
        } catch (error) {
            console.error('Failed to load military knowledge:', error);
            return null;
        }
    }

    // Enhanced message processing for veterans
    enhanceMessageForVeteran(message, userContext) {
        if (!this.isVerified || !this.militaryKnowledge) {
            return message; // Return unchanged if not verified
        }

        try {
            const knowledge = this.militaryKnowledge;
            
            // Detect military context in message
            const militaryContext = this.detectMilitaryContext(message, knowledge);
            
            if (militaryContext) {
                // Add military-specific context to the message
                return this.addMilitaryContext(message, militaryContext, userContext);
            }
            
            return message;
            
        } catch (error) {
            console.error('Error enhancing veteran message:', error);
            return message;
        }
    }

    detectMilitaryContext(message, knowledge) {
        if (!knowledge.detectMilitaryService) return null;
        
        const context = {
            hasMilitaryContent: knowledge.detectMilitaryService(message),
            branch: knowledge.detectBranch ? knowledge.detectBranch(message) : null,
            operation: knowledge.getOperationContext ? knowledge.getOperationContext(message) : null,
            unit: null
        };

        // Try to detect specific unit mentions
        if (knowledge.getUnitInfo) {
            const words = message.split(' ');
            for (const word of words) {
                const unitInfo = knowledge.getUnitInfo(word);
                if (unitInfo) {
                    context.unit = unitInfo;
                    break;
                }
            }
        }

        return context.hasMilitaryContent ? context : null;
    }

    addMilitaryContext(message, militaryContext, userContext) {
        let enhancedMessage = message;
        
        // Add context hints for the AI
        const contextualInfo = [];
        
        if (militaryContext.unit) {
            contextualInfo.push(`[VETERAN_CONTEXT: User mentioned ${militaryContext.unit.nickname || 'military unit'} - show respect for service and unit pride]`);
        }
        
        if (militaryContext.branch) {
            contextualInfo.push(`[VETERAN_CONTEXT: ${militaryContext.branch.toUpperCase()} veteran - use appropriate military courtesy and understanding]`);
        }
        
        if (militaryContext.operation) {
            contextualInfo.push(`[VETERAN_CONTEXT: Operation ${militaryContext.operation} deployment - acknowledge service and potential combat experience]`);
        }

        // Add veteran-specific guidance for AI
        contextualInfo.push(`[VETERAN_MODE: User is verified military veteran - speak with respect, understanding of military culture, and acknowledge service]`);
        
        if (this.veteranProfile?.country) {
            contextualInfo.push(`[VETERAN_COUNTRY: ${this.veteranProfile.country} military service]`);
        }

        // Prepend context to message (invisible to user, guides AI response)
        enhancedMessage = contextualInfo.join('\n') + '\n\nUser message: ' + message;
        
        return enhancedMessage;
    }

    // Get veteran-specific response suggestions
    getVeteranResponseSuggestions(militaryContext) {
        if (!this.isVerified || !this.militaryKnowledge) return [];

        const suggestions = [];
        
        if (militaryContext?.unit && this.militaryKnowledge.getMilitaryResponse) {
            const response = this.militaryKnowledge.getMilitaryResponse(this.veteranProfile, militaryContext.unit);
            if (response) suggestions.push(response);
        }

        // Add branch-specific acknowledgments
        if (militaryContext?.branch) {
            const branchResponses = {
                'army': "That Army training stays with you, doesn't it?",
                'marines': "Semper Fi - that Marine mentality is something else.",
                'navy': "The Navy experience shapes you in unique ways.",
                'air_force': "Air Force precision and excellence - that mindset carries forward.",
                'coast_guard': "Semper Paratus - always ready, always serving."
            };
            
            if (branchResponses[militaryContext.branch]) {
                suggestions.push(branchResponses[militaryContext.branch]);
            }
        }

        return suggestions;
    }

    // Veteran-specific UI enhancements
    addVeteranUIElements() {
        if (!this.isVerified) return;

        // Add veteran indicator to chat header
        const chatHeader = document.querySelector('.chat-header');
        if (chatHeader && !document.getElementById('veteran-indicator')) {
            const veteranBadge = document.createElement('div');
            veteranBadge.id = 'veteran-indicator';
            veteranBadge.innerHTML = `
                <span class="veteran-badge" title="Verified Military Veteran">
                    🎖️ Veteran
                </span>
            `;
            veteranBadge.style.cssText = `
                background: linear-gradient(45deg, #b8860b, #ffd700);
                color: #000;
                padding: 0.25rem 0.5rem;
                border-radius: 4px;
                font-size: 0.8rem;
                font-weight: 600;
                margin-left: 1rem;
                box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            `;
            chatHeader.appendChild(veteranBadge);
        }
    }

    // Log veteran interactions for specialized support
    logVeteranInteraction(interactionType, context) {
        if (!this.isVerified) return;

        console.log(`🎖️ Veteran interaction logged: ${interactionType}`, {
            veteran_id: this.veteranProfile?.id,
            country: this.veteranProfile?.country,
            context: context,
            timestamp: new Date().toISOString()
        });

        // Could send to backend for veteran support analytics
        // This helps improve veteran-specific features
    }
}

// Veteran-specific CSS for UI enhancements
const veteranCSS = `
.veteran-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
}

.veteran-message-enhancement {
    border-left: 3px solid #b8860b;
    background: linear-gradient(to right, rgba(184, 134, 11, 0.1), transparent);
    padding: 0.5rem;
    margin: 0.5rem 0;
    border-radius: 0 4px 4px 0;
}

.military-context-highlight {
    background: rgba(184, 134, 11, 0.2);
    padding: 0.125rem 0.25rem;
    border-radius: 2px;
    font-weight: 600;
}
`;

// Initialize veteran verification system
let veteranSystem = null;

export function initializeVeteranSystem() {
    veteranSystem = new VeteranVerificationSystem();
    
    // Add veteran-specific CSS
    const style = document.createElement('style');
    style.textContent = veteranCSS;
    document.head.appendChild(style);
    
    return veteranSystem;
}

export function getVeteranSystem() {
    return veteranSystem;
}

export { VeteranVerificationSystem };
