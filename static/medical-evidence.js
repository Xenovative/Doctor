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
            
            // Load actual CHP content from content.json
            const response = await fetch('/static/../assets/content.json');
            const chpContent = await response.json();
            
            // Filter and map relevant CHP content based on symptoms
            const relevantContent = this.mapCHPContent(symptoms, chpContent);
            
            return relevantContent;
        } catch (error) {
            console.error('Error fetching CHP data:', error);
            // Fallback to generated content if loading fails
            return this.generateCHPContent(symptoms);
        }
    }

    generateCHPContent(symptoms) {
        // Map common symptoms to relevant CHP health topics with correct URLs
        const chpHealthTopics = {
            '發燒': {
                title: '發燒的處理',
                url: 'https://www.chp.gov.hk/tc/resources/464.htm',
                content: '發燒是身體對感染或疾病的自然反應。成人體溫超過38°C (100.4°F)即屬發燒。',
                advice: '多休息、多喝水、穿著輕便衣物。如持續高燒或出現其他嚴重症狀，應盡快求醫。'
            },
            '咳嗽': {
                title: '咳嗽的認識與處理',
                url: 'https://www.chp.gov.hk/tc/resources/465.htm',
                content: '咳嗽是呼吸道的保護性反射動作，有助清除呼吸道的異物和分泌物。',
                advice: '保持室內空氣流通、多喝溫水、避免刺激性食物。持續咳嗽超過兩週應求醫檢查。'
            },
            '頭痛': {
                title: '頭痛的預防與處理',
                url: 'https://www.chp.gov.hk/tc/resources/466.htm',
                content: '頭痛是常見症狀，大部分屬於原發性頭痛，如緊張性頭痛或偏頭痛。',
                advice: '保持規律作息、適度運動、減少壓力。如頭痛劇烈或伴隨其他症狀，應立即求醫。'
            },
            '腹痛': {
                title: '腹痛的常見原因',
                url: 'https://www.chp.gov.hk/tc/resources/467.htm',
                content: '腹痛可能由多種原因引起，包括消化不良、腸胃炎、闌尾炎等。',
                advice: '注意飲食衛生、避免暴飲暴食。如腹痛劇烈或持續，應盡快求醫診治。'
            },
            '糖尿病': {
                title: '糖尿病的預防與管理',
                url: 'https://www.chp.gov.hk/tc/resources/468.htm',
                content: '糖尿病是一種慢性疾病，患者的血糖水平持續偏高。主要症狀包括多飲、多尿、疲倦等。',
                advice: '定期監測血糖、遵從醫生指示服藥、保持健康飲食和適量運動。'
            },
            '高血壓': {
                title: '高血壓的預防與控制',
                url: 'https://www.chp.gov.hk/tc/resources/469.htm',
                content: '高血壓是心血管疾病的主要風險因素，通常沒有明顯症狀，被稱為「隱形殺手」。',
                advice: '定期量血壓、減少鹽分攝取、保持健康體重、戒煙限酒、適量運動。'
            },
            '感冒': {
                title: '感冒的預防與護理',
                url: 'https://www.chp.gov.hk/tc/resources/470.htm',
                content: '感冒是由病毒感染引起的上呼吸道疾病，症狀包括鼻塞、流鼻水、喉嚨痛等。',
                advice: '充足休息、多喝水、保持室內空氣流通。症狀持續或惡化應求醫診治。'
            },
            '流感': {
                title: '流行性感冒的預防',
                url: 'https://www.chp.gov.hk/tc/resources/471.htm',
                content: '流感是由流感病毒引起的急性呼吸道感染，傳染性強，可引起嚴重併發症。',
                advice: '接種流感疫苗、勤洗手、避免接觸患者。出現症狀應及早求醫。'
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

    mapCHPContent(symptoms, chpContent) {
        const relevantTopics = [];
        
        // Define symptom-to-CHP topic mappings based on actual content
        // Prioritize common conditions over rare infectious diseases
        const symptomMappings = {
            // Cardiovascular & Heart
            '心臟病': ['心臟病', '心血管疾病', '冠心病'],
            '高血壓': ['心臟病', '高血壓', '心血管疾病'],
            '胸痛': ['心臟病', '心血管疾病'],
            '心悸': ['心臟病', '心血管疾病'],
            '心跳': ['心臟病', '心血管疾病'],
            '心律不整': ['心臟病', '心血管疾病'],
            '心臟衰竭': ['心臟病', '心血管疾病'],
            '中風': ['中風', '腦血管疾病'],
            '心': ['心臟病', '心血管疾病'],
            'heart': ['心臟病'],
            'cardiac': ['心臟病'],
            'cardiovascular': ['心血管疾病'],

            // Respiratory & Infectious
            '流感': ['乙型流感嗜血桿菌感染', '季節性流感', '季節流行性感冒', '流行性感冒'],
            '感冒': ['2019冠狀病毒病', '季節流行性感冒', '流行性感冒'],
            '咳嗽': ['2019冠狀病毒病', '肺炎球菌感染', '肺炎支原體感染', '季節流行性感冒'],
            '發燒': ['2019冠狀病毒病', '水痘', '手足口病', '季節流行性感冒', '傷寒'],
            '喉嚨痛': ['2019冠狀病毒病', '猩紅熱', '季節流行性感冒'],
            '呼吸困難': ['2019冠狀病毒病', '肺炎球菌感染', '哮喘'],
            '肺炎': ['肺炎球菌感染', '肺炎支原體感染', '肺炎'],
            '鼻塞': ['2019冠狀病毒病', '季節流行性感冒'],
            '支氣管炎': ['肺炎支原體感染'],
            '哮喘': ['哮喘'],
            '肺結核': ['肺結核'],
            'tuberculosis': ['肺結核'],
            'influenza': ['季節性流感', '季節流行性感冒'],
            'flu': ['季節性流感', '季節流行性感冒'],
            'cough': ['2019冠狀病毒病'],
            'fever': ['2019冠狀病毒病'],
            'sore throat': ['2019冠狀病毒病'],

            // Gastrointestinal & Digestive
            '腹痛': ['諾如病毒感染', '食物中毒', '腸胃炎', '腸胃炎', '霍亂', '傷寒'],
            '腹瀉': ['諾如病毒感染', '食物中毒', '腸胃炎', '霍亂', '傷寒'],
            '嘔吐': ['諾如病毒感染', '食物中毒', '腸胃炎', '霍亂', '傷寒'],
            '胃痛': ['腸胃炎', '消化不良', '消化性潰瘍'],
            '噁心': ['腸胃炎', '食物中毒'],
            '胃腸': ['腸胃炎'],
            '腸胃炎': ['腸胃炎'],
            '食物中毒': ['食物中毒'],
            '消化不良': ['消化不良'],
            '消化性潰瘍': ['消化性潰瘍'],
            '肝炎': ['病毒性肝炎'],
            '膽石': ['膽石症'],
            '胰臟炎': ['急性胰臟炎'],
            'food poisoning': ['食物中毒'],
            'gastroenteritis': ['腸胃炎'],
            'diarrhea': ['諾如病毒感染'],
            'vomiting': ['諾如病毒感染'],
            'nausea': ['腸胃炎'],
            'stomach': ['腸胃炎'],

            // Skin & Dermatological
            '皮疹': ['水痘', '手足口病', '麻疹', '猩紅熱', '德國麻疹'],
            '水泡': ['水痘'],
            '口腔潰瘍': ['手足口病'],
            '手足皮疹': ['手足口病'],
            '麻疹': ['麻疹'],
            '德國麻疹': ['德國麻疹'],
            '猩紅熱': ['猩紅熱'],
            '帶狀皰疹': ['帶狀皰疹'],
            '皮膚感染': ['皮膚感染'],
            'rash': ['水痘', '手足口病'],
            'blister': ['水痘'],
            'measles': ['麻疹'],
            'chickenpox': ['水痘'],
            'shingles': ['帶狀皰疹'],

            // Mental Health & Psychiatric
            '抑鬱': ['心理健康', '抑鬱症', '精神健康'],
            '焦慮': ['心理健康', '焦慮症', '精神健康'],
            '壓力大': ['心理健康', '壓力管理', '精神健康'],
            '精神': ['精神健康'],
            '情緒': ['心理健康'],
            '壓力': ['壓力管理'],
            '焦慮症': ['焦慮症'],
            '抑鬱症': ['抑鬱症'],
            '精神健康': ['精神健康'],
            'depression': ['心理健康', '抑鬱症'],
            'anxiety': ['心理健康', '焦慮症'],
            'stress': ['心理健康', '壓力管理'],
            'mental': ['心理健康'],
            'mood': ['心理健康'],

            // Metabolic & Endocrine
            '糖尿病': ['糖尿病', '糖尿病及其併發症'],
            '口渴': ['糖尿病'],
            '多尿': ['糖尿病'],
            '多飲': ['糖尿病'],
            '體重減輕': ['糖尿病'],
            '甲狀腺': ['甲狀腺功能減退'],
            'diabetes': ['糖尿病'],
            'diabetic': ['糖尿病'],
            'thyroid': ['甲狀腺功能減退'],

            // Neurological
            '頭痛': ['2019冠狀病毒病', '偏頭痛', '頭痛'],
            '頭暈': ['心臟病', '糖尿病', '貧血', '頭暈'],
            '中風': ['中風'],
            '偏頭痛': ['偏頭痛'],
            '頭暈': ['頭暈'],
            '癲癇': ['癲癇'],
            '帕金森病': ['帕金森病'],
            '阿茲海默病': ['認知障礙症'],
            'headache': ['2019冠狀病毒病', '偏頭痛'],
            'dizziness': ['心臟病', '糖尿病'],
            'stroke': ['中風'],
            'migraine': ['偏頭痛'],
            'epilepsy': ['癲癇'],
            'parkinson': ['帕金森病'],

            // Cancer & Oncology
            '癌症': ['癌症預防'],
            '腫瘤': ['癌症預防'],
            '乳癌': ['乳癌'],
            '大腸癌': ['大腸癌'],
            '肺癌': ['肺癌'],
            '肝癌': ['肝癌'],
            '癌': ['癌症預防'],
            'cancer': ['癌症預防'],
            'tumor': ['癌症預防'],
            'breast cancer': ['乳癌'],
            'colorectal cancer': ['大腸癌'],
            'lung cancer': ['肺癌'],
            'liver cancer': ['肝癌'],
            // Cancer symptoms mapping
            '乳房腫塊': ['乳癌'],
            '乳頭分泌': ['乳癌'],
            '乳房': ['乳癌'],
            '尿頻': ['攝護腺癌'],
            '尿急': ['攝護腺癌'],
            '夜尿': ['攝護腺癌'],
            '攝護腺': ['攝護腺癌'],
            '前列腺': ['攝護腺癌'],
            '持續咳嗽': ['肺癌'],
            '咳血': ['肺癌'],
            '睪丸腫大': ['睪丸癌'],
            '睪丸': ['睪丸癌'],
            '疼痛': ['睪丸癌'],
            '腹脹': ['卵巢癌'],
            '腹痛': ['卵巢癌', '大腸癌'],
            '不正常陰道出血': ['子宮頸癌'],
            '骨盆痛': ['子宮頸癌', '卵巢癌'],
            '大便習慣改變': ['大腸癌'],
            '血便': ['大腸癌'],
            '體重減輕': ['肺癌', '肝癌', '大腸癌'],

            // Women's Health
            '乳癌': ['乳癌'],
            '子宮頸癌': ['子宮頸癌'],
            '卵巢癌': ['卵巢癌'],
            '子宮肌瘤': ['子宮肌瘤'],
            '子宮內膜異位': ['子宮內膜異位症'],
            '更年期': ['更年期'],
            '經痛': ['經痛'],
            '不孕': ['不育症'],
            'pregnancy': ['懷孕與準備懷孕'],
            'menopause': ['更年期'],
            'dysmenorrhea': ['經痛'],

            // Men's Health
            '攝護腺': ['攝護腺癌'],
            '前列腺': ['攝護腺癌'],
            '睪丸癌': ['睪丸癌'],
            'prostate': ['攝護腺癌'],
            'testicular': ['睪丸癌'],

            // Pediatric & Children's Health
            '手足口': ['手足口病'],
            '水痘': ['水痘'],
            '麻疹': ['麻疹'],
            '德國麻疹': ['德國麻疹'],
            '百日咳': ['百日咳'],
            '小兒麻痹': ['小兒麻痹症'],
            'child': ['兒童健康'],
            'infant': ['嬰兒健康'],
            'pediatric': ['兒童健康'],

            // Eye & ENT
            '結膜炎': ['傳染性急性結膜炎'],
            '眼紅': ['傳染性急性結膜炎'],
            '青光眼': ['青光眼'],
            '白內障': ['白內障'],
            '中耳炎': ['中耳炎'],
            '耳鳴': ['耳鳴'],
            '眼': ['傳染性急性結膜炎'],
            '耳': ['中耳炎'],
            'conjunctivitis': ['傳染性急性結膜炎'],
            'glaucoma': ['青光眼'],
            'cataract': ['白內障'],
            'otitis': ['中耳炎'],

            // Bone & Joint
            '骨質疏鬆': ['骨質疏鬆'],
            '關節炎': ['關節炎'],
            '骨折': ['骨折'],
            'osteoporosis': ['骨質疏鬆'],
            'arthritis': ['關節炎'],
            'fracture': ['骨折'],

            // Other Medical Conditions
            '貧血': ['貧血'],
            '腎病': ['慢性腎病'],
            '肝病': ['病毒性肝炎'],
            '腎結石': ['腎結石'],
            '膽結石': ['膽石症'],
            '腎': ['慢性腎病'],
            '肝': ['病毒性肝炎'],
            'anemia': ['貧血'],
            'kidney': ['慢性腎病'],
            'liver': ['病毒性肝炎'],

            // Infectious Diseases
            '愛滋病': ['人類免疫缺乏病毒感染'],
            '艾滋病': ['人類免疫缺乏病毒感染'],
            'HIV': ['人類免疫缺乏病毒感染'],
            '愛滋': ['人類免疫缺乏病毒感染'],
            '梅毒': ['梅毒'],
            '淋病': ['淋病'],
            '衣原體': ['衣原體感染'],
            '生殖器皰疹': ['生殖器皰疹'],
            'syphilis': ['梅毒'],
            'gonorrhea': ['淋病'],
            'chlamydia': ['衣原體感染'],
            'herpes': ['生殖器皰疹'],
            // STD symptoms mapping
            '異常分泌物': ['淋病', '衣原體感染', '梅毒'],
            '尿道痛': ['淋病', '衣原體感染'],
            '陰部搔癢': ['淋病', '衣原體感染', '生殖器皰疹'],
            '陰部痛': ['衣原體感染', '淋病'],
            '無症狀感染': ['衣原體感染'],
            '生殖器潰瘍': ['梅毒', '生殖器皰疹'],
            '生殖器': ['梅毒', '生殖器皰疹', '淋病', '衣原體感染'],
            '淋巴結腫大': ['梅毒', '人類免疫缺乏病毒感染'],
            '分泌物': ['淋病', '衣原體感染'],
            '尿道': ['淋病'],
            '陰部': ['衣原體感染', '淋病', '生殖器皰疹'],
            '潰瘍': ['梅毒', '生殖器皰疹'],

            // Other Symptoms
            '疲倦': ['糖尿病', '心臟病', '貧血', '甲狀腺功能減退'],
            '體重': ['糖尿病', '營養'],
            '營養': ['飲食與營養'],
            '營養不良': ['營養不良'],
            '肥胖': ['肥胖'],
            '抽煙': ['戒煙'],
            '酗酒': ['酗酒'],
            '藥物': ['藥物濫用'],
            'fatigue': ['糖尿病', '心臟病'],
            'tired': ['糖尿病', '心臟病'],
            'obesity': ['肥胖'],
            'smoking': ['戒煙'],
            'alcohol': ['酗酒'],
            'drug': ['藥物濫用'],

            // General Health & Prevention
            '疫苗': ['疫苗'],
            '預防': ['預防接種'],
            '健康檢查': ['健康檢查'],
            '運動': ['環境健康與損傷預防'],
            '環境': ['環境健康與損傷預防'],
            '職業安全': ['職業安全'],
            '疫苗': ['疫苗'],
            'vaccine': ['疫苗'],
            'prevention': ['預防接種'],
            'exercise': ['環境健康與損傷預防'],
            'environment': ['環境健康與損傷預防'],
            'occupational': ['職業安全']
        };

        // Find matching CHP content for each symptom
        for (const symptom of symptoms) {
            for (const [key, topics] of Object.entries(symptomMappings)) {
                if (symptom.includes(key) || key.includes(symptom)) {
                    // Find actual CHP content for these topics
                    for (const topic of topics) {
                        const chpEntry = chpContent.find(entry => 
                            entry.title && entry.title.includes(topic)
                        );
                        
                        if (chpEntry && !relevantTopics.find(t => t.url === chpEntry.url)) {
                            const processedEntry = this.processCHPEntry(chpEntry);
                            if (processedEntry) {
                                relevantTopics.push(processedEntry);
                            }
                        }
                    }
                }
            }
        }

        // If no specific matches found, add some general health topics
        if (relevantTopics.length === 0) {
            const generalTopics = ['心理健康', '飲食與營養', '環境健康與損傷預防'];
            for (const topic of generalTopics) {
                const chpEntry = chpContent.find(entry => 
                    entry.title && entry.title.includes(topic)
                );
                if (chpEntry) {
                    const processedEntry = this.processCHPEntry(chpEntry);
                    if (processedEntry) {
                        relevantTopics.push(processedEntry);
                        break; // Just add one general topic
                    }
                }
            }
        }

        return relevantTopics.slice(0, 3); // Limit to top 3 most relevant
    }

    processCHPEntry(chpEntry) {
        if (!chpEntry || !chpEntry.title || !chpEntry.url) {
            return null;
        }

        // Extract clean title (remove "衞生防護中心 - " prefix)
        const cleanTitle = chpEntry.title.replace('衞生防護中心 - ', '');
        
        // Extract meaningful content from the full content
        let content = '';
        let advice = '';
        
        if (chpEntry.content) {
            // Extract key information from content
            const contentText = chpEntry.content;
            
            // Look for disease description (usually after title and date)
            const lines = contentText.split('\n').filter(line => line.trim());
            
            // Find the main description (usually starts after date and before detailed sections)
            let descriptionStart = -1;
            for (let i = 0; i < lines.length; i++) {
                const line = lines[i].trim();
                if (line.includes('引 言') || line.includes('病原體') || line.includes('病徵')) {
                    descriptionStart = i + 1;
                    break;
                }
            }
            
            if (descriptionStart > -1 && descriptionStart < lines.length) {
                // Take the next few meaningful lines as content
                const contentLines = [];
                for (let i = descriptionStart; i < Math.min(descriptionStart + 3, lines.length); i++) {
                    const line = lines[i].trim();
                    if (line.length > 10 && !line.includes('列印') && !line.includes('書籤')) {
                        contentLines.push(line);
                    }
                }
                content = contentLines.join(' ').substring(0, 200) + '...';
            }
            
            // Look for prevention or treatment advice
            if (contentText.includes('預防方法')) {
                const preventionIndex = contentText.indexOf('預防方法');
                const preventionText = contentText.substring(preventionIndex, preventionIndex + 300);
                const preventionLines = preventionText.split('\n').filter(line => 
                    line.trim().length > 5 && !line.includes('預防方法')
                ).slice(0, 2);
                advice = preventionLines.join(' ').substring(0, 150);
            } else if (contentText.includes('治理方法')) {
                const treatmentIndex = contentText.indexOf('治理方法');
                const treatmentText = contentText.substring(treatmentIndex, treatmentIndex + 200);
                const treatmentLines = treatmentText.split('\n').filter(line => 
                    line.trim().length > 5 && !line.includes('治理方法')
                ).slice(0, 1);
                advice = treatmentLines.join(' ').substring(0, 150);
            }
        }
        
        // Use excerpt if content extraction failed
        if (!content && chpEntry.excerpt && chpEntry.excerpt !== 'No excerpt') {
            content = chpEntry.excerpt.substring(0, 200);
        }
        
        // Fallback content if still empty
        if (!content) {
            content = `${cleanTitle}的相關健康資訊，請參閱香港衛生署官方網頁了解詳情。`;
        }
        
        if (!advice) {
            advice = '如有相關症狀或疑問，建議諮詢醫護人員的專業意見。';
        }

        return {
            title: cleanTitle,
            url: chpEntry.url,
            content: content,
            advice: advice
        };
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
