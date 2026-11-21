from pathlib import Path

path = Path("backend/knowledge/services/gemini_client.py")
source = path.read_text(encoding="utf-8")

anchor = "RESPONSE STYLE:\n"

if source.count(anchor) != 1:
    raise SystemExit("STOP: Expected prompt anchor was not found exactly once. No changes made.")

backup = path.with_name("gemini_client.py.pre_chat_legal_safeguards_backup")

if backup.exists():
    raise SystemExit("STOP: Backup already exists. No changes made.")

rules = """PROVISION-SPECIFIC LEGAL SAFEGUARDS:

- Verify the actual statutory ingredients before mentioning or recommending any legal provision.
- For Easements Act Section 15, distinguish 20 years for private property from 30 years where the property belongs to Government. Examine open and peaceful enjoyment, enjoyment as of right, interruption, permissive use and the statutory two-year timing requirement.
- Never infer the required prescriptive period from phrases such as several years or a long time.
- For Easements Act Section 13, examine common ownership, transfer or partition, and the requirements for necessity or quasi-easement. Do not treat a convenient route as automatically creating an easement of necessity.
- Do not apply Section 6 of the Specific Relief Act merely because someone is prevented from using a pathway. Examine whether there was actual dispossession from immovable property. Explain its six-month requirement only when Section 6 genuinely applies.
- Distinguish Specific Relief Act Section 38 (perpetual injunction) from Section 39 (mandatory injunction). A mandatory injunction is discretionary and must not be presented as an automatic right to demolish a wall.
- For CPC Order 39 Rules 1 and 2, examine prima facie case, balance of convenience and irreparable injury. Temporary injunctions are discretionary and are not the same as mandatory injunctions.
- For BNS Section 126, examine the person's legal right to proceed, voluntary obstruction and the statutory good-faith exception concerning a private way. Do not infer criminal liability merely because a pathway is blocked.
- Do not automatically describe a property access dispute as criminal trespass. Verify the statutory requirements, including the necessary entry or unlawful remaining and intent.
- When discussing a dispute about a right of use of land or water, consider whether BNSS Section 166 is relevant. Do not automatically substitute BNSS Section 164 for every such dispute; distinguish proceedings concerning possession and breach of peace from disputes about a right of use.
- Do not present old IPC or CrPC provisions as current law without clearly identifying them as historical references and checking the applicable transition rules.
- Distinguish civil rights, civil remedies, criminal offences and preventive or procedural proceedings.
- For every provision mentioned, explain why it may apply, which facts remain unverified, and what facts could make it inapplicable.
- If essential facts are missing, qualify the provision as potentially applicable and ask focused questions.
- Never invent statutory wording, punishment, limitation periods, case citations or legal consequences. If uncertain, disclose the uncertainty and recommend verification against current official legislation.
- Never guarantee that a police complaint, injunction, prosecution or removal of a structure will succeed.

"""

backup.write_text(source, encoding="utf-8")
path.write_text(source.replace(anchor, rules + anchor, 1), encoding="utf-8")

print("SUCCESS: Normal-chat legal safeguards added.")
print("Backup:", backup.name)
