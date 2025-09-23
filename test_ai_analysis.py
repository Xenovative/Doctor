#!/usr/bin/env python3
"""
Comprehensive AI Analysis Unit Test Suite
Tests medical reference relevance and CHP guideline mapping accuracy
"""

import json
import requests
import time
from datetime import datetime
import sys
import os

class AIAnalysisTester:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
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
            # Make request to AI analysis endpoint
            response = requests.post(
                f"{self.base_url}/analyze",
                json={"symptoms": symptoms},
                timeout=30
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
            analysis = result.get('analysis', '')

            # Extract symptoms from analysis for CHP mapping
            extracted_symptoms = self.extract_symptoms_from_analysis(analysis)

            # Test CHP relevance
            chp_relevance = self.test_chp_relevance(extracted_symptoms, expected_chp_topics)

            # Test PubMed relevance (if available)
            pubmed_relevance = self.test_pubmed_relevance(analysis, symptoms)

            test_result = {
                "test_name": test_name,
                "symptoms": symptoms,
                "extracted_symptoms": extracted_symptoms,
                "status": "PASSED",
                "chp_relevance": chp_relevance,
                "pubmed_relevance": pubmed_relevance,
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

    def extract_symptoms_from_analysis(self, analysis_text):
        """Extract medical terms from AI analysis text"""
        symptoms = []

        # Look for symptom sections in Chinese analysis
        import re

        # Common patterns for symptom extraction
        patterns = [
            r'症狀分析：(.*?)(?=相關專科|緊急程度|資訊|$)',
            r'主要症狀包括：(.*?)(?=相關專科|緊急程度|資訊|$)',
            r'患者出現(.*?)(?=相關專科|緊急程度|資訊|$)'
        ]

        for pattern in patterns:
            match = re.search(pattern, analysis_text, re.DOTALL)
            if match:
                symptom_text = match.group(1)
                # Extract individual symptoms
                symptom_list = re.findall(r'[\u4e00-\u9fff]{2,6}', symptom_text)
                symptoms.extend(symptom_list)
                break

        return list(set(symptoms))  # Remove duplicates

    def test_chp_relevance(self, symptoms, expected_topics=None):
        """Test CHP content relevance for given symptoms"""
        if not self.chp_content:
            return {"score": 0, "matched_topics": [], "error": "CHP content not loaded"}

        relevant_entries = []
        matched_symptoms = []

        # Symptom to CHP topic mapping (same as in medical-evidence.js)
        symptom_mappings = {
            '心臟病': ['心臟病'],
            '糖尿病': ['糖尿病'],
            '高血壓': ['心臟病'],
            '流感': ['乙型流感嗜血桿菌感染'],
            '感冒': ['2019冠狀病毒病'],
            '咳嗽': ['2019冠狀病毒病', '肺炎球菌感染'],
            '發燒': ['2019冠狀病毒病', '水痘'],
            '喉嚨痛': ['2019冠狀病毒病', '猩紅熱'],
            '呼吸困難': ['2019冠狀病毒病', '肺炎球菌感染'],
            '肺炎': ['肺炎球菌感染', '肺炎支原體感染'],
            '腹痛': ['諾如病毒感染'],
            '腹瀉': ['諾如病毒感染'],
            '嘔吐': ['諾如病毒感染'],
            '胸痛': ['心臟病'],
            '疲倦': ['糖尿病', '心臟病'],
            '多尿': ['糖尿病'],
            '多飲': ['糖尿病'],
            '皮疹': ['水痘', '手足口病'],
            '頭痛': ['2019冠狀病毒病'],
            '頭暈': ['心臟病', '糖尿病'],
            '手足口': ['手足口病'],
            '水痘': ['水痘'],
            '抑鬱': ['心理健康'],
            '焦慮': ['心理健康'],
            '營養': ['飲食與營養'],
            '飲食': ['飲食與營養']
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
        # This is a simplified check - in reality we'd need to test the actual PubMed integration
        pubmed_mentions = analysis_text.count('PubMed') + analysis_text.count('醫學文獻')

        # Check if analysis mentions medical literature
        has_medical_refs = pubmed_mentions > 0

        # Basic relevance scoring based on medical terminology
        medical_terms = ['臨床', '研究', '證據', '醫學', '治療', '診斷', '臨床試驗']
        medical_term_count = sum(1 for term in medical_terms if term in analysis_text)

        relevance_score = min(medical_term_count * 15 + (pubmed_mentions * 20), 100)

        return {
            "score": round(relevance_score, 1),
            "has_medical_references": has_medical_refs,
            "pubmed_mentions": pubmed_mentions,
            "medical_terms_found": medical_term_count
        }

    def run_comprehensive_tests(self):
        """Run comprehensive test suite"""
        print("🚀 Starting Comprehensive AI Analysis Test Suite")
        print("=" * 60)

        if not self.load_chp_content():
            print("❌ Cannot proceed without CHP content")
            return []

        # Test cases with various symptom combinations
        test_cases = [
            # Respiratory infections
            {
                "name": "Common Cold Symptoms",
                "symptoms": ["喉嚨痛", "鼻塞", "輕微咳嗽"],
                "expected_chp": ["2019冠狀病毒病"]
            },
            {
                "name": "Flu-like Symptoms",
                "symptoms": ["發燒", "咳嗽", "頭痛", "喉嚨痛"],
                "expected_chp": ["2019冠狀病毒病"]
            },
            {
                "name": "Severe Respiratory",
                "symptoms": ["高燒", "劇烈咳嗽", "呼吸困難"],
                "expected_chp": ["2019冠狀病毒病", "肺炎球菌感染"]
            },

            # Gastrointestinal
            {
                "name": "Food Poisoning",
                "symptoms": ["腹痛", "腹瀉", "嘔吐"],
                "expected_chp": ["諾如病毒感染"]
            },
            {
                "name": "Stomach Issues",
                "symptoms": ["胃痛", "腹瀉", "噁心"],
                "expected_chp": ["諾如病毒感染"]
            },

            # Chronic diseases
            {
                "name": "Diabetes Symptoms",
                "symptoms": ["口渴", "多尿", "疲倦", "體重減輕"],
                "expected_chp": ["糖尿病"]
            },
            {
                "name": "Heart Disease",
                "symptoms": ["胸痛", "呼吸困難", "疲倦"],
                "expected_chp": ["心臟病"]
            },
            {
                "name": "Hypertension",
                "symptoms": ["頭痛", "頭暈", "高血壓"],
                "expected_chp": ["心臟病"]
            },

            # Skin conditions
            {
                "name": "Chickenpox",
                "symptoms": ["發燒", "皮疹", "水泡"],
                "expected_chp": ["水痘"]
            },
            {
                "name": "Hand Foot Mouth",
                "symptoms": ["發燒", "口腔潰瘍", "手足皮疹"],
                "expected_chp": ["手足口病"]
            },

            # Mental health
            {
                "name": "Mental Health",
                "symptoms": ["抑鬱", "焦慮", "壓力大"],
                "expected_chp": ["心理健康"]
            },

            # Mixed symptoms
            {
                "name": "Complex Case",
                "symptoms": ["發燒", "咳嗽", "胸痛", "疲倦"],
                "expected_chp": ["2019冠狀病毒病", "心臟病"]
            }
        ]

        all_results = []

        for i, test_case in enumerate(test_cases, 1):
            print(f"\n📊 Test {i}/{len(test_cases)}")

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

        print("
🎯 OVERALL RESULTS:"        print(f"   Total Tests: {total_tests}")
        print(f"   ✅ Passed: {passed_tests}")
        print(f"   ❌ Failed: {failed_tests}")
        print(".1f"
        # CHP Relevance Analysis
        chp_scores = [r.get("chp_relevance", {}).get("score", 0) for r in results if r["status"] == "PASSED"]
        if chp_scores:
            avg_chp = sum(chp_scores) / len(chp_scores)
            print("
🏥 CHP GUIDELINES ANALYSIS:"            print(".1f"            print(f"   Highest: {max(chp_scores)}/100")
            print(f"   Lowest: {min(chp_scores)}/100")

        # PubMed Relevance Analysis
        pubmed_scores = [r.get("pubmed_relevance", {}).get("score", 0) for r in results if r["status"] == "PASSED"]
        if pubmed_scores:
            avg_pubmed = sum(pubmed_scores) / len(pubmed_scores)
            print("
📚 PUBMED REFERENCES ANALYSIS:"            print(".1f"            print(f"   Highest: {max(pubmed_scores)}/100")
            print(f"   Lowest: {min(pubmed_scores)}/100")

        # Detailed results
        print("
📋 DETAILED TEST RESULTS:"        print("-" * 80)

        for i, result in enumerate(results, 1):
            status = result["status"]
            status_emoji = "✅" if status == "PASSED" else "❌"

            print(f"\n{i}. {status_emoji} {result['test_name']}")

            if status == "PASSED":
                chp = result.get("chp_relevance", {})
                pubmed = result.get("pubmed_relevance", {})

                print(f"   Symptoms: {', '.join(result['symptoms'])}")
                print(f"   Extracted: {', '.join(result.get('extracted_symptoms', []))}")
                print(f"   CHP Score: {chp.get('score', 0)}/100")
                print(f"   PubMed Score: {pubmed.get('score', 0)}/100")

                if chp.get("matched_topics"):
                    print(f"   CHP Topics: {', '.join(chp['matched_topics'][:2])}")

            else:
                print(f"   Error: {result.get('error', 'Unknown')}")

        # Recommendations
        print("
💡 RECOMMENDATIONS:"        print("-" * 80)

        if avg_chp < 70:
            print("⚠️  CHP mapping needs improvement - consider expanding symptom coverage")

        if avg_pubmed < 60:
            print("⚠️  PubMed integration may need enhancement")

        if failed_tests > 0:
            print(f"⚠️  {failed_tests} tests failed - check AI analysis endpoint")

        print("
✅ Testing completed!"        print(f"Report generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

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


def main():
    """Main test runner"""
    tester = AIAnalysisTester()

    # Run comprehensive tests
    results = tester.run_comprehensive_tests()

    # Generate report
    report = tester.generate_report(results)

    # Save results to file
    with open('ai_analysis_test_results.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print("
💾 Results saved to ai_analysis_test_results.json"    return report


if __name__ == "__main__":
    main()
