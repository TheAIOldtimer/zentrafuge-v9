// frontend/js/config.js

const Config = {
  API_BASE: 'https://zentrafuge-v9.onrender.com',
  ROUTES: {
    login: '/',                    // Use absolute path
    register: '/html/register.html',
    chat: '/html/chat.html',
    onboarding: '/html/onboarding.html',
  },
  REDIRECT_DELAY: 2000,            // 2 seconds
  FIREBASE_TIMEOUT: 10000,         // 10 seconds timeout for Firebase initialization
};

export default Config;
