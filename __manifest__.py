# -*- coding: utf-8 -*-

{
    'name': 'Sparks Energy - Renewable Energy Quotation System',
    'version': '18.0.1.0.0',
    'author': 'Sparks IoT Energy',
    'maintainer': 'Willian Zamora Mero',
    'website': 'http://www.zrcomputing.com',
    'license': 'LGPL-3',
    'category': 'Sales/Solar Energy',
    'summary': 'Renewable energy quotation system with consumption analysis and solar panel calculations',
    'description': """
        Sparks Energy Module for Odoo 18
        ================================
        
        This module provides a comprehensive solution for renewable energy quotations:
        
        * Customer energy consumption tracking
        * Monthly consumption bill analysis
        * Solar radiation data by geographic location
        * Solar panel system calculations
        * Cost estimation and quotation generation
        * Energy savings projections
        
        Key Features:
        - Import monthly consumption data
        - Calculate optimal solar panel capacity
        - Generate detailed quotations
        - Track solar radiation by city/region
        - Manage solar kit components and pricing
        - Energy price projections over time
    """,
    'depends': [
        'base',
        'sale',
        'account',
        'contacts',
        'l10n_ec',
    ],
    'data': [
        # Security
        'security/ir.model.access.csv',
        
        # Data
        'data/sequences.xml',
        'data/energy_price_projection_data.xml',
        
        # Views (ANTES QUE LOS MENÚS)
        'views/solar_quotation_views.xml',
        'views/energy_meter_views.xml',
        'views/solar_panel_product_views.xml',
        'views/auxiliary_views.xml',
        'views/res_partner_views.xml',
        
        # Menús (AL FINAL)
        'views/menu_views.xml',
        
        # Wizards
        #'wizards/import_consumption_wizard.xml',
        #'wizards/multi_meter_quotation_wizard.xml',
    ],
    'demo': [
        'demo/demo_data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'sparks/static/src/js/**/*',
            'sparks/static/src/css/**/*',
        ],
    },
    'images': ['static/description/banner.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
    'external_dependencies': {
        'python': ['xlrd', 'openpyxl'],
    },
}
