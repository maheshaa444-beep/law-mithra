from django.test import SimpleTestCase
from knowledge.services.legal_ai_service import LegalAIService, VERIFIED_LEGAL_DOMAINS, DISCLAIMER_TEXTS
from knowledge.services.gemini_client import GeminiClient, clean_legal_text


class LegalDomainMatchingTests(SimpleTestCase):

    def setUp(self):
        self.service = LegalAIService.__new__(LegalAIService)

    def test_pathway_blocked_matches_land_domain(self):
        result = self.service._match_legal_domain(
            "My neighbour constructed a wall blocking our family pathway."
        )
        self.assertIsNotNone(result)
        self.assertEqual(result["id"], "land_encroachment")

    def test_cheque_bounce_matches_cheque_domain(self):
        result = self.service._match_legal_domain(
            "My bank returned my cheque due to insufficient funds."
        )
        self.assertIsNotNone(result)
        self.assertEqual(result["id"], "cheque_bounce")

    def test_property_prices_do_not_match_land_encroachment(self):
        result = self.service._match_legal_domain(
            "What are the latest residential property prices?"
        )
        self.assertIsNone(result)

    def test_unrelated_question_does_not_match_any_domain(self):
        result = self.service._match_legal_domain(
            "How do I prepare for my computer science examination?"
        )
        self.assertIsNone(result)


class LegalAICompletenessCheckerTests(SimpleTestCase):

    def test_bns_126_full_coverage_with_equivalent_wording(self):
        query = "Can I lodge a police complaint under BNS Section 126 for the blocked path?"
        response = (
            "Under BNS Section 126, wrongful restraint involves voluntary obstruction "
            "that prevents a person from proceeding in a direction where they have a lawful right of way. "
            "However, the statutory exception provides that obstructing a private pathway is not an "
            "offence if the person acts in good faith believing they have a lawful right to obstruct it. "
            "Police cannot adjudicate disputed private easements."
        )
        missing = GeminiClient._missing_requested_legal_topics(query, response)
        self.assertEqual(missing, [], f"Expected no missing topics, got {missing}")

    def test_bns_126_missing_exception_is_flagged(self):
        query = "Explain BNS Section 126."
        response = (
            "Section 126 of the BNS deals with voluntary obstruction of any person "
            "who has a legal right to proceed."
        )
        missing = GeminiClient._missing_requested_legal_topics(query, response)
        self.assertIn("BNS Section 126: statutory good-faith private-way exception", missing)

    def test_bnss_166_full_coverage_with_equivalent_wording(self):
        query = "Can the SDM intervene under BNSS Section 166?"
        response = (
            "Under BNSS Section 166, an Executive Magistrate may initiate an inquiry if a dispute "
            "regarding an alleged right of use of land or water is likely to cause a breach of peace. "
            "For a year-round right, it must have been exercised within three months before the report. "
            "For a seasonal right, it must have been exercised during the last season or occasion. "
            "Any order is an interim preventive measure subject to Civil Court determination."
        )
        missing = GeminiClient._missing_requested_legal_topics(query, response)
        self.assertEqual(missing, [], f"Expected no missing topics, got {missing}")

    def test_bnss_166_missing_three_month_condition_flagged(self):
        query = "Can we file under BNSS Section 166 for breach of peace?"
        response = (
            "Under BNSS Section 166, an Executive Magistrate can act if there is a likelihood "
            "of breach of peace concerning a pathway or seasonal water channel."
        )
        missing = GeminiClient._missing_requested_legal_topics(query, response)
        self.assertTrue(any("three-month" in item for item in missing))

    def test_easements_act_s13_and_s15_equivalent_wording(self):
        query = "Does Easements Act Section 13 or Section 15 apply to this pathway?"
        response = (
            "Under the Indian Easements Act Section 13, an easement of necessity requires prior common ownership "
            "followed by partition or transfer, whereas a quasi-easement requires apparent and continuous use. "
            "Under Section 15, prescription requires peaceable and open enjoyment without interruption for twenty years "
            "on private land (or thirty years on government land), ending within two years prior to the suit."
        )
        missing = GeminiClient._missing_requested_legal_topics(query, response)
        self.assertEqual(missing, [], f"Expected no missing topics, got {missing}")

    def test_kannada_equivalent_wording_recognized(self):
        query = "ಬಿಎನ್‌ಎಸ್ ಕಲಂ 126 (BNS Section 126) ಅನ್ವಯಿಸುತ್ತದೆಯೇ?"
        response = (
            "ಬಿಎನ್‌ಎಸ್ ಕಲಂ 126 ರ ಪ್ರಕಾರ, ಚಲಿಸುವ ಹಕ್ಕು ಇರುವ ವ್ಯಕ್ತಿಗೆ ಸ್ವಯಂಪ್ರೇರಿತ ಅಡಚಣೆ ಉಂಟುಮಾಡುವುದು ತಪ್ಪಾಗುತ್ತದೆ. "
            "ಆದರೆ, ಖಾಸಗಿ ದಾರಿಯನ್ನು ಸದ್ಭಾವನೆಯಿಂದ ಮತ್ತು ತಡೆಯುವ ಕಾನೂನುಬದ್ಧ ಹಕ್ಕು ಇದೆ ಎಂದು ನಂಬಿ ತಡೆದರೆ ಅದು ಅಪರಾಧವಾಗುವುದಿಲ್ಲ."
        )
        missing = GeminiClient._missing_requested_legal_topics(query, response)
        self.assertEqual(missing, [], f"Expected Kannada answer to be recognized without false positives, got {missing}")

    def test_unrequested_topics_do_not_produce_warnings(self):
        query = "How do I divide property among family members amicably?"
        response = "Family settlements and partition deeds can be executed through mutual registration."
        missing = GeminiClient._missing_requested_legal_topics(query, response)
        self.assertEqual(missing, [])


