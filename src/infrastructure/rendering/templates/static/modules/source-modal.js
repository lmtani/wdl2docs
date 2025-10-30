/**
 * Source Modal Module
 * Gerencia o modal de visualização de código fonte WDL
 */

export class SourceModal {
    constructor() {
        this.modalOpen = false;
        this.init();
    }
    
    init() {
        this.bindKeyboardEvents();
        this.bindModalClickEvents();
        this.bindDefaultInputsToggles();
    }
    
    bindKeyboardEvents() {
        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape' && this.modalOpen) {
                this.close();
            }
        });
    }
    
    bindModalClickEvents() {
        const modal = document.getElementById('sourceModal');
        if (modal) {
            modal.addEventListener('click', (event) => {
                if (event.target === modal) {
                    this.close();
                }
            });
        }
    }
    
    bindDefaultInputsToggles() {
        // Toggle for inputs with default values (collapsible)
        const defaultInputsDetails = document.querySelectorAll('.default-inputs-details');
        
        defaultInputsDetails.forEach(details => {
            details.addEventListener('toggle', function() {
                const parentRow = this.closest('tr');
                if (!parentRow) return;
                
                let nextRow = parentRow.nextElementSibling;
                while (nextRow && nextRow.classList.contains('default-input-row')) {
                    if (this.open) {
                        nextRow.style.display = '';
                    } else {
                        nextRow.style.display = 'none';
                    }
                    nextRow = nextRow.nextElementSibling;
                }
            });
        });
    }
    
    open() {
        const modal = document.getElementById('sourceModal');
        if (!modal) {
            console.error('Source modal not found');
            return;
        }
        
        modal.style.display = 'flex';
        this.modalOpen = true;
        
        // Apply syntax highlighting
        setTimeout(() => {
            this.applySyntaxHighlighting();
        }, 100);
    }
    
    close() {
        const modal = document.getElementById('sourceModal');
        if (modal) {
            modal.style.display = 'none';
        }
        this.modalOpen = false;
    }
    
    applySyntaxHighlighting() {
        if (typeof Prism !== 'undefined') {
            Prism.highlightAll();
        }
    }
    
    async copyToClipboard() {
        const sourceData = document.getElementById('sourceData');
        
        if (!sourceData) {
            console.error('Source data not found');
            return false;
        }
        
        const text = sourceData.textContent;
        
        try {
            await navigator.clipboard.writeText(text);
            this.showCopyFeedback();
            return true;
        } catch (err) {
            console.error('Failed to copy:', err);
            return false;
        }
    }
    
    showCopyFeedback() {
        const feedback = document.getElementById('copyFeedback');
        if (feedback) {
            feedback.style.display = 'inline';
            setTimeout(() => {
                feedback.style.display = 'none';
            }, 2000);
        }
    }
}

// Create global instance for use in templates
let sourceModalInstance = null;

// Initialize immediately (module is loaded after DOM)
function initSourceModal() {
    if (!sourceModalInstance) {
        sourceModalInstance = new SourceModal();
    }
}

// Initialize when this module is imported
// If DOM is already ready, init now; otherwise wait
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initSourceModal);
} else {
    // DOM is already ready, init immediately
    initSourceModal();
}

// Global functions for compatibility with existing templates
window.openSourceModal = function() {
    if (!sourceModalInstance) {
        sourceModalInstance = new SourceModal();
    }
    sourceModalInstance.open();
};

window.closeSourceModal = function() {
    if (sourceModalInstance) {
        sourceModalInstance.close();
    }
};

window.copySourceCode = function() {
    if (!sourceModalInstance) {
        sourceModalInstance = new SourceModal();
    }
    sourceModalInstance.copyToClipboard();
};
