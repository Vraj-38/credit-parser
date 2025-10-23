"""
Debug script to see actual text extracted from PDFs using both PyPDF2 and OCR
This will help identify the correct patterns
"""

import sys
from PyPDF2 import PdfReader
import pytesseract
from pdf2image import convert_from_path
import re

def extract_and_print_text(pdf_path: str):
    """Extract text using both methods and print relevant sections"""
    print("\n" + "="*80)
    print(f"FILE: {pdf_path}")
    print("="*80)
    
    # Method 1: PyPDF2
    print("\n" + "+"*80)
    print("METHOD 1: PyPDF2 TEXT EXTRACTION")
    print("+"*80)
    
    pypdf_text = ""
    try:
        reader = PdfReader(pdf_path)
        
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                pypdf_text += page_text + "\n"
                if i == 0:  # Print first page in detail
                    print(f"\n--- PAGE 1 (First 2000 chars) ---")
                    print(page_text[:2000])
                    print(f"\n... (total page length: {len(page_text)} chars)")
        
        if not pypdf_text:
            print("⚠️ WARNING: No text extracted with PyPDF2")
            
    except Exception as e:
        print(f"❌ Error with PyPDF2: {e}")
    
    # Method 2: OCR
    print("\n" + "+"*80)
    print("METHOD 2: TESSERACT OCR")
    print("+"*80)
    
    ocr_text = ""
    try:
        images = convert_from_path(pdf_path, dpi=300, first_page=1, last_page=2)
        
        for i, image in enumerate(images):
            page_text = pytesseract.image_to_string(image, lang='eng', config='--psm 6')
            ocr_text += page_text + "\n"
            if i == 0:  # Print first page
                print(f"\n--- PAGE 1 (First 2000 chars) ---")
                print(page_text[:2000])
                print(f"\n... (total page length: {len(page_text)} chars)")
        
        if not ocr_text:
            print("⚠️ WARNING: No text extracted with OCR")
            
    except Exception as e:
        print(f"❌ Error with OCR: {e}")
        import traceback
        traceback.print_exc()
    
    # Combine both texts for pattern search
    combined_text = pypdf_text + "\n" + ocr_text
    
    # Search for key patterns in both
    print("\n" + "="*80)
    print("PATTERN ANALYSIS (PyPDF2 vs OCR)")
    print("="*80)
    
    analyze_patterns(pypdf_text, ocr_text)

