from pathlib import Path

path = Path("backend/knowledge/services/legal_ai_service.py")
source = path.read_text(encoding="utf-8")

domain_start = source.index("'id': 'land_encroachment'")
laws_start = source.index("        'applicable_laws': [", domain_start)
remedies_start = source.index("        'remedies_en': [", laws_start)

old_laws = source[laws_start:remedies_start]

new_laws = """        'applicable_laws': [
            {
                'act': 'Indian Easements Act, 1882',
                'sections': ['Section 13'],
                'english_statute': 'Section 13: Easements of necessity and quasi-easements. The section addresses rights arising when immovable property is transferred or bequeathed, or joint property is partitioned. Necessity easements and quasi-easements have distinct requirements. A quasi-easement generally requires an apparent and continuous use that was necessary for enjoying the property as it was enjoyed when the transfer or partition took effect, subject to the statutory conditions and any contrary intention.',
                'summary': 'Examine common ownership followed by transfer, bequest or partition; distinguish genuine necessity from a quasi-easement. Neighbouring ownership alone does not establish a Section 13 right.'
            },
            {
                'act': 'Indian Easements Act, 1882',
                'sections': ['Section 15'],
                'english_statute': 'Section 15: Acquisition by prescription. A right of way or other easement may become absolute after peaceable and open enjoyment, as of right and without interruption, for 20 years; where the property over which the right is claimed belongs to Government, the period is 30 years. The relevant period must end within two years immediately before institution of the suit in which the claim is contested. Enjoyment by permission or agreement may not qualify. Under Explanation II, interruption requires actual cessation due to another person’s obstruction and submission to or acquiescence in that obstruction for one year after notice of the obstruction and the person responsible.',
                'summary': 'Assess the correct 20-year or 30-year period, open and peaceable use as of right, permission, interruption and the statutory two-year timing rule. Vague use over several years is insufficient to establish prescription.'
            },
            {
                'act': 'Specific Relief Act, 1963',
                'sections': ['Section 38', 'Section 39'],
                'english_statute': 'Section 38 concerns perpetual injunctions to prevent breach of an obligation or invasion of property rights in the circumstances specified by the Act. Section 39 concerns mandatory injunctions: the court may, in its discretion, require acts necessary to prevent breach of an obligation. Neither provision makes an injunction or removal of a wall automatic.',
                'summary': 'Possible civil remedies include a perpetual injunction and, where legally justified, a discretionary mandatory injunction. The claimant must establish the relevant right, obligation and statutory conditions.'
            },
            {
                'act': 'Code of Civil Procedure, 1908',
                'sections': ['Order 39 Rule 1', 'Order 39 Rule 2'],
                'english_statute': 'Order 39 Rules 1 and 2 govern temporary injunctions during a civil suit. Interim relief is discretionary and is assessed using principles including a prima facie case, balance of convenience and irreparable injury. A temporary injunction is distinct from a final mandatory injunction ordering removal of an existing structure.',
                'summary': 'A party may seek interim protection in a properly instituted civil suit, but relief depends on evidence and judicial assessment; it is not an automatic stay.'
            },
            {
                'act': 'Bharatiya Nyaya Sanhita, 2023',
                'sections': ['Section 126'],
                'english_statute': 'Section 126: Wrongful restraint. The provision concerns voluntary obstruction that prevents a person from proceeding in a direction in which that person has a right to proceed. The statutory exception states that obstruction of a private way over land or water is not an offence where the person obstructing it in good faith believes they have a lawful right to do so.',
                'summary': 'Consider only if there is evidence of voluntary obstruction and the affected person had a legal right to proceed. Assess the good-faith private-way exception and do not infer an offence merely because a wall exists.'
            },
            {
                'act': 'Bharatiya Nagarik Suraksha Sanhita, 2023',
                'sections': ['Section 166'],
                'english_statute': 'Section 166: Dispute concerning right of use of land or water. An Executive Magistrate may act where a dispute about an alleged right of use, including an easement, is likely to cause a breach of the peace. The section provides for written proceedings, claims and evidence. For a right exercisable throughout the year, the right must have been exercised within three months before the relevant police report or other information; for a seasonal or occasional right, the corresponding requirement concerns the last season or occasion. Any order depends on the statutory inquiry and findings.',
                'summary': 'A conditional magisterial procedure for qualifying right-of-use disputes likely to cause a breach of peace. It is not an automatic remedy, a final determination of ownership, or a guaranteed demolition order.'
            },
            {
                'act': 'Specific Relief Act, 1963',
                'sections': ['Section 6'],
                'english_statute': 'Section 6 provides a summary suit for recovery of possession where a person has been dispossessed of immovable property without consent and otherwise than in due course of law. The suit must be brought within six months of dispossession, subject to the statutory conditions. Mere obstruction of a pathway does not by itself establish dispossession for this section.',
                'summary': 'Consider only if the facts establish actual qualifying dispossession from immovable property and the six-month statutory period and other requirements are met.'
            }
        ],
"""

if source.count("        'applicable_laws': [", domain_start) < 1:
    raise SystemExit("STOP: applicable_laws block not found.")
if not old_laws.rstrip().endswith("],"):
    raise SystemExit("STOP: Unexpected applicable_laws block ending.")
cheque_start = source.index("'id': 'cheque_bounce'", domain_start)
land_domain = source[domain_start:cheque_start]

if land_domain.count("        'remedies_en': [") != 1:
    raise SystemExit("STOP: remedies_en boundary is not unique in land_encroachment.")

source = source[:laws_start] + new_laws + source[remedies_start:]

remedies_start = source.index("        'remedies_en': [", domain_start)
remedies_end = source.index("        'remedies_kn': [", remedies_start)

new_remedies = """        'remedies_en': [
            '1. Collect title deeds, sale or partition documents, survey records, village maps, tax records, photographs and reliable evidence showing the pathway, its location and history of use.',
            '2. Establish whether the claimed right arises from an express grant, necessity or quasi-easement under Section 13, prescription under Section 15, or another legally recognised basis. Record the exact period and whether use was permissive or as of right.',
            '3. Consult a qualified local civil advocate about an appropriate declaration or injunction claim under the Specific Relief Act and whether temporary relief under Order 39 Rules 1 and 2 CPC is justified by the evidence.',
            '4. Consider BNSS Section 166 only if the dispute concerns an alleged right of use and is likely to cause a breach of peace; check the applicable three-month or last-season/occasion condition and prepare supporting evidence.',
            '5. Consider BNS Section 126 only if the evidence supports voluntary obstruction of a person who has a legal right to proceed, after assessing the statutory good-faith private-way exception.',
            '6. Do not assume that Section 6 of the Specific Relief Act applies unless there was actual qualifying dispossession. Have an advocate assess the correct remedy, limitation and forum before filing.'
        ],
"""

source = source[:remedies_start] + new_remedies + source[remedies_end:]

path.write_text(source, encoding="utf-8")
print("SUCCESS: Pathway-specific legal context and English remedies updated.")
print("Preserved: Kannada, Hindi, Tamil, Telugu and other existing domain entries.")
print("Preserved: cheque_bounce domain and all other source content.")
