# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class HrExpense(models.Model):
    _inherit = 'hr.expense'

    # Additional fields for currency conversion
    original_currency_id = fields.Many2one(
        'res.currency', 
        string='Original Currency',
        help='Currency of the original expense amount'
    )
    original_amount = fields.Float(
        string='Original Amount',
        help='Original amount in the expense currency'
    )
    converted_amount = fields.Float(
        string='Amount in Company Currency',
        compute='_compute_converted_amount',
        store=True,
        help='Amount converted to company currency'
    )
    exchange_rate = fields.Float(
        string='Exchange Rate',
        compute='_compute_exchange_rate',
        store=True,
        help='Exchange rate used for conversion'
    )

    # OCR related fields
    receipt_image = fields.Binary(
        string='Receipt Image',
        attachment=True,
        help='Upload receipt image for OCR processing'
    )
    ocr_processed = fields.Boolean(
        string='OCR Processed',
        default=False,
        help='Indicates if the receipt has been processed with OCR'
    )
    restaurant_name = fields.Char(
        string='Restaurant/Merchant Name',
        help='Name of restaurant or merchant extracted from receipt'
    )

    @api.depends('original_amount', 'original_currency_id', 'company_id.currency_id')
    def _compute_converted_amount(self):
        """
        Compute amount converted to company currency
        """
        for expense in self:
            if expense.original_amount and expense.original_currency_id:
                if expense.original_currency_id == expense.company_id.currency_id:
                    expense.converted_amount = expense.original_amount
                    expense.exchange_rate = 1.0
                else:
                    try:
                        converted = self.env['currency.api'].convert_currency(
                            expense.original_amount,
                            expense.original_currency_id.name,
                            expense.company_id.currency_id.name
                        )
                        expense.converted_amount = converted
                        
                        # Calculate exchange rate
                        if expense.original_amount != 0:
                            expense.exchange_rate = converted / expense.original_amount
                        else:
                            expense.exchange_rate = 1.0
                            
                    except Exception as e:
                        _logger.error(f"Currency conversion failed for expense {expense.id}: {e}")
                        expense.converted_amount = expense.original_amount
                        expense.exchange_rate = 1.0
            else:
                expense.converted_amount = expense.unit_amount or 0.0
                expense.exchange_rate = 1.0

    @api.depends('original_amount', 'converted_amount')
    def _compute_exchange_rate(self):
        """
        Compute exchange rate
        """
        for expense in self:
            if expense.original_amount != 0:
                expense.exchange_rate = expense.converted_amount / expense.original_amount
            else:
                expense.exchange_rate = 1.0

    @api.model
    def create(self, vals):
        """
        Override create to set default values
        """
        if 'original_currency_id' not in vals and 'currency_id' in vals:
            vals['original_currency_id'] = vals['currency_id']
        
        if 'original_amount' not in vals and 'unit_amount' in vals:
            vals['original_amount'] = vals['unit_amount']
        
        return super(HrExpense, self).create(vals)

    def write(self, vals):
        """
        Override write to update related fields
        """
        if 'unit_amount' in vals:
            vals['original_amount'] = vals['unit_amount']
        
        if 'currency_id' in vals:
            vals['original_currency_id'] = vals['currency_id']
        
        return super(HrExpense, self).write(vals)

    def process_receipt_ocr(self):
        """
        Process receipt image using OCR to extract expense information
        """
        for expense in self:
            if not expense.receipt_image:
                raise UserError("Please upload a receipt image first")
            
            try:
                # Process OCR
                ocr_data = self.env['ocr.processor'].read_receipt(expense.receipt_image)
                
                # Update expense with extracted data
                update_vals = {}
                
                if ocr_data.get('amount', 0) > 0:
                    update_vals['original_amount'] = ocr_data['amount']
                    update_vals['unit_amount'] = ocr_data['amount']
                
                if ocr_data.get('date'):
                    update_vals['date'] = ocr_data['date']
                
                if ocr_data.get('restaurant_name'):
                    update_vals['restaurant_name'] = ocr_data['restaurant_name']
                    update_vals['description'] = ocr_data['restaurant_name']
                
                if ocr_data.get('description'):
                    update_vals['description'] = ocr_data['description']
                
                if update_vals:
                    expense.write(update_vals)
                
                expense.ocr_processed = True
                
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'OCR Processing Complete',
                        'message': 'Receipt information has been extracted successfully.',
                        'type': 'success',
                    }
                }
                
            except Exception as e:
                raise UserError(f"OCR processing failed: {e}")

    def action_process_ocr(self):
        """
        Button action to process OCR
        """
        return self.process_receipt_ocr()

class ResCompany(models.Model):
    _inherit = 'res.company'

    @api.model
    def create(self, vals):
        """
        Override create to set currency based on country
        """
        if 'country_id' in vals and not vals.get('currency_id'):
            country = self.env['res.country'].browse(vals['country_id'])
            if country.exists():
                currency_code = self.env['currency.api'].get_currency_by_country(country.name)
                if currency_code:
                    currency = self.env['res.currency'].search([('name', '=', currency_code)], limit=1)
                    if currency:
                        vals['currency_id'] = currency.id
        
        return super(ResCompany, self).create(vals)

    def write(self, vals):
        """
        Override write to update currency when country changes
        """
        if 'country_id' in vals:
            country = self.env['res.country'].browse(vals['country_id'])
            if country.exists():
                currency_code = self.env['currency.api'].get_currency_by_country(country.name)
                if currency_code:
                    currency = self.env['res.currency'].search([('name', '=', currency_code)], limit=1)
                    if currency:
                        vals['currency_id'] = currency.id
        
        return super(ResCompany, self).write(vals)

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # Add settings for currency API and OCR
    enable_currency_conversion = fields.Boolean(
        string='Enable Currency Conversion',
        related='company_id.enable_currency_conversion',
        readonly=False
    )
    enable_ocr_processing = fields.Boolean(
        string='Enable OCR Processing',
        related='company_id.enable_ocr_processing',
        readonly=False
    )
