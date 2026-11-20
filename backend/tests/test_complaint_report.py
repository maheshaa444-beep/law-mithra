import json
import pytest
from django.contrib.auth.models import User
from documents.models import Document, DocumentPage
from analysis.models import ComplaintReport


@pytest.mark.django_db
def test_complaint_report_workflow(client):
    # 1. Create user and log in
    user = User.objects.create_user(
        username="reportuser@lawmithra.in",
        email="reportuser@lawmithra.in",
        password="TestPassword@123"
    )
    login_resp = client.post(
        "/api/auth/login/",
        data={"email": "reportuser@lawmithra.in", "password": "TestPassword@123"},
        content_type="application/json"
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access"]
    headers = {"HTTP_AUTHORIZATION": f"Bearer {token}"}

    # 2. Create document with extracted text
    doc = Document.objects.create(
        owner=user,
        title="Cybercrime_Complaint.pdf",
        file_type="application/pdf",
        file_size=20480,
        status="completed"
    )
    DocumentPage.objects.create(
        document=doc,
        page_number=1,
        extracted_text=(
            "To the Cyber Crime Police Station, Bengaluru. "
            "Subject: Complaint regarding unauthorized credit card transaction of Rs. 45,000 on 10/10/2024. "
            "Sir, I received an SMS that money was debited from my account without my OTP. "
            "Please register an FIR under Section 66C and 66D of Information Technology Act."
        )
    )

    # 3. Generate report
    gen_resp = client.post(
        f"/api/documents/{doc.id}/generate-report/",
        data={"language": "en"},
        content_type="application/json",
        **headers
    )
    assert gen_resp.status_code == 200
    rep_data = gen_resp.json()
    assert rep_data["report_id"].startswith("LM-")
    assert rep_data["version"] == 1
    assert "complaint_type" in rep_data
    assert "legal_provisions" in rep_data
    report_id = rep_data["id"]

    # 4. Fetch latest report
    latest_resp = client.get(f"/api/documents/{doc.id}/reports/latest/", **headers)
    assert latest_resp.status_code == 200
    assert latest_resp.json()["id"] == report_id

    # 5. List reports
    list_resp = client.get(f"/api/documents/{doc.id}/reports/", **headers)
    assert list_resp.status_code == 200
    assert list_resp.json()["count"] == 1

    # 6. Download PDF
    pdf_resp = client.get(f"/api/documents/{doc.id}/reports/{report_id}/pdf/", **headers)
    assert pdf_resp.status_code == 200
    assert pdf_resp["Content-Type"] == "application/pdf"
    assert pdf_resp.content.startswith(b"%PDF")
    assert len(pdf_resp.content) > 1000

    # 7. Regenerate creates version 2
    gen_resp_v2 = client.post(
        f"/api/documents/{doc.id}/generate-report/",
        data={"language": "en"},
        content_type="application/json",
        **headers
    )
    assert gen_resp_v2.status_code == 200
    assert gen_resp_v2.json()["version"] == 2

    # Check total reports count is 2
    list_resp_v2 = client.get(f"/api/documents/{doc.id}/reports/", **headers)
    assert list_resp_v2.json()["count"] == 2


def test_pdf_generator_page_budget_short():
    """Verify short case input fits strictly within 1 page."""
    import io
    import pypdf
    from analysis.services.pdf_generator import generate_pdf

    data = {
        "report_id": "LM-TEST-SHORT-01",
        "case_complaint_no": "NCR/2026/01",
        "generated_date": "19/11/2026",
        "status": "Pre-FIR Inquiry",
        "complaint_type": "Lost Property Report",
        "parties_involved": "Complainant: Ramesh Kumar",
        "incident_date_place": "19/11/2026, MG Road, Bengaluru",
        "complaint_summary": "Complainant lost his wallet containing identity documents and debit card.",
        "legal_provisions": [
            {"act_section": "Section 106, BNSS 2023", "relevance": "Non-cognizable report recording.", "caveat": "NCR only."}
        ],
        "evidence_available": ["Copy of Aadhaar card"],
        "evidence_missing": ["CCTV recording"],
        "complainant_side": "Seeks formal police acknowledgment for reissuance of identity cards.",
        "respondent_side": "No accused named.",
        "persons_role": "Complainant",
        "rights_next_steps": "Submit NCR acknowledgment to bank and UIDAI.",
        "advocate_questions": "Whether formal affidavit is required for lost card reissuance.",
        "current_stage": "NCR recorded",
        "last_updated_date": "19/11/2026",
        "version": 1,
    }
    pdf_bytes = generate_pdf(data)
    assert pdf_bytes.startswith(b"%PDF")
    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    assert len(reader.pages) == 1
    page_text = reader.pages[0].extract_text()
    assert "Page 1 of 1" in page_text
    assert "IMPORTANT ADVOCATE VERIFICATION DISCLAIMER" in page_text


def test_pdf_generator_page_budget_long():
    """Verify long case with up to 8 provisions fits in 1 to 2 pages and never exceeds 2 pages."""
    import io
    import pypdf
    from analysis.services.pdf_generator import generate_pdf

    data = {
        "report_id": "LM-TEST-LONG-02",
        "case_complaint_no": "OS/2026/9941 & Crime No. 234/2026",
        "generated_date": "19/11/2026",
        "status": "Multi-Forum Litigation Under Review",
        "complaint_type": "Commercial Breach of Contract & Criminal Misappropriation",
        "parties_involved": "Complainant: Sri Vigneshwara Infraprojects Pvt Ltd; Respondent: Deccan Urban Developers",
        "incident_date_place": "12/03/2022 at Bengaluru; Encroachments observed on 14/10/2026 at Devanahalli",
        "complaint_summary": (
            "Complainant entered into a registered Joint Development Agreement (JDA) dated 12/03/2022 "
            "with respondents for developing a 4.5-acre residential layout. Complainant paid Rs 2,50,00,000 "
            "as refundable security deposit and invested Rs 4,80,00,000 towards approvals and land development. "
            "Respondents allegedly created clandestine mortgage rights with a cooperative bank suppressing JDA."
        ),
        "legal_provisions": [
            {"act_section": f"Section {i} of Indian Penal Code / Bharatiya Nyaya Sanhita 2023",
             "relevance": f"Detailed statutory ingredients and elements of offense {i}.",
             "caveat": f"Check procedural limitations, ingredients and court jurisdiction for Section {i}."}
            for i in range(1, 9)
        ],
        "evidence_available": [
            "Registered Joint Development Agreement dated 12/03/2022",
            "Bank RTGS payment receipts totaling Rs 2,50,00,000",
            "BDA / BMRDA sanctioned development plan approval orders",
            "Encumbrance Certificate showing subsequent mortgage",
            "CCTV footage and WhatsApp audio recordings",
            "Legal demand notice dated 18/10/2026 with post receipts"
        ],
        "evidence_missing": [
            "Original bank loan sanction files",
            "Joint inspection mahazar report",
            "Certified extract of revenue mutation register",
            "Digital certificate under Section 63 BSA 2023"
        ],
        "complainant_side": "Fulfilled contractual reciprocal promises and established prima facie title violation.",
        "respondent_side": "Contends development delays breached time condition and asserts unilateral forfeiture.",
        "persons_role": "Complainant Developer & Licensee in Lawful Possession",
        "rights_next_steps": "Petition High Court under Section 9 Arbitration Act for ad-interim status quo order.",
        "advocate_questions": "Evaluate commercial suit vs Section 11 arbitration invocation given parallel criminal complaint.",
        "current_stage": "Pre-injunction urgent evidentiary compilation stage",
        "last_updated_date": "19/11/2026",
        "version": 2,
    }
    pdf_bytes = generate_pdf(data)
    assert pdf_bytes.startswith(b"%PDF")
    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    page_count = len(reader.pages)
    assert 1 <= page_count <= 2, f"Expected 1 or 2 pages, got {page_count}"
    # Verify disclaimer is always present on the last page
    last_page_text = reader.pages[-1].extract_text()
    assert "IMPORTANT ADVOCATE VERIFICATION DISCLAIMER" in last_page_text


def test_pdf_generator_multilingual_unicode():
    """Verify Indian languages (Kannada, Hindi, Tamil, Telugu) render without encoding errors."""
    import io
    import pypdf
    from analysis.services.pdf_generator import generate_pdf

    data = {
        "report_id": "LM-TEST-MULTI-03",
        "case_complaint_no": "ದೂರು ಸಂಖ್ಯೆ / शिकायत क्र. 88/2026",
        "generated_date": "19/11/2026",
        "status": "ಪರಿಶೀಲನೆಯಲ್ಲಿದೆ (Under Review)",
        "complaint_type": "ಸೈಬರ್ ವಂಚನೆ / ऑनलाइन वित्तीय धोखाधड़ी / இணைய மோசடி",
        "parties_involved": "ದೂರುದಾರ: ಆನಂದ್ ಕುಮಾರ್; ಆರೋಪಿ: ಅಜ್ಞಾತ ವ್ಯಕ್ತಿಗಳು",
        "incident_date_place": "14/11/2026, ಜಯನಗರ, ಬೆಂಗಳೂರು",
        "complaint_summary": "ದೂರುದಾರರಿಗೆ ಅಜ್ಞಾತ ವ್ಯಕ್ತಿಯಿಂದ ಬ್ಯಾಂಕ್ ಕೆವೈಸಿ ನವೀಕರಣದ ನೆಪದಲ್ಲಿ ಮೋಸದ ಕರೆ ಬಂದಿತ್ತು. ಲಿಂಕ್ ಕ್ಲಿಕ್ ಮಾಡಿದ ನಂತರ ಖಾತೆಯಿಂದ ರೂ. 50,000 ಕಡಿತಗೊಂಡಿದೆ.",
        "legal_provisions": [
            {"act_section": "ಐಟಿ ಕಾಯ್ದೆ ಕಲಂ 66D / IT Act Section 66D",
             "relevance": "ಗಣಕ ಸಂಪನ್ಮೂಲವನ್ನು ಬಳಸಿ ವಂಚನೆ ಮಾಡುವುದು.",
             "caveat": "ಸಾಕ್ಷ್ಯ ಪರಿಶೀಲನೆ ಅಗತ್ಯವಿದೆ."}
        ],
        "evidence_available": ["ಬ್ಯಾಂಕ್ ಪಾಸ್‌ಬುಕ್ ಪ್ರತಿ / Bank statement", "1930 ಸೈಬರ್ ಹೆಲ್ಪ್‌ಲೈನ್ ಸ್ವೀಕೃತಿ"],
        "evidence_missing": ["ಬ್ಯಾಂಕ್ ಸರ್ವರ್ ಲಾಗ್ ವಿವರಗಳು"],
        "complainant_side": "ಅನಧಿಕೃತ ವ್ಯವಹಾರದ ಬಗ್ಗೆ ತಕ್ಷಣ ವರದಿ ಮಾಡಲಾಗಿದೆ.",
        "respondent_side": "ಆರೋಪಿಗಳ ಗುರುತು ಇನ್ನೂ ಪತ್ತೆಯಾಗಿಲ್ಲ.",
        "persons_role": "ದೂರುದಾರ / ಸಂತ್ರಸ್ತ",
        "rights_next_steps": "1930 ಪೋರ್ಟಲ್‌ನಲ್ಲಿ ತಕ್ಷಣ ವರದಿ ಮಾಡಿ ಮತ್ತು ಸೈಬರ್ ಠಾಣೆಗೆ ತೆರಳಿ ಎನ್‌ಸಿಆರ್ ದಾಖಲಿಸಿ.",
        "advocate_questions": "ಬ್ಯಾಂಕ್‌ನಿಂದ ಹಣ ಮರುಪಾವತಿಗೆ ಆರ್‌ಬಿಐ ನಿಯಮಾವಳಿಗಳ ಅನ್ವಯ ಅರ್ಜಿ ಸಲ್ಲಿಸಬಹುದೇ ಎಂದು ಪರಿಶೀಲಿಸಿ.",
        "current_stage": "ದೂರು ದಾಖಲಾತಿ ಹಂತ",
        "last_updated_date": "19/11/2026",
        "version": 1,
    }
    pdf_bytes = generate_pdf(data)
    assert pdf_bytes.startswith(b"%PDF")
    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    assert len(reader.pages) == 1
    page_text = reader.pages[0].extract_text()
    assert "LM-TEST-MULTI-03" in page_text
    assert "IMPORTANT ADVOCATE VERIFICATION DISCLAIMER" in page_text
