# -*- coding: utf-8 -*-
{
    'name': 'Proforma Account Invoice',
    'summary': 'Proforma Account Invoice',
    'description': """
       Proforma Account Invoice.
    """,
    'version': '10.0',
    'category': 'sale',
    'author': 'BI Solutions',
    'depends': ['sale'],
    'data': [
        'views/proforma_account_invoice.xml',
        'views/proforma_sequence.xml',
        'views/proforma_invoice_report.xml',
    ],
    'installable': True,
}
