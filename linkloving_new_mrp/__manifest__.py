# -*- coding: utf-8 -*-
{
    'name': "linkloving_new_mrp",

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

    # any module necessary for this one to work correctly
    'depends': ['base', 'mrp', 'linkloving_mrp_extend', 'linkloving_process'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/rules.xml',
        'views/views.xml',
        'views/mrp_production.xml',
        'views/mrp_product_rule.xml',
        'views/mrp_process.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
