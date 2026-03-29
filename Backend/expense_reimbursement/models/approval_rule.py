from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ApprovalRule(models.Model):
    _name = 'approval.rule'
    _description = 'Approval Rule'
    
    name = fields.Char(string='Rule Name', required=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    rule_type = fields.Selection([
        ('percentage', 'Percentage Rule'),
        ('specific_approver', 'Specific Approver Rule'),
        ('hybrid', 'Hybrid Rule'),
        ('unanimous', 'Unanimous Approval')
    ], string='Rule Type', required=True, default='unanimous')
    
    # Percentage Rule Fields
    percentage_threshold = fields.Float(string='Approval Percentage (%)', help='Minimum percentage of approvers required')
    
    # Specific Approver Rule Fields
    specific_approver_id = fields.Many2one('res.users', string='Specific Approver', help='If this person approves, expense is auto-approved')
    auto_approve_on_specific = fields.Boolean(string='Auto-approve on Specific', default=True)
    
    # Hybrid Rule Fields
    use_percentage = fields.Boolean(string='Use Percentage', default=True)
    use_specific = fields.Boolean(string='Use Specific Approver', default=True)
    
    # Common Fields
    min_approvers = fields.Integer(string='Minimum Approvers', default=1)
    is_active = fields.Boolean(string='Active', default=True)
    amount_threshold = fields.Float(string='Amount Threshold', help='Apply rule for expenses above this amount')
    
    def evaluate_rule(self, approval_steps):
        """Evaluate if approval rule is satisfied"""
        if not self.is_active:
            return False
            
        total_steps = len(approval_steps)
        approved_steps = len(approval_steps.filtered(lambda s: s.status == 'approved'))
        
        if self.rule_type == 'percentage':
            return self._evaluate_percentage_rule(approved_steps, total_steps)
        elif self.rule_type == 'specific_approver':
            return self._evaluate_specific_approver_rule(approval_steps)
        elif self.rule_type == 'hybrid':
            return self._evaluate_hybrid_rule(approval_steps, total_steps)
        elif self.rule_type == 'unanimous':
            return self._evaluate_unanimous_rule(approved_steps, total_steps)
        
        return False
    
    def _evaluate_percentage_rule(self, approved, total):
        """Evaluate percentage-based rule"""
        if total == 0:
            return False
        approval_percentage = (approved / total) * 100
        return approval_percentage >= self.percentage_threshold
    
    def _evaluate_specific_approver_rule(self, approval_steps):
        """Evaluate specific approver rule"""
        if not self.specific_approver_id:
            return False
        
        specific_approval = approval_steps.filtered(
            lambda s: s.approver_id == self.specific_approver_id and s.status == 'approved'
        )
        
        if self.auto_approve_on_specific and specific_approval:
            return True
        
        return False
    
    def _evaluate_hybrid_rule(self, approval_steps, total):
        """Evaluate hybrid rule (percentage OR specific approver)"""
        percentage_met = False
        specific_met = False
        
        # Check percentage condition
        if self.use_percentage:
            percentage_met = self._evaluate_percentage_rule(
                len(approval_steps.filtered(lambda s: s.status == 'approved')),
                total
            )
        
        # Check specific approver condition
        if self.use_specific:
            specific_met = self._evaluate_specific_approver_rule(approval_steps)
        
        # Hybrid: either condition must be met
        return percentage_met or specific_met
    
    def _evaluate_unanimous_rule(self, approved, total):
        """Evaluate unanimous approval rule"""
        return approved == total and total > 0


class ApprovalSequence(models.Model):
    _name = 'approval.sequence'
    _description = 'Approval Sequence'
    _order = 'sequence asc'
    
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    approver_id = fields.Many2one('res.users', string='Approver', required=True)
    sequence = fields.Integer(string='Sequence', required=True)
    is_required = fields.Boolean(string='Required', default=True)
    is_active = fields.Boolean(string='Active', default=True)
    amount_min = fields.Float(string='Minimum Amount', default=0)
    amount_max = fields.Float(string='Maximum Amount')
    expense_category_ids = fields.Many2many('expense.category', string='Expense Categories')
    
    def condition_met(self, expense):
        """Check if this approval step applies to the expense"""
        if not self.is_active:
            return False
        
        # Check amount conditions
        if expense.company_currency_amount < self.amount_min:
            return False
        
        if self.amount_max and expense.company_currency_amount > self.amount_max:
            return False
        
        # Check expense category
        if self.expense_category_ids and expense.category_id not in self.expense_category_ids:
            return False
        
        return True
