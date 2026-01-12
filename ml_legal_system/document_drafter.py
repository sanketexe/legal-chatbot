"""
Legal Document Drafting System
Generate legal documents using templates and AI
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import re


class DocumentDrafter:
    """
    AI-powered legal document drafting system
    Features:
    - Template-based document generation
    - Context-aware customization
    - Compliance checking
    - Multi-format export
    """
    
    def __init__(self, templates_dir: str = "data/document_templates"):
        self.templates_dir = Path(templates_dir)
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self.templates = {}
        self._load_templates()
    
    def _load_templates(self):
        """Load document templates"""
        # Define built-in templates
        self.templates = {
            'nda': self._create_nda_template(),
            'employment_contract': self._create_employment_contract_template(),
            'non_compete': self._create_non_compete_template(),
            'legal_notice': self._create_legal_notice_template(),
            'complaint': self._create_complaint_template(),
            'settlement_agreement': self._create_settlement_template()
        }
        
        print(f"✅ Loaded {len(self.templates)} document templates")
    
    def _create_nda_template(self) -> Dict:
        """Non-Disclosure Agreement template"""
        return {
            'name': 'Non-Disclosure Agreement (NDA)',
            'category': 'Contract',
            'fields': [
                'disclosing_party_name',
                'disclosing_party_address',
                'receiving_party_name',
                'receiving_party_address',
                'effective_date',
                'term_years',
                'purpose',
                'confidential_information_definition',
                'jurisdiction'
            ],
            'template': """
NON-DISCLOSURE AGREEMENT

This Non-Disclosure Agreement ("Agreement") is entered into on {effective_date} ("Effective Date") by and between:

DISCLOSING PARTY:
{disclosing_party_name}
{disclosing_party_address}
("Disclosing Party")

AND

RECEIVING PARTY:
{receiving_party_name}
{receiving_party_address}
("Receiving Party")

RECITALS:

WHEREAS, the Disclosing Party possesses certain confidential and proprietary information;
WHEREAS, the Receiving Party desires to receive such confidential information for the purpose of {purpose};

NOW, THEREFORE, in consideration of the mutual covenants and agreements contained herein, the parties agree as follows:

1. CONFIDENTIAL INFORMATION
   
   1.1 "Confidential Information" means {confidential_information_definition}
   
   1.2 Confidential Information shall not include information that:
       (a) Is or becomes publicly available through no breach of this Agreement;
       (b) Was rightfully in the Receiving Party's possession prior to disclosure;
       (c) Is independently developed by the Receiving Party;
       (d) Is rightfully obtained from a third party without breach.

2. OBLIGATIONS OF RECEIVING PARTY
   
   2.1 The Receiving Party agrees to:
       (a) Maintain the confidentiality of all Confidential Information;
       (b) Use the Confidential Information solely for {purpose};
       (c) Not disclose Confidential Information to any third party without prior written consent;
       (d) Protect Confidential Information with the same degree of care used for its own confidential information.

3. TERM
   
   This Agreement shall commence on the Effective Date and continue for a period of {term_years} years.

4. RETURN OF MATERIALS
   
   Upon termination or upon request, the Receiving Party shall return or destroy all Confidential Information.

5. REMEDIES
   
   The parties acknowledge that breach of this Agreement may cause irreparable harm, and the Disclosing Party shall be entitled to seek injunctive relief.

6. GOVERNING LAW
   
   This Agreement shall be governed by the laws of {jurisdiction}.

7. ENTIRE AGREEMENT
   
   This Agreement constitutes the entire agreement between the parties regarding confidentiality.

IN WITNESS WHEREOF, the parties have executed this Agreement as of the date first written above.

DISCLOSING PARTY:                    RECEIVING PARTY:

_________________________            _________________________
{disclosing_party_name}              {receiving_party_name}

Date: ___________________            Date: ___________________
"""
        }
    
    def _create_employment_contract_template(self) -> Dict:
        """Employment contract template for tech industry"""
        return {
            'name': 'Employment Contract (Tech Industry)',
            'category': 'Employment',
            'fields': [
                'company_name',
                'company_address',
                'employee_name',
                'employee_address',
                'position',
                'start_date',
                'salary_amount',
                'salary_frequency',
                'working_hours',
                'probation_period',
                'notice_period',
                'benefits',
                'ip_clause',
                'jurisdiction'
            ],
            'template': """
