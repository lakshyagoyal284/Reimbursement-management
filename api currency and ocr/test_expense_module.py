#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for expense_reimbursement module functionality
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'expense_reimbursement'))

import requests
import pytesseract
from PIL import Image
import io
import base64

def test_currency_api():
    """Test currency conversion API"""
    print("=== Testing Currency API ===")
    
    try:
        # Test exchange rate API
        base_currency = 'USD'
        url = f'https://api.exchangerate-api.com/v4/latest/{base_currency}'
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        print(f"Base currency: {base_currency}")
        print(f"Rates available for: {len(data.get('rates', {}))} currencies")
        
        # Test conversion
        amount = 100.0
        from_currency = 'USD'
        to_currency = 'EUR'
        
        if to_currency in data.get('rates', {}):
            converted_amount = amount * data['rates'][to_currency]
            print(f"Converted {amount} {from_currency} to {converted_amount:.2f} {to_currency}")
        else:
            print(f"Currency {to_currency} not found in rates")
            
    except Exception as e:
        print(f"Currency API test failed: {e}")

def test_countries_api():
    """Test countries API for currency mapping"""
    print("\n=== Testing Countries API ===")
    
    try:
        url = 'https://restcountries.com/v3.1/all?fields=name,currencies'
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        countries = response.json()
        
        print(f"Retrieved data for {len(countries)} countries")
        
        # Find some examples
        us_dollar_countries = []
        euro_countries = []
        
        for country in countries[:20]:  # Check first 20 countries
            currencies = country.get('currencies', {})
            country_name = country.get('name', {}).get('common', '')
            
            for currency_code, currency_info in currencies.items():
                if currency_code == 'USD':
                    us_dollar_countries.append(country_name)
                elif currency_code == 'EUR':
                    euro_countries.append(country_name)
        
        print(f"Countries using USD: {us_dollar_countries[:5]}")
        print(f"Countries using EUR: {euro_countries[:5]}")
        
    except Exception as e:
        print(f"Countries API test failed: {e}")

def test_ocr_functionality():
    """Test OCR functionality (without actual image)"""
    print("\n=== Testing OCR Setup ===")
    
    try:
        # Check if Tesseract is available
        try:
            pytesseract.get_tesseract_version()
            print(f"Tesseract version: {pytesseract.get_tesseract_version()}")
        except Exception as e:
            print(f"Tesseract not found: {e}")
            print("Please install Tesseract OCR from: https://github.com/UB-Mannheim/tesseract/wiki")
            return
        
        # Test with a simple text image creation
        try:
            # Create a simple test image with text
            from PIL import ImageDraw, ImageFont
            
            # Create a blank image
            img = Image.new('RGB', (400, 200), color='white')
            draw = ImageDraw.Draw(img)
            
            # Add some text
            text = "Restaurant Bill\nTotal: $25.50\nDate: 03/29/2026"
            draw.text((10, 10), text, fill='black')
            
            # Test OCR on the created image
            extracted_text = pytesseract.image_to_string(img)
            print(f"OCR extracted text:\n{extracted_text}")
            
        except Exception as e:
            print(f"OCR test failed: {e}")
            
    except Exception as e:
        print(f"OCR setup test failed: {e}")

def simulate_receipt_parsing():
    """Simulate receipt parsing with sample text"""
    print("\n=== Simulating Receipt Parsing ===")
    
    sample_receipt_text = """
    RESTAURANT NAME
    123 Main Street
    New York, NY 10001
    
    Date: 03/29/2026
    Time: 12:30 PM
    
    Items:
    Burger............$15.99
    Fries.............$4.50
    Soda..............$2.50
    
    Subtotal: $22.99
    Tax: $2.30
    Total: $25.29
    
    Paid by: Credit Card
    Thank you for visiting!
    """
    
    import re
    
    # Parse amount
    amount_patterns = [
        r'Total[:\s]*\$?(\d+(?:\.\d{2})?)',
        r'\$?(\d+(?:\.\d{2})?)\s*Total',
    ]
    
    amount = 0.0
    for pattern in amount_patterns:
        match = re.search(pattern, sample_receipt_text, re.IGNORECASE)
        if match:
            amount = float(match.group(1))
            break
    
    # Parse date
    date_pattern = r'Date[:\s]*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})'
    date_match = re.search(date_pattern, sample_receipt_text, re.IGNORECASE)
    date = date_match.group(1) if date_match else ''
    
    # Parse restaurant name
    lines = sample_receipt_text.strip().split('\n')
    restaurant_name = lines[0].strip() if lines else ''
    
    print(f"Parsed Amount: ${amount}")
    print(f"Parsed Date: {date}")
    print(f"Parsed Restaurant: {restaurant_name}")
    print(f"Description: Restaurant bill at {restaurant_name}")

def main():
    """Run all tests"""
    print("Testing Expense Reimbursement Module Components")
    print("=" * 50)
    
    test_currency_api()
    test_countries_api()
    test_ocr_functionality()
    simulate_receipt_parsing()
    
    print("\n" + "=" * 50)
    print("Testing completed!")
    print("\nTo run the full Odoo module:")
    print("1. Install Odoo")
    print("2. Copy expense_reimbursement to Odoo addons directory")
    print("3. Update addon list and install the module")
    print("4. Configure settings and test the functionality")

if __name__ == '__main__':
    main()
