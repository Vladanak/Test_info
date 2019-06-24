# -*- coding: utf-8 -*-
from __future__ import division
from openerp import api, models, fields


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    average_price = fields.Float(
        string='AVG Price',
    )

    @api.model
    def cron_handle_product_templates(self):

        categ_id = self.env.ref('new_base.category_tires')

        company_id = self.env.user.company_id.id

        sql = """
            WITH purchase_line_total AS (
                SELECT
                    pol.id AS purchase_line_id,
                    CASE WHEN pol.price_unit < (SELECT min_price FROM res_company WHERE id = %(company_id)s) THEN
                        COALESCE((SELECT cost_price FROM default_price_settings WHERE company_id = %(company_id)s AND condition = pt.condition), 0)
                        * pol.product_qty
                    ELSE
                        pol.price_unit * pol.product_qty
                    END AS price
                FROM purchase_order_line pol
                    LEFT JOIN product_product pp on pol.product_id = pp.id
                    LEFT JOIN product_template pt on pp.product_tmpl_id = pt.id
            )
            UPDATE product_template
            SET average_price = s.average_price
            FROM (
                SELECT
                    pt.id template_id,
                    COALESCE(
                        SUM(plt.price) / SUM(pol.product_qty),
                        COALESCE((SELECT cost_price FROM default_price_settings WHERE company_id = %(company_id)s AND condition = pt.condition), 0)
                    ) AS average_price
                FROM product_template pt
                    LEFT JOIN product_product pp ON pt.id = pp.product_tmpl_id
                    LEFT JOIN purchase_order_line pol ON pp.id = pol.product_id
                    LEFT JOIN purchase_line_total plt ON plt.purchase_line_id = pol.id
                WHERE pt.categ_id = %(categ_id)s and pt.type = 'product'
                GROUP BY
                    pt.id
            ) s
            WHERE id = s.template_id
        """

        self.env.cr.execute(sql, {'categ_id': categ_id.id, 'company_id': company_id})