EMPLOYMENT AGREEMENT

This Employment Agreement ("Agreement") is made on {start_date} between:

EMPLOYER:
{company_name}
{company_address}
("Company")

AND

EMPLOYEE:
{employee_name}
{employee_address}
("Employee")

1. POSITION AND DUTIES
   
   1.1 The Employee is appointed as {position}.
   1.2 The Employee shall perform duties as assigned by the Company.
   1.3 The Employee shall devote full working time to the Company's business.

2. COMMENCEMENT AND PROBATION
   
   2.1 Employment commences on {start_date}.
   2.2 Probation period: {probation_period} months.

3. REMUNERATION
   
   3.1 Salary: {salary_amount} per {salary_frequency}.
   3.2 Payment shall be made monthly via bank transfer.
   3.3 Subject to applicable tax deductions as per Indian law.

4. WORKING HOURS
   
   4.1 Standard working hours: {working_hours} per week.
   4.2 The Employee may be required to work additional hours as needed.

5. BENEFITS
   
   {benefits}

6. INTELLECTUAL PROPERTY
   
   {ip_clause}
   
   All work product, inventions, and intellectual property created during employment shall belong to the Company.

7. CONFIDENTIALITY
   
   The Employee agrees to maintain confidentiality of all Company information during and after employment.

8. TERMINATION
   
   8.1 Either party may terminate this Agreement by providing {notice_period} days written notice.
   8.2 The Company may terminate immediately for cause without notice.

9. POST-TERMINATION OBLIGATIONS
   
   Upon termination, the Employee shall:
   - Return all Company property
   - Delete all Company data from personal devices
   - Continue to honor confidentiality obligations

10. NON-COMPETE (if applicable)
    
    During employment and for [SPECIFY PERIOD] after termination, the Employee shall not engage in competing business.

11. GOVERNING LAW
    
    This Agreement is governed by the laws of {jurisdiction}, India.

12. ENTIRE AGREEMENT
    
    This Agreement constitutes the entire agreement between the parties.

SIGNATURES:

COMPANY:                             EMPLOYEE:

_________________________            _________________________
Authorized Signatory                 {employee_name}
{company_name}

Date: ___________________            Date: ___________________
"""
        }
    
    def _create_non_compete_template(self) -> Dict:
        """Non-compete agreement template"""
        return {
            'name': 'Non-Compete Agreement',
            'category': 'Employment',
            'fields': [
                'company_name',
                'employee_name',
                'effective_date',
                'restricted_period_months',
                'geographical_scope',
                'prohibited_activities',
                'consideration',
                'jurisdiction'
            ],
            'template': """
NON-COMPETE AGREEMENT

This Non-Compete Agreement is entered into on {effective_date} between:

{company_name} ("Company")
AND
{employee_name} ("Employee")

1. NON-COMPETE COVENANT
   
   The Employee agrees that during employment and for {restricted_period_months} months after termination, the Employee shall not:
   
   (a) Engage in any business that competes with the Company within {geographical_scope};
   (b) {prohibited_activities}

2. CONSIDERATION
   
   In consideration for this Agreement, the Company provides: {consideration}

3. REASONABLENESS
   
   The parties acknowledge that the restrictions are reasonable and necessary to protect the Company's legitimate business interests.

4. REMEDIES
   
   Breach of this Agreement shall entitle the Company to injunctive relief and damages.

5. GOVERNING LAW
   
   This Agreement is governed by the laws of {jurisdiction}, India.

NOTE: Non-compete clauses in India are generally unenforceable during employment under Section 27 of the Indian Contract Act, 1872. Post-employment restrictions may be valid if reasonable.

SIGNATURES:

_________________________            _________________________
Company Representative               {employee_name}

Date: ___________________            Date: ___________________
"""
        }
    
    def _create_legal_notice_template(self) -> Dict:
        """Legal notice template"""
        return {
            'name': 'Legal Notice',
            'category': 'Litigation',
            'fields': [
                'sender_name',
                'sender_address',
                'recipient_name',
                'recipient_address',
                'notice_date',
                'subject',
                'facts',
                'legal_basis',
                'demands',
                'response_deadline_days'
            ],
            'template': """
LEGAL NOTICE

Date: {notice_date}

To,
{recipient_name}
{recipient_address}

