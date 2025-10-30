# Template Organization

Este documento descreve a organização dos templates Jinja2 do projeto wdl2docs.

## Estrutura de Diretórios

```
src/infrastructure/rendering/templates/
├── macros/              # Macros reutilizáveis
│   ├── badges.html      # Badges (workflow, task, mixed, external, etc.)
│   ├── tables.html      # Tabelas (inputs, outputs, runtime, imports, etc.)
│   └── lists.html       # Listas de arquivos WDL
├── components/          # Componentes complexos
│   ├── buttons.html     # Botões de ação (graph, source)
│   ├── document.html    # Componentes específicos de documentos WDL
│   ├── modals.html      # Modals (graph e source code)
│   ├── stats.html       # Cards de estatísticas
│   └── tabs.html        # Sistema de tabs
├── static/              # Arquivos estáticos (CSS, JS, imagens)
├── base.html            # Template base
├── index.html           # Página índice
├── document.html        # Página de documento WDL
├── docker_images.html   # Inventário de imagens Docker
└── graph.html           # Página de visualização de gráfico
```

## Princípios de Organização

### 1. Macros (`macros/`)
Funções reutilizáveis que retornam HTML. Use macros para:
- Elementos pequenos e repetitivos (badges, inputs, botões)
- Lógica de renderização comum
- Componentes que precisam de parâmetros

**Exemplo:**
```jinja2
{% from "macros/badges.html" import workflow_badge, task_badge %}

{{ workflow_badge() }}  {# Renderiza <span class="badge badge-workflow">WORKFLOW</span> #}
```

### 2. Componentes (`components/`)
Blocos maiores de funcionalidade. Use componentes para:
- Seções completas da página
- Componentes com JavaScript associado
- Lógica complexa de renderização

**Exemplo:**
```jinja2
{% from "components/modals.html" import graph_modal %}

{{ graph_modal(workflow_name, mermaid_graph) }}
```

## Uso nos Templates

### Importando Macros e Componentes

```jinja2
{# No início do template #}
{% from "macros/badges.html" import workflow_badge, task_badge %}
{% from "macros/tables.html" import inputs_table, outputs_table %}
{% from "components/stats.html" import stats_grid, stat_card %}
```

### Exemplo Completo

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

## Catálogo de Macros

### badges.html
- `badge(type, text)` - Badge genérico
- `workflow_badge()` - Badge de workflow
- `task_badge()` - Badge de task
- `mixed_badge()` - Badge de arquivo misto
- `external_badge()` - Badge de arquivo externo
- `count_items(count, singular, plural)` - Badge com contador e pluralização

### tables.html
- `inputs_table(inputs)` - Tabela de inputs com suporte a structs e defaults
- `outputs_table(outputs)` - Tabela de outputs
- `runtime_table(runtime_dict)` - Tabela de runtime
- `imports_table(imports)` - Tabela de imports
- `document_info_table(doc)` - Tabela de informações do documento

### lists.html
- `file_list(title, description, files, badge_macro)` - Lista de arquivos WDL

## Catálogo de Componentes

### buttons.html
- `graph_button()` - Botão para visualizar gráfico
- `source_button()` - Botão para visualizar código fonte
- `action_buttons()` - Container de botões (use com `{% call %}`)

### document.html
- `workflow_section_header(name, has_graph, has_source)` - Header de seção de workflow
- `tasks_section_header(has_source)` - Header de seção de tasks
- `subworkflow_usage_banner(call_info, relative_path)` - Banner de uso como subworkflow
- `call_block(call, doc_relative_path)` - Bloco de call
- `docker_images_grid(docker_images)` - Grid de imagens Docker
- `task_card(task)` - Card completo de task

### modals.html
- `graph_modal(workflow_name, mermaid_graph)` - Modal de visualização de gráfico
- `source_modal(doc_name, source_code)` - Modal de código fonte

### stats.html
- `stats_grid()` - Container de estatísticas (use com `{% call %}`)
- `stat_card(number, label)` - Card individual de estatística
- `stat_card_highlighted(number, label, color)` - Card com destaque

### tabs.html
- `tabs_container()` - Container de tabs (use com `{% call %}`)
- `tab_button(id, icon, label, count, active)` - Botão de tab
- `tab_content(id, active)` - Conteúdo de tab (use com `{% call %}`)
- `tab_notice(icon, title, description)` - Notice dentro de tab

## Benefícios da Organização

1. **Redução de Código Duplicado**: Componentes reutilizáveis eliminam repetição
2. **Manutenção Facilitada**: Mudanças em um lugar afetam todas as páginas
3. **Consistência Visual**: Mesmos componentes = mesma aparência
4. **Testabilidade**: Componentes isolados são mais fáceis de testar
5. **Legibilidade**: Templates principais ficam mais limpos e focados
6. **Escalabilidade**: Fácil adicionar novos templates usando componentes existentes

## Adicionando Novos Componentes

1. **Identifique código duplicado** em múltiplos templates
2. **Decida o tipo**:
   - Pequeno e simples? → Macro em `macros/`
   - Grande ou com JS? → Componente em `components/`
3. **Crie o arquivo** com nome descritivo
4. **Documente os parâmetros** no comentário inicial
5. **Use em templates existentes** e remova código duplicado

## Exemplo de Novo Macro

```jinja2
{# macros/alerts.html #}

{# Alert genérico reutilizável #}
{% macro alert(type, title, message) %}
<div class="alert alert-{{ type }}">
    <strong>{{ title }}</strong>
    <p>{{ message }}</p>
</div>
{%- endmacro %}

{# Alerts específicos #}
{% macro success_alert(message) %}
{{ alert('success', '✓ Success', message) }}
{%- endmacro %}

{% macro error_alert(message) %}
{{ alert('error', '✗ Error', message) }}
{%- endmacro %}
```

## Convenções de Nomenclatura

- **Arquivos**: `snake_case.html` (ex: `docker_images.html`)
- **Macros/Componentes**: `snake_case` (ex: `workflow_badge`, `stat_card`)
- **Parâmetros**: `snake_case` (ex: `doc_relative_path`, `workflow_name`)
- **Classes CSS**: `kebab-case` (ex: `badge-workflow`, `stat-card`)

## Boas Práticas

1. **Sempre documente macros** com comentário explicando parâmetros
2. **Use valores default** quando possível para tornar macros mais flexíveis
3. **Mantenha macros focados**: uma responsabilidade por macro
4. **Evite lógica complexa** em templates, mova para Python quando possível
5. **Teste visualmente** após mudanças em componentes compartilhados
6. **Use `{% call %}` blocks** para componentes que precisam de conteúdo personalizado

## Migração de Templates Antigos

Se você encontrar código duplicado nos templates antigos (`*_backup.html`):

1. Extraia para um novo macro/componente
2. Atualize todos os templates que usam esse código
3. Teste a renderização
4. Remova os arquivos de backup quando confirmado que funciona
