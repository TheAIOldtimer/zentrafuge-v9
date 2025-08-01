/**
 * Zentrafuge v9 - Frontend Application Logic
 * Memory-first, emotionally intelligent AI companion interface
 */

// Application state
const AppState = {
    currentUser: null,
    authToken: null,
    companionName: 'Cael',
    isTyping: false,
    conversationHistory: [],
    userPreferences: {},
    memoryStats: {},
    currentScreen: 'loading'
};

// Configuration
const Config = {
    // Update this to your backend URL - for local development:
    // API_BASE: 'http://localhost:5000'
    // For production, use your Render URL:
    API_BASE: 'https://your-render-app.onrender.com', // Replace with your actual Render URL
    MESSAGE_MAX_LENGTH: 2000,
    TYPING_DELAY: 1000,
    ERROR_DISPLAY_TIME: 5000,
    SUCCESS_DISPLAY_TIME: 3000
};

// DOM Elements Cache
const Elements = {};

// Initialize application
document.addEventListener('DOMContentLoaded', async () => {
    console.log('🧠 Zentrafuge v9 initializing...');
    
    try {
        // Cache DOM elements
        cacheElements();
        
        // Setup event listeners
        setupEventListeners();
        
        // Initialize Firebase and check auth state
        await initializeApp();
        
    } catch (error) {
        console.error('App initialization failed:', error);
        showError('Failed to initialize application. Please refresh and try again.');
    }
});

// Cache frequently used DOM elements
function cacheElements() {
    const elementIds = [
        'loading-screen', 'auth-screen', 'onboarding-screen', 'chat-screen',
        'login-form-element', 'register-form-element', 'auth-error',
        'message-input', 'send-btn', 'chat-messages', 'typing-indicator',
        'companion-name', 'welcome-companion-name', 'char-count',
        'memory-panel', 'settings-panel', 'error-toast', 'success-toast'
    ];
    
    elementIds.forEach(id => {
        Elements[id] = document.getElementById(id);
    });
}

// Setup all event listeners
function setupEventListeners() {
    // Auth form listeners
    Elements['login-form-element'].addEventListener('submit', handleLogin);
    Elements['register-form-element'].addEventListener('submit', handleRegister);
    
    // Auth form switching
    document.getElementById('show-register').addEventListener('click', (e) => {
        e.preventDefault();
        switchToRegister();
    });
    
    document.getElementById('show-login').addEventListener('click', (e) => {
        e.preventDefault();
        switchToLogin();
    });
    
    // Chat input listeners
    Elements['message-input'].addEventListener('input', handleMessageInput);
    Elements['message-input'].addEventListener('keydown', handleKeyDown);
    Elements['send-btn'].addEventListener('click', sendMessage);
    
    // Header action listeners
    document.getElementById('memory-btn').addEventListener('click', openMemoryPanel);
    document.getElementById('settings-btn').addEventListener('click', openSettingsPanel);
    document.getElementById('logout-btn').addEventListener('click', handleLogout);
    
    // Auto-resize textarea
    Elements['message-input'].addEventListener('input', autoResizeTextarea);
}

// Initialize the application
async function initializeApp() {
    try {
        // Check authentication state
        const isAuthenticated = await checkAuthState();
        
        if (isAuthenticated) {
            // Get user profile and determine next screen
            const userProfile = await getUserProfile();
            
            if (userProfile && userProfile.onboarding_complete) {
                AppState.companionName = userProfile.cael_name || 'Cael';
                AppState.userPreferences = userProfile.preferences || {};
                showScreen('chat');
                initializeChat();
            } else {
                showScreen('onboarding');
                initializeOnboarding();
            }
        } else {
            showScreen('auth');
        }
        
    } catch (error) {
        console.error('App initialization error:', error);
        showScreen('auth');
    }
}

// Authentication Functions
async function handleLogin(e) {
    e.preventDefault();
    
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;
    
    try {
        showLoading(true);
        clearAuthError();
        
        // Sign in with Firebase
        const userCredential = await firebase.auth().signInWithEmailAndPassword(email, password);
        AppState.currentUser = userCredential.user;
        AppState.authToken = await userCredential.user.getIdToken();
        
        // Verify with backend
        const isValid = await verifyAuthToken(AppState.authToken);
        
        if (isValid) {
            await initializeApp();
        } else {
            throw new Error('Authentication verification failed');
        }
        
    } catch (error) {
        console.error('Login error:', error);
        showAuthError(getAuthErrorMessage(error));
    } finally {
        showLoading(false);
    }
}

