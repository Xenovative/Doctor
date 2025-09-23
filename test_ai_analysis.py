"""
Comprehensive AI Analysis Unit Test Suite
Tests medical reference relevance and CHP guideline mapping accuracy

MODES:
- AUTO: python test_ai_analysis.py (auto-detects server availability)
- MOCK: python test_ai_analysis.py mock (server not required, uses simulated data)
- REAL: python test_ai_analysis.py real (requires running Flask server)

MOCK MODE:
- Uses simulated AI analysis responses
- Tests symptom extraction and relevance scoring logic
- No server required, runs instantly
- Perfect for development and debugging

REAL MODE:
- Makes actual API calls to running Flask server
- Tests complete end-to-end functionality
- Requires server to be running on localhost:7001
- Provides real AI analysis and evidence gathering
"""

import json
import requests
import time
from datetime import datetime
import sys
import os

class AIAnalysisTester:
    def __init__(self, base_url="http://localhost:7001", mock_mode=False):
        self.base_url = base_url
        self.mock_mode = mock_mode
        self.test_results = []
        self.chp_content = None

    def load_chp_content(self):
        """Load CHP content database for reference"""
        try:
            with open('assets/content.json', 'r', encoding='utf-8') as f:
                self.chp_content = json.load(f)
                print(f"✅ Loaded {len(self.chp_content)} CHP entries")
        except Exception as e:
            print(f"❌ Failed to load CHP content: {e}")
            return False
        return True

    def test_ai_analysis(self, symptoms, expected_chp_topics=None, test_name=""):
        """Test single AI analysis with symptom set"""
        print(f"\n🧪 Testing: {test_name}")
        print(f"   Symptoms: {symptoms}")

        try:
            # Make request to the correct AI analysis endpoint
            # Based on the frontend code, it uses /find_doctor endpoint
            form_data = {
                "age": 30,
                "gender": "男",
                "symptoms": symptoms,
                "language": "zh-TW",
                "location": "香港島",
                "chronicConditions": "",
                "locationDetails": {
                    "region": "香港島",
                    "district": "中西區",
                    "area": "中環"
                },
                "detailedHealthInfo": {
                    "height": "",
                    "weight": "",
                    "medications": "",
                    "allergies": "",
                    "surgeries": "",
                    "bloodThinner": False,
                    "recentVisit": False,
                    "cpapMachine": False,
                    "looseTeeth": False
                },
                "uiLanguage": "zh-TW"
            }

            response = requests.post(
                f"{self.base_url}/find_doctor",
                json=form_data,
                timeout=60  # Increased timeout for AI processing
            )

            if response.status_code != 200:
                return {
                    "test_name": test_name,
                    "symptoms": symptoms,
                    "status": "FAILED",
                    "error": f"HTTP {response.status_code}",
                    "response": None
                }

            result = response.json()

            # Check if we have analysis data
            if 'analysis' not in result:
                return {
                    "test_name": test_name,
                    "symptoms": symptoms,
                    "status": "FAILED",
                    "error": "No analysis data in response",
                    "response": result
                }

            analysis = result.get('analysis', '')

            # Debug: Show what we got from the API
            print(f"   🔍 API Response Keys: {list(result.keys())}")
            print(f"   📝 Analysis Length: {len(analysis)} characters")
            if len(analysis) > 0:
                print(f"   📄 Analysis Preview: {analysis[:100]}...")
            else:
                print("   ❌ Analysis is empty!")

            # Extract symptoms from analysis for CHP mapping
            extracted_symptoms = self.extract_symptoms_from_analysis(analysis)

            # Test CHP relevance
            chp_relevance = self.test_chp_relevance(extracted_symptoms, expected_chp_topics)

            # Test PubMed relevance
            pubmed_relevance = self.test_pubmed_relevance(analysis, symptoms)

            # Test medical evidence gathering
            medical_evidence = self.test_medical_evidence_gathering(symptoms)

            test_result = {
                "test_name": test_name,
                "symptoms": symptoms,
                "extracted_symptoms": extracted_symptoms,
                "status": "PASSED",
                "chp_relevance": chp_relevance,
                "pubmed_relevance": pubmed_relevance,
                "medical_evidence": medical_evidence,
                "analysis_preview": analysis[:200] + "..." if len(analysis) > 200 else analysis
            }

            return test_result

        except Exception as e:
            return {
                "test_name": test_name,
                "symptoms": symptoms,
                "status": "FAILED",
                "error": str(e),
                "response": None
            }

    def test_ai_analysis_mock(self, symptoms, expected_chp_topics=None, test_name="", age=30, gender="男"):
        """Mock version of AI analysis test for development"""
        print(f"\n🧪 Testing: {test_name} (MOCK MODE)")
        print(f"   Patient: Age {age}, Gender {gender}")
        print(f"   Symptoms: {symptoms}")

        # Create realistic form data like a real user entry
        form_data = {
            "age": age,
            "gender": gender,
            "symptoms": symptoms,
            "language": "zh-TW",
            "location": "香港島",
            "chronicConditions": "",
            "locationDetails": {
                "region": "香港島",
                "district": "中西區",
                "area": "中環"
            },
            "detailedHealthInfo": {
                "height": "",
                "weight": "",
                "medications": "",
                "allergies": "",
                "surgeries": "",
                "bloodThinner": False,
                "recentVisit": False,
                "cpapMachine": False,
                "looseTeeth": False
            },
            "uiLanguage": "zh-TW"
        }

        # Mock AI analysis response based on symptoms and patient data
        symptom_text = "、".join(symptoms)
        if "喉嚨痛" in symptoms or "鼻塞" in symptoms:
            diagnosis = "普通感冒或上呼吸道感染"
        elif "腹痛" in symptoms or "腹瀉" in symptoms:
            diagnosis = "腸胃炎或食物中毒"
        elif "胸痛" in symptoms or "呼吸困難" in symptoms:
            diagnosis = "心臟或呼吸系統問題"
        else:
            diagnosis = "一般性不適"

        mock_analysis = f"""
        患者資料：{age}歲{gender}性
        症狀分析：患者出現{symptom_text}等症狀，可能是{diagnosis}引起。
        相關專科：內科
        緊急程度：一般門診就醫
        建議：建議到醫院檢查，遵醫囑治療。
        """

        print(f"   📋 Mock Form Data: Age {form_data['age']}, Gender {form_data['gender']}, Location {form_data['location']}")

        # Extract symptoms from analysis for CHP mapping
        extracted_symptoms = self.extract_symptoms_from_analysis(mock_analysis)

        # Test CHP relevance
        chp_relevance = self.test_chp_relevance(extracted_symptoms, expected_chp_topics)

        # Test PubMed relevance
        pubmed_relevance = self.test_pubmed_relevance(mock_analysis, symptoms)

        # Test medical evidence gathering
        medical_evidence = self.test_medical_evidence_gathering(symptoms)

        test_result = {
            "test_name": test_name,
            "symptoms": symptoms,  # Keep symptoms at top level for consistency
            "patient_data": {
                "age": age,
                "gender": gender,
                "symptoms": symptoms,
                "location": form_data["location"]
            },
            "extracted_symptoms": extracted_symptoms,
            "status": "PASSED",
            "chp_relevance": chp_relevance,
            "pubmed_relevance": pubmed_relevance,
            "medical_evidence": medical_evidence,
            "analysis_preview": mock_analysis[:200] + "..." if len(mock_analysis) > 200 else mock_analysis
        }

        return test_result

    def extract_symptoms_from_analysis(self, analysis_text):
        """Extract medical terms from AI analysis text"""
        symptoms = []

        # Look for symptom sections in both Chinese and English analysis
        import re

        # Common patterns for symptom extraction - both languages
        patterns = [
            # Chinese patterns
            r'症狀分析：(.*?)(?=相關專科|緊急程度|資訊|$)',
            r'主要症狀包括：(.*?)(?=相關專科|緊急程度|資訊|$)',
            r'患者出現(.*?)(?=相關專科|緊急程度|資訊|$)',
            # English patterns
            r'Symptoms include:(.*?)(?=Specialty|Emergency|Information|$)',
            r'Patient presents with(.*?)(?=Specialty|Emergency|Information|$)',
            r'Key symptoms:(.*?)(?=Specialty|Emergency|Information|$)'
        ]

        for pattern in patterns:
            match = re.search(pattern, analysis_text, re.DOTALL | re.IGNORECASE)
            if match:
                symptom_text = match.group(1)
                # Extract medical terms - both Chinese and English
                medical_terms = re.findall(r'[\u4e00-\u9fff]{2,10}|[A-Za-z][a-z]+(?: [a-z]+)*', symptom_text)
                symptoms.extend(medical_terms)
                break

        # If no structured patterns found, extract all medical-sounding terms
        if not symptoms:
            # Look for common medical terms in the text
            medical_terms = re.findall(r'\b(?:acute|chronic|severe|mild|viral|bacterial|infection|syndrome|disease|disorder|condition)\b', analysis_text, re.IGNORECASE)
            chinese_medical = re.findall(r'[\u4e00-\u9fff]{2,6}(?:症|炎|病|毒|痛|瀉|熱)', analysis_text)
            symptoms.extend(medical_terms + chinese_medical)

        return list(set(symptoms))  # Remove duplicates

    def test_chp_relevance(self, symptoms, expected_topics=None):
        """Test CHP content relevance for given symptoms"""
        if not self.chp_content:
            return {"score": 0, "matched_topics": [], "error": "CHP content not loaded"}

        relevant_entries = []
        matched_symptoms = []

        # Symptom to CHP topic mapping (same as in medical-evidence.js)
        symptom_mappings = {
            # Cardiovascular
            '心臟病': ['心臟病'],
            '高血壓': ['心臟病', '高血壓'],
            '胸痛': ['心臟病'],
            'heart': ['心臟病'],
            'cardiac': ['心臟病'],

            # Metabolic/Diabetes
            '糖尿病': ['糖尿病'],
            '口渴': ['糖尿病'],
            '多尿': ['糖尿病'],
            '多飲': ['糖尿病'],
            '體重減輕': ['糖尿病'],
            'diabetes': ['糖尿病'],
            'diabetic': ['糖尿病'],

            # Respiratory/Infectious
            '流感': ['乙型流感嗜血桿菌感染', '季節性流感', '季節流行性感冒'],
            '感冒': ['2019冠狀病毒病', '季節流行性感冒'],
            '咳嗽': ['2019冠狀病毒病', '肺炎球菌感染', '季節流行性感冒'],
            '發燒': ['2019冠狀病毒病', '水痘', '手足口病', '季節流行性感冒'],
            '喉嚨痛': ['2019冠狀病毒病', '猩紅熱', '季節流行性感冒'],
            '呼吸困難': ['2019冠狀病毒病', '肺炎球菌感染'],
            '肺炎': ['肺炎球菌感染', '肺炎支原體感染'],
            '鼻塞': ['2019冠狀病毒病', '季節流行性感冒'],
            'influenza': ['季節性流感', '季節流行性感冒'],
            'flu': ['季節性流感', '季節流行性感冒'],

            # Gastrointestinal
            '腹痛': ['諾如病毒感染', '食物中毒', '腸胃炎'],
            '腹瀉': ['諾如病毒感染', '食物中毒', '腸胃炎'],
            '嘔吐': ['諾如病毒感染', '食物中毒', '腸胃炎'],
            '胃痛': ['腸胃炎', '消化不良'],
            '噁心': ['腸胃炎', '食物中毒'],
            '胃腸': ['腸胃炎'],
            'food poisoning': ['食物中毒'],
            'gastroenteritis': ['腸胃炎'],
            'diarrhea': ['諾如病毒感染'],
            'vomiting': ['諾如病毒感染'],

            # Skin conditions
            '皮疹': ['水痘', '手足口病', '麻疹'],
            '水泡': ['水痘'],
            '口腔潰瘍': ['手足口病'],
            '手足皮疹': ['手足口病'],
            'rash': ['水痘', '手足口病'],
            'blister': ['水痘'],

            # Mental Health
            '抑鬱': ['心理健康', '抑鬱症', '精神健康'],
            '焦慮': ['心理健康', '焦慮症', '精神健康'],
            '壓力大': ['心理健康', '壓力管理', '精神健康'],
            '精神': ['精神健康'],
            '情緒': ['心理健康'],
            'depression': ['心理健康', '抑鬱症'],
            'anxiety': ['心理健康', '焦慮症'],
            'stress': ['心理健康', '壓力管理'],

            # Neurological
            '頭痛': ['2019冠狀病毒病', '偏頭痛'],
            '頭暈': ['心臟病', '糖尿病', '貧血'],
            '中風': ['中風'],
            'headache': ['2019冠狀病毒病', '偏頭痛'],
            'dizziness': ['心臟病', '糖尿病'],

            # Other
            '疲倦': ['糖尿病', '心臟病', '貧血', '甲狀腺功能減退'],
            '體重': ['糖尿病', '營養'],
            '營養': ['飲食與營養'],
            '貧血': ['貧血'],
            'fatigue': ['糖尿病', '心臟病'],
            'tired': ['糖尿病', '心臟病']
        }

        for symptom in symptoms:
            for key, topics in symptom_mappings.items():
                if key in symptom or symptom in key:
                    matched_symptoms.append(symptom)
                    for topic in topics:
                        # Find actual CHP entries
                        chp_entries = [entry for entry in self.chp_content
                                     if entry.get('title', '').find(topic) >= 0]
                        relevant_entries.extend(chp_entries)
                    break

        # Remove duplicates
        seen_urls = set()
        unique_entries = []
        for entry in relevant_entries:
            if entry['url'] not in seen_urls:
                seen_urls.add(entry['url'])
                unique_entries.append(entry)

        # Calculate relevance score
        total_matched = len(matched_symptoms)
        total_entries = len(unique_entries)

        if total_matched == 0:
            relevance_score = 0
        else:
            # Score based on coverage and quality
            coverage_score = min(total_entries / max(total_matched, 1), 1.0) * 50
            quality_score = min(total_entries * 10, 50)  # Max 50 points for quality
            relevance_score = min(coverage_score + quality_score, 100)

        return {
            "score": round(relevance_score, 1),
            "matched_symptoms": matched_symptoms,
            "matched_topics": [entry['title'].replace('衞生防護中心 - ', '') for entry in unique_entries[:3]],
            "total_entries": total_entries,
            "expected_topics": expected_topics or []
        }

    def test_pubmed_relevance(self, analysis_text, original_symptoms):
        """Test PubMed reference relevance"""
        # Enhanced scoring based on evidence quality indicators

        # Evidence quality indicators
        pubmed_mentions = analysis_text.count('PubMed') + analysis_text.count('醫學文獻') + analysis_text.count('研究')
        evidence_indicators = [
            '臨床試驗', '臨床研究', '醫學證據', '系統性回顧', 'meta分析',
            'clinical trial', 'clinical study', 'medical evidence', 'systematic review', 'meta-analysis',
            '研究結果', '證據顯示', '文獻支持', '醫學期刊', 'peer-reviewed'
        ]

        # Count evidence quality indicators
        evidence_count = sum(1 for indicator in evidence_indicators if indicator in analysis_text)

        # Medical terminology indicators (shows scientific rigor)
        medical_terms = [
            '病因', '病理', '診斷', '治療', '預後', '預防', '風險因素',
            'etiology', 'pathology', 'diagnosis', 'treatment', 'prognosis', 'prevention', 'risk factors',
            '臨床特徵', '流行病學', '生物標記', '治療方案', '療效',
            'clinical features', 'epidemiology', 'biomarkers', 'treatment protocol', 'efficacy'
        ]
        medical_term_count = sum(1 for term in medical_terms if term in analysis_text)

        # Statistical and research methodology terms
        research_terms = [
            '統計', '顯著', '相關', '預測', '分析', '模型', '數據',
            'statistics', 'significant', 'correlation', 'prediction', 'analysis', 'model', 'data',
            'p-value', 'confidence interval', 'odds ratio', 'relative risk'
        ]
        research_term_count = sum(1 for term in research_terms if term in analysis_text)

        # Calculate comprehensive score
        base_score = min(pubmed_mentions * 10, 30)  # Max 30 for mentions
        evidence_bonus = min(evidence_count * 8, 25)  # Max 25 for quality indicators
        medical_bonus = min(medical_term_count * 5, 20)  # Max 20 for medical terminology
        research_bonus = min(research_term_count * 3, 15)  # Max 15 for research methodology

        total_score = min(base_score + evidence_bonus + medical_bonus + research_bonus, 100)

        return {
            "score": round(total_score, 1),
            "has_medical_references": pubmed_mentions > 0,
            "pubmed_mentions": pubmed_mentions,
            "evidence_indicators": evidence_count,
            "medical_terms": medical_term_count,
            "research_terms": research_term_count,
            "components": {
                "base_mentions": min(pubmed_mentions * 10, 30),
                "evidence_quality": evidence_bonus,
                "medical_terminology": medical_bonus,
                "research_methodology": research_bonus
            }
        }

    def test_medical_evidence_gathering(self, symptoms):
        """Test actual medical evidence gathering from the system"""
        try:
            # Test the medical evidence API directly
            evidence_response = requests.post(
                f"{self.base_url}/api/medical-evidence",
                json={"symptoms": symptoms},
                timeout=30
            )

            if evidence_response.status_code == 200:
                evidence_data = evidence_response.json()

                # Debug: Show what evidence was actually gathered
                evidence_list = evidence_data.get("evidence", [])
                print(f"   🔍 Evidence Details: {len(evidence_list)} items")
                for i, entry in enumerate(evidence_list[:3]):  # Show first 3 for debugging
                    title = entry.get("title", "No title")
                    source = entry.get("source", "No source")
                    url = entry.get("url", "No URL")
                    print(f"      {i+1}. Title: '{title[:50]}...' | Source: '{source}' | URL: '{url[:50]}...'")

                return {
                    "success": evidence_data.get("success", False),
                    "evidence_count": len(evidence_list),
                    "evidence_titles": [entry.get("title", "") for entry in evidence_list],
                    "evidence_sources": [entry.get("source", "") for entry in evidence_list],
                    "evidence_urls": [entry.get("url", "") for entry in evidence_list],  # Add URLs for counting
                    # Better detection logic - check for PubMed in title, source, or URL
                    "has_pubmed": any(
                        "pubmed" in entry.get("title", "").lower() or
                        "pubmed" in entry.get("source", "").lower() or
                        "pubmed" in entry.get("url", "").lower() or
                        "nih.gov" in entry.get("url", "").lower() or
                        "ncbi.nlm.nih.gov" in entry.get("url", "").lower()
                        for entry in evidence_list
                    ),
                    "has_chp": any(
                        "chp.gov.hk" in entry.get("url", "") or
                        "衞生" in entry.get("title", "") or
                        "衛生" in entry.get("title", "")
                        for entry in evidence_list
                    ),
                    "error": None
                }
            else:
                return {
                    "success": False,
                    "evidence_count": 0,
                    "evidence_titles": [],
                    "evidence_sources": [],
                    "evidence_urls": [],  # Add URLs for consistency
                    "has_pubmed": False,
                    "has_chp": False,
                    "error": f"API returned {evidence_response.status_code}"
                }

        except Exception as e:
            return {
                "success": False,
                "evidence_count": 0,
                "evidence_titles": [],
                "evidence_sources": [],
                "evidence_urls": [],  # Add URLs for consistency
                "has_pubmed": False,
                "has_chp": False,
                "error": str(e)
            }

    def run_comprehensive_tests(self):
        """Run comprehensive test suite"""
        print("🚀 Starting Comprehensive AI Analysis Test Suite")
        print("=" * 60)

        if not self.load_chp_content():
            print("❌ Cannot proceed without CHP content")
            return []

        # Test cases with various symptom combinations and patient profiles
        test_cases = [
            # Respiratory infections
            {
                "name": "Common Cold - Adult Male",
                "age": 35,
                "gender": "男",
                "symptoms": ["喉嚨痛", "鼻塞", "輕微咳嗽"],
                "expected_chp": ["2019冠狀病毒病"]
            },
            {
                "name": "Flu-like - Young Female",
                "age": 28,
                "gender": "女",
                "symptoms": ["發燒", "咳嗽", "頭痛", "喉嚨痛"],
                "expected_chp": ["2019冠狀病毒病"]
            },
            {
                "name": "Severe Respiratory - Elderly",
                "age": 65,
                "gender": "男",
                "symptoms": ["高燒", "劇烈咳嗽", "呼吸困難"],
                "expected_chp": ["2019冠狀病毒病", "肺炎球菌感染"]
            },

            # Gastrointestinal
            {
                "name": "Food Poisoning - Adult",
                "age": 42,
                "gender": "女",
                "symptoms": ["腹痛", "腹瀉", "嘔吐"],
                "expected_chp": ["諾如病毒感染"]
            },
            {
                "name": "Stomach Issues - Child",
                "age": 8,
                "gender": "男",
                "symptoms": ["胃痛", "腹瀉", "噁心"],
                "expected_chp": ["諾如病毒感染"]
            },

            # Chronic diseases
            {
                "name": "Diabetes Symptoms - Middle-aged",
                "age": 55,
                "gender": "男",
                "symptoms": ["口渴", "多尿", "疲倦", "體重減輕"],
                "expected_chp": ["糖尿病"]
            },
            {
                "name": "Heart Disease - Senior",
                "age": 70,
                "gender": "女",
                "symptoms": ["胸痛", "呼吸困難", "疲倦"],
                "expected_chp": ["心臟病"]
            },
            {
                "name": "Hypertension - Adult",
                "age": 50,
                "gender": "男",
                "symptoms": ["頭痛", "頭暈", "高血壓"],
                "expected_chp": ["心臟病"]
            },

            # Skin conditions
            {
                "name": "Chickenpox - Child",
                "age": 6,
                "gender": "女",
                "symptoms": ["發燒", "皮疹", "水泡"],
                "expected_chp": ["水痘"]
            },
            {
                "name": "Hand Foot Mouth - Child",
                "age": 4,
                "gender": "男",
                "symptoms": ["發燒", "口腔潰瘍", "手足皮疹"],
                "expected_chp": ["手足口病"]
            },

            # Mental health
            {
                "name": "Mental Health - Adult",
                "age": 32,
                "gender": "女",
                "symptoms": ["抑鬱", "焦慮", "壓力大"],
                "expected_chp": ["心理健康"]
            },

            # Mixed symptoms
            {
                "name": "Complex Case - Adult",
                "age": 45,
                "gender": "男",
                "symptoms": ["發燒", "咳嗽", "胸痛", "疲倦"],
                "expected_chp": ["2019冠狀病毒病", "心臟病"]
            }
        ]

        all_results = []

        for i, test_case in enumerate(test_cases, 1):
            print(f"\n📊 Test {i}/{len(test_cases)}")

            if self.mock_mode:
                result = self.test_ai_analysis_mock(
                    symptoms=test_case["symptoms"],
                    expected_chp_topics=test_case["expected_chp"],
                    test_name=test_case["name"],
                    age=test_case["age"],
                    gender=test_case["gender"]
                )
            else:
                result = self.test_ai_analysis(
                    symptoms=test_case["symptoms"],
                    expected_chp_topics=test_case["expected_chp"],
                    test_name=test_case["name"]
                )

            all_results.append(result)

            # Show immediate results
            status_emoji = "✅" if result["status"] == "PASSED" else "❌"
            chp_score = result.get("chp_relevance", {}).get("score", 0)
            pubmed_score = result.get("pubmed_relevance", {}).get("score", 0)

            print(f"   {status_emoji} CHP Relevance: {chp_score}/100")
            print(f"   {status_emoji} PubMed Relevance: {pubmed_score}/100")

            # Show medical evidence gathering results
            evidence = result.get("medical_evidence", {})
            if evidence.get("success", False):
                evidence_count = evidence.get("evidence_count", 0)
                has_pubmed = evidence.get("has_pubmed", False)
                has_chp = evidence.get("has_chp", False)
                titles = evidence.get("evidence_titles", [])

                print(f"   📚 Evidence Gathered: {evidence_count} articles")
                if has_pubmed:
                    print(f"   🔬 PubMed: ✅ ({sum(1 for t in titles if 'pubmed' in t.lower())} articles)")
                if has_chp:
                    print(f"   🏥 CHP: ✅ ({sum(1 for t in titles if 'chp' in t.lower() or '衞生' in t)} articles)")

                if titles and len(titles) <= 3:
                    print(f"   📖 Titles: {', '.join(titles[:2])}")
            else:
                print(f"   ❌ Evidence Error: {evidence.get('error', 'Unknown')}")

            if result["status"] == "FAILED":
                print(f"   ❌ Error: {result.get('error', 'Unknown')}")

        return all_results

    def generate_report(self, results):
        """Generate comprehensive test report"""
        print("\n" + "="*80)
        print("📊 COMPREHENSIVE AI ANALYSIS TEST REPORT")
        print("="*80)

        # Summary statistics
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r["status"] == "PASSED")
        failed_tests = total_tests - passed_tests

        print("\n🎯 OVERALL RESULTS:")
        print(f"   Total Tests: {total_tests}")
        print(f"   ✅ Passed: {passed_tests}")
        print(f"   ❌ Failed: {failed_tests}")
        print(f"   Success Rate: {(passed_tests/total_tests*100):.1f}%")

        # CHP Relevance Analysis
        chp_scores = [r.get("chp_relevance", {}).get("score", 0) for r in results if r["status"] == "PASSED"]
        avg_chp = 0.0
        if chp_scores:
            avg_chp = sum(chp_scores) / len(chp_scores)
            print("\n🏥 CHP GUIDELINES ANALYSIS:")
            print(f"   Average Score: {avg_chp:.1f}/100")
            print(f"   Highest: {max(chp_scores)}/100")
            print(f"   Lowest: {min(chp_scores)}/100")

        # PubMed Relevance Analysis
        pubmed_scores = [r.get("pubmed_relevance", {}).get("score", 0) for r in results if r["status"] == "PASSED"]
        avg_pubmed = 0.0
        if pubmed_scores:
            avg_pubmed = sum(pubmed_scores) / len(pubmed_scores)
            print("\n📚 PUBMED REFERENCES ANALYSIS:")
            print(f"   Average Score: {avg_pubmed:.1f}/100")
            print(f"   Highest: {max(pubmed_scores)}/100")
            print(f"   Lowest: {min(pubmed_scores)}/100")

        # Medical Evidence Gathering Analysis
        evidence_results = [r.get("medical_evidence", {}) for r in results if r["status"] == "PASSED"]
        successful_evidence = [e for e in evidence_results if e.get("success", False)]
        avg_evidence_count = 0.0
        total_pubmed_articles = 0
        total_chp_articles = 0

        if successful_evidence:
            evidence_counts = [e.get("evidence_count", 0) for e in successful_evidence]
            avg_evidence_count = sum(evidence_counts) / len(evidence_counts)

            # Count total articles from all evidence sources
            for evidence in successful_evidence:
                titles = evidence.get("evidence_titles", [])
                total_pubmed_articles += sum(1 for t in titles if 'pubmed' in t.lower())
                total_chp_articles += sum(1 for t in titles if 'chp' in t.lower() or '衞生' in t)

            print("\n🔬 MEDICAL EVIDENCE GATHERING ANALYSIS:")
            print(f"   Successful Evidence Gathering: {len(successful_evidence)}/{len(evidence_results)} tests")
            print(f"   Average Articles per Test: {avg_evidence_count:.1f}")
            print(f"   Total PubMed Articles: {total_pubmed_articles}")
            print(f"   Total CHP Articles: {total_chp_articles}")
            print(f"   Evidence Integration Rate: {(len(successful_evidence)/len(evidence_results)*100):.1f}%")

        # Detailed results
        print("\n📋 DETAILED TEST RESULTS:")
        print("-" * 80)

        for i, result in enumerate(results, 1):
            status = result["status"]
            status_emoji = "✅" if status == "PASSED" else "❌"

            print(f"\n{i}. {status_emoji} {result['test_name']}")

            if status == "PASSED":
                patient_data = result.get("patient_data", {})
                chp = result.get("chp_relevance", {})
                pubmed = result.get("pubmed_relevance", {})
                evidence = result.get("medical_evidence", {})

                print(f"   Patient: {patient_data.get('age', 'N/A')}歲 {patient_data.get('gender', 'N/A')}性")
                symptoms = result.get('symptoms', [])
                print(f"   Symptoms: {', '.join(symptoms) if symptoms else 'No symptoms'}")
                print(f"   📄 AI Analysis: {result.get('analysis_preview', 'No analysis available')}")
                extracted = result.get('extracted_symptoms', [])
                print(f"   Extracted: {', '.join(extracted) if extracted else 'No extracted symptoms'}")
                print(f"   CHP Score: {chp.get('score', 0)}/100")
                print(f"   PubMed Score: {pubmed.get('score', 0)}/100")

                if chp.get("matched_topics"):
                    print(f"   CHP Topics: {', '.join(chp['matched_topics'][:2])}")

                # Show medical evidence gathering results
                if evidence.get("success", False):
                    evidence_count = evidence.get("evidence_count", 0)
                    print(f"   📚 Evidence Count: {evidence_count} articles")

                    titles = evidence.get("evidence_titles", [])
                    if titles:
                        print(f"   📖 Titles: {', '.join(titles[:2])}")

                    if evidence.get("has_pubmed", False):
                        # Count PubMed articles by checking URLs
                        urls = evidence.get("evidence_urls", [])
                        pubmed_count = sum(1 for url in urls
                                          if ("pubmed" in url.lower() or
                                              "nih.gov" in url.lower() or
                                              "ncbi.nlm.nih.gov" in url.lower()))
                        print(f"   🔬 PubMed: ✅ ({pubmed_count} articles)")

                    if evidence.get("has_chp", False):
                        chp_count = sum(1 for t in titles if 'chp' in t.lower() or '衞生' in t)
                        print(f"   🏥 CHP Articles: {chp_count}")
                else:
                    print(f"   ❌ Evidence Error: {evidence.get('error', 'API not available')}")

            else:
                print(f"   Error: {result.get('error', 'Unknown')}")

        # Recommendations
        print("\n💡 RECOMMENDATIONS:")
        print("-" * 80)

        if avg_chp < 70:
            print("⚠️  CHP mapping needs improvement - consider expanding symptom coverage")

        if avg_pubmed < 60:
            print("⚠️  PubMed integration may need enhancement")

        if failed_tests > 0:
            print(f"⚠️  {failed_tests} tests failed - check AI analysis endpoint")

        print("\n✅ Testing completed!")
        print(f"Report generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        return {
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "avg_chp_score": round(sum(chp_scores) / len(chp_scores), 1) if chp_scores else 0,
                "avg_pubmed_score": round(sum(pubmed_scores) / len(pubmed_scores), 1) if pubmed_scores else 0
            },
            "detailed_results": results
        }


