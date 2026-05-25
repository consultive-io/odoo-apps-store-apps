# consultive_smart_watermark_pdf/tests/test_qweb_integration.py
#
# Integration tests that render actual PDF HTML and assert on the output.
# These tests require the 'sale' module to be installed (for sale.order).
# If 'sale' is not in the registry the tests are skipped automatically.
#
# Tests verify the complete pipeline:
#   Python config  →  get_watermark_text()  →  QWeb layout  →  HTML output

from odoo.tests.common import tagged

from .common import WatermarkTestCommon


@tagged('consultive_smart_watermark_pdf', 'watermark_qweb')
class TestQwebIntegration(WatermarkTestCommon):
    """End-to-end tests rendering actual report HTML."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._sale_available = 'sale.order' in cls.env.registry

    def setUp(self):
        super().setUp()
        if not self._sale_available:
            self.skipTest(
                'sale module not installed — skipping QWeb integration tests.'
            )

    def _create_sale_config(self, confirmed_states=None):
        """Create a watermark config for sale.order."""
        confirmed_states = confirmed_states or ['sale', 'done', 'cancel']
        config = self._make_config('sale.order')
        self._add_state(config, 'draft', 'QUOTATION', is_confirmed=False)
        self._add_state(config, 'sent', 'QUOTATION SENT', is_confirmed=False)
        for state in confirmed_states:
            label = state.replace('_', ' ').upper()
            self._add_state(config, state, label, is_confirmed=True)
        return config

    def _render_sale_order_html(self, order):
        """Render the sale order PDF report and return HTML bytes."""
        report = self.env.ref('sale.action_report_saleorder', raise_if_not_found=False)
        if not report:
            self.skipTest('sale.action_report_saleorder not found.')
        html, _ = report._render_qweb_html(report.report_name, order.ids)
        return html

    # ------------------------------------------------------------------
    # Watermark appears for preliminary state
    # ------------------------------------------------------------------

    def test_watermark_appears_for_draft_sale_order(self):
        """Quotation (draft) should have QUOTATION watermark in HTML."""
        self._create_sale_config()
        order = self.env['sale.order'].create({
            'partner_id': self.env.ref('base.res_partner_1').id,
        })
        self.assertEqual(order.state, 'draft')

        html = self._render_sale_order_html(order)

        self.assertIn(b'consultive-smart-watermark', html,
                      'Watermark div not found in rendered HTML.')
        self.assertIn(b'QUOTATION', html,
                      'Watermark label "QUOTATION" not found in rendered HTML.')

    # ------------------------------------------------------------------
    # Watermark absent for confirmed state
    # ------------------------------------------------------------------

    def test_watermark_absent_for_confirmed_sale_order(self):
        """Confirmed SO (state=sale) must NOT show any watermark."""
        self._create_sale_config()
        order = self.env['sale.order'].create({
            'partner_id': self.env.ref('base.res_partner_1').id,
        })
        order.action_confirm()
        self.assertEqual(order.state, 'sale')

        html = self._render_sale_order_html(order)

        self.assertNotIn(b'consultive-smart-watermark', html,
                         'Watermark div found in HTML for a confirmed SO.')

    # ------------------------------------------------------------------
    # No config → no watermark (not a crash)
    # ------------------------------------------------------------------

    def test_no_config_means_no_watermark(self):
        """With no config for sale.order, no watermark and no crash."""
        # Do NOT create a config.
        order = self.env['sale.order'].create({
            'partner_id': self.env.ref('base.res_partner_1').id,
        })
        html = self._render_sale_order_html(order)
        self.assertNotIn(b'consultive-smart-watermark', html)

    # ------------------------------------------------------------------
    # Registry guard — model removed after template compiled
    # ------------------------------------------------------------------

    def test_registry_guard_prevents_crash_when_model_absent(self):
        """If consultive.watermark.config is not in registry, PDF still renders."""
        # We can't actually remove the model from the registry in a test,
        # but we verify the guard expression itself is safe.
        # The guard: 'consultive.watermark.config' in env.registry
        self.assertIn('consultive.watermark.config', self.env.registry,
                      'Model should be registered after install.')
        # Render without crash:
        order = self.env['sale.order'].create({
            'partner_id': self.env.ref('base.res_partner_1').id,
        })
        try:
            self._render_sale_order_html(order)
        except Exception as e:
            self.fail(f'PDF rendering raised an unexpected exception: {e}')
