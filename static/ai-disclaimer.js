/**
 * AI Disclaimer Modal Handler
 * Shows disclaimer modal on first visit and manages user acceptance
 */

class AIDisclaimerModal {
    constructor() {
        this.modal = document.getElementById('aiDisclaimerModal');
        this.acceptBtn = document.getElementById('acceptDisclaimer');
        this.modalLanguageToggle = document.getElementById('modalLanguageToggle');
        this.modalLanguageDropdown = document.getElementById('modalLanguageDropdown');
        this.modalCurrentLang = document.getElementById('modalCurrentLang');
        this.storageKey = 'doctor_ai_disclaimer_accepted';
        this.init();
    }

    init() {
        // Always show modal on every page visit
        // Show modal after a short delay to ensure page is fully loaded
        setTimeout(() => {
            this.showModal();
        }, 500);

        // Bind event listeners
        this.bindEvents();
    }

    bindEvents() {
        // Accept button click (add touch events for mobile)
        if (this.acceptBtn) {
            console.log('Binding events to accept button');
            // Make button more responsive on mobile
            this.acceptBtn.style.touchAction = 'manipulation';
            this.acceptBtn.style.pointerEvents = 'auto';
            
            // Add test class for debugging
            this.acceptBtn.classList.add('test-accept-button');
            
            // Use passive event listeners for better performance
            const acceptHandler = (e) => {
                console.log('Accept button clicked', e.type, e);
                e.preventDefault();
                e.stopPropagation();
                console.log('Calling acceptDisclaimer()');
                this.acceptDisclaimer();
            };
            
            // Clear any existing event listeners first
            const newAcceptBtn = this.acceptBtn.cloneNode(true);
            this.acceptBtn.parentNode.replaceChild(newAcceptBtn, this.acceptBtn);
            this.acceptBtn = newAcceptBtn;
            
            // Add both click and touch events with capture phase
            const options = { capture: true, passive: false };
            this.acceptBtn.addEventListener('click', acceptHandler, options);
            this.acceptBtn.addEventListener('touchend', acceptHandler, options);
            
            // Add pointer events as well
            this.acceptBtn.addEventListener('pointerup', acceptHandler, options);
            
            console.log('Event listeners added to accept button');
        }

        // Modal language selector
        if (this.modalLanguageToggle && this.modalLanguageDropdown) {
            this.modalLanguageToggle.addEventListener('click', (e) => {
                e.stopPropagation();
                this.modalLanguageDropdown.classList.toggle('show');
            });

            // Language option selection
            const languageOptions = this.modalLanguageDropdown.querySelectorAll('.language-option');
            languageOptions.forEach(option => {
                option.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const lang = option.getAttribute('data-lang');
                    this.changeModalLanguage(lang);
                    this.modalLanguageDropdown.classList.remove('show');
                });
            });

