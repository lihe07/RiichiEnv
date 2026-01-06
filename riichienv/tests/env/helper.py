from riichienv import Meld, Phase, RiichiEnv


def helper_setup_env(
    seed: int = 42,
    game_type: int = 0,
    hands: list[list[int]] | None = None,
    melds: list[list[Meld]] | None = None,
    active_players: list[int] | None = None,
    current_player: int = 0,
    phase: Phase = Phase.WaitAct,
    needs_tsumo: bool = False,
    drawn_tile: int | None = None,
    wall: list[int] | None = None,
    mjai_log: list[dict] | None = None,
) -> RiichiEnv:
    env = RiichiEnv(seed=seed, game_type=game_type)
    env.reset()

    if hands is not None:
        for player_id in range(4):
            player_hand = hands[player_id]
            if player_hand:
                h = env.hands
                h[player_id] = player_hand
                env.hands[player_id].sort()
                env.hands = h

    if melds is not None:
        for player_id in range(4):
            if melds[player_id]:
                m = env.melds
                m[player_id] = melds[player_id]
                env.melds = m
    if active_players is not None:
        env.active_players = active_players
    if current_player is not None:
        env.current_player = current_player
    if phase is not None:
        env.phase = phase
    if needs_tsumo is not None:
        env.needs_tsumo = needs_tsumo
    if drawn_tile is not None:
        env.drawn_tile = drawn_tile
    if wall is not None:
        env.wall = wall
    if mjai_log is not None:
        env.mjai_log = mjai_log

    return env
