# consultive_smart_watermark_pdf/tests/common.py
#
# Shared setUp helpers for all watermark test classes.
# Every test class that touches consultive.watermark.config MUST call
# clear_caches() in setUp so the @ormcache doesn't leak state across tests.

from odoo.tests.common import TransactionCase


class WatermarkTestCommon(TransactionCase):
    """Base class for all consultive_smart_watermark_pdf tests."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Find a model that has a 'state' field for use across tests.
        # res.partner.title has no state field — good for negative tests.
        # We'll resolve models by name to avoid cross-module dependencies.
        cls.Config = cls.env['consultive.watermark.config']
        cls.StateLine = cls.env['consultive.watermark.config.state']

    def setUp(self):
        super().setUp()
        # Clear the registry cache before each test to avoid stale QWeb/view
        # artefacts bleeding across tests (e.g. compiled template bytecode).
        self.env.registry.clear_cache()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _make_config(self, model_technical_name, company=None):
        """Create and return a watermark config record for the given model."""
        ir_model = self.env['ir.model'].search(
            [('model', '=', model_technical_name)], limit=1
        )
        self.assertTrue(
            ir_model,
            f'Model {model_technical_name!r} not found in ir.model. '
            'Is the required module installed?',
        )
        vals = {'model_id': ir_model.id}
        if company is not None:
            vals['company_id'] = company.id
        return self.Config.create(vals)

    def _add_state(self, config, value, label, is_confirmed=False):
        """Add a state line to the given config and return it."""
        return self.StateLine.create({
            'config_id': config.id,
            'state_value': value,
            'state_label': label,
            'is_confirmed': is_confirmed,
        })