            // Close dropdown when clicking outside
            document.addEventListener('click', (e) => {
                if (!this.modalLanguageToggle.contains(e.target)) {
                    this.modalLanguageDropdown.classList.remove('show');
                }
            });
        }

        // Prevent modal from closing by clicking outside or ESC key
        if (this.modal) {
            this.modal.addEventListener('click', (e) => {
                // Only allow closing by clicking the accept button
                e.stopPropagation();
            });

            // Disable ESC key for this modal
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape' && this.modal.style.display === 'block') {
                    e.preventDefault();
                    e.stopPropagation();
                }
            });
        }
    }


    showModal() {
        if (this.modal) {
            this.modal.style.display = 'block';
            document.body.style.overflow = 'hidden'; // Prevent background scrolling
            
            // Sync modal language with current page language
            this.syncModalLanguage();
            
            // Add animation class
            setTimeout(() => {
                this.modal.classList.add('show');
            }, 10);

            // Focus on accept button for accessibility
            setTimeout(() => {
                if (this.acceptBtn) {
                    // Small delay to ensure the modal is fully visible
                    setTimeout(() => {
                        this.acceptBtn.focus();
                        // Ensure button is clickable
                        this.acceptBtn.style.pointerEvents = 'auto';
                    }, 50);
                }
            }, 300);
        }
    }

    hideModal() {
        console.log('hideModal() called');
        if (this.modal) {
            console.log('Removing show class from modal');
            this.modal.classList.remove('show');
            
            // Force reflow/repaint
            void this.modal.offsetHeight;
            
            setTimeout(() => {
                console.log('Hiding modal completely');
                this.modal.style.display = 'none';
                document.body.style.overflow = ''; // Restore scrolling
                console.log('Modal hidden');
                
                // Dispatch custom event when modal is fully hidden
                const event = new CustomEvent('disclaimerHidden', { detail: { timestamp: Date.now() } });
                document.dispatchEvent(event);
            }, 300);
        } else {
            console.warn('Modal element not found in hideModal()');
        }
    }

    acceptDisclaimer() {
        console.log('acceptDisclaimer() called');
        try {
            console.log('Hiding modal...');
            // Hide modal with animation
            this.hideModal();
            
            // Optional: Track acceptance for analytics
            console.log('Tracking acceptance...');
            this.trackAcceptance();
            
            console.log('acceptDisclaimer() completed');
        } catch (error) {
            console.error('Error in acceptDisclaimer:', error);
            // Still hide modal even if error occurs
            this.hideModal();
        }
    }

    trackAcceptance() {
        // Optional: Send analytics event
        try {
            if (typeof gtag !== 'undefined') {
                gtag('event', 'disclaimer_accepted', {
                    'event_category': 'user_interaction',
                    'event_label': 'ai_disclaimer'
                });
            }
        } catch (error) {
            // Silently fail if analytics not available
        }
    }

    syncModalLanguage() {
        // Get current language from localStorage or default to zh-TW
        let currentLang = 'zh-TW';
        try {
            currentLang = localStorage.getItem('selectedLanguage') || 'zh-TW';
        } catch (error) {
            // Fallback if localStorage is not available
        }

        // Update modal language display without triggering change
        const langMap = {
            'zh-TW': '繁',
            'zh-CN': '简',
            'en': 'EN'
        };
        
        if (this.modalCurrentLang) {
            this.modalCurrentLang.textContent = langMap[currentLang] || '繁';
        }

        // Update active state in dropdown
        if (this.modalLanguageDropdown) {
            const languageOptions = this.modalLanguageDropdown.querySelectorAll('.language-option');
            languageOptions.forEach(option => {
                option.classList.remove('active');
                if (option.getAttribute('data-lang') === currentLang) {
                    option.classList.add('active');
                }
            });
        }
    }

    changeModalLanguage(lang) {
        // Update modal language indicator
        const langMap = {
            'zh-TW': '繁',
            'zh-CN': '简',
            'en': 'EN'
        };
        
        if (this.modalCurrentLang) {
            this.modalCurrentLang.textContent = langMap[lang] || '繁';
        }

        // Update active state in dropdown
        const languageOptions = this.modalLanguageDropdown.querySelectorAll('.language-option');
        languageOptions.forEach(option => {
            option.classList.remove('active');
            if (option.getAttribute('data-lang') === lang) {
                option.classList.add('active');
            }
        });

        // Trigger global language change if the language system exists
        if (typeof window.changeLanguage === 'function') {
            window.changeLanguage(lang);
        } else if (typeof window.languageSystem !== 'undefined' && window.languageSystem.changeLanguage) {
            window.languageSystem.changeLanguage(lang);
        }
    }

    // Public method to manually show disclaimer (for testing or admin purposes)
    forceShow() {
        this.showModal();
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Create global instance
    window.aiDisclaimerModal = new AIDisclaimerModal();
});

// Export for potential module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AIDisclaimerModal;
}
