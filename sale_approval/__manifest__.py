{
    'name': 'Sale Order Approvals',
    'category': 'Sales Management',
    'author': 'Maha Hamza <maha.hamza@acme-group.net>',
    'website': 'http://www.acme-group.net',
    'depends': ['sale'],
    'data': [
        'views/sale_view.xml',
        'views/res_company.xml',
        'reports/sale_order_template.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
}
