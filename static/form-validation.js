// Enhanced form validation with better required field indicators
class FormValidator {
    constructor() {
        this.form = document.getElementById('patientForm');
        this.requiredFields = [
            { id: 'age', name: '年齡', type: 'number' },
            { id: 'gender', name: '性別', type: 'select' },
            { id: 'symptoms', name: '症狀', type: 'custom' },
            { id: 'language', name: '偏好語言', type: 'select' },
            { id: 'region', name: '所在地區', type: 'select' },
            { id: 'district', name: '地區', type: 'select' }
        ];
        this.init();
    }
    
    init() {
        if (!this.form) return;
        
        this.setupRealTimeValidation();
        this.addValidationMessages();
        this.setupSubmitValidation();
    }
    
    setupRealTimeValidation() {
        this.requiredFields.forEach(field => {
            const element = document.getElementById(field.id);
            if (!element) return;
            
            if (field.type === 'custom' && field.id === 'symptoms') {
                // Handle symptom validation separately
                return;
            }
            
            element.addEventListener('blur', () => this.validateField(field));
            element.addEventListener('change', () => this.validateField(field));
            
            if (field.type === 'number') {
                element.addEventListener('input', () => this.validateField(field));
            }
        });
    }
    
    validateField(field) {
        const element = document.getElementById(field.id);
        const formGroup = element.closest('.form-group');
        
        if (!element || !formGroup) return;
        
        let isValid = false;
        let message = '';
        
        switch (field.type) {
            case 'number':
                const value = parseInt(element.value);
                isValid = value >= 1 && value <= 120;
                message = isValid ? '' : '請輸入有效年齡 (1-120歲)';
                break;
                
            case 'select':
                isValid = element.value !== '';
                message = isValid ? '' : `請選擇${field.name}`;
                break;
                
            case 'custom':
                if (field.id === 'symptoms') {
                    const symptomCount = window.symptomInput ? window.symptomInput.getSymptoms().length : 0;
                    isValid = symptomCount >= 3;
                    message = isValid ? `已添加 ${symptomCount} 個症狀` : `還需要 ${3 - symptomCount} 個症狀`;
                }
                break;
        }
        
        this.updateFieldValidation(formGroup, isValid, message);
        return isValid;
    }
    
    updateFieldValidation(formGroup, isValid, message) {
        // Remove existing validation classes and messages
        formGroup.classList.remove('has-error', 'has-success');
        const existingMessage = formGroup.querySelector('.validation-message');
        if (existingMessage) {
            existingMessage.remove();
        }
        
        // Add appropriate class and message
        if (message) {
            formGroup.classList.add(isValid ? 'has-success' : 'has-error');
            
            const messageElement = document.createElement('div');
            messageElement.className = `validation-message ${isValid ? 'success' : ''}`;
            messageElement.innerHTML = `<i class="fas fa-${isValid ? 'check-circle' : 'exclamation-triangle'}"></i>${message}`;
            
            // Insert after the input/select element
            const input = formGroup.querySelector('input, select, .symptom-input-container');
            if (input) {
                input.parentNode.insertBefore(messageElement, input.nextSibling);
            }
        }
    }
    
    addValidationMessages() {
        // Add helpful placeholder text and validation hints
        const ageInput = document.getElementById('age');
        if (ageInput) {
            ageInput.placeholder = '例如：25';
        }
        
        const genderSelect = document.getElementById('gender');
        if (genderSelect && genderSelect.value === '') {
            genderSelect.style.color = '#6c757d';
        }
        
        // Update select color when option is chosen
        document.querySelectorAll('select[required]').forEach(select => {
            select.addEventListener('change', function() {
                this.style.color = this.value ? '#333' : '#6c757d';
            });
        });
    }
    
    setupSubmitValidation() {
        this.form.addEventListener('submit', (e) => {
            if (!this.validateAllFields()) {
                e.preventDefault();
                this.showValidationSummary();
            }
        });
    }
    
    validateAllFields() {
        let allValid = true;
        const errors = [];
        
        this.requiredFields.forEach(field => {
            const isValid = this.validateField(field);
            if (!isValid) {
                allValid = false;
                errors.push(field.name);
            }
        });
        
        // Special validation for district (only required if region is selected)
        const region = document.getElementById('region');
        const district = document.getElementById('district');
        if (region && region.value && district && !district.value) {
            allValid = false;
            errors.push('地區');
            this.updateFieldValidation(district.closest('.form-group'), false, '請選擇地區');
        }
        
        return allValid;
    }
    
    showValidationSummary() {
        // Remove existing summary
        const existingSummary = document.querySelector('.validation-summary');
        if (existingSummary) {
            existingSummary.remove();
        }
        
        // Create validation summary
        const summary = document.createElement('div');
        summary.className = 'validation-summary alert alert-danger';
        summary.innerHTML = `
            <div class="d-flex align-items-center">
                <i class="fas fa-exclamation-triangle me-2"></i>
                <strong>請完成以下必填項目：</strong>
            </div>
            <div class="mt-2">
                <small>請檢查標有紅色星號 (*) 的必填欄位</small>
            </div>
        `;
        
        // Insert before form
        this.form.parentNode.insertBefore(summary, this.form);
        
        // Scroll to summary
        summary.scrollIntoView({ behavior: 'smooth', block: 'center' });
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (summary.parentNode) {
                summary.remove();
            }
        }, 5000);
    }
    
    // Public method to check if form is valid
    isFormValid() {
        return this.validateAllFields();
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.formValidator = new FormValidator();
    
    // Add visual feedback for required fields on page load
    setTimeout(() => {
        const requiredInputs = document.querySelectorAll('input[required], select[required]');
        requiredInputs.forEach(input => {
            const formGroup = input.closest('.form-group');
            if (formGroup && !input.value) {
                formGroup.classList.add('field-required');
            }
        });
    }, 500);
});
