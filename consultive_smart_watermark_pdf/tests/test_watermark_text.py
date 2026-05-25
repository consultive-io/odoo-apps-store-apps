# consultive_smart_watermark_pdf/tests/test_watermark_text.py
#
# Unit tests for ConsultiveWatermarkConfig.get_watermark_text().
# One test method per code path (approved decision 1A - Tests section).
# Records are mocked with MagicMock so no cross-module dependencies are needed.

from unittest.mock import MagicMock, PropertyMock

from odoo.tests.common import tagged

from .common import WatermarkTestCommon


@tagged('consultive_smart_watermark_pdf', 'watermark_text')
class TestGetWatermarkText(WatermarkTestCommon):
    """Tests for the get_watermark_text() method — one test per code path."""

    def _mock_record(self, model_name, state_value, has_state_field=True):
        """Return a MagicMock that mimics a minimal Odoo record."""
        record = MagicMock()
        record._name = model_name
        record.state = state_value
        if has_state_field:
            record._fields = {'state': MagicMock()}
        else:
            record._fields = {}
        return record

    # ------------------------------------------------------------------
    # Path 1: falsy record → False
    # ------------------------------------------------------------------

    def test_false_record_returns_false(self):
        self.assertFalse(self.Config.get_watermark_text(False))

    def test_none_record_returns_false(self):
        self.assertFalse(self.Config.get_watermark_text(None))

    def test_empty_string_record_returns_false(self):
        self.assertFalse(self.Config.get_watermark_text(''))

    # ------------------------------------------------------------------
    # Path 2: model has no 'state' field → False
    # ------------------------------------------------------------------

    def test_no_state_field_returns_false(self):
        record = self._mock_record('some.model', 'draft', has_state_field=False)
        self.assertFalse(self.Config.get_watermark_text(record))

    # ------------------------------------------------------------------
    # Path 3: state is falsy → False
    # ------------------------------------------------------------------

    def test_state_is_false_returns_false(self):
        record = self._mock_record('some.model', False)
        self.assertFalse(self.Config.get_watermark_text(record))

    def test_state_is_empty_string_returns_false(self):
        record = self._mock_record('some.model', '')
        self.assertFalse(self.Config.get_watermark_text(record))

    # ------------------------------------------------------------------
    # Path 4: no config exists for model → False
    # ------------------------------------------------------------------

    def test_no_config_for_model_returns_false(self):
        # No config created — cache returns None → method returns False.
        record = self._mock_record('res.partner', 'draft')
        # res.partner has no standard state field, but we're mocking it.
        self.assertFalse(self.Config.get_watermark_text(record))

    # ------------------------------------------------------------------
    # Path 5: state is in confirmed set → False
    # ------------------------------------------------------------------

    def test_confirmed_state_returns_false(self):
        config = self._make_config('res.users')
        self._add_state(config, 'draft', 'DRAFT', is_confirmed=False)
        self._add_state(config, 'done', 'DONE', is_confirmed=True)

        record = self._mock_record('res.users', 'done')
        self.assertFalse(self.Config.get_watermark_text(record))

    # ------------------------------------------------------------------
    # Path 6: preliminary state, label in config → return label
    # ------------------------------------------------------------------

    def test_preliminary_state_returns_configured_label(self):
        config = self._make_config('res.users')
        self._add_state(config, 'draft', 'QUOTATION', is_confirmed=False)
        self._add_state(config, 'done', 'DONE', is_confirmed=True)

        record = self._mock_record('res.users', 'draft')
        self.assertEqual(self.Config.get_watermark_text(record), 'QUOTATION')

    # ------------------------------------------------------------------
    # Path 7: preliminary state, NOT in config → auto-generated label
    # ------------------------------------------------------------------

    def test_unknown_preliminary_state_auto_generates_label(self):
        """State added after Load States was last run → auto-label from value."""
        config = self._make_config('res.users')
        self._add_state(config, 'done', 'DONE', is_confirmed=True)
        # 'pending_approval' was never added to state_line_ids.

        record = self._mock_record('res.users', 'pending_approval')
        result = self.Config.get_watermark_text(record)
        self.assertEqual(result, 'PENDING APPROVAL')

    # ------------------------------------------------------------------
    # Path 8: config exists but state_line_ids is empty → auto-label for draft
    # ------------------------------------------------------------------

    def test_empty_state_lines_auto_generates_draft_label(self):
        """Config with no state lines: any state becomes auto-label."""
        self._make_config('res.users')  # no state lines added

        record = self._mock_record('res.users', 'draft')
        result = self.Config.get_watermark_text(record)
        self.assertEqual(result, 'DRAFT')

    # ------------------------------------------------------------------
    # Multi-company isolation
    # ------------------------------------------------------------------

    def test_company_specific_config_takes_priority_over_global(self):
        """Company-specific config overrides global config."""
        company_a = self.env['res.company'].create({'name': 'Test Co A'})

        # Global config (company_id=False) — says 'draft' → 'GLOBAL DRAFT'
        global_cfg = self.Config.create({
            'model_id': self.env['ir.model'].search(
                [('model', '=', 'res.users')], limit=1
            ).id,
            'company_id': False,
        })
        self._add_state(global_cfg, 'draft', 'GLOBAL DRAFT', is_confirmed=False)

        # Company A config — says 'draft' → 'COMPANY DRAFT'
        co_cfg = self._make_config('res.users', company=company_a)
        self._add_state(co_cfg, 'draft', 'COMPANY DRAFT', is_confirmed=False)

        record = self._mock_record('res.users', 'draft')

        # When env.company is company_a, company-specific label wins.
        result = self.Config.with_company(company_a).get_watermark_text(record)
        self.assertEqual(result, 'COMPANY DRAFT')
