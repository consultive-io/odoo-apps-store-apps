{
    "name": "MOQ per Vendor-Product",
    "version": "19.0.1.0.0",
    "summary": "Minimum Order Quantity per vendor-product with PO warnings",
    "description": """
Adds a Minimum Order Quantity (MOQ) field on the vendor pricelist of a product
(Product > Purchase tab). When creating a Purchase Order / RFQ, the MOQ is
displayed as a read-only column on each line, and an onchange warning is
shown if the ordered quantity falls below the configured MOQ for the selected
vendor-product combination.
    """,
    "category": "Purchases",
    "author": "Custom",
    "license": "LGPL-3",
    "depends": ["purchase"],
    "data": [
        "views/product_supplierinfo_views.xml",
        "views/purchase_order_views.xml",
    ],
    "installable": True,
    "application": False,
}
