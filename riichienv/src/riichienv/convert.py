def tid_to_mpsz(tid: int) -> str:
    """
    Convert 136-based tile ID to MPSZ string (e.g. 1z, 5p, 0p).
    0-based index: 0 is red 5 for m, p, s.
    """
    if not (0 <= tid < 136):
        raise ValueError(f"Invalid TID: {tid}")

    # Check Red 5
    # 5m: 16-19. 16 is red (usually).
    # 5p: 52-55. 52 is red.
    # 5s: 88-91. 88 is red.
    if tid == 16:
        return "0m"
    if tid == 52:
        return "0p"
    if tid == 88:
        return "0s"

    kind = tid // 36
    if kind < 3:
        suit_char = ["m", "p", "s"][kind]
        offset = tid % 36
        num = offset // 4 + 1
        return f"{num}{suit_char}"
    else:
        offset = tid - 108
        num = offset // 4 + 1
        return f"{num}z"


def tid_to_mjai(tid: int) -> str:
    """
    Convert 136-based tile ID to MJAI string (e.g. E, 5p, 5pr).
    """
    if not (0 <= tid < 136):
        raise ValueError(f"Invalid TID: {tid}")

    # Red 5s
    if tid == 16:
        return "5mr"
    if tid == 52:
        return "5pr"
    if tid == 88:
        return "5sr"

    kind = tid // 36
    if kind < 3:
        suit_char = ["m", "p", "s"][kind]
        offset = tid % 36
        num = offset // 4 + 1
        return f"{num}{suit_char}"
    else:
        offset = tid - 108
        num = offset // 4 + 1
        # MJAI Honors: E, S, W, N, P, F, C
        mjai_honors = ["E", "S", "W", "N", "P", "F", "C"]
        if 1 <= num <= 7:
            return mjai_honors[num - 1]
        return f"{num}z"  # Fallback? Should not reach


def mpsz_to_tid(mpsz_str: str) -> int:
    """
    Convert MPSZ string to TID. Returns canonical TID.
    e.g. 1z -> 108, 0p -> 52, 5p -> 53 (non-red).
    """
    if not mpsz_str:
        raise ValueError("Empty string")

    suit = mpsz_str[-1]
    num_str = mpsz_str[:-1]

    if suit not in ["m", "p", "s", "z"]:
        raise ValueError(f"Invalid suit: {suit}")

    try:
        num = int(num_str)
    except ValueError:
        raise ValueError(f"Invalid number: {num_str}")

    if suit == "z":
        if not (1 <= num <= 7):
            raise ValueError(f"Invalid honor number: {num}")
        # 1z start 108. (num-1)*4 + 108
        return 108 + (num - 1) * 4

    # m, p, s
    suit_idx = {"m": 0, "p": 1, "s": 2}[suit]
    base_idx = 36 * suit_idx

    if num == 0:
        # Red 5
        # 5m: 16, 5p: 52 (36+16), 5s: 88 (72+16)
        return base_idx + 16

    if not (1 <= num <= 9):
        raise ValueError(f"Invalid number: {num}")

    # Normal tile
    # (num-1)*4
    offset = (num - 1) * 4
    # If 5 (non-red), we skip the red one (index 0 of the set of 4 5s) usually?
    # IDs for 5: 16,17,18,19 (relative: 16,17,18,19 of suit block 0-35)
    # Relative offset for 5 is 16.
    # 0 -> 16 (Red)
    # 5 -> 17 (Non-Red)?
    # My tid_to_mpsz: 16->0m. 17->5m.
    # So if num is 5, we should return the first non-red 5.
    # 5m: 16(R), 17, 18, 19.
    # If input is '5m', return 17.

    tid = base_idx + offset
    if num == 5:
        # Check against red ID logic.
        # offset for 5 is 16.
        # base+16 is red.
        # We want non-red, so +1?
        return base_idx + 16 + 1

    return tid


def mpsz_to_mjai(mpsz_str: str) -> str:
    # mpsz -> tid -> mjai
    tid = mpsz_to_tid(mpsz_str)
    return tid_to_mjai(tid)


def mjai_to_tid(mjai_str: str) -> int:
    """
    Convert MJAI string to TID.
    E, S, W, N, P, F, C -> Honors
    5pr -> Red 5p (52)
    5p -> Non-red 5p (53)
    """
    # Check Honors
    honors_map = {"E": 1, "S": 2, "W": 3, "N": 4, "P": 5, "F": 6, "C": 7}
    if mjai_str in honors_map:
        num = honors_map[mjai_str]
        return 108 + (num - 1) * 4

    # Check Red Suffix 'r'
    is_red = mjai_str.endswith("r")
    core = mjai_str[:-1] if is_red else mjai_str

    # Parse core as if it were mpsz, but note honor handling
    # MJAI uses 5mr.
    # Core is 5m.

    # Use mpsz_to_tid logic for core?
    # But wait, MJAI string '5p' (no r) is 5p non-red.
    # mpsz string '5p' is also 5p non-red.
    # mpsz string '0p' is 5p red.

    # If is_red is True, we want 0p equivalent.

    if is_red:
        # Expected core: 5m, 5p, 5s.
        if core not in ["5m", "5p", "5s"]:
            raise ValueError(f"Invalid red spec: {mjai_str}")
        # Convert to 0m, 0p, 0s
        mpsz_equiv = "0" + core[1:]
        return mpsz_to_tid(mpsz_equiv)

    return mpsz_to_tid(mjai_str)


def mjai_to_mpsz(mjai_str: str) -> str:
    tid = mjai_to_tid(mjai_str)
    return tid_to_mpsz(tid)


# List versions
def tid_to_mpsz_list(tid_list: list[int]) -> list[str]:
    return [tid_to_mpsz(t) for t in tid_list]


