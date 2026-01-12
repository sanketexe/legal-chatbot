"""
Legal Document Generator
Generates common legal documents like contracts, affidavits, notices, etc.
"""

from datetime import datetime
from typing import Dict, Any, Optional
import json

class LegalDocumentGenerator:
    """Generate various legal documents"""
    
    def __init__(self):
        self.templates = {
            'rent_agreement': self._rent_agreement_template,
            'affidavit': self._affidavit_template,
            'notice': self._legal_notice_template,
            'power_of_attorney': self._power_of_attorney_template,
            'sale_deed': self._sale_deed_template,
            'employment_contract': self._employment_contract_template,
            'nda': self._nda_template,
            'loan_agreement': self._loan_agreement_template,
        }
    
    def generate_document(self, doc_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a legal document based on type and data"""
        if doc_type not in self.templates:
            return {
                'success': False,
                'error': f'Document type "{doc_type}" not supported'
            }
        
        try:
            content = self.templates[doc_type](data)
            return {
                'success': True,
                'document_type': doc_type,
                'content': content,
                'generated_at': datetime.now().isoformat(),
                'metadata': {
                    'title': self._get_document_title(doc_type),
                    'word_count': len(content.split()),
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error generating document: {str(e)}'
            }
    
    def get_available_templates(self) -> Dict[str, str]:
        """Get list of available document templates"""
        return {
            'rent_agreement': 'Rental Agreement',
            'affidavit': 'Affidavit',
            'notice': 'Legal Notice',
            'power_of_attorney': 'Power of Attorney',
            'sale_deed': 'Sale Deed',
            'employment_contract': 'Employment Contract',
            'nda': 'Non-Disclosure Agreement (NDA)',
            'loan_agreement': 'Loan Agreement',
        }
    
    def _get_document_title(self, doc_type: str) -> str:
        """Get human-readable title for document type"""
        titles = self.get_available_templates()
        return titles.get(doc_type, doc_type.replace('_', ' ').title())
    
    # Template Methods
    
    def _rent_agreement_template(self, data: Dict) -> str:
        """Generate rent agreement"""
        return f"""
RENTAL AGREEMENT

This Rental Agreement is made on {data.get('date', datetime.now().strftime('%B %d, %Y'))} between:

LANDLORD:
Name: {data.get('landlord_name', '[LANDLORD NAME]')}
Address: {data.get('landlord_address', '[LANDLORD ADDRESS]')}
Contact: {data.get('landlord_contact', '[LANDLORD CONTACT]')}

TENANT:
Name: {data.get('tenant_name', '[TENANT NAME]')}
Address: {data.get('tenant_address', '[TENANT ADDRESS]')}
Contact: {data.get('tenant_contact', '[TENANT CONTACT]')}

PROPERTY DETAILS:
Address: {data.get('property_address', '[PROPERTY ADDRESS]')}
Type: {data.get('property_type', 'Residential')}

TERMS AND CONDITIONS:

1. RENT: The monthly rent for the property shall be Rs. {data.get('rent_amount', '[AMOUNT]')}/-

2. SECURITY DEPOSIT: A refundable security deposit of Rs. {data.get('security_deposit', '[AMOUNT]')}/-

3. LEASE PERIOD: From {data.get('start_date', '[START DATE]')} to {data.get('end_date', '[END DATE]')}

4. PAYMENT: Rent shall be paid on or before the {data.get('payment_date', '5th')} day of each month.

5. MAINTENANCE: The Tenant shall maintain the property in good condition and shall be responsible for minor repairs.

6. UTILITIES: {data.get('utilities', 'Electricity, water, and gas charges shall be borne by the Tenant.')}

7. TERMINATION: Either party may terminate this agreement by giving {data.get('notice_period', '30')} days written notice.

8. GOVERNING LAW: This agreement shall be governed by the laws of India.


_______________________          _______________________
Landlord Signature               Tenant Signature

WITNESS 1:                       WITNESS 2:
Name: _______________            Name: _______________
Signature: ___________           Signature: ___________
"""

    def _affidavit_template(self, data: Dict) -> str:
        """Generate affidavit"""
        return f"""
AFFIDAVIT

I, {data.get('deponent_name', '[YOUR NAME]')}, aged {data.get('age', '[AGE]')} years, son/daughter of {data.get('parent_name', '[PARENT NAME]')}, resident of {data.get('address', '[ADDRESS]')}, do hereby solemnly affirm and declare as follows:

1. That I am the Deponent in this matter and I am competent to swear this affidavit.

2. That {data.get('statement', '[YOUR STATEMENT/FACTS]')}

3. That the contents of this affidavit are true and correct to the best of my knowledge and belief.

4. That I have not suppressed any material facts and that no part of this affidavit is false.

5. That this affidavit is being made for {data.get('purpose', '[PURPOSE]')}.


DEPONENT

Solemnly affirmed at {data.get('place', '[PLACE]')} on {data.get('date', datetime.now().strftime('%B %d, %Y'))}

Before me,

NOTARY PUBLIC
"""

    def _legal_notice_template(self, data: Dict) -> str:
        """Generate legal notice"""
        return f"""
LEGAL NOTICE

Date: {data.get('date', datetime.now().strftime('%B %d, %Y'))}

To,
{data.get('recipient_name', '[RECIPIENT NAME]')}
{data.get('recipient_address', '[RECIPIENT ADDRESS]')}

Subject: {data.get('subject', 'Legal Notice')}

Dear Sir/Madam,

UNDER INSTRUCTIONS FROM MY CLIENT:
{data.get('sender_name', '[YOUR NAME]')}
{data.get('sender_address', '[YOUR ADDRESS]')}

FACTS OF THE CASE:
{data.get('facts', '[DETAILED FACTS OF THE CASE]')}

LEGAL GROUNDS:
{data.get('legal_grounds', '[APPLICABLE LAWS AND SECTIONS]')}

DEMAND:
You are hereby called upon to {data.get('demand', '[YOUR DEMAND]')} within {data.get('response_period', '15')} days from the receipt of this notice, failing which my client shall be constrained to initiate appropriate legal proceedings against you at your risk as to costs and consequences.

TAKE NOTICE that if you fail to comply with the above demand within the stipulated time, my client shall be compelled to take appropriate legal action including filing a civil/criminal suit against you.

This notice is without prejudice to the rights, remedies, and contentions of my client, all of which are hereby expressly reserved.

Yours faithfully,

{data.get('lawyer_name', '[ADVOCATE NAME]')}
{data.get('lawyer_address', '[ADVOCATE ADDRESS]')}
{data.get('lawyer_contact', '[ADVOCATE CONTACT]')}
"""

    def _power_of_attorney_template(self, data: Dict) -> str:
        """Generate power of attorney"""
        return f"""
POWER OF ATTORNEY

This Power of Attorney is executed on {data.get('date', datetime.now().strftime('%B %d, %Y'))} at {data.get('place', '[PLACE]')}

By:
{data.get('principal_name', '[PRINCIPAL NAME]')}, aged {data.get('principal_age', '[AGE]')} years
Son/Daughter of {data.get('principal_parent', '[PARENT NAME]')}
Resident of {data.get('principal_address', '[ADDRESS]')}
(hereinafter referred to as the "Principal")

In favour of:
{data.get('attorney_name', '[ATTORNEY NAME]')}, aged {data.get('attorney_age', '[AGE]')} years
Son/Daughter of {data.get('attorney_parent', '[PARENT NAME]')}
Resident of {data.get('attorney_address', '[ADDRESS]')}
(hereinafter referred to as the "Attorney")

WHEREAS the Principal desires to appoint the Attorney to act on behalf of the Principal for {data.get('purpose', '[PURPOSE]')}

NOW THIS POWER OF ATTORNEY WITNESSETH AS FOLLOWS:

1. The Principal hereby appoints the Attorney as their true and lawful attorney to:
   {data.get('powers', '[LIST OF POWERS]')}

2. The Attorney shall have full power and authority to do all acts, deeds, and things as may be necessary for the said purpose.

3. This Power of Attorney shall remain in force from {data.get('start_date', '[START DATE]')} to {data.get('end_date', '[END DATE]')} unless revoked earlier.

4. All acts done by the Attorney pursuant to this Power of Attorney shall be binding on the Principal.


_______________________
Principal Signature

_______________________
Attorney Signature

WITNESSES:
1. _______________    2. _______________
"""

    def _sale_deed_template(self, data: Dict) -> str:
        """Generate sale deed"""
        return f"""
SALE DEED

This Sale Deed is executed on {data.get('date', datetime.now().strftime('%B %d, %Y'))} at {data.get('place', '[PLACE]')}

BETWEEN:

VENDOR:
{data.get('vendor_name', '[VENDOR NAME]')}, aged {data.get('vendor_age', '[AGE]')} years
Son/Daughter of {data.get('vendor_parent', '[PARENT NAME]')}
Resident of {data.get('vendor_address', '[ADDRESS]')}
(hereinafter referred to as the "Vendor")

AND

PURCHASER:
{data.get('purchaser_name', '[PURCHASER NAME]')}, aged {data.get('purchaser_age', '[AGE]')} years
Son/Daughter of {data.get('purchaser_parent', '[PARENT NAME]')}
Resident of {data.get('purchaser_address', '[ADDRESS]')}
(hereinafter referred to as the "Purchaser")

PROPERTY DETAILS:
{data.get('property_description', '[DETAILED PROPERTY DESCRIPTION]')}
Survey No: {data.get('survey_no', '[SURVEY NO]')}
Area: {data.get('area', '[AREA]')}
Boundaries: {data.get('boundaries', '[BOUNDARIES]')}

SALE CONSIDERATION:
Rs. {data.get('sale_amount', '[AMOUNT]')}/-
(Rupees {data.get('sale_amount_words', '[AMOUNT IN WORDS]')} Only)

TERMS AND CONDITIONS:

1. The Vendor hereby transfers all rights, title, and interest in the property to the Purchaser.

2. The Purchaser has paid the full sale consideration to the Vendor.

3. The property is free from all encumbrances, liens, and charges.

4. Possession of the property has been handed over to the Purchaser.

5. All taxes, charges up to the date of this deed shall be borne by the Vendor.


_______________________          _______________________
Vendor Signature                 Purchaser Signature

WITNESSES:
1. _______________    2. _______________
"""

    def _employment_contract_template(self, data: Dict) -> str:
        """Generate employment contract"""
        return f"""
EMPLOYMENT CONTRACT

This Employment Contract is entered into on {data.get('date', datetime.now().strftime('%B %d, %Y'))} between:

EMPLOYER:
{data.get('company_name', '[COMPANY NAME]')}
{data.get('company_address', '[COMPANY ADDRESS]')}
(hereinafter referred to as the "Employer")

AND

EMPLOYEE:
{data.get('employee_name', '[EMPLOYEE NAME]')}
{data.get('employee_address', '[EMPLOYEE ADDRESS]')}
(hereinafter referred to as the "Employee")

TERMS OF EMPLOYMENT:

1. POSITION: {data.get('position', '[JOB TITLE]')}

2. COMMENCEMENT: {data.get('start_date', '[START DATE]')}

3. SALARY: Rs. {data.get('salary', '[AMOUNT]')}/- per month

4. WORKING HOURS: {data.get('working_hours', '9 AM to 6 PM, Monday to Friday')}

5. PROBATION: {data.get('probation_period', '3')} months

6. LEAVE: {data.get('leave_days', '21')} days of paid leave per year

7. NOTICE PERIOD: {data.get('notice_period', '30')} days

8. CONFIDENTIALITY: Employee shall maintain confidentiality of all company information.

9. NON-COMPETE: Employee shall not engage in competing business during employment and for {data.get('non_compete_period', '6')} months after termination.

10. TERMINATION: Either party may terminate with written notice as per clause 7.


_______________________          _______________________
Employer Signature               Employee Signature
"""

    def _nda_template(self, data: Dict) -> str:
        """Generate NDA"""
        return f"""
NON-DISCLOSURE AGREEMENT

This Non-Disclosure Agreement ("Agreement") is made on {data.get('date', datetime.now().strftime('%B %d, %Y'))} between:

DISCLOSING PARTY:
{data.get('disclosing_party', '[DISCLOSING PARTY NAME]')}
{data.get('disclosing_address', '[ADDRESS]')}

AND

RECEIVING PARTY:
{data.get('receiving_party', '[RECEIVING PARTY NAME]')}
{data.get('receiving_address', '[ADDRESS]')}

WHEREAS the parties wish to explore a business relationship regarding {data.get('purpose', '[PURPOSE]')} and in connection therewith may disclose certain confidential information.

NOW THEREFORE, in consideration of the mutual promises and covenants, the parties agree as follows:

1. CONFIDENTIAL INFORMATION: Means any information disclosed by one party to the other including technical, business, or financial information.

2. OBLIGATIONS:
   a) Receiving Party shall maintain confidentiality
   b) Use information only for the stated purpose
   c) Not disclose to third parties without written consent

