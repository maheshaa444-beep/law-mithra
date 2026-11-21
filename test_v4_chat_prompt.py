import sys
from pathlib import Path

sys.path.insert(0, str(Path("backend").resolve()))

from knowledge.services.gemini_client import GeminiClient

client = GeminiClient(api_key="offline-test")
captured = {}

def mock_gemini(prompt, **kwargs):
    captured["prompt"] = prompt
    captured["kwargs"] = kwargs
    return "Offline test response"

client._call_gemini_raw = mock_gemini

result = client.generate_legal_response(
    "A neighbour blocked a pathway used by my family for several years."
)

prompt = captured.get("prompt", "")

required_rules = [
    "STATUTORY PRECISION RULES (V4)",
    "two years immediately preceding",
    "one year after notice",
    "quasi-easement",
    "three months before",
    "good faith",
    "BHARATIYA NYAYA SANHITA, 2023",
    "BHARATIYA NAGARIK SURAKSHA SANHITA, 2023",
]

missing = [rule for rule in required_rules if rule.lower() not in prompt.lower()]

print("Gemini API called: NO (mocked)")
print("Prompt captured:", bool(prompt))
print("Mock response:", result)

if missing:
    print("FAILED — Missing rules:", missing)
    raise SystemExit(1)

print("SUCCESS: All V4 rules reached the normal chat prompt.")
