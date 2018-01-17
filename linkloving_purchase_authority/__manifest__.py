# -*- coding: utf-8 -*-
{
    'name': "linkloving_purchase_authority",

    'summary': """
        修改付款申请权限
        """,

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
    'depends': ['base', 'linkloving_account'],

    # always loaded
    'data': [
        'data/purchase_group.xml',
        # 'security/ir.model.access.csv',
        # 'security/ir.model.access.csv',
        'views/purchase_config_setting.xml',
        'views/views.xml',
        'views/templates.xml',

    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
