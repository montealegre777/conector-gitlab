"""Cliente para gestionar issues, comentarios en Merge Requests y consultar
pipelines en GitLab.

Capacidades:
- create_issue():        crear un issue nuevo.
- list_issues():         consultar/filtrar issues de un proyecto.
- comment_on_mr():       comentar en un Merge Request.
- get_merge_request():   consultar el detalle de un MR.
- list_pipelines():      consultar el estado de ejecuciones de CI/CD (pipelines).
- close_issue():         cerrar un issue.

Fuera de alcance a propósito: fusionar Merge Requests, eliminar
proyectos o ramas, force-push, o cualquier operación destructiva/
irreversible — este cliente simplemente no expone esos métodos.

Autenticación: Personal Access Token de GitLab, enviado en el header
PRIVATE-TOKEN (el método recomendado por GitLab sobre Authorization:
Bearer). Las credenciales SIEMPRE provienen de variables de entorno
RUVIC_GITLAB_* (ver config.GitLabConfig.from_env). Prohibido hardcodearlas.

Nota sobre project_id: la API de GitLab acepta tanto el Id numérico de
un proyecto como su "ruta" (namespace/proyecto) URL-codificada. Este
cliente acepta ambos formatos y codifica automáticamente cuando hace
falta.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

import requests
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import RequestException, Timeout

from .config import GitLabConfig
from .exceptions import GitLabAuthError, GitLabDataError, GitLabNetworkError
from .logging_utils import get_logger


def _encode_project_id(project_id: str | int) -> str:
    """Codifica el project_id para usarlo en la URL (soporta Id numérico
    o ruta tipo 'grupo/proyecto')."""
    return quote(str(project_id), safe="")


class GitLabClient:
    """Cliente de GitLab autenticado con un Personal Access Token.

    Args:
        config: configuración de conexión. Si se omite, se lee de las
            variables de entorno RUVIC_GITLAB_* (comportamiento estándar
            en el runtime de la plataforma).

    Ejemplo:
        >>> client = GitLabClient()  # lee RUVIC_GITLAB_* del entorno
        >>> client.list_issues("mi-grupo/mi-proyecto", state="opened")
        [{'iid': 42, 'title': '...', ...}, ...]
    """

    def __init__(self, config: GitLabConfig | None = None) -> None:
        self.config = config or GitLabConfig.from_env()
        self._logger = get_logger()

    # ------------------------------------------------------------------ #
    # Peticiones HTTP
    # ------------------------------------------------------------------ #

    def _request(self, method: str, path: str, **kwargs: Any) -> requests.Response:
        url = f"{self.config.api_base_url}{path}"
        headers = kwargs.pop("headers", {})
        headers["PRIVATE-TOKEN"] = self.config.access_token
        try:
            return requests.request(
                method, url, headers=headers, timeout=self.config.timeout, **kwargs
            )
        except Timeout as exc:
            raise GitLabNetworkError(
                f"Tiempo de espera agotado ({self.config.timeout}s) llamando a "
                f"la API de GitLab ({path})."
            ) from exc
        except RequestsConnectionError as exc:
            raise GitLabNetworkError(
                f"No se pudo conectar a {self.config.api_base_url}. Verifica la "
                "conectividad de red."
            ) from exc
        except RequestException as exc:
            raise GitLabNetworkError(f"Error de red: {exc}") from exc

    def _raise_for_error(self, resp: requests.Response, context: str) -> None:
        try:
            payload = resp.json()
        except ValueError:
            payload = {}
        message = payload.get("message") or payload.get("error") or resp.text[:300] or "Error desconocido"
        if isinstance(message, (list, dict)):
            message = str(message)[:300]

        if resp.status_code == 401:
            raise GitLabAuthError(
                f"Autenticación fallida en {context}: {message}. Revisa que el "
                "token sea correcto y no haya expirado o sido revocado."
            )
        if resp.status_code == 403:
            raise GitLabAuthError(
                f"Permisos insuficientes en {context}: {message}. El token necesita "
                "el scope y/o rol correspondiente sobre este proyecto."
            )
        if resp.status_code == 429:
            raise GitLabDataError(
                f"Se alcanzó el límite de peticiones a la API de GitLab en {context}. "
                "Reintenta en unos segundos."
            )
        if resp.status_code == 404:
            raise GitLabDataError(
                f"No encontrado en {context}: {message}. Puede ser que el recurso no "
                "exista, o que el token no tenga acceso a él."
            )
        if resp.status_code in (400, 422):
            raise GitLabDataError(f"Solicitud inválida en {context}: {message}")
        raise GitLabDataError(
            f"Error de GitLab en {context} (HTTP {resp.status_code}): {message}"
        )

    # ------------------------------------------------------------------ #
    # Ping / prueba de conexión
    # ------------------------------------------------------------------ #

    def ping(self) -> bool:
        """Verifica el token consultando el usuario autenticado (barato,
        no requiere acceso a ningún proyecto específico)."""
        resp = self._request("GET", "/user")
        if resp.status_code != 200:
            self._raise_for_error(resp, "ping")
        self._logger.info("Ping exitoso a GitLab")
        return True

    # ------------------------------------------------------------------ #
    # Capacidad 1: crear un issue
    # ------------------------------------------------------------------ #

    def create_issue(
        self,
        project_id: str | int,
        title: str,
        description: str | None = None,
        labels: list[str] | None = None,
        assignee_ids: list[int] | None = None,
    ) -> dict[str, Any]:
        """Crea un issue nuevo en un proyecto.

        Args:
            project_id: Id numérico del proyecto, o su ruta "grupo/proyecto".
            title: título del issue.
            description: descripción (opcional, admite Markdown).
            labels: lista de labels a asignar (deben existir ya en el proyecto).
            assignee_ids: lista de Ids de usuario a asignar.

        Returns:
            Dict con "iid" (Id visible del issue dentro del proyecto),
            "web_url", "id" (Id global), "state".

        Ejemplo:
            >>> client.create_issue("ruvic-ai/ruvic-engine", "Bug en login", description="...")
            {'iid': 42, 'web_url': 'https://gitlab.com/...', 'id': ..., 'state': 'opened'}
        """
        if not title or not title.strip():
            raise GitLabDataError("El título del issue no puede estar vacío.")

        payload: dict[str, Any] = {"title": title.strip()}
        if description:
            payload["description"] = description
        if labels:
            payload["labels"] = ",".join(labels)
        if assignee_ids:
            payload["assignee_ids"] = assignee_ids

        pid = _encode_project_id(project_id)
        resp = self._request("POST", f"/projects/{pid}/issues", json=payload)
        if resp.status_code != 201:
            self._raise_for_error(resp, f"create_issue {project_id}")

        data = resp.json()
        self._logger.info("Issue creado en %s: !%s", project_id, data.get("iid"))
        return {
            "iid": data.get("iid"),
            "web_url": data.get("web_url"),
            "id": data.get("id"),
            "state": data.get("state"),
        }

    # ------------------------------------------------------------------ #
    # Capacidad 2: consultar/filtrar issues
    # ------------------------------------------------------------------ #

    def list_issues(
        self,
        project_id: str | int,
        state: str = "opened",
        labels: list[str] | None = None,
        per_page: int = 30,
    ) -> list[dict[str, Any]]:
        """Lista issues de un proyecto, con filtros básicos.

        Args:
            project_id: Id numérico del proyecto, o su ruta "grupo/proyecto".
            state: "opened", "closed" o "all" (default "opened").
            labels: lista de labels para filtrar (opcional).
            per_page: máximo de resultados (default 30, máximo 100).

        Returns:
            Lista de dicts con "iid", "title", "state", "web_url", "labels".

        Ejemplo:
            >>> client.list_issues("ruvic-ai/ruvic-engine", state="opened")
            [{'iid': 42, 'title': 'Bug en login', ...}, ...]
        """
        params: dict[str, Any] = {
            "state": state,
            "per_page": max(1, min(int(per_page), 100)),
        }
        if labels:
            params["labels"] = ",".join(labels)

        pid = _encode_project_id(project_id)
        resp = self._request("GET", f"/projects/{pid}/issues", params=params)
        if resp.status_code != 200:
            self._raise_for_error(resp, f"list_issues {project_id}")

        cleaned = [
            {
                "iid": i.get("iid"),
                "title": i.get("title"),
                "state": i.get("state"),
                "web_url": i.get("web_url"),
                "labels": i.get("labels", []),
            }
            for i in resp.json()
        ]
        self._logger.info("list_issues %s: %d issue(s)", project_id, len(cleaned))
        return cleaned

    # ------------------------------------------------------------------ #
    # Capacidad 3: comentar en un Merge Request
    # ------------------------------------------------------------------ #

    def comment_on_mr(
        self, project_id: str | int, mr_iid: int, body: str
    ) -> dict[str, Any]:
        """Agrega un comentario (nota) a un Merge Request.

        Args:
            project_id: Id numérico del proyecto, o su ruta "grupo/proyecto".
            mr_iid: Id visible del Merge Request dentro del proyecto (iid).
            body: texto del comentario (admite Markdown).

        Returns:
            Dict con "id", "body".

        Ejemplo:
            >>> client.comment_on_mr("ruvic-ai/ruvic-engine", 17, "LGTM, buen trabajo")
            {'id': ..., 'body': 'LGTM, buen trabajo'}
        """
        if not body or not body.strip():
            raise GitLabDataError("El comentario no puede estar vacío.")

        pid = _encode_project_id(project_id)
        resp = self._request(
            "POST",
            f"/projects/{pid}/merge_requests/{mr_iid}/notes",
            json={"body": body},
        )
        if resp.status_code != 201:
            self._raise_for_error(resp, f"comment_on_mr {project_id}!{mr_iid}")

        data = resp.json()
        self._logger.info("Comentario agregado en MR %s!%s", project_id, mr_iid)
        return {"id": data.get("id"), "body": data.get("body")}

    # ------------------------------------------------------------------ #
    # Capacidad 4: consultar el detalle de un Merge Request
    # ------------------------------------------------------------------ #

    def get_merge_request(self, project_id: str | int, mr_iid: int) -> dict[str, Any]:
        """Obtiene el detalle de un Merge Request.

        Args:
            project_id: Id numérico del proyecto, o su ruta "grupo/proyecto".
            mr_iid: Id visible del Merge Request dentro del proyecto (iid).

        Returns:
            Dict con "iid", "title", "state", "merge_status", "web_url",
            "source_branch", "target_branch".

        Ejemplo:
            >>> client.get_merge_request("ruvic-ai/ruvic-engine", 17)
            {'iid': 17, 'title': '...', 'state': 'opened', ...}
        """
        pid = _encode_project_id(project_id)
        resp = self._request("GET", f"/projects/{pid}/merge_requests/{mr_iid}")
        if resp.status_code != 200:
            self._raise_for_error(resp, f"get_merge_request {project_id}!{mr_iid}")

        data = resp.json()
        return {
            "iid": data.get("iid"),
            "title": data.get("title"),
            "state": data.get("state"),
            "merge_status": data.get("detailed_merge_status") or data.get("merge_status"),
            "web_url": data.get("web_url"),
            "source_branch": data.get("source_branch"),
            "target_branch": data.get("target_branch"),
        }

    # ------------------------------------------------------------------ #
    # Capacidad 5: consultar el estado de pipelines (CI/CD)
    # ------------------------------------------------------------------ #

    def list_pipelines(
        self,
        project_id: str | int,
        ref: str | None = None,
        status: str | None = None,
        per_page: int = 10,
    ) -> list[dict[str, Any]]:
        """Consulta el estado de los pipelines (CI/CD) más recientes.

        Args:
            project_id: Id numérico del proyecto, o su ruta "grupo/proyecto".
            ref: filtrar por rama/tag (opcional).
            status: filtrar por estado (ej. "success", "failed", "running").
            per_page: máximo de resultados (default 10, máximo 100).

        Returns:
            Lista de dicts con "id", "status", "ref", "web_url", "created_at".

        Ejemplo:
            >>> client.list_pipelines("ruvic-ai/ruvic-engine", ref="main")
            [{'id': ..., 'status': 'success', ...}, ...]
        """
        params: dict[str, Any] = {"per_page": max(1, min(int(per_page), 100))}
        if ref:
            params["ref"] = ref
        if status:
            params["status"] = status

        pid = _encode_project_id(project_id)
        resp = self._request("GET", f"/projects/{pid}/pipelines", params=params)
        if resp.status_code != 200:
            self._raise_for_error(resp, f"list_pipelines {project_id}")

        cleaned = [
            {
                "id": p.get("id"),
                "status": p.get("status"),
                "ref": p.get("ref"),
                "web_url": p.get("web_url"),
                "created_at": p.get("created_at"),
            }
            for p in resp.json()
        ]
        self._logger.info("list_pipelines %s: %d pipeline(s)", project_id, len(cleaned))
        return cleaned

    # ------------------------------------------------------------------ #
    # Capacidad 6: cerrar un issue
    # ------------------------------------------------------------------ #

    def close_issue(self, project_id: str | int, issue_iid: int) -> dict[str, Any]:
        """Cierra un issue existente.

        Args:
            project_id: Id numérico del proyecto, o su ruta "grupo/proyecto".
            issue_iid: Id visible del issue dentro del proyecto (iid).

        Returns:
            Dict con "iid" y "state".

        Ejemplo:
            >>> client.close_issue("ruvic-ai/ruvic-engine", 42)
            {'iid': 42, 'state': 'closed'}
        """
        pid = _encode_project_id(project_id)
        resp = self._request(
            "PUT", f"/projects/{pid}/issues/{issue_iid}", json={"state_event": "close"}
        )
        if resp.status_code != 200:
            self._raise_for_error(resp, f"close_issue {project_id}!{issue_iid}")

        data = resp.json()
        self._logger.info("Issue cerrado en %s: !%s", project_id, issue_iid)
        return {"iid": data.get("iid"), "state": data.get("state")}
