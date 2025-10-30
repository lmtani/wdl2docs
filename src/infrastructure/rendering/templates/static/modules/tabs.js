/**
 * Tabs Module
 * Gerencia sistema de tabs com persistência em localStorage
 */

export class TabManager {
    constructor(storageKey = 'wdl-doc-active-tab') {
        this.storageKey = storageKey;
        this.init();
    }
    
    init() {
        // Restore last selected tab from localStorage
        this.restoreActiveTab();
    }
    
    /**
     * Troca para a tab especificada
     * @param {string} tabName - Nome da tab
     */
    switchTab(tabName) {
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
        this.saveActiveTab(tabName);
    }
    
    /**
     * Salva a tab ativa no localStorage
     * @param {string} tabName - Nome da tab
     */
    saveActiveTab(tabName) {
        try {
            localStorage.setItem(this.storageKey, tabName);
        } catch (e) {
            console.warn('Failed to save tab preference:', e);
        }
    }
    
    /**
     * Restaura a última tab selecionada do localStorage
     */
    restoreActiveTab() {
        try {
            const savedTab = localStorage.getItem(this.storageKey);
            if (savedTab) {
                const tabButton = document.querySelector(`[data-tab="${savedTab}"]`);
                if (tabButton) {
                    this.switchTab(savedTab);
                }
            }
        } catch (e) {
            console.warn('Failed to restore tab preference:', e);
        }
    }
    
    /**
     * Obtém o nome da tab ativa
     * @returns {string|null} Nome da tab ativa ou null
     */
    getActiveTab() {
        const activeButton = document.querySelector('.tab-button.active');
        return activeButton ? activeButton.dataset.tab : null;
    }
}

// Criar instância global para uso nos templates
let tabManagerInstance = null;

/**
 * Função global para trocar tabs
 * Compatível com templates existentes
 */
window.switchTab = function(tabName) {
    if (!tabManagerInstance) {
        tabManagerInstance = new TabManager();
    }
    tabManagerInstance.switchTab(tabName);
};

/**
 * Função específica para tabs do Docker
 * Mantém compatibilidade com template docker_images.html
 */
window.switchDockerTab = function(tabName) {
    if (!tabManagerInstance) {
        tabManagerInstance = new TabManager('wdl-doc-docker-tab');
    }
    tabManagerInstance.switchTab(tabName);
};

/**
 * Inicializa o tab manager quando o DOM estiver pronto
 */
export function initializeTabs() {
    if (!tabManagerInstance) {
        tabManagerInstance = new TabManager();
    }
}
