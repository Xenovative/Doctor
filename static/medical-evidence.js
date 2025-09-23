/**
 * Dynamic Medical Evidence System
 * Fetches real medical evidence from PubMed and other medical databases
 */

class MedicalEvidenceSystem {
    constructor() {
        this.cache = new Map(); // Cache for API responses
        this.loadingStates = new Map(); // Track loading states
    }

    async fetchEvidenceForSymptoms(symptoms, diagnosis = '') {
        try {
            console.log('fetchEvidenceForSymptoms called with:', symptoms, diagnosis);
            
            // Create cache key
            const cacheKey = JSON.stringify({ symptoms, diagnosis });
            console.log('Cache key:', cacheKey);
            
            // Check cache first
            if (this.cache.has(cacheKey)) {
                console.log('Found in cache');
                return this.cache.get(cacheKey);
            }

            // Check if already loading
            if (this.loadingStates.has(cacheKey)) {
                console.log('Already loading, waiting...');
                return await this.loadingStates.get(cacheKey);
            }

            // Create loading promise
            console.log('Making new API call');
            const loadingPromise = this.fetchFromAPI(symptoms, diagnosis);
            this.loadingStates.set(cacheKey, loadingPromise);

            const result = await loadingPromise;
            console.log('API result:', result);
            
            // Cache the result
            this.cache.set(cacheKey, result);
            this.loadingStates.delete(cacheKey);

            return result;

        } catch (error) {
            console.error('Error fetching medical evidence:', error);
            return { success: false, evidence: [], error: error.message };
        }
    }

    async fetchFromAPI(symptoms, diagnosis) {
        try {
            console.log('fetchFromAPI called with:', symptoms, diagnosis);
            
            const requestBody = {
                symptoms: symptoms,
                diagnosis: diagnosis
            };
            console.log('Request body:', requestBody);
            
            const response = await fetch('/api/medical-evidence', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestBody)
            });