3. EXCLUSIONS: Information that is:
   a) Already in public domain
   b) Independently developed
   c) Rightfully obtained from third parties

4. TERM: This Agreement shall remain in effect for {data.get('duration', '2')} years from the date of execution.

5. REMEDIES: Any breach may result in irreparable harm entitling the aggrieved party to seek injunctive relief.

6. GOVERNING LAW: Laws of India


_______________________          _______________________
Disclosing Party                 Receiving Party
"""

    def _loan_agreement_template(self, data: Dict) -> str:
        """Generate loan agreement"""
        return f"""
LOAN AGREEMENT

This Loan Agreement is made on {data.get('date', datetime.now().strftime('%B %d, %Y'))} between:

LENDER:
{data.get('lender_name', '[LENDER NAME]')}
{data.get('lender_address', '[LENDER ADDRESS]')}

AND

BORROWER:
{data.get('borrower_name', '[BORROWER NAME]')}
{data.get('borrower_address', '[BORROWER ADDRESS]')}

LOAN DETAILS:

1. PRINCIPAL AMOUNT: Rs. {data.get('loan_amount', '[AMOUNT]')}/-

2. INTEREST RATE: {data.get('interest_rate', '[RATE]')}% per annum

3. REPAYMENT PERIOD: {data.get('repayment_period', '[MONTHS]')} months

