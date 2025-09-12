// Symptom input with auto-complete and tag functionality
class SymptomInput {
    constructor() {
        this.symptoms = [];
        this.commonSymptoms = [
            // 常見症狀 - 中文
            '頭痛', '發燒', '咳嗽', '喉嚨痛', '流鼻水', '鼻塞', '打噴嚏',
            '疲勞', '乏力', '頭暈', '噁心', '嘔吐', '腹痛', '腹瀉', '便秘',
            '胸痛', '呼吸困難', '心悸', '失眠', '焦慮', '憂鬱', '食慾不振',
            '體重減輕', '體重增加', '關節痛', '肌肉痛', '背痛', '腰痛',
            '皮疹', '皮膚癢', '眼睛痛', '視力模糊', '耳痛', '聽力下降',
            '牙痛', '口乾', '尿頻', '尿痛', '血尿', '月經不規律', '經痛',
            '手腳麻木', '抽筋', '盜汗', '畏寒', '發抖', '腫脹', '淋巴結腫大',
            
            // English symptoms
            'headache', 'fever', 'cough', 'sore throat', 'runny nose', 'nasal congestion', 'sneezing',
            'fatigue', 'weakness', 'dizziness', 'nausea', 'vomiting', 'abdominal pain', 'diarrhea', 'constipation',
            'chest pain', 'shortness of breath', 'palpitations', 'insomnia', 'anxiety', 'depression', 'loss of appetite',
            'weight loss', 'weight gain', 'joint pain', 'muscle pain', 'back pain', 'lower back pain',
            'rash', 'itchy skin', 'eye pain', 'blurred vision', 'ear pain', 'hearing loss',
            'toothache', 'dry mouth', 'frequent urination', 'painful urination', 'blood in urine', 'irregular periods', 'menstrual pain',
            'numbness', 'cramps', 'night sweats', 'chills', 'shivering', 'swelling', 'swollen lymph nodes'
        ];
        
        this.init();
    }
    
