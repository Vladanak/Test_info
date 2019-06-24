# -*- coding: utf-8 -*-
from openerp import api, models, fields


class MarginRulesCalcConf(models.TransientModel):
    _name = 'margin.rules.calc.conf'
    _inherit = 'parameters.res.config.settings'

    company_id = fields.Many2one(
        comodel_name='res.company',
    )

    input_price_ids = fields.One2many(
        comodel_name='input.price.settings',
        related='company_id.input_price_ids',
    )

    expenses_ids = fields.One2many(
        comodel_name='expenses.settings',
        related='company_id.expenses_ids',
    )

    default_price_ids = fields.One2many(
        comodel_name='default.price.settings',
        related='company_id.default_price_ids',
    )

    allowed_sales_teams = fields.One2many(
        comodel_name='allowed.sales.teams',
        related='company_id.allowed_sales_teams',
    )

    min_price = fields.Float(
        related='company_id.min_price',
        required=True,
    )

    @api.model
    def get_default_company_id(self, field_list):
        return {
            'company_id': self.env.user.company_id.id,
        }
