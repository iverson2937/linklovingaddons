# -*- coding: utf-8 -*-
{
    'name': "linkloving_product_approve",

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
    'depends': ['base', 'product', 'linkloving_warehouse', 'linkloving_sale', 'linkloving_mrp_automatic_plan',
                'linkloving_pdm', 'linkloving_new_bom_update'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/approve_groups.xml',
        'views/assets.xml',
        'views/mrp_approve_stage.xml',
        'views/product_template.xml',

        'wizard/product_state_confirm_wizard.xml',
    ],
    'qweb': ['static/src/xml/*.xml'],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
