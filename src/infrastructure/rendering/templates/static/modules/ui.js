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
        let lastScroll = 0;
        let lastUpdateTime = 0;
        let pendingUpdate = null;
        
        // Hysteresis thresholds to prevent flickering
        const COMPACT_THRESHOLD = 200;      // Scroll down to compact
        const EXPAND_THRESHOLD = 80;        // Scroll up to expand
        const MIN_UPDATE_INTERVAL = 200;    // Min ms between changes
        const DEBOUNCE_DELAY = 50;          // Debounce delay for scroll events
        
        const applyState = (compact) => {
            const now = Date.now();
            
            // Enforce minimum time between state changes
            if (now - lastUpdateTime < MIN_UPDATE_INTERVAL) {
                return;
            }
            
            if (compact !== isCompact) {
                if (compact) {
                    header.classList.add('compact');
                    html.classList.add('header-compact');
                } else {
                    header.classList.remove('compact');
                    html.classList.remove('header-compact');
                }
                isCompact = compact;
                lastUpdateTime = now;
            }
        };
        
        const updateHeader = () => {
            const currentScroll = window.pageYOffset || document.documentElement.scrollTop;
            
            // Clear any pending updates
            if (pendingUpdate) {
                clearTimeout(pendingUpdate);
            }
            
            // Debounce the update
            pendingUpdate = setTimeout(() => {
                // Determine desired state based on scroll position
                let shouldBeCompact = isCompact;
                
                if (!isCompact && currentScroll > COMPACT_THRESHOLD) {
                    shouldBeCompact = true;
                } else if (isCompact && currentScroll < EXPAND_THRESHOLD) {
                    shouldBeCompact = false;
                }
                
                applyState(shouldBeCompact);
                lastScroll = currentScroll;
            }, DEBOUNCE_DELAY);
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
