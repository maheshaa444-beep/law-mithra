from pathlib import Path

path = Path("upgrade_pathway_law_context.py")
script = path.read_text(encoding="utf-8")

old = '''if source.count("        'remedies_en': [", domain_start) != 1:
    raise SystemExit("STOP: remedies_en boundary is not unique in land_encroachment.")
'''

new = '''cheque_start = source.index("'id': 'cheque_bounce'", domain_start)
land_domain = source[domain_start:cheque_start]

if land_domain.count("        'remedies_en': [") != 1:
    raise SystemExit("STOP: remedies_en boundary is not unique in land_encroachment.")
'''

if script.count(old) != 1:
    raise SystemExit("STOP: Expected check not found exactly once. No changes made.")

path.write_text(script.replace(old, new, 1), encoding="utf-8")
print("SUCCESS: Update script boundary check corrected.")
