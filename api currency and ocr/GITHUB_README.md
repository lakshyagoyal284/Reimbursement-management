# API, Currency & OCR - Expense Reimbursement

Enhanced Odoo expense management module with currency conversion and OCR receipt processing.

## 🚀 Features

### 💱 Currency Conversion
- Real-time currency conversion using [ExchangeRate API](https://api.exchangerate-api.com/v4/latest/{BASE_CURRENCY})
- Automatic currency assignment based on company country using [REST Countries API](https://restcountries.com/v3.1/all?fields=name,currencies)
- Support for multiple currencies
- Display converted amounts in company currency

### 🧾 OCR Receipt Processing
- Upload receipt images for automatic data extraction
- Extract amount, date, restaurant name, and description
- Auto-fill expense fields from OCR data
- Support for various receipt formats
- Python Tesseract OCR integration

## 📋 Requirements

- **Python Dependencies:**
  - requests>=2.25.1
  - pytesseract>=0.3.8
  - Pillow>=8.0.0

- **Odoo Dependencies:**
  - base
  - hr_expense

- **System Requirements:**
  - Tesseract OCR engine

## 🛠️ Installation

1. **Clone this repository:**
   ```bash
   git clone https://github.com/lakshyagoyal284/Reimbursement-management.git
   cd Reimbursement-management
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Tesseract OCR:**
   - **Windows:** Download from [UB-Mannheim Tesseract](https://github.com/UB-Mannheim/tesseract/wiki)
   - **Ubuntu/Debian:** `sudo apt-get install tesseract-ocr`
   - **macOS:** `brew install tesseract`

4. **Copy to Odoo addons directory:**
   ```bash
   cp -r expense_reimbursement /path/to/odoo/addons/
   ```

5. **Update Odoo addons list and install the module**

## 🎯 Usage

### Currency Conversion
1. Set original currency and amount when creating expenses
2. System automatically converts to company currency
3. View conversion rates and converted amounts

### OCR Processing
1. Upload receipt image in expense form
2. Click "Process Receipt OCR" button
3. Review and confirm extracted information
4. Save expense with auto-filled data

## 🔧 Configuration

Navigate to **Settings > Expense Reimbursement** to configure:
- Enable/disable currency conversion
- Enable/disable OCR processing

## 📁 Module Structure

```
expense_reimbursement/
├── __init__.py
├── __manifest__.py
├── requirements.txt
├── README.md
├── models/
│   ├── __init__.py
│   ├── currency_api.py      # Currency conversion functions
│   ├── ocr.py              # OCR processing functions
│   └── expense_claim.py    # Enhanced expense model
├── views/
│   ├── __init__.py
│   ├── expense_claim_views.xml
│   └── res_config_settings_views.xml
└── security/
    ├── __init__.py
    └── ir.model.access.csv
```

## 🔌 API Integration

### Currency API
- **Endpoint:** `https://api.exchangerate-api.com/v4/latest/{BASE_CURRENCY}`
- **Function:** `convert_currency(amount, from_currency, to_currency)`
- **Returns:** Converted amount in company currency

### Countries API
- **Endpoint:** `https://restcountries.com/v3.1/all?fields=name,currencies`
- **Function:** Auto-assign currency based on company country
- **Returns:** Currency code for given country

### OCR Functions
- **Function:** `read_receipt(receipt_image_data)`
- **Extracts:** Amount, Date, Restaurant name, Description
- **Technology:** Python Tesseract + PIL

## 🧪 Testing

Run the demo script to test functionality:

```bash
python demo_expense_functions.py
```

## 📊 Demo Results

- ✅ Currency Conversion: 100 USD → 86.80 EUR
- ✅ Country Detection: US → USD, Germany → EUR, Japan → JPY
- ✅ OCR Processing: Extracts amount, date, merchant from receipts
- ✅ Complete Workflow: Upload → OCR → Convert → Save

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

This project is licensed under the LGPL-3 License.

## 🔗 Links

- [GitHub Repository](https://github.com/lakshyagoyal284/Reimbursement-management)
- [ExchangeRate API](https://www.exchangerate-api.com/)
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
- [Odoo](https://www.odoo.com/)

---

**Developed by Lakshya Goyal**
**Expense Reimbursement with API, Currency & OCR Integration**
