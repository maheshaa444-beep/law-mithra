from pathlib import Path

path = Path("backend/knowledge/services/gemini_client.py")
source = path.read_text(encoding="utf-8")

old = '        a = (response or "").casefold()'
new = '        a = re.sub(r"\\s+", " ", (response or "").casefold())'

if source.count(old) != 1:
    raise SystemExit("STOP: Expected exactly one matching line. No changes made.")

path.write_text(source.replace(old, new, 1), encoding="utf-8")
print("SUCCESS: Response whitespace normalization added.")