4. INSTALLMENTS: Rs. {data.get('installment_amount', '[AMOUNT]')}/- per month

5. PAYMENT DATE: {data.get('payment_date', '[DATE]')} of each month

6. PURPOSE: {data.get('purpose', '[LOAN PURPOSE]')}

7. SECURITY: {data.get('security', '[SECURITY/COLLATERAL DETAILS]')}

TERMS AND CONDITIONS:

1. The Borrower promises to repay the loan amount with interest as per the schedule.

2. In case of default, the Lender may:
   a) Charge penalty of {data.get('penalty_rate', '2')}% per month
   b) Demand immediate repayment of outstanding amount
   c) Enforce security/collateral

3. The Borrower may prepay without penalty after {data.get('prepayment_period', '6')} months.

4. This agreement is governed by Indian laws.


_______________________          _______________________
Lender Signature                 Borrower Signature

WITNESSES:
1. _______________    2. _______________
"""


# Utility function
def get_document_fields(doc_type: str) -> Dict[str, Any]:
    """Get required fields for a document type"""
    fields = {
        'rent_agreement': {
            'landlord_name': 'text',
            'landlord_address': 'textarea',
            'tenant_name': 'text',
            'tenant_address': 'textarea',
            'property_address': 'textarea',
            'rent_amount': 'number',
            'security_deposit': 'number',
            'start_date': 'date',
            'end_date': 'date',
        },
        'affidavit': {
            'deponent_name': 'text',
            'age': 'number',
            'parent_name': 'text',
            'address': 'textarea',
            'statement': 'textarea',
            'purpose': 'text',
            'place': 'text',
        },
        'notice': {
            'recipient_name': 'text',
            'recipient_address': 'textarea',
            'sender_name': 'text',
            'subject': 'text',
            'facts': 'textarea',
            'demand': 'textarea',
            'lawyer_name': 'text',
        },
        'power_of_attorney': {
            'principal_name': 'text',
            'attorney_name': 'text',
            'purpose': 'text',
            'powers': 'textarea',
            'start_date': 'date',
            'end_date': 'date',
        },
        'sale_deed': {
            'vendor_name': 'text',
            'purchaser_name': 'text',
            'property_description': 'textarea',
            'sale_amount': 'number',
            'survey_no': 'text',
            'area': 'text',
        },
        'employment_contract': {
            'company_name': 'text',
            'employee_name': 'text',
            'position': 'text',
            'salary': 'number',
            'start_date': 'date',
            'probation_period': 'number',
        },
        'nda': {
            'disclosing_party': 'text',
            'receiving_party': 'text',
            'purpose': 'text',
            'duration': 'number',
        },
        'loan_agreement': {
            'lender_name': 'text',
            'borrower_name': 'text',
            'loan_amount': 'number',
            'interest_rate': 'number',
            'repayment_period': 'number',
            'purpose': 'text',
        },
    }
    return fields.get(doc_type, {})
