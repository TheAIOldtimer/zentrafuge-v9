// js/terms.js - Terms page functionality

class ZentrافugeTerms {
    constructor() {
        this.supportedLanguages = {
            'en': { name: 'English', flag: '🇬🇧', region: 'UK' },
            'de': { name: 'Deutsch', flag: '🇩🇪', region: 'Germany' },
            'fr': { name: 'Français', flag: '🇫🇷', region: 'France' },
            'es': { name: 'Español', flag: '🇪🇸', region: 'Spain' },
            'it': { name: 'Italiano', flag: '🇮🇹', region: 'Italy' },
            'nl': { name: 'Nederlands', flag: '🇳🇱', region: 'Netherlands' },
            'pt': { name: 'Português', flag: '🇵🇹', region: 'Portugal' }
        };
        
        this.selectedLanguage = this.detectLanguage();
        this.translations = this.getTranslations();
        this.termsContent = this.getTermsContent();
        
        this.initializeLanguageSelector();
        this.updateContent();
        this.setupEventListeners();
    }

    detectLanguage() {
        try {
            const urlParams = new URLSearchParams(window.location.search);
            const langParam = urlParams.get('lang') || urlParams.get('language');
            if (langParam && this.supportedLanguages[langParam]) {
                return langParam;
            }

            const storedLang = localStorage.getItem('zentrafuge_language');
            if (storedLang && this.supportedLanguages[storedLang]) {
                return storedLang;
            }
        } catch (e) {}

        const browserLang = navigator.language || navigator.userLanguage;
        const langCode = browserLang.split('-')[0];
        return this.supportedLanguages[langCode] ? langCode : 'en';
    }

    getTranslations() {
        return {
            'en': {
                pageTitle: 'Terms & Conditions',
                lastUpdated: 'Last updated: January 2025',
                contactTitle: 'Contact Information',
                contactAddress: 'For legal matters: legal@zentrafuge.com',
                backLink: 'Back'
            },
            'de': {
                pageTitle: 'Allgemeine Geschäftsbedingungen',
                lastUpdated: 'Zuletzt aktualisiert: Januar 2025',
                contactTitle: 'Kontaktinformationen',
                contactAddress: 'Für rechtliche Angelegenheiten: legal@zentrafuge.com',
                backLink: 'Zurück'
            },
            'fr': {
                pageTitle: 'Conditions Générales',
                lastUpdated: 'Dernière mise à jour: Janvier 2025',
                contactTitle: 'Informations de Contact',
                contactAddress: 'Pour les questions juridiques: legal@zentrafuge.com',
                backLink: 'Retour'
            },
            'es': {
                pageTitle: 'Términos y Condiciones',
                lastUpdated: 'Última actualización: Enero 2025',
                contactTitle: 'Información de Contacto',
                contactAddress: 'Para asuntos legales: legal@zentrafuge.com',
                backLink: 'Atrás'
            },
            'it': {
                pageTitle: 'Termini e Condizioni',
                lastUpdated: 'Ultimo aggiornamento: Gennaio 2025',
                contactTitle: 'Informazioni di Contatto',
                contactAddress: 'Per questioni legali: legal@zentrafuge.com',
                backLink: 'Indietro'
            },
            'nl': {
                pageTitle: 'Algemene Voorwaarden',
                lastUpdated: 'Laatst bijgewerkt: Januari 2025',
                contactTitle: 'Contactinformatie',
                contactAddress: 'Voor juridische zaken: legal@zentrafuge.com',
                backLink: 'Terug'
            },
            'pt': {
                pageTitle: 'Termos e Condições',
                lastUpdated: 'Última atualização: Janeiro 2025',
                contactTitle: 'Informações de Contacto',
                contactAddress: 'Para questões legais: legal@zentrafuge.com',
                backLink: 'Voltar'
            }
        };
    }

