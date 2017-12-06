# -*- coding: utf-8 -*-
{
    'name': "linkloving_mrp_extend",

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
    'depends': ['base', 'mrp', 'linkloving_warehouse', 'sales_team', 'linkloving_rework', 'stock',
                'linkloving_process'],

    # always loaded
    'data': [

        'security/mrp_groups.xml',
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/return_material_view.xml',
        'views/stock_location.xml',
        'views/templates.xml',
        'views/stock_move.xml',
        'views/mrp_production.xml',
        'report/mrp_bom_structure_report_templates.xml',
        'report/mrp_production_templates.xml',
        'report/stock_picking_operations.xml',
        'report/mrp_production_templates_extend.xml',
        'wizard/tracking_number_wizard.xml',
        'wizard/change_product_qty_wizard.xml',
        'report/stock_picking_report.xml',
        'views/qc_feedback.xml',
        'views/stock_picking.xml',
        'security/mrp_qc_feedback_seq.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
