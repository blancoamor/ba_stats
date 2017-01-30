# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from datetime import datetime , timedelta 
from dateutil.relativedelta import relativedelta

from dateutil import parser

from openerp import models, fields, api ,  SUPERUSER_ID
from openerp import tools


from openerp.tools.translate import _
import re
import logging

import requests
from lxml import etree
import json

_logger = logging.getLogger(__name__) 




class ba_stats_business_unit(models.Model):
    _name = 'ba.stats.business.unit'
    _auto = False
    _description = "Estadisticas de venta"

    user_id = fields.Many2one('res.users', 'Salesperson', readonly=True)
    section_id = fields.Many2one('crm.case.section', 'Section', readonly=True)
    product_id = fields.Many2one('product.product', 'Product', readonly=True)
    partner_id = fields.Many2one('res.partner', 'Partner', readonly=True)
    supplier_id = fields.Many2one('res.partner', 'Supplier', readonly=True)

    business_unit_id = fields.Many2one('business.unit', 'Business unit')

    updated_price = fields.Float('updated_price', readonly=True,digits=(16,2))
    line_with_tax = fields.Float('amount', readonly=True,digits=(16,2))
    month = fields.Char('Month', readonly=True)
    date_due = fields.Date('Date due', readonly=True)
    quantity = fields.Float('quantity', readonly=True,digits=(16,0))





    def init(self, cr):
        tools.sql.drop_view_if_exists(cr, 'ba_stats_business_unit')

        cr.execute("""create or replace view  ba_stats_business_unit as (
                        select ail.id,ail.create_uid,ail.write_uid,ail.create_date,ail.write_date,ail.product_id ,ail.price_unit,price_subtotal * 1.21 line_with_tax,quantity,
                        concat(to_char( ai.date_due,'mm'),'/',to_char( ai.date_due,'yy')) as month , 
                        ai.partner_id,ai.user_id,ai.section_id,ai.date_due,
                        pt.business_unit_id , si.name as supplier_id , (price_subtotal * 1.21) * ye.inflation_coef  as updated_price
                        from account_invoice_line ail 
                        join account_invoice ai on (ai.id=ail.invoice_id)
                        join product_product pp on (pp.id=ail.product_id)
                        join product_template pt on (pp.product_tmpl_id = pt.id)
                        join product_supplierinfo si on (si.product_tmpl_id = pt.id and si.sequence=1)
                        join account_period pe on (pe.id = ai.period_id)
                        join account_fiscalyear ye on (ye.id = pe.fiscalyear_id)
                
                 ) """)


class sales_evolution(models.Model):
    _name = 'sales.evolution'
    _auto = False
    _description = "Sales evolution"

    name = fields.Char('Month', readonly=True)

    variacion_real = fields.Float('Variacion real', readonly=True,digits=(16,2))
    variacion_actualizada = fields.Float('avg Variacion actualizada', readonly=True,digits=(16,2))
    amount = fields.Float('monto', readonly=True,digits=(16,2))
    up = fields.Float('monto actualizad0', readonly=True,digits=(16,2))





    def init(self, cr):
        tools.sql.drop_view_if_exists(cr, 'sales_evolution')

        cr.execute("""create or replace view  sales_evolution as (
                        select y1.id as id , concat(y2.year,' vs ', y1.year) as name,
                        (y1.amount * 100 / y2.amount) as variacion_real,
                        (y1.up * 100 / y2.up) as variacion_actualizada,
                        y1.up,
                        y1.amount
                        from 
                        (select min(id) as id , sum(updated_price) up, sum(line_with_tax) amount ,EXTRACT(YEAR FROM  date_due) as year
                        from ba_stats_business_unit
                        group by year ) y1
                         join (select min(id) as id , sum(updated_price) up, sum(line_with_tax) amount ,EXTRACT(YEAR FROM  date_due) as year
                        from ba_stats_business_unit
                        group by year ) y2 on (y1.year - 1 =y2.year)
                        order by y1.year
                
                 ) """)



