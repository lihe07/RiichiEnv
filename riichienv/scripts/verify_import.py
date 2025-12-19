import riichienv
import sys

print(f"RiichiEnv version: {riichienv.__version__ if hasattr(riichienv, '__version__') else 'unknown'}")
print(f"Python version: {sys.version}")

# Test Hand
print("\nTesting Hand...")
h = riichienv.Hand([0, 1, 2, 3, 4, 5, 0, 0])
print(f"Hand created: {h}")

# Test Agari
print("\nTesting Agari...")
# 123m 456m 789m 11s 22s (not really valid, just checking structure)
# Let's make a real agari: 123m 456m 789m 123p 11s
ts = [0,1,2, 3,4,5, 6,7,8, 9,10,11, 18,18]
h_agari = riichienv.Hand(ts)
is_agari = riichienv.is_agari(h_agari)
print(f"Is Agari: {is_agari} (expected True)")

# Test Score
print("\nTesting Score...")
score = riichienv.calculate_score(4, 30, False, True)
print(f"Score: total={score.total}, pay_oya={score.pay_tsumo_oya}, pay_ko={score.pay_tsumo_ko}")
assert score.pay_tsumo_oya == 3900 or score.pay_tsumo_oya == 4000
