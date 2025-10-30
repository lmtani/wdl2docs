/**
 * Docker Images Module
 * Gerencia funcionalidades específicas da página de inventário Docker
 */

export class DockerImagesManager {
    constructor() {
        this.init();
    }
    
    init() {
        this.bindSearchEvents();
    }
    
    /**
     * Toggle de detalhes de uma imagem Docker
     * @param {string} id - ID único da imagem
     */
    toggleImageDetails(id) {
        const container = document.getElementById(`tasks_${id}`);
        const icon = document.getElementById(`icon_${id}`);
        
        if (!container || !icon) {
            console.warn(`Image details not found for id: ${id}`);
            return;
        }
        
        if (container.style.display === 'none') {
            container.style.display = 'block';
            icon.textContent = '▼';
        } else {
            container.style.display = 'none';
            icon.textContent = '▶';
        }
    }
    
    /**
     * Bind eventos de busca específicos do Docker
     */
    bindSearchEvents() {
        const searchBox = document.getElementById('dockerSearchBox');
        if (!searchBox) return;
        
        searchBox.addEventListener('input', (e) => {
            this.performDockerSearch(e.target.value);
        });
    }
    
    /**
     * Realiza busca nas imagens Docker
     * @param {string} searchTerm - Termo de busca
     */
    performDockerSearch(searchTerm) {
        const term = searchTerm.toLowerCase();
        const repositories = document.querySelectorAll('.docker-repository');
        
        repositories.forEach(repo => {
            const images = repo.querySelectorAll('.docker-image-item');
            let hasVisibleImage = false;
            
            images.forEach(image => {
                const imageName = image.dataset.image?.toLowerCase() || '';
                const tasks = Array.from(image.querySelectorAll('.task-name'))
                    .map(t => t.textContent.toLowerCase());
                const workflows = Array.from(image.querySelectorAll('.workflow-name'))
                    .map(w => w.textContent.toLowerCase());
                
                const matches = imageName.includes(term) || 
                              tasks.some(t => t.includes(term)) ||
                              workflows.some(w => w.includes(term));
                
                if (matches) {
                    image.style.display = 'block';
                    hasVisibleImage = true;
                } else {
                    image.style.display = 'none';
                }
            });
            
            // Show/hide repository based on visible images
            repo.style.display = hasVisibleImage ? 'block' : 'none';
        });
    }
}

// Criar instância global
let dockerManagerInstance = null;

/**
 * Função global para toggle de imagens Docker
 * Compatível com templates existentes
 */
window.toggleImageDetails = function(id) {
    if (!dockerManagerInstance) {
        dockerManagerInstance = new DockerImagesManager();
    }
    dockerManagerInstance.toggleImageDetails(id);
};

/**
 * Inicializa o gerenciador de Docker images
 */
export function initializeDockerImages() {
    if (!dockerManagerInstance) {
        dockerManagerInstance = new DockerImagesManager();
    }
}