async function handleRegister(e) {
    e.preventDefault();
    
    const email = document.getElementById('register-email').value;
    const password = document.getElementById('register-password').value;
    const confirmPassword = document.getElementById('register-confirm').value;
    const termsAccepted = document.getElementById('terms-accept').checked;
    
    // Validate inputs
    if (password !== confirmPassword) {
        showAuthError('Passwords do not match');
        return;
    }
    
    if (!termsAccepted) {
        showAuthError('Please accept the Terms of Service');
        return;
    }
    
    try {
        showLoading(true);
        clearAuthError();
        
        // Create user with Firebase
        const userCredential = await firebase.auth().createUserWithEmailAndPassword(email, password);
        AppState.currentUser = userCredential.user;
        AppState.authToken = await userCredential.user.getIdToken();
        
        // Verify with backend (this will create user profile)
        const isValid = await verifyAuthToken(AppState.authToken);
        
        if (isValid) {
            showSuccess('Account created successfully! Let\'s get you set up.');
            showScreen('onboarding');
            initializeOnboarding();
        } else {
            throw new Error('Account verification failed');
        }
        
    } catch (error) {
        console.error('Registration error:', error);
        showAuthError(getAuthErrorMessage(error));
    } finally {
        showLoading(false);
    }
}

async function handleLogout() {
    try {
        await firebase.auth().signOut();
        AppState.currentUser = null;
        AppState.authToken = null;
        AppState.conversationHistory = [];
        showScreen('auth');
        showSuccess('Logged out successfully');
    } catch (error) {
        console.error('Logout error:', error);
        showError('Error logging out. Please try again.');
    }
}

// Check current authentication state
async function checkAuthState() {
    return new Promise((resolve) => {
        firebase.auth().onAuthStateChanged(async (user) => {
            if (user) {
                AppState.currentUser = user;
                AppState.authToken = await user.getIdToken();
                resolve(true);
            } else {
                resolve(false);
            }
        });
    });
}

// Verify auth token with backend
async function verifyAuthToken(token) {
    try {
        const response = await fetch(`${Config.API_BASE}/auth/verify`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ token })
        });
        
        const data = await response.json();
        return data.valid;
        
    } catch (error) {
        console.error('Token verification failed:', error);
        return false;
    }
}

