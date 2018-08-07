# -*- coding: utf-8 -*-

{
    'name': 'MO Pause Reason',
    'version': '10.0.1.0.0',
    'author': 'Maha Hamza <maha.hamza@acme-group.net>',
    'category': 'Manufacturing',
    'website': 'http://www.acme-group.net',
    'depends': ['mrp'],
    'data': [
            'wizard/pause_reason_view.xml',
            'view/mrp_workorder_view.xml',
            'security/ir.model.access.csv',
        ],
    'auto_install': False,
    'installable': True,
}
