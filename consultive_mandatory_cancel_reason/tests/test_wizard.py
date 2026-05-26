import json

from odoo.tests.common import tagged
from odoo.tools import mute_logger

from ..models.cancel_wizard import CANCEL_BYPASS_KEY
from .common import CancelReasonTestCommon


@tagged('consultive_mandatory_cancel_reason', 'cancel_wizard', 'post_install', '-at_install')
class TestCancelWizard(CancelReasonTestCommon):
    """Tests for _open_wizard(), the bypass key, and action_do_cancel() logic."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].search([], limit=1)

    def _make_draft_so(self):
        return self.env['sale.order'].create({'partner_id': self.partner.id})

    # ------------------------------------------------------------------
    # _open_wizard classmethod
    # ------------------------------------------------------------------

    def test_open_wizard_returns_act_window_dict(self):
        action = self.Wizard._open_wizard('sale.order', [1, 2, 3])
        self.assertEqual(action['type'], 'ir.actions.act_window')
        self.assertEqual(action['res_model'], 'consultive.cancel.wizard')
        self.assertEqual(action['target'], 'new')

    def test_open_wizard_context_contains_model_and_ids(self):
        action = self.Wizard._open_wizard('sale.order', [7, 8])
        ctx = action['context']
        self.assertEqual(ctx['default_res_model'], 'sale.order')
        self.assertEqual(json.loads(ctx['default_res_ids']), [7, 8])

    # ------------------------------------------------------------------
    # Bypass key
    # ------------------------------------------------------------------

    def test_action_cancel_without_bypass_returns_wizard_action(self):
        so = self._make_draft_so()
        result = so.action_cancel()
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get('res_model'), 'consultive.cancel.wizard')

    def test_action_cancel_with_bypass_key_skips_wizard(self):
        so = self._make_draft_so()
        result = so.with_context(**{CANCEL_BYPASS_KEY: True}).action_cancel()
        if isinstance(result, dict):
            self.assertNotEqual(result.get('res_model'), 'consultive.cancel.wizard')
        self.assertEqual(so.state, 'cancel')

    # ------------------------------------------------------------------
    # reason_id required
    # ------------------------------------------------------------------

    def test_reason_id_required_on_wizard(self):
        so = self._make_draft_so()
        with mute_logger('odoo.sql_db'), self.assertRaises(Exception):
            self.Wizard.create({
                'reason_id': False,
                'res_model': 'sale.order',
                'res_ids': json.dumps(so.ids),
            })

    # ------------------------------------------------------------------
    # Chatter log content
    # ------------------------------------------------------------------

    def test_chatter_log_contains_reason_name(self):
        so = self._make_draft_so()
        wizard = self._make_wizard('sale.order', so.ids, self.reason_a)
        wizard.action_do_cancel()
        msgs = so.message_ids.filtered(lambda m: 'Autotest Alpha Reason' in (m.body or ''))
        self.assertTrue(msgs, 'Chatter must contain the cancellation reason name.')

    def test_chatter_includes_note_when_provided(self):
        so = self._make_draft_so()
        wizard = self._make_wizard('sale.order', so.ids, self.reason_a, note='Urgent rework needed')
        wizard.action_do_cancel()
        msgs = so.message_ids.filtered(lambda m: 'Urgent rework needed' in (m.body or ''))
        self.assertTrue(msgs, 'Note must appear in the chatter message body.')

    def test_chatter_omits_note_line_when_absent(self):
        so = self._make_draft_so()
        wizard = self._make_wizard('sale.order', so.ids, self.reason_a)
        wizard.action_do_cancel()
        msgs = so.message_ids.filtered(lambda m: 'Note' in (m.body or ''))
        self.assertFalse(msgs, 'Chatter must not include a Note line when no note was given.')

    # ------------------------------------------------------------------
    # Bulk cancel
    # ------------------------------------------------------------------

    def test_bulk_cancel_posts_to_each_record(self):
        so1 = self._make_draft_so()
        so2 = self._make_draft_so()
        wizard = self._make_wizard('sale.order', [so1.id, so2.id], self.reason_b)
        wizard.action_do_cancel()
        for so in (so1, so2):
            msgs = so.message_ids.filtered(lambda m: 'Autotest Beta Reason' in (m.body or ''))
            self.assertTrue(msgs, f'SO {so.id}: chatter must have the reason logged.')

    def test_bulk_cancel_cancels_all_records(self):
        so1 = self._make_draft_so()
        so2 = self._make_draft_so()
        wizard = self._make_wizard('sale.order', [so1.id, so2.id], self.reason_a)
        wizard.action_do_cancel()
        self.assertEqual(so1.state, 'cancel')
        self.assertEqual(so2.state, 'cancel')
