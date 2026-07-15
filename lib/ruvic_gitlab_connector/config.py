"""Configuración del conector leída desde variables de entorno.

Convención de la plataforma: cada campo del formulario de configuración
llega como variable de entorno {ENV_PREFIX}{CAMPO} en mayúsculas.
Para este conector el prefijo es RUVIC_GITLAB_.

Soporta dos modos de autenticación:
- "personal_access_token": token estático.
- "oauth2": OAuth 2.0 con usuario (login + consentimiento) vía una GitLab
  OAuth Application, gestionado por la plataforma vía el campo
  oauth2_authorization del manifest. Requiere CLIENT_ID, CLIENT_SECRET,
  REFRESH_TOKEN (capturado y guardado automáticamente por la plataforma).
El modo activo se detecta por la presencia de RUVIC_GITLAB_REFRESH_TOKEN.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

ENV_PREFIX = "RUVIC_GITLAB_"

_DEFAULT_BASE_URL = "https://gitlab.com/api/v4"
_DEFAULT_OAUTH_TOKEN_URL = "https://gitlab.com/oauth/token"


@dataclass(frozen=True)
class GitLabConfig:
    """Parámetros de conexión a GitLab: Personal Access Token u OAuth2."""

    auth_mode: str = "personal_access_token"  # "personal_access_token" | "oauth2"
    access_token: str = ""
    client_id: str = ""
    client_secret: str = ""
    refresh_token: str = ""
    oauth_token_url: str = _DEFAULT_OAUTH_TOKEN_URL
    api_base_url: str = _DEFAULT_BASE_URL
    timeout: int = 20

    @classmethod
    def from_env(cls) -> "GitLabConfig":
        """Construye la configuración desde las variables RUVIC_GITLAB_*.

        Detecta automáticamente el modo: si existe RUVIC_GITLAB_REFRESH_TOKEN,
        usa OAuth2; si no, exige RUVIC_GITLAB_ACCESS_TOKEN (PAT).

        Raises:
            ValueError: si faltan las variables obligatorias del modo detectado.
        """
        refresh_token = os.environ.get(f"{ENV_PREFIX}REFRESH_TOKEN", "").strip()
        base_url = os.environ.get(f"{ENV_PREFIX}API_BASE_URL", "").strip() or _DEFAULT_BASE_URL
        timeout = int(os.environ.get(f"{ENV_PREFIX}REQUEST_TIMEOUT", "20"))

        if refresh_token:
            client_id = os.environ.get(f"{ENV_PREFIX}CLIENT_ID", "")
            client_secret = os.environ.get(f"{ENV_PREFIX}CLIENT_SECRET", "")
            if not client_id or not client_secret:
                raise ValueError(
                    f"El modo OAuth2 requiere {ENV_PREFIX}CLIENT_ID y "
                    f"{ENV_PREFIX}CLIENT_SECRET además de {ENV_PREFIX}REFRESH_TOKEN."
                )
            # El endpoint de token OAuth vive en el mismo host que la API
            # (ej. https://gitlab.com/oauth/token para https://gitlab.com/api/v4).
            oauth_base = base_url.rstrip("/").removesuffix("/api/v4")
            return cls(
                auth_mode="oauth2",
                client_id=client_id,
                client_secret=client_secret,
                refresh_token=refresh_token,
                oauth_token_url=f"{oauth_base}/oauth/token",
                api_base_url=base_url.rstrip("/"),
                timeout=timeout,
            )

        access_token = os.environ.get(f"{ENV_PREFIX}ACCESS_TOKEN")
        if not access_token:
            raise ValueError(
                f"Falta la variable de entorno del conector gitlab: "
                f"{ENV_PREFIX}ACCESS_TOKEN. Configura el conector en Settings → Conectores."
            )

        return cls(
            auth_mode="personal_access_token",
            access_token=access_token,
            api_base_url=base_url.rstrip("/"),
            timeout=timeout,
        )

