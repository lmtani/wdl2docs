/**
 * WDL Documentation - Main Application Module
 * 
 * Orquestra a inicialização de todos os módulos da aplicação
 */

import { initializeSearch } from './modules/search.js';
import { initializeTabs } from './modules/tabs.js';
import { initializeUI } from './modules/ui.js';
import { initializeDockerImages } from './modules/docker-images.js';

// Import modals (eles se auto-registram globalmente)
import './modules/graph-modal.js';
import './modules/source-modal.js';

class WDLDocApp {
    constructor() {
        this.modules = {
            search: null,
            tabs: null,
            ui: null,
            dockerImages: null
        };
        
        this.init();
    }
    
    init() {
        // Aguarda o DOM estar pronto
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.initializeModules());
        } else {
            this.initializeModules();
        }
    }
    
    initializeModules() {
        console.log('🚀 Initializing WDL Documentation...');
        
        try {
            // Inicializa módulos universais (presentes em todas as páginas)
            this.modules.ui = initializeUI();
            console.log('✓ UI module initialized');
            
            this.modules.tabs = initializeTabs();
            console.log('✓ Tabs module initialized');
            
            // Inicializa módulos condicionais (apenas se elementos existirem)
            if (document.getElementById('searchBox')) {
                this.modules.search = initializeSearch();
                console.log('✓ Search module initialized');
            }
            
            if (document.getElementById('dockerSearchBox')) {
                this.modules.dockerImages = initializeDockerImages();
                console.log('✓ Docker images module initialized');
            }
            
            console.log('✅ WDL Documentation initialized successfully');
        } catch (error) {
            console.error('❌ Error initializing WDL Documentation:', error);
        }
    }
    
    /**
     * Obtém instância de um módulo específico
     * @param {string} moduleName - Nome do módulo
     * @returns {Object|null} Instância do módulo ou null
     */
    getModule(moduleName) {
        return this.modules[moduleName] || null;
    }
}

// Criar instância global da aplicação
const app = new WDLDocApp();

// Exportar para uso em console/debug
window.WDLDocApp = app;

export default app;
