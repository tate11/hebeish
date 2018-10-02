{
    'name': 'Hebeish Custom Reports',
    'version': '10.0',
    'category': 'Quality',
    'author': 'Maha Hamza <maha.hamza@acme-group.net>',
    'depends': ['base', 'quality', 'mrp'],
    'data': [
        'security/quality_data.xml',
        'security/ir.model.access.csv',
        'data/decimal_precision.xml',
        'reports/final_report_template.xml',
        'reports/project_qweb_report.xml',
        'views/quality_report_views.xml',
        'views/res_partner_inherit_view.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
