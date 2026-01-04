from riichienv import Action, ActionType, GameType, Meld, MeldType, Phase, RiichiEnv


def test_round_wind_yaku():
    """
    Test that Bakaze (Round Wind) is correctly identified as a Yaku.
    Specifically tests the fix where round_wind was hardcoded to Wind::East in _check_ron.
    """
    env = RiichiEnv(game_type=GameType.YON_HANCHAN, seed=42)

    # Init Round: South 1. Bakaze=South (1).
    env.reset(bakaze=1, oya=0, honba=0, kyotaku=0)

    pid = 3
    # North player in South 1.
    # Hand (10 tiles): 1m x 3, 2m x 3, 3m x 3, 9p x 1
    # Tiles: 1m(0,1,2), 2m(4,5,6), 3m(8,9,10), 9p(32)
    hand = [0, 1, 2, 4, 5, 6, 8, 9, 10, 32]

    # Melds (3 tiles): Pon South (112, 113, 114)
    m1 = Meld(MeldType.Peng, [112, 113, 114], True)

    hands = env.hands
    hands[pid] = hand
    env.hands = hands

    melds = env.melds
    melds[pid] = [m1]
    env.melds = melds

    # Total tiles: 10 (hand) + 3 (meld) = 13.
    # Wait: 9p (32-35) to complete the pair.

    # Trigger Ron on 9p (33)
    discard_tile = 33
    env.current_player = 2
    env.phase = Phase.WaitAct
    env.active_players = [2]

    # Step: P2 discards 9p
    obs_dict = env.step({2: Action(ActionType.DISCARD, tile=discard_tile)})

    assert pid in obs_dict, "P3 should receive an observation after discard."
    legals = obs_dict[pid].legal_actions()
    has_ron = any(a.type == ActionType.RON for a in legals)
    assert has_ron, "Ron should be legal because South (Bakaze) is a Yaku in a South round."
    obs_dict = env.step({pid: Action(ActionType.RON, tile=discard_tile)})
    # 11: 役牌:場風牌 => 南
    # 21: 対々和
    # 22: 三暗刻
    # 27: 混一色
    assert env.agari_results[pid].yaku == [11, 21, 22, 27]
