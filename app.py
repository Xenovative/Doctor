from flask import Flask, render_template, request, jsonify
import pandas as pd
import requests
import json
import os
from typing import List, Dict, Any

app = Flask(__name__)

# AI服務配置
AI_CONFIG = {
    'provider': os.getenv('AI_PROVIDER', 'ollama'),  # 'ollama' or 'openrouter'
    'openrouter': {
        'api_key': os.getenv('OPENROUTER_API_KEY', ''),
        'base_url': 'https://openrouter.ai/api/v1/chat/completions',
        'model': os.getenv('OPENROUTER_MODEL', 'anthropic/claude-3.5-sonnet'),
        'max_tokens': int(os.getenv('OPENROUTER_MAX_TOKENS', '4000'))
    },
    'ollama': {
        'base_url': 'http://localhost:11434/api/generate',
        'model': os.getenv('OLLAMA_MODEL', 'llama3.1:8b')
    }
}

# 載入醫生資料
def load_doctors_data():
    """載入醫生資料"""
    csv_path = os.path.join('assets', 'finddoc_doctors_detailed 2.csv')
    try:
        print(f"正在載入醫生資料: {csv_path}")
        if not os.path.exists(csv_path):
            print(f"警告: CSV文件不存在: {csv_path}")
            return []
        
        df = pd.read_csv(csv_path)
        print(f"成功載入 {len(df)} 位醫生資料")
        return df.to_dict('records')
    except Exception as e:
        print(f"載入醫生資料時發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return []

# 全局變數存儲醫生資料 - 延遲載入以避免啟動時掛起
DOCTORS_DATA = []

def get_doctors_data():
    """獲取醫生資料，支援延遲載入"""
    global DOCTORS_DATA
    if not DOCTORS_DATA:
        print("延遲載入醫生資料...")
        DOCTORS_DATA = load_doctors_data()
    return DOCTORS_DATA

def generate_user_summary(age: int, symptoms: str, chronic_conditions: str, detailed_health_info: Dict) -> str:
    """生成用戶輸入數據摘要"""
    summary_parts = []
    
    # 基本信息
    summary_parts.append(f"年齡：{age}歲")
    summary_parts.append(f"主要症狀：{symptoms}")
    
    # 長期病史
    if chronic_conditions:
        summary_parts.append(f"長期病史：{chronic_conditions}")
    
    # 身體指標
    if detailed_health_info.get('height') or detailed_health_info.get('weight'):
        height = detailed_health_info.get('height', '')
        weight = detailed_health_info.get('weight', '')
        if height and weight:
            bmi = round(float(weight) / ((float(height) / 100) ** 2), 1) if height and weight else None
            summary_parts.append(f"身高體重：{height}cm / {weight}kg" + (f" (BMI: {bmi})" if bmi else ""))
        elif height:
            summary_parts.append(f"身高：{height}cm")
        elif weight:
            summary_parts.append(f"體重：{weight}kg")
    
    # 藥物信息
    if detailed_health_info.get('medications'):
        summary_parts.append(f"長期藥物：{detailed_health_info['medications']}")
    
    # 敏感史
    if detailed_health_info.get('allergies'):
        summary_parts.append(f"敏感史：{detailed_health_info['allergies']}")
    
    # 手術史
    if detailed_health_info.get('surgeries'):
        summary_parts.append(f"手術史：{detailed_health_info['surgeries']}")
    
    # 特殊情況
    special_conditions = []
    if detailed_health_info.get('bloodThinner'):
        special_conditions.append("有服薄血藥")
    if detailed_health_info.get('recentVisit'):
        special_conditions.append("三個月內曾就診")
    if detailed_health_info.get('cpapMachine'):
        special_conditions.append("使用呼吸機")
    if detailed_health_info.get('looseTeeth'):
        special_conditions.append("有鬆牙問題")
    
    if special_conditions:
        summary_parts.append(f"特殊情況：{'、'.join(special_conditions)}")
    
    return '\n'.join(summary_parts)

def call_openrouter_api(prompt: str) -> str:
    """調用OpenRouter API進行AI分析"""
    try:
        if not AI_CONFIG['openrouter']['api_key']:
            return "請設置OPENROUTER_API_KEY環境變數"
            
        headers = {
            "Authorization": f"Bearer {AI_CONFIG['openrouter']['api_key']}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:5000",
            "X-Title": "AI Doctor Matching System"
        }
        
        data = {
            "model": AI_CONFIG['openrouter']['model'],
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": AI_CONFIG['openrouter']['max_tokens'],
            "temperature": 0.7
        }
        
        response = requests.post(
            AI_CONFIG['openrouter']['base_url'], 
            headers=headers, 
            json=data, 
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            return f"OpenRouter API錯誤: {response.status_code} - {response.text}"
            
    except Exception as e:
        return f"OpenRouter API分析出現錯誤: {str(e)}"

def call_ollama_api(prompt: str) -> str:
    """調用Ollama API進行AI分析"""
    try:
        data = {
            "model": AI_CONFIG['ollama']['model'],
            "prompt": prompt,
            "stream": False
        }
        
        response = requests.post(AI_CONFIG['ollama']['base_url'], json=data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            return result.get('response', '無法獲取AI分析')
        else:
            return "AI服務暫時不可用"
    except requests.exceptions.ConnectionError:
        return "請確保Ollama服務正在運行 (http://localhost:11434)"
    except Exception as e:
        return f"AI分析出現錯誤: {str(e)}"

def call_ai_api(prompt: str) -> str:
    """根據配置調用相應的AI API"""
    provider = AI_CONFIG['provider'].lower()
    
    if provider == 'openrouter':
        return call_openrouter_api(prompt)
    elif provider == 'ollama':
        return call_ollama_api(prompt)
    else:
        return f"不支援的AI提供商: {provider}"

def diagnose_symptoms(age: int, symptoms: str, chronic_conditions: str = '', detailed_health_info: Dict = None) -> Dict[str, str]:
    """使用AI診斷症狀"""
    
    if detailed_health_info is None:
        detailed_health_info = {}
    
    # 構建詳細健康信息
    health_details = []
    if chronic_conditions.strip():
        health_details.append(f"長期病史：{chronic_conditions}")
    
    if detailed_health_info.get('height') or detailed_health_info.get('weight'):
        height = detailed_health_info.get('height', '')
        weight = detailed_health_info.get('weight', '')
        if height and weight:
            try:
                bmi = round(float(weight) / ((float(height) / 100) ** 2), 1)
                health_details.append(f"身高體重：{height}cm / {weight}kg (BMI: {bmi})")
            except:
                health_details.append(f"身高體重：{height}cm / {weight}kg")
        elif height:
            health_details.append(f"身高：{height}cm")
        elif weight:
            health_details.append(f"體重：{weight}kg")
    
    if detailed_health_info.get('medications'):
        health_details.append(f"長期藥物：{detailed_health_info['medications']}")
    
    if detailed_health_info.get('allergies'):
        health_details.append(f"敏感史：{detailed_health_info['allergies']}")
    
    if detailed_health_info.get('surgeries'):
        health_details.append(f"手術史：{detailed_health_info['surgeries']}")
    
    special_conditions = []
    if detailed_health_info.get('bloodThinner'):
        special_conditions.append("有服薄血藥")
    if detailed_health_info.get('recentVisit'):
        special_conditions.append("三個月內曾就診")
    if detailed_health_info.get('cpapMachine'):
        special_conditions.append("使用呼吸機")
    if detailed_health_info.get('looseTeeth'):
        special_conditions.append("有鬆牙問題")
    
    if special_conditions:
        health_details.append(f"特殊情況：{'、'.join(special_conditions)}")
    
    # 構建AI診斷提示
    health_info = "\n    - ".join(health_details) if health_details else "無特殊健康信息"
    
    diagnosis_prompt = f"""
    作為一名經驗豐富的醫療專家，請根據以下病人資料進行初步診斷分析：

    病人資料：
    - 年齡：{age}歲
    - 主要症狀：{symptoms}
    - {health_info}

    請提供：
    1. 可能的病症診斷（最多3個可能性，按可能性排序）
    2. 建議就診的專科
    3. 症狀嚴重程度評估（輕微/中等/嚴重）
    4. 是否需要緊急就醫
    5. 一般建議和注意事項

    請用繁體中文回答，格式如下：
    
    可能診斷：
    1. [最可能的病症] - [可能性百分比]
    2. [第二可能的病症] - [可能性百分比]
    3. [第三可能的病症] - [可能性百分比]
    
    建議專科：[專科名稱]
    嚴重程度：[輕微/中等/嚴重]
    緊急程度：[是/否]
    
    建議：
    [詳細建議和注意事項]
    
    免責聲明：此分析僅供參考，不能替代專業醫療診斷，請務必諮詢合格醫生。
    """
    
    # 獲取AI診斷
    diagnosis_response = call_ai_api(diagnosis_prompt)
    
    # 解析診斷結果
    recommended_specialty = extract_specialty_from_diagnosis(diagnosis_response)
    
    return {
        'diagnosis': diagnosis_response,
        'recommended_specialty': recommended_specialty
    }

def analyze_symptoms_and_match(age: int, symptoms: str, chronic_conditions: str, language: str, location: str, detailed_health_info: Dict = None) -> Dict[str, Any]:
    """使用AI分析症狀並配對醫生"""
    
    if detailed_health_info is None:
        detailed_health_info = {}
    
    # 生成用戶數據摘要
    user_summary = generate_user_summary(age, symptoms, chronic_conditions, detailed_health_info)
    
    # 第一步：AI診斷
    diagnosis_result = diagnose_symptoms(age, symptoms, chronic_conditions, detailed_health_info)
    
    # 第二步：根據診斷結果推薦醫生
    matched_doctors = filter_doctors(
        diagnosis_result['recommended_specialty'], 
        language, 
        location, 
        symptoms, 
        diagnosis_result['diagnosis']
    )
    
    # 第三步：如果是12歲以下，添加兒科醫生
    if age <= 12:
        pediatric_doctors = filter_doctors('兒科', language, location, symptoms, diagnosis_result['diagnosis'])
        # 合併醫生清單，去除重複
        all_doctors = matched_doctors + pediatric_doctors
        seen_names = set()
        unique_doctors = []
        for doctor in all_doctors:
            if doctor['name'] not in seen_names:
                seen_names.add(doctor['name'])
                unique_doctors.append(doctor)
        matched_doctors = unique_doctors[:10]  # 限制最多10位醫生
    
    return {
        'user_summary': user_summary,
        'diagnosis': diagnosis_result['diagnosis'],
        'recommended_specialty': diagnosis_result['recommended_specialty'],
        'doctors': matched_doctors
    }

def extract_specialty_from_diagnosis(diagnosis_response: str) -> str:
    """從診斷結果中提取推薦的專科"""
    # 簡單的關鍵字匹配來提取專科
    specialties_map = {
        '內科': ['內科', '普通科', '家庭醫學科'],
        '外科': ['外科', '一般外科'],
        '皮膚科': ['皮膚科', '皮膚及性病科'],
        '眼科': ['眼科', '眼科醫生'],
        '精神科': ['精神科', '心理科'],
        '婦產科': ['婦產科', '婦科'],
        '兒科': ['兒科', '兒科醫生', '小兒科'],
        '營養': ['營養師', '營養科'],
        '耳鼻喉科': ['耳鼻喉科', 'ENT'],
        '骨科': ['骨科', '骨科醫生'],
        '心臟科': ['心臟科', '心臟內科'],
        '神經科': ['神經科', '腦神經科']
    }
    
    for specialty, keywords in specialties_map.items():
        for keyword in keywords:
            if keyword in diagnosis_response:
                return specialty
    
    # 如果沒有找到特定專科，返回內科作為默認
    return '內科'

def extract_specialty_from_ai_response(ai_response: str) -> str:
    """從AI回應中提取推薦的專科（保留兼容性）"""
    return extract_specialty_from_diagnosis(ai_response)

def safe_str_check(value, search_term):
    """安全的字符串檢查，處理NaN值"""
    if pd.isna(value) or value is None:
        return False
    return search_term in str(value)

def filter_doctors(recommended_specialty: str, language: str, location: str, symptoms: str, ai_analysis: str) -> List[Dict[str, Any]]:
    """根據條件篩選醫生"""
    matched_doctors = []
    
    for doctor in DOCTORS_DATA:
        score = 0
        match_reasons = []
        
        # 專科匹配
        doctor_specialty = doctor.get('specialty', '')
        if doctor_specialty and not pd.isna(doctor_specialty):
            doctor_specialty = str(doctor_specialty)
            if safe_str_check(doctor_specialty, recommended_specialty):
                score += 50
                match_reasons.append(f"專科匹配：{doctor_specialty}")
            elif safe_str_check(doctor_specialty, '普通科') or safe_str_check(doctor_specialty, '內科'):
                score += 30
                match_reasons.append("可處理一般症狀")
        
        # 語言匹配
        doctor_languages = doctor.get('languages', '')
        if doctor_languages and not pd.isna(doctor_languages):
            doctor_languages = str(doctor_languages)
            if safe_str_check(doctor_languages, language):
                score += 30
                match_reasons.append(f"語言匹配：{language}")
        
        # 地區匹配
        doctor_address = doctor.get('clinic_addresses', '')
        if doctor_address and not pd.isna(doctor_address):
            doctor_address = str(doctor_address)
            if location == '香港島' and (safe_str_check(doctor_address, '中環') or safe_str_check(doctor_address, '香港')):
                score += 20
                match_reasons.append("地區匹配：香港島")
            elif location == '九龍' and (safe_str_check(doctor_address, '九龍') or safe_str_check(doctor_address, '尖沙咀') or safe_str_check(doctor_address, '旺角')):
                score += 20
                match_reasons.append("地區匹配：九龍")
            elif location == '新界' and safe_str_check(doctor_address, '新界'):
                score += 20
                match_reasons.append("地區匹配：新界")
        
        # 只保留有一定匹配度的醫生
        if score >= 30:
            # 清理醫生數據，確保所有字段都是字符串
            doctor_copy = {}
            for key, value in doctor.items():
                if pd.isna(value) or value is None:
                    doctor_copy[key] = ''
                else:
                    doctor_copy[key] = str(value)
            
            doctor_copy['match_score'] = score
            doctor_copy['match_reasons'] = match_reasons
            doctor_copy['ai_analysis'] = ai_analysis
            matched_doctors.append(doctor_copy)
    
    # 按匹配分數排序
    matched_doctors.sort(key=lambda x: x['match_score'], reverse=True)
    
    # 返回前5名
    return matched_doctors[:5]

@app.route('/')
def index():
    """主頁"""
    return render_template('index.html')

@app.route('/find_doctor', methods=['POST'])
def find_doctor():
    """處理醫生搜索請求"""
    try:
        data = request.get_json()
        age = int(data.get('age', 0))
        symptoms = data.get('symptoms', '')
        chronic_conditions = data.get('chronicConditions', '')
        language = data.get('language', '中文')
        location = data.get('location', '')
        detailed_health_info = data.get('detailedHealthInfo', {})
        
        # 驗證輸入
        if not all([age, symptoms, language, location]):
            return jsonify({'error': '請填寫所有必要資料'}), 400
        
        # 使用AI分析症狀並配對醫生
        result = analyze_symptoms_and_match(age, symptoms, chronic_conditions, language, location, detailed_health_info)
        
        return jsonify({
            'success': True,
            'user_summary': result['user_summary'],
            'diagnosis': result['diagnosis'],
            'recommended_specialty': result['recommended_specialty'],
            'doctors': result['doctors'],
            'total': len(result['doctors'])
        })
        
    except Exception as e:
        print(f"處理請求時發生錯誤: {e}")
        return jsonify({'error': '服務器內部錯誤'}), 500

@app.route('/health')
def health_check():
    """健康檢查"""
    provider = AI_CONFIG['provider']
    ai_status = 'unknown'
    
    # 測試AI服務狀態
    try:
        test_response = call_ai_api("Hello")
        if "錯誤" not in test_response and "不可用" not in test_response:
            ai_status = 'healthy'
        else:
            ai_status = 'error'
    except:
        ai_status = 'error'
    
    return jsonify({
        'status': 'healthy',
        'doctors_loaded': len(get_doctors_data()),
        'ai_provider': provider,
        'ai_status': ai_status,
        'ai_config': {
            'provider': provider,
            'model': AI_CONFIG[provider]['model'] if provider in AI_CONFIG else 'unknown'
        }
    })

@app.route('/ai-config')
def get_ai_config():
    """獲取AI配置信息"""
    provider = AI_CONFIG['provider']
    config_info = {
        'current_provider': provider,
        'available_providers': ['ollama', 'openrouter'],
        'current_model': AI_CONFIG[provider]['model'] if provider in AI_CONFIG else 'unknown'
    }
    
    if provider == 'openrouter':
        config_info['api_key_set'] = bool(AI_CONFIG['openrouter']['api_key'])
        config_info['max_tokens'] = AI_CONFIG['openrouter']['max_tokens']
    
    return jsonify(config_info)

if __name__ == '__main__':
    doctors_data = get_doctors_data()
    print(f"已載入 {len(doctors_data)} 位醫生資料")
    print("正在啟動AI香港醫療配對系統...")
    print(f"當前AI提供商: {AI_CONFIG['provider']}")
    
    if AI_CONFIG['provider'] == 'openrouter':
        if AI_CONFIG['openrouter']['api_key']:
            print(f"OpenRouter模型: {AI_CONFIG['openrouter']['model']}")
            print("OpenRouter API密鑰已設置")
        else:
            print("警告: 未設置OPENROUTER_API_KEY環境變數")
    else:
        print(f"Ollama模型: {AI_CONFIG['ollama']['model']}")
        print("請確保Ollama服務正在運行：ollama serve")
    
    app.run(debug=True, host='0.0.0.0', port=8081)
