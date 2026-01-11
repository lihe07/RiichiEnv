import { TileRenderer } from './tile_renderer';
import { COLORS } from '../constants';
import { CHAR_SPRITE_BASE64, CHAR_MAP } from '../char_assets';

export class CenterRenderer {
    static renderCenter(
        state: any,
        onCenterClick: (() => void) | null,
        viewpoint: number = 0
    ): HTMLElement {
        const center = document.createElement('div');
        center.className = 'center-info';
        Object.assign(center.style, {
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            backgroundColor: COLORS.centerInfoBackground,
            padding: '15px',
            borderRadius: '8px',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: '10',
            boxShadow: '0 4px 6px rgba(0,0,0,0.3)',
            width: '200px',
            height: '200px',
            boxSizing: 'border-box',
            cursor: 'pointer' // Added cursor pointer
        });

        center.onclick = (e) => {
            e.stopPropagation();
            if (onCenterClick) onCenterClick();
        };

        // Render Wind Labels
        const windMap = ['東_red', '南', '西', '北']; // Keys in CHAR_MAP
        state.players.forEach((p: any, i: number) => {
            const relPos = (i - viewpoint + 4) % 4; // 0: Bottom, 1: Right, 2: Top, 3: Left
            const windIdx = p.wind; // 0: East, 1: South, ...
            if (windIdx < 0 || windIdx > 3) return;

            const assetKey = windMap[windIdx];
            const asset = CHAR_MAP[assetKey];
            if (!asset) return;

            const icon = document.createElement('div');
            Object.assign(icon.style, {
                position: 'absolute',
                width: '30px',
                height: '30px',
                pointerEvents: 'none',
                backgroundImage: `url(${CHAR_SPRITE_BASE64})`,
                backgroundPosition: `-${asset.x}px -${asset.y}px`,
                backgroundRepeat: 'no-repeat',
                // Scale the sprite chunk: define sprite scale relative to rendered size
                // However, our sprite is fontSize=36, rendered in 30x30.
                // We don't have explicit sprite-sheet scaling here without background-size.
                // If background-size is not set, it uses original image size.
                // We should probably set background-size appropriate to scale down?
                // Or rely on the fact that we can't easily scale sprites non-uniformly without background-size covering whole sprite.
                // Actually, if we use just background-position, we display the image at 1:1 scale of the png.
                // Generated font size 36 is likely around 36px high.
                // If we want 30px container, we can let it clip or scale.
                // To scale correctly: custom background-size logic is tricky with sprites unless uniform.
                // Let's assume we want to just display it centered or as is. 36px might be slightly large for 30px box.
                // Let's use 'transform: scale()' on the div if needed, or rely on visual fit.
                // Let's try simple rendering first. If too big, we scale the div.
            });
            // To make the sprite glyph fit 30x30:
            // Since we don't know the exact total width of sprite easily here (unless we export it), 
            // scaling background-size is hard.
            // Better to scale the CONTAINER DIV using transform if it's too big.
            // Or just ensure the generated sprite size (36px font) roughly fits or is scaled down by the user's browser default? No.

            // Wait, we can scale the element itself.
            // icon.style.zoom = ...? No, deprecated.
            // transform: scale(30/36)?

            // Let's stick to 1:1 for now or adjust logic.
            // Actually, `background-size` requires total width/height.
            // Let's assume we render at 1:1 for now (which is 36px font ~> approx 36px+).
            // We set container to 30x30. It might clip.
            // Let's change the container to match asset size? Or scale down.
            // Let's accept clipping or overflow for a moment, or try to center it.
            // backgroundPosition is top-left.

            // Center the background image within the 30x30 box?
            // -${asset.x}px 

            // IMPORTANT: To support scaling, we'd need single images again or a very specific sprite approach.
            // Let's update `width` / `height` of the icon to match the ASSET size (from CHAR_MAP), then scale the icon div using CSS transform to fit 30px target.

            icon.style.width = `${asset.w}px`;
            icon.style.height = `${asset.h}px`;

            const targetSize = 26;
            const maxDim = Math.max(asset.w, asset.h);
            const scale = Math.min(1, targetSize / maxDim);

            icon.style.transformOrigin = 'center center'; // Scale from center

            // Combine rotation (from relPos) and scaling.
            let rotation = '0deg';
            if (relPos === 1) rotation = '-90deg';
            else if (relPos === 2) rotation = '180deg';
            else if (relPos === 3) rotation = '90deg';

            icon.style.transform = `rotate(${rotation}) scale(${scale})`;

            // Positioning Logic
            // "Left side from player's perspective"
            if (relPos === 0) { // Bottom -> Left side is Bottom-Left
                icon.style.bottom = '8px';
                icon.style.left = '8px';
                // 0 deg
            } else if (relPos === 1) { // Right -> Left side is Bottom-Right
                icon.style.right = '8px';
                icon.style.bottom = '8px';
            } else if (relPos === 2) { // Top -> Left side is Top-Right
                icon.style.top = '8px';
                icon.style.right = '8px';
            } else if (relPos === 3) { // Left -> Left side is Top-Left
                icon.style.left = '8px';
                icon.style.top = '8px';
            }
            center.appendChild(icon);
        });

        // Dora: Always 5 tiles. Fill missing with 'back'.
        const doraTiles = [...state.doraMarkers];
        while (doraTiles.length < 5) {
            doraTiles.push('back');
        }

        const doraHtml = doraTiles.map((t: string) =>
            `<div style="width:28px; height:38px;">${TileRenderer.getTileHtml(t)}</div>`
        ).join('');

        // Helper for formatting round
        const formatRound = (r: number) => {
            const winds = ['E', 'S', 'W', 'N'];
            const w = winds[Math.floor(r / 4)];
            const k = (r % 4) + 1;
            return `${w}${k}`;
        };

        center.innerHTML += `
            <div style="margin-bottom: 8px;">
                <span style="font-size: 1.2em; font-weight: bold;">${formatRound(state.round)}-${state.honba}</span>
                <span style="font-size: 0.9em; margin-left: 5px;">Depo: ${state.kyotaku}</span>
            </div>
            <div style="display:flex; align-items: center; gap: 5px;">
                <div style="display:flex; gap:2px;">
                    ${doraHtml}
                </div>
            </div>
        `;

        return center;
    }
}
