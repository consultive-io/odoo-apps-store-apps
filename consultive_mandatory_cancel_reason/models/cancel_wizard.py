import json

from odoo import api, fields, models

from .cancel_model_config import CANCEL_BYPASS_KEY  # noqa: F401 — re-exported for tests


class ConsultiveCancelWizard(models.TransientModel):
    _name = 'consultive.cancel.wizard'
    _description = 'Mandatory Cancellation Reason'

    reason_id = fields.Many2one(
        'consultive.cancel.reason',
        string='Cancellation Reason',
        required=True,
        domain=[('active', '=', True)],
    )
    note = fields.Text(string='Additional Note')
    res_model = fields.Char(
        default=lambda self: self.env.context.get('default_res_model', ''),
    )
    res_ids = fields.Char(
        default=lambda self: self.env.context.get('default_res_ids', '[]'),
    )
    record_display = fields.Char(
        string='Document',
        default=lambda self: self.env.context.get('default_record_display', ''),
    )

    @api.model
    def _open_wizard(self, res_model, res_ids):
        records = self.env[res_model].browse(res_ids).exists()
        names = records.mapped('display_name')
        if len(names) <= 3:
            display = ', '.join(names)
        else:
            display = f'{", ".join(names[:3])} (+{len(names) - 3} more)'
        return {
            'type': 'ir.actions.act_window',
            'name': 'Cancel Document',
            'res_model': 'consultive.cancel.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_res_model': res_model,
                'default_res_ids': json.dumps(res_ids),
                'default_record_display': display,
            },
        }

    def action_do_cancel(self):
        ids = json.loads(self.res_ids or '[]')
        records = self.env[self.res_model].browse(ids)

        config = self.env['consultive.cancel.model.config'].sudo().search(
            [('model_name', '=', self.res_model), ('active', '=', True)], limit=1
        )
        cancel_method = (config.cancel_method if config else None) or 'action_cancel'
        getattr(records.with_context(**{CANCEL_BYPASS_KEY: True}), cancel_method)()

        body = f'<b>Cancellation Reason:</b> {self.reason_id.name}'
        if self.note:
            body += f'<br/><b>Note:</b> {self.note}'
        for record in records:
            record.message_post(body=body)

        self.env['consultive.cancel.log']._create_entries(self, records)
