from pathlib import Path

path = Path("backend/knowledge/services/gemini_client.py")
source = path.read_text(encoding="utf-8")

anchor = "    def analyze_legal_case("
if source.count(anchor) != 1:
    raise SystemExit("STOP: Expected exactly one analyze_legal_case method. No changes made.")

if "def _missing_requested_legal_topics(" in source:
    raise SystemExit("STOP: Completeness checker already exists. No changes made.")

helper = r'''    @staticmethod
    def _missing_requested_legal_topics(query: str, response: str) -> List[str]:
        """Check whether explicitly requested Indian-law topics appear in the answer.

        This is a topic-coverage check, not a verification of legal accuracy.
        """
        q = (query or "").casefold()
        a = (response or "").casefold()
        a = a.replace("–", "-").replace("—", "-").replace("‑", "-")
        missing = []

        def requested(pattern: str) -> bool:
            return re.search(pattern, q, flags=re.IGNORECASE | re.DOTALL) is not None

        def has_any(*terms: str) -> bool:
            return any(term.casefold() in a for term in terms)

        # Indian Easements Act, Section 13
        asks_s13 = requested(
            r"(?:easements?\s+act.{0,80}section\s*13|"
            r"section\s*13.{0,50}easements?\s+act)"
        )
        if asks_s13:
            if not has_any("necessity"):
                missing.append("Easements Act Section 13: easement of necessity")
            if not has_any("quasi-easement", "quasi easement"):
                missing.append("Easements Act Section 13: quasi-easement")
            if not has_any("transfer", "partition", "common ownership"):
                missing.append("Easements Act Section 13: transfer, partition or common ownership")

        # Indian Easements Act, Section 15
        asks_s15 = requested(
            r"(?:easements?\s+act.{0,80}section\s*15|"
            r"section\s*15.{0,50}easements?\s+act)"
        )
        if asks_s15:
            if not has_any("20 years", "20-year", "twenty years", "twenty-year"):
                missing.append("Easements Act Section 15: 20-year period")
            if not has_any("30 years", "30-year", "thirty years", "thirty-year"):
                missing.append("Easements Act Section 15: 30-year period")
            if not has_any("interruption", "interrupted", "interrupted use"):
                missing.append("Easements Act Section 15: statutory interruption")
            if not has_any("two years", "two-year", "2 years", "2-year"):
                missing.append("Easements Act Section 15: two-year timing requirement")

        # Bharatiya Nyaya Sanhita, Section 126
        asks_bns126 = requested(
            r"(?:\bbns\b.{0,60}(?:section\s*126|\b126\b)|"
            r"(?:section\s*126|\b126\b).{0,60}\bbns\b|"
            r"bharatiya\s+nyaya\s+sanhita.{0,60}(?:section\s*126|\b126\b))"
        )
        if asks_bns126:
            if not has_any("voluntary obstruction", "voluntarily obstruct", "voluntary act of obstruction"):
                missing.append("BNS Section 126: voluntary obstruction")
            if not has_any("right to proceed", "right to pass", "right of way", "legal right to proceed"):
                missing.append("BNS Section 126: person's right to proceed")
            if not has_any("good faith", "good-faith"):
                missing.append("BNS Section 126: good-faith exception")
            if not has_any("private way", "private pathway", "private road"):
                missing.append("BNS Section 126: private-way exception")

        # Bharatiya Nagarik Suraksha Sanhita, Section 166
        asks_bnss166 = requested(
            r"(?:\bbnss\b.{0,60}(?:section\s*166|\b166\b)|"
            r"(?:section\s*166|\b166\b).{0,60}\bbnss\b|"
            r"bharatiya\s+nagarik\s+suraksha\s+sanhita.{0,60}(?:section\s*166|\b166\b))"
        )
        if asks_bnss166:
            if not has_any("breach of peace", "breach-of-peace"):
                missing.append("BNSS Section 166: likelihood of breach of peace")
            if not has_any("three months", "three-month", "3 months", "3-month"):
                missing.append("BNSS Section 166: three-month condition")
            if not has_any("seasonal", "last season", "last occasion", "season or occasion"):
                missing.append("BNSS Section 166: seasonal or occasional-use condition")

        # Specific Relief Act, Sections 38 and 39
        asks_sra = requested(
            r"(?:specific relief act.{0,100}(?:section\s*38|section\s*39|sections?\s*38.{0,30}39)|"
            r"(?:section\s*38|section\s*39).{0,60}specific relief act)"
        )
        if asks_sra:
            if not has_any("perpetual injunction", "permanent injunction"):
                missing.append("Specific Relief Act Section 38: perpetual or permanent injunction")
            if not has_any("mandatory injunction"):
                missing.append("Specific Relief Act Section 39: mandatory injunction")

        # Code of Civil Procedure, Order 39 Rules 1 and 2
        asks_order39 = requested(
            r"(?:order\s*39|order\s*xxxix).{0,60}(?:rule\s*1|rule\s*2|rules?\s*1\s*(?:and|&)\s*2)?"
        )
        if asks_order39:
            if not has_any("prima facie"):
                missing.append("CPC Order 39: prima facie case")
            if not has_any("balance of convenience"):
                missing.append("CPC Order 39: balance of convenience")
            if not has_any("irreparable injury", "irreparable harm"):
                missing.append("CPC Order 39: irreparable injury or harm")

        return missing

'''

backup = path.with_name("gemini_client.py.pre_coverage_helper_backup")
if backup.exists():
    raise SystemExit(f"STOP: Backup already exists: {backup.name}")

backup.write_text(source, encoding="utf-8")
path.write_text(source.replace(anchor, helper + anchor, 1), encoding="utf-8")

print("SUCCESS: Offline legal-topic completeness checker added.")
print(f"Backup created: {backup.name}")