def main(mock_mode=None):
    """Main test runner"""
    # Auto-detect mock mode if not specified
    if mock_mode is None:
        # Try to detect if server is running
        try:
            import requests
            response = requests.get('http://localhost:7001/', timeout=2)
            if response.status_code == 200:
                mock_mode = False  # Server is running, use real mode
                print("🔗 Server detected - running in REAL MODE")
            else:
                mock_mode = True   # Server not responding, use mock mode
                print("🔌 Server not detected - running in MOCK MODE")
        except:
            mock_mode = True   # Server not accessible, use mock mode
            print("🔌 Server not accessible - running in MOCK MODE")

    tester = AIAnalysisTester(mock_mode=mock_mode)

    # Run comprehensive tests
    results = tester.run_comprehensive_tests()

    # Generate report
    report = tester.generate_report(results)

    # Save results to file
    with open('ai_analysis_test_results.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print("\n💾 Results saved to ai_analysis_test_results.json")
    mode_text = "MOCK MODE (server not required)" if mock_mode else "REAL MODE (server required)"
    print(f"📝 Note: Tests ran in {mode_text}")
    return report


if __name__ == "__main__":
    import sys

    # Check command line arguments
    mock_mode = None
    if len(sys.argv) > 1:
        if sys.argv[1].lower() == 'mock':
            mock_mode = True
            print("🎭 Forced MOCK MODE by command line argument")
        elif sys.argv[1].lower() == 'real':
            mock_mode = False
            print("🔗 Forced REAL MODE by command line argument")

    main(mock_mode)