class TextCleaningAndScriptIntegrityTests(SimpleTestCase):

    def test_clean_legal_text_formatting(self):
        raw = "### Title\n\n**Section 126** is *applicable*.\n* First point\n* Second point\n\n[Section 166]"
        cleaned = clean_legal_text(raw)
        self.assertNotIn("###", cleaned)
        self.assertNotIn("**", cleaned)
        self.assertNotIn("[Section 166]", cleaned)
        self.assertIn("Section 166", cleaned)
        self.assertIn("• First point", cleaned)
        self.assertIn("• Second point", cleaned)

    def test_clean_legal_text_preserves_indic_scripts(self):
        raw = "**ಕಾನೂನು ಮಾಹಿತಿ**: ಭಾರತೀಯ ನ್ಯಾಯ ಸಂಹಿತೆ ಕಲಂ ೧೨೬ (BNS Section 126)."
        cleaned = clean_legal_text(raw)
        self.assertIn("ಕಾನೂನು ಮಾಹಿತಿ", cleaned)
        self.assertIn("ಕಲಂ ೧೨೬", cleaned)
        self.assertNotIn("**", cleaned)


class StatutoryKnowledgeAccuracyTests(SimpleTestCase):

    def test_bns_and_bnss_elements_in_knowledge_domain(self):
        land_domain = next(d for d in VERIFIED_LEGAL_DOMAINS if d['id'] == 'land_encroachment')
        laws = {law['act']: law for law in land_domain['applicable_laws']}

        # BNS 126 verification
        bns_law = laws.get('Bharatiya Nyaya Sanhita, 2023')
        self.assertIsNotNone(bns_law)
        self.assertIn('Section 126', bns_law['sections'])
        self.assertIn('good-faith', bns_law['summary'])
        self.assertIn('private-way exception', bns_law['summary'])
        self.assertIn('opposing-party defences', bns_law['summary'])

        # BNSS 166 verification
        bnss_law = laws.get('Bharatiya Nagarik Suraksha Sanhita, 2023')
        self.assertIsNotNone(bnss_law)
        self.assertIn('Section 166', bnss_law['sections'])
        self.assertIn('3 months', bnss_law['summary'])
        self.assertIn('Executive Magistrate', bnss_law['summary'])
        self.assertIn('interim preventive measure', bnss_law['english_statute'])

    def test_all_ten_languages_have_disclaimers(self):
        expected_langs = {'en', 'kn', 'hi', 'ta', 'te', 'ml', 'mr', 'bn', 'gu', 'pa'}
        for lang in expected_langs:
            self.assertIn(lang, DISCLAIMER_TEXTS)
            self.assertTrue(len(DISCLAIMER_TEXTS[lang]) > 20)


