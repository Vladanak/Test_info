# -*- coding: utf-8 -*-
from __future__ import division
from openerp import api, models, fields, _
from openerp.exceptions import Warning as UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    discount_reason = fields.Char(
        string='Discount reason',
    )

    is_warning = fields.Boolean(
        string='Is Warning',
        compute='_compute_is_warning'
    )

    is_lower = fields.Boolean(
        string='Keeps tires with negative profit',
        compute='_compute_is_lower',
        search='_search_is_lower',
        store=False,
    )

    validation_messages = fields.Text(
        compute='_compute_is_lower',
    )

    @api.multi
    @api.depends(
        'state',
        'section_id',
        'company_id.allowed_sales_teams',
        'order_line.price_unit',
        'order_line.min_allowed_sales_price',
        'order_line.product_id.categ_id',
        'order_line.is_lower',
    )
    def _compute_is_lower(self):
        for order in self:
            products = ''
            order.is_lower = False

            if any(order.order_line.mapped('is_lower')):
                order.is_lower=True

            for product in order.order_line.filtered('is_lower').mapped('product_id'):
                products += product.display_name + '\n'

            if products:
                order.validation_messages = _(
                    'WARNING! You are trying to sell Tire product(s) with price which is lower than allowed.'
                    'Please, make sure Unit Price is set correctly for products:'
                    '\n'
                    '%s'
                    '\n'
                    'In case all is valid:'
                    '\n'
                    "Fill in 'Discount reason' field"
                    '\n'
                    'Ask your Manager to confirm the Quotation'
                ) % products

    @api.multi
    @api.depends('is_lower')
    def _compute_is_warning(self):
        for order in self:
            order.is_warning = order.is_lower and order.section_id in [x.sales_team for x in
                                                                       self.env.user.company_id.allowed_sales_teams]

    def _search_is_lower(self, operator, value):
        assert operator in ['=', '!=']

        orders = self.env['sale.order'].search([
            ('state', 'not in', ['progress', 'manual', 'cancel', 'done']),
        ])

        # we use sudo() because of performance
        # it's much faster filter under sudo
        if operator == '=':
            filtered = orders.sudo().filtered(lambda x: x.is_lower == value)
        else:
            filtered = orders.sudo().filtered(lambda x: x.is_lower != value)

        return [('id', 'in', filtered.ids)]

    @api.multi
    def ensure_minimal_price(self):
        for order in self:
            user = self.env.context.get('uid')
            if not user:
                user = self.env.uid
            is_margin_conf = self.env['res.users'].browse(user).has_group(
                                             'project_margin_rules_calc.group_margin_rules_calc_conf_allow_so_confirm')
            if order.is_warning and not is_margin_conf and order.discount_reason:
                raise UserError('Ask your Manager to confirm the Quotation')
            if order.is_warning and not is_margin_conf:
                raise UserError('Fill in ‘Discount reason’ field!'
                                '\n'
                                'Ask your Manager to confirm the Quotation')
            if order.is_warning and not order.discount_reason:
                raise UserError("Fill in 'Discount reason' field")