// Get user profile from backend
async function getUserProfile() {
    try {
        const response = await fetch(`${Config.API_BASE}/user/profile`, {
            headers: {
                'Authorization': `Bearer ${AppState.authToken}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            return await response.json();
        }
        
        return null;
        
    } catch (error) {
        console.error('Failed to get user profile:', error);
        return null;
    }
}

// Onboarding Functions
let currentOnboardingStep = 0;
const totalOnboardingSteps = 5; // 0-4

function initializeOnboarding() {
    currentOnboardingStep = 0;
    updateOnboardingProgress();
    showOnboardingStep(0);
}

function nextOnboardingStep() {
    if (currentOnboardingStep < totalOnboardingSteps - 1) {
        currentOnboardingStep++;
        updateOnboardingProgress();
        showOnboardingStep(currentOnboardingStep);
    }
}

function previousOnboardingStep() {
    if (currentOnboardingStep > 0) {
        currentOnboardingStep--;
        updateOnboardingProgress();
        showOnboardingStep(currentOnboardingStep);
    }
}

function showOnboardingStep(step) {
    // Hide all steps
    for (let i = 0; i < totalOnboardingSteps; i++) {
        const stepElement = document.getElementById(`onboarding-step-${i}`);
        if (stepElement) {
            stepElement.style.display = 'none';
        }
    }
    
    // Show current step
    const currentStepElement = document.getElementById(`onboarding-step-${step}`);
    if (currentStepElement) {
        currentStepElement.style.display = 'block';
    }
}

function updateOnboardingProgress() {
    const progressDots = document.querySelectorAll('.progress-dot');
    progressDots.forEach((dot, index) => {
        dot.classList.remove('active', 'completed');
        if (index === currentOnboardingStep) {
            dot.classList.add('active');
        } else if (index < currentOnboardingStep) {
            dot.classList.add('completed');
        }
    });
}

function setCaelName(name) {
    document.getElementById('ai_name').value = name;
}

async function completeOnboarding() {
    try {
        showLoading(true);
        
        // Collect comprehensive onboarding data
        const onboardingData = {
            cael_name: document.getElementById('ai_name')?.value || 'Cael',
            communication_style: getSelectedRadioValue('communication_style') || 'balanced',
            emotional_pacing: getSelectedRadioValue('emotional_pacing') || 'varies_situation',
            life_chapter: document.getElementById('life_chapter')?.value || '',
            sources_of_meaning: getSelectedCheckboxValues('sources_of_meaning'),
            effective_support: getSelectedCheckboxValues('effective_support'),
            preferences: {
                response_length: 'balanced',
                emotional_support: 'moderate',
                learning_speed: 'moderate'
            },
            onboarding_version: 'v9_enhanced',
            personality_profile: generatePersonalityProfile()
        };
        
        // Send to backend
        const response = await fetch(`${Config.API_BASE}/user/onboarding`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${AppState.authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(onboardingData)
        });
        
        if (response.ok) {
            AppState.companionName = onboardingData.cael_name;
            AppState.userPreferences = onboardingData.preferences;
            
            // Show completion step
            showOnboardingStep(5); // Completion step
            document.getElementById('onboarding-complete').style.display = 'block';
        } else {
            throw new Error('Failed to complete onboarding');
        }
        
    } catch (error) {
        console.error('Onboarding completion error:', error);
        showError('Failed to complete setup. Please try again.');
    } finally {
        showLoading(false);
    }
}

function getSelectedRadioValue(name) {
    const selected = document.querySelector(`input[name="${name}"]:checked`);
    return selected ? selected.value : null;
}

function getSelectedCheckboxValues(name) {
    const selected = document.querySelectorAll(`input[name="${name}"]:checked`);
    return Array.from(selected).map(cb => cb.value);
}

function generatePersonalityProfile() {
    // Generate a personality profile based on user selections
    const communicationStyle = getSelectedRadioValue('communication_style');
    const emotionalPacing = getSelectedRadioValue('emotional_pacing');
    const meaningSources = getSelectedCheckboxValues('sources_of_meaning');
    const supportTypes = getSelectedCheckboxValues('effective_support');
    
    return {
        communication_preference: communicationStyle,
        emotional_processing: emotionalPacing,
        meaning_sources: meaningSources,
        preferred_support: supportTypes,
        profile_completeness: calculateProfileCompleteness(),
        generated_at: new Date().toISOString()
    };
}

function calculateProfileCompleteness() {
    const fields = [
        getSelectedRadioValue('communication_style'),
        getSelectedRadioValue('emotional_pacing'),
        document.getElementById('life_chapter')?.value,
        getSelectedCheckboxValues('sources_of_meaning').length > 0,
        getSelectedCheckboxValues('effective_support').length > 0
    ];
    
    const completedFields = fields.filter(field => field && field !== '').length;
    return Math.round((completedFields / fields.length) * 100);
}

function enterChat() {
    showScreen('chat');
    initializeChat();
}

// Chat Functions
function initializeChat() {
    // Update companion name in UI
    Elements['companion-name'].textContent = AppState.companionName;
    Elements['welcome-companion-name'].textContent = AppState.companionName;
    
    // Load chat history
    loadChatHistory();
    
    // Focus message input
    Elements['message-input'].focus();
    
    // Update memory stats
    updateMemoryStats();
}

async function loadChatHistory() {
    try {
        const response = await fetch(`${Config.API_BASE}/chat/history`, {
            headers: {
                'Authorization': `Bearer ${AppState.authToken}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            AppState.conversationHistory = data.messages || [];
            displayChatHistory();
        }
        
    } catch (error) {
        console.error('Failed to load chat history:', error);
        // Continue without history - not critical
    }
}

function displayChatHistory() {
    const messagesContainer = Elements['chat-messages'];
    
    // Clear existing messages (except welcome)
    const existingMessages = messagesContainer.querySelectorAll('.message-container');
    existingMessages.forEach(msg => msg.remove());
    
    // Display recent messages (last 10)
    const recentMessages = AppState.conversationHistory.slice(-10);
    
    recentMessages.forEach(messageData => {
        if (messageData.content && messageData.content.messages) {
            messageData.content.messages.forEach(msg => {
                displayMessage(msg.content, msg.role === 'user' ? 'user' : 'ai', false);
            });
        }
    });
    
    scrollToBottom();
}

function handleMessageInput(e) {
    const input = e.target;
    const charCount = input.value.length;
    const maxLength = Config.MESSAGE_MAX_LENGTH;
    
    // Update character count
    Elements['char-count'].textContent = `${charCount}/${maxLength}`;
    
    // Enable/disable send button
    const canSend = charCount > 0 && charCount <= maxLength && !AppState.isTyping;
    Elements['send-btn'].disabled = !canSend;
    
    // Update char count color
    if (charCount > maxLength * 0.9) {
        Elements['char-count'].style.color = '#ff6b6b';
    } else if (charCount > maxLength * 0.7) {
        Elements['char-count'].style.color = '#ffa726';
    } else {
        Elements['char-count'].style.color = '#64748b';
    }
}

function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
}

function autoResizeTextarea() {
    const textarea = Elements['message-input'];
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
}

async function sendMessage() {
    const messageText = Elements['message-input'].value.trim();
    
    if (!messageText || AppState.isTyping) {
        return;
    }
    
    try {
        // Clear input and disable send button
        Elements['message-input'].value = '';
        Elements['send-btn'].disabled = true;
        Elements['char-count'].textContent = '0/2000';
        autoResizeTextarea();
        
        // Display user message
        displayMessage(messageText, 'user');
        
        // Show typing indicator
        showTypingIndicator(true);
        AppState.isTyping = true;
        
        // Send to backend
        const response = await fetch(`${Config.API_BASE}/chat/message`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${AppState.authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: messageText
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            
            // Simulate typing delay for better UX
            await new Promise(resolve => setTimeout(resolve, Config.TYPING_DELAY));
            
            // Display AI response
            displayMessage(data.response, 'ai');
            
            // Update memory stats if provided
            if (data.metadata) {
                updateMemoryStatsFromResponse(data.metadata);
            }
            
        } else {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to send message');
        }
        
    } catch (error) {
        console.error('Send message error:', error);
        
        // Display error message as AI response
        displayMessage(
            "I'm having trouble connecting right now. Please try again in a moment.", 
            'ai', 
            true
        );
        
        showError('Failed to send message. Please try again.');
        
    } finally {
        showTypingIndicator(false);
        AppState.isTyping = false;
        Elements['message-input'].focus();
    }
}

function displayMessage(content, sender, isError = false) {
    const messagesContainer = Elements['chat-messages'];
    
    // Create message container
    const messageContainer = document.createElement('div');
    messageContainer.className = `message-container ${sender}-message`;
    
    // Create message bubble
    const messageBubble = document.createElement('div');
    messageBubble.className = `message-bubble ${sender}-bubble`;
    
    if (isError) {
        messageBubble.classList.add('error-message');
    }
    
    // Add message content
    messageBubble.innerHTML = formatMessageContent(content);
    
    // Add timestamp
    const timestamp = document.createElement('div');
    timestamp.className = 'message-timestamp';
    timestamp.textContent = new Date().toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit'
    });
    
    messageContainer.appendChild(messageBubble);
    messageContainer.appendChild(timestamp);
    
    // Add to chat
    messagesContainer.appendChild(messageContainer);
    
    // Scroll to bottom
    scrollToBottom();
    
    // Add to conversation history
    AppState.conversationHistory.push({
        content: content,
        sender: sender,
        timestamp: new Date().toISOString(),
        isError: isError
    });
}

