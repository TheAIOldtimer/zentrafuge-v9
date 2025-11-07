// frontend/js/auth.js — Zentrafuge v9 (UK Veterans Edition)
// Using Firebase v8 global SDK
// Handles registration + login via Firebase Auth and your Flask backend

import Config from './config.js';
import {
  waitForFirebase,
  showMessage,
  showLoading,
  getFirebaseErrorMessage
} from './utils.js';
import { createUserProfile } from './api.js';

/**
 * Registers a new user with Firebase and your backend
 */
export async function loginUser(email, password) {
  try {
    showLoading('loading', true);
    showMessage('message', '');

    await waitForFirebase();

    const userCredential = await firebase
      .auth()
      .signInWithEmailAndPassword(email, password);

    const user = userCredential.user;

    // ✅ Enforce email verification before proceeding
    if (!user.emailVerified) {
      await firebase.auth().signOut();
      showMessage(
        'message',
        'Please verify your email before logging in.',
        true
      );
      return;
    }

    showMessage('message', 'Login successful! Redirecting...', false);

    setTimeout(() => {
      // ✅ Chat page lives at /html/chat.html
      const chatRoute =
        (Config && Config.ROUTES && Config.ROUTES.chat) || 'html/chat.html';
      window.location.href = chatRoute;
    }, Config.REDIRECT_DELAY || 2000);
  } catch (error) {
    console.error('Login error:', error);
    showMessage('message', getFirebaseErrorMessage(error), true);
  } finally {
    showLoading('loading', false);
  }
}

/**
 * Logs in an existing Firebase user
 */
export async function loginUser(email, password) {
  try {
    showLoading('loading', true);
    showMessage('message', '');

    await waitForFirebase();

    // ✅ Sign in with Firebase
    const userCredential = await firebase
      .auth()
      .signInWithEmailAndPassword(email, password);

    const user = userCredential.user;

    // ✅ Enforce email verification before proceeding
    if (!user.emailVerified) {
      await firebase.auth().signOut();
      showMessage(
        'message',
        'Please verify your email before logging in.',
        true
      );
      return;
    }

    showMessage('message', 'Login successful! Redirecting...', false);

    setTimeout(() => {
      window.location.href = Config?.ROUTES?.chat || 'chat.html';
    }, Config.REDIRECT_DELAY || 2000);
  } catch (error) {
    console.error('Login error:', error);
    showMessage('message', getFirebaseErrorMessage(error), true);
  } finally {
    showLoading('loading', false);
  }
}
