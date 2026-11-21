from pathlib import Path
import re

path = Path("backend/knowledge/services/legal_ai_service.py")
backup = Path("backend/knowledge/services/legal_ai_service.py.pre_domain_matching_backup")

if not backup.exists():
    raise SystemExit("STOP: Backup not found. No changes made.")

source = path.read_text(encoding="utf-8")

pattern = r"    def _match_legal_domain\(.*?(?=    def _get_localized_remedies\()"

replacement = '''    def _match_legal_domain(self, query: str) -> Optional[Dict[str, Any]]:
        """Matches specific legal issues without relying on generic words."""
        q_lower = " ".join(query.casefold().split())

        for domain in VERIFIED_LEGAL_DOMAINS:
            domain_id = domain.get("id")

            if domain_id == "land_encroachment":
                specific_phrases = (
                    "encroachment",
                    "encroached",
                    "dispossessed",
                    "trespass",
                    "boundary dispute",
                    "boundary wall",
                    "pathway",
                    "right of way",
                    "blocking access",
                    "blocked access",
                    "blocking the road",
                    "wall blocking",
                    "constructed a wall",
                    "built a wall",
                    "illegal occupation",
                    "occupied my land",
                    "occupied our land",
                    "land grabbing",
                )

                if any(term in q_lower for term in specific_phrases):
                    return domain

                generic_english = {
                    "land", "property", "site", "plot", "survey"
                }

                for keyword in domain.get("keywords", []):
                    term = keyword.casefold().strip()
                    if not term or term in generic_english:
                        continue
                    if term in q_lower:
                        return domain

            elif domain_id == "cheque_bounce":
                specific_phrases = (
                    "cheque",
                    "check",
                    "dishonour",
                    "dishonor",
                    "returned unpaid",
                )

                if any(term in q_lower for term in specific_phrases):
                    return domain

                generic_english = {"bank", "insufficient", "bounce"}

                for keyword in domain.get("keywords", []):
                    term = keyword.casefold().strip()
                    if not term or term in generic_english:
                        continue
                    if term in q_lower:
                        return domain

            else:
                for keyword in domain.get("keywords", []):
                    term = keyword.casefold().strip()
                    if term and term in q_lower:
                        return domain

        return None

'''

updated, count = re.subn(pattern, replacement, source, count=1, flags=re.DOTALL)

if count != 1:
    raise SystemExit("STOP: Matching function was not uniquely located. No changes made.")

path.write_text(updated, encoding="utf-8")
print("SUCCESS: Domain matching function updated.")