function formatMessageContent(content) {
    // Basic formatting - convert newlines to <br>
    let formatted = content.replace(/\n/g, '<br>');
    
    // Convert URLs to links
    const urlRegex = /(https?:\/\/[^\s]+)/g;
    formatted = formatted.replace(urlRegex, '<a href="$1" target="_blank" rel="noopener">$1</a>');
    
    // Convert **bold** to <strong>
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Convert *italic* to <em>
    formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>');
    
    return formatted;
}

function showTypingIndicator(show) {
    Elements['typing-indicator'].style.display = show ? 'flex' : 'none';
    
    if (show) {
        document.getElementById('status-text').textContent = 'Typing...';
    } else {
        document.getElementById('status-text').textContent = 'Online';
    }
}

function scrollToBottom() {
    const messagesContainer = Elements['chat-messages'];
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Memory Panel Functions
async function openMemoryPanel() {
    try {
        await updateMemoryStats();
        Elements['memory-panel'].style.display = 'flex';
    } catch (error) {
        console.error('Failed to open memory panel:', error);
        showError('Unable to load memory information');
    }
}

function closeMemoryPanel() {
    Elements['memory-panel'].style.display = 'none';
}

async function updateMemoryStats() {
    try {
        // This would call a backend endpoint for memory stats
        // For now, we'll use mock data
        const stats = {
            conversation_count: AppState.conversationHistory.length,
            memory_count: Math.floor(AppState.conversationHistory.length * 1.5),
            growth_score: Math.min(100, AppState.conversationHistory.length * 5)
        };
        
        AppState.memoryStats = stats;
        
        // Update UI
        const conversationCountEl = document.getElementById('conversation-count');
        const memoryCountEl = document.getElementById('memory-count');
        const growthScoreEl = document.getElementById('growth-score');
        
        if (conversationCountEl) conversationCountEl.textContent = stats.conversation_count;
        if (memoryCountEl) memoryCountEl.textContent = stats.memory_count;
        if (growthScoreEl) growthScoreEl.textContent = stats.growth_score;
        
    } catch (error) {
        console.error('Failed to update memory stats:', error);
    }
}

function updateMemoryStatsFromResponse(metadata) {
    if (metadata.memory_id) {
        AppState.memoryStats.memory_count = (AppState.memoryStats.memory_count || 0) + 1;
        AppState.memoryStats.growth_score = (AppState.memoryStats.growth_score || 0) + 1;
        
        // Update UI if memory panel is open
        const memoryCountEl = document.getElementById('memory-count');
        const growthScoreEl = document.getElementById('growth-score');
        
        if (memoryCountEl) memoryCountEl.textContent = AppState.memoryStats.memory_count;
        if (growthScoreEl) growthScoreEl.textContent = AppState.memoryStats.growth_score;
    }
}

// Settings Panel Functions
function openSettingsPanel() {
    // Populate current settings
    document.getElementById('settings-companion-name').value = AppState.companionName;
    
    const communicationStyle = AppState.userPreferences.communication_style || 'balanced';
    document.getElementById('settings-communication-style').value = communicationStyle;
    
    Elements['settings-panel'].style.display = 'flex';
}

function closeSettingsPanel() {
    Elements['settings-panel'].style.display = 'none';
}

async function saveSettings() {
    try {
        const newCompanionName = document.getElementById('settings-companion-name').value;
        const newCommunicationStyle = document.getElementById('settings-communication-style').value;
        const dataRetention = document.getElementById('data-retention').checked;
        const emotionalAnalysis = document.getElementById('emotional-analysis').checked;
        
        // Update app state
        AppState.companionName = newCompanionName;
        AppState.userPreferences.communication_style = newCommunicationStyle;
        AppState.userPreferences.data_retention = dataRetention;
        AppState.userPreferences.emotional_analysis = emotionalAnalysis;
        
        // Update UI
        Elements['companion-name'].textContent = newCompanionName;
        Elements['welcome-companion-name'].textContent = newCompanionName;
        
        // TODO: Send updates to backend
        // This would require a backend endpoint for updating preferences
        
        closeSettingsPanel();
        showSuccess('Settings saved successfully');
        
    } catch (error) {
        console.error('Failed to save settings:', error);
        showError('Failed to save settings. Please try again.');
    }
}

async function exportData() {
    try {
        // This would call a backend endpoint to export user data
        // For now, create a simple JSON export
        const exportData = {
            user_id: AppState.currentUser?.uid,
            companion_name: AppState.companionName,
            preferences: AppState.userPreferences,
            conversation_history: AppState.conversationHistory,
            memory_stats: AppState.memoryStats,
            exported_at: new Date().toISOString()
        };
        
        const dataStr = JSON.stringify(exportData, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        
        const link = document.createElement('a');
        link.href = URL.createObjectURL(dataBlob);
        link.download = `zentrafuge-data-${new Date().toISOString().split('T')[0]}.json`;
        link.click();
        
        showSuccess('Data exported successfully');
        
    } catch (error) {
        console.error('Failed to export data:', error);
        showError('Failed to export data. Please try again.');
    }
}

// Screen Management
function showScreen(screenName) {
    const screens = ['loading', 'auth', 'onboarding', 'chat'];
    
    screens.forEach(screen => {
        const element = document.getElementById(`${screen}-screen`);
        if (element) {
            element.style.display = screen === screenName ? 'flex' : 'none';
        }
    });
    
    AppState.currentScreen = screenName;
}

// Auth Form Switching
function switchToRegister() {
    document.getElementById('login-form').style.display = 'none';
    document.getElementById('register-form').style.display = 'block';
    clearAuthError();
}

function switchToLogin() {
    document.getElementById('register-form').style.display = 'none';
    document.getElementById('login-form').style.display = 'block';
    clearAuthError();
}

// Error and Success Handling
function showError(message) {
    const toast = Elements['error-toast'];
    const messageEl = toast.querySelector('.toast-message');
    
    messageEl.textContent = message;
    toast.style.display = 'flex';
    
    setTimeout(() => {
        hideErrorToast();
    }, Config.ERROR_DISPLAY_TIME);
}

function hideErrorToast() {
    Elements['error-toast'].style.display = 'none';
}

function showSuccess(message) {
    const toast = Elements['success-toast'];
    const messageEl = toast.querySelector('.toast-message');
    
    messageEl.textContent = message;
    toast.style.display = 'flex';
    
    setTimeout(() => {
        hideSuccessToast();
    }, Config.SUCCESS_DISPLAY_TIME);
}

function hideSuccessToast() {
    Elements['success-toast'].style.display = 'none';
}

function showAuthError(message) {
    const errorEl = Elements['auth-error'];
    errorEl.textContent = message;
    errorEl.style.display = 'block';
}

function clearAuthError() {
    const errorEl = Elements['auth-error'];
    errorEl.style.display = 'none';
    errorEl.textContent = '';
}

function showLoading(show) {
    // This could show/hide loading indicators
    // For now, just disable/enable forms
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        const inputs = form.querySelectorAll('input, button');
        inputs.forEach(input => {
            input.disabled = show;
        });
    });
}

