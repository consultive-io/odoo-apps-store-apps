from odoo import fields, models


class ProductSupplierinfo(models.Model):
    _inherit = "product.supplierinfo"

    moq = fields.Float(
        string="MOQ",
        digits="Product Unit of Measure",
        default=0.0,
        help=(
            "Minimum Order Quantity for this product from this vendor. "
            "A warning is shown on the Purchase Order line if the ordered "
            "quantity is below this value. Leave at 0 to disable the check."
        ),
    )
