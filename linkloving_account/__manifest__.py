# -*- coding: utf-8 -*-
{
    'name': "linkloving_account",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account', 'purchase', 'linkloving_invoice_workflow', 'linkloving_sale',
                'linkloving_account_parent', 'stock_account'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/other_income_seq.xml',
        'security/rules.xml',
        'views/payment_views.xml',
        'views/account_invoice_views.xml',
        'views/sale_views.xml',
        'views/account_account_data.xml',
        'views/account_menu.xml',
        'views/product_category.xml',
        'views/res_partner_views.xml',
        'views/res_partner_bank.xml',
        'views/account_move_line.xml',
        'views/account_payment.xml',
        'views/account_journal.xml',
        'views/account_employee.xml',
        'wizard/account_supplier_payment_wizard.xml',
        'report/report_payment_application.xml',
        'report/report.xml',

    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
