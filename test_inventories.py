# -*- coding: utf-8 -*-
from openerp.tests import common
from . import test_sale_orders
from mock import patch


class TestInventories(test_sale_orders.TestSaleOrders):

    def setUp(self):
        super(TestInventories, self).setUp()
        self.uti_common_location = self.uti_stock.common()

        ou_wh_map_id = self.env['stock.quant.combined.wh_ou_map'].create({
            'operating_unit_id': self.ou_uti.id,
            'internal_wh_location_id': self.uti_stock.common().id,
            'external_wh_location_ids': [(6, 0, [self.frd_stock.common().id])],
        })
        self.env['utires.shop.config.settings'].set(
            'wh_ou_map_ids',
            [(6, 0, [ou_wh_map_id.id])],
        )
        with patch.object(self.env.cr, 'commit'):
            self.env['stock.quant.combined'].init()
        self.env.user.default_section_id = self.team.id

    def test_stock_quant_combined(self):
        product = self.new_product()
        quant = self._add_qty(product, self.uti_stock, 2)
        quant.product_template_id.categ_id = self.env.ref('new_base.category_tires')

        stock_quant = self.env['stock.quant.combined'].search([
            ('quant_id', '=', quant.id)
        ])
        stock_quant._compute_min_allowed_sp()

        self.assertEqual(stock_quant.min_allowed_sales_price, 20.0)
