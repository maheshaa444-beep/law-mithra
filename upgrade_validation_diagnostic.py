from pathlib import Path

path = Path("backend/knowledge/services/gemini_client.py")
source = path.read_text(encoding="utf-8")

old = '''        if not all(text_list(strategy.get(key)) for key in strategy_list_fields):
            return False, "A lawyer_strategy list is missing or invalid."
'''

new = '''        for key in strategy_list_fields:
            if not text_list(strategy.get(key)):
                return False, (
                    f"lawyer_strategy.{key} must be a list "
                    "containing only non-empty strings."
                )
'''

if source.count(old) != 1:
    raise SystemExit("STOP: Expected validation block not found uniquely. No changes made.")

backup = path.with_name("gemini_client.py.pre_diagnostic_backup")
backup.write_text(source, encoding="utf-8")

path.write_text(source.replace(old, new, 1), encoding="utf-8")
print("Detailed validation diagnostics added. Backup created.")
