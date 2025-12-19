import riichienv

# 123m 456m 789m 123p 11s (standard Agari)
# m: 0-8, p: 9-17, s: 18-26
hand = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 18, 18]
h = riichienv.Hand(hand)
print(f"Hand: {h}")

# AgariCalculator
calc = riichienv.AgariCalculator(hand, [])
# Conditions(tsumo, riichi, double_riichi, ippatsu, haitei, houtei, rinshan, player_wind, round_wind, kyoutaku, tsumi)
conditions = riichienv.Conditions(tsumo=True, riichi=False, player_wind=1, round_wind=0)
res = calc.calc(18, [], conditions) # win_tile=18 (1s), no dora

print(f"Agari Result: {res.agari}")
print(f"Han: {res.han}, Fu: {res.fu}")
print(f"Score: oya={res.tsumo_agari_oya}, ko={res.tsumo_agari_ko}")

assert res.agari == True
assert res.han > 0
