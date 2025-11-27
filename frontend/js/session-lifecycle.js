/**
 * Zentrafuge v9 - Session Lifecycle Manager
 * 
 * Ensures sessions are properly saved when:
 * - User clicks logout
 * - User closes browser tab
 * - User navigates away
 * - Page is refreshed
 * 
 * INTEGRATION INSTRUCTIONS:
 * 
 * 1. Add this file to your frontend: /public/js/session-lifecycle.js
 * 
 * 2. Include in your HTML (before other scripts):
 *    <script src="/js/session-lifecycle.js"></script>
 * 
 * 3. Initialize after user logs in:
 *    SessionLifecycle.init(authToken);
 * 
 * 4. Call on logout button:
 *    await SessionLifecycle.logout();
 */

const SessionLifecycle = {
    // State
    authToken: null,
    isLoggingOut: false,
    
    /**
     * Initialize session lifecycle manager
     * @param {string} token - Firebase auth token
     */
    init(token) {
        this.authToken = token;
        this.setupEventListeners();
        console.log('✅ Session lifecycle manager initialized');
    },
    
    /**
     * Setup event listeners for browser lifecycle events
     */
    setupEventListeners() {
        // Handle page unload (browser close, navigate away, refresh)
        window.addEventListener('beforeunload', (e) => {
            if (!this.isLoggingOut) {
                // Try to save session before page closes
                this.saveSessionBeforeUnload();
                
                // Optional: Show warning dialog
                // e.preventDefault();
                // e.returnValue = '';
            }
        });
        
        // Handle visibility change (tab switch, minimize)
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                // Tab hidden - could save session here too
                console.log('👋 Tab hidden - session still active');
            } else {
                // Tab visible again
                console.log('👀 Tab visible - session resumed');
            }
        });
        
        // Handle page hide (more reliable than beforeunload)
        window.addEventListener('pagehide', (e) => {
            if (!this.isLoggingOut) {
                this.saveSessionBeforeUnload();
            }
        });
    },
    
    /**
     * Save session before page unload
     * Uses sendBeacon for reliability (works even as page closes)
     */
    saveSessionBeforeUnload() {
        if (!this.authToken) {
            console.warn('⚠️ No auth token - cannot save session');
            return;
        }
        
        try {
            const apiUrl = '/session/clear';
            const data = JSON.stringify({
                reason: 'page_unload'
            });
            
            // Use sendBeacon - guaranteed to send even as page closes
            const sent = navigator.sendBeacon(
                apiUrl,
                new Blob([data], { type: 'application/json' })
            );
            
            if (sent) {
                console.log('📤 Session save beacon sent');
            } else {
                console.warn('⚠️ Failed to send session save beacon');
            }
            
        } catch (error) {
            console.error('❌ Error saving session:', error);
        }
    },
    
    /**
     * Explicit logout - call this from logout button
     * @returns {Promise<boolean>} Success status
     */
    async logout() {
        if (!this.authToken) {
            console.warn('⚠️ No auth token - cannot logout');
            return false;
        }
        
        // Set flag to prevent duplicate saves
        this.isLoggingOut = true;
        
        try {
            console.log('🔚 Logging out - saving session...');
            
            const response = await fetch('/session/clear', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.authToken}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    reason: 'user_logout'
                })
            });
            
            if (!response.ok) {
                throw new Error(`Logout failed: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.micro_memory_created) {
                console.log(`✅ Session saved: ${data.micro_memory_id}`);
            } else {
                console.log('⏭️ Session too short to save');
            }
            
            // Clear auth token
            this.authToken = null;
            
            return true;
            
        } catch (error) {
            console.error('❌ Logout error:', error);
            return false;
        } finally {
            this.isLoggingOut = false;
        }
    },
    
    /**
     * Manual session save (call periodically if needed)
     * @returns {Promise<boolean>} Success status
     */
    async saveSession() {
        if (!this.authToken) {
            return false;
        }
        
        try {
            const response = await fetch('/session/save', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.authToken}`,
                    'Content-Type': 'application/json'
                }
            });
            
            return response.ok;
            
        } catch (error) {
            console.error('❌ Save session error:', error);
            return false;
        }
    }
};

// Export for ES6 modules (if using)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SessionLifecycle;
}

// Make available globally
window.SessionLifecycle = SessionLifecycle;


// ============================================================================
// USAGE EXAMPLES
// ============================================================================

/*

// Example 1: Initialize after login
async function handleLogin(email, password) {
    const userCredential = await firebase.auth().signInWithEmailAndPassword(email, password);
    const token = await userCredential.user.getIdToken();
    
    // Initialize session lifecycle
    SessionLifecycle.init(token);
}

// Example 2: Logout button
document.getElementById('logout-btn').addEventListener('click', async () => {
    // Save session and clear
    await SessionLifecycle.logout();
    
    // Then do Firebase logout
    await firebase.auth().signOut();
    
    // Redirect to login
    window.location.href = '/login.html';
});

// Example 3: Auto-save every 5 minutes (optional)
setInterval(async () => {
    if (SessionLifecycle.authToken) {
        await SessionLifecycle.saveSession();
        console.log('💾 Auto-saved session');
    }
}, 5 * 60 * 1000); // 5 minutes

*/
