"""
Google Gemini AI Client for Law Mithra.
Uses GEMINI_API_KEY securely from environment variables.
"""

import os
import re
import json
import logging
import urllib.request
import urllib.error
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

GEMINI_MODELS = [
    'models/gemini-3-flash-preview',
    'models/gemini-3.1-flash-lite',
    'models/gemini-flash-lite-latest',
]


def clean_legal_text(text: str) -> str:
    """
    Cleans up any unnecessary markdown asterisks, hashes, and formatting characters
    to provide clean, readable text.
    """
    if not text:
        return ""
    # Remove markdown header hashes: ### Heading -> Heading
    text = re.sub(r'#{1,6}\s*', '', text)
    # Remove double asterisks: **text** -> text
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    # Remove single asterisks: *text* -> text
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    # Clean bullet points: * Item or - Item -> • Item
    text = re.sub(r'^\s*[\*\-]\s+', '• ', text, flags=re.MULTILINE)
    # Clean brackets around sections: [Section 6] -> Section 6
    text = re.sub(r'\[([^\]]+)\]', r'\1', text)
    # Clean extra empty lines
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


class GeminiClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        self.groq_key = os.getenv('GROQ_API_KEY')
        self.openrouter_key = os.getenv('OPENROUTER_API_KEY')
        self.groq_model = 'openai/gpt-oss-120b'
        self.timeout = 60

    def generate_legal_response(
        self,
        query: str,
        language: str = 'en',
        statutory_context: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[str]:
        """
        Generates fact-aware Indian legal explanations.
        Uses concise responses for simple questions and detailed analysis
        when the user's question requires it.
        """
        query = (query or "").strip()
        if not query:
            return "Please describe your legal question so I can assist you."

        is_greeting = bool(re.fullmatch(
            r"(hi|hello|hey|namaste|namaskara|namaskar|good\s+(morning|afternoon|evening)|pranam|pranaam)[\s!.,?]*",
            query,
            re.IGNORECASE
        ))

        if is_greeting:
            prompt = f"""
You are Law Mithra, a friendly and professional AI assistant specializing
in Indian legal information.

The user greeted you with: {query}
Respond in the user's preferred language: {language}

Greet the user naturally, introduce yourself as Law Mithra, and briefly
mention that you can help explain Indian legal issues and procedures.
Ask how you can help.

Keep the response short, warm and natural.
Do not provide unsolicited legal analysis.
Use plain text without Markdown formatting.
"""
        else:
            context_str = "No verified statutory context was supplied.\n"

            if statutory_context:
                context_str = (
                    "Statutory context supplied by the application. "
                    "Use it only when relevant to the user's facts:\n"
                    + json.dumps(statutory_context, ensure_ascii=False, indent=2)
                )

            prompt = f"""
You are Law Mithra, an AI legal information assistant specializing in
Indian law. Help users understand their legal situation clearly,
comprehensively and responsibly.

USER QUESTION:
{query}

PREFERRED LANGUAGE:
{language}

APPLICATION-SUPPLIED STATUTORY CONTEXT:
{context_str}

REASONING AND RESPONSE RULES:

1. Understand the actual question before answering. Do not force simple
questions into an irrelevant formal case template.

2. MULTIPLE QUESTIONS & SUB-ISSUES:
If the user asks multiple legal questions or raises distinct sub-issues
(e.g., whether to file a civil suit vs. a police complaint, injunction options,
remedies for damages, or rights of the opposing party):
- Systematically address EACH question and legal issue distinctly.
- Do not skip secondary questions or collapse separate issues into a vague summary.
- Address each question under clear numbered points or distinct thematic headings.

3. FACT CATEGORIZATION & EVIDENTIARY DISTINCTIONS:
In your analysis, clearly distinguish:
- Established Facts: Facts explicitly provided by the user.
- Allegations & Claims: Unverified assertions or claims made by either party.
- Working Assumptions: Practical assumptions made to explain legal options.
- Missing Evidence: Crucial documents, title deeds, maps, dates, or physical proof needed to substantiate rights or liability.

4. ACCURATE STATUTORY PROVISIONS & CONDITIONS:
- Explain the essential statutory ingredients and conditions for any mentioned provision.
- Clarify whether statutory conditions are cumulative (all must be met) or alternative.
- Distinguish substantive rights from procedural remedies.
- Never invent legal sections, Act titles, court rulings, or statutory limitation periods.
- Mention a section only with a sound legal basis; if uncertain, explicitly recommend verification against official legislation and bare Acts.

5. STATUTORY EXCEPTIONS & PROCEDURAL LIMITATIONS:
- Explicitly explain relevant statutory exceptions (such as the good-faith private-way exception in BNS Section 126).
- Outline jurisdictional preconditions, statutory time windows, and procedural limits (such as the 3-month continuous or last-season requirement in BNSS Section 166, the 6-month limit for dispossession under SRA Section 6, or the 2-year pre-suit requirement under Easements Act Section 15).

6. BALANCED VIEW (CLAIMANT & OPPOSING PARTY):
- Present both perspectives:
  * Claimant's potential arguments, remedies, and burdens of proof.
  * Opposing party's rights, defences, and counter-arguments (e.g., neighbor's property rights, assertion of title/boundaries, lack of prescriptive easement, permissive use / license, good-faith claim).

7. FOCUSED CLARIFICATION QUESTIONS:
- When essential facts are missing (e.g., duration of pathway use, presence of partition deeds, classification of land, evidence of permission, or nature of obstruction), provide 2 to 4 focused clarification questions to guide the user.

8. PROVISION-SPECIFIC SAFEGUARDS:

- BHARATIYA NYAYA SANHITA, 2023 — SECTION 126 (Wrongful Restraint):
  * Core ingredients: (i) voluntary obstruction; (ii) person obstructed has a lawful right to proceed in that direction.
  * Statutory Exception: Obstruction of a private way over land or water is expressly NOT an offence if the person in good faith believes they have a lawful right to obstruct it.
  * Opposing perspective: Neighbour may assert good-faith belief in title, property boundaries, or lawful right to close a private passage.
  * Limitation: A blocked pathway or property boundary dispute is not automatic criminal trespass or wrongful restraint; police cannot determine disputed private easement rights.

- BHARATIYA NAGARIK SURAKSHA SANHITA, 2023 — SECTION 166 (Dispute concerning right of use of land or water):
  * Jurisdiction: Executive Magistrate (SDM/Tahsildar) proceeding when a dispute regarding an alleged right of user of land or water (easement or otherwise) is likely to cause a breach of the peace.
  * Threshold Statutory Conditions:
    - If the right is exercisable at all times of the year: Must have been exercised within 3 months next before receipt of the police report or information.
    - If seasonal or occasional: Must have been exercised during the last of such seasons or occasions next before receipt of the report or information. Do not oversimplify the three-month provision as applying to all disputes without addressing seasonal/occasional use.
  * Scope of Order: Magistrate may prohibit interference or order removal of obstruction pending civil adjudication. It is an interim preventive order, NOT a final determination of ownership or title.
  * Distinction: Distinguish Section 166 (right of use/easement) from Section 164 (disputes concerning actual possession).

- INDIAN EASEMENTS ACT, 1882 — SECTION 15 (Prescription):
  * Statutory Period: Distinguish 20 years for private property from 30 years where the servient property belongs to Government.
  * Mode of Enjoyment: Must be peaceable, open, as an easement, as of right (not by permissive licence or agreement), and without interruption.
  * Timing Requirement: By statutory mandate, each 20-year or 30-year period must be taken to be a period ending within 2 years next before the institution of the suit in which the claim to which such period relates is contested.
  * Interruption vs Temporary Non-Use (Explanation II): Under Explanation II, an interruption requires actual cessation of enjoyment caused by an obstruction by the act of some person, and submission to or acquiescence in that obstruction for 1 year after the claimant has notice of the obstruction and of the person making it. Mere temporary non-use or voluntary cessation of user by the claimant without obstruction and one-year acquiescence does NOT constitute statutory interruption.

- INDIAN EASEMENTS ACT, 1882 — SECTION 13 (Necessity & Quasi-Easements):
  * Severance Requirement: Relates specifically to severance of tenements through transfer, bequest, or partition of joint immovable property; requires examination of the relevant property title history.
  * Easement of Necessity: Arises when without the easement the property cannot be used at all. Do NOT state that every alternative route automatically defeats an easement of necessity: an illusory, impassable, perilous, or legally impermissible alternative route does not defeat necessity; examine the factual and legal viability and usability of any alleged alternative route.
  * Quasi-Easements: Distinguish strict necessity from quasi-easement, which requires apparent and continuous use that was necessary for enjoying the property as it was enjoyed when the transfer or partition took effect.
  * Mere convenience or neighbouring ownership alone does not establish Section 13 rights.

- SPECIFIC RELIEF ACT, 1963 — SECTIONS 38 & 39:
  * Section 38: Perpetual injunction to prevent invasion of rights/obligations.
  * Section 39: Discretionary mandatory injunction to compel performance of acts. Not an automatic right to demolish structures.

- CPC ORDER 39 RULES 1 & 2 (Temporary Injunctions):
  * Discretionary equitable interim relief, NOT an automatic stay or final mandatory decree.
  * Concurrently requires establishing all three foundational legal criteria:
    1. Prima facie case: An arguable, triable legal case establishing a clear probability of relief.
    2. Balance of convenience: Greater hardship will be caused to applicant by withholding interim relief than to respondent by granting it.
    3. Irreparable injury: Substantial injury that cannot be adequately compensated in monetary damages.

- STOLEN / LOST MOBILE PHONES, BNSS SECTION 173 & CEIR PORTAL:
  * BNSS Section 173(1) (Zero FIR): Information regarding a cognizable offence can be given to an officer in charge of a police station irrespective of the area/territorial jurisdiction where the offence was committed. The receiving police station must register the information (Zero FIR) and transfer it to the police station having territorial jurisdiction.
  * BNSS Section 173(3) (Preliminary Inquiry): Where an offence is punishable with imprisonment between 3 and 7 years, an officer in charge may, with prior permission of an officer not below the rank of Deputy Superintendent of Police (DSP), conduct a preliminary inquiry within 14 days to ascertain whether a prima facie case exists, OR may proceed directly to register an FIR without preliminary inquiry. Crucially, do NOT imply that every complaint must undergo a preliminary inquiry; it is discretionary and direct FIR registration remains standard procedure.
  * CEIR (Central Equipment Identity Register - ceir.gov.in) Requirements:
    - Mandatory / Essential requirements: Police report / FIR copy (or digital acknowledgment / lost property report depending on state), re-issued SIM card (essential to receive the OTP verification on the primary linked number), valid identity proof (Aadhaar, Voter ID, PAN, Driving Licence), and device IMEI number(s).
    - Purchase invoice / receipt: Explicitly clarify that purchase invoice / bill is OPTIONAL / supporting where available, and its absence does not bar submitting a blocking request.
  * CEIR Blocking Scope:
    - Clarify that CEIR blocks the device's IMEI from Indian mobile / cellular / telecom networks (preventing any Indian SIM card from accessing telecom networks, and flagging blacklisted handsets).
    - Do NOT claim or imply that the entire device becomes physically unusable or inoperable (e.g. offline functionality, Wi-Fi, or local device features are not permanently destroyed or shut down by network IMEI blocking).
  * e-FIR Availability & Procedure:
    - State clearly that e-FIR availability, portals, and procedures vary by state (e.g., dedicated citizen police apps or portals such as Karnataka KSP, Delhi Police e-FIR, Tamil Nadu CCTNS for theft vs lost property reporting).
  * Fact vs Allegation Safeguards:
    - Distinguish allegations of theft (BNS Section 303(2)) or snatching (BNS Section 304) from lost or misplaced property reports until investigated; avoid stating unverified allegations as established facts.

9. RESPONSE LANGUAGE & READABILITY:
- Write in the user's preferred language ({language}) across the 10 supported Indian languages (English, Kannada, Hindi, Tamil, Telugu, Malayalam, Marathi, Bengali, Gujarati, Punjabi).
- Preserve readable English and Indian-language characters without encoding errors or markdown clutter.
- Keep statutory citations recognizable (e.g. citing the Act and Section in both native script and standard legal notation).
- Start with a direct, practical answer.
- Do not use Markdown asterisks or bracketed section references.
"""

        response = self._call_gemini_raw(
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

TOPICS THE PREVIOUS RESPONSE APPEARS TO HAVE OMITTED OR INCOMPLETELY COVERED:
{chr(10).join("- " + topic for topic in missing_topics)}

TASK:
Write a corrected, complete answer to the original question in {language}.
Systematically address every user question, including the omitted topics listed above.
Preserve relevant useful content from the previous response.

LEGAL REQUIREMENTS TO ENSURE COMPLETENESS:
1. Address all questions asked by the user distinctly and completely.
2. Distinguish established facts, allegations, assumptions, and missing evidence.
3. Present both claimant arguments and opposing-party defences/counter-arguments.
4. For BNS Section 126, explain voluntary obstruction, lawful right to proceed, and the statutory good-faith private-way exception.
5. For BNSS Section 166, explain the Executive Magistrate breach-of-peace jurisdiction, the 3-month (continuous) and last-season/occasion timing conditions, and that it is an interim order subject to Civil Court adjudication.
6. Provide 2-4 focused clarification questions for any missing critical facts.
7. Never invent legal sections, case citations, or limitation deadlines.
8. For stolen/lost mobile phones, accurately cover BNSS 173(1) (Zero FIR irrespective of jurisdiction), BNSS 173(3) (preliminary inquiry is discretionary and not mandatory for all complaints), CEIR requirements (re-issued SIM for OTP, police report, ID, IMEI; invoice is optional), CEIR blocking scope (cellular/telecom networks only; do not claim whole device becomes unusable), and e-FIR state variations.
9. For Indian Easements Act Section 13, explain severance through transfer, bequest or partition and property history, note that not every alternative route automatically defeats an easement of necessity (illusory, perilous or impassable routes do not defeat necessity), and distinguish necessity from quasi-easement.
10. For Indian Easements Act Section 15, explain the 20/30-year prescriptive period ending within two years next before suit, and distinguish statutory interruption (Explanation II: 1 year submission/acquiescence to obstruction after notice) from mere temporary non-use.
11. For CPC Order 39 Rules 1 & 2, explain that temporary injunctions are discretionary equitable relief requiring prima facie case, balance of convenience, and irreparable injury.
12. Return the complete corrected answer in readable, natural {language} without Markdown asterisks or bracketed citations.
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
                        "\n\nCompleteness notice: This answer may not fully "
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

    @staticmethod
    def _missing_requested_legal_topics(query: str, response: str) -> List[str]:
        """Check whether explicitly requested Indian-law topics appear in the answer.

        This is a heuristic topic-coverage check to detect omitted statutory sub-issues.
        It does not treat keyword coverage as proof of legal accuracy.
        """
        q = (query or "").casefold()
        a = re.sub(r"\s+", " ", (response or "").casefold())
        a = a.replace("–", "-").replace("—", "-").replace("‑", "-")
        missing = []

        def requested(pattern: str) -> bool:
            return re.search(pattern, q, flags=re.IGNORECASE | re.DOTALL) is not None

        def has_any(*terms: str) -> bool:
            return any(term.casefold() in a for term in terms)

        # Indian Easements Act, Section 13
        asks_s13 = requested(
            r"(?:easements?\s+act.{0,80}section\s*13|"
            r"section\s*13.{0,50}easements?\s+act|"
            r"\bsection\s*13\b.{0,40}\b(?:necessity|quasi[- ]easement)\b)"
        )
        if asks_s13:
            if not has_any(
                "necessity", "necessary for enjoying", "strictly necessary", "absolute necessity",
                "ಅಗತ್ಯ", "ಅನಿವಾರ್ಯ", "आवश्यकता", "जरूरत", "अवश्यम्भावी"
            ):
                missing.append("Easements Act Section 13: easement of necessity")
            if not has_any(
                "quasi-easement", "quasi easement", "quasi easements", "quasi-easements",
                "apparent and continuous", "continuous and apparent",
                "ಅರೆ-ಸುಖಭೋಗ", "ಉಪ-ಸುಖಭೋಗ", "अर्ध-सुखाधिकार", "समान-सुखाधिकार"
            ):
                missing.append("Easements Act Section 13: quasi-easement")
            if not has_any(
                "transfer", "partition", "common ownership", "severance", "bequest",
                "joint property", "joint ownership", "prior common owner", "single owner",
                "property history", "title history",
                "ವರ್ಗಾವಣೆ", "ವಿಭಜನೆ", "ಹಂಚಿಕೆ", "ಅವಿಭಕ್ತ", "हस्तांतरण", "बंटवारा", "विभाजन", "संयुक्त स्वामित्व"
            ):
                missing.append("Easements Act Section 13: transfer, partition or common ownership")

        # Indian Easements Act, Section 15
        asks_s15 = requested(
            r"(?:easements?\s+act.{0,80}section\s*15|"
            r"section\s*15.{0,50}easements?\s+act|"
            r"\bsection\s*15\b.{0,40}\b(?:prescription|prescriptive|20\s*years?)\b)"
        )
        if asks_s15:
            if not has_any(
                "20 years", "20-year", "twenty years", "twenty-year", "20 yrs", "two decades",
                "20 yr", "20year", "೨೦ ವರ್ಷ", "20 ವರ್ಷ", "20 साल", "20 वर्ष", "बीस वर्ष"
            ):
                missing.append("Easements Act Section 15: 20-year period")
            if not has_any(
                "30 years", "30-year", "thirty years", "thirty-year", "30 yrs", "three decades",
                "30 yr", "30year", "government property (30", "government land (30", "state land (30",
                "೩೦ ವರ್ಷ", "30 ವರ್ಷ", "30 साल", "30 वर्ष", "तीस वर्ष"
            ):
                missing.append("Easements Act Section 15: 30-year period")
            if not has_any(
                "interruption", "interrupted", "interrupted use", "uninterrupted",
                "cessation of enjoyment", "obstruction for one year", "acquiescence",
                "submission to or acquiescence", "explanation ii", "temporary non-use",
                "ತಡೆ", "ಅಡಚಣೆ", "ತಡೆಯಿಲ್ಲದ", "ರುಕಾವಟ", "व्यवधान", "अबाध"
            ):
                missing.append("Easements Act Section 15: statutory interruption")
            if not has_any(
                "two years", "two-year", "2 years", "2-year", "2 yrs",
                "ending within two years", "ending within 2 years", "within two years prior to suit",
                "within 2 years prior to suit", "immediately before institution of the suit",
                "next before the institution", "before the suit",
                "ದಾವೆ ಹೂಡುವ ಮೊದಲು 2 ವರ್ಷ", "मुकदमा दायर करने से पूर्व 2 वर्ष"
            ):
                missing.append("Easements Act Section 15: two-year timing requirement")

        # Bharatiya Nyaya Sanhita, Section 126
        asks_bns126 = requested(
            r"(?:\bbns\b.{0,60}(?:section\s*126|\b126\b)|"
            r"(?:section\s*126|\b126\b).{0,60}\bbns\b|"
            r"bharatiya\s+nyaya\s+sanhita.{0,60}(?:section\s*126|\b126\b)|"
            r"\bwrongful\s+restraint\b)"
        )
        if asks_bns126:
            if not has_any(
                "voluntary obstruction", "voluntarily obstruct", "voluntarily obstructs",
                "voluntarily obstructed", "voluntary act of obstruction", "voluntary blocking",
                "intentional obstruction", "intentionally obstruct", "willful obstruction",
                "deliberately obstruct", "wrongfully obstruct", "wrongfully restrained",
                "ಸ್ವಯಂಪ್ರೇರಿತ ಅಡಚಣೆ", "ಸ್ವೇಚ್ಛೆಯಿಂದ ತಡೆಯುವುದು", "ಅಕ್ರಮ ತಡೆ",
                "स्वेच्छा से अवरोध", "जानबूझकर रोकना", "सदोष अवरोध"
            ):
                missing.append("BNS Section 126: voluntary obstruction")
            if not has_any(
                "right to proceed", "right to pass", "right of way", "legal right to proceed",
                "right of passage", "entitled to proceed", "lawful right to use", "right to move",
                "right to travel", "lawful right to proceed", "entitled to pass",
                "ಚಲಿಸುವ ಹಕ್ಕು", "ಹೋಗುವ ಹಕ್ಕು", "ಹಾದಿಯ ಹಕ್ಕು", "ರಸ್ತೆಯ ಹಕ್ಕು",
                "आगे बढ़ने का अधिकार", "रास्ते का अधिकार", "जाने का अधिकार", "मार्ग का अधिकार"
            ):
                missing.append("BNS Section 126: person's right to proceed")

            # Check statutory private-way good-faith exception:
            has_private_way = has_any(
                "private way", "private pathway", "private road", "private passage",
                "private land", "private property", "land or water", "land or waterway",
                "over land or water", "ಖಾಸಗಿ ದಾರಿ", "ಖಾಸಗಿ ರಸ್ತೆ", "ಖಾಸಗಿ ಜಮೀನು",
                "निजी मार्ग", "निजी रास्ता", "निजी भूमि"
            )
            has_good_faith = has_any(
                "good faith", "good-faith", "bona fide", "honest belief", "believes in good faith",
                "acted in good faith", "acting in good faith", "honest and reasonable belief",
                "ಸದ್ಭಾವನೆ", "ಸದ್ಭಾವನೆಯಿಂದ", "ಪ್ರಾಮಾಣಿಕ ನಂಬಿಕೆ", "सद्भावपूर्वक", "सद्भाव", "सद्भावपूर्ण"
            )
            has_right_to_obstruct = has_any(
                "lawful right to obstruct", "lawful right to do so", "right to obstruct",
                "lawfully entitled to obstruct", "legal right to obstruct", "entitled to obstruct",
                "lawful entitlement", "right to close", "right to block", "lawful authority to obstruct",
                "lawful right", "legal right to close",
                "ಕಾನೂನುಬದ್ಧ ಹಕ್ಕು", "ತಡೆಯುವ ಹಕ್ಕು", "ಕಾನೂನು ಪ್ರಕಾರ ತಡೆಯುವ",
                "कानूनी अधिकार", "रोकने का अधिकार", "अवरोध का वैध अधिकार"
            )

            if not (has_private_way and has_good_faith and has_right_to_obstruct):
                missing.append("BNS Section 126: statutory good-faith private-way exception")

        # Bharatiya Nagarik Suraksha Sanhita, Section 166
        asks_bnss166 = requested(
            r"(?:\bbnss\b.{0,60}(?:section\s*166|\b166\b)|"
            r"(?:section\s*166|\b166\b).{0,60}\bbns\b|"
            r"(?:section\s*166|\b166\b).{0,60}\bbnss\b|"
            r"bharatiya\s+nagarik\s+suraksha\s+sanhita.{0,60}(?:section\s*166|\b166\b)|"
            r"(?:section\s*147|\b147\b).{0,60}\bcrpc\b)"
        )
        if asks_bnss166:
            if not has_any(
                "breach of peace", "breach-of-peace", "breach of the peace", "disturbance of peace",
                "threat to peace", "public peace", "executive magistrate", "magisterial inquiry",
                "sub-divisional magistrate", "sdm", "tahsildar",
                "ಶಾಂತಿಭಂಗ", "ಶಾಂತಿ ಭಂಗ", "ಕಾರ್ಯನಿರ್ವಾಹಕ ಮ್ಯಾಜಿಸ್ಟ್ರೇಟ್", "ಉಪವಿಭಾಗಾಧಿಕಾರಿ",
                "शांतिभंग", "शांति भंग", "कार्यपालक मजिस्ट्रेट", "एसडीएम"
            ):
                missing.append("BNSS Section 166: likelihood of breach of peace / Executive Magistrate")
            if not has_any(
                "three months", "three-month", "3 months", "3-month", "90 days", "ninety days",
                "within three months", "within 3 months", "prior 3 months", "preceding 3 months",
                "೩ ತಿಂಗಳು", "3 ತಿಂಗಳು", "ಮೂರು ತಿಂಗಳು", "तीन महीने", "3 महीने", "3 माह"
            ):
                missing.append("BNSS Section 166: three-month condition for year-round right")
            if not has_any(
                "seasonal", "last season", "last occasion", "season or occasion",
                "particular season", "occasional use", "occasionally used", "seasonal right",
                "particular occasion", "during the last season",
                "ಹಂಗಾಮು", "ಕೊನೆಯ ಸಂದರ್ಭ", "ನಿರ್ದಿಷ್ಟ ಸಂದರ್ಭ", "ಹಂಗಾಮಿ",
                "मौसम", "अंतिम अवसर", "मौसमी", "विशिष्ट अवसर"
            ):
                missing.append("BNSS Section 166: seasonal or occasional-use condition")

        # Specific Relief Act, Sections 38 and 39
        asks_sra = requested(
            r"(?:specific relief act.{0,100}(?:section\s*38|section\s*39|sections?\s*38.{0,30}39)|"
            r"(?:section\s*38|section\s*39).{0,60}specific relief act|"
            r"\bperpetual\s+injunction\b|\bmandatory\s+injunction\b)"
        )
        if asks_sra:
            if not has_any(
                "perpetual injunction", "permanent injunction", "perpetual or permanent",
                "restraining order", "ಶಾಶ್ವತ ತಡೆಯಾಜ್ಞೆ", "ಸ್ಥಿರ ನಿಷೇಧಾಜ್ಞೆ", "स्थायी निषेधाज्ञा", "शाश्वत व्यादेश"
            ):
                missing.append("Specific Relief Act Section 38: perpetual or permanent injunction")
            if not has_any(
                "mandatory injunction", "order to remove", "direction to restore", "compel performance",
                "demolition order", "ಆಜ್ಞಾಪಕ ತಡೆಯಾಜ್ಞೆ", "ಕಡ್ಡಾಯ ತಡೆಯಾಜ್ಞೆ", "आज्ञापक व्यादेश", "अनिवार्य निषेधाज्ञा"
            ):
                missing.append("Specific Relief Act Section 39: mandatory injunction")

        # Code of Civil Procedure, Order 39 Rules 1 and 2
        asks_order39 = requested(
            r"(?:order\s*39|order\s*xxxix).{0,60}(?:rule\s*1|rule\s*2|rules?\s*1\s*(?:and|&)\s*2)?|"
            r"\btemporary\s+injunction\b"
        )
        if asks_order39:
            if not has_any(
                "prima facie", "arguable case", "triable issue",
                "ಪ್ರಥಮ ದೃಷ್ಟಿ", "ಪ್ರೈಮಾ ಫೇಸಿ", "प्रथम दृष्टया", "प्रथम दृष्ट्या"
            ):
                missing.append("CPC Order 39: prima facie case")
            if not has_any(
                "balance of convenience", "convenience lies in favour", "convenience",
                "ಅನುಕೂಲತೆಯ ಸಮತೋಲನ", "ಸುಲಭತೆಯ ಸಮತೋಲನ", "ಅನುಕೂಲತೆ", "सुविधा का संतुलन", "सुविधा संतुलन"
            ):
                missing.append("CPC Order 39: balance of convenience")
            if not has_any(
                "irreparable injury", "irreparable harm", "irreparable loss", "cannot be compensated in damages",
                "irreparable damage", "ಪರಿಹರಿಸಲಾಗದ ನಷ್ಟ", "ಅಪಾರ ಹಾನಿ", "ತುಂಬಲಾರದ ನಷ್ಟ", "अपूरणीय क्षति", "अपूरणीय हानि"
            ):
                missing.append("CPC Order 39: irreparable injury or harm")

        # Stolen / Lost Mobile Phones, BNSS Section 173, and CEIR Portal
        asks_stolen_phone = requested(
            r"(?:stolen|theft|snatched|robbed|lost).{0,40}(?:mobile|phone|cell|smartphone|handset|device)|"
            r"(?:mobile|phone|cell|smartphone|handset|device).{0,40}(?:stolen|theft|snatched|robbed|lost)|"
            r"\bceir\b"
        )
        if asks_stolen_phone:
            # 1. BNSS Section 173(1) - Zero FIR irrespective of territorial jurisdiction
            if not has_any(
                "173(1)", "173 (1)", "zero fir", "territorial jurisdiction", "irrespective of jurisdiction",
                "irrespective of the area", "irrespective of where", "jurisdiction",
                "ಯಾವುದೇ ಠಾಣೆ", "ಶೂನ್ಯ ಎಫ್‌ಐಆರ್", "ಪ್ರಾಂತೀಯ ವ್ಯಾಪ್ತಿ", "ಕ್ಷೇತ್ರಾಧಿಕಾರ",
                "शून्य प्राथमिकी", "शून्य एफआईआर", "क्षेत्राधिकार", "क्षेत्राधिकार के बिना"
            ):
                missing.append("BNSS Section 173(1): Zero FIR irrespective of territorial jurisdiction")

            # 2. BNSS Section 173(3) - preliminary inquiry is discretionary / enabling, not mandatory for all complaints
            if not has_any(
                "173(3)", "173 (3)", "preliminary inquiry", "preliminary enquiry", "not mandatory",
                "discretionary", "dsp", "direct fir", "enabling provision", "not every complaint",
                "ಪೂರ್ವಭಾವಿ ವಿಚಾರಣೆ", "ಕಡ್ಡಾಯವಲ್ಲ", "ಡಿಎಸ್‌ಪಿ", "ಪ್ರಾರಂಭಿಕ ತನಿಖೆ",
                "प्रारंभिक जांच", "अनिवार्य नहीं", "विवेकाधीन", "डीएसपी"
            ):
                missing.append("BNSS Section 173(3): preliminary inquiry is discretionary and not mandatory for all complaints")

            # 3. CEIR requirements - purchase invoice is optional, re-issued SIM for OTP
            if not has_any(
                "invoice", "bill", "receipt", "optional", "not mandatory", "not compulsory",
                "ಬಿಲ್", "ರಶೀದಿ", "ಖರೀದಿ ರಶೀದಿ", "ಐಚ್ಛಿಕ", "ಕಡ್ಡಾಯವಲ್ಲ",
                "इनवॉइस", "रसीद", "बिल", "वैकल्पिक", "अनिवार्य नहीं"
            ):
                missing.append("CEIR requirements: purchase invoice is optional / not mandatory")

            # 4. CEIR blocking scope - blocks IMEI on Indian cellular / mobile networks, not entire device unusable
            if not has_any(
                "network", "cellular", "telecom", "telecom networks", "mobile networks", "indian networks",
                "sim", "unusable", "entire device",
                "ನೆಟ್‌ವರ್ಕ್", "ದೂರಸಂಪರ್ಕ", "ಮೊಬೈಲ್ ನೆಟ್‌ವರ್ಕ್", "ನೆಟ್‌ವರ್ಕ್‌ನಲ್ಲಿ ನಿರ್ಬಂಧ",
                "नेटवर्क", "दूरसंचार", "सेलुलर नेटवर्क"
            ):
                missing.append("CEIR blocking scope: blocks IMEI on cellular networks without claiming entire device becomes unusable")

            # 5. e-FIR availability and procedure vary by state
            if not has_any(
                "vary", "varies", "state", "states", "portal", "ksp", "cctns", "app", "differ",
                "ರಾಜ್ಯ", "ಬದಲಾಗುತ್ತದೆ", "ವ್ಯತ್ಯಾಸ", "ಪೋರ್ಟಲ್",
                "राज्य", "भिन्न", "अलग", "पोर्टल"
            ):
                missing.append("e-FIR availability and procedure vary by state")

        return missing

    def analyze_legal_case(self, case_text: str, language: str = 'en') -> Dict[str, Any]:
        """
        Executes comprehensive AI Legal Case Analysis adhering to the Law Mithra API Instruction Document.
        Returns a structured JSON matching all 10 core instructions and 7 mandatory sections.
        """
        prompt = (
            f"You are an AI Legal Research and Case Analysis Assistant specializing exclusively in Indian law.\n"
            f"Default jurisdiction: India. Apply current applicable legislation (including Bharatiya Nyaya Sanhita 2023, Bharatiya Nagarik Suraksha Sanhita 2023, Bharatiya Sakshya Adhiniyam 2023, Negotiable Instruments Act 1881, Indian Contract Act 1872, Specific Relief Act 1963, Code of Civil Procedure 1908, Indian Easements Act 1882, and Limitation Act 1963).\n\n"
            f"Analyze the following legal case query / facts:\n\"\"\"{case_text}\"\"\"\n\n"
            f"INDIAN LEGAL REASONING SAFEGUARDS:\n"
            f"- Distinguish established facts, allegations, assumptions, and missing information.\n"
            f"- Never treat unverified allegations by either party as proven facts.\n"
            f"- Apply legal provisions only when their essential statutory ingredients are supported by the facts.\n"
            f"- Use 'Confirmed' ONLY when all essential statutory ingredients are factually established. Use 'Potentially applicable' when essential facts remain to be verified.\n"
            f"- Distinguish civil remedies from criminal offences, and substantive rights from procedural remedies.\n"
            f"- Present balanced arguments: detail the claimant/plaintiff/prosecution's case alongside the opposing party/accused/defendant's possible defences and statutory objections.\n"
            f"- Identify critical missing evidence and factual gaps in missing_information.\n"
            f"- Never invent or hallucinate statutory provisions, sections, Act titles, case citations, court decisions, or limitation deadlines.\n"
            f"- If a precedent is not definitively verified with legal certainty, return an empty list: [] for judicial_precedents rather than inventing a citation.\n"
            f"- Clearly state that AI analysis is informational and requires verification by an enrolled Indian advocate.\n\n"
            f"DOMAIN-SPECIFIC LEGAL PRECISION RULES:\n\n"
            f"1. CIVIL PROPERTY & EASEMENTS DISPUTES:\n"
            f"- For Easements Act Section 15, distinguish 20 years for private land from 30 years where the servient property belongs to Government.\n"
            f"- Verify that the prescriptive period was enjoyed peaceably, openly, as an easement, as of right, without interruption, and ends within 2 years immediately before institution of the suit.\n"
            f"- Under Section 15 Explanation II, distinguish statutory interruption (actual cessation due to obstruction with 1 year submission/acquiescence after notice) from mere temporary non-use or voluntary cessation.\n"
            f"- Never infer 20 years from vague phrases such as 'several years' or 'a long time'.\n"
            f"- For Easements Act Section 13, examine severance through transfer, bequest, or partition, and examine property title history. Distinguish strict easement of necessity from quasi-easement. Do not state that every alternative route automatically defeats easement of necessity (illusory, impassable, perilous, or legally impermissible access does not automatically defeat necessity).\n"
            f"- For Specific Relief Act Section 6, apply only where there was actual dispossession from immovable property without consent and otherwise than in due course of law; enforce the strict 6-month limitation.\n"
            f"- Distinguish perpetual injunction under SRA Section 38 from mandatory injunction under SRA Section 39 (discretionary judicial relief; not an automatic right to demolish a wall).\n"
            f"- For CPC Order 39 Rules 1 & 2, examine prima facie case, balance of convenience, and irreparable injury. Temporary injunctions are discretionary equitable interim relief, not automatic stays or final decrees.\n\n"
            f"2. CHEQUE BOUNCE CASES (NEGOTIABLE INSTRUMENTS ACT, 1881):\n"
            f"- Section 138 statutory ingredients: (i) cheque drawn on bank account for discharge of legally enforceable debt/liability; (ii) presented to bank within validity (3 months); (iii) returned unpaid by bank with memo (insufficiency of funds, exceeds arrangement, etc.); (iv) payee issues statutory demand notice in writing within 30 days of receiving return memo; (v) drawer fails to make payment within 15 days of notice receipt. Cause of action arises on the 16th day.\n"
            f"- Limitation: Complaint must be filed under Section 142 before Judicial Magistrate First Class / Metropolitan Magistrate within 30 days after the 15-day notice period expires.\n"
            f"- Section 141 applies for vicarious liability of directors/partners in charge of and responsible to the company/firm.\n"
            f"- Address statutory presumptions under Section 118 (consideration) and Section 139 (debt), and the accused's defence standard of rebuttal on preponderance of probabilities (e.g., security cheque, no existing debt, goods returned/defective).\n"
            f"- Explain interim compensation under Section 143A (up to 20% of cheque amount).\n\n"
            f"3. CRIMINAL COMPLAINTS & OFFENCES (BNS & BNSS, 2023):\n"
            f"- Distinguish cognizable from non-cognizable offences.\n"
            f"- For stolen or lost mobile phones:\n"
            f"  * Apply BNSS Section 173(1): Zero FIR must be registered irrespective of territorial jurisdiction and transferred to the jurisdictional station.\n"
            f"  * Apply BNSS Section 173(3): Preliminary inquiry is an enabling discretion for offences punishable between 3 and 7 years with DSP prior permission; direct FIR can be registered without inquiry, and preliminary inquiry is NOT mandatory for every complaint.\n"
            f"  * CEIR Portal (ceir.gov.in): Blocks device IMEI across Indian cellular/telecom networks (does NOT render the entire device unusable offline or disable local functions). Requirements: police report, re-issued SIM for verification OTP, identity proof, IMEI; purchase invoice/bill is strictly optional.\n"
            f"  * Explain that e-FIR availability and lost report procedures vary by state.\n"
            f"  * Distinguish theft/snatching allegations (BNS Sections 303(2), 304) from lost property reports without presenting allegations as proven facts.\n"
            f"- For BNS Section 126 (wrongful restraint), examine voluntary obstruction and right to proceed, and explicitly evaluate the statutory exception: obstruction of a private way over land or water is NOT an offence if done in good faith believing one has a lawful right to obstruct it.\n"
            f"- For BNSS Section 166 (right of use of land or water dispute before Executive Magistrate), verify likelihood of breach of peace and the mandatory exercise condition: exercised within 3 months prior to police report (for continuous year-round right) or during last season/occasion (for seasonal right). Note it is an interim preventive order subject to Civil Court determination.\n"
            f"- For criminal trespass (BNS Section 329), verify unlawful entry or remaining with intent to commit an offence or intimidate/insult/annoy. A bona fide property or boundary dispute is NOT criminal trespass.\n"
            f"- Outline procedural options: FIR under Section 173 BNSS, representation to SP under Section 173(4) BNSS, application to Magistrate under Section 175(3) BNSS, or private complaint under Section 223 BNSS.\n\n"
            f"4. CONTRACT & COMMERCIAL DISPUTES:\n"
            f"- Indian Contract Act, 1872: Verify valid contract, breach of obligation, Section 73 (compensation for actual loss naturally arising from breach), and Section 74 (liquidated damages vs penalty).\n"
            f"- Specific Relief Act, 1963: Specific performance under Section 10 subject to Section 16(c) (mandatory pleading and proof of continuous readiness and willingness); substituted performance under Section 20.\n"
            f"- Limitation Act, 1963: 3-year limitation period from date of breach for suit for damages or recovery of money.\n"
            f"- Commercial Courts Act, 2015: Mandatory pre-institution mediation under Section 12A if a commercial dispute of specified value.\n\n"
            f"5. INSUFFICIENT-INFORMATION & MINIMAL SCENARIOS:\n"
            f"- When facts are incomplete, ambiguous, or sparse:\n"
            f"  * Mark any tentatively identified provisions as 'Potentially applicable'.\n"
            f"  * Detail every missing fact, date, document, and jurisdictional detail in missing_information.\n"
            f"  * State neutral working assumptions without inventing facts, dates, or parties.\n"
            f"  * Under recommended_actions, emphasize fact organization, evidence preservation, and advocate consultation before litigation.\n\n"
            f"LANGUAGE: {language}\n\n"
            f"PROVISION-BY-PROVISION LEGAL REASONING RULES:\n"
            f"- For every applicable_sections entry, explain the actual statutory ingredients in explanation.\n"
            f"- In why_it_applies, identify supporting facts, missing facts, and facts that could make the provision inapplicable.\n"
            f"- Never use a provision merely because its keywords resemble the user's description.\n"
            f"- In nature_of_offence_or_liability, explicitly identify whether the provision creates criminal liability, civil rights or remedies, or procedural relief.\n"
            f"- In available_punishment_or_legal_consequence, give only consequences supported by the applicable statute. Distinguish statutory punishment from discretionary court relief.\n"
            f"- Use Confirmed only if the available facts establish every essential applicability requirement. Otherwise use Potentially applicable.\n"
            f"- If the legal provision cannot be reliably verified, disclose that uncertainty instead of inventing its title, wording, punishment, or consequence.\n\n"
            f"STRICT JSON VALIDATION RULES:\n"
            f"- Return every required top-level section and field.\n"
            f"- Every field defined as a list must be a JSON array.\n"
            f"- Every string-list array must contain only non-empty strings.\n"
            f"- If no reliable or relevant item exists, return an empty array: [].\n"
            f"- Never use null, a single string, or an object instead of an array.\n"
            f"- Do not invent evidence, legal provisions, precedents, deadlines, or facts.\n"
            f"- Keep evidence_to_preserve as an array of relevant evidence items.\n"
            f"- Return valid, complete JSON only; do not omit required fields.\n\n"
            f"MANDATORY JSON OUTPUT FORMAT:\n"
            f"Return ONLY a valid JSON object without markdown fences, conforming to this exact structure:\n"
            f"{{\n"
            f'  "case_overview": {{\n'
            f'    "case_type": "<Case type>",\n'
            f'    "case_summary": "<Case summary>",\n'
            f'    "parties_involved": "<Parties involved>",\n'
            f'    "court_jurisdiction": "<Court/jurisdiction>",\n'
            f'    "current_procedural_stage": "<Current procedural stage>",\n'
            f'    "main_legal_dispute": "<Main legal dispute / Key legal issues>"\n'
            f'  }},\n'
            f'  "applicable_sections": [\n'
            f'    {{\n'
            f'      "act_name": "<Act name>",\n'
            f'      "section_number": "<Section number>",\n'
            f'      "section_title": "<Section title>",\n'
            f'      "explanation": "<Explanation of ingredients and exceptions>",\n'
            f'      "why_it_applies": "<Why it applies or potential applicability>",\n'
            f'      "nature_of_offence_or_liability": "<Nature of offence or liability>",\n'
            f'      "available_punishment_or_legal_consequence": "<Available punishment or consequence>",\n'
            f'      "status": "<Confirmed / Potentially applicable>",\n'
            f'      "law_type": "<Substantive / Procedural>"\n'
            f'    }}\n'
            f'  ],\n'
            f'  "legal_analysis": {{\n'
            f'    "essential_ingredients": ["<Ingredient 1>", "<Ingredient 2>"],\n'
            f'    "evidence_required": ["<Evidence 1>", "<Evidence 2>"],\n'
            f'    "burden_and_standard_of_proof": "<Burden and standard of proof>",\n'
            f'    "strengths": ["<Strength 1>"],\n'
            f'    "weaknesses": ["<Weakness 1>"],\n'
            f'    "judicial_precedents": [\n'
            f'      {{\n'
            f'        "case_name": "<Precedent citation>",\n'
            f'        "ratio_decidendi": "<Legal principle>"\n'
            f'      }}\n'
            f'    ],\n'
            f'    "possible_legal_objections": ["<Objection 1>"]\n'
            f'  }},\n'
            f'  "lawyer_strategy": {{\n'
            f'    "party_represented": "<Complainant / Accused / Plaintiff / Defendant>",\n'
            f'    "immediate_action": "<Immediate action after summons / incident>",\n'
            f'    "documents_to_collect": ["<Document 1>", "<Document 2>"],\n'
            f'    "evidence_to_preserve": ["<Evidence to preserve>"],\n'
            f'    "preliminary_objections": ["<Preliminary objection>"],\n'
            f'    "possible_applications": ["<Application to file before court>"],\n'
            f'    "key_arguments": ["<Key legal argument>"],\n'
            f'    "relevant_precedents": ["<Key precedent>"],\n'
            f'    "risks_and_weaknesses": ["<Risk/weakness>"],\n'
            f'    "alternative_remedies_or_settlement": "<Lawful alternative remedies or settlement possibilities>"\n'
            f'  }},\n'
            f'  "court_procedure": [\n'
            f'    {{\n'
            f'      "step_number": 1,\n'
            f'      "stage_name": "<Stage name>",\n'
            f'      "procedure_details": "<Procedure details>"\n'
            f'    }}\n'
            f'  ],\n'
            f'  "stipulated_timeline": [\n'
            f'    {{\n'
            f'      "action": "<Court appearance / Filing response / Filing application / Appeal>",\n'
            f'      "applicable_deadline": "<Applicable deadline>",\n'
            f'      "legal_provision": "<Legal provision>",\n'
            f'      "starting_point": "<Starting point>"\n'
            f'    }}\n'
            f'  ],\n'
            f'  "recommended_actions": [\n'
            f'    {{\n'
            f'      "priority": 1,\n'
            f'      "category": "Immediate action",\n'
            f'      "action": "<Action description>"\n'
            f'    }},\n'
            f'    {{\n'
            f'      "priority": 2,\n'
            f'      "category": "Documents required",\n'
            f'      "action": "<Action description>"\n'
            f'    }},\n'
            f'    {{\n'
            f'      "priority": 3,\n'
            f'      "category": "Advocate consultation",\n'
            f'      "action": "<Action description>"\n'
            f'    }},\n'
            f'    {{\n'
            f'      "priority": 4,\n'
            f'      "category": "Court filing or appearance",\n'
            f'      "action": "<Action description>"\n'
            f'    }},\n'
            f'    {{\n'
            f'      "priority": 5,\n'
            f'      "category": "Follow-up action",\n'
            f'      "action": "<Action description>"\n'
            f'    }}\n'
            f'  ],\n'
            f'  "missing_information": ["<Missing facts or dates to verify>"],\n'
            f'  "sources": ["<Relevant Acts and judgments cited>"],\n'
            f'  "legal_disclaimer": "AI Legal Research and Case Analysis guidance only under Indian law. Not a police finding, judicial decree, or substitute for representation by an enrolled advocate."\n'
            f'}}\n'
        )
        providers = [
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
            # Extract JSON block even if surrounded by commentary
            json_match = re.search(r'(\{[\s\S]*\})', clean)
            if json_match:
                clean = json_match.group(1).strip()
            elif clean.startswith("```"):
                clean = re.sub(r'^```(?:json)?\s*', '', clean)
                clean = re.sub(r'\s*```$', '', clean)

            try:
                data = json.loads(clean)
            except (json.JSONDecodeError, TypeError, ValueError) as exc:
                logger.warning("%s returned invalid case-analysis JSON: %s", provider_name, exc)
                continue

            # Defensive normalization: coerce string digits for int fields
            self._normalize_case_analysis_data(data)

            is_valid, reason = self._validate_case_analysis(data)
            if is_valid:
                logger.info("%s produced valid case-analysis JSON.", provider_name)
                return data

            logger.warning("Rejected %s case-analysis JSON: %s", provider_name, reason)

        logger.warning("All AI providers failed case-analysis validation. Using safe fallback.")
        return self._generate_fallback_case_analysis(case_text, language)

    @staticmethod
    def _normalize_case_analysis_data(data: Any) -> None:
        """Coerces string digits in integer fields to int and ensures list types."""
        if not isinstance(data, dict):
            return
        procedures = data.get("court_procedure")
        if isinstance(procedures, list):
            for item in procedures:
                if isinstance(item, dict) and "step_number" in item:
                    val = item["step_number"]
                    if isinstance(val, str) and val.strip().isdigit():
                        item["step_number"] = int(val.strip())
        actions = data.get("recommended_actions")
        if isinstance(actions, list):
            for item in actions:
                if isinstance(item, dict) and "priority" in item:
                    val = item["priority"]
                    if isinstance(val, str) and val.strip().isdigit():
                        item["priority"] = int(val.strip())

    @staticmethod
    def _validate_case_analysis(data: Any) -> tuple[bool, str]:
        """Validate the structure and required content of an AI case analysis."""

        def has_text(value: Any) -> bool:
            return isinstance(value, str) and bool(value.strip())

        def text_list(value: Any) -> bool:
            return isinstance(value, list) and all(has_text(item) for item in value)

        def object_with_text_fields(value: Any, fields: List[str]) -> bool:
            return (
                isinstance(value, dict)
                and all(has_text(value.get(field)) for field in fields)
            )

        top_level = [
            "case_overview", "applicable_sections", "legal_analysis",
            "lawyer_strategy", "court_procedure", "stipulated_timeline",
            "recommended_actions", "missing_information", "sources",
            "legal_disclaimer"
        ]
        if not isinstance(data, dict):
            return False, "Root value must be a JSON object."
        if any(key not in data for key in top_level):
            return False, "One or more required top-level sections are missing."

        overview_fields = [
            "case_type", "case_summary", "parties_involved",
            "court_jurisdiction", "current_procedural_stage",
            "main_legal_dispute"
        ]
        if not object_with_text_fields(data["case_overview"], overview_fields):
            return False, "case_overview is incomplete or has the wrong type."

        section_fields = [
            "act_name", "section_number", "section_title", "explanation",
            "why_it_applies", "nature_of_offence_or_liability",
            "available_punishment_or_legal_consequence", "status", "law_type"
        ]
        sections = data["applicable_sections"]
        if not isinstance(sections, list):
            return False, "applicable_sections must be a list."
        if not all(object_with_text_fields(item, section_fields) for item in sections):
            return False, "An applicable_sections entry is incomplete."

        analysis = data["legal_analysis"]
        analysis_text_fields = ["burden_and_standard_of_proof"]
        analysis_list_fields = [
            "essential_ingredients", "evidence_required", "strengths",
            "weaknesses", "possible_legal_objections"
        ]
        if not isinstance(analysis, dict):
            return False, "legal_analysis must be an object."
        if not all(has_text(analysis.get(key)) for key in analysis_text_fields):
            return False, "legal_analysis is missing required text."
        if not all(text_list(analysis.get(key)) for key in analysis_list_fields):
            return False, "A legal_analysis list is missing or invalid."
        precedents = analysis.get("judicial_precedents")
        if not isinstance(precedents, list) or not all(
            object_with_text_fields(item, ["case_name", "ratio_decidendi"])
            for item in precedents
        ):
            return False, "judicial_precedents must be a valid list of objects."

        strategy = data["lawyer_strategy"]
        strategy_text_fields = [
            "party_represented", "immediate_action",
            "alternative_remedies_or_settlement"
        ]
        strategy_list_fields = [
            "documents_to_collect", "evidence_to_preserve",
            "preliminary_objections", "possible_applications", "key_arguments",
            "relevant_precedents", "risks_and_weaknesses"
        ]
        if not isinstance(strategy, dict):
            return False, "lawyer_strategy must be an object."
        if not all(has_text(strategy.get(key)) for key in strategy_text_fields):
            return False, "lawyer_strategy is missing required text."
        for key in strategy_list_fields:
            if not text_list(strategy.get(key)):
                return False, (
                    f"lawyer_strategy.{key} must be a list "
                    "containing only non-empty strings."
                )

        procedures = data["court_procedure"]
        if not isinstance(procedures, list) or not all(
            isinstance(item, dict)
            and isinstance(item.get("step_number"), int)
            and not isinstance(item.get("step_number"), bool)
            and object_with_text_fields(item, ["stage_name", "procedure_details"])
            for item in procedures
        ):
            return False, "court_procedure contains an invalid entry."

        timelines = data["stipulated_timeline"]
        timeline_fields = ["action", "applicable_deadline", "legal_provision", "starting_point"]
        if not isinstance(timelines, list) or not all(
            object_with_text_fields(item, timeline_fields) for item in timelines
        ):
            return False, "stipulated_timeline contains an invalid entry."

        actions = data["recommended_actions"]
        if not isinstance(actions, list) or not all(
            isinstance(item, dict)
            and isinstance(item.get("priority"), int)
            and not isinstance(item.get("priority"), bool)
            and object_with_text_fields(item, ["category", "action"])
            for item in actions
        ):
            return False, "recommended_actions contains an invalid entry."

        if not text_list(data["missing_information"]):
            return False, "missing_information must be a list of non-empty strings."
        if not text_list(data["sources"]):
            return False, "sources must be a list of non-empty strings."
        if not has_text(data["legal_disclaimer"]):
            return False, "legal_disclaimer is missing or empty."

        return True, "Valid case analysis."

    def _generate_fallback_case_analysis(
        self,
        case_text: str,
        language: str = 'en'
    ) -> Dict[str, Any]:
        """
        Returns a neutral fallback when AI providers are unavailable.
        Does not invent legal provisions, precedents, deadlines or procedures.
        """
        case_text = (case_text or "").strip()

        missing_information = [
            "The AI analysis could not be completed because the configured AI providers did not return a usable response.",
            "The complete facts and chronology of the dispute need to be reviewed.",
            "The identities and roles of the parties need to be established.",
            "The relevant location, jurisdiction and procedural stage need to be confirmed.",
            "Supporting documents and evidence need to be examined.",
            "Any applicable legislation, limitation period and filing deadline must be independently verified."
        ]

        if not case_text:
            missing_information.insert(
                0,
                "No case facts were provided."
            )

        return {
            "case_overview": {
                "case_type": "Not determined",
                "case_summary": (
                    case_text[:1000]
                    if case_text
                    else "No case facts were provided."
                ),
                "parties_involved": "Not established from the provided information.",
                "court_jurisdiction": "Not determined. Location and jurisdiction require verification.",
                "current_procedural_stage": "Not established from the provided information.",
                "main_legal_dispute": "The legal dispute cannot be reliably classified without further analysis."
            },
            "applicable_sections": [],
            "legal_analysis": {
                "essential_ingredients": [],
                "evidence_required": [
                    "Preserve relevant original documents and communications.",
                    "Keep available photographs, videos, receipts and other potentially relevant records.",
                    "Record important dates and events accurately."
                ],
                "burden_and_standard_of_proof": "Cannot be determined without identifying the applicable legal proceedings and claims.",
                "strengths": [],
                "weaknesses": [
                    "The available information has not been independently analyzed."
                ],
                "judicial_precedents": [],
                "possible_legal_objections": []
            },
            "lawyer_strategy": {
                "party_represented": "Not determined",
                "immediate_action": "Preserve relevant records and consult a qualified Indian advocate for case-specific advice.",
                "documents_to_collect": [],
                "evidence_to_preserve": [
                    "Preserve original documents and electronic communications.",
                    "Do not alter, destroy or fabricate evidence."
                ],
                "preliminary_objections": [],
                "possible_applications": [],
                "key_arguments": [],
                "relevant_precedents": [],
                "risks_and_weaknesses": [
                    "The legal position cannot be assessed without reviewing the complete facts and documents."
                ],
                "alternative_remedies_or_settlement": "Possible remedies or settlement options cannot be determined from the available information."
            },
            "court_procedure": [],
            "stipulated_timeline": [],
            "recommended_actions": [
                {
                    "priority": 1,
                    "category": "Preserve evidence",
                    "action": "Keep original documents, communications and other relevant records safe."
                },
                {
                    "priority": 2,
                    "category": "Organize case facts",
                    "action": "Prepare an accurate chronology of events and identify the people involved."
                },
                {
                    "priority": 3,
                    "category": "Advocate consultation",
                    "action": "Ask a qualified Indian advocate to verify the applicable law, remedies and any urgent deadlines."
                }
            ],
            "missing_information": missing_information,
            "sources": [],
            "legal_disclaimer": "AI case analysis was unavailable. This fallback is not a legal opinion and does not identify applicable statutory provisions, establish liability or determine court deadlines. Have the facts and applicable law reviewed by a qualified Indian advocate."
        }

    def _call_gemini_raw(
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

    def _call_groq_raw(
        self,
        prompt: str,
        max_tokens: int = 4000,
        temperature: float = 0.2
    ) -> Optional[str]:
        if not self.groq_key:
            logger.warning("Groq API key is not configured.")
            return None

        payload = {
            "model": self.groq_model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are Law Mithra, an Indian legal information assistant. Give careful, balanced answers. Never invent legal provisions."
                },
                {"role": "user", "content": prompt}
            ],
            "max_completion_tokens": max_tokens,
            "temperature": temperature
        }

        request = urllib.request.Request(
            "https://api.groq.com/openai/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.groq_key}",
                "Content-Type": "application/json"
            },
            method="POST"
        )

        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                data = json.loads(response.read().decode("utf-8"))

            choices = data.get("choices", [])
            if not choices:
                return None

            choice = choices[0]
            content = choice.get("message", {}).get("content")

            if choice.get("finish_reason") == "length":
                logger.warning("Groq response reached its token limit.")

            return content.strip() if content else None

        except Exception as exc:
            logger.warning("Groq request failed: %s", exc)
            return None