    init() {
        this.input = document.getElementById('symptomInput');
        this.tagsContainer = document.getElementById('symptomTags');
        this.suggestionsContainer = document.getElementById('symptomSuggestions');
        this.hiddenTextarea = document.getElementById('symptoms');
        
        if (!this.input || !this.tagsContainer || !this.suggestionsContainer) {
            console.error('Symptom input elements not found');
            return;
        }
        
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        // Input events
        this.input.addEventListener('input', (e) => this.handleInput(e));
        this.input.addEventListener('keydown', (e) => this.handleKeydown(e));
        this.input.addEventListener('focus', () => this.showSuggestions());
        this.input.addEventListener('blur', (e) => {
            // Delay hiding suggestions to allow clicking on them
            setTimeout(() => this.hideSuggestions(), 150);
        });
        
        // Click outside to hide suggestions
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.symptom-input-wrapper')) {
                this.hideSuggestions();
            }
        });
    }
    
    handleInput(e) {
        const value = e.target.value;
        
        // Check if user typed a separator at the end
        if (value.endsWith(',') || value.endsWith(';')) {
            this.processInput();
            return;
        }
        
        const query = value.trim();
        
        if (query === '') {
            this.showAllSuggestions();
        } else {
            this.showFilteredSuggestions(query);
        }
    }
    
    handleKeydown(e) {
        // Handle multiple separators: Enter, Space, Comma, Semicolon, Tab
        if (e.key === 'Enter' || e.key === ' ' || e.key === ',' || e.key === ';' || e.key === 'Tab') {
            e.preventDefault();
            this.processInput();
        } else if (e.key === 'Escape') {
            this.hideSuggestions();
        } else if (e.key === 'Backspace' && this.input.value === '' && this.symptoms.length > 0) {
            // Remove last symptom when backspace is pressed on empty input
            this.removeSymptom(this.symptoms.length - 1);
        }
    }
    
    processInput() {
        const value = this.input.value.trim();
        if (value) {
            // Split by multiple delimiters and process each part
            const parts = value.split(/[,;\s]+/).filter(part => part.trim().length > 0);
            
            parts.forEach(part => {
                const trimmedPart = part.trim();
                if (trimmedPart) {
                    this.addSymptom(trimmedPart);
                }
            });
            
            this.input.value = '';
            this.hideSuggestions();
        }
    }
    
    showAllSuggestions() {
        const suggestions = this.commonSymptoms.slice(0, 10); // Show first 10
        this.renderSuggestions(suggestions);
    }
    
    showFilteredSuggestions(query) {
        const filtered = this.commonSymptoms.filter(symptom => 
            symptom.toLowerCase().includes(query.toLowerCase()) &&
            !this.symptoms.includes(symptom)
        ).slice(0, 8);
        
        this.renderSuggestions(filtered);
    }
    
    renderSuggestions(suggestions) {
        this.suggestionsContainer.innerHTML = '';
        
        if (suggestions.length === 0) {
            this.hideSuggestions();
            return;
        }
        
        suggestions.forEach(suggestion => {
            const div = document.createElement('div');
            div.className = 'suggestion-item';
            div.textContent = suggestion;
            div.addEventListener('click', () => {
                this.addSymptom(suggestion);
                this.input.value = '';
                this.hideSuggestions();
            });
            this.suggestionsContainer.appendChild(div);
        });
        
        this.showSuggestions();
    }
    
    showSuggestions() {
        this.suggestionsContainer.style.display = 'block';
    }
    
    hideSuggestions() {
        this.suggestionsContainer.style.display = 'none';
    }
    
    addSymptom(symptom) {
        if (!symptom || this.symptoms.includes(symptom)) {
            return;
        }
        
        this.symptoms.push(symptom);
        this.renderTags();
        this.updateHiddenInput();
        this.validateSymptomCount();
    }
    
    removeSymptom(index) {
        if (index >= 0 && index < this.symptoms.length) {
            this.symptoms.splice(index, 1);
            this.renderTags();
            this.updateHiddenInput();
            this.validateSymptomCount();
        }
    }
    
    renderTags() {
        this.tagsContainer.innerHTML = '';
        
        this.symptoms.forEach((symptom, index) => {
            const tag = document.createElement('div');
            tag.className = 'symptom-tag';
            tag.innerHTML = `
                <span class="symptom-text">${symptom}</span>
                <button type="button" class="remove-symptom" data-index="${index}">
                    <i class="fas fa-times"></i>
                </button>
            `;
            
            const removeBtn = tag.querySelector('.remove-symptom');
            removeBtn.addEventListener('click', () => this.removeSymptom(index));
            
            this.tagsContainer.appendChild(tag);
        });
    }
    
    updateHiddenInput() {
        this.hiddenTextarea.value = this.symptoms.join('、');
    }
    
    validateSymptomCount() {
        const container = document.querySelector('.symptom-input-container');
        const hint = container.parentNode.querySelector('.input-hint');
        
        if (this.symptoms.length < 3) {
            container.classList.add('insufficient-symptoms');
            if (hint) {
                hint.style.color = '#dc3545';
                hint.innerHTML = `<i class="fas fa-exclamation-triangle"></i> 還需要 ${3 - this.symptoms.length} 個症狀`;
            }
        } else {
            container.classList.remove('insufficient-symptoms');
            if (hint) {
                hint.style.color = '#28a745';
                hint.innerHTML = `<i class="fas fa-check-circle"></i> 已添加 ${this.symptoms.length} 個症狀`;
            }
        }
    }
    
    // Public method to get symptoms
    getSymptoms() {
        return this.symptoms;
    }
    
    // Public method to clear all symptoms
    clearSymptoms() {
        this.symptoms = [];
        this.renderTags();
        this.updateHiddenInput();
        this.validateSymptomCount();
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.symptomInput = new SymptomInput();
});
