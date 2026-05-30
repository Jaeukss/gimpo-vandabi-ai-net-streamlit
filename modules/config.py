"""Configuration helpers that never read local key files directly."""

from __future__ import annotations

import os
from typing import Any


CONFIG_STATUS_KEYS = (
    "OPENROUTER_API_KEY",
    "OPENROUTER_MODEL",
    "VWORLD_API_KEY",
    "DATA_GO_KR_SERVICE_KEY",
    "SENDGRID_API_KEY",
    "EMAIL_ADDRESS",
    "ENABLE_SENDGRID_SEND",
    "VISION_MODEL",
)

TRUE_STRINGS = {"true", "1", "yes", "y", "on"}


def get_secret(name: str, default: Any = None) -> Any:
    """Read a value from st.secrets first, then os.environ; return default on any failure."""
    try:
        import streamlit as st

        value = st.secrets.get(name, None)
        if value not in (None, ""):
            return value
    except Exception:
        pass

    try:
        value = os.environ.get(name)
        if value not in (None, ""):
            return value
    except Exception:
        pass

    return default


def get_bool_secret(name: str, default: bool = False) -> bool:
    value = get_secret(name, None)
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in TRUE_STRINGS


def list_config_status() -> dict[str, bool]:
    """Return whether supported settings exist without exposing actual values."""
    return {key: get_secret(key, None) not in (None, "") for key in CONFIG_STATUS_KEYS}


def get_setting(name: str, default: Any = "") -> Any:
    """Backward-compatible alias for earlier modules."""
    return get_secret(name, default)


def get_bool_setting(name: str, default: bool = False) -> bool:
    """Backward-compatible alias for earlier modules."""
    return get_bool_secret(name, default)


def configured(name: str) -> bool:
    return get_secret(name, None) not in (None, "")
