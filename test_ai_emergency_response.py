#!/usr/bin/env python3
"""
Test AI emergency response format
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import call_ai_api, check_emergency_needed, get_translation

def test_ai_emergency_format():
    """Test what the AI actually responds for emergency symptoms"""
    
    # Build a simple emergency test prompt
    emergency_prompt = """
    您是一位專業醫生，請分析以下症狀：

    病人資料：
    - 年齡：35歲
    - 主要症狀：胸痛、呼吸困難、心跳很快、冒冷汗、頭暈
    - 長期病史：高血壓、糖尿病

    請提供：
    1. 可能的病症診斷（最多3個可能性，按可能性排序）
    2. 建議就診的專科
    3. 症狀嚴重程度評估（輕微/中等/嚴重）
    4. 是否需要緊急就醫
    5. 一般建議和注意事項

    **嚴格格式要求：**
    可能診斷：
    建議專科：
    嚴重程度：
    緊急程度：
    建議：
    """
    
    print("Testing AI response for emergency symptoms...")
    print("Prompt:")
    print("=" * 50)
    print(emergency_prompt)
    print("=" * 50)
    
    # Get AI response
    response = call_ai_api(emergency_prompt)
    
    print("\nAI Response:")
    print("=" * 50)
    print(response)
    print("=" * 50)
    
    # Test emergency detection
    emergency_detected = check_emergency_needed(response)
    print(f"\nEmergency Detected: {emergency_detected}")
    
    # Check for specific patterns
    print("\nPattern Analysis:")
    if "緊急程度：是" in response:
        print("✓ Found '緊急程度：是'")
    elif "緊急程度：否" in response:
        print("✗ Found '緊急程度：否'")
    else:
        print("⚠ No standard emergency format found")
        
    if "緊急就醫" in response:
        print("✓ Found '緊急就醫' keyword")
    if "急診" in response:
        print("✓ Found '急診' keyword")
    if "立即" in response:
        print("✓ Found '立即' keyword")
        
    return response, emergency_detected

if __name__ == "__main__":
    response, emergency_detected = test_ai_emergency_format()
    
    print(f"\n=== Summary ===")
    print(f"Emergency detected: {emergency_detected}")
    if not emergency_detected:
        print("Possible issues:")
        print("1. AI not using correct format '緊急程度：是'")
        print("2. AI using conditional language instead of direct emergency")
        print("3. Emergency detection patterns need updating")
