/**
 * Graph Modal Module
 * Gerencia o modal de visualização de gráficos Mermaid com pan-zoom
 */

export class GraphModal {
    constructor() {
        this.panZoomInstance = null;
        this.modalOpen = false;
        this.graphRendered = false;
        
        this.init();
    }
    
    init() {
        // Bind event listeners
        this.bindKeyboardEvents();
        this.bindModalClickEvents();
    }
    
    bindKeyboardEvents() {
        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape' && this.modalOpen) {
                this.close();
            }
        });
    }
    
    bindModalClickEvents() {
        const modal = document.getElementById('graphModal');
        if (modal) {
            modal.addEventListener('click', (event) => {
                if (event.target === modal) {
                    this.close();
                }
            });
        }
    }
    
    async open() {
        const modal = document.getElementById('graphModal');
        const graphContainer = document.getElementById('graphContainer');
        const graphData = document.getElementById('graphData');
        
        if (!modal) {
            console.error('Graph modal not found');
            return;
        }
        
        modal.style.display = 'flex';
        this.modalOpen = true;
        
        if (!this.graphRendered && graphData) {
            await this.renderMermaidGraph(graphContainer, graphData);
        } else if (this.graphRendered) {
            setTimeout(() => {
                this.initializePanZoom();
            }, 100);
        }
    }
    
    async renderMermaidGraph(container, graphData) {
        const mermaidCode = graphData.querySelector('.mermaid-source')?.textContent;
        
        if (!mermaidCode) {
            console.error('No mermaid code found');
            return;
        }
        
        container.innerHTML = `<div class="mermaid">${mermaidCode}</div>`;
        
        setTimeout(async () => {
            if (typeof window.mermaid !== 'undefined') {
                try {
                    const mermaidDiv = container.querySelector('.mermaid');
                    await window.mermaid.run({
                        nodes: [mermaidDiv]
                    });
                    
                    this.graphRendered = true;
                    setTimeout(() => {
                        this.initializePanZoom();
                    }, 300);
                } catch (error) {
                    console.error('Mermaid rendering error:', error);
                }
            } else {
                console.error('Mermaid library not loaded');
            }
        }, 100);
    }
    
    close() {
        const modal = document.getElementById('graphModal');
        if (modal) {
            modal.style.display = 'none';
        }
        this.modalOpen = false;
        
        if (this.panZoomInstance) {
            this.panZoomInstance.destroy();
            this.panZoomInstance = null;
        }
    }
    
    initializePanZoom() {
        const svg = document.querySelector('#graphContainer svg');
        
        if (!svg) {
            console.warn('SVG not found for pan-zoom initialization');
            return;
        }
        
        // Destroy existing instance
        if (this.panZoomInstance) {
            this.panZoomInstance.destroy();
            this.panZoomInstance = null;
        }
        
        // Prepare SVG for pan-zoom
        this.prepareSvg(svg);
        
        // Initialize svg-pan-zoom
        if (typeof svgPanZoom !== 'undefined') {
            this.panZoomInstance = svgPanZoom(svg, {
                zoomEnabled: true,
                controlIconsEnabled: false,
                fit: true,
                center: true,
                minZoom: 0.1,
                maxZoom: 10,
                zoomScaleSensitivity: 0.3,
                dblClickZoomEnabled: true,
                mouseWheelZoomEnabled: true,
                preventMouseEventsDefault: true
            });
            
            this.panZoomInstance.resize();
            this.panZoomInstance.fit();
            this.panZoomInstance.center();
        } else {
            console.error('svg-pan-zoom library not loaded');
        }
    }
    
    prepareSvg(svg) {
        // Remove size attributes
        svg.removeAttribute('width');
        svg.removeAttribute('height');
        svg.removeAttribute('style');
        
        // Set responsive styles
        svg.style.width = '100%';
        svg.style.height = '100%';
        svg.style.maxWidth = '100%';
        svg.style.maxHeight = '100%';
        
        // Ensure viewBox exists
        if (!svg.getAttribute('viewBox')) {
            const bbox = svg.getBBox();
            svg.setAttribute('viewBox', 
                `${bbox.x - 20} ${bbox.y - 20} ${bbox.width + 40} ${bbox.height + 40}`);
        }
        
        svg.setAttribute('preserveAspectRatio', 'xMidYMid meet');
    }
    
    // Zoom controls
    resetZoom() {
        if (this.panZoomInstance) {
            this.panZoomInstance.resetZoom();
            this.panZoomInstance.center();
            this.panZoomInstance.fit();
        }
    }
    
    zoomIn() {
        if (this.panZoomInstance) {
            this.panZoomInstance.zoomIn();
        }
    }
    
    zoomOut() {
        if (this.panZoomInstance) {
            this.panZoomInstance.zoomOut();
        }
    }
    
    fitToScreen() {
        if (this.panZoomInstance) {
            this.panZoomInstance.fit();
            this.panZoomInstance.center();
        }
    }
}

// Criar instância global para uso nos templates
let graphModalInstance = null;

// Funções globais para compatibilidade com templates existentes
window.openGraphModal = function() {
    if (!graphModalInstance) {
        graphModalInstance = new GraphModal();
    }
    graphModalInstance.open();
};

window.closeGraphModal = function() {
    if (graphModalInstance) {
        graphModalInstance.close();
    }
};

window.resetZoom = function() {
    if (graphModalInstance) {
        graphModalInstance.resetZoom();
    }
};

window.zoomIn = function() {
    if (graphModalInstance) {
        graphModalInstance.zoomIn();
    }
};

window.zoomOut = function() {
    if (graphModalInstance) {
        graphModalInstance.zoomOut();
    }
};

window.fitToScreen = function() {
    if (graphModalInstance) {
        graphModalInstance.fitToScreen();
    }
};
