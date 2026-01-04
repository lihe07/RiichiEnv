from riichienv import RiichiEnv
from riichienv.action import Action, ActionType
from riichienv.agents import RandomAgent


class TestRiichiEnv:
    def test_run_full_game_random(self):
        # Deterministic random agents
        env = RiichiEnv(seed=123, game_type=1)
        agent = RandomAgent(seed=123)
        obs_dict = env.reset()

        steps = 0
        while not env.done() and steps < 1000:
            actions = {pid: agent.act(obs) for pid, obs in obs_dict.items()}
            obs_dict = env.step(actions)
            steps += 1

        # Either someone won or ryukyoku or aborted
        # Ryukyoku adds event logs
        last_ev = env.mjai_log[-1]["type"]
        assert last_ev in ["end_game", "end_kyoku", "hora"]
        # Note: In single-round mode, end_kyoku or hora are expected.

    def test_chi_claim(self):
        env = RiichiEnv(seed=42)
        env.reset()

        # Setup: P0 discards 3m (ID 8,9,10,11).
        # P1 (Right/Next) has 4m, 5m.
        # 3m, 4m, 5m sequence.

        tile_3m = 8
        tile_4m = 12
        tile_5m = 16

        h = env.hands
        h[0] = [tile_3m] + list(range(40, 40 + 12))
        h[1] = [tile_4m, tile_5m] + list(range(60, 60 + 11))
        h[1].sort()
        env.hands = h

        env.active_players = [0]
        env.current_player = 0

        env.drawn_tile = 100  # irrelevant

        # P0 Discards 3m
        env.step({0: Action(ActionType.DISCARD, tile=tile_3m)})

        # Should be in WaitResponse
        # P1 is next player (0->1 is Chi valid)
        assert env.phase == 1
        assert 1 in env.active_players

        # P1 Checks Legal
        obs = env.get_observations([1])[1]
        legals = obs.legal_actions()
        chi_actions = [a for a in legals if a.type == ActionType.CHI]
        assert len(chi_actions) > 0

        # P1 performs CHI
        action = Action(ActionType.CHI, tile=tile_3m, consume_tiles=[tile_4m, tile_5m])
        env.step({1: action})

        # P1 current player
        assert env.current_player == 1
        assert env.phase == 0

        last_ev = env.mjai_log[-1]
        assert last_ev["type"] == "chi"

    def test_ron_claim(self):
        env = RiichiEnv(seed=42)
        env.reset()

        # Setup P0 discards
        # P1 tenpai for 1m

        # 1m,1m,1m (0,1,2), 2m,2m,2m (4,5,6), 3m,3m,3m (8,9,10), 4m,4m,4m (12,13,14), 5m (16)
        # Wait 5m.
        p1_hand = [0, 1, 2, 4, 5, 6, 8, 9, 10, 12, 13, 14, 16]
        p1_hand = [0, 1, 2, 4, 5, 6, 8, 9, 10, 12, 13, 14, 16]
        h = env.hands
        h[1] = p1_hand
        env.hands = h

        env.active_players = [0]
        env.current_player = 0

        # P0 Discards 5m (ID 17, matches pair for 5m)
        tile_5m_target = 17
        h = env.hands
        h[0] = [tile_5m_target] + list(range(40, 40 + 13))
        h[0].sort()
        env.hands = h

        env.step({0: Action(ActionType.DISCARD, tile=tile_5m_target)})

        assert env.phase == 1
        assert 1 in env.active_players

        # P1 Legal Ron
        obs = env.get_observations([1])[1]
        ron = [a for a in obs.legal_actions() if a.type == ActionType.RON]
        assert len(ron) > 0

        # Execute Ron
        env.step({1: Action(ActionType.RON, tile=tile_5m_target)})

        # Should log Hora (A single Ron doesn't necessarily end the game)
        ev_types = [ev["type"] for ev in env.mjai_log[-3:]]
        assert "hora" in ev_types
