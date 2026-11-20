"""
Multilingual Legal AI Reasoning Engine for Indian Law.
Implements the 7-step legal reasoning pipeline:
1. Input language detection
2. Legal query understanding & issue extraction
3. Statutory retrieval of verified Indian laws & citations
4. Factual legal analysis
5. Identification of verified legal remedies & procedural steps
6. Statutory section preservation & safeguards
7. Dual-language generation (Localized output + verified English statutory references)
"""

import re
from typing import Dict, Any, List, Optional
from .language_detector import detect_language, SUPPORTED_LANGUAGES
from .statutory_guard import StatutoryGuard
from .terminology import get_legal_term
from .bhashini_client import BhashiniClient
from .indictrans_client import IndicTransClient
from .gemini_client import GeminiClient

# Comprehensive Indian Law Knowledge Base for Core Civil & Criminal Remedies
VERIFIED_LEGAL_DOMAINS = [
    {
        'id': 'land_encroachment',
        'keywords': [
            'land', 'property', 'encroachment', 'possession', 'dispossessed', 'trespass',
            'boundary', 'site', 'plot', 'survey',
            # Kannada keywords
            'ಜಮೀನು', 'ಆಸ್ತಿ', 'ಸ್ವಾಧೀನ', 'ಅಕ್ರಮ', 'ಒತ್ತುವರಿ', 'ಕಬಳಿಕೆ', 'ಹದ್ದುಬಸ್ತು', 'ಸ್ಥಳ',
            # Hindi / Marathi keywords
            'जमीन', 'कब्जा', 'अतिक्रमण', 'संपत्ति', 'अवैध', 'मिल्कियत', 'प्लॉट',
            # Tamil / Telugu / Malayalam keywords
            'நிலம்', 'சொத்து', 'ஆக்கிரமிப்பு', 'భూమి', 'ఆస్తి', 'ఆక్రమణ', 'സ്ഥലം', 'ഭൂമി', 'കയ്യേറ്റം',
            # Bengali / Gujarati / Punjabi
            'জমি', 'দখল', 'জবরদখল', 'જમીન', 'દબાણ', 'માલિકી', 'ਜ਼ਮੀਨ', 'ਕਬਜ਼ਾ'
        ],
        'legal_issues': 'Unlawful Dispossession, Boundary Dispute, and Criminal Trespass of Immovable Property',
        'applicable_laws': [
            {
                'act': 'Indian Easements Act, 1882',
                'sections': ['Section 13'],
                'english_statute': 'Section 13: Easements of necessity and quasi-easements. Section 13 relates specifically to severance of tenements through transfer, bequest, or partition of joint immovable property and requires examination of the relevant property title history. An easement of necessity arises when, upon severance, the transferred, retained, or partitioned share cannot be used at all without the easement. While the presence of an independent, lawful, and practically usable access route negates necessity, do not assert that every alleged alternative route automatically defeats an easement of necessity: an illusory, impassable, perilous, or legally impermissible access does not automatically defeat necessity, requiring examination of the factual and legal viability of any alleged alternative. Distinctly, a quasi-easement requires that the easement was apparent, continuous, and necessary for enjoying the property as it was enjoyed when the severance took effect, subject to statutory conditions and any contrary intention.',
                'summary': 'Requires severance through transfer, bequest or partition and examination of property history; distinguish genuine necessity (where without the easement the property cannot be used at all, without assuming every theoretical alternative automatically defeats necessity) from a quasi-easement (apparent and continuous use at severance).'
            },
            {
                'act': 'Indian Easements Act, 1882',
                'sections': ['Section 15'],
                'english_statute': 'Section 15: Acquisition by prescription. A right of way or other easement becomes absolute after peaceable, open enjoyment as an easement, as of right and without interruption, for 20 years on private land (or 30 years where the servient heritage belongs to Government). By statutory mandate, each of the said periods of 20 or 30 years must be taken to be a period ending within two years next before the institution of the suit wherein the claim to which such period relates is contested. Enjoyment by permissive grant or revocable licence does not constitute enjoyment as of right. Under Explanation II, a crucial distinction exists between statutory interruption and mere temporary non-use: an interruption requires actual cessation of enjoyment caused by an obstruction by the act of some person, and submission to or acquiescence in that obstruction for one year after the claimant has notice thereof and of the person making or authorizing it. Voluntary temporary non-use or casual discontinuance of user without such obstruction and one-year acquiescence does not constitute statutory interruption.',
                'summary': 'Prescriptive easement requires 20 years (private land) or 30 years (Government land) ending within two years immediately before institution of the suit. Distinguish statutory interruption (actual cessation caused by obstruction submitted to or acquiesced in for one year after notice) from mere temporary non-use.'
            },
            {
                'act': 'Specific Relief Act, 1963',
                'sections': ['Section 38', 'Section 39'],
                'english_statute': 'Section 38 concerns perpetual injunctions to prevent breach of an obligation or invasion of property rights in the circumstances specified by the Act. Section 39 concerns mandatory injunctions: the court may, in its discretion, require acts necessary to prevent breach of an obligation. Neither provision makes an injunction or removal of a wall automatic.',
                'summary': 'Possible civil remedies include a perpetual injunction and, where legally justified, a discretionary mandatory injunction. The claimant must establish the relevant right, obligation and statutory conditions.'
            },
            {
                'act': 'Code of Civil Procedure, 1908',
                'sections': ['Order 39 Rule 1', 'Order 39 Rule 2'],
                'english_statute': 'Order 39 Rules 1 and 2: Temporary injunctions during a civil suit. Temporary injunctions are discretionary equitable interim remedies, not automatic stays or final mandatory decrees. A court grants temporary relief only upon the concurrent establishment of three essential statutory conditions: (i) Prima facie case (an arguable, triable legal case establishing a clear probability of relief); (ii) Balance of convenience (greater hardship would be caused to the applicant by withholding the injunction than to the respondent by granting it); and (iii) Irreparable injury (substantial injury that cannot be adequately compensated in monetary damages).',
                'summary': 'Discretionary interim equitable relief requiring concurrent establishment of: (i) prima facie case, (ii) balance of convenience, and (iii) irreparable injury. It is not an automatic stay or final mandatory relief.'
            },
            {
                'act': 'Bharatiya Nyaya Sanhita, 2023',
                'sections': ['Section 126'],
                'english_statute': 'Section 126: Wrongful restraint. The provision concerns voluntary obstruction that prevents a person from proceeding in a direction in which that person has a right to proceed. The statutory exception states that obstruction of a private way over land or water is not an offence where the person obstructing it in good faith believes they have a lawful right to do so.',
                'summary': 'Consider only if there is evidence of voluntary obstruction and the affected person had a legal right to proceed. Assess the good-faith private-way exception and do not infer an offence merely because a wall exists. Present both claimant arguments and opposing-party defences.'
            },
            {
                'act': 'Bharatiya Nagarik Suraksha Sanhita, 2023',
                'sections': ['Section 166'],
                'english_statute': 'Section 166: Dispute concerning right of use of land or water. Whenever an Executive Magistrate is satisfied from a police report or other information that a dispute likely to cause a breach of the peace exists concerning an alleged right of user of any land or water within local jurisdiction (whether claimed as an easement or otherwise), the Magistrate may inquire into the matter. Threshold statutory conditions: (i) If the right is exercisable at all times of the year, no order shall be made unless the right was exercised within three months next before the police report or information was received; (ii) If the right is exercisable only at particular seasons or occasions, no order shall be made unless the right was exercised during the last of such seasons or occasions next before such report or information was received. Any order passed is an interim preventive measure forbidding interference or directing removal of obstruction pending final adjudication of rights by a competent Civil Court.',
                'summary': 'Conditional Executive Magistrate preventive jurisdiction for land/water right-of-use disputes likely to cause breach of peace. Requires proof of exercise within 3 months next before report/info (for year-round rights) or during the last season or occasion (for seasonal/occasional rights). It is an interim measure, not a final determination of ownership or title.'
            },
            {
                'act': 'Specific Relief Act, 1963',
                'sections': ['Section 6'],
                'english_statute': 'Section 6 provides a summary suit for recovery of possession where a person has been dispossessed of immovable property without consent and otherwise than in due course of law. The suit must be brought within six months of dispossession, subject to the statutory conditions. Mere obstruction of a pathway does not by itself establish dispossession for this section.',
                'summary': 'Consider only if the facts establish actual qualifying dispossession from immovable property and the six-month statutory period and other requirements are met.'
            }
        ],
        'remedies_en': [
            '1. Collect title deeds, prior sale, partition or bequest documents, survey records, village maps, tax records, photographs and reliable evidence showing the pathway, its location and property history.',
            '2. Under Section 13 of the Indian Easements Act, examine severance of tenements through transfer, bequest or partition. An easement of necessity requires that the property cannot be used at all without the easement, but do not assume every theoretical alternative route automatically defeats necessity (illusory, perilous, impassable, or legally impermissible access does not defeat necessity); for a quasi-easement, verify apparent and continuous use at severance.',
            '3. Under Section 15 of the Indian Easements Act, establish 20 years of peaceable, open, uninterrupted user as of right (30 years for Government land) ending within two years immediately before institution of the suit. Distinguish statutory interruption (actual obstruction submitted to or acquiesced in for one year after notice) from mere temporary non-use.',
            '4. In a civil suit, temporary injunctions under Order 39 Rules 1 and 2 CPC are discretionary equitable remedies, not automatic stays; they require concurrent proof of a prima facie case, balance of convenience, and irreparable injury.',
            '5. Under BNSS Section 166, an Executive Magistrate may act if a right-of-use dispute threatens breach of peace, provided the right was exercised within three months before the police report/information (for year-round rights) or during the last season or occasion (for seasonal/occasional rights); it provides interim preventive relief subject to Civil Court adjudication.',
            '6. Consider BNS Section 126 only if the evidence supports voluntary obstruction of a person who has a legal right to proceed, after assessing the statutory good-faith private-way exception.',
            '7. Do not assume that Section 6 of the Specific Relief Act applies unless there was actual qualifying dispossession. Have an advocate assess the correct remedy, limitation and forum before filing.'
        ],
        'remedies_kn': [
            '೧. ಅಕ್ರಮವಾಗಿ ಸ್ವಾಧೀನ ಕಳೆದುಕೊಂಡ ೬ ತಿಂಗಳ ಒಳಗೆ ನಿರ್ದಿಷ್ಟ ಪರಿಹಾರ ಕಾಯ್ದೆ ೧೯೬೩ ರ ಕಲಂ ೬ (Section 6 of Specific Relief Act) ರ ಅಡಿಯಲ್ಲಿ ಸ್ವಾಧೀನ ವಾಪಸಾತಿಗಾಗಿ ಸಿವಿಲ್ ದಾವೆ ಹೂಡಿರಿ.',
            '೨. ಸಿವಿಲ್ ಪ್ರಕ್ರಿಯಾ ಸಂಹಿತೆ (CPC) ಯ ಆರ್ಡರ್ ೩೯ ರೂಲ್ ೧ ಮತ್ತು ೨ ರ ಅಡಿಯಲ್ಲಿ ಪ್ರಥಮ ದೃಷ್ಟಿ ಬಲವಾದ ಪ್ರಕರಣ, ಅನುಕೂಲತೆಯ ಸಮತೋಲನ ಮತ್ತು ಪರಿಹರಿಸಲಾಗದ ನಷ್ಟದ ಆಧಾರದಲ್ಲಿ ಮಧ್ಯಂತರ ತಡೆಯಾಜ್ಞೆ (Temporary Injunction) ಕೋರಿ ತುರ್ತು ಅರ್ಜಿ ಸಲ್ಲಿಸಿರಿ.',
            '೩. ವ್ಯಾಪ್ತಿಯ ಪೊಲೀಸ್ ಠಾಣೆಯಲ್ಲಿ ಅಕ್ರಮ ಪ್ರವೇಶದ ಕುರಿತು ಕಲಂ ೪೪೧ ಮತ್ತು ೪೪೭ ಐಪಿಸಿ (ಕಲಂ ೩೨೯ ಬಿಎನ್‌ಎಸ್) ಅಡಿಯಲ್ಲಿ ಲಿಖಿತ ದೂರು ಸಲ್ಲಿಸಿ ಸ್ವೀಕೃತಿ (Acknowledgment / FIR) ಪಡೆದುಕೊಳ್ಳಿರಿ.',
            '೪. ಶಾಂತಿಭಂಗ ತಡೆಯಲು ಹಾಗೂ ಕಂದಾಯ ಇಲಾಖೆಯ ಸರ್ವೆ ನಡೆಸಲು ಕಲಂ ೧೪೫ ಸಿಆರ್‌ಪಿಸಿ (ಕಲಂ ೧೬೪ ಬಿಎನ್‌ಎಸ್‌ಎಸ್) ಅಡಿಯಲ್ಲಿ ತಹಶೀಲ್ದಾರ್ / ಉಪವಿಭಾಗಾಧಿಕಾರಿಯವರಿಗೆ ಅರ್ಜಿ ಸಲ್ಲಿಸಿರಿ.',
            '೫. ದಾರಿ ಅಥವಾ ನೀರಿನ ಬಳಕೆಯ ಹಕ್ಕಿನ ವಿವಾದ ಹಾಗೂ ಶಾಂತಿಭಂಗದ ಸಂದರ್ಭದಲ್ಲಿ, ಕಲಂ ೧೬೬ ಬಿಎನ್‌ಎಸ್‌ಎಸ್ (ಕಲಂ ೧೪೭ ಸಿಆರ್‌ಪಿಸಿ) ಅಡಿಯಲ್ಲಿ ೩ ತಿಂಗಳ ಬಳಕೆಯ (ಅಥವಾ ಹಂಗಾಮಿ ಹಕ್ಕಿಗೆ ಕೊನೆಯ ಸಂದರ್ಭದ) ಶಾಸನಬದ್ಧ ಷರತ್ತನ್ನು ಗಮನಿಸಿ ಕಾರ್ಯನಿರ್ವಾಹಕ ಮ್ಯಾಜಿಸ್ಟ್ರೇಟ್‌ರಿಗೆ ಅರ್ಜಿ ಸಲ್ಲಿಸಿರಿ.'
        ],
        'remedies_hi': [
            '१. कब्जा छीने जाने के ६ महीने के भीतर विनिर्दिष्ट अनुतोष अधिनियम, १९६३ की धारा ६ (Section 6 of Specific Relief Act) के तहत कब्जा वापसी का दीवानी वाद (Civil Suit) दायर करें।',
            '२. सीपीसी (CPC) के आदेश ३९ नियम १ एवं २ के तहत प्रथम दृष्टया वाद, सुविधा संतुलन और अपूरणीय क्षति के आधार पर अंतरिम व्यादेश / स्थगन (Temporary Injunction) प्राप्त करने का आवेदन दें।',
            '३. संबंधित थाने में आपराधिक अतिचार (Criminal Trespass) हेतु धारा ४४१/४४७ आईपीसी (धारा ३२৯ बीएनएस) के तहत प्राथमिकी (FIR) दर्ज कराएं।',
            '४. शांतिभंग रोकने और राजस्व सीमांकन के लिए धारा १४५ सीआरपीसी (धारा १६४ बीएनएसएस) के तहत एसडीएम / तहसीलदार के समक्ष प्रार्थना पत्र प्रस्तुत करें।',
            '५. रास्ते या जल प्रयोग के अधिकार संबंधी विवाद एवं शांतिभंग की आशंका होने पर, धारा १६६ बीएनएसएस (धारा १४७ सीआरपीसी) के तहत ३ माह की अनिवार्य शर्त (या मौसमी अधिकार हेतु अंतिम अवसर) की जांच कर कार्यपालक मजिस्ट्रेट के समक्ष आवेदन प्रस्तुत करें।'
        ],
        'remedies_ta': [
            '1. உடைமை பறிக்கப்பட்ட 6 மாதங்களுக்குள் குறிப்பிட்ட நிவாரணச் சட்டம் 1963 பிரிவு 6 (Section 6 Specific Relief Act) கீழ் உரிமையியல் வழக்கு (Civil Suit) தாக்கல் செய்யுங்கள்.',
            '2. சிபிசி (CPC) உத்தரவு 39 விதி 1 மற்றும் 2 கீழ் உடனடி தடையுத்தரவு (Injunction) பெற மனு தாக்கல் செய்யவும்.',
            '3. எல்லை மீறல் மற்றும் அத்துமீறலுக்கு எதிராக பிரிவு 441/447 IPC (பிரிவு 329 BNS) கீழ் காவல் நிலையத்தில் எழுத்துப்பூர்வ புகார் (FIR) அளியுங்கள்.',
            '4. அமைதிக்கு பங்கம் ஏற்படாமல் தடுக்க பிரிவு 145 CrPC (பிரிவு 164 BNSS) கீழ் வருவாய் கோட்டாட்சியர் / வட்டாட்சியரிடம் மனு அளியுங்கள்.',
            '5. பாதை அல்லது நீர் பயன்பாட்டு உரிமை தகராறு மற்றும் அமைதிக்கு பங்கம் ஏற்படும் சூழலில், பிரிவு 166 BNSS (பிரிவு 147 CrPC) கீழ் 3 மாத பயன்பாட்டு நிபந்தனையை பரிசீலித்து நிர்வாக நடுவரிடம் மனு அளியுங்கள்.'
        ],
        'remedies_te': [
            '1. ఆక్రమణ జరిగిన 6 నెలల లోపు స్పెసిఫిక్ రిలీఫ్ యాక్ట్, 1963 సెక్షన్ 6 (Section 6 SRA) కింద స్వాధీనం రికవరీ కోసం సివిల్ దావా వేయండి.',
            '2. సీపీసీ (CPC) ఆర్డర్ 39 రూల్ 1 & 2 కింద తక్షణ స్టే ఆర్డర్ / నిషేధాజ్ఞ (Temporary Injunction) కోసం దరఖాస్తు చేయండి.',
            '3. అక్రమ ప్రవేశంపై సెక్షన్ 441/447 ఐపీసీ (సెక్షన్ 329 BNS) కింద పోలీసులకు లిఖితపూర్వక ఫిర్యాదు (FIR) సమర్పించండి.',
            '4. శాంతిభద్రతల పరిరక్షణ మరియు సర్వే కోసం సెక్షన్ 145 CrPC (సెక్షన్ 164 BNSS) కింద ఎగ్జిక్యూటివ్ మేజిస్ట్రేట్ / తహశీల్దార్‌కు దరఖాస్తు చేయండి.',
            '5. దారి లేదా నీటి వినియోగ హక్కు వివాదం మరియు శాంతిభద్రతల సమస్య ఉన్నప్పుడు, సెక్షన్ 166 BNSS (సెక్షన్ 147 CrPC) కింద 3 నెలల వినియోగ నిబంధనను పరిశీలించి ఎగ్జిక్యూటివ్ మేజిస్ట్రేట్‌కు దరఖాస్తు చేయండి.'
        ],
    },
    {
        'id': 'cheque_bounce',
        'keywords': [
            'cheque', 'check', 'bounce', 'dishonour', 'insufficient', 'bank',
            'ಚೆಕ್', 'ಬೌನ್ಸ್', 'ಅಮಾನ್ಯ', 'ಬ್ಯಾಂಕ್', 'ಹಣ',
            'चेक', 'बाउंस', 'अनादर', 'खाता',
            'காசோலை', 'செக்', 'பவுன்ஸ்', 'చెక్', 'బౌన్స్', 'చెల్లక'
        ],
        'legal_issues': 'Dishonour of Cheque for Insufficiency of Funds in Bank Account',
        'applicable_laws': [
            {
                'act': 'Negotiable Instruments Act, 1881',
                'sections': ['Section 138', 'Section 141', 'Section 142'],
                'english_statute': 'Section 138 of the Negotiable Instruments Act, 1881: Dishonour of cheque for insufficiency, etc., of funds in the account is an offence punishable with imprisonment for a term up to 2 years, or with fine which may extend to twice the amount of the cheque, or with both.',
                'summary': 'Statutory 30-day legal demand notice followed by criminal complaint under Section 138 NI Act within 30 days.'
            }
        ],
        'remedies_en': [
            '1. Issue a formal Statutory Legal Demand Notice in writing within 30 days of receiving the cheque return memo from the bank.',
            '2. Provide the drawer a strict statutory window of 15 days from receipt of notice to make payment.',
            '3. If payment is not cleared within 15 days, file a Criminal Complaint under Section 138 of the Negotiable Instruments Act, 1881 before the Judicial Magistrate within 30 days thereafter.',
            '4. Seek interim compensation up to 20% of the cheque amount under Section 143A of the NI Act.'
        ],
        'remedies_kn': [
            '೧. ಬ್ಯಾಂಕಿನಿಂದ ಚೆಕ್ ರಿಟರ್ನ್ ಮೆಮೊ ಬಂದ ದಿನಾಂಕದಿಂದ ೩೦ ದಿನಗಳ ಒಳಗೆ ವಕೀಲರ ಮೂಲಕ ಶಾಸನಬದ್ಧ ಡಿಮಾಂಡ್ ನೋಟಿಸ್ (Legal Notice under Section 138 NI Act) ಕಳುಹಿಸಿರಿ.',
            '೨. ನೋಟಿಸ್ ತಲುಪಿದ ದಿನದಿಂದ ಹಣ ಪಾವತಿಸಲು ೧೫ ದಿನಗಳ ಕಡ್ಡಾಯ ಕಾಲಾವಕಾಶ ನೀಡಿರಿ.',
            '೩. ಆ ೧೫ ದಿನಗಳಲ್ಲಿ ಹಣ ಪಾವತಿಸದಿದ್ದರೆ, ಮುಂದಿನ ೩೦ ದಿನಗಳ ಒಳಗೆ ಪ್ರಥಮ ದರ್ಜೆ ನ್ಯಾಯಾಂಗ ಮ್ಯಾಜಿಸ್ಟ್ರೇಟ್ (JMFC) ನ್ಯಾಯಾಲಯದಲ್ಲಿ ಕ್ರಿಮಿನಲ್ ದೂರು ದಾಖಲಿಸಿರಿ.',
            '೪. ಕಲಂ ೧೪೩ಎ ಎನ್‌ಐ ಕಾಯ್ದೆ (Section 143A NI Act) ಅಡಿಯಲ್ಲಿ ಶೇಕಡಾ ೨೦ ರಷ್ಟು ಮಧ್ಯಂತರ ಪರಿಹಾರವನ್ನು ನ್ಯಾಯಾಲಯದಿಂದ ಕೋರಬಹುದು.'
        ],
        'remedies_hi': [
            '१. बैंक से चेक अनादर मेमो (Cheque Return Memo) मिलने के ३० दिनों के भीतर लिखित में वैधानिक मांग नोटिस (Statutory Notice under Section 138) भेजें।',
            '२. नोटिस प्राप्त होने के बाद देनदार को भुगतान के लिए १५ दिन का समय दें।',
            '३. यदि १५ दिनों में भुगतान नहीं होता है, तो अगले ३० दिनों के भीतर न्यायिक मजिस्ट्रेट की अदालत में परक्राम्य लिखत अधिनियम की धारा १३८ (Section 138 NI Act) के तहत परिवाद दाखिल करें।',
            '४. धारा १४३ए (Section 143A) के तहत चेक राशि का २०% तक अंतरिम मुआवजा देने की मांग करें।'
        ],
        'remedies_ta': [
            '1. காசோலை திரும்பப் பெறப்பட்ட குறிப்பு கிடைத்த 30 நாட்களுக்குள் சட்டப்பூர்வ அறிவிப்பு (Section 138 Legal Notice) அனுப்பவும்.',
            '2. அறிவிப்பைப் பெற்ற நாளிலிருந்து தொகையை செலுத்த 15 நாட்கள் கால அவகாசம் வழங்கவும்.',
            '3. 15 நாட்களுக்குள் பணம் செலுத்தப்படாவிட்டால், அடுத்த 30 நாட்களுக்குள் நீதித்துறை நடுவர் நீதிமன்றத்தில் பிரிவு 138 கீழ் புகார் தாக்கல் செய்யவும்.',
            '4. பிரிவு 143A கீழ் காசோலை தொகையில் 20% வரை இடைக்கால இழப்பீடு கோரலாம்.'
        ],
        'remedies_te': [
            '1. బ్యాంకు రిటర్న్ మెమో అందిన 30 రోజుల్లోగా చట్టబద్ధమైన లీగల్ నోటీసు (Section 138 NI Act) జారీ చేయండి.',
            '2. నోటీసు అందిన నాటి నుంచి సొమ్ము చెల్లించడానికి 15 రోజుల సమయం ఇవ్వండి.',
            '3. 15 రోజుల్లో చెల్లించకపోతే, ఆ తర్వాత 30 రోజుల్లో మేజిస్ట్రేట్ కోర్టులో క్రిమినల్ ఫిర్యాదు దాఖలు చేయండి.',
            '4. సెక్షన్ 143A కింద చెక్ మొత్తంలో 20% మధ్యంతర నష్టపరిహారం కోరవచ్చు.'
        ]
    },
    {
        'id': 'stolen_mobile_phone',
        'keywords': [
            'stolen phone', 'mobile theft', 'lost mobile', 'phone stolen', 'mobile snatched',
            'snatching', 'imei', 'ceir', 'zero fir', 'e-fir',
            # Kannada
            'ಮೊಬೈಲ್ ಕಳ್ಳತನ', 'ಫೋನ್ ಕಳವು', 'ಮೊಬೈಲ್ ಕಳೆದುಹೋಗಿದೆ', 'ಸ್ನ್ಯಾಚಿಂಗ್',
            # Hindi
            'मोबाइल चोरी', 'फोन चोरी', 'मोबाइल खो गया', 'फोन झपटमारी',
            # Tamil / Telugu / Malayalam
            'மொபைல் திருட்டு', 'போன் திருட்டு', 'ఫోన్ దొంగతనం', 'మొబైల్ చోరీ', 'ഫോൺ മോഷണം',
            # Marathi / Bengali / Gujarati / Punjabi
            'मोबाईल चोरी', 'ফোন চুরি', 'ફોન ચોરી', 'ਮੋਬਾਈਲ ਚੋਰੀ'
        ],
        'legal_issues': 'Allegation of Theft or Loss of Mobile Phone Device and Statutory Reporting Procedures',
        'applicable_laws': [
            {
                'act': 'Bharatiya Nagarik Suraksha Sanhita, 2023',
                'sections': ['Section 173(1)'],
                'english_statute': 'Section 173(1) of BNSS provides that every information relating to the commission of a cognizable offence may be given to an officer in charge of a police station irrespective of the area where the offence was committed (Zero FIR principle). Information may be given orally or electronically (e-FIR, subject to state procedure and signing within three days).',
                'summary': 'Information regarding a cognizable offence (such as mobile phone theft) can be reported at any police station irrespective of territorial jurisdiction under the Zero FIR principle. The receiving station registers the Zero FIR and transfers it to the jurisdictional police station.'
            },
            {
                'act': 'Bharatiya Nagarik Suraksha Sanhita, 2023',
                'sections': ['Section 173(3)'],
                'english_statute': 'Section 173(3) of BNSS provides that on receipt of information relating to commission of a cognizable offence punishable with imprisonment for three years or more but less than seven years, the police officer may, with prior permission of an officer not below the rank of Deputy Superintendent of Police, conduct a preliminary inquiry within fourteen days to ascertain whether a prima facie case exists, or proceed directly to investigate.',
                'summary': 'Section 173(3) is an enabling discretionary provision for offences punishable between 3 and 7 years. It does NOT mean that every complaint or FIR must undergo preliminary inquiry; direct registration and investigation can proceed.'
            },
            {
                'act': 'Bharatiya Nyaya Sanhita, 2023',
                'sections': ['Section 303(2)', 'Section 304'],
                'english_statute': 'Section 303(2) of BNS penalizes theft (dishonest taking of movable property out of possession without consent). Section 304 of BNS penalizes snatching (theft committed by sudden or quick grabbing, seizing, or snatching).',
                'summary': 'Theft of a mobile phone constitutes an offence under BNS Section 303(2) (or Section 304 if committed by sudden snatching). Allegations must be factually verified and distinguished from mere accidental misplacement or loss.'
            },
            {
                'act': 'Department of Telecommunications (DoT) — Central Equipment Identity Register (CEIR)',
                'sections': ['CEIR Device IMEI Blocking Portal (ceir.gov.in)'],
                'english_statute': 'CEIR is an official citizen portal (ceir.gov.in) administered by the Department of Telecommunications (DoT) to block lost or stolen mobile devices across all Indian Telecom Service Providers (TSPs). Required submissions: (i) Police complaint / FIR / Lost report acknowledgement, (ii) Re-issued duplicate active SIM card on the same number to receive the verification OTP, (iii) Identity proof, and (iv) 15-digit IMEI number(s) where available. Crucially, the purchase invoice is OPTIONAL. Blocking disables the device IMEI across Indian cellular mobile networks (voice, SMS, data), but does NOT render the entire physical device completely unusable (offline applications or Wi-Fi can still physically function).',
                'summary': 'CEIR blocks the device IMEI from Indian mobile networks and generates network tracing alerts. Requirements: police report/FIR, re-issued active SIM to receive OTP, ID proof, and IMEI where available. Purchase invoice is optional. e-FIR availability and procedure vary by state.'
            }
        ],
        'remedies_en': [
            '1. Immediately contact your telecom service provider to deactivate the stolen SIM card and obtain a re-issued duplicate SIM card on the same number (essential to receive verification OTPs for CEIR blocking).',
            '2. Report the incident promptly to the police. State facts objectively, distinguishing theft allegations from lost property reports without presenting unverified allegations as established facts. Under BNSS Section 173(1), information about a cognizable offence can be given at any police station irrespective of territorial jurisdiction (Zero FIR principle), which will be registered and transferred to the jurisdictional police station.',
            '3. Check your state police citizen portal: e-FIR and online lost mobile reporting availability and procedures vary by state (some states provide specialized lost article portals or e-FIR where the accused is unknown).',
            '4. Note on procedure: Under BNSS Section 173(3), preliminary inquiry is an enabling option requiring DSP approval for offences punishable between 3 and 7 years; it is not mandatory for every complaint, and direct FIR registration can proceed.',
            '5. Submit an IMEI blocking request on the official CEIR portal (ceir.gov.in). Required details: (i) Police complaint/FIR acknowledgement, (ii) Re-issued active SIM to receive OTP, (iii) Identity proof, and (iv) 15-digit IMEI number(s) where available. The purchase invoice is optional.',
            '6. Note on CEIR blocking scope: CEIR blocks the IMEI from accessing Indian cellular mobile networks (voice, SMS, data) and alerts law enforcement if a new SIM is inserted. It does not render the entire physical device completely unusable (e.g. offline use or Wi-Fi remains physically possible on the hardware).',
            '7. Change passwords and log out of linked Google/Apple accounts, email, social media, and UPI/banking applications from another trusted device.'
        ],
        'remedies_kn': [
            '೧. ತಕ್ಷಣವೇ ನಿಮ್ಮ ಮೊಬೈಲ್ ಸೇವಾ ಪೂರೈಕೆದಾರರನ್ನು (ಟೆಲಿಕಾಂ) ಸಂಪರ್ಕಿಸಿ ಕಳವಾದ ಸಿಮ್ ಕಾರ್ಡ್ ನಿರ್ಬಂಧಿಸಿ (Block) ಮತ್ತು ಅದೇ ನಂಬರಿನ ಮರು-ವಿತರಿಸಿದ ಸಿಮ್ (Duplicate SIM) ಪಡೆದುಕೊಳ್ಳಿರಿ (CEIR ಒಟಿಪಿ ಪಡೆಯಲು ಇದು ಕಡ್ಡಾಯ).',
            '೨. ಬಿಎನ್‌ಎಸ್‌ಎಸ್ ಕಲಂ ೧೭೩(೧) (Section 173(1) BNSS) ರ ಅಡಿಯಲ್ಲಿ ಅಪರಾಧ ನಡೆದ ಸ್ಥಳದ ವ್ಯಾಪ್ತಿಯ ಪರಿಮಿತಿಯಿಲ್ಲದೆ ಯಾವುದೇ ಪೊಲೀಸ್ ಠಾಣೆಯಲ್ಲಿ ದೂರು ನೀಡಬಹುದು (ಝೀರೋ ಎಫ್‌ಐಆರ್ / Zero FIR ತತ್ವ).',
            '೩. ನಿಮ್ಮ ರಾಜ್ಯ ಪೊಲೀಸ್ ಪೋರ್ಟಲ್ ಪರಿಶೀಲಿಸಿ: ಇ-ಎಫ್‌ಐಆರ್ (e-FIR) ಮತ್ತು ಮೊಬೈಲ್ ಕಳೆದುಹೋದ ವರದಿ ಸೌಲಭ್ಯ ಮತ್ತು ಪ್ರಕ್ರಿಯೆಗಳು ರಾಜ್ಯದಿಂದ ರಾಜ್ಯಕ್ಕೆ ಬದಲಾಗುತ್ತವೆ (ಉದಾ: ಕರ್ನಾಟಕದಲ್ಲಿ KSP ಆ್ಯಪ್ e-Lost Report).',
            '೪. ಬಿಎನ್‌ಎಸ್‌ಎಸ್ ಕಲಂ ೧೭೩(೩) ರ ಅಡಿಯಲ್ಲಿ ೩ ರಿಂದ ೭ ವರ್ಷ ಶಿಕ್ಷೆಯಾಗುವ ಅಪರಾಧಗಳಿಗೆ ಡಿಎಸ್‌ಪಿ ಅನುಮತಿಯೊಂದಿಗೆ ಪ್ರಾಥಮಿಕ ತನಿಖೆ ಐಚ್ಛಿಕ ಅವಕಾಶವಾಗಿದೆ; ಪ್ರತಿಯೊಂದು ದೂರಿಗೂ ಪ್ರಾಥಮಿಕ ತನಿಖೆ ಕಡ್ಡಾಯವಲ್ಲ, ನೇರ ಎಫ್‌ಐಆರ್ ದಾಖಲಿಸಿ ತನಿಖೆ ಕೈಗೊಳ್ಳಬಹುದು.',
            '೫. ಅಧಿಕೃತ CEIR ಪೋರ್ಟಲ್‌ನಲ್ಲಿ (ceir.gov.in) ಐಎಂಇಐ (IMEI) ನಿರ್ಬಂಧಿಸಲು ಅರ್ಜಿ ಸಲ್ಲಿಸಿ. ಅಗತ್ಯ ದಾಖಲೆಗಳು: (i) ಪೊಲೀಸ್ ದೂರು / ಎಫ್‌ಐಆರ್ ಸ್ವೀಕೃತಿ, (ii) ಒಟಿಪಿ ಸ್ವೀಕರಿಸಲು ಸಕ್ರಿಯ ಮರು-ವಿತರಿಸಿದ ಸಿಮ್, (iii) ಗುರುತಿನ ಚೀಟಿ, ಮತ್ತು (iv) ಲಭ್ಯವಿದ್ದಲ್ಲಿ IMEI ಸಂಖ್ಯೆ. ಖರೀದಿಯ ರಶೀದಿ (Purchase Invoice) ಐಚ್ಛಿಕವಾಗಿರುತ್ತದೆ (Optional).',
            '೬. CEIR ನಿರ್ಬಂಧದ ವ್ಯಾಪ್ತಿ: CEIR ಸಾಧನದ IMEI ಅನ್ನು ಭಾರತೀಯ ಮೊಬೈಲ್ ನೆಟ್‌ವರ್ಕ್‌ಗಳಲ್ಲಿ (ಕರೆ, ಎಸ್‌ಎಂಎಸ್, ಡೇಟಾ) ಮಾತ್ರ ನಿರ್ಬಂಧಿಸುತ್ತದೆ; ಇದು ಇಡೀ ಮೊಬೈಲ್ ಸಾಧನವನ್ನು ಸಂಪೂರ್ಣವಾಗಿ ನಿಷ್ಕ್ರಿಯಗೊಳಿಸುವುದಿಲ್ಲ (ವೈ-ಫೈ ಅಥವಾ ಆಫ್‌ಲೈನ್ ಬಳಕೆ ಸಾಧ್ಯವಿರಬಹುದು).',
            '೭. ಬ್ಯಾಂಕಿಂಗ್, ಯುಪಿಐ, ಇಮೇಲ್ ಮತ್ತು ಸಾಮಾಜಿಕ ಮಾಧ್ಯಮಗಳ ಪಾಸ್‌ವರ್ಡ್‌ಗಳನ್ನು ತಕ್ಷಣ ಬದಲಾಯಿಸಿ ಬೇರೆ ಸಾಧನದಿಂದ ಲಾಗ್‌ಔಟ್ ಮಾಡಿರಿ.'
        ],
        'remedies_hi': [
            '१. तुरंत अपने टेलीकॉम ऑपरेटर से संपर्क कर चोरी हुआ सिम ब्लॉक कराएं और उसी नंबर का पुनः जारी (Duplicate) सिम प्राप्त करें (CEIR सत्यापन ओटीपी प्राप्त करने हेतु यह अनिवार्य है)।',
            '२. बीएनएसएस की धारा १७३(१) (Section 173(1) BNSS) के तहत किसी भी संज्ञेय अपराध की सूचना क्षेत्राधिकार की परवाह किए बिना किसी भी थाने में दी जा सकती है (जीरो एफआईआर / Zero FIR का सिद्धांत)।',
            '३. अपने राज्य के पुलिस पोर्टल की जांच करें: ई-एफआईआर (e-FIR) और गुमशुदगी रिपोर्ट की उपलब्धता एवं प्रक्रिया अलग-अलग राज्यों में भिन्न होती है।',
            '४. प्रक्रिया स्पष्टीकरण: बीएनएसएस की धारा १७३(३) के तहत ३ से ७ वर्ष तक दंडनीय अपराधों में डीएसपी की अनुमति से प्रारंभिक जांच एक वैकल्पिक व सशर्त प्रावधान है; प्रत्येक शिकायत की प्रारंभिक जांच होना अनिवार्य नहीं है, सीधे एफआईआर दर्ज कर जांच हो सकती है।',
            '५. दूरसंचार विभाग के CEIR पोर्टल (ceir.gov.in) पर फोन ब्लॉक करने हेतु आवेदन करें। आवश्यक दस्तावेज: (i) पुलिस शिकायत/एफआईआर रसीद, (ii) ओटीपी हेतु पुनः जारी सक्रिय सिम, (iii) पहचान प्रमाण पत्र, एवं (iv) उपलब्ध होने पर IMEI नंबर। खरीद रसीद (Purchase Invoice) वैकल्पिक (Optional) है।',
            '६. CEIR ब्लॉकिंग का प्रभाव: CEIR डिवाइस के IMEI को भारतीय सेल्युलर नेटवर्क से ब्लॉक करता है; यह पूरे डिवाइस को पूरी तरह से अनुपयोगी नहीं बनाता (वाई-फाई या ऑफलाइन कार्य अभी भी संभव हो सकता है)।',
            '७. अन्य सुरक्षित डिवाइस से अपने बैंक खाते, यूपीआई, ईमेल और सोशल मीडिया खातों के पासवर्ड तुरंत बदलें और रिमोट लॉगआउट करें।'
        ],
        'remedies_ta': [
            '1. தொலைந்த சிம் கார்டை உடனடியாக முடக்கி, அதே எண்ணில் புதிய மாற்று சிம் கார்டைப் பெறுங்கள் (CEIR OTP பெற இது அவசியம்).',
            '2. BNSS பிரிவு 173(1) கீழ் அதிகார எல்லை வரம்பின்றி எந்தவொரு காவல் நிலையத்திலும் புகார் அளிக்கலாம் (ஜீரோ எஃப்.ஐ.ஆர் / Zero FIR தத்துவம்).',
            '3. இ-எஃப்ஐஆர் (e-FIR) மற்றும் தொலைந்த மொபைல் புகார் நடைமுறைகள் மாநிலத்திற்கு மாநிலம் மாறுபடும்.',
            '4. BNSS பிரிவு 173(3) கீழ் 3 முதல் 7 ஆண்டுகள் வரை தண்டனைக்குரிய குற்றங்களில் டிஎஸ்பி அனுமதியுடன் பூர்வாங்க விசாரணை ஒரு நிபந்தனைக்குட்பட்ட நடைமுறையாகும்; ஒவ்வொரு புகாருக்கும் பூர்வாங்க விசாரணை கட்டாயமில்லை, நேரடியாக எஃப்ஐஆர் பதிவு செய்யப்படலாம்.',
            '5. அதிகாரப்பூர்வ CEIR இணையதளத்தில் (ceir.gov.in) ஐஎம்இஐ முடக்க விண்ணப்பிக்கவும். தேவையானவை: (i) காவல் புகார்/எஃப்ஐஆர் ரசீது, (ii) OTP பெற புதிய மாற்று சிம், (iii) அடையாளச் சான்று, மற்றும் (iv) IMEI எண். பில் (Purchase Invoice) விருப்பத்தேர்வாகும் (Optional).',
            '6. CEIR முடக்கம் இந்திய செல்லுலார் மொபைல் நெட்வொர்க்குகளில் மட்டுமே சாதனத்தை முடக்குகிறது; முழு சாதனத்தையும் முற்றிலும் பயன்படுத்த முடியாததாக மாற்றிவிடாது.',
            '7. வங்கி, யுபிஐ, ஜிமெயில் கணக்குகளின் கடவுச்சொற்களை உடனடியாக மாற்றவும்.'
        ],
        'remedies_te': [
            '1. పోయిన సిమ్ కార్డును వెంటనే బ్లాక్ చేసి, అదే నంబర్‌పై రీ-ఇష్యూడ్ డూప్లికేట్ సిమ్ పొందండి (CEIR OTP కోసం ఇది అవసరం).',
            '2. BNSS సెక్షన్ 173(1) కింద పరిధి పరిమితి లేకుండా ఏ పోలీస్ స్టేషన్‌లోనైనా ఫిర్యాదు చేయవచ్చు (జీరో ఎఫ్ఐఆర్ / Zero FIR సూత్రం).',
            '3. ఈ-ఎఫ్ఐఆర్ (e-FIR) మరియు పోగొట్టుకున్న మొబైల్ రిపోర్టింగ్ విధానాలు రాష్ట్రాల వారీగా మారుతూ ఉంటాయి.',
            '4. BNSS సెక్షన్ 173(3) కింద 3 నుండి 7 సంవత్సరాల శిక్ష పడే నేరాలలో డీఎస్పీ అనుమతితో ప్రాథమిక విచారణ అనేది ఒక ఐచ్ఛిక నిబంధన మాత్రమే; ప్రతి ఫిర్యాదుకు ప్రాథమిక విచారణ తప్పనిసరి కాదు, నేరుగా ఎఫ్ఐఆర్ నమోదు చేయవచ్చు.',
            '5. CEIR పోర్టల్ (ceir.gov.in) లో IMEI బ్లాకింగ్ దరఖాస్తు చేయండి. అవసరమైనవి: (i) పోలీస్ ఫిర్యాదు/ఎఫ్ఐఆర్ రసీదు, (ii) OTP కోసం కొత్త సిమ్, (iii) గుర్తింపు కార్డు, మరియు (iv) IMEI నంబర్. కొనుగోలు బిల్లు (Purchase Invoice) ఐచ్ఛికం (Optional).',
            '6. CEIR బ్లాకింగ్ పరిధి: CEIR పరికరం యొక్క IMEI ని భారతీయ మొబైల్ నెట్‌వర్క్‌లలో మాత్రమే బ్లాక్ చేస్తుంది; ఇది మొత్తం పరికరాన్ని పూర్తిగా పనికిరాకుండా చేయదు (వైఫై లేదా ఆఫ్‌లైన్ ఉపయోగం సాధ్యం కావచ్చు).',
            '7. బ్యాంకింగ్, యూపీఐ, ఈమెయిల్ పాస్‌వర్డ్‌లను వెంటనే మార్చండి.'
        ]
    }
]

