// js/chat.js - Chat functionality (Zentrafuge v9, UK Veterans)

import Config from './config.js';
import { sendChatMessage } from './api.js';
import { waitForFirebase } from './utils.js';

let currentUser = null;
let chatContainer = null;
let messageInput = null;
let sendButton = null;

console.log('🟢 chat.js loaded');

document.addEventListener('DOMContentLoaded', () => {
  initializeChat();
});

async function initializeChat() {
  // Grab DOM elements
  chatContainer = document.getElementById('chat-messages');
  messageInput = document.getElementById('message-input');
  sendButton = document.getElementById('send-btn');

  const form = document.getElementById('chat-form');
  const logoutBtn = document.getElementById('logout-btn');

  if (form) {
    form.addEventListener('submit', handleSendMessage);
  }
  if (logoutBtn) {
    logoutBtn.addEventListener('click', handleLogout);
  }

  // Check authentication before enabling chat
  await checkAuthentication();

  if (messageInput) {
    messageInput.focus();
  }
}

async function checkAuthentication() {
  try {
    await waitForFirebase();

    console.log('🔍 Checking Firebase auth state…');

    // Wait once for initial auth state
    const user = await new Promise((resolve) => {
      const unsubscribe = firebase.auth().onAuthStateChanged((u) => {
        unsubscribe();
        resolve(u);
      });
    });

    if (!user) {
      console.log('❌ No authenticated user, redirecting to login');
      // Login page is /index.html at root, chat.html is /html/chat.html
      window.location.href = '../index.html';
      return;
    }

    console.log('👤 Firebase user found:', {
      uid: user.uid,
      email: user.email,
      verified: user.emailVerified,
    });

    // Check if user has completed onboarding
    const userDoc = await firebase
      .firestore()
      .collection('users')
      .doc(user.uid)
      .get();

    if (!userDoc.exists || !userDoc.data().onboarding_complete) {
      console.log('⚠️ User not onboarded, redirecting to onboarding…');
      // chat.html and onboarding.html live together under /html/
      window.location.href = 'onboarding.html';
      return;
    }

    // ✅ Authenticated and onboarded
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

    showWelcomeMessage();
  } catch (error) {
    console.error('❌ Authentication check failed:', error);

    // 🔴 DO NOT redirect back to index here – that feeds the loop.
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

    setInputState(false);
  }
}

async function handleSendMessage(e) {
  e.preventDefault();

  const message = messageInput.value.trim();
  if (!message || !currentUser) return;

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
    if (response && (response.reply || response.response)) {
      // support both { reply } and { response }
      const text = response.reply || response.response;
      addMessage(text, 'assistant');
    } else {
      addMessage(
        'Sorry, I encountered an error processing your message.',
        'system'
      );
    }
  } catch (error) {
    console.error('Chat error:', error);
    hideTypingIndicator();
    addMessage('Connection error. Please try again.', 'system');
  } finally {
    setInputState(true);
    if (messageInput) messageInput.focus();
  }
}

function addMessage(content, type) {
  if (!chatContainer) return;

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
  if (!chatContainer) return;

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
  addMessage(
    "Hello! I'm Cael, your AI companion. I'm here to learn about you and grow alongside you. What would you like to talk about today?",
    'assistant'
  );
}

function setInputState(enabled) {
  if (messageInput) messageInput.disabled = !enabled;
  if (sendButton) sendButton.disabled = !enabled;

  if (sendButton) {
    sendButton.textContent = enabled ? 'Send' : 'Sending...';
  }
}

function scrollToBottom() {
  if (!chatContainer) return;
  chatContainer.scrollTop = chatContainer.scrollHeight;
}

async function handleLogout() {
  try {
    await firebase.auth().signOut();
    // Login page is /index.html at root
    window.location.replace('/');
  } catch (error) {
    console.error('Logout error:', error);
  }
}

// Handle Enter key in textarea (send on Enter, new line on Shift+Enter)
document.addEventListener('keydown', function (e) {
  if (e.target === messageInput && e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    const form = document.getElementById('chat-form');
    if (form) {
      form.dispatchEvent(new Event('submit'));
    }
  }
});
