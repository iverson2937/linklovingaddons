# -*- coding: utf-8 -*-
{
    'name': "linkloving_process",

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
    'depends': ['base', 'mrp', 'linkloving_account', 'hr', 'linkloving_warehouse'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/mrp_process.xml',
        'views/mrp_bom.xml',
        'views/mrp_production.xml',
        'views/hr_employee.xml',
        'views/dashboard.xml',
        'wizard/mrp_production_query_wizard.xml'
    ],
    # only loaded in demonstration mode

    'demo': [
        'demo/demo.xml',
    ],
}
