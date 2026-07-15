"""Excepciones propias del conector GitLab.

Separan los tres tipos de fallo que el usuario debe distinguir:
autenticación, red y datos/permisos (incluye rate limit).
"""


class GitLabConnectorError(Exception):
    """Error base del conector."""


class GitLabAuthError(GitLabConnectorError):
    """Token inválido, expirado, revocado, o sin el scope necesario para
    la operación o el proyecto solicitado."""


class GitLabNetworkError(GitLabConnectorError):
    """No se pudo alcanzar la API de GitLab (DNS, timeout, TLS, red)."""


class GitLabDataError(GitLabConnectorError):
    """La operación es válida pero el recurso no existe, los datos
    enviados no cumplen las reglas de GitLab, o se alcanzó el límite de
    peticiones (rate limit)."""
