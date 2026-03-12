import os
import msal

# ---- Config ----
CLIENT_ID = "27ebca83-bde3-4ebf-bc90-1e3fb8757557"  # tu Application (client) ID
AUTHORITY = "https://login.microsoftonline.com/consumers"  # cuentas personales Microsoft
SCOPES = ["Files.Read", "Files.Read.All", "User.Read"]  # delegados (NO incluyas offline_access)

# Cache file (en la raíz del proyecto)
BASE_PATH = os.path.dirname(os.path.dirname(__file__))  # .../REPORTE
CACHE_PATH = os.path.join(BASE_PATH, "token_cache.bin")


def _load_cache() -> msal.SerializableTokenCache:
    cache = msal.SerializableTokenCache()
    if os.path.exists(CACHE_PATH):
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            cache.deserialize(f.read())
    return cache


def _save_cache(cache: msal.SerializableTokenCache) -> None:
    if cache.has_state_changed:
        with open(CACHE_PATH, "w", encoding="utf-8") as f:
            f.write(cache.serialize())


def get_token() -> str:
    """
    Devuelve un access token.
    1) Intenta silent (cache)
    2) Si no hay, device flow (te pedirá login)
    """
    cache = _load_cache()

    app = msal.PublicClientApplication(
        client_id=CLIENT_ID,
        authority=AUTHORITY,
        token_cache=cache
    )

    # 1) Silent token (sin pedir login)
    accounts = app.get_accounts()
    result = None
    if accounts:
        result = app.acquire_token_silent(SCOPES, account=accounts[0])

    # 2) Device code (solo si no hay token en cache)
    if not result:
        flow = app.initiate_device_flow(scopes=SCOPES)
        if "user_code" not in flow:
            raise RuntimeError(f"Device flow init failed: {flow}")

        print(flow["message"])  # link + code
        result = app.acquire_token_by_device_flow(flow)

    if "access_token" not in result:
        raise RuntimeError(f"Token error: {result}")

    _save_cache(cache)
    return result["access_token"]