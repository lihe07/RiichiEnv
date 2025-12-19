from mahjong.agari import Agari
from mahjong.hand_calculating.hand import HandCalculator
from mahjong.tile import TilesConverter
from mahjong.hand_calculating.hand_config import HandConfig, OptionalRules
from mahjong.meld import Meld
from mahjong.constants import EAST, SOUTH, WEST, NORTH


if False:
    tiles = TilesConverter.string_to_136_array(man='789', pin='789', sou='66', has_aka_dora=False)
    win_tile = TilesConverter.string_to_136_array(pin='9')[0]
    melds = [
        Meld(Meld.PON, TilesConverter.string_to_136_array(honors='555')),
        Meld(Meld.CHI, TilesConverter.string_to_136_array(pin='456'))
    ]
    dora_indicators = None

    config = HandConfig(is_tsumo=False, round_wind=EAST, player_wind=EAST, options=OptionalRules(has_open_tanyao=True, has_aka_dora=False))

    calculator = HandCalculator()
    result = calculator.estimate_hand_value(tiles, win_tile, melds, dora_indicators, config)
    print(result)

if False:
    tiles = TilesConverter.string_to_136_array(man='789', pin='456789', sou='66', honors='777', has_aka_dora=False)
    win_tile = TilesConverter.string_to_136_array(pin='9')[0]
    melds = [
        Meld(Meld.PON, TilesConverter.string_to_136_array(honors='777')),
        Meld(Meld.CHI, TilesConverter.string_to_136_array(pin='456'))
    ]
    dora_indicators = None

    config = HandConfig(is_tsumo=False, round_wind=EAST, player_wind=EAST, options=OptionalRules(has_open_tanyao=True, has_aka_dora=False))

    calculator = HandCalculator()
    result = calculator.estimate_hand_value(tiles, win_tile, melds, dora_indicators, config)
    print(result)


def _make_meld(
    meld_type: str,
    is_open: bool = True,
    man: str = "",
    pin: str = "",
    sou: str = "",
    honors: str = "",
) -> Meld:
    tiles = TilesConverter.string_to_136_array(man=man, pin=pin, sou=sou, honors=honors)
    meld = Meld(meld_type=meld_type, tiles=tiles, opened=is_open, called_tile=tiles[0], who=0)
    return meld


if True:
    tiles = TilesConverter.one_line_string_to_136_array("667788m05678p678s", has_aka_dora=True)
    win_tile = TilesConverter.one_line_string_to_136_array("7s")[0]
    melds = [
        _make_meld(Meld.CHI, pin="678", is_open=True),
    ]

    tiles = [20, 21, 24, 25, 28, 29, 52, 53, 56, 60, 64, 92, 96, 100]
    win_tile = 96
    # print(">>>", tiles, win_tile, melds)
    # melds[0].tiles = [60, 64, 56]
    # melds[0].called_tile = None
    # melds[0].who = None
    # print(melds[0].__dict__)

    config = HandConfig(is_tsumo=True, round_wind=EAST, player_wind=EAST, options=OptionalRules(has_open_tanyao=True, has_aka_dora=True))
    calculator = HandCalculator()
    result = calculator.estimate_hand_value(tiles, win_tile, melds=melds, dora_indicators=None, config=config)
    print(result, result.yaku)


if False:
    tiles = TilesConverter.string_to_34_array(man="789", pin="456789", sou="66", honors="777")
    agari = Agari()
    print(agari.is_agari(tiles))


def _string_to_open_34_set(
    sou: str = "",
    pin: str = "",
    man: str = "",
    honors: str = "",
) -> list[int]:
    open_set = TilesConverter.string_to_136_array(sou=sou, pin=pin, man=man, honors=honors)
    open_set[0] //= 4
    open_set[1] //= 4
    open_set[2] //= 4
    return open_set


if False:
    tiles = TilesConverter.string_to_34_array(man="789", pin="456789", sou="66")
    melds = [
        _string_to_open_34_set(honors="777"),
    ]
    agari = Agari()
    print(agari.is_agari(tiles, melds))