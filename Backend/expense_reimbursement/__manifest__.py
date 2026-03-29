{
    'name': 'Expense Reimbursement',
    'version': '17.0.1.0.0',
    'category': 'Human Resources',
    'summary': 'Expense Reimbursement Management System',
    'description': """
        Expense Reimbursement Management System
        ========================================
        
        This module provides a complete expense reimbursement workflow:
        - Employees can submit expense claims
        - Managers can approve team expenses
        - Admin can provide final approval
        - Role-based security and permissions
    """,
    'author': 'Hackathon Team',
    'depends': ['base', 'hr', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/sequence.xml',
        'data/approval_data.xml',
        'views/expense_views.xml',
        'views/approval_views.xml',
    ],
    'installable': True,
    'application': True,
}
