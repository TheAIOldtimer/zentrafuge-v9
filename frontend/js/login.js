// js/login.js - Login page logic

import { loginUser } from './auth.js';
import { showMessage, waitForFirebase } from './utils.js';

document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('login-form').addEventListener('submit', handleLogin);
  checkAuthState();
});

async function handleLogin(e) {
  e.preventDefault();

  const email = document.getElementById('email').value.trim();
  const password = document.getElementById('password').value;

  if (!email) {
    showMessage('message', 'Please enter your email address', true);
    return;
  }

  if (!password) {
    showMessage('message', 'Please enter your password', true);
    return;
  }

  await loginUser(email, password);
}

async function checkAuthState() {
  try {
    await waitForFirebase();
    firebase.auth().onAuthStateChanged((user) => {
      if (user) {
        window.location.href = 'chat.html';
      }
    });
  } catch (err) {
    console.warn('Firebase not ready in time:', err);
  }
}