class CaseAnalysisWorkflowTests(SimpleTestCase):

    def setUp(self):
        self.client = GeminiClient()

    def test_civil_property_case_analysis_structure(self):
        sample = {
            "case_overview": {
                "case_type": "Civil Property / Easement & Injunction Dispute",
                "case_summary": "Neighbour built a boundary wall obstructing a 22-year-old pathway used by the claimant.",
                "parties_involved": "Plaintiff (Claimant) vs Defendant (Neighbour)",
                "court_jurisdiction": "Civil Judge (Junior Division) within local territorial jurisdiction",
                "current_procedural_stage": "Pre-suit dispute / Notice stage",
                "main_legal_dispute": "Whether the plaintiff has acquired a prescriptive right of way under Section 15 of Indian Easements Act, 1882, and is entitled to an injunction under Sections 38 and 39 of Specific Relief Act, 1963."
            },
            "applicable_sections": [
                {
                    "act_name": "Indian Easements Act, 1882",
                    "section_number": "Section 15",
                    "section_title": "Acquisition by prescription",
                    "explanation": "Right of way peaceably and openly enjoyed as an easement and as of right without interruption for 20 years.",
                    "why_it_applies": "The pathway has allegedly been used continuously for 22 years prior to recent obstruction.",
                    "nature_of_offence_or_liability": "Civil right acquired by statutory prescription",
                    "available_punishment_or_legal_consequence": "Declaration of easementary right of way",
                    "status": "Potentially applicable",
                    "law_type": "Substantive"
                },
                {
                    "act_name": "Specific Relief Act, 1963",
                    "section_number": "Section 38",
                    "section_title": "Perpetual injunction when granted",
                    "explanation": "Injunction to prevent breach of obligation or invasion of property rights.",
                    "why_it_applies": "To restrain neighbour from obstructing peaceful passage.",
                    "nature_of_offence_or_liability": "Civil equitable remedy",
                    "available_punishment_or_legal_consequence": "Permanent restraining order against defendant",
                    "status": "Potentially applicable",
                    "law_type": "Substantive"
                }
            ],
            "legal_analysis": {
                "essential_ingredients": [
                    "Continuous, peaceable, open user for at least 20 years",
                    "Enjoyment as of right, without permissive license",
                    "Suit instituted within 2 years of the end of the 20-year period"
                ],
                "evidence_required": [
                    "Village map and survey sketches",
                    "Photographs of the pathway and wall",
                    "Affidavits of long-standing neighbours"
                ],
                "burden_and_standard_of_proof": "Preponderance of probabilities on the plaintiff",
                "strengths": ["Long continuous user exceeding 20 years"],
                "weaknesses": ["Lack of registered grant deed", "Risk of defendant claiming permissive user"],
                "judicial_precedents": [],
                "possible_legal_objections": [
                    "Defendant may object that use was purely permissive license under Section 52 Easements Act."
                ]
            },
            "lawyer_strategy": {
                "party_represented": "Plaintiff",
                "immediate_action": "Serve a formal legal notice calling for removal of the obstruction.",
                "documents_to_collect": ["Title deed", "Survey settlement sketch", "Tax receipts"],
                "evidence_to_preserve": ["Photographs with geo-coordinates", "Police acknowledgement if any"],
                "preliminary_objections": ["Defendant's plea of lack of territorial jurisdiction if improperly valued"],
                "possible_applications": ["Application for ad-interim temporary injunction under Order 39 Rules 1 and 2 CPC"],
                "key_arguments": ["22 years uninterrupted user created an indefeasible prescriptive easement"],
                "relevant_precedents": [],
                "risks_and_weaknesses": ["Delay in filing suit beyond 2 years from obstruction"],
                "alternative_remedies_or_settlement": "Mediation to establish a mutually agreed demarcated route."
            },
            "court_procedure": [
                {
                    "step_number": 1,
                    "stage_name": "Plaint filing",
                    "procedure_details": "File civil suit with interim injunction application before Civil Judge."
                }
            ],
            "stipulated_timeline": [
                {
                    "action": "Institution of suit under Section 15 Easements Act",
                    "applicable_deadline": "Within 2 years of the 20-year period",
                    "legal_provision": "Section 15, Indian Easements Act, 1882",
                    "starting_point": "From the end of the prescriptive period"
                }
            ],
            "recommended_actions": [
                {
                    "priority": 1,
                    "category": "Immediate action",
                    "action": "Photograph the obstruction and collect survey records."
                }
            ],
            "missing_information": [
                "Exact date the pathway was first used",
                "Whether the servient land belongs to private person or Government"
            ],
            "sources": ["Indian Easements Act, 1882", "Specific Relief Act, 1963", "Code of Civil Procedure, 1908"],
            "legal_disclaimer": "AI Legal Research guidance only. Consult an enrolled advocate before initiating civil litigation."
        }
        is_valid, reason = GeminiClient._validate_case_analysis(sample)
        self.assertTrue(is_valid, f"Validation failed: {reason}")

    def test_cheque_bounce_case_analysis_structure(self):
        sample = {
            "case_overview": {
                "case_type": "Criminal / Negotiable Instruments Act Dispute",
                "case_summary": "Cheque for Rs. 5,00,000 dishonoured for funds insufficient; statutory notice issued.",
                "parties_involved": "Complainant (Payee) vs Accused (Drawer)",
                "court_jurisdiction": "Judicial Magistrate First Class / Metropolitan Magistrate",
                "current_procedural_stage": "Statutory demand notice served; awaiting payment window",
                "main_legal_dispute": "Dishonour of cheque under Section 138 of Negotiable Instruments Act, 1881."
            },
            "applicable_sections": [
                {
                    "act_name": "Negotiable Instruments Act, 1881",
                    "section_number": "Section 138",
                    "section_title": "Dishonour of cheque for insufficiency, etc., of funds in the account",
                    "explanation": "Offence punishable with imprisonment up to 2 years, or with fine up to twice cheque amount, or both.",
                    "why_it_applies": "Cheque returned unpaid with bank memo Funds Insufficient.",
                    "nature_of_offence_or_liability": "Compoundable, bailable criminal offence",
                    "available_punishment_or_legal_consequence": "Imprisonment up to 2 years or fine up to twice the cheque amount",
                    "status": "Confirmed",
                    "law_type": "Substantive"
                }
            ],
            "legal_analysis": {
                "essential_ingredients": [
                    "Cheque drawn for discharge of legally enforceable debt",
                    "Presented within 3 months validity",
                    "Bank return memo for insufficient funds",
                    "Written demand notice within 30 days of memo",
                    "Failure to pay within 15 days of notice receipt"
                ],
                "evidence_required": ["Original cheque", "Bank return memo", "Legal notice", "Postal tracking report"],
                "burden_and_standard_of_proof": "Statutory presumption under Sec 139; accused may rebut on preponderance of probabilities",
                "strengths": ["Documentary evidence and postal delivery confirmation"],
                "weaknesses": ["Accused may claim cheque was given as security"],
                "judicial_precedents": [],
                "possible_legal_objections": ["Accused may challenge service of statutory demand notice."]
            },
            "lawyer_strategy": {
                "party_represented": "Complainant",
                "immediate_action": "Wait for 15-day notice period to expire, then prepare criminal complaint.",
                "documents_to_collect": ["Invoices/bills showing debt", "Bank statement", "Postal receipt"],
                "evidence_to_preserve": ["Original postal dispatch receipt and delivery tracking sheet"],
                "preliminary_objections": ["Plea of limitation if complaint is delayed beyond 30 days of cause of action"],
                "possible_applications": ["Application for interim compensation under Section 143A NI Act"],
                "key_arguments": ["Statutory presumption of consideration and liability under Section 118 and 139"],
                "relevant_precedents": [],
                "risks_and_weaknesses": ["Accused alleging material alteration of cheque"],
                "alternative_remedies_or_settlement": "Lok Adalat settlement or compounding under Section 147 NI Act."
            },
            "court_procedure": [
                {
                    "step_number": 1,
                    "stage_name": "Filing of Complaint",
                    "procedure_details": "File complaint under Section 142 NI Act within 30 days of cause of action."
                }
            ],
            "stipulated_timeline": [
                {
                    "action": "Filing Criminal Complaint",
                    "applicable_deadline": "Within 30 days from expiry of 15 days notice window",
                    "legal_provision": "Section 142(1)(b), NI Act, 1881",
                    "starting_point": "16th day after service of notice"
                }
            ],
            "recommended_actions": [
                {
                    "priority": 1,
                    "category": "Immediate action",
                    "action": "Track postal delivery and note the 15-day expiry date."
                }
            ],
            "missing_information": ["Exact date of receipt of notice by the drawer"],
            "sources": ["Negotiable Instruments Act, 1881", "Bharatiya Nagarik Suraksha Sanhita, 2023"],
            "legal_disclaimer": "AI Legal guidance only under Indian law. Consult an advocate before court filing."
        }
        is_valid, reason = GeminiClient._validate_case_analysis(sample)
        self.assertTrue(is_valid, f"Validation failed: {reason}")

    def test_criminal_complaint_case_analysis_structure(self):
        sample = {
            "case_overview": {
                "case_type": "Criminal / Physical Assault & Wrongful Restraint Dispute",
                "case_summary": "Complainant was stopped and assaulted on a public street by known individuals.",
                "parties_involved": "Complainant vs Accused Persons",
                "court_jurisdiction": "Judicial Magistrate / Jurisdictional Police Station",
                "current_procedural_stage": "Pre-FIR / Police reporting stage",
                "main_legal_dispute": "Offences of wrongful restraint, assault, and criminal intimidation under BNS 2023."
            },
            "applicable_sections": [
                {
                    "act_name": "Bharatiya Nyaya Sanhita, 2023",
                    "section_number": "Section 126",
                    "section_title": "Wrongful restraint",
                    "explanation": "Voluntarily obstructing a person preventing them from proceeding where they have a right to proceed.",
                    "why_it_applies": "Complainant was physically prevented from proceeding on a public road.",
                    "nature_of_offence_or_liability": "Cognizable, bailable criminal offence",
                    "available_punishment_or_legal_consequence": "Simple imprisonment up to 1 month or fine up to Rs. 5,000",
                    "status": "Confirmed",
                    "law_type": "Substantive"
                }
            ],
            "legal_analysis": {
                "essential_ingredients": ["Voluntary obstruction", "Right to proceed along public way"],
                "evidence_required": ["Medical examination certificate", "CCTV footage", "Witness statements"],
                "burden_and_standard_of_proof": "Beyond reasonable doubt on prosecution",
                "strengths": ["Independent eyewitness testimony", "Prompt police intimation"],
                "weaknesses": ["Delay in medical examination"],
                "judicial_precedents": [],
                "possible_legal_objections": ["Accused may raise alibi or cross-complaint."]
            },
            "lawyer_strategy": {
                "party_represented": "Complainant",
                "immediate_action": "Seek immediate government hospital medical examination (MLC) and file written complaint.",
                "documents_to_collect": ["MLC report", "Photographs of injuries"],
                "evidence_to_preserve": ["Clothing worn during incident", "CCTV video footage copies"],
                "preliminary_objections": ["Accused plea of false implication due to pre-existing enmity"],
                "possible_applications": ["Application under Section 175(3) BNSS if police refuse to register FIR"],
                "key_arguments": ["Unprovoked assault on public street supported by medical records"],
                "relevant_precedents": [],
                "risks_and_weaknesses": ["Inconsistencies in initial oral complaint vs medical records"],
                "alternative_remedies_or_settlement": "Compounding of bailable offences with court permission."
            },
            "court_procedure": [
                {
                    "step_number": 1,
                    "stage_name": "FIR Registration",
                    "procedure_details": "Lodging of FIR under Section 173 BNSS before jurisdictional police station."
                }
            ],
            "stipulated_timeline": [
                {
                    "action": "Filing FIR",
                    "applicable_deadline": "Promptly without unjustified delay",
                    "legal_provision": "Section 173, Bharatiya Nagarik Suraksha Sanhita, 2023",
                    "starting_point": "Immediately following the incident"
                }
            ],
            "recommended_actions": [
                {
                    "priority": 1,
                    "category": "Immediate action",
                    "action": "Obtain MLC certificate from nearest hospital."
                }
            ],
            "missing_information": ["Identity of third unknown assailant"],
            "sources": ["Bharatiya Nyaya Sanhita, 2023", "Bharatiya Nagarik Suraksha Sanhita, 2023"],
            "legal_disclaimer": "AI Legal guidance only. Not a formal police finding or judicial order."
        }
        is_valid, reason = GeminiClient._validate_case_analysis(sample)
        self.assertTrue(is_valid, f"Validation failed: {reason}")

    def test_contract_dispute_case_analysis_structure(self):
        sample = {
            "case_overview": {
                "case_type": "Commercial Contract / Breach of Agreement Dispute",
                "case_summary": "Vendor failed to deliver custom machinery after receiving 40% advance payment.",
                "parties_involved": "Buyer (Plaintiff) vs Vendor (Defendant)",
                "court_jurisdiction": "Commercial Court / District Court having territorial jurisdiction",
                "current_procedural_stage": "Pre-litigation mediation stage",
                "main_legal_dispute": "Breach of contract, recovery of advance, and claim for damages under Contract Act 1872."
            },
            "applicable_sections": [
                {
                    "act_name": "Indian Contract Act, 1872",
                    "section_number": "Section 73",
                    "section_title": "Compensation for loss or damage caused by breach of contract",
                    "explanation": "Party suffering breach is entitled to compensation for loss naturally arising in the usual course.",
                    "why_it_applies": "Vendor breached agreed delivery milestone causing direct operational losses.",
                    "nature_of_offence_or_liability": "Civil contractual liability",
                    "available_punishment_or_legal_consequence": "Decree for compensatory damages and refund of advance",
                    "status": "Confirmed",
                    "law_type": "Substantive"
                }
            ],
            "legal_analysis": {
                "essential_ingredients": [
                    "Valid written contract with lawful consideration",
                    "Breach of delivery commitment by vendor",
                    "Direct measurable financial loss incurred by buyer"
                ],
                "evidence_required": ["Written purchase order", "Proof of advance bank transfer", "Email notices of breach"],
                "burden_and_standard_of_proof": "Preponderance of probabilities on the plaintiff",
                "strengths": ["Documented milestone schedule and unfulfilled delivery date"],
                "weaknesses": ["Absence of liquidated damages clause"],
                "judicial_precedents": [],
                "possible_legal_objections": ["Defendant claiming force majeure or scope alterations."]
            },
            "lawyer_strategy": {
                "party_represented": "Buyer (Plaintiff)",
                "immediate_action": "Issue formal legal notice terminating agreement and demanding full refund plus interest.",
                "documents_to_collect": ["Purchase contract", "Bank statement", "Communication log"],
                "evidence_to_preserve": ["Email server records with full headers", "Delivery receipts"],
                "preliminary_objections": ["Defendant asserting arbitration clause or forum selection clause"],
                "possible_applications": ["Pre-institution mediation application under Section 12A Commercial Courts Act"],
                "key_arguments": ["Unjust enrichment and failure of consideration under Section 65 Contract Act"],
                "relevant_precedents": [],
                "risks_and_weaknesses": ["Vendor insolvency or asset dissipation during suit"],
                "alternative_remedies_or_settlement": "Mediation settlement for staged refund."
            },
            "court_procedure": [
                {
                    "step_number": 1,
                    "stage_name": "Pre-Institution Mediation",
                    "procedure_details": "Application before Legal Services Authority under Section 12A Commercial Courts Act."
                }
            ],
            "stipulated_timeline": [
                {
                    "action": "Commercial Suit for breach of contract",
                    "applicable_deadline": "Within 3 years from date of breach",
                    "legal_provision": "Article 55, Limitation Act, 1963",
                    "starting_point": "From the date the contract was broken"
                }
            ],
            "recommended_actions": [
                {
                    "priority": 1,
                    "category": "Immediate action",
                    "action": "Issue formal legal notice for refund and termination."
                }
            ],
            "missing_information": ["Whether contract contains a binding arbitration clause"],
            "sources": ["Indian Contract Act, 1872", "Commercial Courts Act, 2015", "Limitation Act, 1963"],
            "legal_disclaimer": "AI Legal guidance only under Indian law. Consult an advocate before commercial filing."
        }
        is_valid, reason = GeminiClient._validate_case_analysis(sample)
        self.assertTrue(is_valid, f"Validation failed: {reason}")

    def test_insufficient_information_fallback_analysis(self):
        # Empty query
        fallback_empty = self.client._generate_fallback_case_analysis("")
        is_valid, reason = GeminiClient._validate_case_analysis(fallback_empty)
        self.assertTrue(is_valid, f"Empty fallback invalid: {reason}")
        self.assertEqual(fallback_empty["applicable_sections"], [])
        self.assertTrue(len(fallback_empty["missing_information"]) >= 5)

        # Minimal vague text
        fallback_vague = self.client._generate_fallback_case_analysis("A person took some money and didn't give it back.")
        is_valid, reason = GeminiClient._validate_case_analysis(fallback_vague)
        self.assertTrue(is_valid, f"Vague fallback invalid: {reason}")
        self.assertIn("A person took some money", fallback_vague["case_overview"]["case_summary"])
        self.assertIn("advocate", fallback_vague["legal_disclaimer"].lower())


