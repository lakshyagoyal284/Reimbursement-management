from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import datetime


class ExpenseClaim(models.Model):
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _name = 'expense.claim'
    _description = 'Expense Claim'
    _order = 'date desc, id desc'
    _rec_name = 'name'

    name = fields.Char(string='Reference', required=True, copy=False, readonly=True, default='/')
    employee_id = fields.Many2one('res.users', string='Employee', required=True, default=lambda self: self.env.user)
    manager_id = fields.Many2one('res.users', string='Manager', required=True)
    amount = fields.Float(string='Amount', required=True, digits=(16, 2))
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, 
                                  default=lambda self: self.env.company.currency_id)
    company_currency_amount = fields.Float(string='Amount in Company Currency', digits=(16, 2), compute='_compute_company_currency_amount', store=True)
    description = fields.Text(string='Description', required=True)
    date = fields.Date(string='Date', required=True, default=fields.Date.today())
    category_id = fields.Many2one('expense.category', string='Category', required=True)
    
    # Enhanced status with multi-level support
    status = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('in_approval', 'In Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('paid', 'Paid')
    ], string='Status', default='draft', readonly=True, tracking=True)
    
    comment = fields.Text(string='Comments')
    
    # Approval workflow fields
    approval_step_ids = fields.One2many('approval.step', 'expense_id', string='Approval Steps')
    current_step = fields.Integer(string='Current Step', compute='_compute_current_step', store=True)
    total_steps = fields.Integer(string='Total Steps', compute='_compute_total_steps', store=True)
    approval_rule_id = fields.Many2one('approval.rule', string='Approval Rule')
    
    # Receipt fields
    receipt_attachment_ids = fields.One2many('ir.attachment', compute='_compute_receipt_attachments')
    has_receipt = fields.Boolean(string='Has Receipt', compute='_compute_has_receipt')
    
    # OCR fields (for API team integration)
    ocr_data = fields.Text(string='OCR Data')
    ocr_processed = fields.Boolean(string='OCR Processed', default=False)
    
    @api.depends('amount', 'currency_id', 'date')
    def _compute_company_currency_amount(self):
        for record in self:
            if record.currency_id:
                company_currency = self.env.company.currency_id
                if record.currency_id != company_currency:
                    record.company_currency_amount = record.currency_id._convert(
                        record.amount, company_currency, self.env.company, record.date or fields.Date.today()
                    )
                else:
                    record.company_currency_amount = record.amount
            else:
                record.company_currency_amount = record.amount
    
    @api.depends('approval_step_ids.status')
    def _compute_current_step(self):
        for record in self:
            if record.approval_step_ids:
                pending_steps = record.approval_step_ids.filtered(lambda s: s.status == 'pending')
                if pending_steps:
                    record.current_step = min(pending_steps.mapped('sequence'))
                else:
                    record.current_step = 0
            else:
                record.current_step = 0
    
    @api.depends('approval_step_ids')
    def _compute_total_steps(self):
        for record in self:
            record.total_steps = len(record.approval_step_ids)
    
    def _compute_receipt_attachments(self):
        for record in self:
            attachments = self.env['ir.attachment'].search([
                ('res_model', '=', 'expense.claim'),
                ('res_id', '=', record.id),
                ('name', 'ilike', 'receipt')
            ])
            record.receipt_attachment_ids = attachments
    
    def _compute_has_receipt(self):
        for record in self:
            record.has_receipt = bool(record.receipt_attachment_ids)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code('expense.claim') or '/'
        expenses = super().create(vals_list)
        
        # Auto-approval check
        for expense in expenses:
            if expense._should_auto_approve():
                expense.write({'status': 'approved'})
        
        return expenses
    
    def _should_auto_approve(self):
        """Check if expense should be auto-approved"""
        company = self.env.company
        
        # Check auto-approve threshold
        if company.auto_approve_threshold > 0:
            if self.company_currency_amount <= company.auto_approve_threshold:
                return True
        
        # Check category auto-approve
        if self.category_id and self.category_id.auto_approve_amount > 0:
            if self.company_currency_amount <= self.category_id.auto_approve_amount:
                return True
        
        return False

    def submit_expense(self):
        if self.employee_id != self.env.user:
            raise UserError(_('Only the employee can submit their own expense claim.'))
        if self.status != 'draft':
            raise UserError(_('Only draft expenses can be submitted.'))
        
        if not self.manager_id:
            raise UserError(_('Please assign a manager before submitting the expense.'))
        
        # Check if receipt is required
        if self._receipt_required():
            if not self.has_receipt:
                raise UserError(_('Receipt is required for expenses above the threshold.'))
        
        # Create approval steps
        if not self._should_auto_approve():
            self.env['approval.step'].create_approval_steps(self.id)
            self.write({'status': 'submitted'})
        else:
            self.write({'status': 'approved'})
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Expense claim submitted successfully.' if self.status == 'submitted' else 'Expense claim auto-approved.'),
                'type': 'success',
            }
        }
    
    def _receipt_required(self):
        """Check if receipt is required for this expense"""
        company = self.env.company
        
        # Company threshold
        if company.require_receipt_above > 0:
            if self.company_currency_amount > company.require_receipt_above:
                return True
        
        # Category requirement
        if self.category_id and self.category_id.requires_receipt:
            return True
        
        return False

    def _process_next_approval_step(self):
        """Process the next approval step in the workflow"""
        if not self.approval_step_ids:
            return
        
        # Get all pending steps for current sequence
        current_sequence = self.current_step
        if current_sequence == 0:
            # All steps completed
            self._evaluate_final_approval()
            return
        
        pending_steps = self.approval_step_ids.filtered(
            lambda s: s.sequence == current_sequence and s.status == 'pending'
        )
        
        if not pending_steps:
            # Move to next sequence
            next_sequence = current_sequence + 1
            next_pending = self.approval_step_ids.filtered(
                lambda s: s.sequence == next_sequence and s.status == 'pending'
            )
            
            if not next_pending:
                # All steps completed
                self._evaluate_final_approval()
            else:
                self.write({'status': 'in_approval'})
                # Notify next approvers
                self._notify_next_approvers(next_pending)
    
    def _evaluate_final_approval(self):
        """Evaluate final approval based on rules"""
        if not self.approval_rule_id:
            # Default: all steps must be approved
            all_approved = all(step.status == 'approved' for step in self.approval_step_ids)
            if all_approved:
                self.write({'status': 'approved'})
            else:
                rejected_steps = self.approval_step_ids.filtered(lambda s: s.status == 'rejected')
                if rejected_steps:
                    self.write({'status': 'rejected'})
        else:
            # Use approval rule
            rule_satisfied = self.approval_rule_id.evaluate_rule(self.approval_step_ids)
            if rule_satisfied:
                self.write({'status': 'approved'})
            else:
                # Check if any step is rejected
                rejected_steps = self.approval_step_ids.filtered(lambda s: s.status == 'rejected')
                if rejected_steps:
                    self.write({'status': 'rejected'})
                else:
                    self.write({'status': 'in_approval'})
    
    def _notify_next_approvers(self, approval_steps):
        """Notify next approvers in workflow"""
        for step in approval_steps:
            self.message_post(
                body=_('Expense <b>%s</b> is waiting for your approval.') % self.name,
                partner_ids=[step.approver_id.partner_id.id]
            )
    
    def approve_current_step(self, comments=False):
        """Approve current approval step"""
        current_steps = self.approval_step_ids.filtered(
            lambda s: s.sequence == self.current_step and s.status == 'pending'
        )
        
        if not current_steps:
            raise UserError(_('No pending approval steps found.'))
        
        # Find the step for current user
        user_step = current_steps.filtered(lambda s: s.approver_id == self.env.user)
        if not user_step:
            raise UserError(_('You are not an approver for this expense.'))
        
        return user_step.approve_step(comments)
    
    def reject_current_step(self, comments=False):
        """Reject current approval step"""
        current_steps = self.approval_step_ids.filtered(
            lambda s: s.sequence == self.current_step and s.status == 'pending'
        )
        
        if not current_steps:
            raise UserError(_('No pending approval steps found.'))
        
        # Find the step for current user
        user_step = current_steps.filtered(lambda s: s.approver_id == self.env.user)
        if not user_step:
            raise UserError(_('You are not an approver for this expense.'))
        
        return user_step.reject_step(comments)
    
    # Legacy methods for backward compatibility
    def manager_approve(self):
        return self.approve_current_step()
    
    def admin_approve(self):
        return self.approve_current_step()
    
    def reject_expense(self):
        return self.reject_current_step()

    def button_reset_to_draft(self):
        if not self.env.user.has_group('expense_reimbursement.group_expense_admin'):
            raise UserError(_('Only admin users can reset expenses to draft.'))
        
        # Clear approval steps
        self.approval_step_ids.unlink()
        self.write({'status': 'draft'})
        return True

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        if self.employee_id and self.employee_id.employee_id:
            # Get the manager from the employee record
            employee = self.employee_id.employee_id
            if employee.parent_id:
                self.manager_id = employee.parent_id.user_id
            else:
                # If no manager is set, try to find a manager from the same department
                if employee.department_id:
                    manager = self.env['hr.employee'].search([
                        ('department_id', '=', employee.department_id.id),
                        ('parent_id', '=', False)
                    ], limit=1)
                    if manager:
                        self.manager_id = manager.user_id
