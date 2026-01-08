import { GameState } from './game_state';
import { Renderer } from './renderer';
import { MjaiEvent } from './types';

export class Viewer {
    gameState: GameState;
    renderer: Renderer;
    container: HTMLElement;
    log: MjaiEvent[];

    debugPanel!: HTMLElement;
    // slider!: HTMLInputElement; // Removed

    constructor(containerId: string, log: MjaiEvent[]) {
        const el = document.getElementById(containerId);
        if (!el) throw new Error(`Container #${containerId} not found`);
        this.container = el;
        this.log = log;

        // Setup DOM Structure: 2-Column Flex (Main Area + Right Sidebar)
        // Reset Body / HTML to prevent default margins causing scrollbars
        document.body.style.margin = '0';
        document.body.style.padding = '0';
        document.body.style.overflow = 'hidden';
        document.body.style.height = '100vh';
        document.body.style.width = '100vw';
        document.documentElement.style.margin = '0';
        document.documentElement.style.padding = '0';
        document.documentElement.style.overflow = 'hidden';
        document.documentElement.style.height = '100vh';
        document.documentElement.style.width = '100vw';

        this.container.innerHTML = '';
        Object.assign(this.container.style, {
            display: 'flex',
            flexDirection: 'row',
            width: '100%',
            height: '100vh',
            backgroundColor: '#000',
            overflow: 'hidden',
            margin: '0',
            padding: '0'
        });

        // Scrollable Main Content Area
        const scrollContainer = document.createElement('div');
        Object.assign(scrollContainer.style, {
            flex: '1',
            height: '100%',
            position: 'relative',
            overflow: 'hidden', // Disable scrolling entirely
            backgroundColor: '#000',
            display: 'flex',       // Center child
            alignItems: 'center',
            justifyContent: 'center'
        });
        this.container.appendChild(scrollContainer);

        // 1. Board Wrapper (Main Area)
        const boardWrapper = document.createElement('div');
        Object.assign(boardWrapper.style, {
            width: '100%',
            height: '100%', // Full size
            position: 'relative',
            backgroundColor: '#000',
            overflow: 'hidden'
        });
        scrollContainer.appendChild(boardWrapper);

        // The View Area - Fixed Base Size 900x900
        const viewArea = document.createElement('div');
        viewArea.id = `${containerId}-board`;
        Object.assign(viewArea.style, {
            width: '900px',
            height: '900px',
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)', // Initial center
            transformOrigin: 'center center',
            backgroundColor: '#2d5a27', // Board background
            boxShadow: '0 0 20px rgba(0,0,0,0.5)'
        });
        boardWrapper.appendChild(viewArea);

        // 2. Right Sidebar (Controls) - Fixed Width
        const rightSidebar = document.createElement('div');
        Object.assign(rightSidebar.style, {
            width: '80px', // Fixed width for icons
            backgroundColor: '#111',
            borderLeft: '1px solid #333',
            display: 'flex',
            flexDirection: 'column',
            gap: '15px',
            padding: '20px 10px',
            paddingTop: '50px',
            alignItems: 'center',
            flexShrink: '0',
            zIndex: '500',
            height: '100%' // Full height
        });
        this.container.appendChild(rightSidebar);

        this.debugPanel = document.createElement('div');
        this.debugPanel.className = 'debug-panel';
        // Debug Panel in boardWrapper so it scrolls with board
        Object.assign(this.debugPanel.style, {
            position: 'absolute',
            top: '0',
            left: '0',
            width: '100%',
            zIndex: '1000'
        });
        boardWrapper.appendChild(this.debugPanel);

        // Helper to create buttons
        const createBtn = (text: string, onClick: () => void) => {
            const btn = document.createElement('div');
            btn.className = 'icon-btn';
            btn.textContent = text;
            btn.onclick = onClick;
            return btn;
        };

        // Control Buttons
        // Show/Hide Log
        const logBtn = createBtn('📜', () => {
            const display = this.debugPanel.style.display;
            if (display === 'none' || !display) {
                this.debugPanel.style.display = 'block';
                logBtn.classList.add('active-btn');
            } else {
                this.debugPanel.style.display = 'none';
                logBtn.classList.remove('active-btn');
            }
        });
        rightSidebar.appendChild(logBtn);

        // Prev Step
        rightSidebar.appendChild(createBtn('◀️', () => {
            if (this.gameState.stepBackward()) this.update();
        }));

        // Next Step
        rightSidebar.appendChild(createBtn('▶️', () => {
            if (this.gameState.stepForward()) this.update();
        }));

