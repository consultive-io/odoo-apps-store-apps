from odoo.tests.common import tagged

from .common import CancelReasonTestCommon


@tagged('consultive_mandatory_cancel_reason', 'cancel_dynamic_config', 'post_install', '-at_install')
class TestDynamicConfig(CancelReasonTestCommon):
    """Tests for config-driven dynamic model patching."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Config = cls.env['consultive.cancel.model.config']
        cls.IrModel = cls.env['ir.model']

    # -------------------------------------------------------------------------
    # Auto-detect tests
    # -------------------------------------------------------------------------

    def test_auto_detect_action_cancel(self):
        """Config for sale.order should auto-detect action_cancel."""
        so_model = self.IrModel.search([('model', '=', 'sale.order')], limit=1)
        # Remove pre-seeded record to test fresh creation
        existing = self.Config.search([('model_name', '=', 'sale.order')], limit=1)
        existing.unlink()

        config = self.Config.create({'model_id': so_model.id, 'label': 'Test Sale'})
        self.assertEqual(config.cancel_method, 'action_cancel')

    def test_auto_detect_button_cancel(self):
        """Config for purchase.order should auto-detect button_cancel."""
        po_model = self.IrModel.search([('model', '=', 'purchase.order')], limit=1)
        existing = self.Config.search([('model_name', '=', 'purchase.order')], limit=1)
        existing.unlink()

        config = self.Config.create({'model_id': po_model.id, 'label': 'Test PO'})
        self.assertEqual(config.cancel_method, 'button_cancel')

    # -------------------------------------------------------------------------
    # Patch application test
    # -------------------------------------------------------------------------

    def test_patch_applied_on_config_create(self):
        """Creating a config record should patch the model's cancel method."""
        existing = self.Config.search([('model_name', '=', 'sale.order')], limit=1)
        existing.unlink()

        so_model = self.IrModel.search([('model', '=', 'sale.order')], limit=1)
        self.Config.create({'model_id': so_model.id, 'label': 'Sale Order'})

        patched = getattr(type(self.env['sale.order']), '_consultive_patched_action_cancel', False)
        self.assertTrue(patched, 'action_cancel on sale.order must be patched after config create.')

    # -------------------------------------------------------------------------
    # Full cancel flow via dynamically created config
    # -------------------------------------------------------------------------

    def test_cancel_flow_via_dynamic_config(self):
        """Re-adding config dynamically re-patches the model and intercepts cancel."""
        # Remove pre-seeded record
        existing = self.Config.search([('model_name', '=', 'sale.order')], limit=1)
        existing.unlink()

        # Re-add dynamically
        so_model = self.IrModel.search([('model', '=', 'sale.order')], limit=1)
        self.Config.create({'model_id': so_model.id, 'label': 'Sale Order (Dynamic)'})

        # Cancellation must be intercepted
        partner = self.env['res.partner'].search([], limit=1)
        so = self.env['sale.order'].create({'partner_id': partner.id})
        action = so.action_cancel()
        self.assertIsInstance(action, dict)
        self.assertEqual(
            action.get('res_model'), 'consultive.cancel.wizard',
            'Cancel must open the wizard when config is active.',
        )
        self.assertEqual(so.state, 'draft', 'SO must still be draft — cancel intercepted.')

        # Confirm via wizard and verify log label uses dynamic label
        wizard = self._make_wizard('sale.order', so.ids, self.reason_a)
        wizard.action_do_cancel()
        log = self.env['consultive.cancel.log'].search([('res_model', '=', 'sale.order')], limit=1)
        self.assertEqual(log.res_model_label, 'Sale Order (Dynamic)')

    # -------------------------------------------------------------------------
    # Reversion tests
    # -------------------------------------------------------------------------

    def test_reversion_on_disable(self):
        """Disabling a config record must remove the cancel intercept."""
        config = self.Config.search([('model_name', '=', 'sale.order')], limit=1)
        config.active = False  # triggers write → _apply_all_patches → reverts sale.order patch

        # Cancel must now go straight through (state changes directly)
        partner = self.env['res.partner'].search([], limit=1)
        so = self.env['sale.order'].create({'partner_id': partner.id})
        result = so.action_cancel()
        # When not intercepted, action_cancel returns None or a dict that is NOT the wizard
        wizard_opened = isinstance(result, dict) and result.get('res_model') == 'consultive.cancel.wizard'
        self.assertFalse(wizard_opened, 'Cancel must not open wizard when config is disabled.')

    def test_reversion_on_unlink(self):
        """Deleting a config record must remove the cancel intercept."""
        config = self.Config.search([('model_name', '=', 'sale.order')], limit=1)
        config.unlink()  # triggers unlink → _revert_all_patches → re-apply remaining

        # sale.order cancel must not be intercepted
        partner = self.env['res.partner'].search([], limit=1)
        so = self.env['sale.order'].create({'partner_id': partner.id})
        result = so.action_cancel()
        wizard_opened = isinstance(result, dict) and result.get('res_model') == 'consultive.cancel.wizard'
        self.assertFalse(wizard_opened, 'Cancel must not open wizard after config is deleted.')
