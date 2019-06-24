# -*- coding: utf-8 -*-
from __future__ import division
from openerp import api, models, fields


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    min_allowed_sales_price = fields.Float(
        string='Min allowed sales price',
        compute='_compute_min_allowed_sp',
        digits=(16, 2),
        default=0.0,
        store=False,
    )
    is_lower = fields.Boolean(
        compute='_compute_is_lower',
        store=False,
    )

    @api.multi
    @api.depends(
        'price_subtotal',
        'price_unit',
        'product_uom_qty',
        'min_allowed_sales_price',
        'product_id.categ_id',
    )
    def _compute_is_lower(self):
        for line in self:
            line.is_lower = False
            if line.price_subtotal is False:
                continue
            if line.price_subtotal / line.product_uom_qty < line.min_allowed_sales_price \
                    and line.product_id.categ_id == self.env.ref('new_base.category_tires') \
                    and line.product_tmpl_id.type == 'product':
                line.is_lower = True

    @api.multi
    @api.depends(
        'company_id.input_price_ids.input_price_formula',
        'company_id.input_price_ids.margin',
        'company_id.expenses_ids.code',
        'company_id.expenses_ids.purchase_price',
        'order_id.state',
        'order_id.section_id',
        'product_id.list_price',
        'product_id.average_price',
    )
    def _compute_min_allowed_sp(self):
        for line in self:
            if line.product_id:
                line.min_allowed_sales_price = line.product_id.calculation_sp(line.order_id.section_id,
                                                                   price=line.product_tmpl_id.list_price)
