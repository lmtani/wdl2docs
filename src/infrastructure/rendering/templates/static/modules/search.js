/**
 * Search Module
 * Gerencia funcionalidade de busca em documentos WDL
 */

export class SearchManager {
    constructor() {
        this.searchDataInternal = [];
        this.searchDataExternal = [];
        this.allSearchData = [];
        this.debounceTimer = null;
        this.debounceDelay = 300;
        
        this.init();
    }
    
    init() {
        this.loadSearchData();
        this.bindSearchEvents();
    }
    
    loadSearchData() {
        // Load internal search data
        const internalElement = document.getElementById('searchDataInternal');
        if (internalElement) {
            try {
                this.searchDataInternal = JSON.parse(internalElement.textContent);
            } catch (e) {
                console.error('Failed to load internal search data:', e);
            }
        }
        
        // Load external search data
        const externalElement = document.getElementById('searchDataExternal');
        if (externalElement) {
            try {
                this.searchDataExternal = JSON.parse(externalElement.textContent);
            } catch (e) {
                console.error('Failed to load external search data:', e);
            }
        }
        
        // Combine all data for search
        this.allSearchData = [...this.searchDataInternal, ...this.searchDataExternal];
    }
    
    bindSearchEvents() {
        const searchBox = document.getElementById('searchBox');
        if (!searchBox) return;
        
        searchBox.addEventListener('input', () => {
            this.debounce(() => this.performSearch());
        });
        
        searchBox.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                searchBox.value = '';
                this.performSearch();
            }
        });
    }
    
    debounce(func) {
        clearTimeout(this.debounceTimer);
        this.debounceTimer = setTimeout(func, this.debounceDelay);
    }
    
    performSearch() {
        const searchBox = document.getElementById('searchBox');
        const resultsContainer = document.getElementById('searchBoxResults');
        const statsContainer = document.getElementById('searchBoxStats');
        
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
        
        // Perform search
        const results = this.search(query);
        
        // Display results
        this.displayResults(results, query, resultsContainer, statsContainer);
    }
    
    search(query) {
        return this.allSearchData.filter(item => {
            const searchText = `${item.name} ${item.type} ${item.path} ${item.description || ''}`.toLowerCase();
            return searchText.includes(query);
        });
    }
    
    displayResults(results, query, resultsContainer, statsContainer) {
        if (results.length === 0) {
            resultsContainer.innerHTML = '<div class="no-results">Nenhum resultado encontrado</div>';
            if (statsContainer) statsContainer.textContent = '';
            return;
        }
        
        // Separate internal and external results
        const internalResults = results.filter(item => !item.isExternal);
        const externalResults = results.filter(item => item.isExternal);
        
        // Build stats message
        let statsText = `${results.length} resultado${results.length !== 1 ? 's' : ''} encontrado${results.length !== 1 ? 's' : ''}`;
        if (internalResults.length > 0 && externalResults.length > 0) {
            statsText += ` (${internalResults.length} interno${internalResults.length !== 1 ? 's' : ''}, ${externalResults.length} externo${externalResults.length !== 1 ? 's' : ''})`;
        }
        
        if (statsContainer) {
            statsContainer.textContent = statsText;
        }
        
        // Build results HTML
        let html = '';
        
        if (internalResults.length > 0) {
            html += '<div class="search-section"><h4 class="search-section-title">📁 Internal</h4>';
            html += internalResults.map(item => this.createResultItem(item, query)).join('');
            html += '</div>';
        }
        
        if (externalResults.length > 0) {
            html += '<div class="search-section"><h4 class="search-section-title">📦 External</h4>';
            html += externalResults.map(item => this.createResultItem(item, query, true)).join('');
            html += '</div>';
        }
        
        resultsContainer.innerHTML = html;
    }
    
    createResultItem(item, query, isExternal = false) {
        const highlightedName = this.highlightText(item.name, query);
        const highlightedDesc = item.description ? this.highlightText(item.description, query) : '';
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
    
    highlightText(text, query) {
        if (!query) return text;
        const regex = new RegExp(`(${this.escapeRegex(query)})`, 'gi');
        return text.replace(regex, '<span class="highlight">$1</span>');
    }
    
    escapeRegex(str) {
        return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }
}

// Função de inicialização
export function initializeSearch() {
    return new SearchManager();
}