        // Auto Play
        let autoPlayTimer: number | null = null;
        const autoBtn = createBtn('⏯️', () => {
            if (autoPlayTimer) {
                clearInterval(autoPlayTimer);
                autoPlayTimer = null;
                autoBtn.classList.remove('active-btn');
            } else {
                autoBtn.classList.add('active-btn');
                autoPlayTimer = window.setInterval(() => {
                    if (!this.gameState.stepForward()) {
                        if (autoPlayTimer) clearInterval(autoPlayTimer);
                        autoPlayTimer = null;
                        autoBtn.classList.remove('active-btn');
                    } else {
                        this.update();
                    }
                }, 200); // 200ms per step
            }
        });
        rightSidebar.appendChild(autoBtn);

        this.gameState = new GameState(log);
        this.renderer = new Renderer(viewArea);

        // Handle Viewpoint Change from Renderer (Click on Player Info)
        this.renderer.onViewpointChange = (pIdx: number) => {
            if (this.renderer.viewpoint !== pIdx) {
                this.renderer.viewpoint = pIdx;
                this.update();
            }
        };

        this.update();

        // Handle Center Click -> Show Round Selector
        this.renderer.onCenterClick = () => {
            this.showRoundSelector();
        };

        this.update();

        // Mouse Wheel Navigation
        window.addEventListener('wheel', (e: WheelEvent) => {
            // e.preventDefault(); 
        }, { passive: false });

        // Add listener specifically to boardWrapper for navigation
        boardWrapper.addEventListener('wheel', (e: WheelEvent) => {
            // User wants to use wheel for steps. We must prevent default scrolling behavior
            // to avoid scrolling the page while stepping.
            e.preventDefault();
            if (e.deltaY > 0) {
                if (this.gameState.stepForward()) this.update();
            } else {
                if (this.gameState.stepBackward()) this.update();
            }
        }, { passive: false });

        // Robust Responsive Scaling (Contain Strategy)
        const handleResize = () => {
            const wrapperRect = boardWrapper.getBoundingClientRect();
            const availableWidth = wrapperRect.width;
            const availableHeight = wrapperRect.height;
            const baseSize = 900;

            // Calculate scale to CONTAIN (Fit Window)
            const scale = Math.min(availableWidth / baseSize, availableHeight / baseSize);

            // Apply scale + center
            viewArea.style.transform = `translate(-50%, -50%) scale(${scale})`;
        };

        if ('ResizeObserver' in window) {
            // Observe the SCROLL CONTAINER logic width
            const ro = new ResizeObserver(() => handleResize());
            ro.observe(scrollContainer);
        } else {
            window.addEventListener('resize', handleResize);
        }
        // Initial call
        setTimeout(handleResize, 0);
    }

    showRoundSelector() {
        // Create Modal Overlay
        const overlay = document.createElement('div');
        overlay.className = 're-modal-overlay';
        overlay.onclick = () => {
            overlay.remove();
        };

        const content = document.createElement('div');
        content.className = 're-modal-content';
        content.onclick = (e) => e.stopPropagation();

        const title = document.createElement('h3');
        title.textContent = 'Jump to Round';
        title.className = 're-modal-title';
        title.style.marginTop = '0';
        content.appendChild(title);

        const table = document.createElement('table');
        table.className = 're-kyoku-table';

        // Header
        const thead = document.createElement('thead');
        thead.innerHTML = `
            <tr>
                <th>Round</th>
                <th>Honba</th>
                <th>P0 Score</th>
                <th>P1 Score</th>
                <th>P2 Score</th>
                <th>P3 Score</th>
            </tr>
        `;
        table.appendChild(thead);

        // Body
        const tbody = document.createElement('tbody');
        const checkpoints = this.gameState.getKyokuCheckpoints();

        checkpoints.forEach((cp) => {
            const tr = document.createElement('tr');
            tr.className = 're-kyoku-row';
            tr.onclick = () => {
                this.gameState.jumpTo(cp.index + 1);
                this.update();
                overlay.remove();
            };

            const scores = cp.scores || [0, 0, 0, 0];
            tr.innerHTML = `
                <td>${this.renderer.formatRound(cp.round)}</td>
                <td>${cp.honba}</td>
                <td>${scores[0]}</td>
                <td>${scores[1]}</td>
                <td>${scores[2]}</td>
                <td>${scores[3]}</td>
            `;
            tbody.appendChild(tr);
        });
        table.appendChild(tbody);
        content.appendChild(table);

        overlay.appendChild(content);

        // Append to viewArea so it sits over the board
        const viewArea = this.container.querySelector('#' + this.container.id + '-board') || this.container;
        viewArea.appendChild(overlay);
    }

    update() {
        this.renderer.render(this.gameState.current, this.debugPanel);
    }
}

// Global Export for usage in HTML
// @ts-ignore
window.RiichiEnvViewer = Viewer;
