/**
 * AI Disclaimer Modal Handler
 * Shows disclaimer modal on first visit and manages user acceptance
 */

class AIDisclaimerModal {
    constructor() {
        this.modal = document.getElementById('aiDisclaimerModal');
        this.acceptBtn = document.getElementById('acceptDisclaimer');
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
        // Accept button click
        if (this.acceptBtn) {
            this.acceptBtn.addEventListener('click', () => {
                this.acceptDisclaimer();
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
            
            // Add animation class
            setTimeout(() => {
                this.modal.classList.add('show');
            }, 10);

            // Focus on accept button for accessibility
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
