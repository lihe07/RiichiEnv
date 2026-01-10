import { Tile } from '../types';
import { TileRenderer } from './tile_renderer';

export class RiverRenderer {
    static renderRiver(discards: Tile[], highlightTiles?: Set<string>, dahaiAnim?: { discardIdx: number, insertIdx: number, tsumogiri: boolean }): HTMLElement {
        // River
        const riverDiv = document.createElement('div');
        riverDiv.className = 'river-container';

        // Split discards into rows
        const rows: Tile[][] = [[], [], []];
        discards.forEach((d, idx) => {
            if (idx < 6) rows[0].push(d);
            else if (idx < 12) rows[1].push(d);
            else rows[2].push(d);
        });

        const normalize = (t: string) => t.replace('0', '5').replace('r', '');

        rows.forEach((rowTiles) => {
            const rowDiv = document.createElement('div');
            rowDiv.className = 'river-row';
            rowDiv.style.height = '46px';

            rowTiles.forEach(d => {
                const cell = document.createElement('div');
                cell.style.width = '34px';
                cell.style.height = '46px';
                cell.style.position = 'relative'; // Important for overlay
                cell.style.flexShrink = '0'; // Prevent shrinking in 3rd row

                // Handle Riichi Rotation
                let contentContainer = cell;
                if (d.isRiichi) {
                    // Make space for rotated tile
                    cell.style.width = '42px';

                    const inner = document.createElement('div');
                    inner.style.width = '100%'; inner.style.height = '100%';
                    inner.className = 'tile-rotated';
                    inner.innerHTML = TileRenderer.getTileHtml(d.tile);
                    cell.appendChild(inner);
                    contentContainer = inner;
                    // User asked for "tile" to be red.
                    // If rotated, the visual tile is rotated. The buffer is square.
                    // Overlaying the square cell is simplest and effective.
                } else {
                    cell.innerHTML = TileRenderer.getTileHtml(d.tile);
                }

                if (d.isTsumogiri) cell.style.filter = 'brightness(0.7)';

                // Animation for the VERY LAST tile if dahaiAnim is present
                const idx = discards.indexOf(d);
                const isLast = (idx === discards.length - 1);
                if (isLast && dahaiAnim) {
                    contentContainer.classList.add('dahai-anim');
                    // Calculate offsets
                    // Y: Hand is at bottom (flex-end). River is above.
                    // Rough estimation: Vertical distance from Hand Center to River Row Center is ~200px.
                    // X: 
                    // If Tsumogiri: From Tsumo Pos (Right of hand, ~220px from center)
                    // If Tedashi: From Hand Pos (Index based).
                    // Hand tile width 40px. Hand center is 0. 13 tiles.
                    // Index 0 is -6.5 * 40 = -260px.
                    // Index 12 is +260px.
                    // Discard index k -> (k - 6) * 40.
                    // River Tile Pos:
                    // Row 0, 6 tiles centered? No, river row is left aligned?
                    // River Container is width 214px.
                    // Actually we need relative X from River Tile to Hand Tile.
                    // This is hard to get precise without bounding box.
                    // Approximation should be enough for visual flow.

                    let dx = 0;
                    if (dahaiAnim.tsumogiri) {
                        dx = 200; // From right side
                    } else {
                        // From discard index
                        // River row width ~214. Tile idx in river (0..5).
                        // River tile X approx: (idx % 6) * 36 - 100.
                        // Hand tile X: (discardIdx - 6) * 40.
                        // Delta X = HandX - RiverX.
                        const riverX = (idx % 6) * 36 - 107; // Approx center relative
                        const handX = (dahaiAnim.discardIdx - 6) * 40;
                        dx = handX - riverX;
                    }
                    contentContainer.style.setProperty('--dx', `${dx}px`);
                    contentContainer.style.setProperty('--dy', `150px`); // From below
                }

                // Highlight Logic
                if (highlightTiles) {
                    const normT = normalize(d.tile);
                    if (highlightTiles.has(normT)) {
                        const overlay = document.createElement('div');
                        Object.assign(overlay.style, {
                            position: 'absolute',
                            top: '0', left: '0',
                            width: '100%', height: '100%',
                            backgroundColor: 'rgba(255, 0, 0, 0.4)',
                            zIndex: '10',
                            pointerEvents: 'none',
                            borderRadius: '4px'
                        });
                        // Append to cell (non-rotated parent) so it covers the area
                        cell.appendChild(overlay);
                    }
                }

                rowDiv.appendChild(cell);
            });
            riverDiv.appendChild(rowDiv);
        });
        return riverDiv;
    }
}
