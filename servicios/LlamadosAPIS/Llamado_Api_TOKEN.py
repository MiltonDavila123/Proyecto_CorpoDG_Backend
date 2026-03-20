import base64
import os
import threading
import time

import requests
from django.conf import settings as django_settings

DEFAULT_SABRE_AUTH_URL = "https://api.cert.platform.sabre.com/v2/auth/token"
DEFAULT_TOKEN_DURATION_SECONDS = 604800

_TOKEN_LOCK = threading.Lock()
_TOKEN_CACHE = {"value": "", "expires_at": 0.0}


class SabreAuthError(RuntimeError):
    """Error controlado para fallos de autenticacion con Sabre."""


def _get_setting(name, default=""):
    if django_settings.configured:
        return getattr(django_settings, name, default)
    return os.getenv(name, default)


def _build_basic_auth(client_id, client_secret):
    # Mantiene el mismo esquema de codificacion que estabas usando en tu script.
    b64_client_id = base64.b64encode(client_id.encode("ascii")).decode("ascii")
    b64_client_secret = base64.b64encode(client_secret.encode("ascii")).decode("ascii")
    concatenated = f"{b64_client_id}:{b64_client_secret}"
    return base64.b64encode(concatenated.encode("ascii")).decode("ascii")


def _get_refresh_margin_seconds():
    raw_margin = _get_setting("SABRE_TOKEN_REFRESH_MARGIN", 60)
    try:
        return max(int(raw_margin), 0)
    except (TypeError, ValueError):
        return 60


def _solicitar_token_sabre():
    client_id = _get_setting("CLIENT_ID", "")
    client_secret = _get_setting("CLIENT_SECRET", "")
    auth_url = _get_setting("SABRE_AUTH_URL", DEFAULT_SABRE_AUTH_URL)

    if not client_id or not client_secret:
        raise ValueError(
            "Faltan CLIENT_ID o CLIENT_SECRET para autenticar con Sabre."
        )

    final_auth_string = _build_basic_auth(client_id, client_secret)

    headers = {
        "Authorization": f"Basic {final_auth_string}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {"grant_type": "client_credentials"}

    try:
        response = requests.post(auth_url, headers=headers, data=data, timeout=30)
    except requests.RequestException as error:
        raise SabreAuthError(f"No se pudo conectar con Sabre Auth: {error}") from error

    try:
        response_data = response.json()
    except ValueError:
        response_data = {}

    if response.status_code != 200:
        detail = response_data if response_data else response.text
        raise SabreAuthError(f"Sabre Auth Error [{response.status_code}]: {detail}")

    access_token = response_data.get("access_token")
    if not access_token:
        raise SabreAuthError("Sabre Auth Error: la respuesta no incluye access_token")

    try:
        expires_in = int(response_data.get("expires_in", DEFAULT_TOKEN_DURATION_SECONDS))
    except (TypeError, ValueError):
        expires_in = DEFAULT_TOKEN_DURATION_SECONDS

    return access_token, expires_in


def obtener_token_sabre(force_refresh=False):
    current_time = time.time()
    if (
        not force_refresh
        and _TOKEN_CACHE["value"]
        and current_time < _TOKEN_CACHE["expires_at"]
    ):
        return _TOKEN_CACHE["value"]

    with _TOKEN_LOCK:
        current_time = time.time()
        if (
            not force_refresh
            and _TOKEN_CACHE["value"]
            and current_time < _TOKEN_CACHE["expires_at"]
        ):
            return _TOKEN_CACHE["value"]

        token, expires_in = _solicitar_token_sabre()
        refresh_margin = _get_refresh_margin_seconds()
        cache_ttl = max(expires_in - refresh_margin, 1)

        _TOKEN_CACHE["value"] = token
        _TOKEN_CACHE["expires_at"] = time.time() + cache_ttl
        return _TOKEN_CACHE["value"]


def limpiar_cache_token_sabre():
    with _TOKEN_LOCK:
        _TOKEN_CACHE["value"] = ""
        _TOKEN_CACHE["expires_at"] = 0.0


def obtener_token_sabre_v1():
    # Compatibilidad con el nombre anterior.
    return obtener_token_sabre(force_refresh=True)


if __name__ == "__main__":
    try:
        fresh_token = obtener_token_sabre(force_refresh=True)
        print("Token obtenido correctamente.")
        print(fresh_token)
    except (SabreAuthError, ValueError) as error:
        print(f"Error obteniendo token: {error}")