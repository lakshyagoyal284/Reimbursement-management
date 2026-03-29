# Expense Reimbursement Module

Enhanced Odoo expense management module with currency conversion and OCR receipt processing.

## Features

### Currency Conversion
- Real-time currency conversion using ExchangeRate API
- Automatic currency assignment based on company country
- Support for multiple currencies
- Display converted amounts in company currency

### OCR Receipt Processing
- Upload receipt images for automatic data extraction
- Extract amount, date, restaurant name, and description
- Auto-fill expense fields from OCR data
- Support for various receipt formats

## Installation

1. Copy the `expense_reimbursement` folder to your Odoo addons directory
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Update Odoo addons list and install the module

## Dependencies

- requests>=2.25.1
- pytesseract>=0.3.8
- Pillow>=8.0.0

## Usage

### Currency Conversion
1. Set original currency and amount when creating expenses
2. System automatically converts to company currency
3. View conversion rates and converted amounts

### OCR Processing
1. Upload receipt image in expense form
2. Click "Process Receipt OCR" button
3. Review and confirm extracted information
4. Save expense with auto-filled data

## Configuration

Navigate to Settings > Expense Reimbursement to configure:
- Enable/disable currency conversion
- Enable/disable OCR processing

## API Endpoints

- ExchangeRate API: https://api.exchangerate-api.com/v4/latest/{BASE_CURRENCY}
- REST Countries API: https://restcountries.com/v3.1/all?fields=name,currencies