// Utility Functions
function getAuthErrorMessage(error) {
    const errorMessages = {
        'auth/user-not-found': 'No account found with this email address',
        'auth/wrong-password': 'Incorrect password',
        'auth/email-already-in-use': 'An account with this email already exists',
        'auth/weak-password': 'Password should be at least 6 characters',
        'auth/invalid-email': 'Please enter a valid email address',
        'auth/user-disabled': 'This account has been disabled',
        'auth/too-many-requests': 'Too many failed attempts. Please try again later'
    };
    
    return errorMessages[error.code] || error.message || 'An authentication error occurred';
}

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    // Escape key closes panels
    if (e.key === 'Escape') {
        if (Elements['memory-panel'].style.display === 'flex') {
            closeMemoryPanel();
        }
        if (Elements['settings-panel'].style.display === 'flex') {
            closeSettingsPanel();
        }
    }
    
    // Ctrl/Cmd + Enter sends message
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        if (AppState.currentScreen === 'chat') {
            sendMessage();
        }
    }
});

// Click outside panels to close
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('overlay-panel')) {
        if (Elements['memory-panel'].style.display === 'flex') {
            closeMemoryPanel();
        }
        if (Elements['settings-panel'].style.display === 'flex') {
            closeSettingsPanel();
        }
    }
});

// Prevent zoom on iOS
document.addEventListener('touchstart', (e) => {
    if (e.touches.length > 1) {
        e.preventDefault();
    }
});

// Console welcome message
console.log(`
🧠 Zentrafuge v9 - Memory-First AI Companion
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Built with emotional intelligence and user sovereignty in mind.
Your data belongs to you. Your AI grows with you.

Need help? Check the documentation or contact support.
`);

// Export for debugging (development only)
if (typeof window !== 'undefined') {
    window.ZentrافugeDebug = {
        AppState,
        Config,
        Elements,
        showScreen,
        updateMemoryStats
    };
}
