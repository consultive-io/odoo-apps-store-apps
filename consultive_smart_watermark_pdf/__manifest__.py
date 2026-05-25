{
    'name': 'Smart Watermark PDF',
    'version': '19.0.1.0.0',
    'category': 'Technical',
    'summary': (
        'State-aware diagonal watermark on every PDF report — fully '
        'configurable per model via Settings, zero code changes needed.'
    ),
    'description': """
Consultive – Smart Watermark PDF
=================================
Automatically overlays a bold diagonal watermark on every PDF or printed
report whenever the underlying Odoo record is in a non-confirmed state.
The watermark label and which states trigger it are fully configurable
per model through a Settings UI — no code changes needed.

Configuration (Settings > Watermark > Watermark Configuration):
  * Add any Odoo model that has a Print PDF action.
  * Click "Load States from Model" to auto-populate all state values.
  * Check "Confirmed (No Watermark)" for states that should NOT show a watermark.
  * All other states show their configured label as a diagonal watermark.

Default behaviour:
  * No config for a model  ->  no watermark (opt-in per model).
  * State added after "Load States"  ->  auto-label from state value.
  * Multi-company aware: company-specific config overrides global config.

* Works system-wide — covers all four built-in report layouts:
  Standard, Striped, Boxed, and Bold.
* Compatible with both Odoo Community and Enterprise editions.
* When the record reaches a confirmed state the watermark disappears automatically.
    """,
    'author': 'Consultive',
    'website': 'https://www.consultive.io',
    'support': 'contact@consultive.io',
    'license': 'LGPL-3',

    # ------------------------------------------------------------------ #
    #  Dependencies                                                        #
    # ------------------------------------------------------------------ #
    # Only 'web' required: all four layout templates live in web module.
    # The Python models use only 'base' framework classes.
    'depends': ['web'],

    # ------------------------------------------------------------------ #
    #  Data files                                                          #
    # ------------------------------------------------------------------ #
    'data': [
        'security/ir.model.access.csv',
        'views/watermark_config_views.xml',
        'report/report_layout.xml',
    ],

    # ------------------------------------------------------------------ #
    #  App Store assets                                                    #
    # ------------------------------------------------------------------ #
    'images': [
        'static/description/consultive_smart_watermark_pdf_image_01.png',
        'static/description/consultive_smart_watermark_pdf_image_02.png',
    ],

    'installable': True,
    'auto_install': False,
    'application': False,
}
