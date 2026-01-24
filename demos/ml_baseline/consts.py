
# Constants for ML Baseline

# 34 tiles + Chi, Pon, Kan, Riichi, Agari, Pass
# Simplified Action Space
ACTION_SPACE_SIZE = 40

# Action Indices
ACT_DISCARD_START = 0
ACT_DISCARD_END = 33
ACT_CHI = 34
ACT_PON = 35
ACT_KAN = 36 # Daiminkan, Ankan, Kakan (Combined for simplicity or separate?)
ACT_RIICI = 37
ACT_AGARI = 38
ACT_PASS = 39

# Feature Channels
FEATURE_CHANNELS = 23

# CQL Constants
CQL_ALPHA = 1.0 # Regularization coefficient
