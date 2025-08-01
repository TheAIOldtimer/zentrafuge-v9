/**
 * Zentrafuge v9 - Firebase Configuration
 * Using Firebase v9 compat SDK for compatibility with existing code
 */

// Your Firebase configuration
const firebaseConfig = {
    apiKey: "AIzaSyA0UGTSall_tMMIQWd7PBrjM-xIibiAQ-8",
    authDomain: "zentrafuge-v9.firebaseapp.com",
    projectId: "zentrafuge-v9",
    storageBucket: "zentrafuge-v9.appspot.com",
    messagingSenderId: "188961704770",
    appId: "1:188961704770:web:91de60d7aa0c696c52d6db",
    measurementId: "G-X5YXZMLNW4"
};

// Initialize Firebase
let firebaseApp;
let auth;
let firestore;

try {
    console.log('🔥 Initializing Firebase...');
    
    // Check if Firebase is loaded
    if (typeof firebase === 'undefined') {
        throw new Error('Firebase SDK not loaded. Please check your script tags.');
    }
    
    // Initialize Firebase App
    firebaseApp = firebase.initializeApp(firebaseConfig);
    
    // Initialize services
    auth = firebase.auth();
    firestore = firebase.firestore();
    
    console.log('✅ Firebase initialized successfully');
    console.log('📱 Firebase App:', firebaseApp.name);
    
    // Enable offline persistence for Firestore
    firestore.enablePersistence({ synchronizeTabs: true })
        .then(() => {
            console.log('✅ Firestore offline persistence enabled');
        })
        .catch((err) => {
            if (err.code === 'failed-precondition') {
                console.warn('⚠️ Firestore persistence failed: Multiple tabs open');
            } else if (err.code === 'unimplemented') {
                console.warn('⚠️ Firestore persistence not available in this browser');
            } else {
                console.warn('⚠️ Firestore persistence error:', err);
            }
        });
    
    // Dispatch ready event for other scripts
    if (typeof window !== 'undefined') {
        window.dispatchEvent(new CustomEvent('firebaseReady', {
            detail: { app: firebaseApp, auth, firestore }
        }));
    }
    
} catch (error) {
    console.error('❌ Firebase initialization failed:', error);
    
    // Show user-friendly error
    const showFirebaseError = () => {
        const errorDiv = document.createElement('div');
        errorDiv.innerHTML = `
            <div style="
                position: fixed; 
                top: 20px; 
                left: 50%; 
                transform: translateX(-50%); 
                background: #fef2f2; 
                color: #dc2626; 
                padding: 1rem 2rem; 
                border-radius: 8px; 
                border: 1px solid #fecaca;
                z-index: 9999;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                max-width: 90%;
                text-align: center;
            ">
                <strong>🔥 Firebase Connection Error</strong><br>
                ${error.message}<br>
                <small>Please refresh the page and try again.</small>
            </div>
        `;
        document.body.appendChild(errorDiv);
        
        // Auto-remove after 10 seconds
        setTimeout(() => {
            if (errorDiv.parentNode) {
                errorDiv.parentNode.removeChild(errorDiv);
            }
        }, 10000);
    };
    
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', showFirebaseError);
    } else {
        showFirebaseError();
    }
}

// Export for global access (compat mode)
if (typeof window !== 'undefined') {
    window.firebaseApp = firebaseApp;
    window.firebaseAuth = auth;
    window.firebaseFirestore = firestore;
}

// Firebase Auth state change handler
if (auth) {
    auth.onAuthStateChanged((user) => {
        if (user) {
            console.log('👤 User signed in:', user.email);
            console.log('✅ Email verified:', user.emailVerified);
            window.currentUser = user;
        } else {
            console.log('👤 User signed out');
            window.currentUser = null;
        }
        
        // Dispatch auth state change event
        if (typeof window !== 'undefined') {
            window.dispatchEvent(new CustomEvent('authStateChanged', { 
                detail: { user } 
            }));
        }
    });
}

console.log('🔥 Firebase configuration loaded');
