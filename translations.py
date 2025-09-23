# -*- coding: utf-8 -*-
"""
Language translations for the AI Doctor Matching System
Supports: Traditional Chinese (zh-TW), Simplified Chinese (zh-CN), English (en)
"""

TRANSLATIONS = {
    'zh-TW': {
        # Header and Navigation
        'app_title': 'AI香港醫療配對系統',
        'main_title': 'Doctor AI.io',
        'subtitle': '免費AI症狀分析平台',
        'back_to_website': '返回主頁',
        'admin_panel': '管理後台',
        
        # Form Labels
        'patient_info': '病人資料',
        'age': '年齡',
        'symptoms': '症狀描述',
        'symptoms_note': '(至少需要3個症狀)',
        'symptoms_placeholder': '請詳細描述您的症狀，例如：頭痛、發燒、咳嗽、疲勞等（至少3個症狀以便AI準確分析）',
        'symptoms_hint': '選擇或輸入症狀，至少需要3個症狀以便AI準確分析',
        'symptom_input_placeholder': '輸入症狀並按Enter添加...',
        'height_placeholder': '例如：170',
        'weight_placeholder': '例如：65',
        'medications_placeholder': '例如：降血壓藥、糖尿病藥物等',
        'allergies_placeholder': '例如：花生、盤尼西林等',
        'surgeries_placeholder': '例如：盲腺手術、2020年等',
        'chronic_conditions': '長期病史',
        'optional': '(可選)',
        'chronic_hint': '可選擇多項，如無長期病史可不選',
        'preferred_language': '偏好語言',
        'gender': '生理性別',
        'male': '男性',
        'female': '女性',
        'location': '所在地區',
        'select_region': '請選擇大區',
        'select_district': '請選擇地區',
        'select_area': '請選擇具體位置 (可選)',
        'find_doctor': '尋找合適醫生',
        
        # More Info Section
        'more_info': '更多資料',
        'detailed_health_info': '詳細健康資料',
        'detailed_info_desc': '以下資料可協助AI更精準地分析您的病情',
        'height': '身高 (cm)',
        'weight': '體重 (kg)',
        'medications': '有服用任何長期藥物嗎？ 如有，請提供藥物種類名稱。',
        'allergies': '有食物/藥物敏感嗎？ 如有，請提供',
        'surgeries': '請問客人曾經有冒做過手術？如有，請提供',
        'blood_thinner': '有服薄血藥嗎？',
        'recent_visit': '三個月內有否就診？',
        'cpap_machine': '睡覺時需要用呼吸機嗎？',
        'loose_teeth': '有沒有已知，但未處理嘉鬆牙？',
        
        # Chronic Conditions
        'high_blood_pressure': '血壓高',
        'diabetes': '糖尿病',
        'high_cholesterol': '胆固醇高',
        'heart_disease': '心臟病',
        'stroke': '中風',
        'asthma': '哮喘',
        'chronic_lung_disease': '慢性肺病',
        'hepatitis_b': '乙型肝炎',
        'other_conditions': '其他長期疾病',
        'other_conditions_placeholder': '請輸入其他長期疾病',
        
        # Languages
        'cantonese': '廣東話',
        'english': '英語',
        'mandarin': '普通話',
        'french': '法語',
        
        # Regions
        'hong_kong_island': '香港島',
        'kowloon': '九龍',
        'new_territories': '新界',
        
        # Loading and Results
        'loading_message': 'AI正在分析您的症狀並配對合適的醫生...',
        'recommended_doctors': 'AI症狀分析結果',
        
        # Footer
        'terms_conditions': '條款及細則',
        'privacy_policy': '隱私權政策',
        'accessibility': '無障礙聲明',
        'copyright': ' 2025 XENOVATIVE Limited. 版權所有',
        
        # Bug Report
        'bug_report_title': '回報問題',
        'bug_description': '問題描述',
        'bug_description_placeholder': '請詳細描述您遇到的問題...',
        'bug_hint': '請盡量詳細描述問題，以便我們更好地協助您',
        'contact_info': '聯絡方式',
        'contact_info_placeholder': '電郵或電話號碼 (如需回覆)',
        'bug_image': '附加圖片',
        'image_hint': '支援 JPG, PNG, GIF 格式，最大 5MB',
        'optional': '(可選)',
        'cancel': '取消',
        'send_report': '發送回報',
        'sending': '發送中...',
        
        # Admin Panel
        'dashboard': '儀表板',
        'analytics': '分析報告',
        'system_config': '系統配置',
        'user_management': '用戶管理',
        'view_website': '查看網站',
        'logout': '登出',
        
        # Language Toggle
        'language_toggle': '語言',
        'switch_language': '切換語言',
        
        # Missing UI translations
        'select_language': '請選擇語言',
        'select_region': '請選擇大區',
        'select_district': '請選擇地區',
        'select_area': '請選擇具體位置 (可選)',
        
        # Region translations
        '香港島': '香港島',
        '九龍': '九龍', 
        '新界': '新界',
        
        # Dynamic UI elements
        'more_info': '更多資料',
        'less_info': '收起資料',
        'show_more_doctors': '顯示更多醫生',
        'recommended_doctors': 'AI症狀分析結果',
        'doctor_list_header': '醫生列表',
        'no_doctors_found': '抱歉，未能找到合適的醫生。請嘗試修改搜索條件。',
        'service_unavailable': '服務暫時不可用',
        'ai_diagnosis_unavailable': 'AI症狀分析暫時不可用',
        'ai_diagnosis_unavailable_desc': '我們的AI症狀分析服務暫時無法使用，但您仍可以查看相關的醫生資訊。請直接諮詢醫療專業人士。',
        
        # User summary and diagnosis cards
        'user_health_summary': '您的健康資料摘要',
        'ai_diagnosis_analysis': 'AI 智能症狀分析',
        'recommended_specialty': '相關專科資訊',
        'age_years': '年齡',
        'main_symptoms': '主要症狀',
        'body_info': '身高體重',
        'years_old_suffix': '歲',
        'height_weight_format': 'cm / kg (BMI: )',
        'important_reminder': '重要提醒：',
        'ai_disclaimer': '此AI分析僅供參考，不構成醫療建議或診斷。請務必諮詢合格醫生進行專業評估。',
        
        # Medical Specialties
        '內科': 'Internal Medicine',
        '外科': 'Surgery', 
        '兒科': 'Pediatrics',
        '婦產科': 'Obstetrics & Gynecology',
        '眼科': 'Ophthalmology',
        '耳鼻喉科': 'Otolaryngology (ENT)',
        '皮膚科': 'Dermatology',
        '骨科': 'Orthopedics',
        '神經科': 'Neurology',
        '心臟科': 'Cardiology',
        '泌尿科': 'Urology',
        '腸胃科': 'Gastroenterology',
        '精神科': 'Psychiatry',
        '急診科': 'Emergency Medicine',
        '家庭醫學科': 'Family Medicine',
        '普通科': 'General Practice',
        '呼吸科': 'Pulmonology',
        '腎臟科': 'Nephrology',
        '內分泌科': 'Endocrinology',
        '風濕免疫科': 'Rheumatology',
        '血液科': 'Hematology',
        '腫瘤科': 'Oncology',
        '復健科': 'Physical Medicine & Rehabilitation',
        '麻醉科': 'Anesthesiology',
        '放射科': 'Radiology',
        '病理科': 'Pathology',
        '核醫科': 'Nuclear Medicine',
        '職業醫學科': 'Occupational Medicine',
        '預防醫學科': 'Preventive Medicine',
        
        # Doctor Card Labels
        'recommendation_rank': '',
        'recommendation_suffix': '',
        'click_to_contact': {
            'zh-TW': '點擊聯絡',
            'en': 'Click to Contact'
        },
        'more_info': {
            'zh-TW': '更多資訊',
            'en': 'More Info'
        },
        'contact': {
            'zh-TW': '聯絡',
            'en': 'Contact'
        },
        'contact_info': {
            'zh-TW': '聯絡資訊',
            'en': 'Contact Information'
        },
        'contact_via_whatsapp': {
            'zh-TW': '透過WhatsApp聯絡',
            'en': 'Contact via WhatsApp'
        },
        'website': {
            'zh-TW': '網站',
            'en': 'Website'
        },
        'specialty_label': {
            'zh-TW': '專科',
            'en': 'Specialty'
        },
        'phone_label': {
            'zh-TW': '電話：',
            'en': 'Phone:'
        },
        'email_label': {
            'zh-TW': '電郵：',
            'en': 'Email:'
        },
        'clinic_address_label': {
            'zh-TW': '診所地址：',
            'en': 'Clinic Address:'
        },
        'qualifications_label': {
            'zh-TW': '專業資格：',
            'en': 'Qualifications:'
        },
        'language_label': {
            'zh-TW': '語言：',
            'en': 'Languages:'
        },
        'not_provided': {
            'zh-TW': '未提供',
            'en': 'Not provided'
        },
        'unknown_doctor': {
            'zh-TW': '未知醫生',
            'en': 'Unknown Doctor'
        },
        'general_specialist': {
            'zh-TW': '全科醫生',
            'en': 'General Practitioner'
        },
        'emergency_care_needed': '🚨 可能需要緊急醫療關注',
        'urgent_consultation': '可能需要緊急醫療諮詢',
        
        # AI Disclaimer Modal
        'ai_disclaimer_title': 'Doctor-AI.io 醫療配對系統聲明',
        'not_medical_advice_title': '⚠️ 非醫療建議',
        'not_medical_advice_desc': '本系統僅為AI輔助工具，提供的資訊和建議不構成專業醫療建議、診斷或治療。所有醫療決定應諮詢合格的醫療專業人員。',
        'ai_limitations_title': '🤖 AI系統限制',
        'ai_limitations_desc': 'AI分析基於您提供的症狀描述，可能存在誤差或遺漏。系統無法替代醫生的專業判斷和實際檢查。',
        'doctor_matching_title': '👨‍⚕️ 醫生配對服務',
        'doctor_matching_desc': '本系統協助您找到合適的醫療專業人員，但最終的醫療服務質量取決於個別醫生和診所。我們不對醫療結果承擔責任。',
        'emergency_notice_title': '🚨 緊急情況',
        'emergency_notice_desc': '如遇緊急醫療情況，請立即撥打999或前往最近的急診室，切勿依賴本系統進行緊急醫療決定。',
        'disclaimer_agreement': '繼續使用本系統即表示您已理解並同意以上聲明。',
        'understand_continue': '我已理解，繼續使用',
        
        # Location translations - Districts
        '中西區': '中西區',
        '東區': '東區', 
        '南區': '南區',
        '灣仔區': '灣仔區',
        '九龍城區': '九龍城區',
        '觀塘區': '觀塘區',
        '深水埗區': '深水埗區',
        '黃大仙區': '黃大仙區',
        '油尖旺區': '油尖旺區',
        '離島區': '離島區',
        '葵青區': '葵青區',
        '北區': '北區',
        '西貢區': '西貢區',
        '沙田區': '沙田區',
        '大埔區': '大埔區',
        '荃灣區': '荃灣區',
        '屯門區': '屯門區',
        '元朗區': '元朗區',
        
        # Geolocation messages
        'geolocation_auto_selected': '已自動選擇您附近的地區',
        'geolocation_permission_denied': '位置權限被拒絕，請手動選擇地區',
        'geolocation_unavailable': '位置信息不可用，請手動選擇地區',
        'geolocation_timeout': '獲取位置超時，請手動選擇地區',
        'geolocation_error': '無法獲取您的位置',

        # Location translations - Areas
        '中環': '中環', '上環': '上環', '西環': '西環', '金鐘': '金鐘', '堅尼地城': '堅尼地城', '石塘咀': '石塘咀', '西營盤': '西營盤',
        '銅鑼灣': '銅鑼灣', '天后': '天后', '炮台山': '炮台山', '北角': '北角', '鰂魚涌': '鰂魚涌', '西灣河': '西灣河', '筲箕灣': '筲箕灣', '柴灣': '柴灣', '小西灣': '小西灣',
        '香港仔': '香港仔', '鴨脷洲': '鴨脷洲', '黃竹坑': '黃竹坑', '深水灣': '深水灣', '淺水灣': '淺水灣', '赤柱': '赤柱', '石澳': '石澳',
        '灣仔': '灣仔', '跑馬地': '跑馬地', '大坑': '大坑', '渣甸山': '渣甸山', '寶馬山': '寶馬山',
        '九龍城': '九龍城', '土瓜灣': '土瓜灣', '馬頭角': '馬頭角', '馬頭圍': '馬頭圍', '啟德': '啟德', '紅磡': '紅磡', '何文田': '何文田',
        '觀塘': '觀塘', '牛頭角': '牛頭角', '九龍灣': '九龍灣', '彩虹': '彩虹', '坪石': '坪石', '秀茂坪': '秀茂坪', '藍田': '藍田', '油塘': '油塘',
        '深水埗': '深水埗', '長沙灣': '長沙灣', '荔枝角': '荔枝角', '美孚': '美孚', '石硤尾': '石硤尾', '又一村': '又一村',
        '黃大仙': '黃大仙', '新蒲崗': '新蒲崗', '樂富': '樂富', '橫頭磡': '橫頭磡', '東頭': '東頭', '竹園': '竹園', '慈雲山': '慈雲山', '鑽石山': '鑽石山',
        '油麻地': '油麻地', '尖沙咀': '尖沙咀', '旺角': '旺角', '大角咀': '大角咀', '太子': '太子', '佐敦': '佐敦',
        '長洲': '長洲', '南丫島': '南丫島', '坪洲': '坪洲', '大嶼山': '大嶼山', '東涌': '東涌', '愉景灣': '愉景灣',
        '葵涌': '葵涌', '青衣': '青衣', '葵芳': '葵芳', '荔景': '荔景',
        '上水': '上水', '粉嶺': '粉嶺', '打鼓嶺': '打鼓嶺', '沙頭角': '沙頭角', '鹿頸': '鹿頸',
        '西貢': '西貢', '將軍澳': '將軍澳', '坑口': '坑口', '調景嶺': '調景嶺', '寶林': '寶林', '康盛花園': '康盛花園',
        '沙田': '沙田', '大圍': '大圍', '火炭': '火炭', '馬鞍山': '馬鞍山', '烏溪沙': '烏溪沙',
        '大埔': '大埔', '太和': '太和', '大埔墟': '大埔墟', '林村': '林村', '汀角': '汀角',
        '荃灣': '荃灣', '梨木樹': '梨木樹', '象山': '象山', '城門': '城門',
        '屯門': '屯門', '友愛': '友愛', '安定': '安定', '山景': '山景', '大興': '大興', '良景': '良景', '建生': '建生',
        '元朗': '元朗', '天水圍': '天水圍', '洪水橋': '洪水橋', '流浮山': '流浮山', '錦田': '錦田', '八鄉': '八鄉',
        
        # AI Analysis Prompts
        'diagnosis_prompt_intro': '請根據以下症狀資料提供初步症狀分析和相關專科資訊：',
        'patient_data': '病人資料：',
        'age_label': '年齡：',
        'main_symptoms': '主要症狀：',
        'years_old': '歲',
        'no_special_health_info': '無特殊健康信息',
        'please_provide': '請提供：',
        'possible_diagnosis': '可能的症狀分析（最多3個可能性，按可能性排序）',
        'recommended_specialty': '相關專科資訊',
        'severity_assessment': '症狀嚴重程度評估（輕微/中等/嚴重）',
        'emergency_needed': '是否需要緊急就醫',
        'general_advice': '一般資訊和注意事項',
        'important_guidelines': '重要指引：',
        'mental_health_guideline': '只有在明確涉及精神健康問題（如精神崩潰、妄想、幻覺、自殺念頭、嚴重抑鬱/焦慮、恐慌症等）時，才推薦精神科。單純的身體症狀（如頭痛、頭暈、食慾不振）應優先考慮相關的身體專科',
        'trauma_guideline': '如涉及心理創傷、PTSD、情緒失控等，應推薦精神科而非內科',
        'emergency_guideline': '如症狀涉及急性或危及生命情況，應推薦急診科',
        'specialty_guideline': '根據症狀的主要系統選擇最適合的專科，避免一律推薦內科',
        'response_language': '請用繁體中文回答。所有症狀分析結果、資訊和醫療術語都必須使用繁體中文。回答格式如下：',
        'diagnosis_format': '症狀分析：',
        'specialty_format': '相關專科：',
        'severity_format': '嚴重程度：',
        'emergency_format': '緊急程度：',
        'advice_format': '資訊：',
        'disclaimer': '免責聲明：此分析僅供參考，不構成醫療建議或診斷，請務必諮詢合格醫生。'
    },
    
    'zh-CN': {
        # Header and Navigation
        'app_title': 'AI香港医疗配对系统',
        'main_title': 'Doctor AI.io',
        'subtitle': '免费AI症状分析平台',
        'back_to_website': '返回主页',
        'admin_panel': '管理后台',
        
        # Form Labels
        'patient_info': '病人资料',
        'age': '年龄',
        'symptoms': '症状描述',
        'symptoms_note': '(至少需要3个症状)',
        'symptoms_placeholder': '请详细描述您的症状，例如：头痛、发烧、咳嗽、疲劳等（至少3个症状以便AI准确分析）',
        'symptoms_hint': '请尽量详细描述症状，包括持续时间、严重程度等',
        'chronic_conditions': '长期病史',
        'optional': '(可选)',
        'chronic_hint': '可选择多项，如无长期病史可不选',
        'preferred_language': '偏好语言',
        'gender': '生理性别',
        'male': '男性',
        'female': '女性',
        'location': '所在地区',
        'select_region': '请选择大区',
        'select_district': '请选择地区',
        'select_area': '请选择具体位置 (可选)',
        'find_doctor': '寻找合适医生',
        
        # More Info Section
        'more_info': '更多资料',
        'detailed_health_info': '详细健康资料',
        'detailed_info_desc': '以下资料可协助AI更精准地分析您的病情',
        'height': '身高 (cm)',
        'weight': '体重 (kg)',
        'medications': '有服用任何长期药物吗？ 如有，请提供药物种类名称。',
        'allergies': '有食物/药物敏感吗？ 如有，请提供',
        'surgeries': '请问客人曾经有做过手术？如有，请提供',
        'blood_thinner': '有服薄血药吗？',
        'recent_visit': '三个月内有否就诊？',
        'cpap_machine': '睡觉时需要用呼吸机吗？',
        'loose_teeth': '有没有已知，但未处理的松牙？',
        
        # Chronic Conditions
        'high_blood_pressure': '血压高',
        'diabetes': '糖尿病',
        'high_cholesterol': '胆固醇高',
        'heart_disease': '心脏病',
        'stroke': '中风',
        'asthma': '哮喘',
        'chronic_lung_disease': '慢性肺病',
        'hepatitis_b': '乙型肝炎',
        'other_conditions': '其他长期疾病',
        'other_conditions_placeholder': '请输入其他长期疾病',
        
        # Languages
        'cantonese': '广东话',
        'english': '英语',
        'mandarin': '普通话',
        'french': '法语',
        
        # Regions
        'hong_kong_island': '香港岛',
        'kowloon': '九龙',
        'new_territories': '新界',
        
        # Loading and Results
        'loading_message': 'AI正在分析您的症状并配对合适的医生...',
        'recommended_doctors': 'AI症状分析结果',
        
        # Footer
        'terms_conditions': '条款及细则',
        'privacy_policy': '隐私权政策',
        'accessibility': '无障碍声明',
        'copyright': '2025 XENOVATIVE Limited. 版权所有',
        
        # Admin Panel
        'dashboard': '仪表板',
        'analytics': '分析报告',
        'system_config': '系统配置',
        'user_management': '用户管理',
        'view_website': '查看网站',
        'logout': '登出',
        
        # Language Toggle
        'language_toggle': '语言',
        'switch_language': '切换语言',
        
        # Missing UI translations
        'select_language': '请选择语言',
        'select_region': '请选择大区',
        'select_district': '请选择地区',
        'select_area': '请选择具体位置 (可选)',
        
        # Region translations
        '香港島': '香港岛',
        '九龍': '九龙', 
        '新界': '新界',
        
        # Dynamic UI elements
        'more_info': '更多资料',
        'less_info': '收起资料',
        'show_more_doctors': '显示更多医生',
        'recommended_doctors': 'AI症状分析结果',
        'doctor_list_header': '医生列表',
        'no_doctors_found': '抱歉，未能找到合适的医生。请尝试修改搜索条件。',
        'service_unavailable': '服务暂时不可用',
        'ai_diagnosis_unavailable': 'AI症状分析暂时不可用',
        'ai_diagnosis_unavailable_desc': '我们的AI症状分析服务暂时无法使用，但您仍可以查看相关的医生资讯。请直接咨询医疗专业人士。',
        
        # User summary and diagnosis cards
        'user_health_summary': '您的健康资料摘要',
        'ai_diagnosis_analysis': 'AI 智能症状分析',
        'recommended_specialty': '相关专科资讯',
        'age_years': '年龄',
        'main_symptoms': '主要症状',
        'body_info': '身高体重',
        'years_old_suffix': '岁',
        'height_weight_format': 'cm / kg (BMI: )',
        'important_reminder': '重要提醒：',
        'ai_disclaimer': '此AI分析仅供参考，不构成医疗建议或诊断。请务必咨询合格医生进行专业评估。',
        
        # Medical Specialties
        '內科': '内科',
        '外科': '外科', 
        '兒科': '儿科',
        '婦產科': '妇产科',
        '眼科': '眼科',
        '耳鼻喉科': '耳鼻喉科',
        '皮膚科': '皮肤科',
        '骨科': '骨科',
        '神經科': '神经科',
        '心臟科': '心脏科',
        '泌尿科': '泌尿科',
        '腸胃科': '肠胃科',
        '精神科': '精神科',
        '急診科': '急诊科',
        '家庭醫學科': '家庭医学科',
        '普通科': '普通科',
        '呼吸科': '呼吸科',
        '腎臟科': '肾脏科',
        '內分泌科': '内分泌科',
        '風濕免疫科': '风湿免疫科',
        '血液科': '血液科',
        '腫瘤科': '肿瘤科',
        '復健科': '康复科',
        '麻醉科': '麻醉科',
        '放射科': '放射科',
        '病理科': '病理科',
        '核醫科': '核医科',
        '職業醫學科': '职业医学科',
        '預防醫學科': '预防医学科',
        
        # Doctor Card Labels
        'recommendation_rank': '',
        'recommendation_suffix': '',
        'click_to_contact': '点击联络',
        'language_label': '语言：',
        'phone_label': '电话：',
        'email_label': '电邮：',
        'clinic_address_label': '诊所地址：',
        'qualifications_label': '专业资格：',
        'not_provided': '未提供',
        'unknown_doctor': '未知医生',
        'general_specialist': '专科医生',
        'emergency_care_needed': '🚨 可能需要紧急医疗关注',
        'urgent_consultation': '可能需要紧急医疗咨询',
        
        # AI Disclaimer Modal
        'ai_disclaimer_title': 'Doctor-AI.io 医疗配对系统声明',
        'not_medical_advice_title': '⚠️ 非医疗建议',
        'not_medical_advice_desc': '本系统仅为AI辅助工具，提供的资讯和建议不构成专业医疗建议、诊断或治疗。所有医疗决定应咨询合格的医疗专业人员。',
        'ai_limitations_title': '🤖 AI系统限制',
        'ai_limitations_desc': 'AI分析基于您提供的症状描述，可能存在误差或遗漏。系统无法替代医生的专业判断和实际检查。',
        'doctor_matching_title': '👨‍⚕️ 医生配对服务',
        'doctor_matching_desc': '本系统协助您找到合适的医疗专业人员，但最终的医疗服务质量取决于个别医生和诊所。我们不对医疗结果承担责任。',
        'emergency_notice_title': '🚨 紧急情况',
        'emergency_notice_desc': '如遇紧急医疗情况，请立即拨打999或前往最近的急诊室，切勿依赖本系统进行紧急医疗决定。',
        'disclaimer_agreement': '继续使用本系统即表示您已理解并同意以上声明。',
        'understand_continue': '我已理解，继续使用',
        
        # Location translations - Districts
        '中西區': '中西区',
        '東區': '东区', 
        '南區': '南区',
        '灣仔區': '湾仔区',
        '九龍城區': '九龙城区',
        '觀塘區': '观塘区',
        '深水埗區': '深水埗区',
        '黃大仙區': '黄大仙区',
        '油尖旺區': '油尖旺区',
        '離島區': '离岛区',
        '葵青區': '葵青区',
        '北區': '北区',
        '西貢區': '西贡区',
        '沙田區': '沙田区',
        '大埔區': '大埔区',
        '荃灣區': '荃湾区',
        '屯門區': '屯门区',
        '元朗區': '元朗区',
        
        # Geolocation messages
        'geolocation_auto_selected': '已自动选择您附近的地区',
        'geolocation_permission_denied': '位置权限被拒绝，请手动选择地区',
        'geolocation_unavailable': '位置信息不可用，请手动选择地区',
        'geolocation_timeout': '获取位置超时，请手动选择地区',
        'geolocation_error': '无法获取您的位置',

        # Location translations - Areas
        '中環': '中环', '上環': '上环', '西環': '西环', '金鐘': '金钟', '堅尼地城': '坚尼地城', '石塘咀': '石塘咀', '西營盤': '西营盘',
        '銅鑼灣': '铜锣湾', '天后': '天后', '炮台山': '炮台山', '北角': '北角', '鰂魚涌': '鲗鱼涌', '西灣河': '西湾河', '筲箕灣': '筲箕湾', '柴灣': '柴湾', '小西灣': '小西湾',
        '香港仔': '香港仔', '鴨脷洲': '鸭脷洲', '黃竹坑': '黄竹坑', '深水灣': '深水湾', '淺水灣': '浅水湾', '赤柱': '赤柱', '石澳': '石澳',
        '灣仔': '湾仔', '跑馬地': '跑马地', '大坑': '大坑', '渣甸山': '渣甸山', '寶馬山': '宝马山',
        '九龍城': '九龙城', '土瓜灣': '土瓜湾', '馬頭角': '马头角', '馬頭圍': '马头围', '啟德': '启德', '紅磡': '红磡', '何文田': '何文田',
        '觀塘': '观塘', '牛頭角': '牛头角', '九龍灣': '九龙湾', '彩虹': '彩虹', '坪石': '坪石', '秀茂坪': '秀茂坪', '藍田': '蓝田', '油塘': '油塘',
        '深水埗': '深水埗', '長沙灣': '长沙湾', '荔枝角': '荔枝角', '美孚': '美孚', '石硤尾': '石硖尾', '又一村': '又一村',
        '黃大仙': '黄大仙', '新蒲崗': '新蒲岗', '樂富': '乐富', '橫頭磡': '横头磡', '東頭': '东头', '竹園': '竹园', '慈雲山': '慈云山', '鑽石山': '钻石山',
        '油麻地': '油麻地', '尖沙咀': '尖沙咀', '旺角': '旺角', '大角咀': '大角咀', '太子': '太子', '佐敦': '佐敦',
        '長洲': '长洲', '南丫島': '南丫岛', '坪洲': '坪洲', '大嶼山': '大屿山', '東涌': '东涌', '愉景灣': '愉景湾',
        '葵涌': '葵涌', '青衣': '青衣', '葵芳': '葵芳', '荔景': '荔景',
        '上水': '上水', '粉嶺': '粉岭', '打鼓嶺': '打鼓岭', '沙頭角': '沙头角', '鹿頸': '鹿颈',
        '西貢': '西贡', '將軍澳': '将军澳', '坑口': '坑口', '調景嶺': '调景岭', '寶林': '宝林', '康盛花園': '康盛花园',
        '沙田': '沙田', '大圍': '大围', '火炭': '火炭', '馬鞍山': '马鞍山', '烏溪沙': '乌溪沙',
        '大埔': '大埔', '太和': '太和', '大埔墟': '大埔墟', '林村': '林村', '汀角': '汀角',
        '荃灣': '荃湾', '梨木樹': '梨木树', '象山': '象山', '城門': '城门',
        '屯門': '屯门', '友愛': '友爱', '安定': '安定', '山景': '山景', '大興': '大兴', '良景': '良景', '建生': '建生',
        '元朗': '元朗', '天水圍': '天水围', '洪水橋': '洪水桥', '流浮山': '流浮山', '錦田': '锦田', '八鄉': '八乡',
        
        # AI Analysis Prompts
        'diagnosis_prompt_intro': '作为一名经验丰富的医疗专家，请根据以下病人资料进行初步病征分析：',
        'patient_data': '病人资料：',
        'age_label': '年龄：',
        'main_symptoms': '主要症状：',
        'years_old': '岁',
        'no_special_health_info': '无特殊健康信息',
        'please_provide': '请提供：',
        'possible_diagnosis': '可能的病症分析（最多3个可能性，按可能性排序）',
        'recommended_specialty': '建议就诊的专科',
        'severity_assessment': '症状严重程度评估（轻微/中等/严重）',
        'emergency_needed': '是否需要紧急就医',
        'general_advice': '一般建议和注意事项',
        'important_guidelines': '重要指引：',
        'mental_health_guideline': '只有在明确涉及精神健康问题（如精神崩溃、妄想、幻觉、自杀念头、严重抑郁/焦虑、恐慌症等）时，才推荐精神科。单纯的身体症状（如头痛、头晕、食欲不振）应优先考虑相关的身体专科',
        'trauma_guideline': '如涉及心理创伤、PTSD、情绪失控等，应推荐精神科而非内科',
        'emergency_guideline': '如症状涉及急性或危及生命情况，应推荐急诊科',
        'specialty_guideline': '根据症状的主要系统选择最适合的专科，避免一律推荐内科',
        'response_language': '请用简体中文回答。所有病征分析结果、建议和医疗术语都必须使用简体中文。回答格式如下：',
        'diagnosis_format': '可能病征：',
        'specialty_format': '建议专科：',
        'severity_format': '严重程度：',
        'emergency_format': '紧急程度：',
        'advice_format': '建议：',
        'disclaimer': '免责声明：此分析仅供参考，不能替代专业医疗病征分析，请务必咨询合格医生。'
    },
    
    'en': {
        # Header and Navigation
        'app_title': 'AI Hong Kong Medical Matching System',
        'main_title': 'Doctor AI.io',
        'subtitle': 'Free AI Symptom Analysis Platform',
        'back_to_website': 'Back to Homepage',
        'admin_panel': 'Admin Panel',
        
        # Form Labels
        'patient_info': 'Patient Information',
        'age': 'Age',
        'symptoms': 'Symptom Description',
        'symptoms_note': '(At least 3 symptoms required)',
        'symptoms_placeholder': 'Please describe your symptoms in detail, e.g.: headache, fever, cough, fatigue, etc. (at least 3 symptoms for accurate AI analysis)',
        'symptoms_hint': 'Select or enter symptoms, at least 3 symptoms required for accurate AI analysis',
        'symptom_input_placeholder': 'Enter symptoms and press Enter to add...',
        'height_placeholder': 'e.g.: 170',
        'weight_placeholder': 'e.g.: 65',
        'medications_placeholder': 'e.g.: blood pressure medication, diabetes medication, etc.',
        'allergies_placeholder': 'e.g.: peanuts, penicillin, etc.',
        'surgeries_placeholder': 'e.g.: appendectomy, 2020, etc.',
        'chronic_conditions': 'Medical History',
        'optional': '(Optional)',
        'chronic_hint': 'Multiple selections allowed, leave blank if no medical history',
        'preferred_language': 'Preferred Language',
        'gender': 'Biological Sex',
        'male': 'Male',
        'female': 'Female',
        'location': 'Location',
        'select_region': 'Please select region',
        'select_district': 'Please select district',
        'select_area': 'Please select specific area (optional)',
        'find_doctor': 'Find Suitable Doctor',
        
        # More Info Section
        'more_info': 'More Information',
        'detailed_health_info': 'Detailed Health Information',
        'detailed_info_desc': 'The following information can help AI analyze your condition more accurately',
        'height': 'Height (cm)',
        'weight': 'Weight (kg)',
        'medications': 'Are you taking any long-term medications? If yes, please provide medication types.',
        'allergies': 'Do you have any food/drug allergies? If yes, please provide details',
        'surgeries': 'Have you had any surgeries? If yes, please provide details',
        'blood_thinner': 'Are you taking blood thinners?',
        'recent_visit': 'Have you visited a doctor in the past 3 months?',
        'cpap_machine': 'Do you use a CPAP machine while sleeping?',
        'loose_teeth': 'Do you have any known untreated loose teeth?',
        
        # Chronic Conditions
        'high_blood_pressure': 'High Blood Pressure',
        'diabetes': 'Diabetes',
        'high_cholesterol': 'High Cholesterol',
        'heart_disease': 'Heart Disease',
        'stroke': 'Stroke',
        'asthma': 'Asthma',
        'chronic_lung_disease': 'Chronic Lung Disease',
        'hepatitis_b': 'Hepatitis B',
        'other_conditions': 'Other Chronic Conditions',
        'other_conditions_placeholder': 'Please enter other chronic conditions',
        
        # Languages
        'cantonese': 'Cantonese',
        'english': 'English',
        'mandarin': 'Mandarin',
        'french': 'French',
        
        # Regions
        'hong_kong_island': 'Hong Kong Island',
        'kowloon': 'Kowloon',
        'new_territories': 'New Territories',
        
        # Loading and Results
        'loading_message': 'AI is analyzing your symptoms and matching suitable doctors...',
        'recommended_doctors': 'AI Symptom Analysis Results',
        
        # Footer
        'terms_conditions': 'Terms & Conditions',
        'privacy_policy': 'Privacy Policy',
        'accessibility': 'Accessibility Statement',
        'copyright': '2025 XENOVATIVE Limited. All rights reserved',
        
        # Admin Panel
        'dashboard': 'Dashboard',
        'analytics': 'Analytics',
        'system_config': 'System Configuration',
        'user_management': 'User Management',
        'view_website': 'View Website',
        'logout': 'Logout',
        
        # Language Toggle
        'language_toggle': 'Language',
        'switch_language': 'Switch Language',
        
        # Missing UI translations
        'select_language': 'Please select language',
        'select_region': 'Please select region',
        'select_district': 'Please select district',
        'select_area': 'Please select specific area (optional)',
        
        # Region translations
        '香港島': 'Hong Kong Island',
        '九龍': 'Kowloon', 
        '新界': 'New Territories',
        
        # Dynamic UI elements
        'more_info': 'More Information',
        'less_info': 'Less Information',
        'show_more_doctors': 'Show More Doctors',
        'recommended_doctors': 'AI Symptom Analysis Results',
        'doctor_list_header': 'Doctor List',
        'no_doctors_found': 'Sorry, no suitable doctors found. Please try modifying your search criteria.',
        'service_unavailable': 'Service Temporarily Unavailable',
        'ai_diagnosis_unavailable': 'AI Symptom Analysis Temporarily Unavailable',
        'ai_diagnosis_unavailable_desc': 'Our AI symptom analysis service is temporarily unavailable, but you can still view recommended doctors. We suggest consulting medical professionals directly.',
        
        # User summary and diagnosis cards
        'user_health_summary': 'Your Health Information Summary',
        'ai_diagnosis_analysis': 'AI Symptom Analysis',
        'recommended_specialty': 'Recommended Specialty',
        'age_years': 'Age',
        'main_symptoms': 'Main Symptoms',
        'body_info': 'Height & Weight',
        'years_old_suffix': ' years old',
        'height_weight_format': 'cm / kg (BMI: )',
        'important_reminder': 'Important Reminder:',
        'ai_disclaimer': 'This AI analysis is for reference only and cannot replace professional medical symptom analysis. Please consult a qualified physician for formal symptom analysis.',
        
        # Medical Specialties
        '內科': 'Internal Medicine',
        '外科': 'Surgery', 
        '兒科': 'Pediatrics',
        '婦產科': 'Obstetrics & Gynecology',
        '眼科': 'Ophthalmology',
        '耳鼻喉科': 'Otolaryngology (ENT)',
        '皮膚科': 'Dermatology',
        '骨科': 'Orthopedics',
        '神經科': 'Neurology',
        '心臟科': 'Cardiology',
        '泌尿科': 'Urology',
        '腸胃科': 'Gastroenterology',
        '精神科': 'Psychiatry',
        '急診科': 'Emergency Medicine',
        '家庭醫學科': 'Family Medicine',
        '普通科': 'General Practice',
        '呼吸科': 'Pulmonology',
        '腎臟科': 'Nephrology',
        '內分泌科': 'Endocrinology',
        '風濕免疫科': 'Rheumatology',
        '血液科': 'Hematology',
        '腫瘤科': 'Oncology',
        '復健科': 'Physical Medicine & Rehabilitation',
        '麻醉科': 'Anesthesiology',
        '放射科': 'Radiology',
        '病理科': 'Pathology',
        '核醫科': 'Nuclear Medicine',
        '職業醫學科': 'Occupational Medicine',
        '預防醫學科': 'Preventive Medicine',
        
        # Doctor Card Labels
        'recommendation_rank': '',
        'recommendation_suffix': '',
        'click_to_contact': 'Click to Contact',
        'language_label': 'Languages: ',
        'phone_label': 'Phone: ',
        'email_label': 'Email: ',
        'clinic_address_label': 'Clinic Address: ',
        'qualifications_label': 'Qualifications: ',
        'not_provided': 'Not Provided',
        'unknown_doctor': 'Unknown Doctor',
        'general_specialist': 'General Practitioner',
        'emergency_care_needed': '🚨 Emergency Care Recommended',
        'urgent_consultation': 'Urgent Medical Consultation Required',
        
        # AI Disclaimer Modal
        'ai_disclaimer_title': 'Doctor-AI.io Medical Matching System Disclaimer',
        'not_medical_advice_title': '⚠️ Not Medical Advice',
        'not_medical_advice_desc': 'This system is an AI-assisted tool only. The information and recommendations provided do not constitute professional medical advice, diagnosis, or treatment. All medical decisions should be made in consultation with qualified healthcare professionals.',
        'ai_limitations_title': '🤖 AI System Limitations',
        'ai_limitations_desc': 'AI analysis is based on the symptom descriptions you provide and may contain errors or omissions. The system cannot replace a doctor\'s professional judgment and physical examination.',
        'doctor_matching_title': '👨‍⚕️ Doctor Matching Service',
        'doctor_matching_desc': 'This system helps you find suitable healthcare professionals, but the quality of medical services ultimately depends on individual doctors and clinics. We are not responsible for medical outcomes.',
        'emergency_notice_title': '🚨 Emergency Situations',
        'emergency_notice_desc': 'In case of medical emergencies, please immediately call 999 or go to the nearest emergency room. Do not rely on this system for emergency medical decisions.',
        'disclaimer_agreement': 'By continuing to use this system, you acknowledge that you have read and agree to the above disclaimer.',
        'understand_continue': 'I Understand, Continue',
        
        # Geolocation messages
        'geolocation_auto_selected': 'Automatically selected nearby area',
        'geolocation_permission_denied': 'Location permission denied, please select area manually',
        'geolocation_unavailable': 'Location information unavailable, please select area manually',
        'geolocation_timeout': 'Location request timed out, please select area manually',
        'geolocation_error': 'Unable to get your location',

        # Location translations - Districts
        '中西區': 'Central and Western District',
        '東區': 'Eastern District', 
        '南區': 'Southern District',
        '灣仔區': 'Wan Chai District',
        '九龍城區': 'Kowloon City District',
        '觀塘區': 'Kwun Tong District',
        '深水埗區': 'Sham Shui Po District',
        '黃大仙區': 'Wong Tai Sin District',
        '油尖旺區': 'Yau Tsim Mong District',
        '離島區': 'Islands District',
        '葵青區': 'Kwai Tsing District',
        '北區': 'North District',
        '西貢區': 'Sai Kung District',
        '沙田區': 'Sha Tin District',
        '大埔區': 'Tai Po District',
        '荃灣區': 'Tsuen Wan District',
        '屯門區': 'Tuen Mun District',
        '元朗區': 'Yuen Long District',
        
        # Location translations - Areas
        '中環': 'Central', '上環': 'Sheung Wan', '西環': 'Sai Wan', '金鐘': 'Admiralty', '堅尼地城': 'Kennedy Town', '石塘咀': 'Shek Tong Tsui', '西營盤': 'Sai Ying Pun',
        '銅鑼灣': 'Causeway Bay', '天后': 'Tin Hau', '炮台山': 'Fortress Hill', '北角': 'North Point', '鰂魚涌': 'Quarry Bay', '西灣河': 'Sai Wan Ho', '筲箕灣': 'Shau Kei Wan', '柴灣': 'Chai Wan', '小西灣': 'Siu Sai Wan',
        '香港仔': 'Aberdeen', '鴨脷洲': 'Ap Lei Chau', '黃竹坑': 'Wong Chuk Hang', '深水灣': 'Deep Water Bay', '淺水灣': 'Repulse Bay', '赤柱': 'Stanley', '石澳': 'Shek O',
        '灣仔': 'Wan Chai', '跑馬地': 'Happy Valley', '大坑': 'Tai Hang', '渣甸山': 'Jardine\'s Lookout', '寶馬山': 'Braemar Hill',
        '九龍城': 'Kowloon City', '土瓜灣': 'To Kwa Wan', '馬頭角': 'Ma Tau Kok', '馬頭圍': 'Ma Tau Wai', '啟德': 'Kai Tak', '紅磡': 'Hung Hom', '何文田': 'Ho Man Tin',
        '觀塘': 'Kwun Tong', '牛頭角': 'Ngau Tau Kok', '九龍灣': 'Kowloon Bay', '彩虹': 'Choi Hung', '坪石': 'Ping Shek', '秀茂坪': 'Sau Mau Ping', '藍田': 'Lam Tin', '油塘': 'Yau Tong',
        '深水埗': 'Sham Shui Po', '長沙灣': 'Cheung Sha Wan', '荔枝角': 'Lai Chi Kok', '美孚': 'Mei Foo', '石硤尾': 'Shek Kip Mei', '又一村': 'Yau Yat Chuen',
        '黃大仙': 'Wong Tai Sin', '新蒲崗': 'San Po Kong', '樂富': 'Lok Fu', '橫頭磡': 'Wang Tau Hom', '東頭': 'Tung Tau', '竹園': 'Chuk Yuen', '慈雲山': 'Tsz Wan Shan', '鑽石山': 'Diamond Hill',
        '油麻地': 'Yau Ma Tei', '尖沙咀': 'Tsim Sha Tsui', '旺角': 'Mong Kok', '大角咀': 'Tai Kok Tsui', '太子': 'Prince Edward', '佐敦': 'Jordan',
        '長洲': 'Cheung Chau', '南丫島': 'Lamma Island', '坪洲': 'Peng Chau', '大嶼山': 'Lantau Island', '東涌': 'Tung Chung', '愉景灣': 'Discovery Bay',
        '葵涌': 'Kwai Chung', '青衣': 'Tsing Yi', '葵芳': 'Kwai Fong', '荔景': 'Lai King',
        '上水': 'Sheung Shui', '粉嶺': 'Fanling', '打鼓嶺': 'Ta Kwu Ling', '沙頭角': 'Sha Tau Kok', '鹿頸': 'Luk Keng',
        '西貢': 'Sai Kung', '將軍澳': 'Tseung Kwan O', '坑口': 'Hang Hau', '調景嶺': 'Tiu Keng Leng', '寶林': 'Po Lam', '康盛花園': 'Hong Sing Garden',
        '沙田': 'Sha Tin', '大圍': 'Tai Wai', '火炭': 'Fo Tan', '馬鞍山': 'Ma On Shan', '烏溪沙': 'Wu Kai Sha',
        '大埔': 'Tai Po', '太和': 'Tai Wo', '大埔墟': 'Tai Po Market', '林村': 'Lam Tsuen', '汀角': 'Ting Kok',
        '荃灣': 'Tsuen Wan', '梨木樹': 'Lei Muk Shue', '象山': 'Cheung Shan', '城門': 'Shing Mun',
        '屯門': 'Tuen Mun', '友愛': 'Yau Oi', '安定': 'On Ting', '山景': 'Shan King', '大興': 'Tai Hing', '良景': 'Leung King', '建生': 'Kin Sang',
        '元朗': 'Yuen Long', '天水圍': 'Tin Shui Wai', '洪水橋': 'Hung Shui Kiu', '流浮山': 'Lau Fau Shan', '錦田': 'Kam Tin', '八鄉': 'Pat Heung',
        
        # AI Diagnosis Prompts
        'diagnosis_prompt_intro': 'As an experienced medical expert, please provide a preliminary diagnostic analysis based on the following patient information:',
        'patient_data': 'Patient Information:',
        'age_label': 'Age:',
        'main_symptoms': 'Main Symptoms:',
        'years_old': 'years old',
        'no_special_health_info': 'No special health information',
        'please_provide': 'Please provide:',
        'possible_diagnosis': 'Possible diagnoses (up to 3 possibilities, ranked by likelihood)',
        'recommended_specialty': 'Recommended medical specialty',
        'severity_assessment': 'Symptom severity assessment (Mild/Moderate/Severe)',
        'emergency_needed': 'Whether emergency medical attention is needed',
        'general_advice': 'General recommendations and precautions',
        'important_guidelines': 'Important Guidelines:',
        'mental_health_guideline': 'Only recommend psychiatry when there are clear mental health issues (such as mental breakdown, delusions, hallucinations, suicidal thoughts, severe depression/anxiety, panic disorders). Pure physical symptoms (like headache, dizziness, loss of appetite) should prioritize relevant physical specialties',
        'trauma_guideline': 'For psychological trauma, PTSD, emotional dysregulation, psychiatry should be recommended rather than internal medicine',
        'emergency_guideline': 'For acute or life-threatening symptoms, emergency department should be recommended',
        'specialty_guideline': 'Select the most appropriate specialty based on the main system involved, avoid defaulting to internal medicine',
        'response_language': 'Please respond in English. All diagnosis results, recommendations, and medical terminology must be in English. Response format:',
        'diagnosis_format': 'Possible Diagnoses:',
        'specialty_format': 'Recommended Specialty:',
        'severity_format': 'Severity:',
        'emergency_format': 'Emergency:',
        'advice_format': 'Recommendations:',
        'disclaimer': 'Disclaimer: This analysis is for reference only and cannot replace professional medical diagnosis. Please consult a qualified physician.'
    }
}

def get_translation(key, lang='zh-TW'):
    """Get translation for a given key and language"""
    return TRANSLATIONS.get(lang, {}).get(key, TRANSLATIONS['zh-TW'].get(key, key))

def get_available_languages():
    """Get list of available languages"""
    return [
        {'code': 'zh-TW', 'name': '繁體中文', 'flag': '🇭🇰'},
        {'code': 'zh-CN', 'name': '简体中文', 'flag': '🇨🇳'},
        {'code': 'en', 'name': 'English', 'flag': '🇺🇸'}
    ]
