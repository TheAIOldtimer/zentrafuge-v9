// js/chat.js - Chat functionality (Updated for your Firebase setup)

import Config from './config.js';
import { sendChatMessage } from './api.js';
import { waitForFirebase } from './utils.js';

let currentUser = null;
let chatContainer = null;
let messageInput = null;
let sendButton = null;

document.addEventListener('DOMContentLoaded', function() {
    initializeChat();
});

async function initializeChat() {
    // Get DOM elements
    chatContainer = document.getElementById('chat-messages');
    messageInput = document.getElementById('message-input');
    sendButton = document.getElementById('send-btn');
    
    // Set up event listeners
    document.getElementById('chat-form').addEventListener('submit', handleSendMessage);
    document.getElementById('logout-btn').addEventListener('click', handleLogout);
    
    // Check authentication
    await checkAuthentication();
    
    // Show welcome message
    showWelcomeMessage();
    
    // Auto-focus input
    messageInput.focus();
}

async function checkAuthentication() {
    try {
        await waitForFirebase();
        
        // Use your global firebase auth
        firebase.auth().onAuthStateChanged((user) => {
            if (user) {
                currentUser = user;
                document.getElementById('user-name').textContent = user.displayName || user.email;
                
                // Log user info for debugging
                console.log('👤 Chat user:', {
                    email: user.email,
                    verified: user.emailVerified,
                    name: user.displayName
                });
            } else {
                // Redirect to login if not authenticated
                console.log('❌ No authenticated user, redirecting to login');
                window.location.href = '../index.html';
            }
        });
    } catch (error) {
        console.error('Authentication check failed:', error);
        window.location.href = '../index.html';
    }
}

async function handleSendMessage(e) {
    e.preventDefault();
    
    const message = messageInput.value.trim();
    if (!message || !currentUser) return;
    
    // Disable input while sending
    setInputState(false);
    
    // Add user message to chat
    addMessage(message, 'user');
    
    // Clear input
    messageInput.value = '';
    
    // Show typing indicator
    showTypingIndicator();
    
    try {
        // Get auth token
        const token = await currentUser.getIdToken();
        
        // Send message to backend
        const response = await sendChatMessage(token, message);
        
        // Remove typing indicator
        hideTypingIndicator();
        
        // Add AI response
        if (response.reply) {
            addMessage(response.reply, 'assistant');
        } else {
            addMessage('Sorry, I encountered an error processing your message.', 'system');
        }
        
    } catch (error) {
        console.error('Chat error:', error);
        hideTypingIndicator();
        addMessage('Connection error. Please try again.', 'system');
    } finally {
        setInputState(true);
        messageInput.focus();
    }
}

function addMessage(content, type) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    
    const contentDiv = document.createElement('div');
    contentDiv.textContent = content;
    
    const timeDiv = document.createElement('div');
    timeDiv.className = 'message-time';
    timeDiv.textContent = new Date().toLocaleTimeString();
    
    messageDiv.appendChild(contentDiv);
    if (type !== 'system') {
        messageDiv.appendChild(timeDiv);
    }
    
    chatContainer.appendChild(messageDiv);
    scrollToBottom();
}

function showTypingIndicator() {
    const typingDiv = document.createElement('div');
    typingDiv.className = 'typing-indicator';
    typingDiv.id = 'typing-indicator';
    
    typingDiv.innerHTML = `
        <span>Cael is typing</span>
        <div class="typing-dots">
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        </div>
    `;
    
    chatContainer.appendChild(typingDiv);
    scrollToBottom();
}

function hideTypingIndicator() {
    const indicator = document.getElementById('typing-indicator');
    if (indicator) {
        indicator.remove();
    }
}

function showWelcomeMessage() {
    addMessage('Hello! I\'m Cael, your AI companion. I\'m here to learn about you and grow alongside you. What would you like to talk about today?', 'assistant');
}

function setInputState(enabled) {
    messageInput.disabled = !enabled;
    sendButton.disabled = !enabled;
    
    if (enabled) {
        sendButton.textContent = 'Send';
    } else {
        sendButton.textContent = 'Sending...';
    }
}

function scrollToBottom() {
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

async function handleLogout() {
    try {
        await firebase.auth().signOut();
        window.location.href = '../index.html';
    } catch (error) {
        console.error('Logout error:', error);
    }
}

// Handle enter key in textarea
document.addEventListener('keydown', function(e) {
    if (e.target === messageInput && e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        document.getElementById('chat-form').dispatchEvent(new Event('submit'));
    }
});
