# -*- coding: utf-8 -*-
{
    'name': 'MultiPAC GECOERP PAC Adicional (CFDI 4.0 México)',
    'version': '0.2',
    'description':  ''' 
         Añade GECOERP como MultiPAC adicional para la certificación de documentos CFDI.
                    ''',
    'category': 'Accounting',
    'author': 'GECOERP',
    'maintainer': 'GECOERP',
    'website': 'https://www.gecoerp.com/',
    'depends': [
        'account',
        'l10n_mx_edi'
    ],
    'data': [
        'views/res_company_view.xml',
        'data/cron.xml',
    ],    
    'images': ['static/description/banner.gif'],
    'application': False,
    'installable': True,
    'license': 'OPL-1',
    'price': 25.00,
    'currency': 'USD',
}
