from odoo import models, fields, api
from odoo.exceptions import ValidationError


class CustomFieldConfig(models.Model):
    _name = 'custom.field.config'
    _description = 'Custom Field Builder Configuration'
    
    name = fields.Char('Configuration', default='Custom Field Settings', required=True)
    default_section_label = fields.Char('Default Section Label', 
                                        default='Additional Fields',
                                        required=True,
                                        help='Default label for the section containing custom fields in forms')
    enable_field_editor = fields.Boolean('Enable Field Editor', 
                                         default=False,
                                         help='Allow editing of existing model fields. '
                                              'WARNING: Enabling this feature allows modification of system fields. '
                                              'Only enable if you understand the risks.')
    
    @api.model
    def create(self, vals):
        # Allow creation only if no record exists
        existing = self.search([])
        if existing:
            raise ValidationError('Only one configuration record is allowed. Please edit the existing one.')
        record = super(CustomFieldConfig, self).create(vals)
        self._toggle_field_editor_menu(vals.get('enable_field_editor', False))
        return record
    
    def write(self, vals):
        result = super(CustomFieldConfig, self).write(vals)
        if 'enable_field_editor' in vals:
            self._toggle_field_editor_menu(vals['enable_field_editor'])
        return result
    
    def _toggle_field_editor_menu(self, enabled):
        """Show/hide field editor menu based on configuration"""
        menu = self.env.ref('custom_field_builder.menu_field_editor', raise_if_not_found=False)
        if menu:
            menu.active = enabled
    
    @api.constrains('name')
    def _check_single_record(self):
        # Ensure only one record exists
        if self.search_count([]) > 1:
            raise ValidationError('Only one configuration record is allowed!')
