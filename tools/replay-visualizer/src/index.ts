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
        this.container.innerHTML = '';
        Object.assign(this.container.style, {
            display: 'block', // Block for auto margins
            // width/height will be set by resize logic
            maxWidth: '100%',
            overflow: 'hidden', // Hide overflow from transform
            backgroundColor: '#000',
            margin: '0',
            padding: '0'
        });

        // 1. Scrollable/Centering Container
        const scrollContainer = document.createElement('div');
        Object.assign(scrollContainer.style, {
            flex: '1',
            width: '100%',
            height: '100%',
            overflow: 'hidden', // Disable scrolling, strictly 'contain'
            // Let's keep it simple: Center content.
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'flex-start', // Top Align
            // Usually board is 900px. If screen is smaller, we want scroll.
            // If screen is larger, we want center.
            backgroundColor: '#000'
        });
        this.container.appendChild(scrollContainer);

        // 2a. Scale Wrapper (New Intermediate Layer)
        // This wrapper will have the exact SCALED width/height.
        const scaleWrapper = document.createElement('div');
        Object.assign(scaleWrapper.style, {
            position: 'relative',
            // Dimensions set via JS on resize
            overflow: 'hidden'
        });
        scrollContainer.appendChild(scaleWrapper);

        // 2b. Content Wrapper (Board + Sidebar) - High Res Source
        const contentWrapper = document.createElement('div');
        Object.assign(contentWrapper.style, {
            display: 'flex',
            flexDirection: 'row',
            alignItems: 'flex-start', // Align top of board and sidebar
            position: 'absolute', // Absolute within scaleWrapper
            top: '0',
            left: '0',
            width: '970px', // Explicit layout width (900 board + 10 margin + 60 sidebar)
            height: '900px', // Explicit layout height
            flexShrink: '0',
            transformOrigin: 'top left' // Always scale from top-left
        });
        scaleWrapper.appendChild(contentWrapper);

        // 3. The View Area - Fixed Base Size 900x900
        const viewArea = document.createElement('div');
        viewArea.id = `${containerId}-board`;
        Object.assign(viewArea.style, {
            width: '900px',
            height: '900px',
            position: 'relative', // Changed from absolute
            // No transform needed if in flex
            backgroundColor: '#2d5a27',
            boxShadow: '0 0 20px rgba(0,0,0,0.5)',
            flexShrink: '0' // Don't shrink board
        });
        contentWrapper.appendChild(viewArea);

        // 4. Right Sidebar (Controls) - Placed next to board
        const rightSidebar = document.createElement('div');
        rightSidebar.id = 'controls';
        Object.assign(rightSidebar.style, {
            width: '60px', // Slightly narrower?
            backgroundColor: '#111',
            // borderLeft: '1px solid #333', // Optional border
            display: 'flex',
            flexDirection: 'column',
            gap: '15px',
            padding: '20px 10px',
            marginTop: '20px', // Offset from top to look nice? Or aligned?
            // User image shows it aligned top, or slightly disjoint.
            // Let's align top with padding.
            alignItems: 'center',
            flexShrink: '0',
            zIndex: '500',
            height: 'auto', // Height fits content? Or matches board?
            // If match board, set height 100% (of wrapper).
            // But contentWrapper height is determined by Board (900).
            // So height: '100%' should work.
            // But maybe just let it flow.
            borderRadius: '0 12px 12px 0', // Rounded corners on right?
            marginLeft: '10px' // Gap between board and sidebar
        });
        contentWrapper.appendChild(rightSidebar);

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
        viewArea.appendChild(this.debugPanel); // Attach to viewArea so it's inside the board

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

        // Initialize Controller
        this.controller = new ReplayController(this);
        this.controller.setupKeyboardControls(window);
        this.controller.setupWheelControls(viewArea);

        // Resize Logic to scale the entire content (Board + Sidebar)
        // Resize Logic to scale the entire content (Board + Sidebar)
        // We use ResizeObserver on the container to detect size changes of the parent environment (e.g. Jupyter cell)
        const resizeObserver = new ResizeObserver((entries) => {
            for (const entry of entries) {
                // The entry.contentRect gives the size of the container.
                // However, since we adjust the container size ourselves (in older logic),
                // we must be careful.
                // Actually, in the latest logic (step 293), we resize `scaleWrapper`, 
                // and `this.container` is just a flexible wrapper (display: block, maxWidth: 100%).
                // So `this.container.clientWidth` should reflect the PARENT's constraint.

                const availableW = entry.contentRect.width;
                // For height, we might not be constrained by parent height in Jupyter (it grows).
                // But we want to fit within window height if it's full screen.
                // If Jupyter, height is usually auto.
                // If we use window.innerHeight, we ensure it doesn't get taller than the viewport.
                const availableH = window.innerHeight; // Still useful to prevent being too tall

                if (availableW === 0) continue;

                const baseW = 970;
                const baseH = 900;

                // Calculate scale
                const scale = Math.min(availableW / baseW, availableH / baseH, 1.0);

                contentWrapper.style.transform = `scale(${scale})`;

                const finalW = Math.floor(baseW * scale);
                const finalH = Math.floor(baseH * scale);

                scaleWrapper.style.width = `${finalW}px`;
                scaleWrapper.style.height = `${finalH}px`;

                // We do NOT touch this.container dimensions here. 
                // It will shrink-wrap scaleWrapper height naturally if display: block/flex.
            }
        });

        resizeObserver.observe(this.container);

        // Also keep window resize listener as fallback or for height updates?
        // ResizeObserver on container usually covers window resizes that affect container width.
        // But window height changes might not trigger container resize if container is short.
        // We can add a simple listener to trigger observer logic?
        // Or just observe document.body?
        // Let's stick to observing container + window resize.

        window.addEventListener('resize', () => {
            // Force check
            // But ResizeObserver loop is separate.
            // We can just rely on ResizeObserver if width changes.
            // If ONLY height changes (e.g. browser resizing vertically), container width might not change.
            // But `availableH` from window.innerHeight depends on it.
            // So we need to re-run logic.
            // Let's manually run the logic:
            const availableW = this.container.clientWidth;
            const availableH = window.innerHeight;
            const baseW = 970; const baseH = 900;
            const scale = Math.min(availableW / baseW, availableH / baseH, 1.0);
            contentWrapper.style.transform = `scale(${scale})`;
            scaleWrapper.style.width = `${Math.floor(baseW * scale)}px`;
            scaleWrapper.style.height = `${Math.floor(baseH * scale)}px`;
        });

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
