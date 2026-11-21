from pathlib import Path

path = Path("backend/knowledge/services/gemini_client.py")
source = path.read_text(encoding="utf-8")

old = "text = re.sub(r'^\\s*[\\*\\-]\\s+', 'â€¢ ', text, flags=re.MULTILINE)"
new = "text = re.sub(r'^\\s*[\\*\\-]\\s+', '• ', text, flags=re.MULTILINE)"

if source.count(old) != 1:
    raise SystemExit("STOP: Expected corrupted bullet line was not found exactly once. No changes made.")

path.write_text(source.replace(old, new, 1), encoding="utf-8")
print("SUCCESS: Bullet character corrected. Other text unchanged.")
