# -*- coding: utf-8 -*-
{
    'name': "linkloving_mrp_automatic_plan",

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
    'depends': ['base', 'mrp', 'purchase', 'sale', 'linkloving_purchase', 'linkloving_process', 'hr',
                'linkloving_app_api', 'linkloving_mrp_extend'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/auto_plan_data.xml',
        'views/dashboard.xml',
        'views/ScheduleReport.xml',
        'views/sale_order_view.xml',
        'views/mrp_production_view.xml',
        'views/purchase_view.xml',
        'views/mrp_equipment.xml',
        'views/views.xml',
        'views/templates.xml',
        'views/HrConfigSettings.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'qweb': ['static/src/xml/*.xml'],
}
