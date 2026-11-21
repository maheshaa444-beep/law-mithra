import os
import sys

sys.path.insert(0, os.path.abspath("backend"))

from knowledge.services.gemini_client import GeminiClient

query = """
Explain my rights under:
1. Indian Easements Act, Section 13: necessity versus quasi-easement.
2. Indian Easements Act, Section 15: 20-year and 30-year periods,
   interruption and the two-year timing requirement.
3. BNS Section 126: voluntary obstruction, right to proceed,
   and good-faith private-way exception.
4. BNSS Section 166: breach of peace and three-month or seasonal condition.
5. Specific Relief Act Sections 38 and 39.
6. CPC Order 39 Rules 1 and 2.
"""

incomplete = """
Section 6 of the Specific Relief Act may apply in certain cases.
A temporary injunction may also be available.
"""

complete = """
Easements Act Section 13 distinguishes easement of necessity from
quasi-easement. Common ownership, transfer and partition are relevant.

Section 15 requires 20 years for private property and 30 years for
Government property. Statutory interruption and the two-year timing
requirement must be considered.

BNS Section 126 concerns voluntary obstruction of a person with a
right to proceed. The good-faith exception for a private way must
also be considered.

BNSS Section 166 requires a dispute likely to cause a breach of peace.
The three-month condition applies to rights exercised throughout
the year. Seasonal or occasional rights require examination of the
last season or last occasion.

Specific Relief Act Section 38 concerns a perpetual injunction.
Section 39 concerns a mandatory injunction.

CPC Order 39 requires consideration of a prima facie case,
balance of convenience and irreparable injury.
"""

def make_client(gemini_answers, router_answers=None):
    client = GeminiClient()
    calls = {"gemini": 0, "router": 0}

    def fake_gemini(*args, **kwargs):
        calls["gemini"] += 1
        return gemini_answers.pop(0) if gemini_answers else None

    def fake_router(*args, **kwargs):
        calls["router"] += 1
        return router_answers.pop(0) if router_answers else None

    client._call_gemini_raw = fake_gemini
    client._call_openrouter_raw = fake_router
    return client, calls

# TEST 1: Gemini initial answer incomplete, retry complete.
client, calls = make_client([incomplete, complete])
result = client.generate_legal_response(query)

assert result is not None
assert "Completeness notice:" not in result
assert calls == {"gemini": 2, "router": 0}
print("TEST 1 PASSED: Gemini retry completed the answer.")
print("Calls:", calls)

# TEST 2: Both retries remain incomplete; warning must be shown.
client, calls = make_client(
    [incomplete, incomplete],
    [incomplete]
)
result = client.generate_legal_response(query)

assert result is not None
assert "Completeness notice:" in result
assert calls == {"gemini": 2, "router": 1}
print("\nTEST 2 PASSED: Persistent omissions produced a warning.")
print("Calls:", calls)

# TEST 3: Greeting should not trigger completeness retries.
client, calls = make_client(["Hello! I am Law Mithra."])
result = client.generate_legal_response("Hello")

assert result is not None
assert "Completeness notice:" not in result
assert calls == {"gemini": 1, "router": 0}
print("\nTEST 3 PASSED: Greeting bypassed completeness retry.")
print("Calls:", calls)

print("\nSUCCESS: All three offline retry tests passed.")
print("No live AI API calls were made.")
