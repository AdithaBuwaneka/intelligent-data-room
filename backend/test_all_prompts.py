"""
Comprehensive Test Suite for Intelligent Data Room Backend
Tests all sample prompts from the requirements document.
"""

import requests
import json
import time
from typing import Dict, Any

BASE_URL = "http://localhost:8000"
SESSION_ID = "test-comprehensive"

# Upload the sample file first
SAMPLE_FILE = "D:/intelligent-data-room/Sample Superstore.csv"

def upload_file() -> str:
    """Upload the sample CSV and return the file_url."""
    print("📤 Uploading sample file...")
    
    with open(SAMPLE_FILE, 'rb') as f:
        files = {'file': f}
        data = {'session_id': SESSION_ID}
        
        response = requests.post(f"{BASE_URL}/api/upload", files=files, data=data)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Upload successful: {result['filename']}")
            print(f"   Rows: {result['row_count']}, Columns: {len(result['columns'])}")
            return result['file_url']
        else:
            print(f"❌ Upload failed: {response.status_code}")
            print(response.text)
            return None

def test_query(question: str, file_url: str, test_name: str) -> Dict[str, Any]:
    """Test a single query."""
    print(f"\n{'='*80}")
    print(f"🧪 Test: {test_name}")
    print(f"❓ Question: {question}")
    print(f"{'='*80}")
    
    payload = {
        "session_id": SESSION_ID,
        "question": question,
        "file_url": file_url
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/query",
            json=payload,
            timeout=120  # 2 minutes timeout for complex queries
        )
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"\n📋 PLAN:")
            print(result.get('plan', 'No plan')[:200] + "...")
            
            print(f"\n✅ ANSWER:")
            answer = result.get('answer', 'No answer')
            print(answer[:300] + ("..." if len(answer) > 300 else ""))
            
            if result.get('chart_config'):
                chart = result['chart_config']
                print(f"\n📊 CHART: {chart.get('type', 'unknown type')}")
                print(f"   Title: {chart.get('title', 'No title')}")
            
            print(f"\n⏱️  Execution Time: {result.get('execution_time', 'N/A')}")
            
            return {
                "status": "PASS",
                "result": result,
                "test_name": test_name
            }
        else:
            print(f"\n❌ FAILED: HTTP {response.status_code}")
            print(response.text[:500])
            return {
                "status": "FAIL",
                "error": response.text,
                "test_name": test_name
            }
            
    except Exception as e:
        print(f"\n❌ EXCEPTION: {str(e)}")
        return {
            "status": "ERROR",
            "error": str(e),
            "test_name": test_name
        }
    
    finally:
        time.sleep(2)  # Rate limiting

# Test Cases from Requirements
EASY_TESTS = [
    ("Create a bar chart showing the total Sales and Profit for each Category.", "E1: Sales & Profit by Category"),
    ("Visualize the distribution of total Sales across different Regions using a pie chart.", "E2: Sales by Region (Pie)"),
    ("Which Customer Segment places the most orders? Show this with a count plot.", "E3: Orders by Segment"),
    ("Identify the Top 5 States by total Sales using a horizontal bar chart.", "E4: Top 5 States"),
    ("How has the total Profit changed over the Years (2018–2021)? Use a line chart.", "E5: Profit Trend by Year"),
]

MEDIUM_TESTS = [
    ("Which Sub-Categories are currently unprofitable on average? Visualize this with a bar chart.", "M1: Unprofitable Sub-Categories"),
    ("Compare the Sales Trend of different Ship Modes over time using a multi-line chart.", "M2: Sales by Ship Mode"),
    ("List the Top 10 Customers by total Profit and display them in a bar chart.", "M3: Top 10 Customers"),
    ("Is there a correlation between Discount and Profit? Create a scatter plot to show the relationship.", "M4: Discount vs Profit"),
]

CONTEXT_TESTS = [
    ("What are the top 3 regions by sales?", "C1: Top 3 Regions"),
    ("Now show the profit for those same regions", "C2: Follow-up (Context Test)"),
    ("Create a chart comparing them", "C3: Follow-up Chart (Context Test)"),
]

EDGE_CASES = [
    ("Show me everything", "EDGE1: Vague Query"),
    ("Calculate the average discount for products with negative profit", "EDGE2: Complex Filter"),
    ("What is the return rate?", "EDGE3: Missing Column"),
    ("", "EDGE4: Empty Query"),
]

def run_test_suite():
    """Run all tests."""
    print("\n" + "="*80)
    print("🚀 INTELLIGENT DATA ROOM - COMPREHENSIVE TEST SUITE")
    print("="*80)
    
    # Step 1: Upload file
    file_url = upload_file()
    if not file_url:
        print("\n❌ Cannot proceed without file upload")
        return
    
    results = {
        "easy": [],
        "medium": [],
        "context": [],
        "edge": []
    }
    
    # Test Easy Prompts
    print("\n\n" + "🟢"*40)
    print("EASY PROMPTS (5 tests)")
    print("🟢"*40)
    for question, name in EASY_TESTS:
        result = test_query(question, file_url, name)
        results["easy"].append(result)
    
    # Test Medium Prompts
    print("\n\n" + "🟡"*40)
    print("MEDIUM PROMPTS (4 tests)")
    print("🟡"*40)
    for question, name in MEDIUM_TESTS:
        result = test_query(question, file_url, name)
        results["medium"].append(result)
    
    # Test Context Retention
    print("\n\n" + "🔵"*40)
    print("CONTEXT RETENTION TESTS (3 tests)")
    print("🔵"*40)
    for question, name in CONTEXT_TESTS:
        result = test_query(question, file_url, name)
        results["context"].append(result)
    
    # Test Edge Cases
    print("\n\n" + "🔴"*40)
    print("EDGE CASE TESTS (4 tests)")
    print("🔴"*40)
    for question, name in EDGE_CASES:
        result = test_query(question, file_url, name)
        results["edge"].append(result)
    
    # Summary Report
    print("\n\n" + "="*80)
    print("📊 TEST SUMMARY REPORT")
    print("="*80)
    
    for category, tests in results.items():
        passed = sum(1 for t in tests if t["status"] == "PASS")
        total = len(tests)
        percentage = (passed / total * 100) if total > 0 else 0
        
        status_icon = "✅" if percentage == 100 else "⚠️" if percentage >= 50 else "❌"
        
        print(f"\n{status_icon} {category.upper()}: {passed}/{total} passed ({percentage:.1f}%)")
        
        for test in tests:
            icon = "✅" if test["status"] == "PASS" else "❌"
            print(f"   {icon} {test['test_name']}")
    
    # Overall Score
    all_tests = results["easy"] + results["medium"] + results["context"] + results["edge"]
    total_passed = sum(1 for t in all_tests if t["status"] == "PASS")
    total_tests = len(all_tests)
    overall_score = (total_passed / total_tests * 100) if total_tests > 0 else 0
    
    print(f"\n{'='*80}")
    print(f"🎯 OVERALL SCORE: {total_passed}/{total_tests} ({overall_score:.1f}%)")
    print(f"{'='*80}")
    
    if overall_score == 100:
        print("\n🎉 PERFECT SCORE! All requirements met!")
    elif overall_score >= 80:
        print("\n👍 GOOD! Most features working correctly.")
    elif overall_score >= 60:
        print("\n⚠️  NEEDS IMPROVEMENT: Some core features failing.")
    else:
        print("\n❌ CRITICAL: Many features not working.")
    
    # Save results to file
    with open('test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\n💾 Detailed results saved to: test_results.json")

if __name__ == "__main__":
    run_test_suite()
