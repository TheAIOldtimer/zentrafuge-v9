export function showLoading(elementId, show = true) {
  const element = document.getElementById(elementId);
  if (element) {
    element.style.display = show ? 'block' : 'none';
  }
}

export function showMessage(containerId, message, isError = false) {
  const container = document.getElementById(containerId);
  if (container) {
    const className = isError ? 'message-error' : 'message-success';
    container.innerHTML = `<div class="${className}">${message}</div>`;
  }
}

export function waitForFirebase() {
  return new Promise((resolve, reject) => {
    if (typeof firebase !== 'undefined' && firebase.apps.length > 0) {
      resolve();
      return;
    }
    
    window.addEventListener('firebaseReady', () => resolve());
    setTimeout(() => reject(new Error('Firebase timeout')), Config.FIREBASE_TIMEOUT);
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
    'auth/operation-not-allowed': 'This operation is currently disabled'
  };
  
  return errorMessages[error.code] || error.message || 'An error occurred. Please try again.';
}
