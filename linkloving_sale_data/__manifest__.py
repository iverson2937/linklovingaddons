# -*- coding: utf-8 -*-
{
    'name': "linkloving_sale_data",

    'summary': """
    汇整销售数据页面
        """,

    'description': """
        Long description of module's purpose
    """,

    'author': "Allen Tao",
    'website': "http://www.linkloving.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale', 'linkloving_sale', 'sales_team', 'website', 'mrp'],

    # always loaded
    'data': [

        # 'security/ir.model.access.csv',
        'wizard/product_wizard.xml',
        'wizard/sale_order_wizard.xml',
        'views/views.xml',
        'report/sale_order_report.xml',
        'report/product_report.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
