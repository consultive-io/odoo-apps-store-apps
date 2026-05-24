{
    "name": "Recently Viewed Records",
    "version": "19.0.1.0.0",
    "summary": "Systray dropdown showing your last 20 opened records across all models",
    "description": """
Adds a history icon to the Odoo top bar (systray). Click it to see a dropdown
listing the last 20 records you opened, across all models. Each entry links
directly back to the record. Tracked per user, stored server-side, available
across devices and browsers.
    """,
    "category": "Productivity",
    "author": "Consultive",
    "website": "https://consultive.io",
    "support": "contact@consultive.io",
    "license": "LGPL-3",
    "depends": ["web"],
    "data": [
        "security/ir.model.access.csv",
        "security/ir_recent_record_rule.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "consultive_recently_viewed_basic/static/src/css/recently_viewed.css",
            "consultive_recently_viewed_basic/static/src/xml/recently_viewed_systray.xml",
            "consultive_recently_viewed_basic/static/src/js/recently_viewed_systray.js",
            "consultive_recently_viewed_basic/static/src/js/form_controller_patch.js",
        ],
    },
    "images": [
        "static/description/screenshot_1.png",
        "static/description/screenshot_2.png",
    ],
    "price": 0,
    "currency": "EUR",
    "installable": True,
    "application": False,
}
