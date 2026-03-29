# -*- coding: utf-8 -*-
{
    'name': 'Expense Reimbursement with Currency and OCR',
    'version': '1.0',
    'category': 'Human Resources',
    'summary': 'Expense management with currency conversion and OCR receipt processing',
    'description': """
Enhanced expense reimbursement module featuring:
- Currency conversion using ExchangeRate API
- Automatic currency assignment based on company country
- OCR receipt processing using Tesseract
- Auto-fill expense fields from receipt images
""",
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'license': 'LGPL-3',
    'depends': ['base', 'hr_expense'],
    'data': [
        'security/ir.model.access.csv',
        'views/expense_claim_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'external_dependencies': {
        'python': ['requests', 'pytesseract', 'Pillow'],
    },
}
