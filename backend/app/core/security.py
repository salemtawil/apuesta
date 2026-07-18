from fastapi import Header

from app.core.config import get_settings


def current_user_id(authorization: str | None = Header(default=None)) -> str:
    """Development auth shim.

    Production will validate Supabase JWT and return `sub`. Local development uses
    the demo UUID so the app can run without secrets.
    """
    if authorization and authorization.startswith("Bearer demo-"):
        return authorization.removeprefix("Bearer demo-")
    return get_settings().demo_user_id
