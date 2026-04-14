# Custom Field Builder for Odoo 19.0

A powerful module that allows you to create and manage custom fields dynamically in Odoo, similar to Odoo Studio functionality.

## Features

### Core Functionality
- **Dynamic Field Creation**: Create custom fields for any Odoo model without coding
- **Multiple Field Types**: Support for 12 field types including:
  - Text (Char)
  - Multiline Text
  - Integer
  - Float
  - Monetary
  - Boolean (Checkbox)
  - Date and DateTime
  - Selection (dropdown)
  - Many2one (relational)
  - Many2many (relational)
  - One2many (relational)

### Field Attributes
- **Basic Attributes**: Set fields as required, readonly, or invisible
- **Conditional Attributes**: Apply conditions dynamically based on other field values
  - Readonly conditions
  - Invisible conditions
  - Required conditions
- **Help Text**: Add tooltips and help text for user guidance
- **Default Values**: Set default values for fields
- **Field Tracking**: Enable change tracking (chatter integration)

### Security & Access Control
- **Group-based Security**: Restrict field visibility to specific user groups
- **Domain Filtering**: Apply domain filters for relational fields

### View Management
- **Automatic View Integration**: Fields are automatically added to form and tree views
- **Sequence Control**: Define field order with sequence numbers
- **Optional Display**: Fields appear as optional columns in tree views

## Installation

1. Copy the module folder to your Odoo addons directory:
   ```
   your_odoo/addons/custom_field_builder/
   ```

2. Update the apps list:
   - Go to Apps menu
   - Click "Update Apps List"
   - Remove the "Apps" filter
   - Search for "Custom Field Builder"

3. Install the module:
   - Click Install button

## Module Structure

```
custom_field_builder/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   └── custom_field.py
├── security/
│   └── ir.model.access.csv
├── views/
│   ├── custom_field_views.xml
│   └── menu_views.xml
├── static/
│   └── description/
│       └── icon.png (optional)
└── README.md
```

## Usage Guide

### Creating a Custom Field

1. Navigate to **Custom Fields > Custom Fields**
2. Click **Create**
3. Fill in the basic information:
   - **Model**: Select the model (e.g., res.partner, sale.order)
   - **Field Name**: Technical name starting with `x_` (e.g., `x_custom_rating`)
   - **Field Label**: User-friendly label (e.g., "Customer Rating")
   - **Field Type**: Select the appropriate type

4. Configure field properties based on type:

   **For Relational Fields (Many2one/Many2many/One2many):**
   - Select the Related Model
   - For One2many: Select the inverse relation field
   - Optionally add a domain filter

   **For Selection Fields:**
   - Add options in format: `key,Label` (one per line)
   - Example:
     ```
     draft,Draft
     confirmed,Confirmed
     done,Done
     ```

5. Set attributes:
   - Check **Required**, **Readonly**, or **Invisible** as needed
   - Add conditional logic if needed (Python domain syntax)
   - Add help text for users

6. Configure security (optional):
   - Select user groups who can see the field
   - Leave empty for all users

7. Click **Create Field** button

### Conditional Attributes Examples

**Readonly Condition:**
```python
[("state", "=", "done")]
```
Makes the field readonly when state is "done"

**Invisible Condition:**
```python
[("is_company", "=", False)]
```
Hides the field when is_company is False

**Required Condition:**
```python
[("country_id", "!=", False)]
```
Makes field required when country is selected

### Updating an Existing Field

1. Open the custom field record
2. Modify the attributes (cannot change name or type)
3. Click **Update Field**

### Deleting a Custom Field

1. Open the custom field record
2. Click **Delete Field**
3. Confirm the deletion

**Warning**: This permanently removes the field and its data!

## Field Naming Convention

- All custom field names **must** start with `x_`
- Use lowercase letters, numbers, and underscores only
- Examples: `x_rating`, `x_custom_date`, `x_project_ref`

## Technical Details

### How It Works

1. **Field Creation**: Creates an `ir.model.fields` record which adds the column to the database
2. **View Integration**: Creates inherited views (ir.ui.view) to display the field
3. **Registry Update**: Refreshes the Odoo registry to recognize the new field

### Database Schema

Custom fields are stored in the `custom_field_builder` table and linked to:
- `ir.model.fields`: The actual field definition
- `ir.model`: The target model
- `res.groups`: Security groups

### Limitations

- Cannot modify field name or type after creation
- One2many fields require an existing Many2one field on the related model
- Custom fields cannot be used in computed fields initially
- Some advanced field features may require manual customization

## Advanced Features

### Field Tracking
Enable "Track Changes" to log field modifications in the chatter

### Domain Filtering
For relational fields, you can add domain filters:
```python
[("customer_rank", ">", 0)]
```

### Multiple Views
Fields are automatically added to:
- Form view (in a custom group)
- Tree view (as optional column)

## Troubleshooting

### Field not appearing in views
- Check if the field is marked as invisible
- Verify security groups allow your user to see it
- Clear browser cache and restart Odoo

### Error creating field
- Ensure field name starts with `x_`
- Verify the model exists and is not transient
- Check that relational models are correctly selected

### Permission errors
- Ensure you have System Administrator rights
- Check that the security rules are properly installed

## Best Practices

1. **Naming**: Use descriptive names like `x_customer_rating` not `x_cr`
2. **Documentation**: Always add help text for user guidance
3. **Testing**: Test fields in a development environment first
4. **Backup**: Backup your database before deleting fields
5. **Performance**: Avoid creating too many fields on heavily-used models
6. **Organization**: Use sequence numbers to organize related fields together

## Future Enhancements

Potential features for future versions:
- Computed fields support
- Related fields support
- Custom widgets
- View position control (before/after specific fields)
- Bulk field operations
- Field templates
- Export/import field definitions
- Kanban view integration
- Search view customization

## Support

For issues, questions, or contributions:
- Check Odoo documentation: https://www.odoo.com/documentation/19.0/
- Review Odoo community forums
- Submit issues or pull requests to the repository

## License

LGPL-3

## Author

Your Name / Your Company

## Version History

- **1.0.0** (2025-01-21): Initial MVP release
  - Basic field creation
  - Support for 12 field types
  - Conditional attributes
  - View integration
  - Security controls
