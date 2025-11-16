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

    // ✅ Sign out so they have to verify first
    await firebase.auth().signOut();

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

    let user = userCredential.user;

    // ✅ Reload user to get fresh email verification status
    await user.reload();
    user = firebase.auth().currentUser;

    // ✅ Enforce email verification before proceeding
    if (!user.emailVerified) {
      await firebase.auth().signOut();
      showMessage(
        'message',
        'Please verify your email before logging in. Check your inbox (and spam folder).',
        true
      );
      
      // Offer to resend verification email
      const messageDiv = document.getElementById('message');
      if (messageDiv) {
        const resendLink = document.createElement('a');
        resendLink.href = '#';
        resendLink.textContent = 'Resend verification email';
        resendLink.style.cssText = 'display: block; margin-top: 0.5rem; color: #3b82f6; text-decoration: underline;';
        resendLink.onclick = async (e) => {
          e.preventDefault();
          try {
            // Sign in again to send email
            const tempUser = await firebase.auth().signInWithEmailAndPassword(email, password);
            await tempUser.user.sendEmailVerification();
            await firebase.auth().signOut();
            showMessage('message', 'Verification email sent! Please check your inbox.', false);
          } catch (err) {
            console.error('Resend error:', err);
            showMessage('message', 'Could not resend email. Please try again later.', true);
          }
        };
        messageDiv.appendChild(resendLink);
      }
      
      return;
    }

    // ✅ FIXED: Check onboarding status BEFORE redirecting
    console.log('🔍 Checking onboarding status...');
    
    try {
      const userDoc = await firebase
        .firestore()
        .collection('users')
        .doc(user.uid)
        .get();

      const userData = userDoc.exists ? userDoc.data() : null;
      const onboardingComplete = userData?.onboarding_complete || false;

      console.log('📊 User data:', {
        exists: userDoc.exists,
        onboarding_complete: onboardingComplete
      });

      if (!onboardingComplete) {
        // User needs onboarding
        console.log('⚠️ Onboarding not complete, redirecting to onboarding...');
        showMessage('message', 'Please complete your profile setup...', false);
        
        setTimeout(() => {
          window.location.href = '/html/onboarding.html';
        }, 1000);
        return;
      }

      // ✅ User has completed onboarding, go to chat
      console.log('✅ Onboarding complete, redirecting to chat...');
      showMessage('message', 'Login successful! Redirecting...', false);

      setTimeout(() => {
        window.location.replace('/html/chat.html');
      }, Config.REDIRECT_DELAY || 2000);

    } catch (firestoreError) {
      console.error('❌ Error checking onboarding status:', firestoreError);
      
      // If we can't check Firestore, assume they need onboarding
      console.log('⚠️ Could not check onboarding status, redirecting to onboarding...');
      showMessage('message', 'Setting up your profile...', false);
      
      setTimeout(() => {
        window.location.href = '/html/onboarding.html';
      }, 1000);
    }

  } catch (error) {
    console.error('Login error:', error);
    showMessage('message', getFirebaseErrorMessage(error), true);
  } finally {
    showLoading('loading', false);
  }
}
