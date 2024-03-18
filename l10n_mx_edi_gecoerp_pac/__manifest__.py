# -*- coding: utf-8 -*-
{
    'name': 'Integra a GECOERP como PAC Adicional (CFDI 4.0 México)',
    'version': '0.1',
    'description':  ''' 
         Integra a GECOERP como PAC adicional para la certificación de documentos CFDI.
                    ''',
    'category': 'Accounting',
    'author': 'GECOERP',
    'website': 'https://www.gecoerp.com/',
    'depends': [
        'account',
        'l10n_mx_edi'
    ],
    'data': [
        'views/res_company_view.xml',
        'data/cron.xml',
    ],    
    'images': ['static/description/banner.png'],
    'application': False,
    'installable': True,
    'license': 'OPL-1',
    'price': 0.00,
    'currency': 'USD',
}
