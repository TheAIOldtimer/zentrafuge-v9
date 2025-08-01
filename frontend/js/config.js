const Config = {
  API_BASE: 'http://localhost:5000',
  FIREBASE_TIMEOUT: 10000,
  REDIRECT_DELAY: 2000,
  
  // Firebase config will be loaded from firebase.js
  ROUTES: {
    login: 'index.html',
    register: 'register.html', 
    chat: 'chat.html',
    emailVerified: 'email-verified.html'
  }
};

export default Config;
