import lzma
import time
import glob
import gzip
import json
import tempfile

import tqdm

from riichienv import AgariCalculator, Conditions, ReplayGame, Wind
from mjsoul_parser import MjsoulPaifuParser, Paifu

YAKUMAN_IDS = [35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 47, 48, 49, 50]


def iter_game_kyoku(paifu: Paifu) -> Iterator[Kyoku]:
    uuid = paifu.header["uuid"]
    with tempfile.NamedTemporaryFile(delete=True) as f:
        with gzip.GzipFile(fileobj=f, mode="w") as g:
            g.write(json.dumps({"rounds": paifu.data}).encode("utf-8"))
        f.flush()
        f.seek(0)
        game = ReplayGame.from_json(f.name)

    for kyoku in game.take_kyokus():
        yield kyoku


def main():
    total_agari = 0
    t_riichienv_py = 0

    target_files = list(glob.glob("/data/mahjong_game_record_4p_*/*.bin.xz"))
    for path in tqdm.tqdm(target_files, desc="Processing files", ncols=100):
        with lzma.open(path, "rb") as f:
            data = f.read()
            paifu: Paifu = MjsoulPaifuParser.to_dict(data)

        for kyoku in iter_game_kyoku(paifu):
            for ctx in kyoku.take_agari_contexts():
                total_agari += 1

                expected_yakuman = len(set(ctx.expected_yaku) & set(YAKUMAN_IDS)) > 0
                expected_han = ctx.expected_han
                expected_fu = ctx.expected_fu

                # Riichienv (py)
                t0 = time.time()
                cond_py = Conditions()
                for attr in [
                    "tsumo",
                    "riichi",
                    "double_riichi",
                    "ippatsu",
                    "haitei",
                    "houtei",
                    "rinshan",
                    "chankan",
                    "tsumo_first_turn",
                    "player_wind",
                    "round_wind",
                    "kyoutaku",
                    "tsumi",
                ]:
                    setattr(cond_py, attr, getattr(ctx.conditions, attr))

                res_r_py = AgariCalculator(
                    tiles=ctx.tiles,
                    melds=ctx.melds,
                ).calc(ctx.agari_tile, ctx.dora_indicators, cond_py, ctx.ura_indicators)
                t_riichienv_py += time.time() - t0

                if not res_r_py.agari:
                    print(f"Error in {log_path} (riichienv-py): not agari")
                    print(f"  Closed Tiles (ctx.tiles): {ctx.tiles} (len={len(ctx.tiles)})")
                    print(f"  Win Tile (ctx.agari_tile): {ctx.agari_tile}")
                    print(f"  Melds (ctx.melds): {ctx.melds}")
                    # Try to see if win_tile is in tiles for Tsumo
                    if ctx.conditions.tsumo:
                        print(f"  Tsumo: win_tile in tiles? {ctx.agari_tile in ctx.tiles}")

                assert res_r_py.yakuman == expected_yakuman
                assert res_r_py.agari
                if expected_yakuman:
                    pass
                else:
                    assert res_r_py.han == expected_han, f"Han (py): {res_r_py.han} != {expected_han}"
                    assert res_r_py.fu == expected_fu, f"Fu (py): {res_r_py.fu} != {expected_fu}"

                # print(res_r_py.yaku, ctx.expected_yaku)

    print(f"{total_agari}: {t_riichienv_py:.2f} seconds")


if __name__ == "__main__":
    main()
