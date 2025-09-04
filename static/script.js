document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('patientForm');
    const results = document.getElementById('results');
    const loadingDiv = document.getElementById('loading');
    const doctorList = document.getElementById('doctorList');
    const diagnosisResult = document.getElementById('diagnosisResult');
    
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
                this.innerHTML = '<i class="fas fa-plus-circle"></i> 更多資料';
            } else {
                moreInfoSection.style.display = 'block';
                this.classList.add('expanded');
                this.innerHTML = '<i class="fas fa-minus-circle"></i> 收起資料';
            }
        });
    }

    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const age = document.getElementById('age').value;
        const symptoms = document.getElementById('symptoms').value;
        const language = document.getElementById('language').value;
        const location = document.getElementById('location').value;
        
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
        
        // 收集表單數據
        const formData = {
            age: age,
            symptoms: symptoms,
            chronicConditions: chronicConditions,
            language: language,
            location: location,
            detailedHealthInfo: detailedHealthInfo
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
            doctorList.innerHTML = `
                <div class="alert alert-warning" style="text-align: center; padding: 20px; margin: 20px 0; border-radius: 10px; background-color: #fff3cd; border: 1px solid #ffeaa7;">
                    <i class="fas fa-exclamation-triangle" style="font-size: 2rem; color: #856404; margin-bottom: 10px;"></i>
                    <h4 style="color: #856404; margin-bottom: 10px;">服務暫時不可用</h4>
                    <p style="color: #856404; margin-bottom: 15px;">抱歉，AI診斷服務暫時無法使用。請稍後再試，或直接聯繫醫療專業人士。</p>
                    <button onclick="location.reload()" class="btn btn-primary" style="background-color: #007bff; border: none; padding: 10px 20px; border-radius: 5px; color: white;">
                        <i class="fas fa-redo"></i> 重新嘗試
                    </button>
                </div>
            `;
            results.scrollIntoView({ behavior: 'smooth' });
        }
    });

    function displayResults(data) {
        doctorList.innerHTML = '';
        
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
                errorCard.innerHTML = `
                    <i class="fas fa-exclamation-triangle" style="font-size: 2rem; color: #856404; margin-bottom: 10px;"></i>
                    <h4 style="color: #856404; margin-bottom: 10px;">AI診斷暫時不可用</h4>
                    <p style="color: #856404; margin-bottom: 15px;">我們的AI診斷服務暫時無法使用，但您仍可以查看推薦的醫生。建議直接諮詢醫療專業人士。</p>
                `;
                doctorList.appendChild(errorCard);
            } else {
                const diagnosisCard = createDiagnosisCard(data.diagnosis, data.recommended_specialty);
                doctorList.appendChild(diagnosisCard);
            }
        }
        
        if (data.doctors && data.doctors.length > 0) {
            // 添加醫生推薦標題
            const doctorHeader = document.createElement('h3');
            doctorHeader.innerHTML = '<i class="fas fa-user-doctor"></i> 推薦醫生';
            doctorHeader.style.cssText = 'margin: 30px 0 20px 0; color: #333; font-size: 1.5rem; display: flex; align-items: center; gap: 10px;';
            doctorList.appendChild(doctorHeader);
            
            data.doctors.forEach((doctor, index) => {
                const doctorCard = createDoctorCard(doctor, index + 1);
                doctorList.appendChild(doctorCard);
            });
            results.style.display = 'block';
            results.scrollIntoView({ behavior: 'smooth' });
        } else {
            const noResultsMsg = document.createElement('p');
            noResultsMsg.innerHTML = '抱歉，未能找到合適的醫生。請嘗試修改搜索條件。';
            noResultsMsg.style.cssText = 'text-align: center; color: #666; font-size: 1.1rem; margin-top: 20px;';
            doctorList.appendChild(noResultsMsg);
            results.style.display = 'block';
        }
    }

    function createDoctorCard(doctor, rank) {
        const card = document.createElement('div');
        card.className = 'doctor-card';
        
        // 獲取醫生姓名的第一個字符作為頭像
        const avatarText = doctor.name ? doctor.name.charAt(0) : 'Dr';
        
        // 處理聯絡電話（可能有多個）
        const phones = doctor.contact_numbers ? doctor.contact_numbers.split(',').map(p => p.trim()) : [];
        const phoneDisplay = phones.length > 0 ? phones.join(' / ') : '未提供';
        
        // 處理地址
        const address = doctor.clinic_addresses || '未提供';
        
        // 處理語言
        const languages = doctor.languages || '未提供';
        
        // 處理資格
        const qualifications = doctor.qualifications || '未提供';
        
        card.innerHTML = `
            <div class="match-score">
                <i class="fas fa-star"></i>
                第 ${rank} 推薦
            </div>
            <div class="whatsapp-hint">
                <i class="fab fa-whatsapp"></i>
                點擊聯絡
            </div>
            
            <div class="doctor-header">
                <div class="doctor-avatar">
                    ${avatarText}
                </div>
                <div class="doctor-info">
                    <h3>${doctor.name || '未知醫生'}</h3>
                    <div class="doctor-specialty">${doctor.specialty || '專科醫生'}</div>
                </div>
            </div>
            
            <div class="doctor-details">
                <div class="detail-item">
                    <i class="fas fa-language"></i>
                    <div>
                        <strong>語言：</strong>
                        ${languages}
                    </div>
                </div>
                
                <div class="detail-item">
                    <i class="fas fa-phone"></i>
                    <div>
                        <strong>電話：</strong>
                        ${phoneDisplay}
                    </div>
                </div>
                
                <div class="detail-item">
                    <i class="fas fa-envelope"></i>
                    <div>
                        <strong>電郵：</strong>
                        ${doctor.email || '未提供'}
                    </div>
                </div>
                
                <div class="detail-item">
                    <i class="fas fa-map-marker-alt"></i>
                    <div>
                        <strong>診所地址：</strong>
                        ${address}
                    </div>
                </div>
            </div>
            
            <div class="detail-item" style="margin-top: 15px;">
                <i class="fas fa-graduation-cap"></i>
                <div>
                    <strong>專業資格：</strong>
                    ${qualifications}
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
                    <h3>您的健康資料摘要</h3>
                </div>
            </div>
            
            <div class="summary-content">
                <div class="summary-text">
                    ${formattedSummary}
                </div>
            </div>
        `;
        
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
                    <h3>AI 智能診斷分析</h3>
                    <div class="recommended-specialty">推薦專科：${recommendedSpecialty}</div>
                </div>
            </div>
            
            <div class="diagnosis-content">
                <div class="diagnosis-text">
                    ${formattedDiagnosis}
                </div>
            </div>
            
            <div class="diagnosis-disclaimer">
                <i class="fas fa-exclamation-triangle"></i>
                <strong>重要提醒：</strong>此AI分析僅供參考，不能替代專業醫療診斷。請務必諮詢合格醫生進行正式診斷。
            </div>
        `;
        
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
