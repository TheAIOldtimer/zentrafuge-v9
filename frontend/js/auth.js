// js/auth.js - Authentication Logic (Zentrafuge v9)

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
export async function registerUser(formData) {
  try {
    showLoading('loading', true);
    showMessage('message', '');

    await waitForFirebase();

    // Create user in Firebase Auth
    const userCredential = await firebase
      .auth()
      .createUserWithEmailAndPassword(formData.email, formData.password);

    const user = userCredential.user;

    // Optionally send email verification
    // await user.sendEmailVerification();

    // Update Firebase user profile with display name
    await user.updateProfile({ displayName: formData.name });

    // Create user profile in your backend
    const token = await user.getIdToken();
    try {
      await createUserProfile(token, {
        name: formData.name,
        email: formData.email,
        is_veteran: formData.isVeteran,
        marketing_opt_in: false
      });
    } catch (apiError) {
      console.warn('⚠️ Backend profile creation failed:', apiError);
      showMessage(
        'message',
        'Account created, but we had trouble saving your profile. Please contact support if needed.',
        true
      );
    }

    // Notify user and redirect
    showMessage('message', 'Account created successfully! Redirecting...', false);

    setTimeout(() => {
      window.location.href = Config?.ROUTES?.login || 'index.html';
    }, Config.REDIRECT_DELAY);
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

    const userCredential = await firebase
      .auth()
      .signInWithEmailAndPassword(email, password);

    const user = userCredential.user;

    // Optional: Enforce email verification
    // if (!user.emailVerified) {
    //   showMessage('message', 'Please verify your email before logging in.', true);
    //   return;
    // }

    showMessage('message', 'Login successful! Redirecting...', false);

    setTimeout(() => {
      window.location.href = Config?.ROUTES?.chat || 'chat.html';
    }, Config.REDIRECT_DELAY);
  } catch (error) {
    console.error('Login error:', error);
    showMessage('message', getFirebaseErrorMessage(error), true);
  } finally {
    showLoading('loading', false);
  }
}
