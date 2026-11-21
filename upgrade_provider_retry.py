from pathlib import Path

path = Path("backend/knowledge/services/gemini_client.py")
source = path.read_text(encoding="utf-8")

old = '''        raw = self._call_gemini_raw(prompt, max_tokens=6000, temperature=0.1)
        if not raw:
            logger.warning("Gemini unavailable for case analysis. Trying OpenRouter.")
            raw = self._call_openrouter_raw(prompt, max_tokens=6000)

        if raw:
            clean = raw.strip()
            if clean.startswith("```"):
                clean = re.sub(r'^```(?:json)?\\s*', '', clean)
                clean = re.sub(r'\\s*```$', '', clean)
            try:
                data = json.loads(clean)
                is_valid, reason = self._validate_case_analysis(data)
                if is_valid:
                    return data
                logger.warning("Rejected incomplete case analysis JSON: %s", reason)
            except (json.JSONDecodeError, TypeError, ValueError) as exc:
                logger.warning("Failed to parse case analysis JSON: %s", exc)

        return self._generate_fallback_case_analysis(case_text, language)
'''

new = '''        providers = [
            ("Gemini", lambda: self._call_gemini_raw(
                prompt, max_tokens=6000, temperature=0.1
            )),
            ("OpenRouter", lambda: self._call_openrouter_raw(
                prompt, max_tokens=6000
            )),
        ]

        for provider_name, provider_call in providers:
            raw = provider_call()

            if not raw:
                logger.warning("%s returned no case-analysis response.", provider_name)
                continue

            clean = raw.strip()
            if clean.startswith("```"):
                clean = re.sub(r'^```(?:json)?\\s*', '', clean)
                clean = re.sub(r'\\s*```$', '', clean)

            try:
                data = json.loads(clean)
            except (json.JSONDecodeError, TypeError, ValueError) as exc:
                logger.warning("%s returned invalid case-analysis JSON: %s", provider_name, exc)
                continue

            is_valid, reason = self._validate_case_analysis(data)
            if is_valid:
                logger.info("%s produced valid case-analysis JSON.", provider_name)
                return data

            logger.warning("Rejected %s case-analysis JSON: %s", provider_name, reason)

        logger.warning("All AI providers failed case-analysis validation. Using safe fallback.")
        return self._generate_fallback_case_analysis(case_text, language)
'''

if source.count(old) != 1:
    raise SystemExit("STOP: Expected code block not found exactly once. No changes made.")

backup = path.with_name("gemini_client.py.pre_provider_retry_backup")
backup.write_text(source, encoding="utf-8")
path.write_text(source.replace(old, new, 1), encoding="utf-8")

print("Provider validation retry added. Backup created.")
