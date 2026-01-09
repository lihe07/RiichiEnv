import { Viewer } from './index';

export class ReplayController {
    viewer: Viewer;
    autoPlayTimer: number | null = null;
    private logBtn: HTMLElement | null = null;
    private autoBtn: HTMLElement | null = null;

    constructor(viewer: Viewer) {
        this.viewer = viewer;
    }

    setupKeyboardControls(target: HTMLElement | Window) {
        target.addEventListener('keydown', (e: any) => {
            if (e.key === 'ArrowRight') this.stepForward();
            if (e.key === 'ArrowLeft') this.stepBackward();
            if (e.key === 'ArrowUp') this.prevTurn();
            if (e.key === 'ArrowDown') this.nextTurn();
        });
    }

    setupWheelControls(target: HTMLElement) {
        let lastWheelTime = 0;
        const WHEEL_THROTTLE_MS = 100;

        target.addEventListener('wheel', (e) => {
            e.preventDefault();
            e.stopPropagation();
            e.stopImmediatePropagation();

            const now = Date.now();
            if (now - lastWheelTime < WHEEL_THROTTLE_MS) return;
            lastWheelTime = now;

            if (e.deltaY > 0) {
                this.nextTurn();
            } else {
                this.prevTurn();
            }
        }, { passive: false });
    }

    stepForward() {
        if (this.viewer.gameState.stepForward()) this.viewer.update();
    }

    stepBackward() {
        if (this.viewer.gameState.stepBackward()) this.viewer.update();
    }

    nextTurn() {
        const vp = this.viewer.renderer.viewpoint;
        if (this.viewer.gameState.jumpToNextTurn(vp)) this.viewer.update();
    }

    prevTurn() {
        const vp = this.viewer.renderer.viewpoint;
        if (this.viewer.gameState.jumpToPrevTurn(vp)) this.viewer.update();
    }

    toggleAutoPlay(btn: HTMLElement) {
        this.autoBtn = btn;
        if (this.autoPlayTimer) {
            clearInterval(this.autoPlayTimer);
            this.autoPlayTimer = null;
            btn.classList.remove('active-btn');
        } else {
            btn.classList.add('active-btn');
            this.autoPlayTimer = window.setInterval(() => {
                if (!this.viewer.gameState.stepForward()) {
                    if (this.autoPlayTimer) clearInterval(this.autoPlayTimer);
                    this.autoPlayTimer = null;
                    btn.classList.remove('active-btn');
                } else {
                    this.viewer.update();
                }
            }, 200);
        }
    }

    toggleLog(btn: HTMLElement, panel: HTMLElement) {
        this.logBtn = btn;
        const display = panel.style.display;
        if (display === 'none' || !display) {
            panel.style.display = 'block';
            btn.classList.add('active-btn');
        } else {
            panel.style.display = 'none';
            btn.classList.remove('active-btn');
        }
    }
}
