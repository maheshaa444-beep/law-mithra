from pathlib import Path

path = Path("backend/knowledge/services/gemini_client.py")
source = path.read_text(encoding="utf-8")

anchor = '            f"LANGUAGE: {language}\\n\\n"\n'

rules = '''            f"ADDITIONAL LEGAL ACCURACY SAFEGUARDS:\\n"
            f"- For Easements Act Section 15, distinguish the ordinary 20-year period from the 30-year period where the property belongs to Government.\\n"
            f"- Check that the relevant prescriptive period ends within two years before institution of the suit.\\n"
            f"- Examine permissive use, actual interruption, and whether enjoyment was as an easement and as of right.\\n"
            f"- Never conclude that an easement exists merely because a pathway has been used for several years.\\n"
            f"- For Easements Act Section 13, identify the relevant common ownership and transfer or partition facts before assessing necessity or quasi-easement.\\n"
            f"- For BNS Section 126, separately examine voluntary obstruction, the person's legal right to proceed, and the statutory good-faith private-way exception.\\n"
            f"- Do not describe BNS Section 126 as an established offence merely because access has been blocked.\\n"
            f"- For CPC Order 39 Rules 1 and 2, describe temporary injunctions as discretionary judicial relief, not an automatic entitlement. Explain the relevant factual requirements.\\n"
            f"- Do not describe a temporary injunction as an order to demolish or permanently remove an existing structure.\\n"
            f"- Distinguish temporary injunctions under CPC Order 39 from mandatory injunctions under Section 39 of the Specific Relief Act, 1963.\\n"
            f"- Explain that a mandatory injunction is discretionary and depends on the legal obligation and facts established before the court.\\n"
            f"- Never mark a legal provision Confirmed merely because it is relevant in principle. If essential facts are missing, use Potentially applicable or another appropriately qualified status.\\n"
            f"- Never guarantee an injunction, removal of a wall, criminal prosecution, punishment, or legal outcome.\\n"
            f"- Clearly distinguish a possible legal remedy from a proven right and from relief actually granted by a court.\\n\\n"
'''

if source.count(anchor) != 1:
    raise SystemExit("STOP: Unique insertion point not found. No changes made.")

backup = path.with_name("gemini_client.py.pre_legal_safeguards_v2_backup")
if backup.exists():
    raise SystemExit("STOP: V2 backup already exists. No changes made.")

backup.write_text(source, encoding="utf-8")
path.write_text(source.replace(anchor, rules + anchor, 1), encoding="utf-8")

print("SUCCESS: Additional legal accuracy safeguards added.")
print("Backup:", backup.name)
