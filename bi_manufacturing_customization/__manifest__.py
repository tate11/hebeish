# -*- coding: utf-8 -*-
{
    'name': "BI Manufacturing Customization",
    'summary': "BI Manufacturing Customization",
    'description': """ 
            This module edit on manufacturing module.
     """,
    'author': "BI Solutions Development Team",
    'category': 'Manufacturing',
    'version': '0.1',
    'depends': ['mrp'],
    'data': [
        'views/mrp_production_inherit.xml',
    ],
    'installable': True,
    'auto_install': False,
    'sequence': 1
}
