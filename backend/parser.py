
"""
Credit Card Statement Parser - FIXED VERSION
Supports: HDFC, ICICI, Kotak, Amex, Capital One
Extracts: Due Date, Last 4 Digits, Credit Limit, Available Credit, Statement Date

Based on actual text extraction analysis from debug output
"""

import re
import pytesseract
from pdf2image import convert_from_path
from PyPDF2 import PdfReader
from datetime import datetime
from typing import Dict, Optional, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CreditCardParser:
    """Enhanced parser based on actual PDF text patterns"""
    
    def __init__(self, tesseract_path: Optional[str] = None):
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
    
    def parse_statement(self, pdf_path: str) -> Dict[str, Optional[str]]:
        """Parse credit card statement using both regex and OCR"""
        logger.info(f"Processing: {pdf_path}")
        
        # Extract text using PyPDF2
        text_content = self._extract_text_from_pdf(pdf_path)
        
        # Extract text using OCR
        ocr_content = self._extract_text_from_ocr(pdf_path)
        
        # Detect bank
        bank = self._detect_bank(text_content, ocr_content)
        logger.info(f"Detected bank: {bank}")
        
        # Extract fields using both methods
        regex_results = self._extract_with_regex(text_content, bank, "PyPDF2")
        ocr_results = self._extract_with_regex(ocr_content, bank, "OCR")
        
        # Combine results with bank-specific logic
        final_results = self._combine_results(regex_results, ocr_results, bank)
        final_results['bank'] = bank
        
        # Log results
        for key, value in final_results.items():
            if value:
                logger.info(f"✓ Found {key}: {value}")
            else:
                logger.warning(f"✗ Missing {key}")
        
        return final_results
    
    def _extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF using PyPDF2"""
        try:
            reader = PdfReader(pdf_path)
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            return text
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            return ""
    
    def _extract_text_from_ocr(self, pdf_path: str) -> str:
        """Extract text from PDF using OCR"""
        try:
            images = convert_from_path(pdf_path, dpi=300, first_page=1, last_page=3)
            
            ocr_text = ""
            for i, image in enumerate(images):
                text = pytesseract.image_to_string(image, lang='eng', config='--psm 6')
                ocr_text += text + "\n"
                logger.info(f"OCR processed page {i+1}")
            
            return ocr_text
        except Exception as e:
            logger.error(f"Error in OCR processing: {e}")
            return ""
    
    def _detect_bank(self, text_content: str, ocr_content: str) -> str:
        """Detect bank from statement"""
        combined_text = (text_content + " " + ocr_content).lower()
        
        if "hdfc bank" in combined_text or "hdfcbank" in combined_text:
            return "HDFC"
        elif "icici bank" in combined_text or "icicibank" in combined_text:
            return "ICICI"
        elif "kotak" in combined_text:
            return "KOTAK"
        elif "american express" in combined_text or "amex" in combined_text or "aebc" in combined_text:
            return "AMEX"
        elif "capital one" in combined_text or "capitalone" in combined_text:
            return "CAPITAL_ONE"
        else:
            return "UNKNOWN"
    
    def _extract_with_regex(self, text: str, bank: str, method: str) -> Dict[str, Optional[str]]:
        """Extract fields using bank-specific patterns"""
        results = {
            'due_date': None,
            'last_4_digits': None,
            'credit_limit': None,
            'available_credit': None,
            'statement_date': None
        }
        
        if bank == "HDFC":
            results.update(self._parse_hdfc(text, method))
        elif bank == "ICICI":
            results.update(self._parse_icici(text, method))
        elif bank == "KOTAK":
            results.update(self._parse_kotak(text, method))
        elif bank == "AMEX":
            results.update(self._parse_amex(text, method))
        elif bank == "CAPITAL_ONE":
            results.update(self._parse_capital_one(text, method))
        
        return results
    
    def _parse_hdfc(self, text: str, method: str) -> Dict[str, Optional[str]]:
        """Parse HDFC Bank statement
        Pattern from debug: Credit Limit Available Credit Limit Available Cash Limit
                           3,02,000 23,519 0.00 (PyPDF2)
                           3,02,000 2,56,760.00 - (OCR - correct!)
        """
        results = {}
        
        # Due Date - Pattern: Payment Due Date Total Dues Minimum Amount Due
        #                     28/06/2019 45,240.00 13,636.00
        patterns = [
            r'Payment\s+Due\s+Date\s+Total\s+Dues\s+Minimum\s+Amount\s+Due\s+(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            r'Payment\s+Due\s+Date[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
        ]
        results['due_date'] = self._find_first_match(text, patterns, format_func=self._format_date)
        
        # Card Number: Card No: 5228 52XX XXXX 0591
        patterns = [
            r'Card\s+No[:\s]+\d{4}\s+\d{2}XX\s+XXXX\s+(\d{4})',
        ]
        results['last_4_digits'] = self._find_first_match(text, patterns)
        
        # Credit Limit - First number after "Credit Limit Available Credit Limit"
        patterns = [
            r'Credit\s+Limit\s+Available\s+Credit\s+Limit[^\d]+(\d{1},?\d{2},\d{3})',
        ]
        results['credit_limit'] = self._find_first_match(text, patterns, format_func=self._clean_amount)
        
        # Available Credit - For OCR, look for pattern with comma: 2,56,760.00
        # OCR has the correct value!
        if method == "OCR":
            patterns = [
                r'Available\s+Credit\s+Limit[^\d]+\d{1},?\d{2},\d{3}[^\d]+(\d{1},\d{2},\d{3}(?:\.\d{2})?)',
                r'Credit\s+Limit[^\d]+\d{1},?\d{2},\d{3}[^\d]+(\d{1},\d{2},\d{3}(?:\.\d{2})?)',
            ]
        else:
            # PyPDF2 shows 23,519 which might be wrong
            patterns = [
                r'Credit\s+Limit\s+Available\s+Credit\s+Limit[^\d]+\d{1},?\d{2},\d{3}\s+([0-9,]+)',
            ]
        results['available_credit'] = self._find_first_match(text, patterns, format_func=self._clean_amount)
        
        # Statement Date
        patterns = [
            r'Statement\s+Date[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
        ]
        results['statement_date'] = self._find_first_match(text, patterns, format_func=self._format_date)
        
        return results
    
    def _parse_icici(self, text: str, method: str) -> Dict[str, Optional[str]]:
        """Parse ICICI Bank statement
        OCR shows TWO "Summary" lines:
        1. Summary 3,410.51 6,481.76 0.00 4,009.75 (Account Summary - WRONG)
        2. Summary 83,000.00 77,115.48 (Credit Summary - CORRECT!)
        
        Need to match the one AFTER "Credit Limit Available Credit"
        """
        results = {}
        
        # Due Date - Only from PyPDF2 (OCR has wrong date)
        patterns = [
            r'Due\s+Date\s*:\s+(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
        ]
        results['due_date'] = self._find_first_match(text, patterns, format_func=self._format_date)
        
        # Card Number
        patterns = [
            r'\d{4}\s+XXXX\s+XXXX\s+(\d{3,4})',
        ]
        matches = re.findall(patterns[0], text, re.IGNORECASE)
        if matches:
            results['last_4_digits'] = matches[-1].zfill(4)
        
        # Credit Limit and Available Credit
        # MUST match the line AFTER "Credit Limit Available Credit"
        # Pattern: Credit Limit Available Credit ... Summary 83,000.00 77,115.48
        patterns = [
            # Match: Credit [Credit] Limit Available Credit ... Summary XX,XXX.XX XX,XXX.XX
            r'Credit\s+(?:Credit\s+)?Limit\s+Available\s+Credit[^S]*?Summary\s+(\d{1,3},\d{3}(?:\.\d{2})?)\s+(\d{1,3},\d{3}(?:\.\d{2})?)',
            # PyPDF2 format: Credit SummaryCredit Limit Available Credit\n83,000.00 77,115.48
            r'Credit\s+Summary\s*Credit\s+Limit\s+Available\s+Credit[^\d]+(\d{1,3},\d{3}(?:\.\d{2})?)\s+(\d{1,3},\d{3}(?:\.\d{2})?)',
        ]
        
        match = self._find_first_match_obj(text, patterns)
        if match:
            results['credit_limit'] = self._clean_amount(match.group(1))
            results['available_credit'] = self._clean_amount(match.group(2))
        
        # Statement Date
        patterns = [
            r'Statement\s+Date[^\d]{0,50}?(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
        ]
        results['statement_date'] = self._find_first_match(text, patterns, format_func=self._format_date)
        
        return results
    
    def _parse_kotak(self, text: str, method: str) -> Dict[str, Optional[str]]:
        """Parse Kotak Bank statement
        Pattern: Credit Limit(Rs.) Available Credit
                 900,000 380,229.49
        """
        results = {}
        
        # Due Date
        patterns = [
            r'Due\s+Date\s+(\d{1,2}[-/]\w{3}[-/]\d{4})',
        ]
        results['due_date'] = self._find_first_match(text, patterns, format_func=self._format_date)
        
        # Card Number: 414767XXXXXX6705
        patterns = [
            r'\d{6}X+(\d{4})',
        ]
        results['last_4_digits'] = self._find_first_match(text, patterns)
        
        # Credit Limit - First number: 900,000
        patterns = [
            r'Credit\s+Limit\s*\(Rs\.\)\s+Available\s+Credit[^\d]+([0-9,]+(?:\.\d{2})?)',
        ]
        results['credit_limit'] = self._find_first_match(text, patterns, format_func=self._clean_amount)
        
        # Available Credit - Second number: 380,229.49
        patterns = [
            r'Credit\s+Limit\s*\(Rs\.\)\s+Available\s+Credit[^\d]+[0-9,]+(?:\.\d{2})?\s+([0-9,]+(?:\.\d{2})?)',
        ]
        results['available_credit'] = self._find_first_match(text, patterns, format_func=self._clean_amount)
        
        # Statement Date
        patterns = [
            r'Statement\s+Date\s+(\d{1,2}[-/]\w{3}[-/]\d{4})',
        ]
        results['statement_date'] = self._find_first_match(text, patterns, format_func=self._format_date)
        
        return results
    
    def _parse_amex(self, text: str, method: str) -> Dict[str, Optional[str]]:
        """Parse American Express statement
        Pattern: Credit Summary Credit Limit Rs Available Credit Limit Rs
                 At January 14, 2024 470,000.00 257,545.52
        """
        results = {}
        
        # Due Date: February 1, 2024
        patterns = [
            r'Due\s+by\s+(\w+\s+\d{1,2},?\s+\d{4})',
            r'Minimum\s+Payment:\s+Rs\s+[0-9,]+(?:\.\d{2})?\s+Due\s+by\s+(\w+\s+\d{1,2},?\s+\d{4})',
        ]
        results['due_date'] = self._find_first_match(text, patterns, format_func=self._format_date)
        
        # Membership Number: XXXX-XXXXXX-01007 (last 5 digits)
        patterns = [
            r'XXXX-XXXX+-(\d{5})',
            r'Membership\s+Number[^\d]+XXXX-XXXX+-(\d{5})',
        ]
        results['last_4_digits'] = self._find_first_match(text, patterns)
        
        # Credit Limit: Pattern shows 470,000.00 257,545.52 on same line
        patterns = [
            r'Credit\s+Summary\s+Credit\s+Limit\s+Rs[^\d]+Available\s+Credit\s+Limit\s+Rs[^\d]+At[^\d]+\d{1,2}[/-]\d{1,2}[/-]\d{4}\s+([0-9,]+(?:\.\d{2})?)',
            r'At\s+\w+\s+\d{1,2},?\s+\d{4}\s+([0-9,]+(?:\.\d{2})?)\s+[0-9,]+(?:\.\d{2})?',
        ]
        results['credit_limit'] = self._find_first_match(text, patterns, format_func=self._clean_amount)
        
        # Available Credit Limit: Second number
        patterns = [
            r'Credit\s+Summary\s+Credit\s+Limit\s+Rs[^\d]+Available\s+Credit\s+Limit\s+Rs[^\d]+At[^\d]+\d{1,2}[/-]\d{1,2}[/-]\d{4}\s+[0-9,]+(?:\.\d{2})?\s+([0-9,]+(?:\.\d{2})?)',
            r'At\s+\w+\s+\d{1,2},?\s+\d{4}\s+[0-9,]+(?:\.\d{2})?\s+([0-9,]+(?:\.\d{2})?)',
        ]
        results['available_credit'] = self._find_first_match(text, patterns, format_func=self._clean_amount)
        
        # Statement Date: From "Membership Number Date" field
        patterns = [
            r'Membership\s+Number\s+Date[^\d]+XXXX-XXXX+-\d{5}\s+(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            r'Date[^\d]+(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
        ]
        results['statement_date'] = self._find_first_match(text, patterns, format_func=self._format_date)
        
        return results
    
    def _parse_capital_one(self, text: str, method: str) -> Dict[str, Optional[str]]:
        """Parse Capital One statement
        Pattern: Available to spend as
                 at 05/10/24
                 £780.74
        """
        results = {}
        
        # Due Date: It's due on 31 Oct 24
        patterns = [
            r"It'?s\s+due\s+on\s+(\d{1,2}\s+\w{3}\s+\d{2,4})",
        ]
        results['due_date'] = self._find_first_match(text, patterns, format_func=self._format_date)
        
        # Card Number: **** **** **** 4811
        patterns = [
            r'\*{4}\s+\*{4}\s+\*{4}\s+(\d{4})',
        ]
        results['last_4_digits'] = self._find_first_match(text, patterns)
        
        # Credit Limit
        patterns = [
            r'Credit\s+limit[^\d]+£([0-9,]+(?:\.\d{2})?)',
        ]
        results['credit_limit'] = self._find_first_match(text, patterns, format_func=self._clean_amount)
        
        # Available to spend - handle newlines between "as" and "at"
        patterns = [
            r'Available\s+to\s+spend\s+as[^\d£]*at[^\d]+\d{2}/\d{2}/\d{2}[^\d£]+£([0-9,]+(?:\.\d{2})?)',
            r'Available\s+to\s+spend[^\d£]+£([0-9,]+(?:\.\d{2})?)',
        ]
        results['available_credit'] = self._find_first_match(text, patterns, format_func=self._clean_amount)
        
        # Statement Date: Statement date 5 October 24
        patterns = [
            r'Statement\s+date[^\d]+(\d{1,2}\s+\w+\s+\d{2,4})',
        ]
        results['statement_date'] = self._find_first_match(text, patterns, format_func=self._format_date)
        
        return results
    
    def _find_first_match(self, text: str, patterns: List[str], format_func=None) -> Optional[str]:
        """Try multiple patterns and return first match"""
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                value = match.group(1)
                return format_func(value) if format_func else value
        return None
    
    def _find_first_match_obj(self, text: str, patterns: List[str]) -> Optional[re.Match]:
        """Try multiple patterns and return first match object"""
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                return match
        return None
    
    def _combine_results(self, regex_results: Dict, ocr_results: Dict, bank: str) -> Dict:
        """Combine results with bank-specific logic"""
        final = {}
        
        for key in ['due_date', 'last_4_digits', 'credit_limit', 'available_credit', 'statement_date']:
            # Bank-specific logic
            if bank == "HDFC" and key == "available_credit":
                # OCR is more accurate for HDFC available credit
                final[key] = ocr_results.get(key) or regex_results.get(key)
            elif bank == "ICICI":
                if key == "due_date":
                    # PyPDF2 is correct for ICICI due date (OCR has error)
                    final[key] = regex_results.get(key) or ocr_results.get(key)
                elif key in ["credit_limit", "available_credit", "statement_date"]:
                    # OCR has the credit values for ICICI
                    final[key] = ocr_results.get(key) or regex_results.get(key)
                else:
                    final[key] = regex_results.get(key) or ocr_results.get(key)
            else:
                # Default: prefer regex (PyPDF2), fallback to OCR
                final[key] = regex_results.get(key) or ocr_results.get(key)
        
        return final
    
    def _clean_amount(self, amount_str: str) -> str:
        """Clean and format amount string"""
        if not amount_str:
            return None
        # Remove everything except digits, commas, and decimal points
        cleaned = re.sub(r'[^\d,.]', '', amount_str)
        return cleaned.strip() if cleaned else None
    
    def _format_date(self, date_str: str) -> Optional[str]:
        """Format date to standard format (YYYY-MM-DD)"""
        if not date_str:
            return None
        
        date_str = date_str.strip()
        
        date_formats = [
            '%d/%m/%Y', '%d-%m-%Y', '%d/%m/%y', '%d-%m-%y',
            '%d %b %Y', '%d-%b-%Y', '%d %B %Y', '%d-%B-%Y',
            '%B %d, %Y', '%b %d, %Y', '%d %b %y',
            '%d %B %y', '%d %b %Y', '%d %B %Y',
            '%d %b-%Y', '%d-%b %Y',
            '%d %B %y', '%d-%B-%Y',
        ]
        
        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(date_str, fmt)
                if parsed_date.year < 100:
                    if parsed_date.year < 50:
                        parsed_date = parsed_date.replace(year=parsed_date.year + 2000)
                    else:
                        parsed_date = parsed_date.replace(year=parsed_date.year + 1900)
                return parsed_date.strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        logger.warning(f"Could not parse date: {date_str}")
        return date_str


# Usage Example
if __name__ == "__main__":
    import sys
    
    parser = CreditCardParser()
    
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        pdf_path = "path/to/credit_card_statement.pdf"
    
    try:
        result = parser.parse_statement(pdf_path)
        
        print("\n" + "="*60)
        print("CREDIT CARD STATEMENT PARSER - RESULTS")
        print("="*60)
        print(f"Bank: {result.get('bank', 'Unknown')}")
        print(f"Due Date: {result.get('due_date', 'Not found')}")
        print(f"Last 4 Digits: {result.get('last_4_digits', 'Not found')}")
        print(f"Credit Limit: {result.get('credit_limit', 'Not found')}")
        print(f"Available Credit: {result.get('available_credit', 'Not found')}")
        print(f"Statement Date: {result.get('statement_date', 'Not found')}")
        print("="*60 + "\n")
        
    except FileNotFoundError:
        print(f"Error: File not found - {pdf_path}")
        print("Usage: python parser.py <path_to_pdf>")
    except Exception as e:
        print(f"Error processing statement: {e}")
        import traceback
        traceback.print_exc()