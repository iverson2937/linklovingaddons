# -*- coding: utf-8 -*-
{
    'name': "linkloving_return_goods",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctlyh
    'depends': ['base', 'sale', 'purchase', 'stock', 'linkloving_invoice_workflow', 'linkloving_purchase'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/return_material.xml',
        'views/templates.xml',
        'views/stock_picking.xml',
        'data/ir_sequence_data.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
