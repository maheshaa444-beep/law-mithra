from pathlib import Path

path = Path("backend/knowledge/services/gemini_client.py")
source = path.read_text(encoding="utf-8")

old = '''            f"LANGUAGE: {language}\\n\\n"
            f"MANDATORY JSON OUTPUT FORMAT:\\n"
'''

new = '''            f"LANGUAGE: {language}\\n\\n"
            f"STRICT JSON VALIDATION RULES:\\n"
            f"- Return every required top-level section and field.\\n"
            f"- Every field defined as a list must be a JSON array.\\n"
            f"- Every string-list array must contain only non-empty strings.\\n"
            f"- If no reliable or relevant item exists, return an empty array: [].\\n"
            f"- Never use null, a single string, or an object instead of an array.\\n"
            f"- Do not invent evidence, legal provisions, precedents, deadlines, or facts.\\n"
            f"- Keep evidence_to_preserve as an array of relevant evidence items.\\n"
            f"- Return valid, complete JSON only; do not omit required fields.\\n\\n"
            f"MANDATORY JSON OUTPUT FORMAT:\\n"
'''

if source.count(old) != 1:
    raise SystemExit("STOP: Prompt insertion point was not uniquely found. No changes made.")

backup = path.with_name("gemini_client.py.pre_prompt_rules_backup")
backup.write_text(source, encoding="utf-8")

path.write_text(source.replace(old, new, 1), encoding="utf-8")
print("Strict JSON formatting instructions added. Backup created.")
