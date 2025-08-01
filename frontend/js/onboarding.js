// js/onboarding.js - Enhanced onboarding functionality with veteran support

import Config from './config.js';
import { showMessage, showLoading } from './utils.js';

// Onboarding state
let currentOnboardingStep = 0;
const totalOnboardingSteps = 6; // 0-5 (Welcome, Name, Veteran, Communication, Emotional, Life Context, Completion)

export function initializeOnboarding() {
    currentOnboardingStep = 0;
    updateOnboardingProgress();
    showOnboardingStep(0);
    
    // Setup onboarding event listeners
    setupOnboardingListeners();
}

function setupOnboardingListeners() {
    // Name suggestion buttons
    const nameButtons = document.querySelectorAll('.name-btn');
    nameButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            setCaelName(btn.textContent);
        });
    });
    
    // Navigation buttons
    const nextButtons = document.querySelectorAll('.onboarding-next');
    nextButtons.forEach(btn => {
        btn.addEventListener('click', nextOnboardingStep);
    });
    
    const prevButtons = document.querySelectorAll('.onboarding-prev');
    prevButtons.forEach(btn => {
        btn.addEventListener('click', previousOnboardingStep);
    });
    
    // Completion button
    const completeButton = document.getElementById('complete-onboarding');
    if (completeButton) {
        completeButton.addEventListener('click', completeVeteranOnboarding);
    }
    
    // Enter chat button
    const enterChatButton = document.getElementById('enter-chat');
    if (enterChatButton) {
        enterChatButton.addEventListener('click', enterChat);
    }

    // Veteran checkbox toggle
    const veteranCheckbox = document.getElementById('veteran');
    const veteranDetails = document.getElementById('veteran-details');
    if (veteranCheckbox && veteranDetails) {
        veteranCheckbox.addEventListener('change', () => {
            veteranDetails.style.display = veteranCheckbox.checked ? 'block' : 'none';
        });
    }
}

function nextOnboardingStep() {
    if (currentOnboardingStep < totalOnboardingSteps - 1) {
        currentOnboardingStep++;
        updateOnboardingProgress();
        showOnboardingStep(currentOnboardingStep);
    }
}

function previousOnboardingStep() {
    if (currentOnboardingStep > 0) {
        currentOnboardingStep--;
        updateOnboardingProgress();
        showOnboardingStep(currentOnboardingStep);
    }
}

function showOnboardingStep(step) {
    // Hide all steps
    for (let i = 0; i < totalOnboardingSteps; i++) {
        const stepElement = document.getElementById(i === 2 ? 'onboarding-step-veteran' : `onboarding-step-${i}`);
        if (stepElement) {
            stepElement.style.display = 'none';
        }
    }
    
    // Show current step
    const currentStepElement = document.getElementById(step === 2 ? 'onboarding-step-veteran' : `onboarding-step-${step}`);
    if (currentStepElement) {
        currentStepElement.style.display = 'block';
    }
    
    // Update progress bar
    updateProgressBar();
}

function updateOnboardingProgress() {
    const progressDots = document.querySelectorAll('.progress-dot');
    progressDots.forEach((dot, index) => {
        dot.classList.remove('active', 'completed');
        if (index === currentOnboardingStep) {
            dot.classList.add('active');
        } else if (index < currentOnboardingStep) {
            dot.classList.add('completed');
        }
    });
}

function updateProgressBar() {
    const progressFill = document.querySelector('.progress-fill');
    if (progressFill) {
        const progress = ((currentOnboardingStep + 1) / totalOnboardingSteps) * 100;
        progressFill.style.width = `${progress}%`;
    }
}

function setCaelName(name) {
    const nameInput = document.getElementById('ai_name');
    if (nameInput) {
        nameInput.value = name;
    }
}

