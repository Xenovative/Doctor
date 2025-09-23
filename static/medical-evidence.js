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
                    <div class="evidence-disclaimer">
                        <i class="fas fa-info-circle"></i>
                        <small>醫學文獻來源於 PubMed 等權威醫學資料庫，僅供參考，不構成醫療建議。</small>
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
