#!/usr/bin/env python3
"""
Simplified CHP Mapping Test - Tests CHP relevance without requiring server
"""

import json
import time
from datetime import datetime

class CHPRelevanceTester:
    def __init__(self):
        self.chp_content = None
        self.test_results = []

    def load_chp_content(self):
        """Load CHP content database"""
        try:
            with open('assets/content.json', 'r', encoding='utf-8') as f:
                self.chp_content = json.load(f)
                print(f"✅ Loaded {len(self.chp_content)} CHP entries")
        except Exception as e:
            print(f"❌ Failed to load CHP content: {e}")
            return False
        return True

    def test_chp_relevance(self, symptoms, expected_topics=None, test_name=""):
        """Test CHP content relevance for given symptoms"""
        print(f"\n🧪 Testing CHP mapping: {test_name}")
        print(f"   Input symptoms: {symptoms}")

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

            # Metabolic/Diabetes
            '糖尿病': ['糖尿病'],
            '口渴': ['糖尿病'],
            '多尿': ['糖尿病'],
            '多飲': ['糖尿病'],
            '體重減輕': ['糖尿病'],

            # Respiratory/Infectious
            '流感': ['乙型流感嗜血桿菌感染', '季節性流感', '季節流行性感冒'],
            '感冒': ['2019冠狀病毒病', '季節流行性感冒'],
            '咳嗽': ['2019冠狀病毒病', '肺炎球菌感染', '季節流行性感冒'],
            '發燒': ['2019冠狀病毒病', '水痘', '手足口病', '季節流行性感冒'],
            '喉嚨痛': ['2019冠狀病毒病', '猩紅熱', '季節流行性感冒'],
            '呼吸困難': ['2019冠狀病毒病', '肺炎球菌感染'],
            '肺炎': ['肺炎球菌感染', '肺炎支原體感染'],
            '鼻塞': ['2019冠狀病毒病', '季節流行性感冒'],

            # Gastrointestinal
            '腹痛': ['諾如病毒感染', '食物中毒', '腸胃炎'],
            '腹瀉': ['諾如病毒感染', '食物中毒', '腸胃炎'],
            '嘔吐': ['諾如病毒感染', '食物中毒', '腸胃炎'],
            '胃痛': ['腸胃炎', '消化不良'],
            '噁心': ['腸胃炎', '食物中毒'],
            '胃腸': ['腸胃炎'],

            # Skin conditions
            '皮疹': ['水痘', '手足口病', '麻疹'],
            '水泡': ['水痘'],
            '口腔潰瘍': ['手足口病'],
            '手足皮疹': ['手足口病'],

            # Mental Health
            '抑鬱': ['心理健康', '抑鬱症', '精神健康'],
            '焦慮': ['心理健康', '焦慮症', '精神健康'],
            '壓力大': ['心理健康', '壓力管理', '精神健康'],
            '精神': ['精神健康'],
            '情緒': ['心理健康'],

            # Neurological
            '頭痛': ['2019冠狀病毒病', '偏頭痛'],
            '頭暈': ['心臟病', '糖尿病', '貧血'],
            '中風': ['中風'],

            # Other
            '疲倦': ['糖尿病', '心臟病', '貧血', '甲狀腺功能減退'],
            '體重': ['糖尿病', '營養'],
            '營養': ['飲食與營養'],
            '貧血': ['貧血']
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

        result = {
            "test_name": test_name,
            "input_symptoms": symptoms,
            "matched_symptoms": matched_symptoms,
            "score": round(relevance_score, 1),
            "matched_topics": [entry['title'].replace('衞生防護中心 - ', '') for entry in unique_entries[:3]],
            "total_entries": total_entries,
            "expected_topics": expected_topics or []
        }

        print(f"   Matched symptoms: {matched_symptoms}")
        print(f"   CHP topics found: {result['matched_topics']}")
        print(f"   Relevance score: {result['score']}/100")

        return result

    def run_mapping_tests(self):
        """Run comprehensive CHP mapping tests"""
        print("🚀 Starting CHP Mapping Relevance Tests")
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

            result = self.test_chp_relevance(
                symptoms=test_case["symptoms"],
                expected_topics=test_case["expected_chp"],
                test_name=test_case["name"]
            )

            all_results.append(result)

        return all_results

    def generate_report(self, results):
        """Generate comprehensive test report"""
        print("\n" + "="*80)
        print("📊 CHP MAPPING RELEVANCE TEST REPORT")
        print("="*80)

        # Summary statistics
        total_tests = len(results)
        scores = [r.get("score", 0) for r in results]
        avg_score = sum(scores) / len(scores) if scores else 0

        print("\n🎯 OVERALL RESULTS:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Average Score: {avg_score:.1f}/100")

        # Score distribution analysis
        excellent = sum(1 for s in scores if s >= 80)
        good = sum(1 for s in scores if 60 <= s < 80)
        fair = sum(1 for s in scores if 40 <= s < 60)
        poor = sum(1 for s in scores if s < 40)

        print("\n📊 SCORE DISTRIBUTION:")
        print(f"   Excellent (80-100): {excellent} tests")
        print(f"   Good (60-79): {good} tests")
        print(f"   Fair (40-59): {fair} tests")
        print(f"   Poor (0-39): {poor} tests")

        # Detailed results
        print("\n📋 DETAILED TEST RESULTS:")
        print("-" * 80)

        for i, result in enumerate(results, 1):
            score = result.get("score", 0)
            status_emoji = "✅" if score >= 60 else "⚠️" if score >= 40 else "❌"

            print(f"\n{i}. {status_emoji} {result['test_name']} - {score}/100")

            print(f"   Input: {', '.join(result['input_symptoms'])}")
            print(f"   Matched: {', '.join(result.get('matched_symptoms', []))}")
            if result.get("matched_topics"):
                print(f"   CHP Topics: {', '.join(result['matched_topics'])}")
            else:
                print("   CHP Topics: None found")

        # Recommendations
        print("\n💡 RECOMMENDATIONS:")
        print("-" * 80)

        if avg_score >= 70:
            print("✅ CHP mapping is working well!")
        elif avg_score >= 50:
            print("⚠️  CHP mapping needs some improvements")
        else:
            print("❌ CHP mapping needs significant improvements")

        if poor > 0:
            print(f"⚠️  {poor} tests had poor mapping - consider expanding symptom coverage")

        print("\n✅ Testing completed!")
        print(f"Report generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        return {
            "summary": {
                "total_tests": total_tests,
                "avg_score": round(avg_score, 1),
                "score_distribution": {
                    "excellent": excellent,
                    "good": good,
                    "fair": fair,
                    "poor": poor
                }
            },
            "detailed_results": results
        }


def main():
    """Main test runner"""
    tester = CHPRelevanceTester()

    # Run mapping tests
    results = tester.run_mapping_tests()

    # Generate report
    report = tester.generate_report(results)

    # Save results to file
    with open('chp_mapping_test_results.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print("\n💾 Results saved to chp_mapping_test_results.json")
    return report


if __name__ == "__main__":
    main()
