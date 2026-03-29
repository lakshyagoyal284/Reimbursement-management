# -*- coding: utf-8 -*-

import pytesseract
import logging
import re
from PIL import Image
from io import BytesIO
from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class OCRProcessor(models.Model):
    _name = 'ocr.processor'
    _description = 'OCR Receipt Processor'

    @api.model
    def read_receipt(self, receipt_image_data):
        """
        Extract information from receipt image using OCR
        """
        try:
            # Convert binary data to PIL Image
            image = Image.open(BytesIO(receipt_image_data))
            
            # Extract text using Tesseract OCR
            extracted_text = pytesseract.image_to_string(image)
            
            # Parse extracted text for expense information
            expense_data = self.parse_receipt_text(extracted_text)
            
            return expense_data
            
        except Exception as e:
            _logger.error(f"OCR processing failed: {e}")
            raise UserError(f"OCR processing failed: {e}")

    @api.model
    def parse_receipt_text(self, text):
        """
        Parse OCR text to extract expense information
        """
        expense_data = {
            'amount': 0.0,
            'date': False,
            'restaurant_name': '',
            'description': '',
        }

        lines = text.strip().split('\n')
        
        # Extract amount (look for currency symbols and numbers)
        amount_patterns = [
            r'[$€£¥]\s*(\d+(?:\.\d{2})?)',
            r'(\d+(?:\.\d{2})?)\s*[$€£¥]',
            r'Total[:\s]*(\d+(?:\.\d{2})?)',
            r'Amount[:\s]*(\d+(?:\.\d{2})?)',
            r'Sum[:\s]*(\d+(?:\.\d{2})?)',
        ]
        
        for line in lines:
            for pattern in amount_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    try:
                        expense_data['amount'] = float(match.group(1))
                        break
                    except ValueError:
                        continue
            if expense_data['amount'] > 0:
                break

        # Extract date (various date formats)
        date_patterns = [
            r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
            r'(\d{2,4}[-/]\d{1,2}[-/]\d{1,2})',
            r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4})',
            r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{2,4})',
        ]
        
        for line in lines:
            for pattern in date_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    expense_data['date'] = match.group(1)
                    break
            if expense_data['date']:
                break

        # Extract restaurant/merchant name (usually first few lines)
        # Look for common restaurant/merchant indicators
        merchant_keywords = ['restaurant', 'cafe', 'hotel', 'store', 'shop', 'market', 'diner']
        
        for i, line in enumerate(lines[:5]):  # Check first 5 lines
            line = line.strip()
            if len(line) > 3 and not any(keyword in line.lower() for keyword in ['total', 'amount', 'tax', 'cash', 'card']):
                # Check if it looks like a business name
                if any(char.isupper() for char in line) and not line.startswith('0'):
                    expense_data['restaurant_name'] = line[:50]  # Limit length
                    break

        # Extract description (could be items or general description)
        item_patterns = [
            r'(\d+\s+[A-Za-z\s]+(?:\d+(?:\.\d{2})?)?)',
            r'([A-Za-z\s]+(?:\d+(?:\.\d{2})?)?)',
        ]
        
        description_items = []
        for line in lines:
            line = line.strip()
            if len(line) > 5 and not any(keyword in line.lower() for keyword in ['total', 'tax', 'subtotal', 'cash', 'card']):
                if re.search(r'\d', line) and any(c.isalpha() for c in line):
                    description_items.append(line[:30])  # Limit length
        
        if description_items:
            expense_data['description'] = ', '.join(description_items[:3])  # Take first 3 items
        else:
            expense_data['description'] = f'Receipt from {expense_data["restaurant_name"]}' if expense_data['restaurant_name'] else 'Receipt expense'

        return expense_data

    @api.model
    def process_receipt_attachment(self, attachment_id):
        """
        Process receipt from attachment record
        """
        attachment = self.env['ir.attachment'].browse(attachment_id)
        if not attachment.exists():
            raise UserError("Attachment not found")
        
        if not attachment.datas:
            raise UserError("Attachment has no data")
        
        return self.read_receipt(attachment.datas)
