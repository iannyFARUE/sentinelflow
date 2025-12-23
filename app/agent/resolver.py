from __future__ import annotations

import re

def parse_selection_index(user_message: str) -> int | None:
    msg = user_message.lower().strip()
    # "second", "2", "option 2"
    mapping = {"first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5}
    for word, idx in mapping.items():
        if word in msg:
            return idx
    m = re.search(r"\b(\d)\b", msg)
    if m:
        return int(m.group(1))
    return None
