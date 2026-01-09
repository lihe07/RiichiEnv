import { Tile } from '../types';
import { TileRenderer } from './tile_renderer';

export class RiverRenderer {
    static renderRiver(discards: Tile[]): HTMLElement {
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

        rows.forEach((rowTiles) => {
            const rowDiv = document.createElement('div');
            rowDiv.className = 'river-row';
            rowDiv.style.height = '46px';

            rowTiles.forEach(d => {
                const cell = document.createElement('div');
                cell.style.width = '34px';
                cell.style.height = '46px';
                cell.style.position = 'relative';
                cell.style.flexShrink = '0'; // Prevent shrinking in 3rd row

                if (d.isRiichi) {
                    const inner = document.createElement('div');
                    inner.style.width = '100%'; inner.style.height = '100%';
                    inner.className = 'tile-rotated';
                    inner.innerHTML = TileRenderer.getTileHtml(d.tile);
                    cell.appendChild(inner);
                } else {
                    cell.innerHTML = TileRenderer.getTileHtml(d.tile);
                }
                if (d.isTsumogiri) cell.style.filter = 'brightness(0.7)';
                rowDiv.appendChild(cell);
            });
            riverDiv.appendChild(rowDiv);
        });
        return riverDiv;
    }
}
