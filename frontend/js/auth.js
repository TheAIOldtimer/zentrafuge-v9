import Config from './config.js';
import { waitForFirebase, showMessage, showLoading, getFirebaseErrorMessage } from './utils.js';
import { createUserProfile } from './api.js';

export async function registerUser(formData) {
  try {
    showLoading('loading', true);
    showMessage('message', '');
    
    await waitForFirebase();
    
    // Create Firebase user
    const userCredential = await firebase.auth().createUserWithEmailAndPassword(
      formData.email, 
      formData.password
    );
    const user = userCredential.user;
    
    // Update profile
    await user.updateProfile({ displayName: formData.name });
    
    // Get token and create backend profile
    const token = await user.getIdToken();
    await createUserProfile(token, {
      name: formData.name,
      email: formData.email,
      is_veteran: formData.isVeteran,
      marketing_opt_in: false
    });
    
    showMessage('message', 'Account created successfully! Redirecting...', false);
    
    setTimeout(() => {
      window.location.href = Config.ROUTES.login;
    }, Config.REDIRECT_DELAY);
    
  } catch (error) {
    console.error('Registration error:', error);
    showMessage('message', getFirebaseErrorMessage(error), true);
  } finally {
    showLoading('loading', false);
  }
}

export async function loginUser(email, password) {
  try {
    showLoading('loading', true);
    showMessage('message', '');
    
    await waitForFirebase();
    
    const userCredential = await firebase.auth().signInWithEmailAndPassword(email, password);
    
    showMessage('message', 'Login successful! Redirecting...', false);
    
    setTimeout(() => {
      window.location.href = Config.ROUTES.chat;
    }, Config.REDIRECT_DELAY);
    
  } catch (error) {
    console.error('Login error:', error);
    showMessage('message', getFirebaseErrorMessage(error), true);
  } finally {
    showLoading('loading', false);
  }
}
