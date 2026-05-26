from odoo import api, fields, models

CANCEL_BYPASS_KEY = 'consultive_cancel_reason.bypass'

_KNOWN_CANCEL_METHODS = ['action_cancel', 'button_cancel', 'action_refuse']


class ConsultiveCancelModelConfig(models.Model):
    _name = 'consultive.cancel.model.config'
    _description = 'Cancel Intercepted Model'
    _order = 'sequence, id'

    model_id = fields.Many2one(
        'ir.model',
        string='Model',
        required=True,
        ondelete='cascade',
    )
    model_name = fields.Char(
        related='model_id.model',
        store=True,
        string='Model Technical Name',
    )
    label = fields.Char(
        string='Display Label',
        help='How this document type appears in the cancellation log.',
    )
    cancel_method = fields.Char(
        string='Cancel Method',
        readonly=True,
        help='Auto-detected when the config record is saved.',
    )
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)

    _sql_constraints = [
        ('model_unique', 'UNIQUE(model_id)', 'Each model can only be configured once.'),
    ]

    # -------------------------------------------------------------------------
    # ORM overrides
    # -------------------------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            if not rec.cancel_method:
                rec.cancel_method = rec._detect_cancel_method()
            if not rec.label:
                rec.label = rec.model_id.name
        self._apply_all_patches()
        return records

    def write(self, vals):
        result = super().write(vals)
        self._apply_all_patches()
        return result

    def unlink(self):
        self._revert_all_patches()
        result = super().unlink()
        remaining = (
            self.env['consultive.cancel.model.config']
            .with_context(active_test=False)
            .sudo()
            .search([('active', '=', True)])
        )
        remaining._apply_patches()
        return result

    # -------------------------------------------------------------------------
    # Startup hook — called by Odoo after all modules are loaded
    # -------------------------------------------------------------------------

    def _register_hook(self):
        super()._register_hook()
        active_configs = (
            self.with_context(active_test=False).sudo().search([('active', '=', True)])
        )
        active_configs._apply_patches()

    # -------------------------------------------------------------------------
    # Patch management
    # -------------------------------------------------------------------------

    def _apply_all_patches(self):
        """Revert all known patches then re-apply only active ones.

        Must use active_test=False so that just-disabled records are included
        in the revert pass — otherwise Odoo's auto-filter silently excludes them
        and their class-level patch is never removed.
        """
        all_configs = self.with_context(active_test=False).sudo().search([])
        all_configs._revert_patches()
        active_configs = all_configs.filtered('active')
        active_configs._apply_patches()

    def _revert_all_patches(self):
        all_configs = self.with_context(active_test=False).sudo().search([])
        all_configs._revert_patches()

    def _apply_patches(self):
        for config in self:
            config._apply_patch()

    def _revert_patches(self):
        for config in self:
            config._revert_patch()

    def _apply_patch(self):
        self.ensure_one()
        model_name = self.model_name
        if not model_name or model_name not in self.env:
            return

        method_name = self.cancel_method or 'action_cancel'
        model_cls = type(self.env[model_name])

        if not hasattr(model_cls, method_name):
            return

        patched_flag = f'_consultive_patched_{method_name}'
        if not getattr(model_cls, patched_flag, False):
            original = getattr(model_cls, method_name)
            bypass_key = CANCEL_BYPASS_KEY

            def intercepted_cancel(self_record, *args, **kwargs):
                if self_record.env.context.get(bypass_key):
                    return original(self_record, *args, **kwargs)
                return self_record.env['consultive.cancel.wizard']._open_wizard(
                    self_record._name, self_record.ids
                )

            # _patch_method was removed in Odoo 19 — use setattr directly on the registry class
            original_attr = f'_consultive_original_{method_name}'
            setattr(model_cls, original_attr, original)
            setattr(model_cls, method_name, intercepted_cancel)
            setattr(model_cls, patched_flag, True)

        self._apply_button_view_override()

    def _revert_patch(self):
        self.ensure_one()
        model_name = self.model_name
        if not model_name or model_name not in self.env:
            return

        method_name = self.cancel_method or 'action_cancel'
        model_cls = type(self.env[model_name])

        patched_flag = f'_consultive_patched_{method_name}'
        if getattr(model_cls, patched_flag, False):
            original_attr = f'_consultive_original_{method_name}'
            original = getattr(model_cls, original_attr, None)
            if original is not None:
                setattr(model_cls, method_name, original)
                delattr(model_cls, original_attr)
            setattr(model_cls, patched_flag, False)

        self._revert_button_view_override()

    # -------------------------------------------------------------------------
    # View-level: strip confirm attribute from cancel buttons
    # -------------------------------------------------------------------------

    def _apply_button_view_override(self):
        """Create ir.ui.view overrides to remove confirm dialogs from cancel buttons.

        Some Odoo form views attach a browser-level confirm="…" attribute to the
        cancel button.  That dialog fires before our server-side intercept, giving
        users two sequential popups.  We fix this by creating lightweight view
        inheritance records that clear the attribute for any affected form view.
        """
        self.ensure_one()
        if not self.model_name or not self.cancel_method:
            return

        model_name = self.model_name
        method_name = self.cancel_method

        try:
            from lxml import etree  # always available in Odoo
        except ImportError:
            return

        form_views = self.env['ir.ui.view'].sudo().search([
            ('model', '=', model_name),
            ('type', '=', 'form'),
            ('active', '=', True),
        ])

        for view in form_views:
            try:
                arch = view.arch_base or ''
                if not arch:
                    continue
                tree = etree.fromstring(arch.encode('utf-8') if isinstance(arch, str) else arch)
                if not tree.xpath(f'//button[@name="{method_name}"][@confirm]'):
                    continue
            except Exception:
                continue

            override_name = f'consultive.noconfirm.{model_name}.{method_name}.{view.id}'
            if self.env['ir.ui.view'].sudo().search_count([('name', '=', override_name)]):
                continue

            self.env['ir.ui.view'].sudo().create({
                'name': override_name,
                'model': model_name,
                'inherit_id': view.id,
                'arch_base': (
                    f'<data>'
                    f'<xpath expr="//button[@name=\'{method_name}\']"'
                    f' position="attributes">'
                    f'<attribute name="confirm"></attribute>'
                    f'</xpath>'
                    f'</data>'
                ),
                'active': True,
            })

    def _revert_button_view_override(self):
        """Delete any view overrides previously created by _apply_button_view_override."""
        self.ensure_one()
        if not self.model_name or not self.cancel_method:
            return

        prefix = f'consultive.noconfirm.{self.model_name}.{self.cancel_method}.'
        overrides = self.env['ir.ui.view'].sudo().search([
            ('name', 'like', prefix),
            ('model', '=', self.model_name),
        ])
        if overrides:
            overrides.sudo().unlink()

    # -------------------------------------------------------------------------
    # Auto-detection
    # -------------------------------------------------------------------------

    def _detect_cancel_method(self):
        self.ensure_one()
        if not self.model_name or self.model_name not in self.env:
            return 'action_cancel'
        model_cls = type(self.env[self.model_name])
        for method in _KNOWN_CANCEL_METHODS:
            if method in model_cls.__dict__ or any(
                method in klass.__dict__ for klass in model_cls.__mro__
                if klass not in (object,)
            ):
                return method
        return 'action_cancel'