class CaseAnalysisValidationResilienceTests(SimpleTestCase):

    def test_normalization_coerces_string_digits_to_int(self):
        data = {
            "court_procedure": [
                {"step_number": "1", "stage_name": "Filing", "procedure_details": "Filing plaint"},
                {"step_number": "2", "stage_name": "Summons", "procedure_details": "Issue summons"}
            ],
            "recommended_actions": [
                {"priority": "1", "category": "Urgent", "action": "Preserve documents"},
                {"priority": "2", "category": "Next", "action": "Consult advocate"}
            ]
        }
        GeminiClient._normalize_case_analysis_data(data)
        self.assertEqual(data["court_procedure"][0]["step_number"], 1)
        self.assertEqual(data["court_procedure"][1]["step_number"], 2)
        self.assertEqual(data["recommended_actions"][0]["priority"], 1)
        self.assertEqual(data["recommended_actions"][1]["priority"], 2)

    def test_validation_rejects_missing_top_level_section(self):
        data = {
            "case_overview": {},
            "applicable_sections": []
            # Missing other required sections
        }
        is_valid, reason = GeminiClient._validate_case_analysis(data)
        self.assertFalse(is_valid)
        self.assertIn("missing", reason)

    def test_validation_rejects_non_dict_root(self):
        is_valid, reason = GeminiClient._validate_case_analysis("not a dict")
        self.assertFalse(is_valid)
        self.assertIn("JSON object", reason)


