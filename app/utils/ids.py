from __future__ import annotations

import secrets


def new_idempotency_key(prefix: str = "idem") -> str:
    return f"{prefix}_{secrets.token_urlsafe(18)}"


def new_confirmation_token(prefix: str = "confirm") -> str:
    return f"{prefix}_{secrets.token_urlsafe(18)}"
