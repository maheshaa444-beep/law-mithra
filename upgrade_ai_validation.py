
from pathlib import Path

path = Path(__file__).parent / "backend" / "knowledge" / "services" / "gemini_client.py"
source = path.read_text(encoding="utf-8")

start = source.index("    def _call_gemini_raw(")
end = source.index("    def _call_groq_raw(", start)

replacement = '''    def _call_gemini_raw(
        self,
        prompt: str,
        max_tokens: int = 2048,
        temperature: float = 0.1
    ) -> Optional[str]:
        """Return only non-empty, completed Gemini responses."""
        if not self.api_key:
            logger.warning("Gemini API key is not configured.")
            return None

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            }
        }

        body_bytes = json.dumps(payload).encode("utf-8")

        for model in GEMINI_MODELS:
            url = (
                "https://generativelanguage.googleapis.com/v1beta/"
                f"{model}:generateContent?key={self.api_key}"
            )
            req = urllib.request.Request(
                url,
                data=body_bytes,
                headers={"Content-Type": "application/json"},
                method="POST"
            )

            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as res:
                    data = json.loads(res.read().decode("utf-8"))

                candidates = data.get("candidates", [])
                if not candidates:
                    logger.warning("Gemini %s returned no candidates.", model)
                    continue

                candidate = candidates[0]
                finish_reason = candidate.get("finishReason")

                if finish_reason not in (None, "STOP"):
                    logger.warning(
                        "Gemini %s response rejected: %s",
                        model, finish_reason
                    )
                    continue

                parts = candidate.get("content", {}).get("parts", [])
                response_text = " ".join(
                    part["text"].strip()
                    for part in parts
                    if isinstance(part, dict)
                    and isinstance(part.get("text"), str)
                    and part["text"].strip()
                )

                if response_text:
                    return response_text

                logger.warning("Gemini %s returned empty text.", model)

            except Exception as exc:
                logger.warning("Gemini model %s attempt failed: %s", model, exc)

        return None

    def _call_openrouter_raw(
        self,
        prompt: str,
        max_tokens: int = 1024
    ) -> Optional[str]:
        """Return only non-empty, completed OpenRouter responses."""
        if not self.openrouter_key:
            logger.warning("OpenRouter API key is not configured.")
            return None

        models = [
            "mistralai/mistral-small-3.2-24b-instruct-2506:free",
            "deepseek/deepseek-r1:free",
            "google/gemini-2.0-flash-lite:free",
            "meta-llama/llama-3.2-3b-instruct:free",
        ]

        payload = {
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are Law Mithra, an Indian legal information "
                        "assistant. Never invent legal provisions or deadlines."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,
            "max_tokens": max_tokens,
        }

        for model in models:
            payload["model"] = model
            req = urllib.request.Request(
                "https://openrouter.ai/api/v1/chat/completions",
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {self.openrouter_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://lawmithra.in",
                    "X-Title": "Law Mithra",
                },
                method="POST"
            )

            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as res:
                    data = json.loads(res.read().decode("utf-8"))

                choices = data.get("choices", [])
                if not choices:
                    logger.warning("OpenRouter %s returned no choices.", model)
                    continue

                choice = choices[0]
                finish_reason = choice.get("finish_reason")

                if finish_reason not in (None, "stop"):
                    logger.warning(
                        "OpenRouter %s response rejected: %s",
                        model, finish_reason
                    )
                    continue

                content = choice.get("message", {}).get("content")
                if isinstance(content, str) and content.strip():
                    return content.strip()

                logger.warning("OpenRouter %s returned empty text.", model)

            except Exception as exc:
                logger.warning(
                    "OpenRouter model %s attempt failed: %s", model, exc
                )

        return None

'''

path.write_text(source[:start] + replacement + source[end:], encoding="utf-8")
print("Gemini and OpenRouter response validation upgraded.")
