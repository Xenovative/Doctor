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
        const languageOptions = document.querySelectorAll('.language-option');

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

            // Prevent dropdown from closing when clicking inside
            languageDropdown.addEventListener('click', (e) => {
                e.stopPropagation();
            });
        }

        // Language option selection
        languageOptions.forEach(option => {
            option.addEventListener('click', async (e) => {
                const selectedLang = option.dataset.lang;
                await this.switchLanguage(selectedLang);
                languageDropdown.classList.remove('show');
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
                
                console.log(`Language switched to: ${lang}`);
            }
        } catch (error) {
            console.error('Failed to switch language:', error);
        }
    }

    updateLanguageDisplay() {
        const currentLangElement = document.getElementById('currentLang');
        const languageOptions = document.querySelectorAll('.language-option');
        
        if (currentLangElement) {
            const langMap = {
                'zh-TW': '繁',
                'zh-CN': '简',
                'en': 'EN'
            };
            currentLangElement.textContent = langMap[this.currentLang] || '繁';
        }

        // Update active state
        languageOptions.forEach(option => {
            option.classList.toggle('active', option.dataset.lang === this.currentLang);
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
}

// Initialize language manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.languageManager = new LanguageManager();
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = LanguageManager;
}
