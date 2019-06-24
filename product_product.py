# -*- coding: utf-8 -*-
from __future__ import division
from openerp import api, models, _
from openerp.tools.safe_eval import safe_eval
from openerp.exceptions import Warning as UserError


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.multi
    def calculation_sp(self, sales_team=None, avg=None, price=None):
        self.ensure_one()
        price_conf, parameters = self.get_price_conf(sales_team)

        if self.categ_id != self.env.ref('new_base.category_tires') or self.type != 'product':
            return 0
        if avg is None:
            parameters['AVG'] = self.average_price
        else:
            parameters['AVG'] = avg
        if 'SP' in price_conf.input_price_formula:
            parameters['SP'] = price
        input_price = safe_eval(price_conf.input_price_formula, parameters)
        return input_price + price_conf.margin

    @api.multi
    def get_price_conf(self, sales_team):
        conf = self.env.user.company_id
        price_conf = [x
                      for x in conf.input_price_ids
                      if x.sales_team == sales_team]

        if not price_conf:
            raise UserError(_('Sales Team for your user is not added to configuration for '
                            'Min. allowed price calculation. Please, contact administrator.'))

        parameters = {expenses.code: expenses.purchase_price
                      for expenses in conf.expenses_ids}

        return price_conf[0], parameters
