import json

from odoo.tests.common import TransactionCase


class CancelReasonTestCommon(TransactionCase):
    """Base class for all consultive_mandatory_cancel_reason tests."""

    _TEST_REASON_NAMES = ('Autotest Alpha Reason', 'Autotest Beta Reason')

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Reason = cls.env['consultive.cancel.reason']
        cls.Wizard = cls.env['consultive.cancel.wizard']
        # Remove any stale records left by a previously crashed test run so that
        # the UNIQUE constraint never blocks setUpClass.
        cls.Reason.with_context(active_test=False).search(
            [('name', 'in', list(cls._TEST_REASON_NAMES))]
        ).unlink()
        cls.reason_a = cls.Reason.create({'name': 'Autotest Alpha Reason'})
        cls.reason_b = cls.Reason.create({'name': 'Autotest Beta Reason'})

    def setUp(self):
        super().setUp()
        # Class-level method patches (setattr on registry class) are NOT rolled
        # back when DB savepoints roll back. Re-apply all active patches before
        # every test so that reversion tests in a prior class don't leave the
        # cancel methods unpatched for subsequent test classes.
        (
            self.env['consultive.cancel.model.config']
            .with_context(active_test=False)
            .sudo()
            .search([('active', '=', True)])
            ._apply_patches()
        )

    def _make_wizard(self, res_model, res_ids, reason, note=None):
        """Create and return a wizard record ready to confirm."""
        vals = {
            'reason_id': reason.id,
            'res_model': res_model,
            'res_ids': json.dumps(res_ids),
        }
        if note is not None:
            vals['note'] = note
        return self.Wizard.create(vals)
