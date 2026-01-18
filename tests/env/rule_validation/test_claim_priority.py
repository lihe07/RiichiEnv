from riichienv import Action, ActionType

from ..helper import helper_setup_env


class TestClaimPriority:
    """
    Verify claim priority: Pon > Chi.
    """

    def test_pon_priority_over_chi(self):
        """
        Setup scenario:

        1. Player 0 discards a tile.
        2. Player 1 (Next) wants to Chi.
        3. Player 2 (Opposite/Other) wants to Pon.
        4. Verify claim priority: Pon > Chi.
        """
        env = helper_setup_env(
            seed=1,
            hands=[
                [57] + [2] * 12,  # P0
                [62, 65] + [0] * 11,  # P1
                [56, 58] + [1] * 11,  # P2
                [12, 16, 19, 21, 48, 59, 64, 77, 81, 89, 104, 130, 133],  # P3
            ],
            current_player=0,
            active_players=[0],
            drawn_tile=100,
        )

        # P0 Discards 57
        env.step({0: Action(ActionType.DISCARD, tile=57)})

        # Now should be WaitResponse
        assert env.phase == 1

        # Check active players.
        # P1 (Next) can Chi?
        # P2 can Pon?
        # Ideally P1, P2 should be active.
        # Note: Depending on P3's hand, P3 might be active too if we didn't clear it, but default reset random hands.
        # Let's check who is active.
        print("Active players:", env.active_players)

        # We expect P1 and P2 to be in active_players if they have legal actions.
        assert 1 in env.active_players
        assert 2 in env.active_players

        # Submit Actions
        # P1 Chi
        action_chi = Action(ActionType.CHI, tile=57, consume_tiles=[62, 65])
        # P2 Pon
        action_pon = Action(ActionType.PON, tile=57, consume_tiles=[56, 58])

        # If P3 is also active (maybe random hand has something), we need to handle it.
        # For this test, ensure P3 is NOT active or provide dummy pass.
        # Simplest: Force P3 hand to be empty or garbage that can't claim 6p.
        # 57 is 6p.
        # P3 hand: [130]*13 (West/North/Etc that doesn't match 6p)
        if 3 in env.active_players:
            # Just pass for P3 if active
            pass

        actions = {1: action_chi, 2: action_pon}

        # If P3 active, add PASS
        if 3 in env.active_players:
            actions[3] = Action(ActionType.PASS)

        # Step
        env.step(actions)

        # Expectation:
        # Pon wins.
        # Current player becomes P2 (Ponner).
        # Phase becomes WaitAct (P2 must discard).

        print(f"DEBUG: Before Step. Phase is now {env.phase}")
        assert env.phase == 0  # Phase.WaitAct is 0 in Rust
        assert 2 in env.active_players

        # Check Log
        last_ev = env.mjai_log[-1]
        assert last_ev["type"] == "pon"
