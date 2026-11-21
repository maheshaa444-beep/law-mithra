from pathlib import Path

path = Path("backend/knowledge/services/gemini_client.py")
source = path.read_text(encoding="utf-8")

old = '''            try:
                return json.loads(clean)
            except Exception as exc:
                logger.warning(f"Failed to parse case analysis JSON: {exc}")
'''

new = '''            try:
                data = json.loads(clean)
                is_valid, reason = self._validate_case_analysis(data)
                if is_valid:
                    return data
                logger.warning("Rejected incomplete case analysis JSON: %s", reason)
            except (json.JSONDecodeError, TypeError, ValueError) as exc:
                logger.warning("Failed to parse case analysis JSON: %s", exc)
'''

if source.count(old) != 1:
    raise SystemExit("STOP: Could not uniquely locate the JSON parsing block. No changes made.")

marker = '''    def _generate_fallback_case_analysis(
'''

validator = '''    @staticmethod
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
        if not all(text_list(strategy.get(key)) for key in strategy_list_fields):
            return False, "A lawyer_strategy list is missing or invalid."

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

'''

if source.count(marker) != 1:
    raise SystemExit("STOP: Could not uniquely locate the fallback method. No changes made.")

source = source.replace(old, new, 1)
source = source.replace(marker, validator + marker, 1)
path.write_text(source, encoding="utf-8")
print("Case-analysis JSON validation added successfully.")
