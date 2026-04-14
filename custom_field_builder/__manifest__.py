{
    'name': 'Custom Field Builder & Manager',
    'version': '19.0.1.1.0',
    'category': 'Customization',
    'summary': 'Create custom fields and enhance existing fields dynamically',
    'description': """
        Custom Field Builder & Manager
        ================================
        * Create custom fields for any model
        * Edit existing model fields safely
        * Set field attributes (readonly, required, invisible)
        * Manage field visibility in views
        * Visual domain builder for conditions
        * Support for multiple field types
        * Configurable field positioning
    """,
    'author': 'Your Name',
    'depends': ['base', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'views/custom_field_config_views.xml',
        'views/custom_field_views.xml',
        'views/field_editor_views.xml',
        'views/menu_views.xml',
        'data/custom_field_config_data.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
