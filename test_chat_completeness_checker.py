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

incomplete_answer = """
Section 6 of the Specific Relief Act may apply if there has been
qualifying dispossession. A temporary injunction may also be available.
"""

complete_answer = """
Under Indian Easements Act Section 13, an easement of necessity is
different from a quasi-easement. The analysis considers common ownership,
transfer or partition, and the relevant prior use.

Under Section 15, prescription generally requires 20 years for private
property and 30 years for Government property. The use must satisfy the
statutory conditions. Statutory interruption and the two-year timing
requirement must also be examined.

BNS Section 126 concerns voluntary obstruction of a person who has a
right to proceed. The good-faith exception for obstruction of a private
way must also be considered.

BNSS Section 166 concerns a dispute likely to cause a breach of peace.
For a right exercised throughout the year, the three-month condition
must be examined. Seasonal or occasional use requires consideration of
the last season or last occasion.

Specific Relief Act Section 38 concerns a perpetual or permanent
injunction. Section 39 concerns a mandatory injunction.

Under CPC Order 39, the court considers a prima facie case, balance of
convenience and irreparable injury when deciding temporary injunctions.
"""

missing = GeminiClient._missing_requested_legal_topics(
    query, incomplete_answer
)

complete_missing = GeminiClient._missing_requested_legal_topics(
    query, complete_answer
)

print("\nINCOMPLETE ANSWER CHECK")
for item in missing:
    print("-", item)

print("\nCOMPLETE ANSWER CHECK")
print("Missing topics:", complete_missing)

assert len(missing) >= 10, (
    "FAIL: The checker did not detect enough missing topics."
)

assert complete_missing == [], (
    "FAIL: The complete sample was incorrectly flagged."
)

print("\nSUCCESS: Both completeness-checker tests passed.")
print("NOTE: This tests topic coverage, not legal correctness.")
