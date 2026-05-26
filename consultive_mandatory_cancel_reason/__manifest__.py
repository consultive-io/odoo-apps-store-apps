{
    'name': 'Mandatory Cancellation Reason',
    'version': '19.0.1.0.0',
    'category': 'Operations/Inventory',
    'summary': (
        'Force users to select a reason before cancelling any document '
        '— logged in the chatter for full accountability.'
    ),
    'description': """
Consultive – Mandatory Cancellation Reason
=============================================
Prevents one-click cancellations with no accountability. Whenever a user
attempts to cancel a document, a modal wizard opens requiring them to choose
a reason from a configurable list and optionally add a free-text note.

After confirming, the document is cancelled and the reason + note are
automatically logged in the chatter — timestamped and attributed to the user.

Works out of the box for:
  * Sale Orders
  * Purchase Orders
  * Customer Invoices, Vendor Bills, Credit Notes (account.move)
  * Warehouse Transfers / Pickings (stock.picking)

Extend to any other model (e.g. Manufacturing Orders) in one click via
Settings > Technical > Cancellation > Model Configuration — no coding required.

Configurable reason list:
  * Manage reasons under Settings > Technical > Cancellation > Cancellation Reasons.
  * Reasons can be archived (soft-deleted) without losing historical chatter logs.
  * Drag-and-drop ordering for the dropdown list.

Compatible with Odoo 19.0 Community and Enterprise.
    """,
    'author': 'Consultive',
    'website': 'https://www.consultive.io',
    'support': 'contact@consultive.io',
    'license': 'LGPL-3',
    'price': 0.0,
    'currency': 'EUR',

    'depends': ['sale', 'purchase', 'account', 'stock'],

    'data': [
        'security/ir.model.access.csv',
        'data/cancel_model_config_data.xml',
        'views/cancel_reason_views.xml',
        'views/cancel_wizard_views.xml',
        'views/cancel_log_views.xml',
        'views/cancel_model_config_views.xml',
    ],

    'images': [
        'static/description/consultive_mandatory_cancel_reason_01.png',
    ],

    'installable': True,
    'auto_install': False,
    'application': False,
}
