/**
 * AI Disclaimer Modal Handler
 * Shows disclaimer modal on first visit and manages user acceptance
 */

class AIDisclaimerModal {
    constructor() {
        this.modal = document.getElementById('aiDisclaimerModal');
        this.acceptBtn = document.getElementById('acceptDisclaimer');
        this.contentWrapper = document.querySelector('.disclaimer-content-wrapper');
        this.modalLanguageToggle = document.getElementById('modalLanguageToggle');
        this.modalLanguageDropdown = document.getElementById('modalLanguageDropdown');
        this.modalCurrentLang = document.getElementById('modalCurrentLang');
        this.storageKey = 'doctor_ai_disclaimer_accepted';
        this.hasScrolledToBottom = false;
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
            this.acceptBtn.addEventListener('click', () => {
                this.acceptDisclaimer();
            });
            
            // Add touch event for mobile devices
            this.acceptBtn.addEventListener('touchend', (e) => {
                e.preventDefault();
                this.acceptDisclaimer();
            });
        }

        // Scroll event listener for content wrapper
        if (this.contentWrapper) {
            this.contentWrapper.addEventListener('scroll', () => {
                this.checkScrollPosition();
            });
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
            
            // Reset scroll state and disable button
            this.hasScrolledToBottom = false;
            this.updateButtonState();
            
            // Sync modal language with current page language
            this.syncModalLanguage();
            
            // Add animation class
            setTimeout(() => {
                this.modal.classList.add('show');
            }, 10);

            // Focus on accept button for accessibility (but it will be disabled)
            setTimeout(() => {
                if (this.acceptBtn) {
                    this.acceptBtn.focus();
                }
            }, 300);
        }
    }

    hideModal() {
        if (this.modal) {
            this.modal.classList.remove('show');
            
            setTimeout(() => {
                this.modal.style.display = 'none';
                document.body.style.overflow = ''; // Restore scrolling
            }, 300);
        }
    }

    acceptDisclaimer() {
        // Only allow acceptance if user has scrolled to bottom
        if (!this.hasScrolledToBottom) {
            return;
        }
        
        try {
            // Hide modal with animation
            this.hideModal();
            
            // Optional: Track acceptance for analytics
            this.trackAcceptance();
            
        } catch (error) {
            console.warn('Error in disclaimer acceptance:', error);
            // Still hide modal even if error occurs
            this.hideModal();
        }
    }

    checkScrollPosition() {
        if (!this.contentWrapper) return;
        
        const scrollTop = this.contentWrapper.scrollTop;
        const scrollHeight = this.contentWrapper.scrollHeight;
        const clientHeight = this.contentWrapper.clientHeight;
        
        // Check if user has scrolled to within 10px of the bottom
        const isAtBottom = scrollTop + clientHeight >= scrollHeight - 10;
        
        if (isAtBottom && !this.hasScrolledToBottom) {
            this.hasScrolledToBottom = true;
            this.updateButtonState();
        } else if (!isAtBottom && this.hasScrolledToBottom) {
            this.hasScrolledToBottom = false;
            this.updateButtonState();
        }
    }

    updateButtonState() {
        if (!this.acceptBtn) return;
        
        if (this.hasScrolledToBottom) {
            this.acceptBtn.classList.add('enabled');
            this.acceptBtn.removeAttribute('disabled');
        } else {
            this.acceptBtn.classList.remove('enabled');
            this.acceptBtn.setAttribute('disabled', 'true');
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
