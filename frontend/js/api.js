import Config from './config.js';

export async function createUserProfile(token, userData) {
  const response = await fetch(`${Config.API_BASE}/user/profile`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(userData)
  });
  
  if (!response.ok) {
    throw new Error(`Profile creation failed: ${response.status}`);
  }
  
  return response.json();
}

export async function submitOnboarding(token, onboardingData) {
  const response = await fetch(`${Config.API_BASE}/user/onboarding`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(onboardingData)
  });
  
  if (!response.ok) {
    throw new Error(`Onboarding submission failed: ${response.status}`);
  }
  
  return response.json();
}

export async function sendChatMessage(token, message) {
  const response = await fetch(`${Config.API_BASE}/index`, {  // ✅ updated
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ message })
  });

  if (!response.ok) {
    throw new Error(`Chat message failed: ${response.status}`);
  }

  return response.json();
}

