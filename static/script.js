document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('patientForm');
    const results = document.getElementById('results');
    const loadingDiv = document.getElementById('loading');
    const doctorList = document.getElementById('doctorList');
    const diagnosisResult = document.getElementById('diagnosisResult');
    
    // Location cascade data
    const locationData = {
        '香港島': {
            '中西區': ['中環', '上環', '西環', '金鐘', '堅尼地城', '石塘咀', '西營盤'],
            '東區': ['銅鑼灣', '天后', '炮台山', '北角', '鰂魚涌', '西灣河', '筲箕灣', '柴灣', '小西灣'],
            '南區': ['香港仔', '鴨脷洲', '黃竹坑', '深水灣', '淺水灣', '赤柱', '石澳'],
            '灣仔區': ['灣仔', '跑馬地', '大坑', '渣甸山', '寶馬山']
        },
        '九龍': {
            '九龍城區': ['九龍城', '土瓜灣', '馬頭角', '馬頭圍', '啟德', '紅磡', '何文田'],
            '觀塘區': ['觀塘', '牛頭角', '九龍灣', '彩虹', '坪石', '秀茂坪', '藍田', '油塘'],
            '深水埗區': ['深水埗', '長沙灣', '荔枝角', '美孚', '石硤尾', '又一村'],
            '黃大仙區': ['黃大仙', '新蒲崗', '樂富', '橫頭磡', '東頭', '竹園', '慈雲山', '鑽石山'],
            '油尖旺區': ['油麻地', '尖沙咀', '旺角', '大角咀', '太子', '佐敦']
        },
        '新界': {
            '離島區': ['長洲', '南丫島', '坪洲', '大嶼山', '東涌', '愉景灣'],
            '葵青區': ['葵涌', '青衣', '葵芳', '荔景'],
            '北區': ['上水', '粉嶺', '打鼓嶺', '沙頭角', '鹿頸'],
            '西貢區': ['西貢', '將軍澳', '坑口', '調景嶺', '寶林', '康盛花園'],
            '沙田區': ['沙田', '大圍', '火炭', '馬鞍山', '烏溪沙'],
            '大埔區': ['大埔', '太和', '大埔墟', '林村', '汀角'],
            '荃灣區': ['荃灣', '梨木樹', '象山', '城門'],
            '屯門區': ['屯門', '友愛', '安定', '山景', '大興', '良景', '建生'],
            '元朗區': ['元朗', '天水圍', '洪水橋', '流浮山', '錦田', '八鄉']
        }
    };
    
    // Location cascade handlers
    const regionSelect = document.getElementById('region');
    const districtSelect = document.getElementById('district');
    const areaSelect = document.getElementById('area');
    
    regionSelect.addEventListener('change', function() {
        const selectedRegion = this.value;
        
        // Reset and hide subsequent dropdowns
        const districtPlaceholder = window.currentTranslations && window.currentTranslations['select_district'] 
            ? window.currentTranslations['select_district'] : '請選擇地區';
        const areaPlaceholder = window.currentTranslations && window.currentTranslations['select_area'] 
            ? window.currentTranslations['select_area'] : '請選擇具體位置 (可選)';
            
        districtSelect.innerHTML = `<option value="" data-translate="select_district">${districtPlaceholder}</option>`;
        areaSelect.innerHTML = `<option value="" data-translate="select_area">${areaPlaceholder}</option>`;
        districtSelect.style.display = 'none';
        areaSelect.style.display = 'none';
        
        if (selectedRegion && locationData[selectedRegion]) {
            // Populate district dropdown
            Object.keys(locationData[selectedRegion]).forEach(district => {
                const option = document.createElement('option');
                option.value = district;
                option.setAttribute('data-translate', district);
                
                // Use current translation if available
                if (window.currentTranslations && window.currentTranslations[district]) {
                    option.textContent = window.currentTranslations[district];
                } else {
                    option.textContent = district;
                }
                
                districtSelect.appendChild(option);
            });
            districtSelect.style.display = 'block';
        }
    });
    
    districtSelect.addEventListener('change', function() {
        const selectedRegion = regionSelect.value;
        const selectedDistrict = this.value;
        
        // Reset area dropdown
        const areaPlaceholder = window.currentTranslations && window.currentTranslations['select_area'] 
            ? window.currentTranslations['select_area'] : '請選擇具體位置 (可選)';
        areaSelect.innerHTML = `<option value="" data-translate="select_area">${areaPlaceholder}</option>`;
        areaSelect.style.display = 'none';
        
        if (selectedRegion && selectedDistrict && locationData[selectedRegion][selectedDistrict]) {
            // Populate area dropdown
            locationData[selectedRegion][selectedDistrict].forEach(area => {
                const option = document.createElement('option');
                option.value = area;
                option.setAttribute('data-translate', area);
                
                // Use current translation if available
                if (window.currentTranslations && window.currentTranslations[area]) {
                    option.textContent = window.currentTranslations[area];
                } else {
                    option.textContent = area;
                }
                
                areaSelect.appendChild(option);
            });
            areaSelect.style.display = 'block';
        }
    });
    
    // 處理「其他」選項的顯示/隱藏
    const otherCheckbox = document.getElementById('other-condition-checkbox');
    const otherInput = document.getElementById('other-condition-input');
    
    if (otherCheckbox && otherInput) {
        otherCheckbox.addEventListener('change', function() {
            if (this.checked) {
                otherInput.style.display = 'block';
                document.getElementById('other-condition-text').focus();
            } else {
                otherInput.style.display = 'none';
                document.getElementById('other-condition-text').value = '';
            }
        });
    }
    
    // 處理「更多資料」按鈕的展開/收縮
    const moreInfoBtn = document.getElementById('more-info-btn');
    const moreInfoSection = document.getElementById('more-info-section');
    
    if (moreInfoBtn && moreInfoSection) {
        moreInfoBtn.addEventListener('click', function() {
            const isVisible = moreInfoSection.style.display !== 'none';
            
            if (isVisible) {
                moreInfoSection.style.display = 'none';
                this.classList.remove('expanded');
                const moreText = window.currentTranslations && window.currentTranslations['more_info'] 
                    ? window.currentTranslations['more_info'] : '更多資料';
                this.innerHTML = `<i class="fas fa-plus-circle"></i> ${moreText}`;
            } else {
                moreInfoSection.style.display = 'block';
                this.classList.add('expanded');
                const lessText = window.currentTranslations && window.currentTranslations['less_info'] 
                    ? window.currentTranslations['less_info'] : '收起資料';
                this.innerHTML = `<i class="fas fa-minus-circle"></i> ${lessText}`;
            }
        });
    }

    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const age = document.getElementById('age').value;
        const symptoms = document.getElementById('symptoms').value;
        const language = document.getElementById('language').value;
        
        // Collect 3-tier location data
        const region = document.getElementById('region').value;
        const district = document.getElementById('district').value;
        const area = document.getElementById('area').value;
        
        // Create location string for backend compatibility
        const location = area || district || region;
        
        // 收集長期病史複選框數據
        const chronicConditions = (function() {
            const checkboxes = document.querySelectorAll('input[name="chronic-condition"]:checked');
            const conditions = [];
            
            checkboxes.forEach(checkbox => {
                if (checkbox.value === '其他') {
                    const otherText = document.getElementById('other-condition-text').value.trim();
                    if (otherText) {
                        conditions.push(otherText);
                    }
                } else {
                    conditions.push(checkbox.value);
                }
            });
            
            return conditions.join('、');
        })();
        
        // 驗證症狀數量
        if (!validateSymptoms(symptoms)) {
            alert('請至少輸入3個症狀，以便 AI 進行準確分析。');
            return;
        }

        // 收集詳細健康信息
        const detailedHealthInfo = (function() {
            const height = document.getElementById('height').value;
            const weight = document.getElementById('weight').value;
            const medications = document.getElementById('medications').value;
            const allergies = document.getElementById('allergies').value;
            const surgeries = document.getElementById('surgeries').value;
            
            const bloodThinner = document.getElementById('blood-thinner').checked;
            const recentVisit = document.getElementById('recent-visit').checked;
            const cpapMachine = document.getElementById('cpap-machine').checked;
            const looseTeeth = document.getElementById('loose-teeth').checked;
            
            return {
                height: height,
                weight: weight,
                medications: medications,
                allergies: allergies,
                surgeries: surgeries,
                bloodThinner: bloodThinner,
                recentVisit: recentVisit,
                cpapMachine: cpapMachine,
                looseTeeth: looseTeeth
            };
        })();
        
        // Get current UI language from language manager
        const currentUILanguage = window.languageManager ? window.languageManager.currentLang : 'zh-TW';
        
        // 收集表單數據
        const formData = {
            age: age,
            symptoms: symptoms,
            chronicConditions: chronicConditions,
            language: language,
            location: location,
            locationDetails: {
                region: region,
                district: district,
                area: area
            },
            detailedHealthInfo: detailedHealthInfo,
            uiLanguage: currentUILanguage  // Add UI language for diagnosis
        };

        // 顯示載入動畫
        loading.style.display = 'block';
        results.style.display = 'none';

        try {
            // 發送請求到後端
            const response = await fetch('/find_doctor', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });

            if (!response.ok) {
                throw new Error('網絡請求失敗');
            }

            const data = await response.json();
            
            // 隱藏載入動畫
            loading.style.display = 'none';
            
            // 顯示結果
            displayResults(data);
            
        } catch (error) {
            console.error('錯誤:', error);
            loading.style.display = 'none';
            
            // Show graceful error message
            results.style.display = 'block';
            const serviceUnavailableTitle = window.currentTranslations && window.currentTranslations['service_unavailable'] 
                ? window.currentTranslations['service_unavailable'] : '服務暫時不可用';
            doctorList.innerHTML = `
                <div class="alert alert-warning" style="text-align: center; padding: 20px; margin: 20px 0; border-radius: 10px; background-color: #fff3cd; border: 1px solid #ffeaa7;">
                    <i class="fas fa-exclamation-triangle" style="font-size: 2rem; color: #856404; margin-bottom: 10px;"></i>
                    <h4 style="color: #856404; margin-bottom: 10px;">${serviceUnavailableTitle}</h4>
                    <p style="color: #856404; margin-bottom: 15px;">我們的服務暫時遇到問題，請稍後再試。如有緊急醫療需要，請直接聯繫醫療機構。</p>
                    <p style="color: #856404; font-size: 0.9rem;">錯誤代碼: ${error.message || 'Unknown error'}</p>
                </div>
            `;
            results.scrollIntoView({ behavior: 'smooth' });
        }
    });

    // Global variables for pagination
    let allDoctors = [];
    let currentlyDisplayed = 0;
    const doctorsPerPage = 5;

    function displayResults(data) {
        doctorList.innerHTML = '';
        
        // Reset pagination state
        allDoctors = data.doctors || [];
        currentlyDisplayed = 0;
        
        // 顯示用戶數據摘要
        if (data.user_summary) {
            const summaryCard = createUserSummaryCard(data.user_summary);
            doctorList.appendChild(summaryCard);
        }
        
        // 顯示AI診斷結果
        if (data.diagnosis) {
            // Check if diagnosis contains error messages
            if (data.diagnosis.includes('AI分析服務暫時不可用') || 
                data.diagnosis.includes('AI服務配置不完整') ||
                data.diagnosis.includes('請稍後再試')) {
                
                const errorCard = document.createElement('div');
                errorCard.className = 'alert alert-warning';
                errorCard.style.cssText = 'text-align: center; padding: 20px; margin: 20px 0; border-radius: 10px; background-color: #fff3cd; border: 1px solid #ffeaa7;';
                const aiUnavailableTitle = window.currentTranslations && window.currentTranslations['ai_diagnosis_unavailable'] 
                    ? window.currentTranslations['ai_diagnosis_unavailable'] : 'AI診斷暫時不可用';
                const aiUnavailableDesc = window.currentTranslations && window.currentTranslations['ai_diagnosis_unavailable_desc'] 
                    ? window.currentTranslations['ai_diagnosis_unavailable_desc'] : '我們的AI診斷服務暫時無法使用，但您仍可以查看推薦的醫生。建議直接諮詢醫療專業人士。';
                errorCard.innerHTML = `
                    <i class="fas fa-exclamation-triangle" style="font-size: 2rem; color: #856404; margin-bottom: 10px;"></i>
                    <h4 style="color: #856404; margin-bottom: 10px;">${aiUnavailableTitle}</h4>
                    <p style="color: #856404; margin-bottom: 15px;">${aiUnavailableDesc}</p>
                `;
                doctorList.appendChild(errorCard);
            } else {
                const diagnosisCard = createDiagnosisCard(data.diagnosis, data.recommended_specialty);
                doctorList.appendChild(diagnosisCard);
            }
        }
        
        // Store doctor results globally for language switching
        window.lastDoctorResults = allDoctors;
        
        // 顯示醫生結果
        if (allDoctors.length > 0) {
            // 添加醫生推薦標題
            const doctorHeader = document.createElement('h3');
            const headerText = window.currentTranslations && window.currentTranslations['recommended_doctors'] 
                ? window.currentTranslations['recommended_doctors'] : '推薦醫生';
            doctorHeader.innerHTML = `<i class="fas fa-user-doctor"></i> ${headerText}`;
            doctorHeader.style.cssText = 'margin: 30px 0 20px 0; color: #333; font-size: 1.5rem; display: flex; align-items: center; gap: 10px;';
            doctorList.appendChild(doctorHeader);
            
            // Create container for doctors
            const doctorsContainer = document.createElement('div');
            doctorsContainer.id = 'doctorsContainer';
            doctorList.appendChild(doctorsContainer);
            
            // Show initial doctors
            showMoreDoctors();
            
            results.style.display = 'block';
            results.scrollIntoView({ behavior: 'smooth' });
        } else {
            const noResultsMsg = document.createElement('p');
            const noResultsText = window.currentTranslations && window.currentTranslations['no_doctors_found'] 
                ? window.currentTranslations['no_doctors_found'] : '抱歉，未能找到合適的醫生。請嘗試修改搜索條件。';
            noResultsMsg.innerHTML = noResultsText;
            noResultsMsg.style.cssText = 'text-align: center; color: #666; font-size: 1.1rem; margin-top: 20px;';
            doctorList.appendChild(noResultsMsg);
            results.style.display = 'block';
        }
    }

    function showMoreDoctors() {
        const doctorsContainer = document.getElementById('doctorsContainer');
        const startIndex = currentlyDisplayed;
        const endIndex = Math.min(startIndex + doctorsPerPage, allDoctors.length);
        
        // Add doctors to display
        for (let i = startIndex; i < endIndex; i++) {
            const doctorCard = createDoctorCard(allDoctors[i], i + 1);
            doctorsContainer.appendChild(doctorCard);
        }
        
        currentlyDisplayed = endIndex;
        
        // Remove existing "Show More" button
        const existingButton = document.getElementById('showMoreButton');
        if (existingButton) {
            existingButton.remove();
        }
        
        // Add "Show More" button if there are more doctors
        if (currentlyDisplayed < allDoctors.length) {
            const showMoreButton = document.createElement('div');
            showMoreButton.id = 'showMoreButton';
            showMoreButton.className = 'show-more-container';
            const showMoreText = window.currentTranslations && window.currentTranslations['show_more_doctors'] 
                ? window.currentTranslations['show_more_doctors'] : '顯示更多醫生';
            showMoreButton.innerHTML = `
                <button class="show-more-btn" id="showMoreBtn">
                    <i class="fas fa-plus-circle"></i>
                    ${showMoreText} (還有 ${allDoctors.length - currentlyDisplayed} 位)
                </button>
            `;
            
            // Add event listener to the button
            const showMoreBtn = showMoreButton.querySelector('#showMoreBtn');
            showMoreBtn.addEventListener('click', showMoreDoctors);
            doctorList.appendChild(showMoreButton);
        }
    }

    function translateSpecialty(specialty) {
        if (!specialty || !window.currentTranslations) {
            console.log('translateSpecialty: No specialty or no translations available', { specialty, hasTranslations: !!window.currentTranslations });
            return specialty;
        }
        
        // Try to find translation for the specialty
        const translated = window.currentTranslations[specialty];
        console.log('translateSpecialty:', { specialty, translated, found: !!translated });
        return translated || specialty;
    }

    function translateText(key) {
        if (!key) {
            return '';
        }
        
        // Use language manager if available
        if (window.languageManager) {
            return window.languageManager.getTranslation(key);
        }
        
        // Fallback to window.currentTranslations
        if (window.currentTranslations) {
            const translated = window.currentTranslations[key];
            return translated !== undefined ? translated : key;
        }
        
        return key;
    }

    // Helper function to get bilingual text based on current language
    function getBilingualText(doctor, field, currentLang) {
        const isEnglish = currentLang === 'en';
        
        // For English UI, prefer English then Chinese
        if (isEnglish) {
            return doctor[field + '_en'] || doctor[field + '_zh'] || doctor[field] || '';
        }
        // For Chinese UI, prefer Chinese then English
        else {
            return doctor[field + '_zh'] || doctor[field + '_en'] || doctor[field] || '';
        }
    }

    // Make createDoctorCard globally accessible
    window.createDoctorCard = function createDoctorCard(doctor, rank) {
        const card = document.createElement('div');
        card.className = 'doctor-card';
        
        // Get current language from language manager
        const currentLang = window.languageManager ? window.languageManager.getCurrentLanguage() : 'zh-TW';
        
        // Use bilingual data based on current language
        const doctorName = getBilingualText(doctor, 'name', currentLang);
        const doctorSpecialty = getBilingualText(doctor, 'specialty', currentLang);
        const doctorQualifications = getBilingualText(doctor, 'qualifications', currentLang);
        const doctorLanguages = getBilingualText(doctor, 'languages', currentLang);
        
        // 獲取醫生姓名的第一個字符作為頭像
        const avatarText = doctorName ? doctorName.charAt(0) : 'Dr';
        
        // 處理聯絡電話（可能有多個）
        const phones = doctor.contact_numbers ? doctor.contact_numbers.split(',').map(p => p.trim()) : [];
        const phoneDisplay = phones.length > 0 ? phones.join(' / ') : translateText('not_provided');
        
        // 處理地址
        const address = doctor.clinic_addresses || translateText('not_provided');
        
        card.innerHTML = `
            <div class="match-score">
                <i class="fas fa-star"></i>
                ${translateText('recommendation_rank')} ${rank}${translateText('recommendation_suffix') ? ' ' + translateText('recommendation_suffix') : ''}
            </div>
            <div class="whatsapp-hint">
                <i class="fab fa-whatsapp"></i>
                ${translateText('click_to_contact')}
            </div>
            
            <div class="doctor-header">
                <div class="doctor-avatar">
                    ${avatarText}
                </div>
                <div class="doctor-info">
                    <h3>${doctorName || translateText('unknown_doctor')}</h3>
                    <div class="doctor-specialty">${translateSpecialty(doctorSpecialty || translateText('general_specialist'))}</div>
                </div>
            </div>
            
            <div class="doctor-details">
                <div class="detail-item">
                    <i class="fas fa-language"></i>
                    <div>
                        <strong>${translateText('language_label')}</strong>
                        ${doctorLanguages || translateText('not_provided')}
                    </div>
                </div>
                
                <div class="detail-item">
                    <i class="fas fa-phone"></i>
                    <div>
                        <strong>${translateText('phone_label')}</strong>
                        ${phoneDisplay}
                    </div>
                </div>
                
                <div class="detail-item">
                    <i class="fas fa-envelope"></i>
                    <div>
                        <strong>${translateText('email_label')}</strong>
                        ${doctor.email || translateText('not_provided')}
                    </div>
                </div>
                
                <div class="detail-item">
                    <i class="fas fa-map-marker-alt"></i>
                    <div>
                        <strong>${translateText('clinic_address_label')}</strong>
                        ${address}
                    </div>
                </div>
            </div>
            
            <div class="detail-item" style="margin-top: 15px;">
                <i class="fas fa-graduation-cap"></i>
                <div>
                    <strong>${translateText('qualifications_label')}</strong>
                    ${doctorQualifications || translateText('not_provided')}
                </div>
            </div>
            
            ${false ? `
                <div class="ai-analysis">
                    <h4><i class="fas fa-robot"></i> AI 分析</h4>
                    <p>${doctor.ai_analysis}</p>
                </div>
            ` : ''}
        `;
        
        // 添加WhatsApp鏈接功能
        card.style.cursor = 'pointer';
        card.addEventListener('click', function() {
            // Track doctor click
            trackDoctorClick(doctor.name, doctor.specialty);
            
            const whatsappUrl = 'https://api.whatsapp.com/send/?phone=85294974070';
            window.open(whatsappUrl, '_blank');
        });
        
        // 添加hover效果
        card.addEventListener('mouseenter', function() {
            card.style.transform = 'translateY(-2px)';
            card.style.boxShadow = '0 8px 25px rgba(0,0,0,0.15)';
        });
        
        card.addEventListener('mouseleave', function() {
            card.style.transform = 'translateY(0)';
            card.style.boxShadow = '0 4px 15px rgba(0,0,0,0.1)';
        });
        
        return card;
    }

    function createUserSummaryCard(userSummary) {
        const card = document.createElement('div');
        card.className = 'user-summary-card';
        
        // 格式化用戶摘要文本
        const formattedSummary = userSummary.replace(/\n/g, '<br>');
        
        card.innerHTML = `
            <div class="summary-header">
                <div class="summary-icon">
                    <i class="fas fa-user-circle"></i>
                </div>
                <div class="summary-title">
                    <h3 data-translate="user_health_summary">您的健康資料摘要</h3>
                </div>
            </div>
            
            <div class="summary-content">
                <div class="summary-text">
                    ${formattedSummary}
                </div>
            </div>
        `;
        
        // Apply translations to newly created card
        setTimeout(() => {
            if (window.currentTranslations) {
                card.querySelectorAll('[data-translate]').forEach(element => {
                    const key = element.getAttribute('data-translate');
                    if (window.currentTranslations[key]) {
                        element.textContent = window.currentTranslations[key];
                    }
                });
            }
        }, 0);
        
        return card;
    }

    function createDiagnosisCard(diagnosis, recommendedSpecialty) {
        const card = document.createElement('div');
        card.className = 'diagnosis-card';
        
        // 處理診斷文本，保留換行格式
        const formattedDiagnosis = diagnosis.replace(/\n/g, '<br>');
        
        card.innerHTML = `
            <div class="diagnosis-header">
                <div class="diagnosis-icon">
                    <i class="fas fa-stethoscope"></i>
                </div>
                <div class="diagnosis-title">
                    <h3 data-translate="ai_diagnosis_analysis">AI 智能診斷分析</h3>
                    <div class="recommended-specialty"><span data-translate="recommended_specialty">推薦專科</span>：${translateSpecialty(recommendedSpecialty)}</div>
                </div>
            </div>
            
            <div class="diagnosis-content">
                <div class="diagnosis-text">
                    ${formattedDiagnosis}
                </div>
            </div>
            
            <div class="diagnosis-disclaimer">
                <i class="fas fa-exclamation-triangle"></i>
                <strong data-translate="important_reminder">重要提醒：</strong><span data-translate="ai_disclaimer">此AI分析僅供參考，不能替代專業醫療診斷。請務必諮詢合格醫生進行正式診斷。</span>
            </div>
        `;
        
        // Apply translations to newly created diagnosis card
        setTimeout(() => {
            if (window.currentTranslations) {
                card.querySelectorAll('[data-translate]').forEach(element => {
                    const key = element.getAttribute('data-translate');
                    if (window.currentTranslations[key]) {
                        element.textContent = window.currentTranslations[key];
                    }
                });
            }
        }, 0);
        
        return card;
    }

    function validateSymptoms(symptoms) {
        if (!symptoms || symptoms.trim().length === 0) {
            return false;
        }
        
        // 簡單的症狀數量檢查：使用常見分隔符
        const separators = ['、', ',', '，', ';', '；', '和', '及', '還有', '以及', '\n', '。'];
        let symptomCount = 1; // 至少有1個症狀
        
        for (const separator of separators) {
            const parts = symptoms.split(separator);
            if (parts.length > symptomCount) {
                symptomCount = parts.filter(part => part.trim().length > 0).length;
            }
        }
        
        // 檢查是否有至少3個非空白的部分
        return symptomCount >= 3;
    }

    // Function to track doctor clicks
    function trackDoctorClick(doctorName, doctorSpecialty) {
        fetch('/track_click', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                doctor_name: doctorName,
                doctor_specialty: doctorSpecialty
            })
        }).catch(error => {
            console.log('Click tracking failed:', error);
        });
    }
});