            console.log('Response status:', response.status);
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error('API error response:', errorText);
                throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
            }

            const data = await response.json();
            console.log('API response data:', data);
            return data;

        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }

    async generateEvidenceHTML(symptoms, diagnosis = '') {
        console.log('generateEvidenceHTML called with:', symptoms, diagnosis);
        try {
            // Show loading state
            const loadingHTML = this.generateLoadingHTML();
            
            // Fetch evidence from API
            const result = await this.fetchEvidenceForSymptoms(symptoms, diagnosis);
            console.log('fetchEvidenceForSymptoms returned:', result);
            
            if (!result) {
                console.log('Result is null/undefined');
                return '';
            }
            
            if (!result.success) {
                console.log('Result success is false:', result.success);
                return '';
            }
            
            if (!result.evidence) {
                console.log('Result evidence is null/undefined:', result.evidence);
                return '';
            }
            
            if (result.evidence.length === 0) {
                console.log('Result evidence array is empty, length:', result.evidence.length);
                return '';
            }

            console.log('Generating HTML from evidence data:', result.evidence);
            return this.generateEvidenceHTMLFromData(result.evidence);

        } catch (error) {
            console.error('Error generating evidence HTML:', error);
            return ''; // Return empty on error
        }
    }

    generateLoadingHTML() {
        return `
            <div class="medical-evidence-container" id="medicalEvidenceContainer">
                <div class="evidence-header" onclick="toggleMedicalEvidence()">
                    <div class="evidence-header-content">
                        <h4 data-translate="medical_evidence_title">📚 醫學文獻參考</h4>
                    </div>
                    <i class="fas fa-chevron-down evidence-toggle-icon" id="evidenceToggleIcon"></i>
                </div>
                <div class="evidence-content" id="evidenceContent">
                    <div class="evidence-loading">
                        <i class="fas fa-spinner fa-spin"></i>
                        <span>正在搜尋相關醫學文獻...</span>
                    </div>
                </div>
            </div>
        `;
    }

    generateEvidenceHTMLFromData(evidence) {
        let evidenceHTML = `
            <div class="medical-evidence-container" id="medicalEvidenceContainer">
                <div class="evidence-header" onclick="toggleMedicalEvidence()">
                    <div class="evidence-header-content">
                        <h4 data-translate="medical_evidence_title">📚 醫學文獻參考</h4>
                    </div>
                    <i class="fas fa-chevron-down evidence-toggle-icon" id="evidenceToggleIcon"></i>
                </div>
                <div class="evidence-content" id="evidenceContent">
                    <div class="evidence-introduction">
                        <span data-translate="evidence_introduction">根據分析結果，您的症狀與以下醫學研究參考相關：</span>
                    </div>
                    
                    <!-- Evidence Tabs -->
                    <div class="evidence-tabs">
                        <button class="evidence-tab active" onclick="switchEvidenceTab('pubmed')" id="pubmedTab">
                            <i class="fas fa-microscope"></i> PubMed 研究
                        </button>
                        <button class="evidence-tab" onclick="switchEvidenceTab('chp')" id="chpTab">
                            <i class="fas fa-hospital"></i> 香港衛生署
                        </button>
                    </div>
                    
                    <!-- PubMed Content -->
                    <div class="evidence-tab-content active" id="pubmedContent">
        `;

        evidence.forEach((entry, index) => {
            const pubmedLink = entry.url ? `<a href="${entry.url}" target="_blank" class="pubmed-link"><i class="fas fa-external-link-alt"></i> PubMed</a>` : '';
            
            evidenceHTML += `
                <div class="journal-entry ${entry.type || ''}">
                    <div class="journal-title">${this.escapeHtml(entry.title)}</div>
                    <div class="journal-source">
                        <i class="fas fa-journal-whills"></i>
                        <span data-translate="journal_source">期刊來源</span>: ${this.escapeHtml(entry.source)}
                        ${pubmedLink}
                    </div>
                    <div class="journal-excerpt">"${this.escapeHtml(entry.excerpt)}"</div>
                    <div class="clinical-relevance">
                        <strong data-translate="clinical_relevance">臨床相關性</strong>: ${this.escapeHtml(entry.relevance)}
                    </div>
                </div>
            `;
        });

        evidenceHTML += `
                    </div>
                    
                    <!-- CHP Content -->
                    <div class="evidence-tab-content" id="chpContent">
                        <div class="chp-loading" id="chpLoading">
                            <i class="fas fa-spinner fa-spin"></i>
                            <span>正在載入香港衛生署健康資訊...</span>
                        </div>
                        <div class="chp-content-area" id="chpContentArea" style="display: none;">
                            <!-- CHP content will be loaded here -->
                        </div>
                    </div>
                    
                    <div class="evidence-disclaimer">
                        <i class="fas fa-info-circle"></i>
                        <small>醫學文獻來源於 PubMed 等權威醫學資料庫及香港衛生署，僅供參考，不構成醫療建議。</small>
                    </div>
                </div>
            </div>
        `;

        return evidenceHTML;
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    async fetchCHPData(symptoms) {
        try {
            console.log('Fetching CHP data for symptoms:', symptoms);
            
            // For now, we'll generate relevant CHP content based on symptoms
            // In the future, this could be enhanced to scrape actual CHP pages
            const chpData = this.generateCHPContent(symptoms);
            
            return chpData;
        } catch (error) {
            console.error('Error fetching CHP data:', error);
            return [];
        }
    }

    generateCHPContent(symptoms) {
        // Map common symptoms to relevant CHP health topics
        const chpHealthTopics = {
            '發燒': {
                title: '發燒的處理',
                url: 'https://www.chp.gov.hk/tc/resources/e_health_topics/pdfwav/fever.html',
                content: '發燒是身體對感染或疾病的自然反應。成人體溫超過38°C (100.4°F)即屬發燒。',
                advice: '多休息、多喝水、穿著輕便衣物。如持續高燒或出現其他嚴重症狀，應盡快求醫。'
            },
            '咳嗽': {
                title: '咳嗽的認識與處理',
                url: 'https://www.chp.gov.hk/tc/resources/e_health_topics/pdfwav/cough.html',
                content: '咳嗽是呼吸道的保護性反射動作，有助清除呼吸道的異物和分泌物。',
                advice: '保持室內空氣流通、多喝溫水、避免刺激性食物。持續咳嗽超過兩週應求醫檢查。'
            },
            '頭痛': {
                title: '頭痛的預防與處理',
                url: 'https://www.chp.gov.hk/tc/resources/e_health_topics/headache.html',
                content: '頭痛是常見症狀，大部分屬於原發性頭痛，如緊張性頭痛或偏頭痛。',
                advice: '保持規律作息、適度運動、減少壓力。如頭痛劇烈或伴隨其他症狀，應立即求醫。'
            },
            '腹痛': {
                title: '腹痛的常見原因',
                url: 'https://www.chp.gov.hk/tc/resources/e_health_topics/abdominal_pain.html',
                content: '腹痛可能由多種原因引起，包括消化不良、腸胃炎、闌尾炎等。',
                advice: '注意飲食衛生、避免暴飲暴食。如腹痛劇烈或持續，應盡快求醫診治。'
            },
            '糖尿病': {
                title: '糖尿病的預防與管理',
                url: 'https://www.chp.gov.hk/tc/resources/e_health_topics/diabetes.html',
                content: '糖尿病是一種慢性疾病，患者的血糖水平持續偏高。主要症狀包括多飲、多尿、疲倦等。',
                advice: '定期監測血糖、遵從醫生指示服藥、保持健康飲食和適量運動。'
            },
            '高血壓': {
                title: '高血壓的預防與控制',
                url: 'https://www.chp.gov.hk/tc/resources/e_health_topics/hypertension.html',
                content: '高血壓是心血管疾病的主要風險因素，通常沒有明顯症狀，被稱為「隱形殺手」。',
                advice: '定期量血壓、減少鹽分攝取、保持健康體重、戒煙限酒、適量運動。'
            }
        };

        const relevantTopics = [];
        
        // Check if symptoms match any CHP topics
        for (const symptom of symptoms) {
            for (const [key, topic] of Object.entries(chpHealthTopics)) {
                if (symptom.includes(key) || key.includes(symptom)) {
                    relevantTopics.push(topic);
                }
            }
        }

        // If no specific matches, provide general health advice
        if (relevantTopics.length === 0) {
            relevantTopics.push({
                title: '一般健康建議',
                url: 'https://www.chp.gov.hk/tc/resources/submenu/463/index.html',
                content: '保持身體健康需要均衡飲食、適量運動、充足睡眠和定期健康檢查。',
                advice: '如有任何健康問題或症狀持續，建議諮詢醫護人員的專業意見。'
            });
        }

        return relevantTopics;
    }

}

