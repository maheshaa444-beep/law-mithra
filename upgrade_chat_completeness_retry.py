from pathlib import Path

path = Path("backend/knowledge/services/gemini_client.py")
source = path.read_text(encoding="utf-8")

old = '''        response = self._call_gemini_raw(
            prompt,
            max_tokens=3000 if not is_greeting else 300,
            temperature=0.2
        )

        if not response:
            logger.warning("Gemini unavailable. Trying OpenRouter.")
            response = self._call_openrouter_raw(
                prompt,
                max_tokens=3000 if not is_greeting else 300
            )

        if response:
            return clean_legal_text(response)

        logger.error("All configured AI providers failed to generate a response.")
        return None
'''

new = '''        response = self._call_gemini_raw(
            prompt,
            max_tokens=3000 if not is_greeting else 300,
            temperature=0.2
        )

        if not response:
            logger.warning("Gemini unavailable. Trying OpenRouter.")
            response = self._call_openrouter_raw(
                prompt,
                max_tokens=3000 if not is_greeting else 300
            )

        if response and not is_greeting:
            best_response = response
            missing_topics = self._missing_requested_legal_topics(
                query, best_response
            )

            if missing_topics:
                logger.warning(
                    "Chat response omitted %d requested legal topics. "
                    "Attempting a focused completeness retry.",
                    len(missing_topics)
                )

                context_for_retry = (
                    json.dumps(statutory_context, ensure_ascii=False, indent=2)
                    if statutory_context else "No statutory context was supplied."
                )

                retry_prompt = f"""
You are correcting an incomplete Indian legal information response.

ORIGINAL USER QUESTION:
{query}

APPLICATION-SUPPLIED STATUTORY CONTEXT:
{context_for_retry}

PREVIOUS RESPONSE:
{best_response}

TOPICS THE PREVIOUS RESPONSE APPEARS TO HAVE OMITTED:
{chr(10).join("- " + topic for topic in missing_topics)}

TASK:
Write a corrected, complete answer to the original question in {language}.
Cover every requested topic, including the omitted topics listed above.
Preserve relevant useful content from the previous response.
Explain statutory conditions, exceptions and uncertainty accurately.
Do not invent facts, legal provisions, deadlines or legal conclusions.
Distinguish established facts from possible legal arguments.
If a legal point cannot be determined from the supplied facts, say so.
Do not claim that merely mentioning a topic proves legal correctness.
Return the complete corrected answer, not just a list of additions.
"""

                retry_candidates = []

                gemini_retry = self._call_gemini_raw(
                    retry_prompt,
                    max_tokens=4000,
                    temperature=0.1
                )
                if gemini_retry:
                    retry_candidates.append(("Gemini retry", gemini_retry))

                for provider_name, candidate in retry_candidates:
                    candidate_missing = self._missing_requested_legal_topics(
                        query, candidate
                    )
                    if len(candidate_missing) < len(missing_topics):
                        best_response = candidate
                        missing_topics = candidate_missing

                    if not missing_topics:
                        logger.info(
                            "%s produced an answer covering all detected topics.",
                            provider_name
                        )
                        break

                if missing_topics:
                    openrouter_retry = self._call_openrouter_raw(
                        retry_prompt,
                        max_tokens=4000
                    )

                    if openrouter_retry:
                        candidate_missing = self._missing_requested_legal_topics(
                            query, openrouter_retry
                        )
                        if len(candidate_missing) < len(missing_topics):
                            best_response = openrouter_retry
                            missing_topics = candidate_missing

                if missing_topics:
                    logger.warning(
                        "Chat answer still has %d topic-coverage warning(s).",
                        len(missing_topics)
                    )
                    warning = (
                        "\\n\\nCompleteness notice: This answer may not fully "
                        "address these requested topics: "
                        + "; ".join(missing_topics)
                        + ". This automated check measures topic coverage only, "
                        "not legal accuracy. Please seek verification from a "
                        "qualified Indian advocate."
                    )
                    best_response = best_response.rstrip() + warning

                response = best_response

        if response:
            return clean_legal_text(response)

        logger.error("All configured AI providers failed to generate a response.")
        return None
'''

if source.count(old) != 1:
    raise SystemExit(
        "STOP: Expected chat response block was not found exactly once. "
        "No changes made."
    )

backup = path.with_name("gemini_client.py.pre_chat_completeness_retry_backup")
if backup.exists():
    raise SystemExit(f"STOP: Backup already exists: {backup.name}")

backup.write_text(source, encoding="utf-8")
path.write_text(source.replace(old, new, 1), encoding="utf-8")

print("SUCCESS: Chat completeness retry integrated.")
print(f"Backup created: {backup.name}")
