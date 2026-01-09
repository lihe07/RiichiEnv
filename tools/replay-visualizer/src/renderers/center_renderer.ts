import { TileRenderer } from './tile_renderer';

export class CenterRenderer {
    static renderCenter(
        state: any,
        onCenterClick: (() => void) | null
    ): HTMLElement {
        const center = document.createElement('div');
        center.className = 'center-info';
        Object.assign(center.style, {
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            backgroundColor: '#1a3317',
            padding: '15px',
            borderRadius: '8px',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: '10',
            boxShadow: '0 4px 6px rgba(0,0,0,0.3)',
            minWidth: '120px',
            cursor: 'pointer' // Added cursor pointer
        });

        center.onclick = (e) => {
            e.stopPropagation();
            if (onCenterClick) onCenterClick();
        };

        const doraHtml = state.doraMarkers.map((t: string) =>
            `<div style="width:28px; height:38px;">${TileRenderer.getTileHtml(t)}</div>`
        ).join('');

        // Helper for formatting round
        const formatRound = (r: number) => {
            const winds = ['E', 'S', 'W', 'N'];
            const w = winds[Math.floor(r / 4)];
            const k = (r % 4) + 1;
            return `${w}${k}`;
        };

        center.innerHTML = `
            <div style="font-size: 1.2em; font-weight: bold; margin-bottom: 5px;">
                ${formatRound(state.round)} <span style="font-size:0.8em; opacity:0.8; margin-left:5px;">Honba: ${state.honba}</span>
            </div>
            <div style="margin-bottom: 8px;">Kyotaku: ${state.kyotaku}</div>
            <div style="display:flex; align-items: center; gap: 5px;">
                <span>Dora:</span>
                <div style="display:flex; gap:2px;">
                    ${doraHtml}
                </div>
            </div>
        `;

        return center;
    }
}
