# -*- coding: utf-8 -*-
{
    'name': "Linkloving HR",

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
    'depends': ['base', 'sale', 'hr_expense','account'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'security/groups.xml',
        'security/hide_menu.xml',
        # 'security/hr_expense_sheet_rule.xml',
        'view/account_payment.xml',
        'view/hr_expense_views.xml',
        'view/hr_department_view.xml',
        'view/partner_view.xml',
        'view/hr_view.xml',
        'wizard/hr_expense_register_payment.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo.xml',
    ],
}
