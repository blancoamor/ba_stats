# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#    Copyright (C) 2010-2013 OpenERP s.a. (<http://openerp.com>).
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

from operator import itemgetter
from textwrap import dedent

from openerp import tools, SUPERUSER_ID
from openerp.osv import fields, osv

import logging


_logger = logging.getLogger(__name__) 


class stats_board_bu(osv.osv):
    _name = 'stats.board.bu'
    _description = "Stat board"
    _auto = False
    _columns = {}

    @tools.cache()
    def list(self, cr, uid, context=None):

        Actions = self.pool.get('ir.actions.act_window')
        Menus = self.pool.get('ir.ui.menu')
        IrValues = self.pool.get('ir.values')

        act_ids = Actions.search(cr, uid, [('res_model', '=', self._name)], context=context)
        refs = ['%s,%s' % (Actions._name, act_id) for act_id in act_ids]

        # cannot search "action" field on menu (non stored function field without search_fnct)
        irv_ids = IrValues.search(cr, uid, [
            ('model', '=', 'ir.ui.menu'),
            ('key', '=', 'action'),
            ('key2', '=', 'tree_but_open'),
            ('value', 'in', refs),
        ], context=context)
        menu_ids = map(itemgetter('res_id'), IrValues.read(cr, uid, irv_ids, ['res_id'], context=context))
        menu_names = Menus.name_get(cr, uid, menu_ids, context=context)
        return [dict(id=m[0], name=m[1]) for m in menu_names]

    def _clear_list_cache(self):
        self.list.clear_cache(self)

    def create(self, cr, user, vals, context=None):
        return 0

    def fields_view_get(self, cr, user, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        """
        Overrides orm field_view_get.
        @return: Dictionary of Fields, arch and toolbar.
        """
        _logger.info("hola amego %r " , view_id)

        res = {}
        res = super(stats_board_bu, self).fields_view_get(cr, user, view_id, view_type,
                                                       context=context, toolbar=toolbar, submenu=submenu)

        CustView = self.pool.get('ir.ui.view.custom')
        vids = CustView.search(cr, user, [('user_id', '=', user), ('ref_id', '=', view_id)], context=context)


        if vids:
            view_id = vids[0]
            arch = CustView.browse(cr, user, view_id, context=context)
            res['custom_view_id'] = view_id
            res['arch'] = arch.arch
        res['arch'] = '''
                        <form string="My Dashboard">
                            <board style="1">
                                <column>
                                    <action context="{'lang': 'es_AR', 'tz': 'America/Argentina/Buenos_Aires', 'uid': 1, 'dashboard_merge_domains_contexts': True, 'group_by': [], 'params': {'action': 896}}" domain="" name="896" string="Por unidad de neogocios" view_mode="graph"></action>
                                </column>
                            </board>
                        </form>
                    '''
        res['arch'] = self._arch_preprocessing(cr, user, res['arch'], context=context)
        res['toolbar'] = {'print': [], 'action': [], 'relate': []}
        _logger.info("res['arch'] %r " , res['arch'])

        return res

    def _arch_preprocessing(self, cr, user, arch, context=None):
        from lxml import etree
        def remove_unauthorized_children(node):
            for child in node.iterchildren():
                if child.tag == 'action' and child.get('invisible'):
                    node.remove(child)
                else:
                    child = remove_unauthorized_children(child)
            return node

        def encode(s):
            if isinstance(s, unicode):
                return s.encode('utf8')
            return s

        archnode = etree.fromstring(encode(arch))
        return etree.tostring(remove_unauthorized_children(archnode), pretty_print=True)


