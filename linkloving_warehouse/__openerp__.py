# -*- coding: utf-8 -*-
{
    'name': "linkloving_warehouse",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Your Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'product', 'mrp', 'purchase', 'stock'],

    # always loaded
    'data': [
        'security/rules.xml',
        'security/ir.model.access.csv',
        'security/engineer_groups.xml',
        'views/stock_view.xml',
        'views/stock_location.xml',
        'views/mrp_production_cancel.xml',
        'views/mrp_production_combine.xml',
        # 'views/stock_picking_view.xml',
        'views/product_view.xml',
        'views/product_config.xml',
        'views/mrp_production.xml',
        # 'views/product_template.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo.xml',
    ],
    'qweb': ['static/src/xml/*.xml'],
}
