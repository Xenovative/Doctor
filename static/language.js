/**
 * Language switching functionality for AI Doctor Matching System
 */

class LanguageManager {
    constructor() {
        this.currentLang = 'zh-TW';
        this.translations = {};
        this.init();
    }

    async init() {
        // Get current language from server or localStorage
        this.currentLang = localStorage.getItem('preferred_language') || 'zh-TW';
        
        // Load translations
        await this.loadTranslations(this.currentLang);
        
        // Setup event listeners
        this.setupEventListeners();
        
        // Update UI
        this.updateLanguageDisplay();
        this.translatePage();
    }

    async loadTranslations(lang) {
        try {
            const response = await fetch(`/api/translations/${lang}`);
            this.translations = await response.json();
        } catch (error) {
            console.error('Failed to load translations:', error);
            // Fallback to default translations
            this.translations = {};
        }
    }

    setupEventListeners() {
        const languageToggle = document.getElementById('languageToggle');
        const languageDropdown = document.getElementById('languageDropdown');
        const languageToggleMobile = document.getElementById('languageToggleMobile');
        const languageDropdownMobile = document.getElementById('languageDropdownMobile');
        const languageOptions = document.querySelectorAll('.language-option');

        // Desktop language toggle
        if (languageToggle && languageDropdown) {
            // Toggle dropdown
            languageToggle.addEventListener('click', (e) => {
                e.stopPropagation();
                languageDropdown.classList.toggle('show');
            });

            // Close dropdown when clicking outside
            document.addEventListener('click', () => {
                languageDropdown.classList.remove('show');
            });
        }

        // Mobile language toggle
        if (languageToggleMobile && languageDropdownMobile) {
            // Toggle dropdown
            languageToggleMobile.addEventListener('click', (e) => {
                e.stopPropagation();
                languageDropdownMobile.classList.toggle('show');
            });

            // Close dropdown when clicking outside
            document.addEventListener('click', () => {
                languageDropdownMobile.classList.remove('show');
            });
        }

        // Language option selection (works for both desktop and mobile)
        languageOptions.forEach(option => {
            option.addEventListener('click', (e) => {
                const selectedLang = option.getAttribute('data-lang');
                this.switchLanguage(selectedLang);
                
                // Close both dropdowns
                if (languageDropdown) languageDropdown.classList.remove('show');
                if (languageDropdownMobile) languageDropdownMobile.classList.remove('show');
            });
        });
    }

