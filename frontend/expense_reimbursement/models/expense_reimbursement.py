from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ExpenseReimbursement(models.Model):
    _name = 'expense.reimbursement'
    _description = 'Expense Reimbursement'
    _order = 'date desc, id desc'
    _rec_name = 'description'

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, default=lambda self: self.env.user.employee_id)
    manager_id = fields.Many2one('hr.employee', string='Manager', related='employee_id.parent_id', store=True)
    admin_id = fields.Many2one('res.users', string='Admin', default=lambda self: self.env.user)
    
    amount = fields.Monetary(string='Amount', required=True, currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, default=lambda self: self.env.company.currency_id)
    date = fields.Date(string='Date', required=True, default=fields.Date.today)
    description = fields.Text(string='Description', required=True)
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('manager_approved', 'Manager Approved'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], string='Status', default='draft', tracking=True)
    
    submit_date = fields.Datetime(string='Submit Date', readonly=True)
    manager_approval_date = fields.Datetime(string='Manager Approval Date', readonly=True)
    admin_approval_date = fields.Datetime(string='Admin Approval Date', readonly=True)
    
    manager_comment = fields.Text(string='Manager Comment')
    admin_comment = fields.Text(string='Admin Comment')
    
    # Dashboard fields
    total_expenses = fields.Monetary(string='Total Expenses', compute='_compute_dashboard_stats', currency_field='currency_id')
    pending_count = fields.Integer(string='Pending Count', compute='_compute_dashboard_stats')
    pending_amount = fields.Monetary(string='Pending Amount', compute='_compute_dashboard_stats', currency_field='currency_id')
    approved_count = fields.Integer(string='Approved Count', compute='_compute_dashboard_stats')
    approved_amount = fields.Monetary(string='Approved Amount', compute='_compute_dashboard_stats', currency_field='currency_id')
    rejected_count = fields.Integer(string='Rejected Count', compute='_compute_dashboard_stats')
    rejected_amount = fields.Monetary(string='Rejected Amount', compute='_compute_dashboard_stats', currency_field='currency_id')

    @api.depends_context('uid')
    def _compute_dashboard_stats(self):
        domain = []
        if not self.env.user.has_group('base.group_system'):
            domain = [('employee_id', '=', self.env.user.employee_id.id)]
        
        expenses = self.search(domain)
        
        self.total_expenses = sum(expenses.mapped('amount'))
        self.pending_count = len(expenses.filtered(lambda e: e.state == 'submitted'))
        self.pending_amount = sum(expenses.filtered(lambda e: e.state == 'submitted').mapped('amount'))
        self.approved_count = len(expenses.filtered(lambda e: e.state == 'approved'))
        self.approved_amount = sum(expenses.filtered(lambda e: e.state == 'approved').mapped('amount'))
        self.rejected_count = len(expenses.filtered(lambda e: e.state == 'rejected'))
        self.rejected_amount = sum(expenses.filtered(lambda e: e.state == 'rejected').mapped('amount'))

    def action_submit(self):
        if not self.employee_id.parent_id:
            raise ValidationError('No manager assigned to this employee. Please contact HR.')
        self.write({
            'state': 'submitted',
            'submit_date': fields.Datetime.now()
        })
        
    def action_manager_approve(self):
        if self.manager_id.user_id != self.env.user and not self.env.user.has_group('base.group_system'):
            raise ValidationError('You are not authorized to approve this expense.')
        self.write({
            'state': 'manager_approved',
            'manager_approval_date': fields.Datetime.now()
        })
        
    def action_admin_approve(self):
        if not self.env.user.has_group('base.group_system'):
            raise ValidationError('You are not authorized to approve this expense.')
        self.write({
            'state': 'approved',
            'admin_approval_date': fields.Datetime.now()
        })
        
    def action_reject(self):
        self.write({'state': 'rejected'})

    @api.model
    def create(self, vals):
        if 'employee_id' not in vals:
            vals['employee_id'] = self.env.user.employee_id.id
        return super(ExpenseReimbursement, self).create(vals)