def tid_to_mjai_list(tid_list: list[int]) -> list[str]:
    return [tid_to_mjai(t) for t in tid_list]


def mpsz_to_tid_list(mpsz_list: list[str]) -> list[int]:
    return [mpsz_to_tid(s) for s in mpsz_list]


def mpsz_to_mjai_list(mpsz_list: list[str]) -> list[str]:
    return [mpsz_to_mjai(s) for s in mpsz_list]


def mjai_to_tid_list(mjai_list: list[str]) -> list[int]:
    return [mjai_to_tid(s) for s in mjai_list]


def mjai_to_mpsz_list(mjai_list: list[str]) -> list[str]:
    return [mjai_to_mpsz(s) for s in mjai_list]


def paishan_to_wall(paishan_str: str) -> list[int]:
    """
    Parses a paishan string (concatenated MPSZ, e.g. "1m2m3p") into a list of 136 unique Tile IDs.
    Handles duplicate tiles by tracking counts (e.g. first "1m" -> 0, second "1m" -> 1).
    """
    if len(paishan_str) % 2 != 0:
        raise ValueError(f"Invalid paishan string length: {len(paishan_str)}")

    wall = []
    tid_count = {}

    for i in range(0, len(paishan_str), 2):
        chunk = paishan_str[i : i + 2]
        tid_base = mpsz_to_tid(chunk)

        # Determine offset for uniqueness (0, 1, 2, 3)
        # mpsz_to_tid returns the base canonical ID.
        # We assume paishan lists tiles sequentially.
        # If "1m" appears 4 times, they should map to canonical, canonical+1, etc.
        # EXCEPT for Red 5s?
        # mpsz_to_tid("0m") -> 16 (Red 5m).
        # mpsz_to_tid("5m") -> 17 (Normal 5m start).
        # If paishan has "0m", it maps to 16. Count 0 -> 16.
        # If paishan has "5m" x 3, it maps to 17. Count 0->17, 1->18, 2->19.
        # This assumes the canonical ID base accounts for Red/Non-Red distinction correctly.
        # 5m (17) range is 17, 18, 19? Or 16, 17, 18, 19?
        # Let's check mpsz_to_tid implementation.
        # 5m -> 17?
        # 5m Red is 16.
        # Normal 5m starts at 17? Or 16?
        # Typically 5m TIDs: 16, 17, 18, 19.
        # If 16 is Red, then 17, 18, 19 are normal.
        # mpsz_to_tid("5m"):
        #   base_idx = 0. num=5.
        #   return base_idx + (4*4) = 16? No.
        #   offset = (num-1)*4 = 16. returns 0+16 = 16.
        #   So "5m" returns 16?
        #   Wait, line 90: base_idx = 36 * suit_idx.
        #   line 103: return base_idx + (num - 1) * 4.
        #   For 5m: 0 + (4)*4 = 16.
        #   But Red 5 check at line 94: if num==0 return base_idx+16.
        #   So "0m" -> 16. "5m" -> 16.
        #   This is a collision if we use simple offsets!
        #   But TIDs are unique 0-135.
        #   5m (Red) is 16. 5m (Normal) are 17, 18, 19.
        #   If `mpsz_to_tid("5m")` returns 17, good.
        #   Let's check code.

        cnt = tid_count.get(tid_base, 0)

        # Correction for 5s:
        # If "0m" (Red) comes, it uses TID 16.
        # If "5m" comes, it uses TID ?
        # We need to ensure we don't produce duplicate TIDs.
        # If base logic returns 16 for "5m", and we have "0m" (16) and "5m" (16),
        # we need to shift "5m" to 17, 18, 19.

        # Current mpsz_to_tid logic (inferred):
        # returns base_idx + (num-1)*4. So "5m" -> 16.
        # "0m" -> 16.
        # So "5m" and "0m" collide at base 16.

        # Strategy:
        # 1. Map to base IDs. 0m->16, 5m->16.
        # 2. Track usage count for base 16.
        #    If we see 16 used (e.g. from 0m), next request for 16 (from 5m) gets 17.
        #    BUT we must ensure proper Red/Normal assignment if strictly required.
        #    Paishan "0m" means specifically the Red tile. "5m" means Normal.
        #    If we treat them all as bucket 16..19:
        #    "0m" -> bucket 5m.
        #    "5m" -> bucket 5m.
        #    If we assign sequentially 16, 17, 18, 19...
        #    Does 16 HAVE to be Red?
        #    In `tid_to_mpsz`, 16 returns "0m". 17,18,19 return "5m".
        #    So yes, 16 is Red.
        #    We must ensure "0m" gets 16. "5m" gets 17, 18, 19.

        # Revised Logic:
        # If chunk is "0m", force ID 16.
        # If chunk is "5m", force IDs 17, 18, 19.
        # Generalize:
        # "0x" -> RedID.
        # "5x" -> NormalIDs.

        real_tid = tid_base

        # Red Handling
        is_red_str = chunk.startswith("0")
        if is_red_str:
            # tid_base is correct (e.g. 16 for 0m)
            # Just use it.
            pass
        else:
            # "5m" -> 16. Since we want non-red, we start at 17?
            # Check collision with Red ID.
            # 5m base is 16.
            # If 16 is reserved for Red, normal start at 17.
            if tid_base in [16, 52, 88]:
                real_tid += 1  # Start at 17, 53, 89

        # Now apply offset for multiples
        # We track count per real_tid base?
        # No, for normals like "1m" (0): 0, 1, 2, 3.
        # "5m" (17): 17, 18, 19.
        # count for 17 should increment 17->18->19.

        cnt = tid_count.get(real_tid, 0)
        final_tid = real_tid + cnt
        tid_count[real_tid] = cnt + 1

        wall.append(final_tid)

    return wall
