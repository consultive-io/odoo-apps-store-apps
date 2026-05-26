from odoo import fields, models


class ConsultiveCancelReason(models.Model):
    _name = 'consultive.cancel.reason'
    _description = 'Cancellation Reason'
    _order = 'sequence, name'

    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    _unique_name = models.Constraint(
        'UNIQUE(name)',
        'A cancellation reason with this name already exists.',
    )
