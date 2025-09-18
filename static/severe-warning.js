/**
 * Severe Symptoms Warning System
 * Handles detection and display of severe medical condition warnings
 */

class SevereWarningSystem {
    constructor() {
        this.modal = document.getElementById('severeWarningModal');
        this.closeBtn = document.getElementById('closeSevereModal');
        this.callEmergencyBtn = document.getElementById('callEmergency');
        this.cancelBtn = document.getElementById('cancelDiagnosis');
        this.proceedBtn = document.getElementById('proceedAnyway');
        
        this.pendingFormData = null;
        this.onProceedCallback = null;
        
        this.initEventListeners();
    }
    
    initEventListeners() {
        // Close modal events
        this.closeBtn.addEventListener('click', () => this.closeModal());
        this.cancelBtn.addEventListener('click', () => this.closeModal());
        
        // Emergency call button
        this.callEmergencyBtn.addEventListener('click', () => this.callEmergency());
        
        // Proceed anyway button
        this.proceedBtn.addEventListener('click', () => this.proceedWithDiagnosis());
        
        // Close modal when clicking outside
        window.addEventListener('click', (event) => {
            if (event.target === this.modal) {
                this.closeModal();
            }
        });
        
        // Close modal with Escape key
        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape' && this.modal.style.display === 'block') {
                this.closeModal();
            }
        });
    }
    
    async checkSevereSymptoms(formData) {
        try {
            const response = await fetch('/check_severe_symptoms', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    symptoms: formData.symptoms,
                    chronicConditions: formData.chronicConditions
                })
            });
            
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            
            const result = await response.json();
            return result;
            
        } catch (error) {
            console.error('Error checking severe symptoms:', error);
            return { is_severe: false, warning: null };
        }
    }
    
    showWarning(warningData, formData, onProceedCallback) {
        this.pendingFormData = formData;
        this.onProceedCallback = onProceedCallback;
        
        // Update modal content
        this.updateModalContent(warningData);
        
        // Show modal
        this.modal.style.display = 'block';
        document.body.style.overflow = 'hidden';
        
        // Focus on the modal for accessibility
        this.modal.focus();
    }
    
    updateModalContent(warningData) {
        const warning = warningData.warning;
        
        // Update title
        document.getElementById('severeWarningTitle').textContent = warning.title;
        
        // Update message
        document.getElementById('severeWarningMessage').textContent = warning.message;
        
        // Update recommendations
        const recommendationsList = document.getElementById('severeRecommendations');
        recommendationsList.innerHTML = '';
        warning.recommendations.forEach(rec => {
            const li = document.createElement('li');
            li.textContent = rec;
            recommendationsList.appendChild(li);
        });
        
        // Update disclaimer
        document.getElementById('severeDisclaimer').textContent = warning.disclaimer;
        
        // Update severe items if any
        this.updateSevereItems(warning.severe_items);
    }
    
    updateSevereItems(severeItems) {
        const container = document.getElementById('severeItemsContainer');
        const symptomsDiv = document.getElementById('severeSymptoms');
        const conditionsDiv = document.getElementById('severeConditions');
        
        // Clear previous content
        symptomsDiv.innerHTML = '';
        conditionsDiv.innerHTML = '';
        
        let hasItems = false;
        
        // Add severe symptoms
        if (severeItems.symptoms && severeItems.symptoms.length > 0) {
            hasItems = true;
            const symptomsTitle = document.createElement('h5');
            symptomsTitle.textContent = '嚴重症狀：';
            symptomsDiv.appendChild(symptomsTitle);
            
            const symptomsList = document.createElement('ul');
            severeItems.symptoms.forEach(symptom => {
                const li = document.createElement('li');
                li.textContent = symptom;
                symptomsList.appendChild(li);
            });
            symptomsDiv.appendChild(symptomsList);
        }
        
        // Add severe conditions
        if (severeItems.conditions && severeItems.conditions.length > 0) {
            hasItems = true;
            const conditionsTitle = document.createElement('h5');
            conditionsTitle.textContent = '嚴重病史：';
            conditionsDiv.appendChild(conditionsTitle);
            
            const conditionsList = document.createElement('ul');
            severeItems.conditions.forEach(condition => {
                const li = document.createElement('li');
                li.textContent = condition;
                conditionsList.appendChild(li);
            });
            conditionsDiv.appendChild(conditionsList);
        }
        
        // Show/hide the container based on whether there are items
        container.style.display = hasItems ? 'block' : 'none';
    }
    
    closeModal() {
        this.modal.style.display = 'none';
        document.body.style.overflow = 'auto';
        
        // Clear pending data
        this.pendingFormData = null;
        this.onProceedCallback = null;
    }
    
    callEmergency() {
        // Try to initiate emergency call
        if (navigator.userAgent.match(/iPhone|iPad|iPod|Android/i)) {
            // On mobile devices, try to open phone dialer
            window.location.href = 'tel:999';
        } else {
            // On desktop, show instructions
            alert('請使用您的電話撥打 999 緊急服務熱線');
        }
        
        // Log emergency action
        console.log('Emergency call initiated by user');
        
        // Keep modal open so user can still see the warning
    }
    
    proceedWithDiagnosis() {
        if (this.pendingFormData) {
            // Log that user proceeded despite warning
            console.log('User proceeded with diagnosis despite severe symptoms warning');
            
            // Close modal
            this.closeModal();
            
            // Execute the original diagnosis request using the global function
            if (window.proceedWithDiagnosis) {
                window.proceedWithDiagnosis(this.pendingFormData);
            } else if (this.onProceedCallback) {
                // Fallback to callback if global function not available
                this.onProceedCallback(this.pendingFormData);
            }
        }
    }
    
    // Static method to check if symptoms/conditions contain severe items
    static containsSevereItems(symptoms, conditions) {
        // This is a basic client-side check - the server does the comprehensive check
        const severeKeywords = [
            '胸痛', '呼吸困難', '中風', '昏迷', '大出血', '心臟病發作', 
            '無法呼吸', '劇烈頭痛', '嘔血', '自殺', '癌症', '心臟病'
        ];
        
        const text = (symptoms + ' ' + conditions).toLowerCase();
        return severeKeywords.some(keyword => text.includes(keyword.toLowerCase()));
    }
}

// Initialize the severe warning system when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.severeWarningSystem = new SevereWarningSystem();
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SevereWarningSystem;
}
