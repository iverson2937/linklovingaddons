# -*- coding: utf-8 -*-
{
    'name': "linkloving_sale",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Linklove",
    'website': "http://www.Linkloving.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale', 'product', 'sales_team', 'sale_stock', 'linkloving_stock_picking',
                'linkloving_warehouse', 'delivery'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/sale_group.xml',
        'view/sale_view.xml',
        'view/payment_view.xml',
        'view/partner_view.xml',
        'view/crm_team.xml',
        'view/product_template.xml',
        'view/stock_picking.xml',
        'wizard/sale_order_cancel.xml',
        'wizard/res_partner_assign_wizard.xml',
        'report/sale_order_report_templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo.xml',
    ],
    'qweb': ['static/src/xml/*.xml'],
}
