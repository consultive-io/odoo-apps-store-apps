from odoo.tests.common import tagged
from odoo.tools import mute_logger

from .common import CancelReasonTestCommon


@tagged('consultive_mandatory_cancel_reason', 'cancel_reason')
class TestCancelReason(CancelReasonTestCommon):
    """Tests for the consultive.cancel.reason model."""

    def test_name_required(self):
        with mute_logger('odoo.sql_db'), self.assertRaises(Exception):
            self.Reason.create({'name': False})

    def test_active_default_true(self):
        reason = self.Reason.create({'name': 'Test Active Default'})
        self.assertTrue(reason.active)

    def test_unique_name_constraint(self):
        with mute_logger('odoo.sql_db'), self.assertRaises(Exception):
            self.Reason.create({'name': self.reason_a.name})

    def test_archived_reason_excluded_from_wizard_domain(self):
        archived = self.Reason.create({'name': 'Old Reason', 'active': False})
        active_ids = self.Reason.search([('active', '=', True)]).ids
        self.assertNotIn(archived.id, active_ids)

    def test_wizard_view_exists(self):
        views = self.env['ir.ui.view'].search([
            ('model', '=', 'consultive.cancel.wizard'),
        ])
        self.assertTrue(views, 'Wizard form view must exist after module install.')

    def test_cancel_reason_view_exists(self):
        views = self.env['ir.ui.view'].search([
            ('model', '=', 'consultive.cancel.reason'),
        ])
        self.assertTrue(views, 'Cancel reason list/form views must exist.')
