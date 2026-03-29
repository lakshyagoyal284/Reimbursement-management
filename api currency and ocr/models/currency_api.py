# -*- coding: utf-8 -*-

import requests
import logging
from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class CurrencyAPI(models.Model):
    _name = 'currency.api'
    _description = 'Currency API Integration'

    @api.model
    def get_exchange_rates(self, base_currency='USD'):
        """
        Get exchange rates from ExchangeRate API
        """
        try:
            url = f'https://api.exchangerate-api.com/v4/latest/{base_currency}'
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            _logger.error(f"Failed to fetch exchange rates: {e}")
            raise UserError(f"Failed to fetch exchange rates: {e}")

    @api.model
    def convert_currency(self, amount, from_currency, to_currency):
        """
        Convert currency amount from one currency to another
        """
        if from_currency == to_currency:
            return amount

        try:
            rates_data = self.get_exchange_rates(from_currency)
            rates = rates_data.get('rates', {})
            
            if to_currency not in rates:
                raise UserError(f"Target currency {to_currency} not found in exchange rates")
            
            converted_amount = amount * rates[to_currency]
            return round(converted_amount, 2)
            
        except Exception as e:
            _logger.error(f"Currency conversion failed: {e}")
            raise UserError(f"Currency conversion failed: {e}")

    @api.model
    def get_country_currencies(self):
        """
        Get all countries with their currencies from REST Countries API
        """
        try:
            url = 'https://restcountries.com/v3.1/all?fields=name,currencies'
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            _logger.error(f"Failed to fetch country currencies: {e}")
            raise UserError(f"Failed to fetch country currencies: {e}")

    @api.model
    def get_currency_by_country(self, country_name):
        """
        Get currency code by country name
        """
        try:
            countries_data = self.get_country_currencies()
            
            for country in countries_data:
                if country.get('name', {}).get('common', '').lower() == country_name.lower():
                    currencies = country.get('currencies', {})
                    if currencies:
                        return list(currencies.keys())[0]
            
            return None
            
        except Exception as e:
            _logger.error(f"Failed to get currency for country {country_name}: {e}")
            return None
