// js/utils.js - Utility Functions (Updated for your Firebase setup)

import Config from './config.js';

export function showLoading(elementId, show = true) {
  const element = document.getElementById(elementId);
  if (element) {
    if (show) {
      element.classList.remove('hidden');
    } else {
      element.classList.add('hidden');
    }
  }
}

export function showMessage(containerId, message, isError = false) {
  const container = document.getElementById(containerId);
  if (container) {
    if (message) {
      const className = isError ? 'message-error' : 'message-success';
      container.innerHTML = `<div class="${className}">${message}</div>`;
    } else {
      container.innerHTML = '';
    }
  }
}

export function waitForFirebase() {
  return new Promise((resolve, reject) => {
    // Check if Firebase is already ready (using your global setup)
    if (typeof firebase !== 'undefined' && firebase.apps.length > 0 && window.firebaseAuth) {
      resolve();
      return;
    }
    
    // Listen for your custom firebaseReady event
    const handleReady = () => {
      window.removeEventListener('firebaseReady', handleReady);
      resolve();
    };
    
    window.addEventListener('firebaseReady', handleReady);
    
    // Timeout after 10 seconds
    setTimeout(() => {
      window.removeEventListener('firebaseReady', handleReady);
      reject(new Error('Firebase initialization timeout'));
    }, Config.FIREBASE_TIMEOUT);
  });
}

export function validateEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

export function getFirebaseErrorMessage(error) {
  const errorMessages = {
    'auth/email-already-in-use': 'An account with this email already exists',
    'auth/weak-password': 'Password should be at least 6 characters',
    'auth/invalid-email': 'Please enter a valid email address',
    'auth/user-not-found': 'No account found with this email',
    'auth/wrong-password': 'Incorrect password',
    'auth/operation-not-allowed': 'This operation is currently disabled',
    'auth/too-many-requests': 'Too many failed attempts. Please try again later.',
    'auth/network-request-failed': 'Network error. Please check your connection.'
  };
  
  return errorMessages[error.code] || error.message || 'An error occurred. Please try again.';
}

export function formatTimestamp(timestamp) {
  return new Date(timestamp).toLocaleTimeString();
}

export function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}
