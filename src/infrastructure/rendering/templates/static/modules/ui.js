/**
 * UI Components Module
 * Gerencia componentes de UI como structs, headers e scrolling
 */

export class UIManager {
    constructor() {
        this.init();
    }
    
    init() {
        this.initializeStructToggles();
        this.initializeScrollHeader();
    }
    
    /**
     * Inicializa toggles para campos de struct
     */
    initializeStructToggles() {
        const structDetails = document.querySelectorAll('.struct-details');
        
        structDetails.forEach(details => {
            // Hide struct field rows by default
            const structRow = details.closest('.struct-row');
            if (structRow) {
                const inputName = details.querySelector('code')?.textContent;
                if (inputName) {
                    const fieldRows = document.querySelectorAll(`.struct-field-row[data-parent="${inputName}"]`);
                    fieldRows.forEach(row => row.style.display = 'none');
                }
            }
            
            // Toggle field rows when details is opened/closed
            details.addEventListener('toggle', function() {
                const structRow = this.closest('.struct-row');
                if (structRow) {
                    const inputName = this.querySelector('code')?.textContent;
                    if (inputName) {
                        const fieldRows = document.querySelectorAll(`.struct-field-row[data-parent="${inputName}"]`);
                        
                        if (this.open) {
                            fieldRows.forEach(row => row.style.display = 'table-row');
                        } else {
                            fieldRows.forEach(row => row.style.display = 'none');
                        }
                    }
                }
            });
        });
    }
    
    /**
     * Compacta o header ao fazer scroll
     */
    initializeScrollHeader() {
        const header = document.querySelector('header');
        const html = document.documentElement;
        
        if (!header) return;
        
        let isCompact = false;
        let lastUpdateTime = 0;
        
        // Hysteresis thresholds to prevent flickering
        const COMPACT_THRESHOLD = 150;      // Scroll down to compact
        const EXPAND_THRESHOLD = 50;        // Scroll up to expand
        const MIN_UPDATE_INTERVAL = 100;    // Min ms between changes
        
        const updateHeader = () => {
            const currentScroll = window.pageYOffset || document.documentElement.scrollTop;
            const now = Date.now();
            
            // Prevent rapid state changes
            if (now - lastUpdateTime < MIN_UPDATE_INTERVAL) {
                return;
            }
            
            // Use hysteresis
            if (!isCompact && currentScroll > COMPACT_THRESHOLD) {
                header.classList.add('compact');
                html.classList.add('header-compact');
                isCompact = true;
                lastUpdateTime = now;
            } else if (isCompact && currentScroll < EXPAND_THRESHOLD) {
                header.classList.remove('compact');
                html.classList.remove('header-compact');
                isCompact = false;
                lastUpdateTime = now;
            }
        };
        
        // Throttle scroll events with requestAnimationFrame
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
}

/**
 * Inicializa componentes de UI
 */
export function initializeUI() {
    return new UIManager();
}
