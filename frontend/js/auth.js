// frontend/js/auth.js — Zentrafuge v9 (UK Veterans Edition)
// Using Firebase compat SDK (global `firebase` object)
// Handles registration + login via Firebase Auth and your Flask backend

import Config from './config.js';
import {
  waitForFirebase,
  showMessage,
  showLoading,
  getFirebaseErrorMessage,
} from './utils.js';
import { createUserProfile } from './api.js';

/**
 * Registers a new user with Firebase and your backend
 */
export async function registerUser(formData) {
  try {
    showLoading('loading', true);
    showMessage('message', '');

    // Wait until Firebase SDK has loaded
    await waitForFirebase();

    // ✅ Create user in Firebase Auth
    const userCredential = await firebase
      .auth()
      .createUserWithEmailAndPassword(formData.email, formData.password);

    const user = userCredential.user;

    // ✅ Send email verification
    await user.sendEmailVerification();

    // ✅ Update Firebase user profile with display name
    await user.updateProfile({ displayName: formData.name });

    // ✅ Create profile in your backend via API
    const token = await user.getIdToken();
    try {
      await createUserProfile(token, {
        name: formData.name,
        email: formData.email,
        is_veteran: formData.isVeteran,
        marketing_opt_in: false,
      });
    } catch (apiError) {
      console.warn('⚠️ Backend profile creation failed:', apiError);
      showMessage(
        'message',
        'Account created, but we had trouble saving your profile. Please contact support if needed.',
        true
      );
    }

    // ✅ Notify user and redirect to login
    showMessage(
      'message',
      'Account created! Please check your email and verify before logging in.',
      false
    );

    setTimeout(() => {
      // Use absolute path to root
      window.location.href = '/';
    }, Config.REDIRECT_DELAY || 3000);
  } catch (error) {
    console.error('Registration error:', error);
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
      // Use absolute path to chat
      window.location.replace('/html/chat.html');
    }, Config.REDIRECT_DELAY || 2000);
  } catch (error) {
    console.error('Login error:', error);
    showMessage('message', getFirebaseErrorMessage(error), true);
  } finally {
    showLoading('loading', false);
  }
}
