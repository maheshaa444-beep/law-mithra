from pathlib import Path

path = Path("backend/knowledge/services/gemini_client.py")
source = path.read_text(encoding="utf-8")

anchor = '            f"LANGUAGE: {language}\\n\\n"\n'

rules = '''            f"INDIAN LEGAL REASONING SAFEGUARDS:\\n"
            f"- Distinguish established facts, allegations, assumptions, and missing information.\\n"
            f"- Never treat unverified allegations as proven.\\n"
            f"- Apply legal provisions only when their essential statutory ingredients are supported by facts.\\n"
            f"- Use Potentially applicable when essential facts need verification.\\n"
            f"- Never infer a 20-year period from vague phrases such as several years.\\n"
            f"- For Easements Act Section 15, examine the 20-year period, open and peaceful enjoyment, enjoyment as of right, interruption, and statutory timing requirements.\\n"
            f"- For Easements Act Section 13, examine common ownership, transfer or partition, and necessity requirements.\\n"
            f"- Examine statutory exceptions, mental elements, and possible defences for criminal provisions.\\n"
            f"- For BNS Section 126, examine the good-faith private-way obstruction exception.\\n"
            f"- Distinguish civil remedies from criminal offences.\\n"
            f"- Present possible arguments and defences for all relevant parties.\\n"
            f"- Never invent legal provisions, precedents, deadlines, or facts.\\n"
            f"- Verify applicable law against current official legislation and judgments.\\n\\n"
'''

if source.count(anchor) != 1:
    raise SystemExit("STOP: Anchor not unique. No changes made.")

backup = path.with_name("gemini_client.py.pre_legal_safeguards_backup")
if backup.exists():
    raise SystemExit("STOP: Backup already exists. No changes made.")

backup.write_text(source, encoding="utf-8")
path.write_text(source.replace(anchor, rules + anchor, 1), encoding="utf-8")

print("SUCCESS: Legal safeguards added. Backup created.")
