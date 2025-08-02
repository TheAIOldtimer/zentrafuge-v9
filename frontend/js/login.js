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
    firebase.auth().onAuthStateChanged(async (user) => {
      if (user) {
        const uid = user.uid;
        const userDoc = await firebase.firestore().collection('users').doc(uid).get();

        if (userDoc.exists && userDoc.data().onboarding_complete) {
          window.location.href = 'chat.html';
        } else {
          window.location.href = 'onboarding.html';
        }
      }
    });
  } catch (err) {
    console.warn('Firebase not ready in time:', err);
  }
}
