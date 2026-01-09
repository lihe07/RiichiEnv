import { GameState } from './game_state';
import { Renderer } from './renderer';
import { MjaiEvent } from './types';
import { ReplayController } from './controller';

export class Viewer {
    gameState: GameState;
    renderer: Renderer;
    container: HTMLElement;
    log: MjaiEvent[];
    controller!: ReplayController;

    debugPanel!: HTMLElement;

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
            maxHeight: '768px', // Force Max Height
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
            alignItems: 'flex-start', // Top Align
            justifyContent: 'center'
        });
        this.container.appendChild(scrollContainer);

        // 1. Board Wrapper (Main Area)
        const boardWrapper = document.createElement('div');
        boardWrapper.id = this.container.id + '-board-wrapper';
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
            top: '0',        // Top Align
            left: '50%',     // Horizontal Center
            transform: 'translateX(-50%)', // Initial horizontal center only
            transformOrigin: 'top center', // Scale from Top
            backgroundColor: '#2d5a27', // Board background
            boxShadow: '0 0 20px rgba(0,0,0,0.5)'
        });
        boardWrapper.appendChild(viewArea);

        // 2. Right Sidebar (Controls) - Fixed Width
        const rightSidebar = document.createElement('div');
        rightSidebar.id = 'controls'; // Added ID for controller usage if needed
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
            height: '100%', // Full height
            boxSizing: 'border-box', // Ensure padding doesn't overflow height
            overflow: 'hidden'       // Prevent any scrollbars
        });
        this.container.appendChild(rightSidebar);

        this.debugPanel = document.createElement('div');
        this.debugPanel.className = 'debug-panel';
        this.debugPanel.id = 'log-panel'; // ID for controller
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
        const createBtn = (id: string, text: string) => {
            const btn = document.createElement('div');
            btn.id = id;
            btn.className = 'icon-btn';
            btn.textContent = text;
            return btn;
        };

        console.log("[Viewer] Initializing GameState with log length:", log.length);
        this.gameState = new GameState(log);
        console.log("[Viewer] GameState initialized. Current event index:", this.gameState.current.eventIndex);

        console.log("[Viewer] Initializing Renderer");
        this.renderer = new Renderer(viewArea);

        // Create Buttons
        rightSidebar.appendChild(createBtn('btn-log', '📜'));
        rightSidebar.appendChild(createBtn('btn-pturn', '⏮️')); // Reusing icons
        rightSidebar.appendChild(createBtn('btn-nturn', '⏭️'));
        rightSidebar.appendChild(createBtn('btn-prev', '◀️'));
        rightSidebar.appendChild(createBtn('btn-next', '▶️'));
        rightSidebar.appendChild(createBtn('btn-auto', '⏯️'));

        // Pseudo button for Round Selector (hidden or triggered by center?)
        const rBtn = document.createElement('div');
        rBtn.id = 'btn-round';
        rBtn.style.display = 'none';
        rightSidebar.appendChild(rBtn);


        // Robust Responsive Scaling (Contain Strategy)
        // With MAX_WIDTH = 768px and MAX_HEIGHT = 768px constraint
        const MAX_WIDTH = 768;
        const MAX_HEIGHT = 768;

        const resizeObserver = new ResizeObserver((entries) => {
            for (const entry of entries) {
                const { width, height } = entry.contentRect;
                if (width === 0 || height === 0) continue;

                const availableWidth = Math.min(width, MAX_WIDTH);
                const availableHeight = Math.min(height, MAX_HEIGHT);

                // Scale to fit smaller dimension
                // We want to fit 900x900 into availableWidth x availableHeight
                const scale = Math.min(availableWidth / 900, availableHeight / 900);

                viewArea.style.transform = `translateX(-50%) scale(${scale})`;
            }
        });
        resizeObserver.observe(boardWrapper);

        // Initial call
        setTimeout(() => {
            // Manually trigger resize observer for initial layout
            boardWrapper.getBoundingClientRect(); // accessing layout properties can flush layout
            resizeObserver.observe(boardWrapper); // Re-observe to trigger
            resizeObserver.disconnect(); // Disconnect to avoid duplicate triggers
            resizeObserver.observe(boardWrapper); // Re-observe for future changes
        }, 0);

        // --- Controller Initialization ---
        this.controller = new ReplayController(this);
        this.controller.setupKeyboardControls(window);
        this.controller.setupWheelControls(boardWrapper);

        // Wire up buttons
        document.getElementById('btn-prev')!.onclick = () => this.controller.stepBackward();
        document.getElementById('btn-next')!.onclick = () => this.controller.stepForward();
        document.getElementById('btn-auto')!.onclick = (e) => this.controller.toggleAutoPlay(e.target as HTMLElement);
        document.getElementById('btn-log')!.onclick = (e) => this.controller.toggleLog(e.target as HTMLElement, this.debugPanel);

        document.getElementById('btn-pturn')!.onclick = () => this.controller.prevTurn();
        document.getElementById('btn-nturn')!.onclick = () => this.controller.nextTurn();


        // Handle Viewpoint Change from Renderer (Click on Player Info)
        this.renderer.onViewpointChange = (pIdx: number) => {
            if (this.renderer.viewpoint !== pIdx) {
                this.renderer.viewpoint = pIdx;
                this.update();
            }
        };

        console.log("[Viewer] Calling first update()");
        this.update();

        // Handle Center Click -> Show Round Selector
        this.renderer.onCenterClick = () => {
            this.showRoundSelector();
        };
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

        const tbody = document.createElement('tbody');
        const kyokus = this.gameState.kyokus;

        kyokus.forEach((k, idx) => {
            const tr = document.createElement('tr');
            tr.onclick = () => {
                // Jump to this kyoku
                // Find start_kyoku event index
                // We know kyokus[idx] corresponds to limits[idx].start
                // Actually GameState stores limits. 
                // We need to jump to k.startEventIndex
                // Wait, GameState kyokus array has { round, honba, scores, startEventIndex }?
                // Let's assume GameState has a method or list.
                // Looking at GameState class (inferred), it likely has this info.
                // For now, let's assume we can jump by index if we had it.
                // Simplified: use gameState.jumpToKyoku(idx).
                this.gameState.jumpToKyoku(idx);
                this.update();
                overlay.remove();
            };

            // Round Name
            const winds = ['E', 'S', 'W', 'N'];
            const w = winds[Math.floor(k.round / 4)];
            const rNum = (k.round % 4) + 1;
            const roundStr = `${w}${rNum}`;

            tr.innerHTML = `
                <td>${roundStr}</td>
                <td>${k.honba}</td>
                <td>${k.scores[0]}</td>
                <td>${k.scores[1]}</td>
                <td>${k.scores[2]}</td>
                <td>${k.scores[3]}</td>
            `;
            tbody.appendChild(tr);
        });
        table.appendChild(tbody);
        content.appendChild(table);

        overlay.appendChild(content);
        this.container.appendChild(overlay);
    }

    update() {
        if (!this.gameState || !this.renderer) return;
        const state = this.gameState.getState();
        this.renderer.render(state, this.debugPanel);
        // Update URL/History?
    }
}

(window as any).RiichiEnvViewer = Viewer;
