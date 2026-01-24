from riichienv import Action, ActionType, Phase, RiichiEnv


def test_honba_reset_on_ko_win():
    # Initialize env
    env = RiichiEnv(game_mode="4p-red-half", seed=42)
    # Start with Oya 0, Honba 5
    env.reset(oya=0, honba=5)

    # Force a win for Player 1 (Ko) via Ron
    # Player 0 discards 7m, Player 1 calls Ron
    # Setup Hands
    # Player 1 has 7m pairs (Tenpai waiting on 7m/24)
    h1 = [0, 0, 4, 4, 8, 8, 12, 12, 16, 16, 20, 20, 24]
    # Player 0 has Tid 24 to discard
    h0 = [1, 1, 5, 5, 9, 9, 13, 13, 17, 17, 21, 21, 25, 24]  # 14 tiles for Oya

    hands = env.hands
    hands[0] = h0
    hands[1] = h1
    env.hands = hands

    # 0 discards 24 (7m)
    env.current_player = 0
    env.needs_tsumo = False
    env.phase = Phase.WaitAct
    env.active_players = [0, 1, 2, 3]

    # Step where 0 discards
    obs = env.step({0: Action(ActionType.Discard, 24, [])})

    # Now it should be WaitResponse phase, Player 1 can Ron
    assert env.phase == Phase.WaitResponse
    assert env.last_discard == (0, 24)  # (pid, tile)

    # Player 1 Rons
    env.step({1: Action(ActionType.Ron, 24, [])})

    # Transition to end state
    print(f"DEBUG: Honba before next step: {env.honba}")
    env.step({})  # Trigger initialization
    print(f"DEBUG: Honba after win: {env.honba}")

    assert env.honba == 0, f"Honba should reset to 0 after Ko Ron win, but got {env.honba}"
    assert env.oya == 1, f"Oya should rotate to 1, got {env.oya}"


def test_honba_increment_on_oya_win():
    # Initialize env
    env = RiichiEnv(game_mode="4p-red-half", seed=42)
    env.reset()

    # Set initial state: Oya is Player 0, Honba is 5
    env.set_state(oya=0, honba=5)

    # Force a win for Player 0 (Oya)
    env.current_player = 0
    h0 = [0, 0, 4, 4, 8, 8, 12, 12, 16, 16, 20, 20, 24]
    hands = env.hands
    hands[0] = h0
    env.hands = hands
    env.drawn_tile = 24
    env.needs_tsumo = False
    env.phase = Phase.WaitAct

    env.step({0: Action(ActionType.Tsumo)})

    # Trigger initialization
    env.step({})

    print(f"DEBUG: Honba after Oya win: {env.honba}")

    assert env.honba == 6, f"Honba should increment to 6 after Oya win, but got {env.honba}"
    assert env.oya == 0, f"Oya should remain 0, got {env.oya}"


if __name__ == "__main__":
    test_honba_reset_on_ko_win()
    test_honba_increment_on_oya_win()