DISCLAIMER_TEXTS = {
    'en': 'DISCLAIMER: This legal explanation is generated by Law Mithra AI for informational guidance under Indian law and does not constitute an official court order, government notification, or substitute for formal legal representation.',
    'kn': 'ಎಚ್ಚರಿಕೆ: ಈ ಕಾನೂನು ವಿವರಣೆಯನ್ನು ಭಾರತೀಯ ಕಾನೂನಿನ ಅಡಿಯಲ್ಲಿ ಮಾಹಿತಿ ಮಾರ್ಗದರ್ಶನಕ್ಕಾಗಿ ಲಾ ಮಿತ್ರ ಎಐ ರೂಪಿಸಿದೆ. ಇದು ಅಧಿಕೃತ ನ್ಯಾಯಾಲಯದ ತೀರ್ಪಲ್ಲ ಅಥವಾ ವಕೀಲರ ಅಧಿಕೃತ ಕಾನೂನು ಸಲಹೆಗೆ ಪರ್ಯಾಯವಲ್ಲ.',
    'hi': 'अस्वीकरण: यह कानूनी विश्लेषण भारतीय कानून के तहत सूचनात्मक मार्गदर्शन हेतु लॉ मित्र एआई द्वारा तैयार किया गया है। यह आधिकारिक अदालती आदेश या अधिवक्ता परामर्श का विकल्प नहीं है।',
    'ta': 'பொறுப்புத் துறப்பு: இந்த சட்ட விளக்கம் இந்திய சட்டத்தின் கீழ் தகவல் வழிகாட்டுதலுக்காக லா மித்ரா ஏஐ ஆல் உருவாக்கப்பட்டது. இது அதிகாரப்பூர்வ நீதிமன்ற உத்தரவு அல்ல.',
    'te': 'నిరాకరణ: ఈ న్యాయ వివరణ భారతీయ చట్టం కింద సమాచార మార్గదర్శకత్వం కోసం లా మిత్ర ఏఐ ద్వారా అందించబడింది. ఇది అధికారిక కోర్టు తీర్పు కాదు.',
    'ml': 'നിരാകരണം: ഈ നിയമ വിവരണം ഇന്ത്യൻ നിയമപ്രകാരമുള്ള വിവര മാർഗ്ഗനിർദ്ദേശത്തിനായി ലോ മിത്ര എഐ തയ്യാറാക്കിയതാണ്. ഇത് ഔദ്യോഗിക കോടതി ഉത്തരവല്ല.',
    'mr': 'अस्वीकरण: हे कायदेशीर स्पष्टीकरण भारतीय कायद्यांतर्गत माहितीपर मार्गदर्शनासाठी लॉ मित्र एआय द्वारे तयार केले आहे. हा अधिकृत न्यायालयीन आदेश नाही.',
    'bn': 'দাবিত্যাগ: এই আইনি ব্যাখ্যাটি ভারতীয় আইনের অধীনে তথ্যগত নির্দেশনার জন্য ল মিত্র এআই দ্বারা প্রস্তুত করা হয়েছে। এটি কোনো সরকারি আদালতের আদেশ নয়।',
    'gu': 'અસ્વીકરણ: આ કાયદાકીય સમજૂતી ભારતીય કાયદા હેઠળ માહિતીના માર્ગદર્શન માટે લૉ મિત્ર એઆઈ દ્વારા તૈયાર કરવામાં આવી છે. આ સત્તાવાર કોર્ટ આદેશ નથી.',
    'pa': 'ਬੇਦਾਅਵਾ: ਇਹ ਕਾਨੂੰਨੀ ਵਿਆਖਿਆ ਭਾਰਤੀ ਕਾਨੂੰਨ ਤਹਿਤ ਜਾਣਕਾਰੀ ਲਈ ਲਾਅ ਮਿੱਤਰਾ ਏਆਈ ਦੁਆਰਾ ਤਿਆਰ ਕੀਤੀ ਗਈ ਹੈ। ਇਹ ਕੋਈ ਅਧਿਕਾਰਤ ਅਦਾਲਤੀ ਹੁਕਮ ਨਹੀਂ ਹੈ।'
}


