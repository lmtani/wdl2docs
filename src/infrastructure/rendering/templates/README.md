# Jinja2 Template Organization

This document describes the organization of Jinja2 templates in the WDL Atlas project.

## Directory Structure

```
src/infrastructure/rendering/templates/
├── macros/              # Reusable macros
│   ├── badges.html      # Badges (workflow, task, mixed, external, etc.)
│   ├── tables.html      # Tables (inputs, outputs, runtime, imports, etc.)
│   └── lists.html       # Lists of WDL files
├── components/          # Complex components
│   ├── buttons.html     # Action buttons (graph, source)
│   ├── document.html    # WDL document-specific components
│   ├── modals.html      # Modals (graph and source code)
│   ├── stats.html       # Statistic cards
│   └── tabs.html        # Tab system
├── static/              # Static files (CSS, JS, images)
├── base.html            # Base template
├── index.html           # Index page
├── document.html        # WDL document page
├── docker_images.html   # Docker images inventory
└── graph.html           # Graph visualization page
```

## Organization Principles

### 1. Macros (`macros/`)
Reusable functions that return HTML. Use macros for:
- Small, repetitive elements (badges, inputs, buttons)
- Common rendering logic
- Components that need parameters

**Example:**
```jinja2
{% from "macros/badges.html" import workflow_badge, task_badge %}

{{ workflow_badge() }}  {# Renders <span class="badge badge-workflow">WORKFLOW</span> #}
```

### 2. Components (`components/`)
Larger blocks of functionality. Use components for:
- Complete page sections
- Components with associated JavaScript
- Complex rendering logic

**Example:**
```jinja2
{% from "components/modals.html" import graph_modal %}

{{ graph_modal(workflow_name, mermaid_graph) }}
```

## Usage in Templates

### Importing Macros and Components

```jinja2
{# At the beginning of the template #}
{% from "macros/badges.html" import workflow_badge, task_badge %}
{% from "macros/tables.html" import inputs_table, outputs_table %}
{% from "components/stats.html" import stats_grid, stat_card %}
```

### Complete Example

```jinja2
{% extends "base.html" %}
{% from "macros/badges.html" import workflow_badge %}
{% from "macros/tables.html" import inputs_table %}

{% block content %}
<div class="card">
    <h2>{{ workflow_badge() }} {{ workflow_name }}</h2>
    
    {% if workflow.has_inputs %}
    <h3>Inputs</h3>
    {{ inputs_table(workflow.inputs) }}
    {% endif %}
</div>
{% endblock %}
```

## Macro Catalog

### badges.html
- `badge(type, text)` - Generic badge
- `workflow_badge()` - Workflow badge
- `task_badge()` - Task badge
- `mixed_badge()` - Mixed file badge
- `external_badge()` - External file badge
- `count_items(count, singular, plural)` - Badge with counter and pluralization

### tables.html
- `inputs_table(inputs)` - Inputs table with support for structs and defaults
- `outputs_table(outputs)` - Outputs table
- `runtime_table(runtime_dict)` - Runtime table
- `imports_table(imports)` - Imports table
- `document_info_table(doc)` - Document info table

### lists.html
- `file_list(title, description, files, badge_macro)` - List of WDL files

## Component Catalog

### buttons.html
- `graph_button()` - Button to view graph
- `source_button()` - Button to view source code
- `action_buttons()` - Button container (use with `{% call %}`)

### document.html
- `workflow_section_header(name, has_graph, has_source)` - Workflow section header
- `tasks_section_header(has_source)` - Tasks section header
- `subworkflow_usage_banner(call_info, relative_path)` - Subworkflow usage banner
- `call_block(call, doc_relative_path)` - Call block
- `docker_images_grid(docker_images)` - Docker images grid
- `task_card(task)` - Complete task card

### modals.html
- `graph_modal(workflow_name, mermaid_graph)` - Graph visualization modal
- `source_modal(doc_name, source_code)` - Source code modal

### stats.html
- `stats_grid()` - Statistics container (use with `{% call %}`)
- `stat_card(number, label)` - Individual statistic card
- `stat_card_highlighted(number, label, color)` - Highlighted card

### tabs.html
- `tabs_container()` - Tabs container (use with `{% call %}`)
- `tab_button(id, icon, label, count, active)` - Tab button
- `tab_content(id, active)` - Tab content (use with `{% call %}`)
- `tab_notice(icon, title, description)` - Notice inside tab

## Organization Benefits

1. **Reduced Code Duplication**: Reusable components eliminate repetition
2. **Easier Maintenance**: Changes in one place affect all pages
3. **Visual Consistency**: Same components = same look
4. **Testability**: Isolated components are easier to test
5. **Readability**: Main templates are cleaner and more focused
6. **Scalability**: Easy to add new templates using existing components

## Adding New Components

1. **Identify duplicated code** in multiple templates
2. **Decide the type**:
   - Small and simple? → Macro in `macros/`
   - Large or with JS? → Component in `components/`
3. **Create the file** with a descriptive name
4. **Document parameters** in the initial comment
5. **Use in existing templates** and remove duplicated code

## Example of a New Macro

```jinja2
{# macros/alerts.html #}

{# Reusable generic alert #}
{% macro alert(type, title, message) %}
<div class="alert alert-{{ type }}">
    <strong>{{ title }}</strong>
    <p>{{ message }}</p>
</div>
{%- endmacro %}

{# Specific alerts #}
{% macro success_alert(message) %}
{{ alert('success', '✓ Success', message) }}
{%- endmacro %}

{% macro error_alert(message) %}
{{ alert('error', '✗ Error', message) }}
{%- endmacro %}
```

## Naming Conventions

- **Files**: `snake_case.html` (e.g., `docker_images.html`)
- **Macros/Components**: `snake_case` (e.g., `workflow_badge`, `stat_card`)
- **Parameters**: `snake_case` (e.g., `doc_relative_path`, `workflow_name`)
- **CSS Classes**: `kebab-case` (e.g., `badge-workflow`, `stat-card`)

## Best Practices

1. **Always document macros** with comments explaining parameters
2. **Use default values** when possible to make macros more flexible
3. **Keep macros focused**: one responsibility per macro
4. **Avoid complex logic** in templates, move to Python when possible
5. **Test visually** after changes in shared components
6. **Use `{% call %}` blocks** for components needing custom content