import uuid
import json
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from knowledge.models import ChatSession, ChatMessage


class ChatConversationPersistenceTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user_a = User.objects.create_user(
            username='user_a@lawmithra.in',
            email='user_a@lawmithra.in',
            password='PasswordA!2026'
        )
        self.user_b = User.objects.create_user(
            username='user_b@lawmithra.in',
            email='user_b@lawmithra.in',
            password='PasswordB!2026'
        )
        refresh_a = RefreshToken.for_user(self.user_a)
        self.token_a = str(refresh_a.access_token)

        refresh_b = RefreshToken.for_user(self.user_b)
        self.token_b = str(refresh_b.access_token)

    def test_create_and_list_chat_sessions(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_a}')
        # Create session
        res = self.client.post('/api/knowledge/sessions/', {
            'title': 'Property Boundary Dispute'
        }, format='json')
        self.assertEqual(res.status_code, 201)
        session_id = res.json()['id']

        # List sessions
        list_res = self.client.get('/api/knowledge/sessions/')
        self.assertEqual(list_res.status_code, 200)
        sessions = list_res.json()
        self.assertEqual(len(sessions), 1)
        self.assertEqual(sessions[0]['id'], session_id)
        self.assertEqual(sessions[0]['title'], 'Property Boundary Dispute')

    def test_chat_session_user_isolation(self):
        # User A creates session
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_a}')
        res = self.client.post('/api/knowledge/sessions/', {
            'title': 'Confidential Dispute User A'
        }, format='json')
        session_a_id = res.json()['id']

        # User B switches context
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_b}')

        # User B list should be empty
        list_res = self.client.get('/api/knowledge/sessions/')
        self.assertEqual(list_res.status_code, 200)
        self.assertEqual(len(list_res.json()), 0)

        # User B cannot access User A's session detail -> 404
        detail_res = self.client.get(f'/api/knowledge/sessions/{session_a_id}/')
        self.assertEqual(detail_res.status_code, 404)

        # User B cannot delete User A's session -> 404
        delete_res = self.client.delete(f'/api/knowledge/sessions/{session_a_id}/')
        self.assertEqual(delete_res.status_code, 404)

        # User A's session still exists in DB
        self.assertTrue(ChatSession.objects.filter(id=session_a_id).exists())

    def test_multi_turn_chat_persistence_and_ordering(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_a}')

        # Turn 1: create chat without session_id (auto-creates session)
        req_id_1 = str(uuid.uuid4())
        chat_res = self.client.post('/api/knowledge/chat/', {
            'query': 'What is Section 138 of Negotiable Instruments Act?',
            'preferred_language': 'en',
            'client_request_id': req_id_1,
        }, format='json')
        self.assertEqual(chat_res.status_code, 200)
        session_id = chat_res.json()['session_id']

        # Verify session has 2 messages (user turn + assistant turn)
        detail_res = self.client.get(f'/api/knowledge/sessions/{session_id}/')
        self.assertEqual(detail_res.status_code, 200)
        data = detail_res.json()
        self.assertEqual(len(data['messages']), 2)
        self.assertEqual(data['messages'][0]['sender'], 'user')
        self.assertEqual(data['messages'][0]['sequence_number'], 1)
        self.assertEqual(data['messages'][1]['sender'], 'assistant')
        self.assertEqual(data['messages'][1]['sequence_number'], 2)

        # Turn 2: continue conversation passing session_id
        req_id_2 = str(uuid.uuid4())
        chat_res_2 = self.client.post('/api/knowledge/chat/', {
            'query': 'What is the limitation period for filing notice?',
            'session_id': session_id,
            'client_request_id': req_id_2,
        }, format='json')
        self.assertEqual(chat_res_2.status_code, 200)

        # Verify session now has 4 messages sequenced 1, 2, 3, 4
        detail_res_2 = self.client.get(f'/api/knowledge/sessions/{session_id}/')
        messages = detail_res_2.json()['messages']
        self.assertEqual(len(messages), 4)
        self.assertEqual([m['sequence_number'] for m in messages], [1, 2, 3, 4])

    def test_individual_session_deletion(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_a}')

        # Create two distinct sessions
        s1 = self.client.post('/api/knowledge/sessions/', {'title': 'Case 1'}, format='json').json()
        s2 = self.client.post('/api/knowledge/sessions/', {'title': 'Case 2'}, format='json').json()

        # Delete Session 1
        del_res = self.client.delete(f'/api/knowledge/sessions/{s1["id"]}/')
        self.assertEqual(del_res.status_code, 200)

        # Verify Session 1 is deleted
        self.assertEqual(self.client.get(f'/api/knowledge/sessions/{s1["id"]}/').status_code, 404)

        # Verify Session 2 is intact
        s2_res = self.client.get(f'/api/knowledge/sessions/{s2["id"]}/')
        self.assertEqual(s2_res.status_code, 200)
        self.assertEqual(s2_res.json()['title'], 'Case 2')

    def test_idempotent_retry_prevents_duplicate_turns(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_a}')

        req_id = str(uuid.uuid4())
        payload = {
            'query': 'What are the penalties under BNS Section 318?',
            'client_request_id': req_id,
        }
        res1 = self.client.post('/api/knowledge/chat/', payload, format='json')
        self.assertEqual(res1.status_code, 200)
        session_id = res1.json()['session_id']

        # Retry with identical client_request_id
        res2 = self.client.post('/api/knowledge/chat/', {
            'query': 'What are the penalties under BNS Section 318?',
            'session_id': session_id,
            'client_request_id': req_id,
        }, format='json')
        self.assertEqual(res2.status_code, 200)
        self.assertTrue(res2.json().get('idempotent_replay'))

        # Messages should remain 2, not 4
        detail = self.client.get(f'/api/knowledge/sessions/{session_id}/').json()
        self.assertEqual(len(detail['messages']), 2)


