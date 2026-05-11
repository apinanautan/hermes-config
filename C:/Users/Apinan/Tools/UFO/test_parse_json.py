from ufo import utils

# Test with think block and capitalized keys
test1 = """<think>
Some thinking here.


{
  "Observation": "User asked for JSON",
  "Thought": "I should respond",
  "Plan": ["Step 1", "Step 2"]
}
"""

# Test without think block
test2 = '{"Observation": "test", "Thought": "think", "Plan": []}'

print('Test 1 (with think block):')
try:
    r1 = utils.json_parser(test1)
    print('  Result:', r1)
    print('  Keys:', list(r1.keys()))
except Exception as e:
    print('  Error:', e)

print()
print('Test 2 (capitalized keys):')
try:
    r2 = utils.json_parser(test2)
    print('  Result:', r2)
    print('  Keys:', list(r2.keys()))
except Exception as e:
    print('  Error:', e)