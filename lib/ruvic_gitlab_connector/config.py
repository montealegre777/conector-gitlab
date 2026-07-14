"""Configuración del conector leída desde variables de entorno.

Convención de la plataforma: cada campo del formulario de configuración
llega como variable de entorno {ENV_PREFIX}{CAMPO} en mayúsculas.
Para este conector el prefijo es RUVIC_GITLAB_.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

ENV_PREFIX = "RUVIC_GITLAB_"

_DEFAULT_BASE_URL = "https://gitlab.com/api/v4"


@dataclass(frozen=True)
class GitLabConfig:
    """Parámetros de conexión a GitLab vía Personal Access Token."""

    access_token: str
    api_base_url: str = _DEFAULT_BASE_URL
    timeout: int = 20

    @classmethod
    def from_env(cls) -> "GitLabConfig":
        """Construye la configuración desde las variables RUVIC_GITLAB_*.

        Raises:
            ValueError: si falta RUVIC_GITLAB_ACCESS_TOKEN.
        """
        access_token = os.environ.get(f"{ENV_PREFIX}ACCESS_TOKEN")
        if not access_token:
            raise ValueError(
                f"Falta la variable de entorno del conector gitlab: "
                f"{ENV_PREFIX}ACCESS_TOKEN. Configura el conector en Settings → Conectores."
            )

        base_url = os.environ.get(f"{ENV_PREFIX}API_BASE_URL", "").strip() or _DEFAULT_BASE_URL

        return cls(
            access_token=access_token,
            api_base_url=base_url.rstrip("/"),
            timeout=int(os.environ.get(f"{ENV_PREFIX}REQUEST_TIMEOUT", "20")),
        )
