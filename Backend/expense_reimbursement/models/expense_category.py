from odoo import models, fields, api


class ExpenseCategory(models.Model):
    _name = 'expense.category'
    _description = 'Expense Category'
    _order = 'name asc'
    
    name = fields.Char(string='Category Name', required=True)
    code = fields.Char(string='Code', required=True)
    description = fields.Text(string='Description')
    parent_id = fields.Many2one('expense.category', string='Parent Category')
    child_ids = fields.One2many('expense.category', 'parent_id', string='Child Categories')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    is_active = fields.Boolean(string='Active', default=True)
    requires_receipt = fields.Boolean(string='Requires Receipt', default=True)
    max_amount = fields.Float(string='Maximum Amount')
    auto_approve_amount = fields.Float(string='Auto-approve Amount', help='Expenses below this amount are auto-approved')
    
    @api.depends('name', 'parent_id')
    def name_get(self):
        result = []
        for category in self:
            if category.parent_id:
                result.append((category.id, f"{category.parent_id.name} / {category.name}"))
            else:
                result.append((category.id, category.name))
        return result
