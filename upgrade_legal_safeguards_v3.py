from pathlib import Path

path = Path("backend/knowledge/services/gemini_client.py")
source = path.read_text(encoding="utf-8")

anchor = '            f"STRICT JSON VALIDATION RULES:\\n"\n'

rules = '''            f"PROVISION-BY-PROVISION LEGAL REASONING RULES:\\\\n"
            f"- For every applicable_sections entry, explain the actual statutory ingredients in explanation.\\\\n"
            f"- In why_it_applies, identify supporting facts, missing facts, and facts that could make the provision inapplicable.\\\\n"
            f"- Never use a provision merely because its keywords resemble the user's description.\\\\n"
            f"- For Easements Act Section 15, distinguish 20 years for private property and 30 years for Government property. Examine the statutory two-year timing rule, open and peaceful enjoyment, enjoyment as of right, interruption, and permissive use.\\\\n"
            f"- Do not state that Section 15 is established without sufficient evidence for every required element.\\\\n"
            f"- For Easements Act Section 13, explain the relevant transfer or partition, common ownership, and necessity or quasi-easement requirements separately.\\\\n"
            f"- For BNS Section 126, explain the right to proceed, voluntary obstruction, and the statutory exception for a private way where the person in good faith believes they have a lawful right to obstruct it.\\\\n"
            f"- Do not infer criminal intent or criminal liability solely from a property boundary or access disagreement.\\\\n"
            f"- For Specific Relief Act Section 38, explain the conditions for a perpetual injunction and distinguish it from temporary relief.\\\\n"
            f"- For Specific Relief Act Section 39, explain the legal obligation and circumstances required for a mandatory injunction. Do not promise demolition or removal of a structure.\\\\n"
            f"- For CPC Order 39 Rules 1 and 2, assess prima facie case, balance of convenience, and irreparable injury. Explain that relief is discretionary.\\\\n"
            f"- Do not describe CPC Order 39 as a criminal offence or as an automatic right to demolish an existing wall.\\\\n"
            f"- In nature_of_offence_or_liability, explicitly identify whether the provision creates criminal liability, civil rights or remedies, or procedural relief.\\\\n"
            f"- In available_punishment_or_legal_consequence, give only consequences supported by the applicable statute. Distinguish statutory punishment from discretionary court relief.\\\\n"
            f"- Use Confirmed only if the available facts establish every essential applicability requirement. Otherwise use Potentially applicable.\\\\n"
            f"- If the legal provision cannot be reliably verified, disclose that uncertainty instead of inventing its title, wording, punishment, or consequence.\\\\n\\\\n"
'''

if source.count(anchor) != 1:
    raise SystemExit("STOP: Unique JSON instruction anchor not found. No changes made.")

backup = path.with_name("gemini_client.py.pre_legal_safeguards_v3_backup")
if backup.exists():
    raise SystemExit("STOP: V3 backup already exists. No changes made.")

backup.write_text(source, encoding="utf-8")
path.write_text(source.replace(anchor, rules + anchor, 1), encoding="utf-8")

print("SUCCESS: V3 provision-specific safeguards added.")
print("Backup:", backup.name)
