"""Prueba de conexión estándar del conector gitlab.

Firma estándar Ruvic: def test_connection() -> tuple[bool, str]
- Lee la configuración EXCLUSIVAMENTE de las env vars RUVIC_GITLAB_*.
- Nunca lanza excepciones; retorna (ok, mensaje).

Ejecutable también como script para pruebas locales:
    python test_connection.py
"""

from __future__ import annotations


def test_connection() -> tuple[bool, str]:
    """Verifica el Access Token de GitLab usando las env vars RUVIC_GITLAB_*."""
    try:
        from ruvic_gitlab_connector import (
            GitLabAuthError,
            GitLabClient,
            GitLabDataError,
            GitLabNetworkError,
        )
    except ImportError:
        return (
            False,
            "La librería ruvic-gitlab-connector no está instalada. "
            "Instala con: pip install git+https://github.com/tu-org/"
            "conector-gitlab.git#subdirectory=lib",
        )

    try:
        client = GitLabClient()  # valida que exista la env var del token
    except ValueError as exc:
        return False, str(exc)

    try:
        client.ping()
    except GitLabAuthError as exc:
        return False, f"Autenticación fallida: {exc}"
    except GitLabNetworkError as exc:
        return False, f"Error de red: {exc}"
    except GitLabDataError as exc:
        return False, f"Error de datos: {exc}"
    except Exception as exc:  # red de seguridad: jamás propagar
        return False, f"Error inesperado: {exc}"

    return True, f"Conexión exitosa a GitLab ({client.config.api_base_url})"


if __name__ == "__main__":
    ok, message = test_connection()
    print(f"{'OK' if ok else 'FALLO'}: {message}")
    raise SystemExit(0 if ok else 1)