async function completeVeteranOnboarding() {
    try {
        showLoading('onboarding-loading', true);
        
        // Collect comprehensive onboarding data
        const onboardingData = {
            cael_name: document.getElementById('ai_name')?.value || 'Cael',
            communication_style: getSelectedRadioValue('communication_style') || 'balanced',
            emotional_pacing: getSelectedRadioValue('emotional_pacing') || 'varies_situation',
            life_chapter: document.getElementById('life_chapter')?.value || '',
            sources_of_meaning: getSelectedCheckboxValues('sources_of_meaning'),
            effective_support: getSelectedCheckboxValues('effective_support'),
            veteran_profile: {
                is_veteran: document.getElementById('veteran')?.checked || false,
                service_branch: document.getElementById('service_branch')?.value || null,
                service_country: document.getElementById('service_country')?.value || 'US',
                service_years: document.getElementById('service_years')?.value || null,
                unit_served: document.getElementById('unit_served')?.value || null,
                deployments: document.getElementById('deployments')?.value || null,
                verification_status: 'pending' // Will be verified by backend
            },
            preferences: {
                response_length: 'balanced',
                emotional_support: 'moderate',
                learning_speed: 'moderate'
            },
            onboarding_version: 'v9_enhanced',
            personality_profile: generatePersonalityProfile()
        };
        
        // Get current user token
        const user = firebase.auth().currentUser;
        if (!user) {
            throw new Error('User not authenticated');
        }
        
        const token = await user.getIdToken();
        
        // Send to backend
        const response = await fetch(`${Config.API_BASE}/user/onboarding`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(onboardingData)
        });
        
        if (response.ok) {
            const responseData = await response.json();
            console.log('✅ Onboarding completed successfully:', responseData);
            
            // If veteran verification is approved, initialize veteran system
            if (responseData.veteran_verified) {
                const veteranSystem = await initializeVeteranSystem();
                await veteranSystem.verifyVeteranStatus(user.uid, token);
            }
            
            // Store companion name globally
            window.companionName = onboardingData.cael_name;
            
            // Show completion step
            showOnboardingStep(5);
            
            // Show success message
            showMessage('onboarding-message', 'Setup completed successfully! Welcome to Zentrafuge.', false);
            
        } else {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to complete onboarding');
        }
        
    } catch (error) {
        console.error('❌ Onboarding completion error:', error);
        showMessage('onboarding-message', 'Failed to complete setup. Please try again.', true);
    } finally {
        showLoading('onboarding-loading', false);
    }
}

function getSelectedRadioValue(name) {
    const selected = document.querySelector(`input[name="${name}"]:checked`);
    return selected ? selected.value : null;
}

function getSelectedCheckboxValues(name) {
    const selected = document.querySelectorAll(`input[name="${name}"]:checked`);
    return Array.from(selected).map(cb => cb.value);
}

function generatePersonalityProfile() {
    // Generate a personality profile based on user selections
    const communicationStyle = getSelectedRadioValue('communication_style');
    const emotionalPacing = getSelectedRadioValue('emotional_pacing');
    const meaningSources = getSelectedCheckboxValues('sources_of_meaning');
    const supportTypes = getSelectedCheckboxValues('effective_support');
    
    return {
        communication_preference: communicationStyle,
        emotional_processing: emotionalPacing,
        meaning_sources: meaningSources,
        preferred_support: supportTypes,
        profile_completeness: calculateProfileCompleteness(),
        generated_at: new Date().toISOString()
    };
}

function calculateProfileCompleteness() {
    const fields = [
        getSelectedRadioValue('communication_style'),
        getSelectedRadioValue('emotional_pacing'),
        document.getElementById('life_chapter')?.value,
        getSelectedCheckboxValues('sources_of_meaning').length > 0,
        getSelectedCheckboxValues('effective_support').length > 0,
        document.getElementById('veteran')?.checked
    ];
    
    const completedFields = fields.filter(field => field && field !== '').length;
    return Math.round((completedFields / fields.length) * 100);
}

function enterChat() {
    // Redirect to chat page
    window.location.href = 'chat.html';
}
