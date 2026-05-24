{
    'name': 'Enable Print Time Date Basic',
    'version': '19.0.1.0.0',
    'category': 'Technical',
    'summary': (
        'Appends a print timestamp (date, time, AM/PM, GMT) '
        'to the footer of every PDF/print report system-wide.'
    ),
    'description': """
Consultive – Enable Print Time Date Basic
==========================================
Automatically appends a "Printed on: <date> <time> AM/PM (GMT)" line at the
very bottom of every PDF or printed report in Odoo.

* Covers all four built-in report layouts: Standard, Striped, Boxed, Bold.
* Works for both Odoo Community and Enterprise editions.
* No per-model configuration required – installing the module is enough.
* Time is always expressed in GMT/UTC so the stamp is unambiguous regardless
  of the server's or user's local time zone.
    """,
    'author': 'Consultive',
    'website': 'https://www.consultive.io',
    'support': 'contact@consultive.io',
    'license': 'LGPL-3',

    # ------------------------------------------------------------------ #
    #  Dependencies                                                        #
    # ------------------------------------------------------------------ #
    # Only 'web' is required: all four layout templates live in web/views/
    # report_templates.xml.  There is no dependency on 'account' or any
    # other business module, so the stamp appears on every single report.
    'depends': ['web'],

    # ------------------------------------------------------------------ #
    #  Data files                                                          #
    # ------------------------------------------------------------------ #
    'data': [
        'report/report_layout.xml',
    ],

    # ------------------------------------------------------------------ #
    #  App Store assets                                                    #
    # ------------------------------------------------------------------ #
    # icon.png is auto-discovered from static/description/icon.png
    # images lists the cover / gallery images shown on the App Store page
    'images': [
        'static/description/app_image_1.png',
        'static/description/app_image_2.png',
    ],

    'installable': True,
    'auto_install': False,
    'application': False,
}
