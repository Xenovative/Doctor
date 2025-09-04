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
        'subtitle': '免費AI診症平台',
        'back_to_website': '返回主頁',
        'admin_panel': '管理後台',
        
        # Form Labels
        'patient_info': '病人資料',
        'age': '年齡',
        'symptoms': '症狀描述',
        'symptoms_note': '(至少需要3個症狀)',
        'symptoms_placeholder': '請詳細描述您的症狀，例如：頭痛、發燒、咳嗽、疲勞等（至少3個症狀以便AI準確分析）',
        'symptoms_hint': '請盡量詳細描述症狀，包括持續時間、嚴重程度等',
        'chronic_conditions': '長期病史',
        'optional': '(可選)',
        'chronic_hint': '可選擇多項，如無長期病史可不選',
        'preferred_language': '偏好語言',
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
        'recommended_doctors': '推薦醫生',
        
        # Footer
        'terms_conditions': '條款及細則',
        'privacy_policy': '隱私權政策',
        'accessibility': '無障礙聲明',
        'copyright': '2025 XENOVATIVE Limited. 版權所有',
        
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
        
        # AI Diagnosis Prompts
        'diagnosis_prompt_intro': '作為一名經驗豐富的醫療專家，請根據以下病人資料進行初步診斷分析：',
        'patient_data': '病人資料：',
        'age_label': '年齡：',
        'main_symptoms': '主要症狀：',
        'years_old': '歲',
        'no_special_health_info': '無特殊健康信息',
        'please_provide': '請提供：',
        'possible_diagnosis': '可能的病症診斷（最多3個可能性，按可能性排序）',
        'recommended_specialty': '建議就診的專科',
        'severity_assessment': '症狀嚴重程度評估（輕微/中等/嚴重）',
        'emergency_needed': '是否需要緊急就醫',
        'general_advice': '一般建議和注意事項',
        'important_guidelines': '重要指引：',
        'mental_health_guideline': '如涉及精神健康問題（如精神崩潰、妄想、幻覺、自殺念頭、嚴重抑鬱/焦慮等），必須推薦精神科',
        'trauma_guideline': '如涉及心理創傷、PTSD、情緒失控等，應推薦精神科而非內科',
        'emergency_guideline': '如症狀涉及急性或危及生命情況，應推薦急診科',
        'specialty_guideline': '根據症狀的主要系統選擇最適合的專科，避免一律推薦內科',
        'response_language': '請用繁體中文回答，格式如下：',
        'diagnosis_format': '可能診斷：',
        'specialty_format': '建議專科：',
        'severity_format': '嚴重程度：',
        'emergency_format': '緊急程度：',
        'advice_format': '建議：',
        'disclaimer': '免責聲明：此分析僅供參考，不能替代專業醫療診斷，請務必諮詢合格醫生。'
    },
    
    'zh-CN': {
        # Header and Navigation
        'app_title': 'AI香港医疗配对系统',
        'main_title': 'Doctor AI.io',
        'subtitle': '免费AI诊症平台',
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
        'recommended_doctors': '推荐医生',
        
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
        
        # AI Diagnosis Prompts
        'diagnosis_prompt_intro': '作为一名经验丰富的医疗专家，请根据以下病人资料进行初步诊断分析：',
        'patient_data': '病人资料：',
        'age_label': '年龄：',
        'main_symptoms': '主要症状：',
        'years_old': '岁',
        'no_special_health_info': '无特殊健康信息',
        'please_provide': '请提供：',
        'possible_diagnosis': '可能的病症诊断（最多3个可能性，按可能性排序）',
        'recommended_specialty': '建议就诊的专科',
        'severity_assessment': '症状严重程度评估（轻微/中等/严重）',
        'emergency_needed': '是否需要紧急就医',
        'general_advice': '一般建议和注意事项',
        'important_guidelines': '重要指引：',
        'mental_health_guideline': '如涉及精神健康问题（如精神崩溃、妄想、幻觉、自杀念头、严重抑郁/焦虑等），必须推荐精神科',
        'trauma_guideline': '如涉及心理创伤、PTSD、情绪失控等，应推荐精神科而非内科',
        'emergency_guideline': '如症状涉及急性或危及生命情况，应推荐急诊科',
        'specialty_guideline': '根据症状的主要系统选择最适合的专科，避免一律推荐内科',
        'response_language': '请用简体中文回答，格式如下：',
        'diagnosis_format': '可能诊断：',
        'specialty_format': '建议专科：',
        'severity_format': '严重程度：',
        'emergency_format': '紧急程度：',
        'advice_format': '建议：',
        'disclaimer': '免责声明：此分析仅供参考，不能替代专业医疗诊断，请务必咨询合格医生。'
    },
    
    'en': {
        # Header and Navigation
        'app_title': 'AI Hong Kong Medical Matching System',
        'main_title': 'Doctor AI.io',
        'subtitle': 'Free AI Diagnosis Platform',
        'back_to_website': 'Back to Homepage',
        'admin_panel': 'Admin Panel',
        
        # Form Labels
        'patient_info': 'Patient Information',
        'age': 'Age',
        'symptoms': 'Symptom Description',
        'symptoms_note': '(At least 3 symptoms required)',
        'symptoms_placeholder': 'Please describe your symptoms in detail, e.g.: headache, fever, cough, fatigue, etc. (at least 3 symptoms for accurate AI analysis)',
        'symptoms_hint': 'Please describe symptoms in detail, including duration and severity',
        'chronic_conditions': 'Medical History',
        'optional': '(Optional)',
        'chronic_hint': 'Multiple selections allowed, leave blank if no medical history',
        'preferred_language': 'Preferred Language',
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
        'recommended_doctors': 'Recommended Doctors',
        
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
        'mental_health_guideline': 'For mental health issues (such as mental breakdown, delusions, hallucinations, suicidal thoughts, severe depression/anxiety), psychiatry must be recommended',
        'trauma_guideline': 'For psychological trauma, PTSD, emotional dysregulation, psychiatry should be recommended rather than internal medicine',
        'emergency_guideline': 'For acute or life-threatening symptoms, emergency department should be recommended',
        'specialty_guideline': 'Select the most appropriate specialty based on the main system involved, avoid defaulting to internal medicine',
        'response_language': 'Please respond in English, using the following format:',
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