def analyze_patterns(pypdf_text: str, ocr_text: str):
    """Analyze and compare patterns found in both extraction methods"""
    
    print("\n" + "-"*80)
    print("1. DUE DATE PATTERNS")
    print("-"*80)
    
    due_patterns = [
        (r'Due\s+Date\s*:\s*(\d{1,2}[/-]\d{1,2}[/-]\d{4})', 'Due Date : DD/MM/YYYY'),
        (r'Payment\s+Due\s+Date\s+.*?(\d{1,2}[/-]\d{1,2}[/-]\d{4})', 'Payment Due Date ... DD/MM/YYYY'),
        (r'Due\s+Date\s+(\d{1,2}[-/]\w{3}[-/]\d{4})', 'Due Date DD-Mon-YYYY'),
        (r'Due\s+by\s+(\w+\s+\d{1,2},?\s+\d{4})', 'Due by Month DD, YYYY'),
        (r"It'?s\s+due\s+on\s+(\d{1,2}\s+\w{3}\s+\d{2,4})", "It's due on DD Mon YY"),
        (r'Minimum\s+Payment[^\d]+(\d{1,2}[/-]\d{1,2}[/-]\d{4})', 'Minimum Payment ... DD/MM/YYYY'),
    ]
    
    print("\n📄 PyPDF2:")
    for pattern, desc in due_patterns:
        matches = re.findall(pattern, pypdf_text, re.IGNORECASE)
        if matches:
            print(f"  ✓ {desc}: {matches[:2]}")
    
    print("\n🔍 OCR:")
    for pattern, desc in due_patterns:
        matches = re.findall(pattern, ocr_text, re.IGNORECASE)
        if matches:
            print(f"  ✓ {desc}: {matches[:2]}")
    
    print("\n" + "-"*80)
    print("2. CARD NUMBER PATTERNS")
    print("-"*80)
    
    card_patterns = [
        (r'Card\s+(?:No|Number|Account\s+No)[^\n]*?(\d{4}[\sX*]+\d{4})', 'Card No/Number'),
        (r'(\d{4}\s+X+\s+X+\s+\d{3,4})', 'XXXX XXXX XXXX DDDD'),
        (r'(\d{6}X+\d{4})', 'XXXXXXDDDD'),
        (r'Membership\s+Number[^\d]*(X+-X+-\d{5})', 'Membership Number (Amex)'),
        (r'\*{4}\s+\*{4}\s+\*{4}\s+(\d{4})', '**** **** **** DDDD'),
    ]
    
    print("\n📄 PyPDF2:")
    for pattern, desc in card_patterns:
        matches = re.findall(pattern, pypdf_text, re.IGNORECASE)
        if matches:
            print(f"  ✓ {desc}: {matches[:2]}")
    
    print("\n🔍 OCR:")
    for pattern, desc in card_patterns:
        matches = re.findall(pattern, ocr_text, re.IGNORECASE)
        if matches:
            print(f"  ✓ {desc}: {matches[:2]}")
    
    print("\n" + "-"*80)
    print("3. CREDIT LIMIT PATTERNS")
    print("-"*80)
    
    credit_patterns = [
        (r'Credit\s+Limit[^\n]{0,150}', 'Credit Limit (context)'),
        (r'Available\s+Credit[^\n]{0,150}', 'Available Credit (context)'),
        (r'Credit\s+Summary[^\n]{0,200}', 'Credit Summary (context)'),
    ]
    
    print("\n📄 PyPDF2:")
    for pattern, desc in credit_patterns:
        matches = re.findall(pattern, pypdf_text, re.IGNORECASE | re.DOTALL)
        if matches:
            for match in matches[:2]:
                # Clean up for display
                clean = ' '.join(match.split())
                print(f"  ✓ {desc}:")
                print(f"    {clean[:120]}...")
    
    print("\n🔍 OCR:")
    for pattern, desc in credit_patterns:
        matches = re.findall(pattern, ocr_text, re.IGNORECASE | re.DOTALL)
        if matches:
            for match in matches[:2]:
                # Clean up for display
                clean = ' '.join(match.split())
                print(f"  ✓ {desc}:")
                print(f"    {clean[:120]}...")
    
    print("\n" + "-"*80)
    print("4. STATEMENT DATE PATTERNS")
    print("-"*80)
    
    stmt_patterns = [
        (r'Statement\s+Date[^\n]{0,80}', 'Statement Date (context)'),
        (r'Statement\s+date[^\n]{0,80}', 'statement date (lowercase)'),
        (r'Date[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{4})', 'Date: DD/MM/YYYY'),
    ]
    
    print("\n📄 PyPDF2:")
    for pattern, desc in stmt_patterns:
        matches = re.findall(pattern, pypdf_text, re.IGNORECASE)
        if matches:
            for match in matches[:2]:
                print(f"  ✓ {desc}: {match}")
    
    print("\n🔍 OCR:")
    for pattern, desc in stmt_patterns:
        matches = re.findall(pattern, ocr_text, re.IGNORECASE)
        if matches:
            for match in matches[:2]:
                print(f"  ✓ {desc}: {match}")
    
    print("\n" + "-"*80)
    print("5. LOOKING FOR SPECIFIC NUMBERS (Credit Limits)")
    print("-"*80)
    
    # Look for large numbers that could be credit limits
    number_pattern = r'(?:Rs\.?\s*)?([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{2})?)'
    
    print("\n📄 PyPDF2 - Large numbers found:")
    numbers = re.findall(number_pattern, pypdf_text)
    # Filter for numbers > 10000
    large_nums = [n for n in numbers if ',' in n or (n.replace(',', '').replace('.', '').isdigit() and float(n.replace(',', '')) > 10000)]
    for num in large_nums[:10]:
        print(f"  → {num}")
    
    print("\n🔍 OCR - Large numbers found:")
    numbers = re.findall(number_pattern, ocr_text)
    large_nums = [n for n in numbers if ',' in n or (n.replace(',', '').replace('.', '').isdigit() and float(n.replace(',', '')) > 10000)]
    for num in large_nums[:10]:
        print(f"  → {num}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        extract_and_print_text(sys.argv[1])
    else:
        print("Usage: python debug_parser.py <path_to_pdf>")
        print("\nOr it will run on all PDFs below:")
        
        # Add your PDF paths here
        pdfs = [
            "/Users/vcparikh/Desktop/creditcard_parser/413867735-CreditCardStatement-3.pdf",  # ICICI
            "/Users/vcparikh/Desktop/creditcard_parser/423908303-5228xxxxxxxxxx91-08-06-2019-Hdfc-unlocked-1.pdf",  # HDFC
            "/Users/vcparikh/Desktop/creditcard_parser/641112054-Untitled.pdf",  # KOTAK
            "/Users/vcparikh/Desktop/creditcard_parser/704269324-2024-01-14.pdf",  # AMEX
            "/Users/vcparikh/Desktop/creditcard_parser/808906604-Capital-One-Statement.pdf",  # Capital One
        ]
        
        for pdf in pdfs:
            try:
                extract_and_print_text(pdf)
            except FileNotFoundError:
                print(f"⚠️ File not found: {pdf}")
            except Exception as e:
                print(f"❌ Error processing {pdf}: {e}")