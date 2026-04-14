from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError, AccessError
import logging

_logger = logging.getLogger(__name__)


class FieldEditor(models.Model):
    _name = 'field.editor'
    _description = 'Field Editor - Modify Existing Fields'
    _order = 'model_id, field_id'

    @api.model
    def default_get(self, fields_list):
        """Override to check if feature is enabled"""
        self._check_field_editor_enabled()
        return super(FieldEditor, self).default_get(fields_list)

    name = fields.Char('Field Name', related='field_id.name', readonly=True, store=True)
    model_id = fields.Many2one('ir.model', string='Model', required=True,
                               domain=[('transient', '=', False)],
                               ondelete='cascade')
    field_id = fields.Many2one('ir.model.fields', string='Field', required=True, 
                               ondelete='cascade',
                               domain="[('model_id', '=', model_id), ('model_id.transient', '=', False)]")
    model_name = fields.Char(related='model_id.model', string='Model Name', 
                            readonly=True, store=True)
    
    # Field information (readonly - for display)
    field_description = fields.Char('Current Label', related='field_id.field_description', 
                                    readonly=True)
    field_type = fields.Selection(related='field_id.ttype', string='Field Type', 
                                  readonly=True)
    field_state = fields.Selection(related='field_id.state', string='Field State', 
                                   readonly=True)
    is_custom_field = fields.Boolean('Is Custom Field', compute='_compute_is_custom_field', 
                                     store=True)
    
    # Editable attributes
    new_field_description = fields.Char('New Label', 
                                        help='Change the field label shown to users')
    new_help_text = fields.Text('Help Text',
                                help='Add or update help text for the field')
    
    # Conditional attributes
    readonly_condition = fields.Char('Readonly Condition',
                                     help='Domain expression for readonly condition')
    invisible_condition = fields.Char('Invisible Condition',
                                      help='Domain expression for invisible condition')
    required_condition = fields.Char('Required Condition',
                                     help='Domain expression for required condition')
    
    # View management
    groups_ids = fields.Many2many('res.groups', string='Restrict to Groups',
                                  help='Limit field visibility to specific user groups')
    view_position = fields.Selection([
        ('keep', 'Keep Original Position'),
        ('before_notebook', 'Before Notebook/Tabs'),
        ('after_notebook', 'After Notebook/Tabs'),
        ('top', 'Top of Form'),
        ('bottom', 'Bottom of Form'),
    ], string='Position in Form', default='keep',
       help='Where to position the field (creates view inheritance)')
    
    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
    ], default='draft', required=True)
    
    active = fields.Boolean(default=True)
    modification_note = fields.Text('Modification Notes',
                                    help='Document why this field was modified')

    @api.model
    def create(self, vals):
        # Check if field editor is enabled
        self._check_field_editor_enabled()
        return super(FieldEditor, self).create(vals)
    
    def write(self, vals):
        # Check if field editor is enabled
        self._check_field_editor_enabled()
        return super(FieldEditor, self).write(vals)
    
    def _check_field_editor_enabled(self):
        """Check if field editor feature is enabled"""
        config = self.env['custom.field.config'].search([], limit=1)
        if not config or not config.enable_field_editor:
            raise AccessError(_(
                'Field Editor is disabled. '
                'Please enable it in Custom Fields > Configuration > Settings.'
            ))

    @api.depends('field_id.state')
    def _compute_is_custom_field(self):
        for record in self:
            # Custom fields have state='manual'
            record.is_custom_field = record.field_id.state == 'manual'

    @api.onchange('field_id')
    def _onchange_field_id(self):
        """Pre-fill values when selecting a field"""
        if self.field_id:
            self.new_field_description = self.field_id.field_description
            self.new_help_text = self.field_id.help

    def action_apply_modifications(self):
        """Apply the modifications to the field"""
        self.ensure_one()
        
        # Check if field editor is enabled
        config = self.env['custom.field.config'].search([], limit=1)
        if not config or not config.enable_field_editor:
            raise UserError(_(
                'Field Editor is disabled. '
                'Please enable it in Custom Fields > Configuration > Settings.'
            ))
        
        # Warn if modifying a system field
        if not self.is_custom_field:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Warning: Modifying System Field',
                'res_model': 'field.editor.warning',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_field_editor_id': self.id,
                    'default_field_name': self.field_id.field_description,
                    'default_model_name': self.model_id.name,
                }
            }
        
        # Apply modifications for custom fields
        self._apply_safe_modifications()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Field modifications applied successfully'),
                'type': 'success',
            }
        }

    def _apply_safe_modifications(self):
        """Apply safe modifications to the field"""
        self.ensure_one()
        
        # Update field definition (safe attributes only)
        vals = {}
        if self.new_field_description:
            vals['field_description'] = self.new_field_description
        if self.new_help_text:
            vals['help'] = self.new_help_text
        if self.groups_ids:
            vals['groups'] = [(6, 0, self.groups_ids.ids)]
        
        if vals:
            self.field_id.write(vals)
        
        # Create/update view inheritance for conditional attributes
        if any([self.readonly_condition, self.invisible_condition, 
                self.required_condition, self.view_position != 'keep']):
            self._create_or_update_view_inheritance()
        
        self.write({'state': 'active'})

    def _create_or_update_view_inheritance(self):
        """Create view inheritance for conditional attributes"""
        self.ensure_one()
        
        # Find primary form view for the model
        view_obj = self.env['ir.ui.view']
        form_view = view_obj.search([
            ('model', '=', self.model_id.model),
            ('type', '=', 'form'),
            ('mode', '=', 'primary')
        ], limit=1)
        
        if not form_view:
            _logger.warning(f'No primary form view found for model {self.model_id.model}')
            return
        
        # Check if we already created an inherited view
        existing_view = view_obj.search([
            ('model', '=', self.model_id.model),
            ('name', '=', f'{self.model_id.model}.field.editor.{self.field_id.name}')
        ], limit=1)
        
        if existing_view:
            existing_view.unlink()
        
        # Build attributes string
        attrs = self._build_field_attrs()
        attrs_str = ' '.join([f'{k}="{v}"' for k, v in attrs.items()]) if attrs else ''
        
        # Determine XPath based on position
        if self.view_position == 'keep':
            # Try to find the field in the view and modify its attributes
            xpath_expr = f"//field[@name='{self.field_id.name}']"
            position = 'attributes'
            
            arch_content = ''
            for attr_name, attr_value in attrs.items():
                arch_content += f'<attribute name="{attr_name}">{attr_value}</attribute>\n                '
            
            arch = f'''<?xml version="1.0"?>
<data>
    <xpath expr="{xpath_expr}" position="{position}">
        {arch_content}
    </xpath>
</data>'''
        else:
            # Move field to new position (more complex - future enhancement)
            _logger.info(f'Position change requested for {self.field_id.name} - feature coming soon')
            arch = f'''<?xml version="1.0"?>
<data>
    <xpath expr="//field[@name='{self.field_id.name}']" position="attributes">
        {attrs_str and f'<attribute name="attrs">{attrs_str}</attribute>' or ''}
    </xpath>
</data>'''
        
        # Create the inherited view
        view_vals = {
            'name': f'{self.model_id.model}.field.editor.{self.field_id.name}',
            'model': self.model_id.model,
            'inherit_id': form_view.id,
            'arch': arch,
            'active': True,
        }
        
        view_obj.create(view_vals)

    def _build_field_attrs(self):
        """Build field attributes dictionary for view modifications"""
        attrs = {}
        
        conditions = {}
        if self.readonly_condition:
            conditions['readonly'] = self.readonly_condition
        if self.invisible_condition:
            conditions['invisible'] = self.invisible_condition
        if self.required_condition:
            conditions['required'] = self.required_condition
        
        if conditions:
            attrs['attrs'] = str(conditions)
        
        return attrs

    def action_reset_modifications(self):
        """Remove all modifications and restore field to original state"""
        self.ensure_one()
        
        # Remove view inheritance
        view_obj = self.env['ir.ui.view']
        views = view_obj.search([
            ('model', '=', self.model_id.model),
            ('name', '=', f'{self.model_id.model}.field.editor.{self.field_id.name}')
        ])
        views.unlink()
        
        self.write({'state': 'draft'})
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Field modifications removed'),
                'type': 'success',
            }
        }


class FieldEditorWarning(models.TransientModel):
    _name = 'field.editor.warning'
    _description = 'Field Editor Warning Dialog'

    field_editor_id = fields.Many2one('field.editor', string='Field Editor', required=True)
    field_name = fields.Char('Field Name', readonly=True)
    model_name = fields.Char('Model Name', readonly=True)
    confirmation = fields.Boolean('I understand the risks')

    def action_confirm(self):
        """User confirmed they understand the risks"""
        self.ensure_one()
        if not self.confirmation:
            raise UserError(_('Please confirm that you understand the risks before proceeding.'))
        
        # Apply modifications
        self.field_editor_id._apply_safe_modifications()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Field modifications applied successfully'),
                'type': 'success',
            }
        }

    def action_cancel(self):
        """User cancelled"""
        return {'type': 'ir.actions.act_window_close'}