class StolenMobilePhoneLegalAccuracyTests(SimpleTestCase):
    """
    Regression tests verifying targeted legal accuracy improvements for stolen/lost mobile phone responses:
    1. BNSS Section 173(1): Zero FIR irrespective of territorial jurisdiction.
    2. BNSS Section 173(3): Preliminary inquiry is discretionary for 3-7 year offences with DSP permission, not mandatory for all complaints.
    3. CEIR Requirements: Police report, re-issued SIM for verification OTP, ID proof, IMEI; purchase invoice is optional.
    4. CEIR Scope: Blocks device IMEI from Indian mobile/cellular networks; does not claim entire device becomes unusable.
    5. e-FIR: Availability and procedure vary by state.
    6. Fact vs Allegation: Avoids presenting allegations as established facts.
    """

    def setUp(self):
        self.service = LegalAIService.__new__(LegalAIService)

    def test_stolen_mobile_domain_matching(self):
        # English queries
        res_en = self.service._match_legal_domain("My mobile phone was stolen on the bus yesterday.")
        self.assertIsNotNone(res_en)
        self.assertEqual(res_en["id"], "stolen_mobile_phone")

        res_snatch = self.service._match_legal_domain("Someone snatched my smartphone at the railway station.")
        self.assertIsNotNone(res_snatch)
        self.assertEqual(res_snatch["id"], "stolen_mobile_phone")

        res_ceir = self.service._match_legal_domain("How do I block my phone IMEI on the CEIR portal?")
        self.assertIsNotNone(res_ceir)
        self.assertEqual(res_ceir["id"], "stolen_mobile_phone")

        # Kannada query
        res_kn = self.service._match_legal_domain("ನನ್ನ ಮೊಬೈಲ್ ಕಳ್ಳತನವಾಗಿದೆ, ದೂರು ನೀಡುವುದು ಹೇಗೆ?")
        self.assertIsNotNone(res_kn)
        self.assertEqual(res_kn["id"], "stolen_mobile_phone")

        # Hindi query
        res_hi = self.service._match_legal_domain("मेरा मोबाइल चोरी हो गया है, मुझे क्या करना चाहिए?")
        self.assertIsNotNone(res_hi)
        self.assertEqual(res_hi["id"], "stolen_mobile_phone")

    def test_stolen_mobile_statutory_provisions(self):
        domain = next((d for d in VERIFIED_LEGAL_DOMAINS if d["id"] == "stolen_mobile_phone"), None)
        self.assertIsNotNone(domain)

        applicable_laws = domain["applicable_laws"]
        acts = [law["act"] for law in applicable_laws]

        # Must include BNSS 2023, BNS 2023, and DoT CEIR Portal
        self.assertIn("Bharatiya Nagarik Suraksha Sanhita, 2023", acts)
        self.assertIn("Bharatiya Nyaya Sanhita, 2023", acts)
        self.assertTrue(any("CEIR" in act for act in acts))

        # Check BNSS 173(1) and 173(3)
        bnss_laws = [l for l in applicable_laws if l["act"] == "Bharatiya Nagarik Suraksha Sanhita, 2023"]
        all_bnss_sections = [sec for l in bnss_laws for sec in l["sections"]]
        self.assertIn("Section 173(1)", all_bnss_sections)
        self.assertIn("Section 173(3)", all_bnss_sections)

        # Check BNSS 173(1) Zero FIR principle: irrespective of territorial jurisdiction
        statute_173_1 = next(l for l in bnss_laws if "Section 173(1)" in l["sections"])
        self.assertIn("irrespective of the area", statute_173_1["english_statute"])
        self.assertIn("Zero FIR", statute_173_1["english_statute"])

        # Check BNSS 173(3) non-mandatory preliminary inquiry
        statute_173_3 = next(l for l in bnss_laws if "Section 173(3)" in l["sections"])
        self.assertIn("preliminary inquiry", statute_173_3["english_statute"].lower())
        self.assertIn("deputy superintendent of police", statute_173_3["english_statute"].lower())
        self.assertTrue(
            "not mandatory" in statute_173_3["summary"].lower() or
            "not mean that every complaint" in statute_173_3["summary"].lower()
        )

        # Check CEIR Portal requirements and scope
        ceir_law = next(l for l in applicable_laws if "CEIR" in l["act"])
        ceir_statute = ceir_law["english_statute"]
        self.assertIn("re-issued", ceir_statute.lower())
        self.assertIn("sim", ceir_statute.lower())
        self.assertIn("otp", ceir_statute.lower())
        self.assertIn("purchase invoice is optional", ceir_statute.lower())
        self.assertIn("device imei", ceir_statute.lower())
        self.assertIn("indian cellular", ceir_statute.lower())
        self.assertIn("does not render the entire physical device completely unusable", ceir_statute.lower())

    def test_stolen_mobile_remedies_accuracy(self):
        domain = next((d for d in VERIFIED_LEGAL_DOMAINS if d["id"] == "stolen_mobile_phone"), None)
        remedies_en = " ".join(domain["remedies_en"])

        # 1. BNSS 173(1) Zero FIR
        self.assertIn("BNSS Section 173(1)", remedies_en)
        self.assertIn("Zero FIR", remedies_en)
        self.assertIn("irrespective of territorial jurisdiction", remedies_en)

        # 2. BNSS 173(3) not mandatory
        self.assertIn("BNSS Section 173(3)", remedies_en)
        self.assertIn("not mandatory", remedies_en.lower())

        # 3. CEIR requirements: invoice is optional, re-issued SIM for OTP
        self.assertIn("re-issued", remedies_en.lower())
        self.assertIn("sim", remedies_en.lower())
        self.assertIn("otp", remedies_en.lower())
        self.assertIn("purchase invoice is optional", remedies_en.lower())

        # 4. CEIR scope: cellular networks, not entire device
        self.assertIn("Indian cellular mobile networks", remedies_en)
        self.assertIn("does not render the entire physical device completely unusable", remedies_en)

        # 5. e-FIR state variations
        self.assertIn("vary by state", remedies_en.lower())

        # 6. Distinguish theft allegations from lost property
        self.assertIn("allegations", remedies_en.lower())

    def test_completeness_checker_flags_missing_stolen_phone_topics(self):
        query = "My mobile phone was stolen on the way home, what legal action can I take?"

        # Incomplete response: only mentions going to local police and buying a new phone
        incomplete_response = (
            "You should go to your nearest police station and file a complaint. "
            "Then you can buy a replacement phone."
        )
        missing = GeminiClient._missing_requested_legal_topics(query, incomplete_response)
        self.assertTrue(len(missing) >= 4)
        missing_str = " ".join(missing)
        self.assertIn("BNSS Section 173(1)", missing_str)
        self.assertIn("BNSS Section 173(3)", missing_str)
        self.assertIn("CEIR requirements", missing_str)
        self.assertIn("CEIR blocking scope", missing_str)
        self.assertIn("e-FIR", missing_str)

    def test_completeness_checker_passes_complete_response(self):
        query = "My smartphone was stolen from my pocket, how do I file a complaint and block it?"
        complete_response = (
            "1. SIM and CEIR: Immediately block the lost SIM and obtain a re-issued SIM with the same number "
            "to receive the verification OTP. Visit the Department of Telecommunications CEIR portal (ceir.gov.in) "
            "to request blocking of the device IMEI across Indian mobile networks. The required documents are your "
            "police report, ID proof, and re-issued SIM for OTP. Note that the purchase invoice is optional and "
            "not mandatory. CEIR network blocking prevents use across Indian cellular networks but does not render "
            "the entire device physically unusable offline.\n"
            "2. Police Reporting and Zero FIR: Under BNSS Section 173(1), an FIR can be registered at any police "
            "station irrespective of territorial jurisdiction under the Zero FIR principle, which will then be "
            "transferred to the jurisdictional police station. Note that e-FIR availability and lost report procedures "
            "vary by state.\n"
            "3. Statutory Inquiry Procedure: For offences punishable between 3 and 7 years (such as theft under BNS "
            "Section 303(2)), an officer may conduct a preliminary inquiry under BNSS Section 173(3) with prior "
            "permission from a DSP within 14 days, but preliminary inquiry is not mandatory for all complaints and direct "
            "FIR registration may proceed.\n"
            "4. Fact Assessment: Presenting these theft allegations clearly with IMEI and location will aid police "
            "investigation to determine facts."
        )
        missing = GeminiClient._missing_requested_legal_topics(query, complete_response)
        self.assertEqual(missing, [], f"Expected all topics covered, but got: {missing}")