class LegalAIService:
    """
    Multilingual Legal Intelligence pipeline.
    Preserves statutory accuracy, matches relevant Indian codes,
    and returns dual-format verified statutory provisions.
    """

    def __init__(self):
        self.bhashini = BhashiniClient()
        self.indictrans = IndicTransClient()
        self.gemini = GeminiClient()

    def process_query(
        self,
        query_text: str,
        preferred_lang: str = 'en',
        auto_detect_lang: bool = True
    ) -> Dict[str, Any]:
        """
        Executes the 7-step multilingual legal reasoning pipeline.
        """
        # Step 1: Language Detection
        detected_lang, confidence = detect_language(query_text, fallback=preferred_lang)
        target_lang = detected_lang if auto_detect_lang else preferred_lang
        if target_lang not in SUPPORTED_LANGUAGES:
            target_lang = 'en'

        # Step 2: Query Understanding & Legal Domain Matching
        matched_domain = self._match_legal_domain(query_text)

        # Step 3 & 4: Statutory Retrieval & Legal Fact Analysis
        applicable_laws = matched_domain['applicable_laws'] if matched_domain else []
        legal_issue = matched_domain['legal_issues'] if matched_domain else "Indian Legal Advisory"

        # Step 5: Procedural Remedies in Target Language
        localized_remedies = self._get_localized_remedies(matched_domain, target_lang)

        # Generate live response with Gemini AI if configured
        gemini_explanation = None
        try:
            gemini_explanation = self.gemini.generate_legal_response(
                query=query_text,
                language=target_lang,
                statutory_context=applicable_laws if applicable_laws else None
            )
        except Exception:
            gemini_explanation = None

        # Step 6 & 7: Dual-Language Generation with Statutory Protection
        response_data = {
            'query': query_text,
            'detected_language': detected_lang,
            'target_language': target_lang,
            'confidence': confidence,
            'legal_issue': gemini_explanation or legal_issue,
            'remedies': localized_remedies,
            'applicable_sections': [
                {
                    'act': law['act'],
                    'sections': law['sections'],
                    'summary': law['summary'],
                    'original_english_statute': law['english_statute'],
                }
                for law in applicable_laws
            ],
            'disclaimer': DISCLAIMER_TEXTS.get(target_lang, DISCLAIMER_TEXTS['en']),
            'terminology': [
                {
                    'term': 'Encroachment',
                    'localized': get_legal_term('Encroachment', target_lang)
                },
                {
                    'term': 'Injunction',
                    'localized': get_legal_term('Injunction', target_lang)
                },
                {
                    'term': 'Jurisdiction',
                    'localized': get_legal_term('Jurisdiction', target_lang)
                }
            ]
        }

        return response_data

    def _match_legal_domain(self, query: str) -> Optional[Dict[str, Any]]:
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

            elif domain_id == "stolen_mobile_phone":
                has_device = any(d in q_lower for d in ("phone", "mobile", "cell", "handset", "smartphone", "device"))
                has_theft_loss = any(l in q_lower for l in ("stolen", "lost", "theft", "snatch", "snatched", "snatching", "robbed"))
                if (has_device and has_theft_loss) or "ceir" in q_lower or "imei" in q_lower:
                    return domain

                specific_phrases = (
                    "stolen phone", "stolen mobile", "phone stolen", "mobile stolen",
                    "lost phone", "lost mobile", "phone lost", "mobile lost",
                    "snatched phone", "phone snatched", "mobile snatching", "snatching",
                    "theft of phone", "theft of mobile", "phone theft", "mobile theft",
                    "stolen cell", "lost cell", "stolen device",
                    "ceir", "imei", "block imei", "zero fir",
                    # Multilingual
                    "ಮೊಬೈಲ್ ಕಳ್ಳತನ", "ಫೋನ್ ಕಳೆದುಹೋಗಿದೆ", "ಮೊಬೈಲ್ ಕಳವು", "ಫೋನ್ ಕಳವು",
                    "मोबाइल चोरी", "फोन चोरी", "फोन खो गया", "मोबाइल खो गया",
                    "மொபைல் திருட்டு", "போன் தொலைந்துவிட்டது",
                    "ఫోన్ దొంగతనం", "మొబైల్ పోయింది",
                    "ഫോൺ മോഷ്ടിക്കപ്പെട്ടു", "മൊബൈൽ നഷ്ടപ്പെട്ടു",
                    "मोबाईल चोरी", "फोन चोरीला गेला",
                    "ফোন চুরি", "মোবাইল চুরি",
                    "મોબાઇલ ચોરી", "ફોન ચોરાયો",
                    "ਮੋਬਾਈਲ ਚੋਰੀ", "ਫੋਨ ਗੁੰਮ ਹੋ ਗਿਆ"
                )

                if any(term in q_lower for term in specific_phrases):
                    return domain

                generic_english = {"phone", "mobile", "device", "cell"}

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

    def _get_localized_remedies(self, domain: Optional[Dict[str, Any]], lang: str) -> List[str]:
        """Fetches curated verified legal remedies in target language."""
        if not domain:
            return []
        key = f"remedies_{lang}"
        if key in domain:
            return domain[key]

        # If direct curated translation is not stored for this specific regional dialect,
        # use English source guarded through Bhashini / IndicTrans
        en_remedies = domain.get('remedies_en', [])
        if lang == 'en':
            return en_remedies

        translated_remedies = []
        for remedy in en_remedies:
            translated = None
            if self.bhashini.is_configured:
                translated = self.bhashini.translate(remedy, source_lang='en', target_lang=lang)
            elif self.indictrans.is_configured:
                translated = self.indictrans.translate(remedy, source_lang='en', target_lang=lang)

            if translated:
                translated_remedies.append(translated)
            else:
                # Fallback to English with statutory guard to preserve strict legal validity
                translated_remedies.append(remedy)

        return translated_remedies

