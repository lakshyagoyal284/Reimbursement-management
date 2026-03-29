from odoo import models, fields, api


class ResCompany(models.Model):
    _inherit = 'res.company'
    
    # Approval Configuration
    enable_manager_approval = fields.Boolean(string='Enable Manager Approval', default=True)
    enable_multi_level_approval = fields.Boolean(string='Enable Multi-Level Approval', default=False)
    approval_rule_id = fields.Many2one('approval.rule', string='Default Approval Rule')
    approval_sequence_ids = fields.One2many('approval.sequence', 'company_id', string='Approval Sequence')
    
    # Auto-approval Settings
    auto_approve_threshold = fields.Float(string='Auto-approve Threshold', default=0,
                                        help='Expenses below this amount are auto-approved')
    require_receipt_above = fields.Float(string='Require Receipt Above', default=0,
                                       help='Receipt required for expenses above this amount')
    
    # Currency Settings
    default_currency_id = fields.Many2one('res.currency', string='Default Currency',
                                         related='currency_id', readonly=False)
    auto_update_currency_rates = fields.Boolean(string='Auto-update Currency Rates', default=True)
    
    # Employee Management
    auto_create_employee_on_user = fields.Boolean(string='Auto-create Employee on User Creation', default=True)
    default_manager_id = fields.Many2one('res.users', string='Default Manager')
    
    def get_approval_steps_for_expense(self, expense):
        """Get approval steps for a specific expense"""
        steps = []
        
        # Manager approval (if enabled)
        if self.enable_manager_approval and expense.manager_id:
            steps.append({
                'approver_id': expense.manager_id.id,
                'sequence': 1,
                'is_required': True,
                'is_manager_approver': True
            })
        
        # Additional approval steps
        if self.enable_multi_level_approval:
            sequence_num = 2
            for approval_seq in self.approval_sequence_ids:
                if approval_seq.condition_met(expense):
                    steps.append({
                        'approver_id': approval_seq.approver_id.id,
                        'sequence': sequence_num,
                        'is_required': approval_seq.is_required,
                        'is_manager_approver': False
                    })
                    sequence_num += 1
        
        return steps
