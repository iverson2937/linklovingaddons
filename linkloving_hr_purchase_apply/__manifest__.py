# -*- coding: utf-8 -*-
{
    'name': "linkloving_hr_purchase_apply",

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
    'depends': ['base', 'linkloveing_hr', 'linkloving_app_api'],

    # always loaded
    'data': [
        'report/hr_purchase_apply.xml',
        'report/report.xml',
        'wizard/hr_purchase_apply_refuse_wizard.xml',
        'data/hr_purchase_apply_seq.xml',
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/purchase_apply.xml',
        'views/hr_expense_sheet.xml',

    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
