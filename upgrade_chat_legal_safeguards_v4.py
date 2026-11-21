from pathlib import Path

path = Path("backend/knowledge/services/gemini_client.py")
source = path.read_text(encoding="utf-8")

anchor = "RESPONSE STYLE:"
marker = "STATUTORY PRECISION RULES (V4):"

if source.count(anchor) != 1:
    raise SystemExit("STOP: RESPONSE STYLE anchor is not unique. No changes made.")

if marker in source:
    raise SystemExit("STOP: V4 rules already exist. No changes made.")

block = """
STATUTORY PRECISION RULES (V4):

EASEMENTS ACT, 1882 — SECTION 15:
- For prescription, distinguish 20 years for private property from 30 years where the property belongs to Government.
- Verify open, peaceable and uninterrupted enjoyment as an easement, as of right, without permission or agreement.
- The statutory period must end within the two years immediately preceding the institution of the suit in which the claim is contested. Do not misstate this as a general rule to file a suit within two years of the obstruction.
- Explain that statutory interruption requires actual cessation due to obstruction by another person, followed by submission or acquiescence for one year after notice of the obstruction and the identity of the obstructing person.
- Do not automatically treat every temporary blockage as a completed statutory interruption.
- Do not assume that vague descriptions such as several years establish the required period.

EASEMENTS ACT, 1882 — SECTION 13:
- Distinguish an easement of necessity from a quasi-easement.
- Examine whether the relevant properties passed by transfer, bequest, partition or another legally relevant event involving common ownership.
- For necessity, identify the facts supporting genuine necessity arising from that event.
- For a quasi-easement, examine whether the prior use was apparent and continuous and necessary for enjoying the property as it was enjoyed when the transfer or partition took effect, subject to the statutory requirements and contrary intention.
- Do not assume neighbouring ownership alone proves common ownership or an easement.
- Do not state categorically that any alternative route defeats a claim. Assess the actual legal test and facts.
- Distinguish an easement claimed under Section 13 from a right created by an express grant.

BHARATIYA NYAYA SANHITA, 2023 — SECTION 126:
- Identify whether the affected person had a legal right to proceed along the relevant way.
- Examine voluntary obstruction and the other statutory ingredients.
- Explicitly consider the exception for obstruction of a private way where the person acts in good faith believing they have a lawful right to obstruct it.
- Do not infer an offence merely from the existence of a wall or disagreement about property boundaries.

BHARATIYA NAGARIK SURAKSHA SANHITA, 2023 — SECTION 166:
- Explain that this is a proceeding before an Executive Magistrate concerning a dispute about an alleged right of use of land or water, including an easement, where the dispute is likely to cause a breach of peace.
- Do not describe it as an automatic remedy for every blocked pathway or as a final determination of ownership.
- Examine the statutory inquiry, the parties' claims and evidence before describing any possible order.
- For a right exercisable throughout the year, address the requirement that it was exercised within three months before the relevant police report or other information. For a seasonal or occasional right, address the corresponding last-season or last-occasion requirement.
- Explain that an order to prevent interference or remove an obstruction depends on the statutory conditions and the Magistrate's findings. Never promise demolition.
- Do not treat Sections 164 and 166 as interchangeable. Explain any relevance of Section 164 only where legally justified.

GENERAL PRECISION:
- Separate what the statute requires from whether the user's facts satisfy those requirements.
- If a necessary fact is unknown, say that the legal position cannot yet be determined and identify the evidence needed.
- Do not convert a possible legal argument into a confirmed right, offence or guaranteed remedy.

"""

path.write_text(source.replace(anchor, block + anchor, 1), encoding="utf-8")

print("SUCCESS: V4 statutory precision rules added.")
print("Backup: gemini_client.py.pre_legal_safeguards_v4_backup")
