## Tile Representations

Three representation formats:
1. **136-based tile ID (TID)**: Integer (0-135). Distinguishes individual tiles (e.g., four 1m tiles are 0, 1, 2, 3).
2. **MPSZ string**: String (e.g., "1z", "5p", "0p"). "0" denotes red five.
3. **MJAI string**: String (e.g., "E", "5p", "5pr"). "r" suffix denotes red five. "E" for East, etc.

### Examples

* **TID**: 108, 53, 52
* **MPSZ**: 1z, 5p, 0p
* **MJAI**: E, 5p, 5pr

**Note**: In RiichiEnv, we use **TID** as the internal representation. MJAI string is primarily used for user interfaces where distinct tiles of the same type are not distinguished.

### Conversion Functions

Available in `riichienv.convert`:

*   **TID (int) ↔ MPSZ (str)**
    *   `tid_to_mpsz(tid: int) -> str`
    *   `mpsz_to_tid(mpsz_str: str) -> int` (Returns canonical TID, red if specified)

*   **TID (int) ↔ MJAI (str)**
    *   `tid_to_mjai(tid: int) -> str`
    *   `mjai_to_tid(mjai_str: str) -> int` (Returns canonical TID)

*   **MPSZ (str) ↔ MJAI (str)**
    *   `mpsz_to_mjai(mpsz_str: str) -> str`
    *   `mjai_to_mpsz(mjai_str: str) -> str`

#### List Conversions

*   `tid_to_mpsz_list(tid_list: list[int]) -> list[str]`
*   `tid_to_mjai_list(tid_list: list[int]) -> list[str]`
*   `mpsz_to_tid_list(mpsz_list: list[str]) -> list[int]`
*   `mpsz_to_mjai_list(mpsz_list: list[str]) -> list[str]`
*   `mjai_to_tid_list(mjai_list: list[str]) -> list[int]`
*   `mjai_to_mpsz_list(mjai_list: list[str]) -> list[str]`

