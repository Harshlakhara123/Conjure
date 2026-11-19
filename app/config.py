import os
from pathlib import Path

from dotenv import dotenv_values

env_path = Path(__file__).resolve().parents[1] / ".env"
local_settings = dotenv_values(env_path, encoding="utf-8-sig")


def get_setting(name: str) -> str:
    value = os.environ.get(name, local_settings.get(name))
    if not value:
        raise RuntimeError(f"Missing configuration: {name}")
    return value


def get_frontend_origins() -> list[str]:
    return [
        origin.strip()
        for origin in get_setting("CLERK_AUTHORIZED_PARTIES").split(",")
        if origin.strip()
    ]