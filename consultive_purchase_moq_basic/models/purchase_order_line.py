from odoo import _, api, fields, models


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    vendor_moq = fields.Float(
        string="Vendor MOQ",
        compute="_compute_vendor_moq",
        digits="Product Unit of Measure",
        help="Minimum Order Quantity configured for this product with the selected vendor.",
    )

    def _get_supplierinfo_moq(self):
        """Return the highest MOQ among matching supplierinfo records
        for this line's product and the order's vendor. 0.0 if none."""
        self.ensure_one()
        if not (self.product_id and self.order_id.partner_id):
            return 0.0
        sellers = self.product_id.seller_ids.filtered(
            lambda s: s.partner_id == self.order_id.partner_id
        )
        if not sellers:
            return 0.0
        return max(sellers.mapped("moq") or [0.0])

    @api.depends("product_id", "order_id.partner_id")
    def _compute_vendor_moq(self):
        for line in self:
            line.vendor_moq = line._get_supplierinfo_moq()

    @api.onchange("product_qty", "product_id")
    def _onchange_check_moq(self):
        if not self.product_id or self.product_qty <= 0:
            return
        moq = self._get_supplierinfo_moq()
        if moq and self.product_qty < moq:
            return {
                "warning": {
                    "title": _("Below Minimum Order Quantity"),
                    "message": _(
                        "Quantity %(qty)s for '%(product)s' is below the MOQ "
                        "(%(moq)s) set for vendor '%(vendor)s'."
                    ) % {
                        "qty": self.product_qty,
                        "product": self.product_id.display_name,
                        "moq": moq,
                        "vendor": self.order_id.partner_id.display_name,
                    },
                }
            }
