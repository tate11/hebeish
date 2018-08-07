{
    'name': 'Hebeish Custom Reports',
    'version': '10.0',
    'category': 'Quality',
    'author': 'Maha Hamza <maha.hamza@acme-group.net>',
    'depends': ['base','quality','mrp'],
    'data': [
        'security/quality_data.xml',
        'security/ir.model.access.csv',
        'data/decimal_precision.xml',
        'reports/final_report_template.xml',
        'reports/project_qweb_report.xml',
        'views/quality_report_views.xml'
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