// Global function to toggle medical evidence
function toggleMedicalEvidence() {
    console.log('toggleMedicalEvidence called');
    
    const container = document.getElementById('medicalEvidenceContainer');
    const content = document.getElementById('evidenceContent');
    const icon = document.getElementById('evidenceToggleIcon');
    
    console.log('Elements found:', {
        container: !!container,
        content: !!content,
        icon: !!icon
    });
    
    if (container && content && icon) {
        const isExpanded = content.classList.contains('expanded');
        console.log('Current state - isExpanded:', isExpanded);
        
        if (isExpanded) {
            content.classList.remove('expanded');
            container.classList.remove('expanded');
            icon.classList.remove('expanded');
            console.log('Collapsed evidence');
        } else {
            content.classList.add('expanded');
            container.classList.add('expanded');
            icon.classList.add('expanded');
            console.log('Expanded evidence');
        }
    } else {
        console.error('Missing elements for toggle:', {
            container: container,
            content: content,
            icon: icon
        });
    }
}

// Global function to switch evidence tabs
function switchEvidenceTab(tabName) {
    console.log('Switching to tab:', tabName);
    
    // Update tab buttons
    const pubmedTab = document.getElementById('pubmedTab');
    const chpTab = document.getElementById('chpTab');
    
    // Update content areas
    const pubmedContent = document.getElementById('pubmedContent');
    const chpContent = document.getElementById('chpContent');
    
    if (tabName === 'pubmed') {
        pubmedTab.classList.add('active');
        chpTab.classList.remove('active');
        pubmedContent.classList.add('active');
        chpContent.classList.remove('active');
    } else if (tabName === 'chp') {
        chpTab.classList.add('active');
        pubmedTab.classList.remove('active');
        chpContent.classList.add('active');
        pubmedContent.classList.remove('active');
        
        // Load CHP content if not already loaded
        loadCHPContent();
    }
}

