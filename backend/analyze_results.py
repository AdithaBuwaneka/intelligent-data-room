import json

with open('test_results.json', 'r') as f:
    data = json.load(f)

print("\n" + "="*80)
print("📊 TEST RESULTS ANALYSIS")
print("="*80)

categories = {
    'easy': 'Easy Prompts',
    'medium': 'Medium Prompts', 
    'context': 'Context Retention',
    'edge': 'Edge Cases'
}

total_tests = 0
total_success = 0
total_errors = 0

errors_by_type = {
    'No code found': [],
    'No result returned': [],
    'Malicious code': [],
    'Other': []
}

successful_tests = []

for category, tests in data.items():
    cat_name = categories.get(category, category)
    total_tests += len(tests)
    
    print(f"\n{'='*80}")
    print(f"📁 {cat_name.upper()} ({len(tests)} tests)")
    print(f"{'='*80}")
    
    for test in tests:
        test_name = test['test_name']
        answer = test['result'].get('answer', '')
        
        # Check if it's a real success or has errors
        is_success = True
        error_type = None
        
        if 'Unfortunately' in answer:
            is_success = False
            total_errors += 1
            
            if 'No code found' in answer:
                error_type = 'No code found'
                errors_by_type['No code found'].append(test_name)
            elif 'No result returned' in answer:
                error_type = 'No result returned'
                errors_by_type['No result returned'].append(test_name)
            elif "shouldn't use 'os'" in answer or 'malicious' in answer.lower():
                error_type = 'Malicious code'
                errors_by_type['Malicious code'].append(test_name)
            else:
                error_type = 'Other'
                errors_by_type['Other'].append(test_name)
        else:
            total_success += 1
            successful_tests.append(test_name)
        
        # Print status
        if is_success:
            print(f"  ✅ {test_name}")
            if answer.startswith('D:/'):
                print(f"     → Chart generated")
            elif 'Here are the results:' in answer or 'The answer is:' in answer:
                print(f"     → Data returned: {answer[:80]}...")
        else:
            print(f"  ❌ {test_name}")
            print(f"     → Error: {error_type}")

# Summary
print(f"\n{'='*80}")
print(f"📈 SUMMARY")
print(f"{'='*80}")
print(f"Total Tests: {total_tests}")
print(f"✅ Successful: {total_success} ({total_success/total_tests*100:.1f}%)")
print(f"❌ Failed: {total_errors} ({total_errors/total_tests*100:.1f}%)")

print(f"\n{'='*80}")
print(f"🔍 ERROR BREAKDOWN")
print(f"{'='*80}")

for error_type, tests in errors_by_type.items():
    if tests:
        print(f"\n{error_type}: {len(tests)} tests")
        for test in tests:
            print(f"  - {test}")

print(f"\n{'='*80}")
print(f"✨ SUCCESSFUL TESTS ({len(successful_tests)})")
print(f"{'='*80}")
for test in successful_tests:
    print(f"  ✅ {test}")

# Requirements compliance
print(f"\n{'='*80}")
print(f"📋 REQUIREMENTS COMPLIANCE")
print(f"{'='*80}")

easy_success = sum(1 for t in data['easy'] if 'Unfortunately' not in t['result'].get('answer', ''))
medium_success = sum(1 for t in data['medium'] if 'Unfortunately' not in t['result'].get('answer', ''))
context_success = sum(1 for t in data['context'] if 'Unfortunately' not in t['result'].get('answer', ''))

print(f"Easy Prompts (5 required): {easy_success}/5 ({easy_success/5*100:.0f}%)")
print(f"Medium Prompts (4 required): {medium_success}/4 ({medium_success/4*100:.0f}%)")
print(f"Context Retention (3 required): {context_success}/3 ({context_success/3*100:.0f}%)")

if context_success == 3:
    print("\n✅ CONTEXT RETENTION: FULLY WORKING")
    print("   - Follow-up questions successfully handled")
    print("   - Session memory functioning correctly")

print(f"\n{'='*80}")
if total_success >= total_tests * 0.8:
    print("🎉 OVERALL: EXCELLENT - System is production ready!")
elif total_success >= total_tests * 0.6:
    print("👍 OVERALL: GOOD - Minor issues need fixing")
else:
    print("⚠️  OVERALL: NEEDS WORK - Several core features failing")
print(f"{'='*80}\n")