class EasementsBnssCpcLegalAccuracyTests(SimpleTestCase):
    """
    Focused regression tests verifying targeted legal accuracy for:
    1. Indian Easements Act, 1882, Section 13 (severance, property history, alternative route nuances, quasi-easements).
    2. Indian Easements Act, 1882, Section 15 (20/30-year period ending within 2 years before suit, Explanation II interruption vs temporary non-use).
    3. Bharatiya Nagarik Suraksha Sanhita, 2023, Section 166 (Executive Magistrate, 3-month continuous and last season/occasion conditions).
    4. CPC Order 39 Rules 1 and 2 (discretionary interim relief requiring prima facie case, balance of convenience, irreparable injury).
    """

    def setUp(self):
        self.land_domain = next(d for d in VERIFIED_LEGAL_DOMAINS if d["id"] == "land_encroachment")
        self.laws = {l["act"]: l for l in self.land_domain["applicable_laws"]}

    def test_easements_act_s13_statutory_context(self):
        s13_law = next(
            l for l in self.land_domain["applicable_laws"]
            if l["act"] == "Indian Easements Act, 1882" and "Section 13" in l["sections"]
        )
        statute_text = s13_law["english_statute"]
        summary_text = s13_law["summary"]

        # Severance through transfer, bequest or partition & property history
        self.assertIn("severance", statute_text.lower())
        self.assertIn("transfer", statute_text.lower())
        self.assertIn("partition", statute_text.lower())
        self.assertIn("bequest", statute_text.lower())
        self.assertIn("property title history", statute_text.lower())

        # Alternative route nuance: not every alternative automatically defeats necessity
        self.assertIn("cannot be used at all without the easement", statute_text)
        self.assertIn("do not assert that every alleged alternative route automatically defeats an easement of necessity", statute_text)
        self.assertIn("illusory, impassable, perilous, or legally impermissible", statute_text)

        # Distinguish necessity from quasi-easement (apparent and continuous use)
        self.assertIn("quasi-easement", statute_text.lower())
        self.assertIn("apparent, continuous, and necessary", statute_text.lower())

    def test_easements_act_s15_statutory_context(self):
        s15_law = next(
            l for l in self.land_domain["applicable_laws"]
            if l["act"] == "Indian Easements Act, 1882" and "Section 15" in l["sections"]
        )
        statute_text = s15_law["english_statute"]

        # 20 years on private land vs 30 years on Government land
        self.assertIn("20 years on private land", statute_text)
        self.assertIn("30 years where the servient heritage belongs to government", statute_text.lower())

        # Two-year period ending next before institution of suit
        self.assertIn("ending within two years next before the institution of the suit", statute_text.lower())

        # Explanation II: statutory interruption vs temporary non-use
        self.assertIn("explanation ii", statute_text.lower())
        self.assertIn("obstruction by the act of some person", statute_text.lower())
        self.assertIn("acquiescence in that obstruction for one year after the claimant has notice", statute_text.lower())
        self.assertIn("temporary non-use", statute_text.lower())
        self.assertIn("does not constitute statutory interruption", statute_text)

    def test_bnss_166_statutory_context(self):
        bnss_law = next(
            l for l in self.land_domain["applicable_laws"]
            if l["act"] == "Bharatiya Nagarik Suraksha Sanhita, 2023" and "Section 166" in l["sections"]
        )
        statute_text = bnss_law["english_statute"]

        # Executive Magistrate jurisdiction & breach of peace
        self.assertIn("executive magistrate", statute_text.lower())
        self.assertIn("breach of the peace", statute_text.lower())

        # Both year-round (3 months) and seasonal/occasional conditions
        self.assertIn("within three months next before the police report", statute_text.lower())
        self.assertIn("during the last of such seasons or occasions", statute_text.lower())

        # Interim preventive measure subject to Civil Court adjudication
        self.assertIn("interim preventive measure", statute_text.lower())
        self.assertIn("competent civil court", statute_text.lower())

    def test_cpc_order39_statutory_context(self):
        cpc_law = next(
            l for l in self.land_domain["applicable_laws"]
            if l["act"] == "Code of Civil Procedure, 1908" and "Order 39 Rule 1" in l["sections"]
        )
        statute_text = cpc_law["english_statute"]

        # Discretionary interim equitable relief, not automatic stay
        self.assertIn("discretionary equitable interim remedies", statute_text.lower())
        self.assertIn("not automatic stays", statute_text.lower())

        # All three essential conditions concurrently required
        self.assertIn("prima facie case", statute_text.lower())
        self.assertIn("balance of convenience", statute_text.lower())
        self.assertIn("irreparable injury", statute_text.lower())

    def test_remedies_accuracy_for_easements_and_injunctions(self):
        remedies_en = " ".join(self.land_domain["remedies_en"])

        # Section 13 severance and alternative route nuance
        self.assertIn("severance of tenements through transfer, bequest or partition", remedies_en)
        self.assertIn("cannot be used at all without the easement", remedies_en)
        self.assertIn("do not assume every theoretical alternative route automatically defeats necessity", remedies_en)

        # Section 15 20/30 years, two years before suit, and interruption vs temporary non-use
        self.assertIn("20 years of peaceable, open, uninterrupted user as of right (30 years for government land)", remedies_en.lower())
        self.assertIn("ending within two years immediately before institution of the suit", remedies_en.lower())
        self.assertIn("distinguish statutory interruption", remedies_en.lower())
        self.assertIn("temporary non-use", remedies_en.lower())

        # CPC Order 39 Rules 1 & 2 discretionary interim nature and 3 criteria
        self.assertIn("order 39 rules 1 and 2 cpc are discretionary equitable remedies, not automatic stays", remedies_en.lower())
        self.assertIn("prima facie case", remedies_en.lower())
        self.assertIn("balance of convenience", remedies_en.lower())
        self.assertIn("irreparable injury", remedies_en.lower())

        # BNSS Section 166 year-round 3 months and seasonal/occasional
        self.assertIn("three months before the police report/information", remedies_en.lower())
        self.assertIn("last season or occasion", remedies_en.lower())

    def test_completeness_checker_preserves_accuracy_with_nuanced_responses(self):
        query = (
            "Does Easements Act Section 13 apply to this pathway? There is another pathway across a steep cliff. "
            "Also explain prescription under Section 15 and temporary injunction under CPC Order 39."
        )
        response = (
            "1. Indian Easements Act, 1882, Section 13: Easement of necessity requires severance of tenements "
            "through transfer, bequest, or partition, and examination of prior common ownership and title history. "
            "Necessity arises when the property cannot be used at all without the easement. However, the law does "
            "not hold that every alternative route automatically defeats an easement of necessity: an impassable, "
            "illusory, or perilous route (such as a dangerous cliff) does not provide practically usable or lawful access. "
            "Distinctly, a quasi-easement requires apparent and continuous use at severance.\n"
            "2. Indian Easements Act, 1882, Section 15: Acquisition of an easement by prescription requires twenty years "
            "of peaceable and open enjoyment as of right without interruption on private land (or thirty years on government land). "
            "By statute, this period must end within two years immediately before institution of the suit. Under Explanation II, "
            "an actual statutory interruption requires cessation caused by an obstruction submitted to or acquiesced in for one year "
            "after notice; mere casual discontinuance or temporary non-use does not constitute statutory interruption.\n"
            "3. Code of Civil Procedure, 1908, Order 39 Rules 1 & 2: A temporary injunction is discretionary interim relief and "
            "not an automatic stay. The applicant must establish a prima facie case, balance of convenience, and irreparable injury."
        )
        missing = GeminiClient._missing_requested_legal_topics(query, response)
        self.assertEqual(missing, [], f"Expected all topics covered cleanly, but got warnings: {missing}")

