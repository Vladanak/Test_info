# -*- coding: utf-8 -*-
from __future__ import division
from openerp import models, fields, api


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    input_price = fields.Float(
        string="Input Price",
        digits=(16, 2),
        default=0.0,
        compute='_compute_sales_input_price',
        store=True,
    )

    sales_price = fields.Float(
        string="Sales Price",
        digits=(16, 2),
        default=0.0,
        compute='_compute_sales_input_price',
        store=True,
    )

    @api.multi
    @api.depends('location_id', 'purchase_order_line_id.price_unit')
    def _compute_sales_input_price(self):
        conf = self.env.user.company_id
        for quant in self:
            if quant.location_id.usage == 'customer' and \
                    quant.sale_order_line_id.product_id.categ_id == self.env.ref('utires_base.category_tires'):
                quant.sales_price = quant.sale_order_line_id.price_subtotal / quant.sale_order_line_id.product_uom_qty

                min_price = quant.product_id.calculation_sp(quant.so_id.section_id,
                                                            quant.purchase_order_line_id.price_unit,
                                                            quant.product_template_id.list_price)

                if quant.purchase_order_line_id.price_unit == 0:
                    default_price = [price.cost_price
                                     for price in conf.default_price_ids
                                     if price.condition == quant.product_template_id.condition]
                    min_price += default_price[0]

                quant.input_price = min_price
