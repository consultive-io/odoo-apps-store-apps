# consultive_smart_watermark_pdf/models/watermark_config.py
#
# Two models:
#   consultive.watermark.config        — one row per (model, company)
#   consultive.watermark.config.state  — one row per state of that model
#
# Design notes:
#   - No ormcache: config table has at most a handful of rows; a direct
#     search() per PDF render is microseconds and avoids all cache-API
#     version issues across Odoo releases.
#   - 'state' in record._fields preferred over hasattr (no accidental ORM reads)
#   - action_load_states uses bulk-fetch dedup (2 queries regardless of state count)
#   - get_watermark_text uses explicit guard-clause style with auto-label fallback

import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class ConsultiveWatermarkConfig(models.Model):
    """Per-model watermark configuration header.

    One record per (model, company) pair.  A record with company_id=False acts
    as a global default that applies to all companies which have no
    company-specific config.
    """

    _name = 'consultive.watermark.config'
    _description = 'Watermark Configuration'
    _rec_name = 'model_id'
    _order = 'model_id'

    model_id = fields.Many2one(
        'ir.model',
        string='Model',
        required=True,
        ondelete='cascade',
        index=True,
        help='The Odoo model whose PDF reports should carry a watermark.',
    )
    model_name = fields.Char(
        related='model_id.model',
        string='Technical Name',
        store=True,
        readonly=True,
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        index=True,
        help='Leave empty to apply this configuration to all companies.',
    )
    state_line_ids = fields.One2many(
        'consultive.watermark.config.state',
        'config_id',
        string='States',
    )
    active = fields.Boolean(default=True)

    _unique_model_company = models.Constraint(
        'UNIQUE(model_id, company_id)',
        'A watermark configuration already exists for this model and company.',
    )

    # ------------------------------------------------------------------
    # Public API — called from QWeb via env['consultive.watermark.config']
    # ------------------------------------------------------------------

    @api.model
    def get_watermark_text(self, record):
        """Return the watermark label string for *record*, or False.

        Called from the QWeb layout sub-template on every PDF render.
        All paths return False on any problem — never raises.

        Lookup order:
          1. record falsy or wrong type           → False
          2. model has no 'state' field           → False
          3. record.state is falsy                → False
          4. no config found for model + company  → False
          5. state is in the confirmed set        → False  (no watermark)
          6. state label found in config          → label string
          7. state not in config (custom stage)   → auto-generated label
        """
        if not record:
            return False
        if 'state' not in record._fields:
            return False
        state = record.state
        if not state:
            return False

        try:
            config_data = self._get_config_data(record._name)
        except Exception:
            _logger.exception(
                'consultive_smart_watermark_pdf: unexpected error resolving '
                'watermark config for model %s', record._name
            )
            return False

        if config_data is None:
            # No configuration exists for this model — show no watermark.
            return False
        if state in config_data['confirmed']:
            # Confirmed / done state — no watermark.
            return False

        # Preliminary state — return the configured label or auto-generate one.
        label = config_data['labels'].get(state)
        if label:
            return label
        # State not in config (e.g. custom approval stage added after Load States).
        # Generate a readable label automatically from the state value.
        return state.replace('_', ' ').upper()

    # ------------------------------------------------------------------
    # Internal config lookup (direct DB query — no cache needed)
    # ------------------------------------------------------------------

    def _get_config_data(self, model_name):
        """Return config data dict for model_name, or None if no config exists.

        Company resolution: company-specific config takes priority over a
        global config (company_id=False).

        No ormcache is used here. The config table has very few rows and
        Odoo's ORM already caches recordset reads within a request. A direct
        search() adds negligible overhead to PDF rendering.
        """
        company_id = self.env.company.id
        config = self.search(
            [
                ('model_name', '=', model_name),
                '|',
                ('company_id', '=', company_id),
                ('company_id', '=', False),
            ],
            order='company_id desc nulls last',
            limit=1,
        )
        if not config:
            return None

        lines = config.state_line_ids
        return {
            'confirmed': set(
                lines.filtered(lambda l: l.is_confirmed).mapped('state_value')
            ),
            'labels': {l.state_value: l.state_label for l in lines},
        }

    # ------------------------------------------------------------------
    # "Load States" button
    # ------------------------------------------------------------------

    def action_load_states(self):
        """Introspect the model's state field and add missing child rows.

        Idempotent: running multiple times never creates duplicate rows.
        Existing rows (including hand-crafted custom stage entries) are
        preserved — only *missing* state values are added.

        Resolution order for the selection list:
          1. field._description_selection(env) — handles callables & methods
          2. ir.model.fields.selection table   — fallback for edge cases
        """
        self.ensure_one()

        try:
            model_cls = self.env[self.model_id.model]
        except KeyError:
            _logger.warning(
                'consultive_smart_watermark_pdf: model %s is not installed; '
                'cannot load states.', self.model_id.model
            )
            return True

        if 'state' not in model_cls._fields:
            return True

        # Resolve selection — _description_selection handles all variants
        # (list, method name string, callable).
        selection = []
        try:
            selection = model_cls._fields['state']._description_selection(
                model_cls.env
            )
        except Exception:
            _logger.debug(
                'consultive_smart_watermark_pdf: _description_selection failed '
                'for %s; falling back to ir.model.fields.selection.',
                self.model_id.model,
            )

        if not selection:
            field_rec = self.env['ir.model.fields'].search(
                [('model_id', '=', self.model_id.id), ('name', '=', 'state')],
                limit=1,
            )
            if field_rec:
                selection = [
                    (s.value, s.string) for s in field_rec.selection_ids
                ]

        if not selection:
            return True

        # Bulk deduplication — 1 query for existing values, 1 bulk insert.
        existing = set(self.state_line_ids.mapped('state_value'))
        to_create = [
            {
                'config_id': self.id,
                'state_value': value,
                'state_label': label.upper(),
                'is_confirmed': False,
            }
            for value, label in selection
            if value not in existing
        ]
        if to_create:
            self.env['consultive.watermark.config.state'].create(to_create)

        return True


class ConsultiveWatermarkConfigState(models.Model):
    """One row per state value for a given watermark configuration.

    When is_confirmed is True the state is treated as "done" — no watermark.
    When is_confirmed is False the state_label is shown as the watermark text.
    """

    _name = 'consultive.watermark.config.state'
    _description = 'Watermark Config State Line'
    _order = 'sequence, id'

    config_id = fields.Many2one(
        'consultive.watermark.config',
        string='Configuration',
        required=True,
        ondelete='cascade',
        index=True,
    )
    sequence = fields.Integer(default=10)
    state_value = fields.Char(
        string='State Value',
        required=True,
        help="Internal state identifier, e.g. 'draft', 'sale', 'done'.",
    )
    state_label = fields.Char(
        string='Watermark Label',
        required=True,
        help="Text shown as the watermark, e.g. 'QUOTATION'. Uppercase recommended.",
    )
    is_confirmed = fields.Boolean(
        string='Confirmed (No Watermark)',
        default=False,
        help=(
            'If checked, this state is considered confirmed/finalised. '
            'PDFs in this state will NOT display a watermark.'
        ),
    )

    _unique_state_per_config = models.Constraint(
        'UNIQUE(config_id, state_value)',
        'This state value already exists for this configuration.',
    )