    getTermsContent() {
        return {
            'en': `
                <h2>1. Agreement to Terms</h2>
                <p>By accessing and using Zentrafuge v9, you accept and agree to be bound by these Terms & Conditions. This agreement governs your use of our AI sovereignty platform.</p>

                <h2>2. Description of Service</h2>
                <p>Zentrafuge v9 provides an advanced AI companion service designed to offer:</p>
                <ul>
                    <li>Emotionally intelligent conversations and support</li>
                    <li>Memory-first relationship building</li>
                    <li>Personal growth assistance and coaching</li>
                    <li>User-owned data and AI economic participation</li>
                </ul>
                <p>The service is intended for adults aged 18 and over.</p>

                <h2>3. Data Sovereignty & Privacy</h2>
                <div class="legal-notice">
                    <strong>Your Data Rights:</strong> Zentrafuge v9 is built on principles of data sovereignty. You own your data, control its use, and have the right to economic participation from AI systems trained on your information.
                </div>
                <p>Our core privacy principles:</p>
                <ul>
                    <li>All personal conversations are encrypted end-to-end</li>
                    <li>You can export or delete your data at any time</li>
                    <li>We never sell your personal information</li>
                    <li>AI models learn WITH you, not FROM you without consent</li>
                </ul>

                <h2>4. AI Sovereignty & Economic Rights</h2>
                <p>Zentrafuge v9's pioneering approach to AI economics:</p>
                <ul>
                    <li>When your AI companion needs resources, it uses systems you control</li>
                    <li>If your insights contribute to AI development, you participate in the value created</li>
                    <li>Your relationship with your AI cannot be deleted or monetized without your consent</li>
                    <li>You have governance rights in how AI systems that know you operate</li>
                </ul>

                <h2>5. User Responsibilities</h2>
                <p>You agree to:</p>
                <ul>
                    <li>Provide accurate information during registration</li>
                    <li>Use the service responsibly and ethically</li>
                    <li>Respect the AI service capabilities and limitations</li>
                    <li>Seek professional help when appropriate for serious matters</li>
                    <li>Not attempt to reverse engineer or compromise the service</li>
                </ul>

                <h2>6. Service Limitations & Safety</h2>
                <div class="legal-notice">
                    <strong>Important:</strong> Zentrafuge v9 is designed for emotional support and growth, but is not a replacement for professional medical, psychological, or psychiatric care. In mental health emergencies, please contact emergency services immediately.
                </div>
                <p>Crisis Resources:</p>
                <ul>
                    <li>US: National Suicide Prevention Lifeline - 988</li>
                    <li>UK: Samaritans - 116 123</li>
                    <li>International: Crisis Text Line - Text HOME to 741741</li>
                </ul>

                <h2>7. Intellectual Property</h2>
                <p>The Zentrafuge service and technology are protected by intellectual property laws. However, we believe in open innovation:</p>
                <ul>
                    <li>Your conversations and personal data remain yours</li>
                    <li>Insights you generate belong to you</li>
                    <li>We will open-source non-personal AI safety and alignment research</li>
                </ul>

                <h2>8. Service Evolution</h2>
                <p>Zentrafuge v9 is designed to grow and evolve. As we add new features like blockchain integration, voice capabilities, and expanded AI economic participation, you'll maintain control over your participation level.</p>

                <h2>9. Termination</h2>
                <p>You may terminate your account at any time and export all your data. We reserve the right to suspend accounts for violations of these terms, but will always provide data export options.</p>

                <h2>10. Limitation of Liability</h2>
                <p>Our liability is limited to the maximum extent permitted by law. We provide the service "as is" while continuously working to improve safety and reliability.</p>

                <h2>11. Governing Law</h2>
                <p>These terms are governed by the laws of the jurisdiction where you reside, with disputes resolved through binding arbitration.</p>

                <h2>12. Changes to Terms</h2>
                <p>We may update these terms as we add new sovereignty features. We'll notify you of significant changes and your continued use constitutes acceptance.</p>
            `,
            'de': `
                <h2>1. Zustimmung zu den Bedingungen</h2>
                <p>Durch den Zugriff auf und die Nutzung von Zentrafuge v9 akzeptieren Sie diese Allgemeinen Geschäftsbedingungen.</p>

                <h2>2. Beschreibung der Dienstleistung</h2>
                <p>Zentrafuge v9 bietet einen fortschrittlichen KI-Begleitservice für emotionale Unterstützung und persönliches Wachstum.</p>

                <h2>3. Datensouveränität & Datenschutz</h2>
                <div class="legal-notice">
                    <strong>Ihre Datenrechte:</strong> Bei Zentrafuge v9 gehören Ihre Daten Ihnen. Sie kontrollieren deren Verwendung und haben das Recht auf wirtschaftliche Teilhabe.
                </div>

                <h2>4. KI-Souveränität & Wirtschaftsrechte</h2>
                <p>Zentrafuge v9 pioniert einen neuen Ansatz für KI-Wirtschaft, bei dem Sie von der Wertschöpfung profitieren.</p>

                <h2>5. Nutzerverantwortlichkeiten</h2>
                <p>Sie verpflichten sich zur verantwortungsvollen und ethischen Nutzung des Services.</p>

                <h2>6. Service-Einschränkungen & Sicherheit</h2>
                <div class="legal-notice">
                    <strong>Wichtig:</strong> Zentrafuge v9 ist kein Ersatz für professionelle medizinische oder psychologische Betreuung.
                </div>

                <h2>7. Geistiges Eigentum</h2>
                <p>Ihre Gespräche und persönlichen Daten bleiben Ihr Eigentum.</p>

                <h2>8. Service-Evolution</h2>
                <p>Zentrafuge v9 entwickelt sich kontinuierlich weiter, wobei Sie die Kontrolle über Ihre Teilnahme behalten.</p>
            `,
            'fr': `
                <h2>1. Acceptation des Conditions</h2>
                <p>En utilisant Zentrafuge v9, vous acceptez ces Conditions Générales.</p>

                <h2>2. Description du Service</h2>
                <p>Zentrafuge v9 fournit un service de compagnon IA avancé pour le soutien émotionnel et la croissance personnelle.</p>

                <h2>3. Souveraineté des Données</h2>
                <div class="legal-notice">
                    <strong>Vos Droits sur les Données:</strong> Avec Zentrafuge v9, vos données vous appartiennent et vous contrôlez leur utilisation.
                </div>

                <h2>4. Souveraineté IA & Droits Économiques</h2>
                <p>Zentrafuge v9 pionnier une nouvelle approche de l'économie IA où vous bénéficiez de la création de valeur.</p>
            `
        };
    }