From,
{sender_name}
{sender_address}

Subject: {subject}

Dear Sir/Madam,

Under instructions from and on behalf of my client, {sender_name}, I serve upon you this legal notice.

FACTS:

{facts}

LEGAL BASIS:

{legal_basis}

DEMANDS:

My client demands that you:

{demands}

You are hereby called upon to comply with the above demands within {response_deadline_days} days from the receipt of this notice, failing which my client shall be constrained to initiate appropriate legal proceedings against you, at your risk as to costs and consequences, without any further reference to you.

This notice is issued without prejudice to my client's rights, remedies, and contentions, all of which are expressly reserved.

Yours faithfully,

_________________________
[Advocate Name]
[Enrollment Number]
[Address]

(On behalf of {sender_name})
"""
        }
    
    def _create_complaint_template(self) -> Dict:
        """Legal complaint template"""
        return {
            'name': 'Legal Complaint',
            'category': 'Litigation',
            'fields': [
                'court_name',
                'plaintiff_name',
                'plaintiff_address',
                'defendant_name',
                'defendant_address',
                'case_type',
                'facts',
                'cause_of_action',
                'relief_sought',
                'jurisdiction_reason',
                'valuation'
            ],
            'template': """
IN THE {court_name}

{case_type} NO. _____ OF 20___

IN THE MATTER OF:

{plaintiff_name}
{plaintiff_address}
... Plaintiff

VERSUS

{defendant_name}
{defendant_address}
... Defendant

COMPLAINT UNDER [SPECIFY ACT/SECTION]

TO,
THE HON'BLE [DESIGNATION OF JUDGE]

The Plaintiff most respectfully submits as follows:

1. PARTIES

   1.1 The Plaintiff, {plaintiff_name}, is a resident of {plaintiff_address}.
   
   1.2 The Defendant, {defendant_name}, is a resident of {defendant_address}.

2. FACTS OF THE CASE

{facts}

3. CAUSE OF ACTION

{cause_of_action}

4. JURISDICTION

This Hon'ble Court has jurisdiction to entertain this complaint because:

{jurisdiction_reason}

5. VALUATION

The subject matter is valued at Rs. {valuation} for the purpose of court fees and jurisdiction.

6. RELIEF SOUGHT

In light of the above, the Plaintiff prays that this Hon'ble Court may be pleased to:

{relief_sought}

7. VERIFICATION

I, {plaintiff_name}, the Plaintiff, do hereby verify that the contents of the above complaint are true to the best of my knowledge and belief and nothing material has been concealed therefrom.

Place: __________
Date: __________

                                        _________________________
                                        {plaintiff_name}
                                        (Plaintiff)
"""
        }
    
    def _create_settlement_template(self) -> Dict:
        """Settlement agreement template"""
        return {
            'name': 'Settlement Agreement',
            'category': 'Dispute Resolution',
            'fields': [
                'party1_name',
                'party1_address',
                'party2_name',
                'party2_address',
                'dispute_description',
                'settlement_date',
                'settlement_amount',
                'payment_terms',
                'mutual_release',
                'jurisdiction'
            ],
            'template': """
SETTLEMENT AGREEMENT

This Settlement Agreement is entered into on {settlement_date} between:

PARTY 1:
{party1_name}
{party1_address}

AND

PARTY 2:
{party2_name}
{party2_address}

RECITALS:

A. A dispute arose between the parties concerning: {dispute_description}

B. The parties wish to settle all disputes amicably without litigation.

NOW, THEREFORE, the parties agree as follows:

1. SETTLEMENT PAYMENT
   
   {payment_terms}
   
   Party 2 shall pay Party 1 the sum of Rs. {settlement_amount} as full and final settlement.

2. MUTUAL RELEASE
   
   {mutual_release}
   
   Upon payment, both parties release each other from all claims related to the dispute.

3. CONFIDENTIALITY
   
   The parties agree to keep the terms of this settlement confidential.

4. NO ADMISSION OF LIABILITY
   
   This settlement is made without admission of liability by either party.

5. GOVERNING LAW
   
   This Agreement is governed by the laws of {jurisdiction}, India.

6. ENTIRE AGREEMENT
   
   This Agreement constitutes the entire understanding between the parties.

SIGNATURES:

_________________________            _________________________
{party1_name}                        {party2_name}

