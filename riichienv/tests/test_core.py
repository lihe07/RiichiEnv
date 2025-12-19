import pytest
import riichienv

def test_hand_creation():
    h = riichienv.Hand([0, 1, 2, 3, 4, 5, 0])
    assert str(h).startswith("Hand(counts=")

def test_agari():
    # 123m 456m 789m 123p 11s (indices: 0-8, 9-11, 18)
    tiles = [0,1,2, 3,4,5, 6,7,8, 9,10,11, 18,18]
    h = riichienv.Hand(tiles)
    assert riichienv.is_agari(h) == True

def test_not_agari():
    tiles = [0,0,0, 1,2,3, 4,5,6, 7,8,9, 10] # 13 tiles
    h = riichienv.Hand(tiles)
    # usually 14 tiles needed for standard check? 
    # Current impl just checks decomposition. 13 tiles might evaluate false or strictly 14?
    # Our backtrack checks "if pair found, decompose rest".
    # 13 tiles: 1 pair (2) -> 11 tiles. 11 is not divisible by 3.
    # It should return false.
    assert riichienv.is_agari(h) == False

def test_score_calculation():
    # 30fu 4han -> 7700 or 7900/8000(Kiriage).
    # with Kiriage -> 8000.
    # without Kiriage -> 7900 (3900/2000)
    score = riichienv.calculate_score(4, 30, False, True)
    assert score.pay_tsumo_oya == 3900
    assert score.pay_tsumo_ko == 2000
    assert score.total == 7900

def test_hand_parsing():
    from riichienv import AgariCalculator, Meld, MeldType

    # Test hand_from_text (13 tiles)
    text = "123m456p789s111z2z" # 13 tiles
    hand = AgariCalculator.hand_from_text(text)
    assert len(hand.tiles_136) == 13

    # Test to_text reciprocity (canonical grouping)
    # 111z2z -> 1112z
    assert hand.to_text() == "123m456p789s1112z"

    # Test with Red 5
    # Need 13 tiles: 055m (3) + 456p (3) + 789s (3) + 1122z (4) = 13
    text_red = "055m456p789s1122z"
    hand_red = AgariCalculator.hand_from_text(text_red)
    assert 16 in hand_red.tiles_136
    assert hand_red.to_text() == "055m456p789s1122z"

    # Test calc_from_text (14 tiles)
    # 123m 456p 789s 111z 22z. Win on 2z.
    # Hand including win tile: 123m456p789s111z22z (14)
    res = AgariCalculator.calc_from_text("123m456p789s111z22z")
    assert res.agari
    assert res.han > 0

    # Test with Melds (13 tiles total)
    # 123m (3) + 456p (3) + 789s (3) + 2z (1) + Pon 1z (3) = 13
    melded_text = "123m456p789s2z(p1z0)"
    hand_melded = AgariCalculator.hand_from_text(melded_text)
    assert len(hand_melded.tiles_136) == 10 # 13 total - 3 melded
    assert len(hand_melded.melds) == 1
    m = hand_melded.melds[0]
    assert m.meld_type == MeldType.Peng
    
    # to_text: 123m456p789s2z(p1z0)
    assert hand_melded.to_text() == "123m456p789s2z(p1z0)"

def test_yaku_scenarios():
    import riichienv
    from riichienv import AgariCalculator

    def get_tile(s):
        tiles, _ = riichienv.parse_hand(s)
        return tiles[0]

    scenarios = [
        {
            "name": "Tanyao",
            "hand": "234m234p234s66m88s",
            "win_tile": "6m",
            "min_han": 1, 
            "yaku_check": lambda y: 12 in y or 4 in y # MJSoul ID 4 or 12 (Observed)
        },
        {
            "name": "Pinfu",
            # 123m 456p 789s 23p 99m. Win 1p or 4p.
            "hand": "123m456p789s23p99m",
            "min_han": 1,
            "win_tile": "1p",
            "yaku_check": lambda y: 14 in y or 3 in y # MJSoul ID 3 or 14
        },
        {
            "name": "Yakuhai White",
            # 123m 456p 78s (Pon 5z) 88m. Win 9s.
            "hand": "123m456p78s88m(p5z0)",
            "win_tile": "9s",
            "min_han": 1,
            "yaku_check": lambda y: 7 in y or 12 in y or 18 in y # 7 is Observed
        },
        {
            "name": "Honitsu",
            # 123m 567m 11m 33z 22z. Win 2z.
            "hand": "123m567m111m33z22z",
            "win_tile": "2z",
            "min_han": 3,
            "yaku_check": lambda y: 27 in y or 29 in y or 30 in y or 34 in y # Honitsu ID (27 observed)
        },
        {
            "name": "Red Dora Pinfu",
            "hand": "234m067p678s34m22z",
            "win_tile": "5m", 
            "min_han": 2, 
            "yaku_check": lambda y: 14 in y or 3 in y 
        },
        {
            "name": "Regression Honroutou False Positive",
            "hand": "11s22z(p5z0)(456s0)(789m0)",
            "win_tile": "1s", 
            "min_han": 1,
            "yaku_check": lambda y: (18 in y or 7 in y) and (24 not in y) and (31 not in y)
        }
    ]

    for s in scenarios:
        hand_str = s["hand"]
        win_tile_str = s["win_tile"]
        print(f"Testing {s['name']}...")
        
        calc = AgariCalculator.hand_from_text(hand_str)
        win_tile_val = get_tile(win_tile_str)
        
        res = calc.calc(win_tile_val)
        
        if "yaku_check" in s:
            assert s["yaku_check"](res.yaku), f"{s['name']}: Yaku check failed. Got {res.yaku}"
