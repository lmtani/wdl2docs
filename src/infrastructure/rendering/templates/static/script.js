/**
 * WDL Documentation - Search and Syntax Highlighting
 * 
 * NOTA: Syntax highlighting foi desabilitado devido a problemas de double-encoding
 * com o autoescape do Jinja2. Para reativar, considere usar uma biblioteca como
 * Prism.js ou highlight.js que lidam melhor com o escape de HTML.
 */

// Simple syntax highlighting for bash/shell commands (DESABILITADO)
function highlightCommand(code) {
    // Note: code is already plain text, no need to escape
    
    // Highlight comments
    code = code.replace(/(#[^\n]*)/g, '<span class="token comment">$1</span>');
    
    // Highlight strings (single and double quotes)
    code = code.replace(/("(?:[^"\\]|\\.)*")/g, '<span class="token string">$1</span>');
    code = code.replace(/('(?:[^'\\]|\\.)*')/g, '<span class="token string">$1</span>');
    
    // Highlight variables (~{variable} for WDL, $variable for bash)
    code = code.replace(/(~\{[^}]+\})/g, '<span class="token variable">$1</span>');
    code = code.replace(/(\$\{?[a-zA-Z_][a-zA-Z0-9_]*\}?)/g, '<span class="token variable">$1</span>');
    
    // Highlight common shell keywords
    const keywords = ['if', 'then', 'else', 'fi', 'for', 'while', 'do', 'done', 'case', 'esac', 'function'];
    keywords.forEach(kw => {
        const regex = new RegExp(`\\b(${kw})\\b`, 'g');
        code = code.replace(regex, '<span class="token keyword">$1</span>');
    });
    
    // Highlight common commands
    const builtins = ['echo', 'cat', 'grep', 'awk', 'sed', 'cut', 'sort', 'uniq', 'head', 'tail', 
                      'wc', 'find', 'cd', 'ls', 'pwd', 'export', 'source', 'bash', 'sh',
                      'gatk', 'samtools', 'bcftools', 'java', 'python', 'perl', 'bgzip', 'tabix',
                      'bedtools', 'picard'];
    builtins.forEach(cmd => {
        const regex = new RegExp(`\\b(${cmd})\\b`, 'g');
        code = code.replace(regex, '<span class="token builtin">$1</span>');
    });
    
    // Highlight operators
    code = code.replace(/([|&><;\\])/g, '<span class="token operator">$1</span>');
    
    // Escape HTML after highlighting to preserve our spans
    return code;
}

// Apply syntax highlighting to all command blocks
function applySyntaxHighlighting() {
    // Desabilitado - estava causando problema de double-encoding
    // O código agora é exibido como texto puro
    return;
    
    /* CÓDIGO ORIGINAL COMENTADO
    const codeBlocks = document.querySelectorAll('pre code');
    codeBlocks.forEach(block => {
        if (!block.classList.contains('highlighted')) {
            // Get the original plain text
            const originalCode = block.textContent;
            // Apply highlighting
            const highlighted = highlightCommand(originalCode);
            // Set as HTML
            block.innerHTML = highlighted;
            block.classList.add('highlighted', 'command-block');
        }
    });
    */
}

// Search functionality
let searchDataInternal = [];
let searchDataExternal = [];
let allSearchData = [];

function initializeSearch() {
    // Build search index from the page
    const searchBox = document.getElementById('searchBox');
    if (!searchBox) return;
    
    // Load internal search data
    const internalElement = document.getElementById('searchDataInternal');
    if (internalElement) {
        try {
            searchDataInternal = JSON.parse(internalElement.textContent);
        } catch (e) {
            console.error('Failed to load internal search data:', e);
        }
    }
    
    // Load external search data
    const externalElement = document.getElementById('searchDataExternal');
    if (externalElement) {
        try {
            searchDataExternal = JSON.parse(externalElement.textContent);
        } catch (e) {
            console.error('Failed to load external search data:', e);
        }
    }
    
    // Combine all data for search
    allSearchData = [...searchDataInternal, ...searchDataExternal];
    
    // Add search event listener
    searchBox.addEventListener('input', debounce(performSearch, 300));
    searchBox.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            searchBox.value = '';
            performSearch();
        }
    });
}

function performSearch() {
    const searchBox = document.getElementById('searchBox');
    const resultsContainer = document.getElementById('searchResults');
    const statsContainer = document.getElementById('searchStats');
    
    if (!searchBox || !resultsContainer) return;
    
    const query = searchBox.value.trim().toLowerCase();
    
    if (query.length === 0) {
        resultsContainer.innerHTML = '';
        if (statsContainer) statsContainer.textContent = '';
        return;
    }
    
    if (query.length < 2) {
        resultsContainer.innerHTML = '<div class="no-results">Digite pelo menos 2 caracteres para buscar</div>';
        if (statsContainer) statsContainer.textContent = '';
        return;
    }
    
    // Perform search on all data
    const results = allSearchData.filter(item => {
        const searchText = `${item.name} ${item.type} ${item.path} ${item.description || ''}`.toLowerCase();
        return searchText.includes(query);
    });
    
    // Separate internal and external results
    const internalResults = results.filter(item => !item.isExternal);
    const externalResults = results.filter(item => item.isExternal);
    
    // Display results
    if (results.length === 0) {
        resultsContainer.innerHTML = '<div class="no-results">Nenhum resultado encontrado</div>';
        if (statsContainer) statsContainer.textContent = '';
    } else {
        // Build stats message
        let statsText = `${results.length} resultado${results.length !== 1 ? 's' : ''} encontrado${results.length !== 1 ? 's' : ''}`;
        if (internalResults.length > 0 && externalResults.length > 0) {
            statsText += ` (${internalResults.length} interno${internalResults.length !== 1 ? 's' : ''}, ${externalResults.length} externo${externalResults.length !== 1 ? 's' : ''})`;
        }
        if (statsContainer) {
            statsContainer.textContent = statsText;
        }
        
        // Group results by origin
        let html = '';
        
        if (internalResults.length > 0) {
            html += '<div class="search-section"><h4 class="search-section-title">📁 Internal</h4>';
            html += internalResults.map(item => createSearchResultItem(item, query)).join('');
            html += '</div>';
        }
        
        if (externalResults.length > 0) {
            html += '<div class="search-section"><h4 class="search-section-title">📦 External</h4>';
            html += externalResults.map(item => createSearchResultItem(item, query, true)).join('');
            html += '</div>';
        }
        
        resultsContainer.innerHTML = html;
    }
}

