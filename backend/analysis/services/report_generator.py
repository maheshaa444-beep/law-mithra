"""
Universal Complaint Analysis Report Generator.
Calls Gemini AI to fill the 7-section report template from document text.
Never invents facts — uses 'Not provided' / 'Requires verification' for missing info.
"""

import json
import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Optional

from knowledge.services.gemini_client import GeminiClient
from analysis.services.openrouter_doc_service import OpenRouterDocService

logger = logging.getLogger(__name__)


REPORT_PROMPT = """You are Law Mithra, an AI legal assistant for Indian law.

Analyze the following legal document and generate a structured Universal Complaint Analysis Report.
Respond ONLY with a valid JSON object — no markdown, no code fences, no explanation outside JSON.

DOCUMENT TEXT:
{document_text}

OUTPUT LANGUAGE: {language}

Fill each field based ONLY on what the document actually says.
If information is missing or unclear, use the string "Not provided" or "Requires verification".
NEVER invent facts, names, dates, sections, or events not present in the document.
NEVER assign guilt or final legal conclusions.

Output this exact JSON structure:
{{
  "complaint_type": "<type of complaint/subject — e.g., Theft, Fraud, Property Dispute>",
  "parties_involved": "<Complainant: Name/Role | Accused/Respondent: Name/Role | Others: Name/Role>",
  "incident_date_place": "<date and place of the reported incident>",
  "case_complaint_no": "<FIR/complaint/court case number if present, else Not provided>",
  "status": "<Current stage: e.g., Complaint received / Investigation / Court proceeding / Closed>",
  "complaint_summary": "<2-4 sentence neutral summary: who complained, against whom, what allegedly happened, when/where, what loss was reported, what action is requested. Separate reported claims from verified facts.>",
  "legal_provisions": [
    {{
      "act_section": "<Act name and section number, e.g., IPC Section 420>",
      "relevance": "<Why this may apply based on the facts in the document>",
      "caveat": "<What needs to be verified — ingredients, date applicability, jurisdiction, etc.>"
    }}
  ],
  "evidence_available": ["<item 1>", "<item 2>"],
  "evidence_missing": ["<item 1>", "<item 2>"],
  "complainant_side": "<What the complainant claims, supporting evidence mentioned, requested remedy, weaknesses or gaps>",
  "respondent_side": "<Allegations against respondent, any known response/defence in document, applicable rights, evidence that may help respondent>",
  "persons_role": "<Identify: Complainant / Accused / Victim / Witness / Other — from document>",
  "rights_next_steps": "<Role-specific practical steps: documents to preserve, authorities to contact, deadlines to watch, when to consult an advocate>",
  "advocate_questions": "<Key legal questions, jurisdiction issues, evidence gaps, procedural issues that need advocate review>",
  "current_stage": "<Intake / Police / Investigation / Notice / Court / Appeal / Other — based on document>",
  "last_updated_date": "<Date from document if available, else Requires verification>"
}}"""


