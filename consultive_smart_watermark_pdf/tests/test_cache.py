# consultive_smart_watermark_pdf/tests/test_cache.py
#
# Tests for live DB-lookup behaviour of consultive.watermark.config.
# The model uses direct search() per call (no @ormcache by design — the
# config table has very few rows). These tests verify that:
#   - get_watermark_text() returns correct results from DB
#   - Writing a config record is reflected immediately on next call
#   - Writing a state line record is reflected immediately on next call
#   - Deleting a config removes watermark for that model immediately
#   - Results are isolated by company

from unittest.mock import MagicMock

from odoo.tests.common import tagged

from .common import WatermarkTestCommon


@tagged('consultive_smart_watermark_pdf', 'watermark_cache')
class TestLiveDbLookup(WatermarkTestCommon):
    """Verifies get_watermark_text() reflects DB state immediately after writes."""

    def _mock_record(self, model_name, state_value):
        record = MagicMock()
        record._name = model_name
        record.state = state_value
        record._fields = {'state': MagicMock()}
        return record

    def test_repeated_calls_return_consistent_result(self):
        """Multiple calls return the same result (no stale state between calls)."""
        config = self._make_config('res.users')
        self._add_state(config, 'draft', 'DRAFT', is_confirmed=False)

        record = self._mock_record('res.users', 'draft')
        result_1 = self.Config.get_watermark_text(record)
        result_2 = self.Config.get_watermark_text(record)
        self.assertEqual(result_1, 'DRAFT')
        self.assertEqual(result_1, result_2)

    def test_writing_config_reflected_immediately(self):
        """Updating the config record is reflected on the next call."""
        config = self._make_config('res.users')
        self._add_state(config, 'draft', 'OLD LABEL', is_confirmed=False)

        record = self._mock_record('res.users', 'draft')
        self.assertEqual(self.Config.get_watermark_text(record), 'OLD LABEL')

        # Update the config — should clear cache.
        config.write({'active': False})

        # Config is now inactive; search won't find it → returns False.
        result = self.Config.get_watermark_text(record)
        self.assertFalse(result)

    def test_writing_state_line_reflected_immediately(self):
        """Updating a child state line is reflected on the next call."""
        config = self._make_config('res.users')
        line = self._add_state(config, 'draft', 'ORIGINAL', is_confirmed=False)

        record = self._mock_record('res.users', 'draft')
        self.assertEqual(self.Config.get_watermark_text(record), 'ORIGINAL')

        # Update the state line label.
        line.write({'state_label': 'UPDATED'})

        result = self.Config.get_watermark_text(record)
        self.assertEqual(result, 'UPDATED')

    def test_marking_state_confirmed_takes_immediate_effect(self):
        """Toggling is_confirmed on a state line is reflected on the next call."""
        config = self._make_config('res.users')
        line = self._add_state(config, 'draft', 'DRAFT', is_confirmed=False)

        record = self._mock_record('res.users', 'draft')
        self.assertEqual(self.Config.get_watermark_text(record), 'DRAFT')

        # Mark as confirmed — draft should now show no watermark.
        line.write({'is_confirmed': True})

        self.assertFalse(self.Config.get_watermark_text(record))

    def test_deleting_config_removes_watermark_immediately(self):
        """Deleting a config removes watermark for that model immediately."""
        config = self._make_config('res.users')
        self._add_state(config, 'draft', 'DRAFT', is_confirmed=False)

        record = self._mock_record('res.users', 'draft')
        self.assertEqual(self.Config.get_watermark_text(record), 'DRAFT')

        config.unlink()

        self.assertFalse(self.Config.get_watermark_text(record))

    def test_deleting_state_line_reflected_immediately(self):
        """Deleting a state line is reflected on the next call."""
        config = self._make_config('res.users')
        line = self._add_state(config, 'draft', 'DRAFT', is_confirmed=False)

        record = self._mock_record('res.users', 'draft')
        self.assertEqual(self.Config.get_watermark_text(record), 'DRAFT')

        line.unlink()

        # 'draft' no longer in config — falls through to auto-label.
        result = self.Config.get_watermark_text(record)
        self.assertEqual(result, 'DRAFT')  # auto-generated from state value

    def test_results_are_isolated_per_company(self):
        """Company A's result must not affect Company B."""
        company_a = self.env['res.company'].create({'name': 'Cache Test Co A'})
        company_b = self.env['res.company'].create({'name': 'Cache Test Co B'})

        config_a = self._make_config('res.users', company=company_a)
        self._add_state(config_a, 'draft', 'COMPANY A DRAFT', is_confirmed=False)

        record = self._mock_record('res.users', 'draft')

        result_a = self.Config.with_company(company_a).get_watermark_text(record)
        result_b = self.Config.with_company(company_b).get_watermark_text(record)

        self.assertEqual(result_a, 'COMPANY A DRAFT')
        self.assertFalse(result_b)  # No config for company B
