from backend.knowledge.services.gemini_client import clean_legal_text

sample = "* First item\n- ಎರಡನೇ ಅಂಶ\nKannada: ನಮಸ್ಕಾರ"
result = clean_legal_text(sample)

print("FORMATTED OUTPUT:")
print(result)

assert "• First item" in result
assert "• ಎರಡನೇ ಅಂಶ" in result
assert "ನಮಸ್ಕಾರ" in result
assert "â€¢" not in result

print("\nSUCCESS: Bullet formatting and Kannada text tests passed.")
