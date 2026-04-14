from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class CustomFieldBuilder(models.Model):
    _name = 'custom.field.builder'
    _description = 'Custom Field Builder'
    _order = 'model_id, sequence, id'

    name = fields.Char('Field Name', required=True, help='Technical name of the field (e.g., x_custom_field)')
    field_description = fields.Char('Field Label', required=True, help='Label shown in the interface')
    model_id = fields.Many2one('ir.model', string='Model', required=True, ondelete='cascade',
                                domain=[('transient', '=', False)])
    model_name = fields.Char(related='model_id.model', string='Model Name', store=True)
    
    field_type = fields.Selection([
        ('char', 'Text'),
        ('text', 'Multiline Text'),
        ('integer', 'Integer'),
        ('float', 'Float'),
        ('monetary', 'Monetary'),
        ('boolean', 'Checkbox'),
        ('date', 'Date'),
        ('datetime', 'Date & Time'),
        ('selection', 'Selection'),
        ('many2one', 'Many2one'),
        ('many2many', 'Many2many'),
        ('one2many', 'One2many'),
    ], string='Field Type', required=True, default='char')
    
    # Relational field settings
    relation_model_id = fields.Many2one('ir.model', string='Related Model',
                                         help='Model for relational fields')
    relation_field_id = fields.Many2one('ir.model.fields', string='Relation Field',
                                         help='Field for one2many inverse relation')
    
    # Selection field settings
    selection_options = fields.Text('Selection Options',
                                     help='Options for selection field (one per line: key,Label)')
    
    # Field attributes
    required = fields.Boolean('Required', default=False)
    readonly = fields.Boolean('Readonly', default=False)
    invisible = fields.Boolean('Invisible', default=False)
    track_visibility = fields.Boolean('Track Changes', default=False)
    help_text = fields.Text('Help Text')
    default_value = fields.Char('Default Value')
    
    # Domain and conditions
    domain = fields.Char('Domain', help='Domain for filtering (Python expression)')
    readonly_condition = fields.Char('Readonly Condition', 
                                      help='Domain expression for readonly condition')
    invisible_condition = fields.Char('Invisible Condition',
                                       help='Domain expression for invisible condition')
    required_condition = fields.Char('Required Condition',
                                      help='Domain expression for required condition')
    
    # View management
    sequence = fields.Integer('Sequence', default=10)
    view_position = fields.Selection([
        ('before_notebook', 'Before Notebook/Tabs'),
        ('after_notebook', 'After Notebook/Tabs'),
        ('top', 'Top of Form'),
        ('bottom', 'Bottom of Form'),
        ('first_group', 'First Group'),
    ], string='Position in Form', default='before_notebook',
       help='Where to place the field in the form view')
    groups_ids = fields.Many2many('res.groups', string='Groups',
                                   help='User groups that can see this field')
    
    # Technical fields
    field_id = fields.Many2one('ir.model.fields', string='Created Field', readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('archived', 'Archived')
    ], default='draft', required=True)
    
    active = fields.Boolean(default=True)

    @api.constrains('name')
    def _check_field_name(self):
        for record in self:
            if not record.name.startswith('x_'):
                raise ValidationError(_('Custom field names must start with "x_"'))
            if not record.name.replace('_', '').isalnum():
                raise ValidationError(_('Field name can only contain letters, numbers and underscores'))

    @api.constrains('field_type', 'relation_model_id')
    def _check_relational_fields(self):
        for record in self:
            if record.field_type in ('many2one', 'many2many', 'one2many'):
                if not record.relation_model_id:
                    raise ValidationError(_('Related Model is required for relational fields'))

    def action_create_field(self):
        """Create the actual field in the database"""
        self.ensure_one()
        
        if self.field_id:
            raise UserError(_('Field already created. Use Update instead.'))
        
        # Prepare field values
        field_vals = self._prepare_field_values()
        
        # Create the ir.model.fields record
        field = self.env['ir.model.fields'].create(field_vals)
        
        # Update the model and registry
        self.env['base'].flush_model()
        self.env.registry.init_models(self.env.cr, [self.model_id.model], 
                                       dict(self.env.context, update_custom_fields=True))
        
        self.write({'field_id': field.id, 'state': 'active'})
        
        # Add field to views
        self._add_field_to_views()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Field created successfully'),
                'type': 'success',
                'sticky': False,
            }
        }

    def action_update_field(self):
        """Update existing field attributes"""
        self.ensure_one()
        
        if not self.field_id:
            raise UserError(_('No field to update. Create it first.'))
        
        # Update field values
        field_vals = self._prepare_field_values()
        field_vals.pop('name', None)  # Cannot change field name
        field_vals.pop('ttype', None)  # Cannot change field type
        
        self.field_id.write(field_vals)
        
        # Refresh views
        self._update_field_in_views()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Field updated successfully'),
                'type': 'success',
            }
        }

    def action_delete_field(self):
        """Delete the field from model and views"""
        self.ensure_one()
        
        if self.field_id:
            # Remove from views first
            self._remove_field_from_views()
            
            # Delete the field
            self.field_id.unlink()
            
            # Clear registry
            self.env.registry.init_models(self.env.cr, [self.model_id.model],
                                          dict(self.env.context, update_custom_fields=True))
        
        self.write({'state': 'archived', 'active': False})
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Field deleted successfully'),
                'type': 'success',
            }
        }

    def _prepare_field_values(self):
        """Prepare values for ir.model.fields creation"""
        vals = {
            'name': self.name,
            'field_description': self.field_description,
            'model_id': self.model_id.id,
            'model': self.model_id.model,
            'ttype': self.field_type,
            'required': self.required,
            'readonly': self.readonly,
            'help': self.help_text or '',
            'tracking': self.track_visibility,
        }
        
        # Handle relational fields
        if self.field_type in ('many2one', 'many2many', 'one2many'):
            vals['relation'] = self.relation_model_id.model
            
        if self.field_type == 'one2many' and self.relation_field_id:
            vals['relation_field'] = self.relation_field_id.name
        
        # Handle selection field
        if self.field_type == 'selection' and self.selection_options:
            selection_list = []
            for line in self.selection_options.split('\n'):
                if ',' in line:
                    key, label = line.split(',', 1)
                    selection_list.append((key.strip(), label.strip()))
            vals['selection'] = str(selection_list)
        
        # Handle monetary field
        if self.field_type == 'monetary':
            vals['ttype'] = 'monetary'
        
        # Add domain if specified
        if self.domain:
            vals['domain'] = self.domain
        
        # Add groups
        if self.groups_ids:
            vals['groups'] = [(6, 0, self.groups_ids.ids)]
        
        return vals

    def _add_field_to_views(self):
        """Add field to form and list views"""
        self.ensure_one()
        
        # Get existing views for the model
        view_obj = self.env['ir.ui.view']
        form_views = view_obj.search([
            ('model', '=', self.model_id.model),
            ('type', '=', 'form'),
            ('mode', '=', 'primary')
        ], limit=1)
        
        list_views = view_obj.search([
            ('model', '=', self.model_id.model),
            ('type', '=', 'list'),
            ('mode', '=', 'primary')
        ], limit=1)
        
        # Create inherited views to add the field
        if form_views and not self.invisible:
            self._create_form_view_inherit(form_views[0])
        
        if list_views and not self.invisible:
            self._create_list_view_inherit(list_views[0])

    def _create_form_view_inherit(self, parent_view):
        """Create an inherited form view to add the custom field"""
        # Get section label from config
        config = self.env['custom.field.config'].search([], limit=1)
        section_label = config.default_section_label if config else 'Additional Fields'
        
        # Build field attributes
        attrs = self._build_field_attrs()
        attrs_str = ' '.join([f'{k}="{v}"' for k, v in attrs.items()])
        
        # Determine XPath based on position
        xpath_expr, position = self._get_form_xpath_position()
        
        # Create XPath to add field
        arch = f'''<?xml version="1.0"?>
<data>
    <xpath expr="{xpath_expr}" position="{position}">
        <group name="custom_fields_{self.id}" string="{section_label}">
            <field name="{self.name}" {attrs_str}/>
        </group>
    </xpath>
</data>'''
        
        view_vals = {
            'name': f'{self.model_id.model}.custom.field.{self.name}',
            'model': self.model_id.model,
            'inherit_id': parent_view.id,
            'arch': arch,
            'active': True,
        }
        
        self.env['ir.ui.view'].create(view_vals)
    
    def _get_form_xpath_position(self):
        """Get XPath expression and position based on view_position setting"""
        position_map = {
            'before_notebook': ('//form/sheet/notebook', 'before'),
            'after_notebook': ('//form/sheet/notebook', 'after'),
            'top': ('//form/sheet', 'before'),
            'bottom': ('//form/sheet', 'inside'),
            'first_group': ('//form/sheet/group[1]', 'inside'),
        }
        
        xpath_expr, position = position_map.get(self.view_position, ('//form/sheet/notebook', 'before'))
        
        # Fallback to bottom if notebook doesn't exist
        if 'notebook' in xpath_expr:
            # Check if the view has a notebook
            try:
                view = self.env['ir.ui.view'].search([
                    ('model', '=', self.model_id.model),
                    ('type', '=', 'form'),
                    ('mode', '=', 'primary')
                ], limit=1)
                if view and 'notebook' not in (view.arch or ''):
                    # No notebook found, use bottom instead
                    xpath_expr, position = '//form/sheet', 'inside'
            except:
                pass
        
        return xpath_expr, position

    def _create_list_view_inherit(self, parent_view):
        """Create an inherited list view to add the custom field"""
        arch = f'''<?xml version="1.0"?>
<data>
    <xpath expr="//list" position="inside">
        <field name="{self.name}" optional="hide"/>
    </xpath>
</data>'''
        
        view_vals = {
            'name': f'{self.model_id.model}.custom.field.list.{self.name}',
            'model': self.model_id.model,
            'inherit_id': parent_view.id,
            'arch': arch,
            'active': True,
        }
        
        self.env['ir.ui.view'].create(view_vals)

    def _build_field_attrs(self):
        """Build field attributes dictionary"""
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
        
        if self.groups_ids:
            attrs['groups'] = ','.join(self.groups_ids.mapped('full_name'))
        
        return attrs

    def _update_field_in_views(self):
        """Update field in existing views"""
        # Find and remove old inherited views
        view_obj = self.env['ir.ui.view']
        views = view_obj.search([
            ('model', '=', self.model_id.model),
            ('name', 'like', f'%.custom.field.{self.name}%')
        ])
        views.unlink()
        
        # Recreate views with updated settings
        self._add_field_to_views()

    def _remove_field_from_views(self):
        """Remove field from views"""
        view_obj = self.env['ir.ui.view']
        views = view_obj.search([
            ('model', '=', self.model_id.model),
            ('name', 'like', f'%.custom.field.{self.name}%')
        ])
        views.unlink()
