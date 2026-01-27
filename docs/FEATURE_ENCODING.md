# Feature Encoding Specification

This document describes the observation feature encoding used for `obs.encode()` in RiichiEnv.
The encoding produces a **(C, 34)** tensor, where C is the number of channels and 34 corresponds to the tile types (0-33).

## Channels Definition

Total Channels: **46** (Subject to implementation details)

| Channel Index | Description | Details |
| :--- | :--- | :--- |
| **0 - 3** | **Hand** | Binary encoding of hand tile counts (1, 2, 3, 4). <br> Ch 0: count >= 1, Ch 1: count >= 2, ... |
| **4** | **Red Tiles** | 1 if the tile in hand is Red. |
| **5 - 8** | **Melds (Self)** | Binary encoding of self melds. |
| **9 - 12** | **Discards (Self)** | Last 4 discards of self. |
| **13 - 24** | **Discards (Opponents)** | Last 4 discards of each opponent (Player +1, +2, +3). (3 players * 4 channels = 12). |
| **25 - 28** | **Discards (All - Counts)** | Count of discards for each tile type (normalized or bucketed). |
| **29** | **Dora Indicators** | 1 if tile is a Dora indicator. |
| **30** | **Riichi (Self)** | Broadcast 1 if self declared Riichi. |
| **31 - 33** | **Riichi (Opponents)** | Broadcast 1 if opponent declared Riichi. |
| **34** | **Round Wind** | Broadcast 1 at the tile index corresponding to the Round Wind. |
| **35** | **Self Wind** | Broadcast 1 at the tile index corresponding to the Self Wind. |
| **36** | **Scores (Self)** | Normalized score of self. |
| **38** | **Waits** | 1 at index of waiting tiles (if tenpai). |
| **39** | **Is Tenpai** | Broadcast 1 if tenpai. |
| **40 - 43** | **Rank** | One-hot encoding of player rank (based on score). |
| **44** | **Kyoku Index** | Normalized Kyoku index (approx 0-8). |
| **45** | **Tiles Seen** | Normalized count of all visible tiles (0, 0.25, 0.5, 0.75, 1.0). |

Total Channels: **46**
