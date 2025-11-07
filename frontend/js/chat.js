// js/chat.js - Chat functionality (Updated for your Firebase setup)

import Config from './config.js';
import { sendChatMessage } from './api.js';
import { waitForFirebase } from './utils.js';

// DON'T check profile immediately - wait for proper auth state
// async function checkUserProfile() { ... }
// checkUserProfile(); ← REMOVE THIS LINE

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
    
    // Check authentication (this handles redirects properly)
    await checkAuthentication();
    
    // Auto-focus input
    if (messageInput) messageInput.focus();
}

async function checkAuthentication() {
  try {
    await waitForFirebase();

    // Wait once for initial auth state
    const user = await new Promise((resolve) => {
      const unsubscribe = firebase.auth().onAuthStateChanged((u) => {
        unsubscribe();
        resolve(u);
      });
    });

    if (!user) {
      console.log('❌ No authenticated user, redirecting to login');
      // Login page is root /index.html, so from /html/chat.html this is correct:
      window.location.href = '../index.html';
      return;
    }

    // Check if user has completed onboarding
    const userDoc = await firebase
      .firestore()
      .collection('users')
      .doc(user.uid)
      .get();

    if (!userDoc.exists || !userDoc.data().onboarding_complete) {
      console.log('⚠️ User not onboarded, redirecting to onboarding...');
      // chat.html and onboarding.html live together under /html/
      window.location.href = 'onboarding.html';
      return;
    }

    // ✅ User is authenticated and onboarded
    currentUser = user;

    const nameEl = document.getElementById('user-name');
    if (nameEl) {
      nameEl.textContent = user.displayName || user.email || 'You';
    }

    console.log('✅ Chat ready for user:', {
      email: user.email,
      verified: user.emailVerified,
      name: user.displayName,
    });

    // NOW show welcome message after everything is ready
    showWelcomeMessage();

  } catch (error) {
    console.error('❌ Authentication check failed:', error);

    // 🔴 Do NOT bounce back to index here – that feeds the loop.
    const messages = document.getElementById('chat-messages');
    if (messages) {
      const div = document.createElement('div');
      div.className = 'message assistant';
      div.innerHTML = `
        <div class="message-content">
          I'm having trouble confirming your login right now.
          Please go back to the main page and sign in again.
        </div>
      `;
      messages.appendChild(div);
    }

    // Disable input so the user isn't typing into a broken session
    setInputState(false);
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
