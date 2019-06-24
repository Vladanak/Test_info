# -*- coding: utf-8 -*-
from __future__ import division
from openerp.tests import common
from openerp.addons.utires_base.tests import test_base
from openerp.exceptions import Warning as UserError


class TestSaleOrders(test_base.TestBase):

    def setUp(self):
        super(TestSaleOrders, self).setUp()
        self.conf = self.env.user.company_id
        self.uti_stock_shelf = self.env['stock.location'].create({
            'name': 'TEST',
            'usage': 'internal',
        })

        values = {'list_price': 3.33, 'special_usage': True}

        self.product = self.new_tire(values)

        self.quant = self.env['stock.quant'].create({
            'product_id': self.product.id,
            'location_id': self.uti_stock_shelf.id,
            'qty': 1,
        })
        self.quant.product_template_id.categ_id = self.env.ref('new_base.category_tires')

        self.partner = self.testing['res.partner'].create({})

        self.conf.min_price = 11

        self.team = self.env['crm.case.section'].create({
            'name': 'Test',
            'code': 'TS',
        })
        self.input_config = self.conf.input_price_ids.create({
            'sales_team': self.team.id,
            'input_price_formula': 'AVG+MK',
            'margin': 10,
            'company_id': self.conf.id,
        })
        self.expense_config = self.conf.expenses_ids.create({
            'expenses': 'Marketing',
            'code': 'MK',
            'purchase_price': 10,
            'company_id': self.conf.id,
        })
        self.allowed_config = self.conf.allowed_sales_teams.create({
            'sales_team': self.team.id,
            'company_id': self.conf.id,
        })
        self.default_price_config = self.conf.default_price_ids.create({
            'condition': 'new',
            'cost_price': 30,
            'company_id': self.conf.id,
        })

    def test_sale_order(self):
        self.quant.product_template_id.cron_handle_product_templates()
        self.assertEqual(self.quant.product_template_id.average_price, 30)

        so = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 1,
                'price_unit': 100,
            })],
            'date_order': '2019-10-10 10:10:10',
            'section_id': self.team.id,
        })

        self.assertTrue(so.section_id in [x.sales_team
                                          for x in self.conf.allowed_sales_teams])

        so.order_line.price_unit = 500

        self.assertEqual(so.order_line.min_allowed_sales_price, 50)
        self.assertTrue(so.order_line.price_subtotal / so.order_line.product_uom_qty >
                        so.order_line.min_allowed_sales_price)
        self.assertFalse(so.is_lower)
        self.assertFalse(so.is_warning)
        self.assertFalse(so.validation_messages)

        so.order_line.price_unit = -500

        self.assertFalse(so.order_line.price_subtotal / so.order_line.product_uom_qty >
                         so.order_line.min_allowed_sales_price)
        self.assertTrue(so.is_lower)
        self.assertTrue(so.is_warning)
        self.assertTrue(bool(so.validation_messages))

        with self.assertRaises(UserError):
            so.confirm_and_move_from_external()

        so.discount_reason = 'New'

        with self.assertRaises(UserError):
            so.confirm_and_move_from_external()

        group = self.env['res.groups'].search([('full_name', '=', 'Margin Rules / Allow to confirm Sale Orders')])
        self.env['res.users'].browse(self.env.uid).groups_id = group

        reservation = self.env['stock.reservation'].create({
            'location_id': self.quant.location_id.id,
            'product_uom_qty': self.quant.qty,
            'product_uos_qty': self.quant.qty,
            'product_uom': so.order_line.product_uom.id,
            'name': "%s (%s)" % (so.name, so.order_line.name),
            'product_id': so.order_line.product_id.id,
        })

        so.order_line.reservation_ids = reservation

        so.confirm_and_move_from_external()

        self.assertFalse(so.order_line.price_subtotal / so.order_line.product_uom_qty >
                         so.order_line.min_allowed_sales_price)
        self.assertTrue(so.is_lower)
        self.assertTrue(so.is_warning)
        self.assertTrue(bool(so.discount_reason))