// Global function to load CHP content
async function loadCHPContent() {
    const chpContentArea = document.getElementById('chpContentArea');
    const chpLoading = document.getElementById('chpLoading');
    
    if (!chpContentArea || !chpLoading) {
        console.error('CHP content elements not found');
        return;
    }
    
    // Check if already loaded
    if (chpContentArea.style.display !== 'none') {
        return;
    }
    
    try {
        // Show loading
        chpLoading.style.display = 'block';
        chpContentArea.style.display = 'none';
        
        // Get symptoms from the current analysis (if available)
        const symptoms = window.currentSymptoms || ['一般健康'];
        
        // Fetch CHP data
        const chpData = await window.medicalEvidenceSystem.fetchCHPData(symptoms);
        
        // Generate CHP HTML
        let chpHTML = '';
        chpData.forEach((topic, index) => {
            chpHTML += `
                <div class="chp-entry">
                    <div class="chp-title">
                        <i class="fas fa-hospital"></i>
                        ${window.medicalEvidenceSystem.escapeHtml(topic.title)}
                    </div>
                    <div class="chp-content">
                        ${window.medicalEvidenceSystem.escapeHtml(topic.content)}
                    </div>
                    <div class="chp-advice">
                        <strong>建議：</strong>
                        ${window.medicalEvidenceSystem.escapeHtml(topic.advice)}
                    </div>
                    <div class="chp-source">
                        <a href="${topic.url}" target="_blank" class="chp-link">
                            <i class="fas fa-external-link-alt"></i> 香港衛生署官方資訊
                        </a>
                    </div>
                </div>
            `;
        });
        
        // Update content
        chpContentArea.innerHTML = chpHTML;
        
        // Hide loading and show content
        chpLoading.style.display = 'none';
        chpContentArea.style.display = 'block';
        
        console.log('CHP content loaded successfully');
        
    } catch (error) {
        console.error('Error loading CHP content:', error);
        chpContentArea.innerHTML = `
            <div class="chp-error">
                <i class="fas fa-exclamation-triangle"></i>
                <span>載入香港衛生署資訊時發生錯誤，請稍後再試。</span>
            </div>
        `;
        chpLoading.style.display = 'none';
        chpContentArea.style.display = 'block';
    }
}

// Helper function to ensure evidence starts collapsed
function ensureEvidenceCollapsed() {
    setTimeout(() => {
        const container = document.getElementById('medicalEvidenceContainer');
        const content = document.getElementById('evidenceContent');
        const icon = document.getElementById('evidenceToggleIcon');
        
        if (container && content && icon) {
            // Ensure it starts collapsed
            content.classList.remove('expanded');
            container.classList.remove('expanded');
            icon.classList.remove('expanded');
            console.log('Ensured evidence starts collapsed');
        }
    }, 100);
}

// Initialize global instance
window.medicalEvidenceSystem = new MedicalEvidenceSystem();