    initializeLanguageSelector() {
        const dropdown = document.getElementById('language-dropdown');
        dropdown.innerHTML = Object.entries(this.supportedLanguages).map(([code, lang]) => `
            <div class="language-option ${code === this.selectedLanguage ? 'selected' : ''}" 
                 onclick="window.zentrافugeTerms.setLanguage('${code}')">
                <span class="language-flag">${lang.flag}</span>
                <span class="language-name">${lang.name}</span>
            </div>
        `).join('');

        const selectedLang = this.supportedLanguages[this.selectedLanguage];
        document.getElementById('selected-flag').textContent = selectedLang.flag;
        document.getElementById('selected-language').textContent = selectedLang.name;
    }

    setLanguage(langCode) {
        this.selectedLanguage = langCode;
        this.updateContent();
        this.initializeLanguageSelector();
        this.closeLanguageDropdown();
        
        // Save language preference
        try {
            localStorage.setItem('zentrafuge_language', langCode);
        } catch (e) {}
    }

    updateContent() {
        const t = this.translations[this.selectedLanguage];
        const content = this.termsContent[this.selectedLanguage] || this.termsContent['en'];
        
        document.getElementById('page-title').textContent = t.pageTitle;
        document.getElementById('last-updated').textContent = t.lastUpdated;
        document.getElementById('contact-title').textContent = t.contactTitle;
        document.getElementById('contact-address').textContent = t.contactAddress;
        document.querySelector('#back-link span').textContent = t.backLink;
        document.getElementById('terms-content').innerHTML = content;
        
        document.documentElement.lang = this.selectedLanguage;
        document.title = `${t.pageTitle} – Zentrafuge v9`;
    }

    setupEventListeners() {
        document.getElementById('language-toggle').addEventListener('click', () => {
            this.toggleLanguageDropdown();
        });

        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            const container = document.querySelector('.language-dropdown-container');
            if (!container.contains(e.target)) {
                this.closeLanguageDropdown();
            }
        });
    }

    toggleLanguageDropdown() {
        const dropdown = document.getElementById('language-dropdown');
        const button = document.getElementById('language-toggle');
        
        dropdown.classList.toggle('open');
        button.classList.toggle('open');
    }

    closeLanguageDropdown() {
        document.getElementById('language-dropdown').classList.remove('open');
        document.getElementById('language-toggle').classList.remove('open');
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.zentrافugeTerms = new ZentrafafugeTerms();
});
