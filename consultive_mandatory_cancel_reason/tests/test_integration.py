from odoo.tests.common import tagged

from .common import CancelReasonTestCommon


@tagged('consultive_mandatory_cancel_reason', 'cancel_integration', 'post_install', '-at_install')
class TestCancelIntegration(CancelReasonTestCommon):
    """End-to-end test: full cancel flow on a real sale order."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].search([], limit=1)
        cls.product = cls.env['product.product'].search(
            [('type', '!=', 'service')], limit=1
        ) or cls.env['product.product'].search([], limit=1)

    def test_sale_order_cancel_end_to_end(self):
        so = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 1,
            })],
        })

        # Step 1: action_cancel intercepted — returns wizard action, not a cancel
        action = so.action_cancel()
        self.assertIsInstance(action, dict, 'action_cancel must return the wizard action dict.')
        self.assertEqual(
            action.get('res_model'), 'consultive.cancel.wizard',
            'The returned action must open the cancel wizard.',
        )
        self.assertEqual(so.state, 'draft', 'SO must still be draft — cancel was intercepted.')

        # Step 2: Confirm via wizard
        wizard = self._make_wizard('sale.order', so.ids, self.reason_a, note='Integration test')
        wizard.action_do_cancel()

        # Step 3: SO is now cancelled
        self.assertEqual(so.state, 'cancel', 'SO must be cancelled after wizard confirmation.')

        # Step 4: Chatter has reason and note
        reason_in_chatter = so.message_ids.filtered(
            lambda m: self.reason_a.name in (m.body or '')
        )
        self.assertTrue(reason_in_chatter, 'Reason name must appear in the chatter.')

        note_in_chatter = so.message_ids.filtered(
            lambda m: 'Integration test' in (m.body or '')
        )
        self.assertTrue(note_in_chatter, 'Note must appear in the chatter.')
