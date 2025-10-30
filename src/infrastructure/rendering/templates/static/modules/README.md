# JavaScript Modules - WDL Atlas

This directory contains the modularized JavaScript modules for the WDL Atlas application.

## 📁 Module Structure

### Core Modules

#### `app.js` (Main Orchestrator)
- **Location**: `static/app.js`
- **Purpose**: Main orchestrator that initializes all modules
- **Responsibilities**:
  - Imports and initializes all modules in the correct order
  - Manages the application lifecycle
  - Provides global access to modules via `window.WDLDocApp`
  - Conditional initialization based on elements present on the page

#### `graph-modal.js`
- **Purpose**: Workflow graph visualization modal
- **Technologies**: Mermaid.js, svg-pan-zoom
- **Features**:
  - Mermaid diagram rendering
  - Zoom controls (in, out, fit, reset)
  - Interactive pan & zoom with mouse/touch
  - Keyboard shortcuts (ESC to close)
- **Global API**:
  ```javascript
  openGraphModal()    // Opens modal and renders graph
  closeGraphModal()   // Closes modal
  zoomIn()            // Zoom in
  zoomOut()           // Zoom out
  fitToScreen()       // Fit graph to screen
  resetZoom()         // Reset view
  ```

#### `source-modal.js`
- **Purpose**: WDL source code visualization modal
- **Technologies**: Prism.js
- **Features**:
  - WDL code syntax highlighting
  - Copy to clipboard
  - Visual feedback on copy
  - Keyboard shortcuts
- **Global API**:
  ```javascript
  openSourceModal()   // Opens modal and applies syntax highlighting
  closeSourceModal()  // Closes modal
  copySourceCode()    // Copies code to clipboard
  ```

#### `tabs.js`
- **Purpose**: Tab management (Internal/External)
- **Features**:
  - Tab switching
  - State persistence in localStorage
  - Automatic restoration of last active tab
  - Support for multiple tab instances
- **Global API**:
  ```javascript
  switchTab(tabName)      // Switches to specified tab
  switchDockerTab(name)   // Specific for docker_images.html
  ```

#### `search.js`
- **Purpose**: Global search system
- **Features**:
  - Real-time search with 300ms debouncing
  - Separation of Internal/External results
  - Search term highlighting
  - Result statistics
  - Search by name, type, path, and description
  - ESC shortcut to clear search
- **Data**: Loads JSON from `#searchDataInternal` and `#searchDataExternal`

#### `docker-images.js`
- **Purpose**: Features specific to the Docker Inventory page
- **Features**:
  - Toggle Docker image details
  - Specific search for images, tasks, and workflows
  - Repository filter by visibility
  - Expand/collapse animation
- **Global API**:
  ```javascript
  toggleImageDetails(id)  // Toggle image details
  ```

#### `ui.js`
- **Purpose**: UI components and general interactions
- **Features**:
  - **Struct Toggles**: Collapse/expand struct fields
  - **Scroll Header**: Compact header on scroll
    - Compact threshold: 150px down
    - Expand threshold: 50px up
    - Hysteresis to prevent flickering
    - Throttling with requestAnimationFrame

## 🔄 Initialization Flow

```
1. DOM Load
   ↓
2. app.js (Main Orchestrator)
   ↓
3. Import all modules
   ↓
4. Initialize universal modules
   - ui.js (struct toggles, scroll header)
   - tabs.js (restore active tab)
   ↓
5. Conditional initialization
   - search.js (if #searchBox exists)
   - docker-images.js (if #dockerSearchBox exists)
   ↓
6. Modals self-register globally
   - graph-modal.js
   - source-modal.js
```

## 🎯 Design Patterns

### Module Pattern
Each module exports:
- A main class
- An initialization function
- Global function wrappers for backward compatibility

### Singleton Pattern
Modules like `SearchManager`, `TabManager` use singleton:
```javascript
let instance = null;

export function initializeSearch() {
    if (!instance) {
        instance = new SearchManager();
    }
    return instance;
}
```

### Global Functions (Backward Compatibility)
Templates can still use `onclick="functionName()"`:
```javascript
// Export class for modular use
export class GraphModal { ... }

// Expose globally for templates
window.openGraphModal = openGraphModal;
window.closeGraphModal = closeGraphModal;
```

## 📦 External Dependencies

### CDN Libraries
- **Mermaid.js** v10: Graph rendering
- **svg-pan-zoom** v3.6.1: SVG pan & zoom
- **Prism.js** v1.29.0: Syntax highlighting

### Load Order
1. Mermaid.js (inline in `<head>`)
2. svg-pan-zoom (loaded by `components/modals.html`)
3. Prism.js (loaded in `<footer>`)
4. ES6 modules (after DOMContentLoaded)

## 🧪 Testing

To test the modules:
```bash
# Generate documentation
make docs

# Open in browser
open docs/index.html

# Check browser console
# You should see: "✅ WDL Atlas initialized successfully"
```

### Feature Checklist
- [ ] Search box works with debouncing
- [ ] Tabs switch and persist in localStorage
- [ ] Graph modal opens, renders, and controls zoom
- [ ] Source modal opens and copies code
- [ ] Docker images expand/collapse
- [ ] Header compacts on scroll (hysteresis works)
- [ ] Struct fields collapse/expand
- [ ] ESC closes modals
- [ ] Click outside closes modals

## 🔧 Maintenance

### Adding a New Module
1. Create file in `static/modules/module-name.js`
2. Export class and initialization function
3. Add global function if needed for templates
4. Import and initialize in `app.js`
5. Document here in the README

### Debug
- Console logs are enabled during initialization
- Use `window.WDLDocApp.getModule('moduleName')` in the console
- Check `localStorage` for tab state

### Performance
- Search debouncing (300ms)
- Scroll throttling (requestAnimationFrame)
- Lazy loading of Mermaid graphs (only renders when modal opens)
- Lazy syntax highlighting (only when source modal opens)

## 📚 References

- [ES6 Modules](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Modules)
- [Mermaid.js Docs](https://mermaid.js.org/)
- [svg-pan-zoom Docs](https://github.com/bumbu/svg-pan-zoom)
- [Prism.js Docs](https://prismjs.com/)

## 🎨 Code Conventions

- **Class Names**: PascalCase (e.g., `GraphModal`, `SearchManager`)
- **Function Names**: camelCase (e.g., `initializeSearch`, `toggleImageDetails`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `COMPACT_THRESHOLD`)
- **Comments**: JSDoc for public functions
- **Console logs**: Emojis for categorization (🚀 init, ✓ success, ❌ error)