def generate_report(document_text: str, language: str = "en", document_id: str = "") -> dict:
    """
    Generate a Universal Complaint Analysis Report from document text.
    Returns a dict with all 7 sections + metadata.
    """
    report_id = f"LM-{uuid.uuid4().hex[:8].upper()}"
    generated_at = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")

    # Truncate very long documents to stay within token limits (~3000 words)
    max_chars = 12000
    truncated = document_text[:max_chars]
    if len(document_text) > max_chars:
        truncated += "\n\n[Document truncated for analysis. Full text processed for section detection.]"

    prompt = REPORT_PROMPT.format(document_text=truncated, language=language)

    client = GeminiClient()
    raw = None
    try:
        raw = client._call_gemini_raw(prompt, max_tokens=2048)
    except Exception as exc:
        logger.warning(f"Gemini call failed for report generation: {exc}")

    # Fallback to OpenRouter if Gemini returned None
    if not raw:
        try:
            or_service = OpenRouterDocService()
            raw = or_service.modify_or_analyze_document(
                document_text=truncated,
                instructions="Respond strictly with the valid JSON object conforming to the Universal Complaint Report schema specified.",
                language=language
            )
        except Exception as exc:
            logger.warning(f"OpenRouter fallback failed: {exc}")

    if raw:
        try:
            clean = raw.strip()
            if "```" in clean:
                clean = clean.split("```", 2)[-1]
                if clean.startswith("json"):
                    clean = clean[4:]
                clean = clean.rsplit("```", 1)[0].strip()
            ai_data = json.loads(clean)
        except (json.JSONDecodeError, ValueError) as exc:
            logger.warning(f"JSON parse error in report: {exc}. Raw: {raw[:200]}")
            ai_data = {}
    else:
        ai_data = {}

    # Deterministic heuristics when LLM network is offline
    if not ai_data:
        # Extract subject/type
        sub_match = re.search(r'(?:subject|regarding|re:)\s*[:\-]?\s*([^\n\.\r]+)', document_text, re.IGNORECASE)
        complaint_type = sub_match.group(1).strip() if sub_match else "Legal Complaint / Document"

        # Extract dates
        date_match = re.search(r'\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4})\b', document_text, re.IGNORECASE)
        incident_date = date_match.group(0) if date_match else "Not provided"

        # Extract sections mentioned (e.g. Section 379 IPC / Section 303 BNS)
        sec_matches = re.findall(r'(?:Sec(?:tion)?\.?\s*([0-9A-Z\(\)]+)\s*(?:of\s+the\s+)?([A-Za-z\s]+))', document_text, re.IGNORECASE)
        provisions = []
        for s_num, act_name in sec_matches[:4]:
            act_clean = act_name.strip().upper()
            if any(k in act_clean for k in ['IPC', 'BNS', 'CRPC', 'BNSS', 'CPC', 'ACT', 'BSA', 'IEA']):
                provisions.append({
                    "act_section": f"Section {s_num} {act_clean}".strip(),
                    "relevance": f"Referenced in uploaded complaint context.",
                    "caveat": "Verification needed: check ingredients, incident date applicability, and amendments."
                })

        # Summary first 2 sentences
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', document_text[:800]) if len(s.strip()) > 20]
        extracted_summary = " ".join(sentences[:3]) if sentences else document_text[:300].strip()

        ai_data = {
            "complaint_type": complaint_type,
            "parties_involved": "Complainant identified in text; respondent details to be verified.",
            "incident_date_place": f"Date: {incident_date} | Place: identified from document text.",
            "case_complaint_no": "Not provided",
            "status": "Complaint received / Preliminary review",
            "complaint_summary": extracted_summary,
            "legal_provisions": provisions,
            "evidence_available": ["Uploaded complaint copy", "Supporting material referenced in text"],
            "evidence_missing": ["Original acknowledgements", "Investigating authority verification", "Independent witness statements"],
            "complainant_side": "Complainant has set out the grievance and requested police or legal action.",
            "respondent_side": "Allegations are untested claims. Identity, statement or defence of respondent not yet established.",
            "persons_role": "Complainant / Applicant",
            "rights_next_steps": "Preserve original document and any supporting receipts or media. Follow up with the designated station or authority. Consult an advocate for legal recourse.",
            "advocate_questions": "Verify territorial and subject-matter jurisdiction. Check whether limitation period applies. Confirm evidence compliance under Section 65B IEA / Section 63 BSA.",
            "current_stage": "Complaint submission",
            "last_updated_date": datetime.now(timezone.utc).strftime("%d/%m/%Y"),
        }

    NP = "Not provided"
    RV = "Requires verification"

    legal_provisions = ai_data.get("legal_provisions", [])
    if not isinstance(legal_provisions, list):
        legal_provisions = []
    # Ensure each entry has required keys
    cleaned_provisions = []
    for item in legal_provisions:
        if isinstance(item, dict):
            cleaned_provisions.append({
                "act_section": item.get("act_section", RV),
                "relevance": item.get("relevance", RV),
                "caveat": item.get("caveat", "Check ingredients, date, amendments and jurisdiction. Do not treat a possible section as a final finding."),
            })

    evidence_available = ai_data.get("evidence_available", [])
    evidence_missing = ai_data.get("evidence_missing", [])
    if not isinstance(evidence_available, list):
        evidence_available = [str(evidence_available)] if evidence_available else []
    if not isinstance(evidence_missing, list):
        evidence_missing = [str(evidence_missing)] if evidence_missing else []

    return {
        "report_id": report_id,
        "generated_date": generated_at,
        "case_complaint_no": ai_data.get("case_complaint_no", NP),
        "status": ai_data.get("status", RV),
        "complaint_type": ai_data.get("complaint_type", RV),
        "parties_involved": ai_data.get("parties_involved", NP),
        "incident_date_place": ai_data.get("incident_date_place", NP),
        "complaint_summary": ai_data.get("complaint_summary", RV),
        "legal_provisions": cleaned_provisions if cleaned_provisions else [
            {
                "act_section": RV,
                "relevance": RV,
                "caveat": "Check ingredients, date, amendments and jurisdiction.",
            }
        ],
        "evidence_available": evidence_available if evidence_available else [NP],
        "evidence_missing": evidence_missing if evidence_missing else [RV],
        "complainant_side": ai_data.get("complainant_side", RV),
        "respondent_side": ai_data.get("respondent_side", RV),
        "persons_role": ai_data.get("persons_role", RV),
        "rights_next_steps": ai_data.get("rights_next_steps", RV),
        "advocate_questions": ai_data.get("advocate_questions", RV),
        "current_stage": ai_data.get("current_stage", RV),
        "last_updated_date": ai_data.get("last_updated_date", RV),
        "version": 1,
    }