    async switchLanguage(lang) {
        try {
            // Update server session
            const response = await fetch(`/set_language/${lang}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            if (response.ok) {
                this.currentLang = lang;
                localStorage.setItem('preferred_language', lang);
                
                // Load new translations
                await this.loadTranslations(lang);
                
                // Update UI
                this.updateLanguageDisplay();
                this.translatePage();
                
                // Update form placeholders and options
                this.updateFormElements();
                
                // Update diagnosis card content if available
                this.updateDiagnosisContent();
                
                console.log(`Language switched to: ${lang}`);
            }
        } catch (error) {
            console.error('Failed to switch language:', error);
        }
    }

    updateLanguageDisplay() {
        const currentLangSpan = document.getElementById('currentLang');
        const currentLangMobileSpan = document.getElementById('currentLangMobile');
        
        const langMap = {
            'zh-TW': '繁',
            'zh-CN': '简', 
            'en': 'EN'
        };
        
        const displayText = langMap[this.currentLang] || '繁';
        
        if (currentLangSpan) {
            currentLangSpan.textContent = displayText;
        }
        
        if (currentLangMobileSpan) {
            currentLangMobileSpan.textContent = displayText;
        }
        
        // Update active state for both desktop and mobile dropdowns
        document.querySelectorAll('.language-option').forEach(option => {
            if (option.getAttribute('data-lang') === this.currentLang) {
                option.classList.add('active');
            } else {
                option.classList.remove('active');
            }
        });
    }

    translatePage() {
        function updateTranslations(translations) {
            // Update text content
            document.querySelectorAll('[data-translate]').forEach(element => {
                const key = element.getAttribute('data-translate');
                if (translations[key]) {
                    element.textContent = translations[key];
                }
            });

            // Update placeholders
            document.querySelectorAll('[data-translate-placeholder]').forEach(element => {
                const key = element.getAttribute('data-translate-placeholder');
                if (translations[key]) {
                    element.placeholder = translations[key];
                }
            });

            // Update dynamically created location options
            updateLocationDropdowns(translations);
            
            // Update doctor cards if they exist
            updateDoctorCardLabels(translations);
        }

        // Update doctor card labels dynamically
        function updateDoctorCardLabels(translations) {
            const doctorCards = document.querySelectorAll('.doctor-card');
            doctorCards.forEach(card => {
                // Update recommendation rank
                const matchScore = card.querySelector('.match-score');
                if (matchScore) {
                    const rankMatch = matchScore.textContent.match(/(\d+)/);
                    if (rankMatch) {
                        const rank = rankMatch[1];
                        matchScore.innerHTML = `
                            <i class="fas fa-star"></i>
                            ${translations && translations['recommendation_rank'] || '第'} ${rank} ${translations && translations['recommendation_suffix'] || '推薦'}
                        `;
                    }
                }
                
                // Update WhatsApp hint
                const whatsappHint = card.querySelector('.whatsapp-hint');
                if (whatsappHint) {
                    whatsappHint.innerHTML = `
                        <i class="fab fa-whatsapp"></i>
                        ${translations && translations['click_to_contact'] || '點擊聯絡'}
                    `;
                }
                
                // Update detail labels
                const detailItems = card.querySelectorAll('.detail-item');
                detailItems.forEach(item => {
                    const icon = item.querySelector('i');
                    const strongElement = item.querySelector('strong');
                    
                    if (icon && strongElement) {
                        if (icon.classList.contains('fa-language')) {
                            strongElement.textContent = translations && translations['language_label'] || '語言：';
                        } else if (icon.classList.contains('fa-phone')) {
                            strongElement.textContent = translations && translations['phone_label'] || '電話：';
                        } else if (icon.classList.contains('fa-envelope')) {
                            strongElement.textContent = translations && translations['email_label'] || '電郵：';
                        } else if (icon.classList.contains('fa-map-marker-alt')) {
                            strongElement.textContent = translations && translations['clinic_address_label'] || '診所地址：';
                        } else if (icon.classList.contains('fa-graduation-cap')) {
                            strongElement.textContent = translations && translations['qualifications_label'] || '專業資格：';
                        }
                    }
                });
            });
        }

        // Update location dropdown options with translations
        function updateLocationDropdowns(translations) {
            const districtSelect = document.getElementById('district');
            const areaSelect = document.getElementById('area');
            
            if (districtSelect) {
                Array.from(districtSelect.options).forEach(option => {
                    const key = option.getAttribute('data-translate');
                    if (key && translations[key]) {
                        option.textContent = translations[key];
                    }
                });
            }
            
            if (areaSelect) {
                Array.from(areaSelect.options).forEach(option => {
                    const key = option.getAttribute('data-translate');
                    if (key && translations[key]) {
                        option.textContent = translations[key];
                    }
                });
            }
            
            // Store current translations for use when dropdowns are populated
            window.currentTranslations = translations;
        }

        updateTranslations(this.translations);

        // Update page title
        if (this.translations.app_title) {
            document.title = this.translations.app_title;
        }

        // Update HTML lang attribute
        document.documentElement.lang = this.currentLang;
    }

    updateFormElements() {
        // Update language dropdown options
        const languageSelect = document.getElementById('language');
        if (languageSelect) {
            const options = languageSelect.querySelectorAll('option');
            options.forEach(option => {
                const value = option.value;
                if (value) {
                    const translationKey = this.getLanguageTranslationKey(value);
                    if (this.translations[translationKey]) {
                        option.textContent = this.translations[translationKey];
                    }
                }
            });
            
            // Update placeholder option
            const placeholderOption = languageSelect.querySelector('option[value=""]');
            if (placeholderOption && this.translations.preferred_language) {
                placeholderOption.textContent = `請選擇${this.translations.preferred_language}`;
            }
        }

        // Update region dropdown options
        const regionSelect = document.getElementById('region');
        if (regionSelect) {
            const options = regionSelect.querySelectorAll('option');
            options.forEach(option => {
                const value = option.value;
                if (value) {
                    const translationKey = this.getRegionTranslationKey(value);
                    if (this.translations[translationKey]) {
                        option.textContent = this.translations[translationKey];
                    }
                }
            });
        }

        // Update chronic condition checkboxes
        this.updateChronicConditionLabels();
        
        // Update detailed health info labels
        this.updateDetailedHealthLabels();
    }

    getLanguageTranslationKey(value) {
        const langMap = {
            '廣東話': 'cantonese',
            '英語': 'english', 
            '普通話': 'mandarin',
            '法語': 'french'
        };
        return langMap[value] || value;
    }

    getRegionTranslationKey(value) {
        const regionMap = {
            '香港島': 'hong_kong_island',
            '九龍': 'kowloon',
            '新界': 'new_territories'
        };
        return regionMap[value] || value;
    }

    updateChronicConditionLabels() {
        const conditionMap = {
            '血壓高': 'high_blood_pressure',
            '糖尿病': 'diabetes',
            '胆固醇高': 'high_cholesterol',
            '心臟病': 'heart_disease',
            '中風': 'stroke',
            '哮喘': 'asthma',
            '慢性肺病': 'chronic_lung_disease',
            '乙型肝炎': 'hepatitis_b',
            '其他長期疾病': 'other_conditions'
        };

        Object.entries(conditionMap).forEach(([originalText, translationKey]) => {
            const labels = document.querySelectorAll('.checkbox-item');
            labels.forEach(label => {
                if (label.textContent.trim() === originalText && this.translations[translationKey]) {
                    const textNode = Array.from(label.childNodes).find(node => 
                        node.nodeType === Node.TEXT_NODE && node.textContent.trim() === originalText
                    );
                    if (textNode) {
                        textNode.textContent = this.translations[translationKey];
                    }
                }
            });
        });
    }

    updateDetailedHealthLabels() {
        // Update detailed health section labels
        const detailedLabels = {
            'height': 'height',
            'weight': 'weight', 
            'medications': 'medications',
            'allergies': 'allergies',
            'surgeries': 'surgeries'
        };

        Object.entries(detailedLabels).forEach(([fieldId, translationKey]) => {
            const field = document.getElementById(fieldId);
            if (field && this.translations[translationKey]) {
                const label = document.querySelector(`label[for="${fieldId}"]`);
                if (label) {
                    const textSpan = label.querySelector('span:not(.fas)');
                    if (textSpan) {
                        textSpan.textContent = this.translations[translationKey];
                    }
                }
            }
        });

        // Update checkbox labels in detailed section
        const detailedCheckboxes = {
            'blood-thinner': 'blood_thinner',
            'recent-visit': 'recent_visit',
            'cpap-machine': 'cpap_machine',
            'loose-teeth': 'loose_teeth'
        };

        Object.entries(detailedCheckboxes).forEach(([fieldId, translationKey]) => {
            const checkbox = document.getElementById(fieldId);
            if (checkbox && this.translations[translationKey]) {
                const label = checkbox.closest('.checkbox-item-detailed');
                if (label) {
                    const textNode = Array.from(label.childNodes).find(node => 
                        node.nodeType === Node.TEXT_NODE && node.textContent.trim()
                    );
                    if (textNode) {
                        textNode.textContent = this.translations[translationKey];
                    }
                }
            }
        });
    }

    // Public method to get current language
    getCurrentLanguage() {
        return this.currentLang;
    }

    // Public method to get translation
    getTranslation(key) {
        return this.translations[key] || key;
    }

    updateDiagnosisContent() {
        // Update diagnosis card content if multi-language diagnosis data is available
        if (window.currentDiagnosisData) {
            const diagnosisCard = document.getElementById('diagnosisCard');
            if (diagnosisCard) {
                const currentLang = this.currentLang;
                const currentDiagnosis = window.currentDiagnosisData[currentLang] || window.currentDiagnosisData['zh-TW'] || {};
                
                // Update diagnosis text
                const diagnosisText = diagnosisCard.querySelector('.diagnosis-text');
                if (diagnosisText && currentDiagnosis.diagnosis) {
                    const formattedDiagnosis = currentDiagnosis.diagnosis.replace(/\n/g, '<br>');
                    diagnosisText.innerHTML = formattedDiagnosis;
                }
                
                // Update recommended specialty
                const specialtyDiv = diagnosisCard.querySelector('.recommended-specialty');
                if (specialtyDiv && currentDiagnosis.recommended_specialty) {
                    const specialtyLabel = this.translations['recommended_specialty'] || '推薦專科';
                    specialtyDiv.innerHTML = `${specialtyLabel}：${this.translateSpecialty(currentDiagnosis.recommended_specialty)}`;
                }
                
                // Re-apply translations to the diagnosis card
                diagnosisCard.querySelectorAll('[data-translate]').forEach(element => {
                    const key = element.getAttribute('data-translate');
                    if (this.translations[key]) {
                        element.textContent = this.translations[key];
                    }
                });
            }
        }
    }

    translateSpecialty(specialty) {
        // Specialty translation mapping
        const specialtyTranslations = {
            'zh-TW': {
                'Internal Medicine': '內科',
                'Cardiology': '心臟科',
                'Neurology': '神經科',
                'Gastroenterology': '腸胃科',
                'Pulmonology': '呼吸科',
                'Orthopedics': '骨科',
                'Dermatology': '皮膚科',
                'Ophthalmology': '眼科',
                'Otolaryngology (ENT)': '耳鼻喉科',
                'Obstetrics & Gynecology': '婦產科',
                'Pediatrics': '兒科',
                'Psychiatry': '精神科',
                'Urology': '泌尿科',
                'Emergency Medicine': '急診科'
            },
            'zh-CN': {
                'Internal Medicine': '内科',
                'Cardiology': '心脏科',
                'Neurology': '神经科',
                'Gastroenterology': '肠胃科',
                'Pulmonology': '呼吸科',
                'Orthopedics': '骨科',
                'Dermatology': '皮肤科',
                'Ophthalmology': '眼科',
                'Otolaryngology (ENT)': '耳鼻喉科',
                'Obstetrics & Gynecology': '妇产科',
                'Pediatrics': '儿科',
                'Psychiatry': '精神科',
                'Urology': '泌尿科',
                'Emergency Medicine': '急诊科',
                '內科': '内科',
                '心臟科': '心脏科',
                '神經科': '神经科',
                '腸胃科': '肠胃科',
                '呼吸科': '呼吸科',
                '骨科': '骨科',
                '皮膚科': '皮肤科',
                '眼科': '眼科',
                '耳鼻喉科': '耳鼻喉科',
                '婦產科': '妇产科',
                '兒科': '儿科',
                '精神科': '精神科',
                '泌尿科': '泌尿科',
                '急診科': '急诊科'
            },
            'en': {
                '內科': 'Internal Medicine',
                '心臟科': 'Cardiology',
                '神經科': 'Neurology',
                '腸胃科': 'Gastroenterology',
                '呼吸科': 'Pulmonology',
                '骨科': 'Orthopedics',
                '皮膚科': 'Dermatology',
                '眼科': 'Ophthalmology',
                '耳鼻喉科': 'Otolaryngology (ENT)',
                '婦產科': 'Obstetrics & Gynecology',
                '兒科': 'Pediatrics',
                '精神科': 'Psychiatry',
                '泌尿科': 'Urology',
                '急診科': 'Emergency Medicine',
                '内科': 'Internal Medicine',
                '心脏科': 'Cardiology',
                '神经科': 'Neurology',
                '肠胃科': 'Gastroenterology',
                '妇产科': 'Obstetrics & Gynecology',
                '儿科': 'Pediatrics',
                '皮肤科': 'Dermatology',
                '耳鼻喉科': 'Otolaryngology (ENT)',
                '泌尿科': 'Urology',
                '急诊科': 'Emergency Medicine'
            }
        };

        const translations = specialtyTranslations[this.currentLang];
        return translations && translations[specialty] ? translations[specialty] : specialty;
    }
}

// Initialize language manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.languageManager = new LanguageManager();
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = LanguageManager;
}
