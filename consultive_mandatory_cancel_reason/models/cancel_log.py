from odoo import api, fields, models


class ConsultiveCancelLog(models.Model):
    _name = 'consultive.cancel.log'
    _description = 'Cancellation Log'
    _order = 'cancel_date desc'
    _rec_name = 'res_name'

    reason_id = fields.Many2one(
        'consultive.cancel.reason',
        string='Reason',
        ondelete='restrict',
        readonly=True,
    )
    note = fields.Text(string='Note', readonly=True)
    res_model = fields.Char(string='Document Model', readonly=True)
    res_model_label = fields.Char(string='Document Type', readonly=True)
    res_id = fields.Integer(string='Document ID', readonly=True)
    res_name = fields.Char(string='Document', readonly=True)
    cancelled_by = fields.Many2one(
        'res.users',
        string='Cancelled By',
        readonly=True,
    )
    cancel_date = fields.Datetime(
        string='Cancelled On',
        readonly=True,
    )

    @api.model
    def _create_entries(self, wizard, records):
        config = self.env['consultive.cancel.model.config'].sudo().search(
            [('model_name', '=', wizard.res_model)], limit=1
        )
        label = config.label if config else wizard.res_model
        now = fields.Datetime.now()
        uid = self.env.uid
        vals_list = [
            {
                'reason_id': wizard.reason_id.id,
                'note': wizard.note or False,
                'res_model': wizard.res_model,
                'res_model_label': label,
                'res_id': record.id,
                'res_name': record.display_name,
                'cancelled_by': uid,
                'cancel_date': now,
            }
            for record in records
        ]
        self.create(vals_list)

    def action_open_document(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': self.res_model,
            'res_id': self.res_id,
            'view_mode': 'form',
            'target': 'current',
        }