function createSearchResultItem(item, query, isExternal = false) {
    const highlightedName = highlightText(item.name, query);
    const highlightedDesc = item.description ? highlightText(item.description, query) : '';
    
    const externalBadge = isExternal ? '<span class="badge badge-external">EXTERNAL</span>' : '';
    
    return `
        <div class="search-result-item" onclick="window.location.href='${item.url}'">
            <div class="result-title">
                <span class="badge badge-${item.type.toLowerCase()}">${item.type}</span>
                ${externalBadge}
                ${highlightedName}
            </div>
            <div class="result-path">${item.path}</div>
            ${highlightedDesc ? `<div class="result-description">${highlightedDesc}</div>` : ''}
        </div>
    `;
}

function highlightText(text, query) {
    if (!query) return text;
    const regex = new RegExp(`(${escapeRegex(query)})`, 'gi');
    return text.replace(regex, '<span class="highlight">$1</span>');
}

function escapeRegex(str) {
    return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Struct field row visibility toggle
function initializeStructToggles() {
    const structDetails = document.querySelectorAll('.struct-details');
    
    structDetails.forEach(details => {
        // Hide struct field rows by default
        const structRow = details.closest('.struct-row');
        if (structRow) {
            const inputName = details.querySelector('code').textContent;
            const fieldRows = document.querySelectorAll(`.struct-field-row[data-parent="${inputName}"]`);
            fieldRows.forEach(row => row.style.display = 'none');
        }
        
        // Toggle field rows when details is opened/closed
        details.addEventListener('toggle', function() {
            const structRow = this.closest('.struct-row');
            if (structRow) {
                const inputName = this.querySelector('code').textContent;
                const fieldRows = document.querySelectorAll(`.struct-field-row[data-parent="${inputName}"]`);
                
                if (this.open) {
                    fieldRows.forEach(row => row.style.display = 'table-row');
                } else {
                    fieldRows.forEach(row => row.style.display = 'none');
                }
            }
        });
    });
}

// Compact header on scroll
function initializeScrollHeader() {
    const header = document.querySelector('header');
    const html = document.documentElement;
    let isCompact = false;
    let lastUpdateTime = 0;
    
    if (!header) return;
    
    // Large hysteresis gap to prevent any flickering
    const COMPACT_THRESHOLD = 150;      // Scroll down to this point to compact
    const EXPAND_THRESHOLD = 50;        // Scroll up past this point to expand
    const MIN_UPDATE_INTERVAL = 100;    // Minimum ms between state changes
    
    function updateHeader() {
        const currentScroll = window.pageYOffset || document.documentElement.scrollTop;
        const now = Date.now();
        
        // Prevent rapid state changes
        if (now - lastUpdateTime < MIN_UPDATE_INTERVAL) {
            return;
        }
        
        // Use different thresholds depending on current state (hysteresis)
        if (!isCompact && currentScroll > COMPACT_THRESHOLD) {
            // Transition to compact
            header.classList.add('compact');
            html.classList.add('header-compact');
            isCompact = true;
            lastUpdateTime = now;
        } else if (isCompact && currentScroll < EXPAND_THRESHOLD) {
            // Transition to expanded
            header.classList.remove('compact');
            html.classList.remove('header-compact');
            isCompact = false;
            lastUpdateTime = now;
        }
    }
    
    // Update on scroll with throttling using requestAnimationFrame
    let ticking = false;
    
    window.addEventListener('scroll', () => {
        if (!ticking) {
            window.requestAnimationFrame(() => {
                updateHeader();
                ticking = false;
            });
            ticking = true;
        }
    }, { passive: true });
    
    // Initial check
    updateHeader();
}

// Tab switching
function switchTab(tabName) {
    // Update tab buttons
    const tabButtons = document.querySelectorAll('.tab-button');
    tabButtons.forEach(button => {
        if (button.dataset.tab === tabName) {
            button.classList.add('active');
        } else {
            button.classList.remove('active');
        }
    });
    
    // Update tab contents
    const tabContents = document.querySelectorAll('.tab-content');
    tabContents.forEach(content => {
        if (content.id === `tab-${tabName}`) {
            content.classList.add('active');
        } else {
            content.classList.remove('active');
        }
    });
    
    // Store preference in localStorage
    try {
        localStorage.setItem('wdl-doc-active-tab', tabName);
    } catch (e) {
        // Ignore localStorage errors
    }
}

// Initialize tabs
function initializeTabs() {
    // Restore last selected tab from localStorage
    try {
        const savedTab = localStorage.getItem('wdl-doc-active-tab');
        if (savedTab) {
            const tabButton = document.querySelector(`[data-tab="${savedTab}"]`);
            if (tabButton) {
                switchTab(savedTab);
            }
        }
    } catch (e) {
        // Ignore localStorage errors
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    applySyntaxHighlighting();
    initializeSearch();
    initializeStructToggles();
    initializeScrollHeader();
    initializeTabs();
});