Date: ___________________            Date: ___________________
"""
        }
    
    def list_templates(self) -> List[Dict]:
        """Get list of available templates"""
        return [
            {
                'id': key,
                'name': template['name'],
                'category': template['category'],
                'fields': template['fields']
            }
            for key, template in self.templates.items()
        ]
    
    def draft_document(self, template_id: str, fields: Dict, ai_enhance: bool = False) -> Dict:
        """
        Draft a legal document
        
        Args:
            template_id: Template identifier
            fields: Dictionary of field values
            ai_enhance: Whether to use AI for enhancement
            
        Returns:
            Dict with document text, warnings, suggestions
        """
        if template_id not in self.templates:
            return {
                'error': f'Template {template_id} not found',
                'available_templates': list(self.templates.keys())
            }
        
        template = self.templates[template_id]
        
        # Validate required fields
        missing_fields = [f for f in template['fields'] if f not in fields]
        if missing_fields:
            return {
                'error': 'Missing required fields',
                'missing_fields': missing_fields,
                'required_fields': template['fields']
            }
        
        # Generate document
        try:
            document_text = template['template'].format(**fields)
        except KeyError as e:
            return {
                'error': f'Field formatting error: {e}',
                'fields_provided': list(fields.keys()),
                'fields_required': template['fields']
            }
        
        # Validate document
        warnings = self._validate_document(document_text, template_id)
        
        # Generate suggestions
        suggestions = self._generate_suggestions(template_id, fields)
        
        result = {
            'template_name': template['name'],
            'document': document_text,
            'warnings': warnings,
            'suggestions': suggestions,
            'generated_at': datetime.now().isoformat(),
            'word_count': len(document_text.split())
        }
        
        # Save draft
        self._save_draft(template_id, result)
        
        return result
    
    def _validate_document(self, document: str, template_id: str) -> List[str]:
        """Validate document for common issues"""
        warnings = []
        
        # Check for unfilled placeholders
        placeholders = re.findall(r'\{(\w+)\}', document)
        if placeholders:
            warnings.append(f"⚠️ Unfilled placeholders: {', '.join(placeholders)}")
        
        # Check for empty sections
        if '____' in document and document.count('____') > 3:
            warnings.append("⚠️ Multiple blank fields to be filled manually")
        
        # Template-specific validations
        if template_id == 'non_compete':
            warnings.append(
                "⚠️ Non-compete clauses during employment are generally unenforceable in India "
                "under Section 27 of the Indian Contract Act, 1872"
            )
        
        if template_id == 'employment_contract':
            if 'probation' in document.lower():
                warnings.append(
                    "ℹ️ Ensure probation period complies with applicable labor laws"
                )
        
        return warnings
    
    def _generate_suggestions(self, template_id: str, fields: Dict) -> List[str]:
        """Generate improvement suggestions"""
        suggestions = []
        
        if template_id == 'nda':
            suggestions.append("Consider adding specific examples of confidential information")
            suggestions.append("Review if geographic or temporal limitations are appropriate")
        
        if template_id == 'employment_contract':
            suggestions.append("Ensure salary complies with minimum wage laws")
            suggestions.append("Consider adding clauses for work-from-home arrangements")
            suggestions.append("Review IP assignment clauses for compliance")
        
        if template_id == 'legal_notice':
            suggestions.append("Attach supporting documents if available")
            suggestions.append("Send via registered post with acknowledgment due")
        
        suggestions.append("Have document reviewed by a qualified legal professional")
        suggestions.append("Ensure all parties receive copies of the signed document")
        
        return suggestions
    
    def _save_draft(self, template_id: str, result: Dict):
        """Save draft to file"""
        drafts_dir = self.templates_dir / "drafts"
        drafts_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{template_id}_{timestamp}.json"
        
        try:
            with open(drafts_dir / filename, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Could not save draft: {e}")
    
    def export_document(self, document_text: str, filename: str, format: str = 'txt'):
        """
        Export document to file
        
        Args:
            document_text: Document content
            filename: Output filename
            format: Output format ('txt', 'md')
        """
        output_dir = self.templates_dir / "exports"
        output_dir.mkdir(exist_ok=True)
        
        filepath = output_dir / f"{filename}.{format}"
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(document_text)
            
            return {
                'success': True,
                'filepath': str(filepath),
                'size_bytes': filepath.stat().st_size
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
