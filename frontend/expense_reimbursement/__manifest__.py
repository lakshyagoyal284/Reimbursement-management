{
    'name': 'Expense Reimbursement',
    'version': '17.0.1.0.0',
    'category': 'Human Resources',
    'summary': 'Complete expense reimbursement management system',
    'description': """
        Expense Reimbursement Management System
        ========================================
        
        Features:
        - Employee expense submission
        - Manager approval workflow
        - Admin final approval
        - Dashboard with statistics
        - Clean and modern UI
    """,
    'author': 'Your Company',
    'depends': ['base', 'hr'],
    'data': [
        'security/ir.model.access.csv',
        'views/menu.xml',
        'views/expense_views.xml',
        'views/dashboard.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
