from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ApprovalStep(models.Model):
    _name = 'approval.step'
    _description = 'Approval Step'
    _order = 'sequence asc, id asc'
    
    expense_id = fields.Many2one('expense.claim', string='Expense Claim', required=True, ondelete='cascade')
    approver_id = fields.Many2one('res.users', string='Approver', required=True)
    sequence = fields.Integer(string='Sequence', required=True)
    is_required = fields.Boolean(string='Required', default=True)
    status = fields.Selection([
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('skipped', 'Skipped')
    ], string='Status', default='pending', tracking=True)
    approval_date = fields.Datetime(string='Approval Date')
    comments = fields.Text(string='Comments')
    is_manager_approver = fields.Boolean(string='Is Manager Approver', default=False)
    
    @api.model
    def create_approval_steps(self, expense_id):
        """Create approval steps based on company rules"""
        expense = self.env['expense.claim'].browse(expense_id)
        steps = []
        
        # Step 1: Manager Approval (if enabled)
        if expense.company_id.enable_manager_approval:
            if expense.manager_id:
                steps.append({
                    'expense_id': expense_id,
                    'approver_id': expense.manager_id.id,
                    'sequence': 1,
                    'is_required': True,
                    'is_manager_approver': True
                })
        
        # Step 2+: Additional Approvers
        additional_approvers = expense.company_id.approval_sequence_ids.filtered(lambda r: r.is_active)
        seq_num = 2
        
        for approver_rule in additional_approvers:
            if approver_rule.condition_met(expense):
                steps.append({
                    'expense_id': expense_id,
                    'approver_id': approver_rule.approver_id.id,
                    'sequence': seq_num,
                    'is_required': approver_rule.is_required,
                    'is_manager_approver': False
                })
                seq_num += 1
        
        return self.create(steps)
    
    def approve_step(self, comments=False):
        """Approve current step"""
        if self.status != 'pending':
            raise UserError(_('This step is not pending for approval.'))
        
        if self.approver_id != self.env.user and not self.env.user.has_group('expense_reimbursement.group_expense_admin'):
            raise UserError(_('You are not authorized to approve this step.'))
        
        self.write({
            'status': 'approved',
            'approval_date': fields.Datetime.now(),
            'comments': comments
        })
        
        # Process next step
        self.expense_id._process_next_approval_step()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Step Approved'),
                'message': _('Approval step completed successfully.'),
                'type': 'success',
            }
        }
    
    def reject_step(self, comments=False):
        """Reject current step"""
        if self.status != 'pending':
            raise UserError(_('This step is not pending for approval.'))
        
        if self.approver_id != self.env.user and not self.env.user.has_group('expense_reimbursement.group_expense_admin'):
            raise UserError(_('You are not authorized to reject this step.'))
        
        self.write({
            'status': 'rejected',
            'approval_date': fields.Datetime.now(),
            'comments': comments
        })
        
        # Reject the entire expense
        self.expense_id.write({'status': 'rejected'})
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Step Rejected'),
                'message': _('Expense claim has been rejected.'),
                'type': 'danger',
            }
        }
