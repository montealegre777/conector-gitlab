---
name: gitlab
description: Usa la librería ruvic_gitlab_connector para gestionar proyectos de GitLab - crear issues (create_issue), consultar/filtrar issues (list_issues), comentar en Merge Requests (comment_on_mr), consultar el detalle de un MR (get_merge_request), revisar el estado de pipelines de CI/CD (list_pipelines), y cerrar issues (close_issue). Úsala cuando el usuario pida crear, buscar o cerrar issues, comentar o revisar Merge Requests, o consultar el estado de un pipeline/CI en GitLab. NO permite fusionar Merge Requests, eliminar proyectos/ramas, ni force-push.
triggers:
- gitlab
- issue gitlab
- merge request
- mr
- pipeline
- ci/cd gitlab
---

# Conector GitLab (ruvic_gitlab_connector)

Librería Python para gestionar issues, comentarios en Merge Requests y consultar pipelines en GitLab, autenticada con un **Personal Access Token**. Está **preinstalada en el runtime** cuando el conector está configurado (si no, instálala con `pip install git+https://github.com/tu-org/conector-gitlab.git#subdirectory=lib`).

## Regla crítica de credenciales

El código generado **NUNCA hardcodea credenciales**. Siempre se leen de variables de entorno, disponibles cuando el conector `gitlab` está configurado:

| Variable | Contenido |
|----------|-----------|
| `RUVIC_GITLAB_ACCESS_TOKEN` | Personal Access Token |
| `RUVIC_GITLAB_API_BASE_URL` | (opcional) default `https://gitlab.com/api/v4`; usar la URL de la instancia self-managed si aplica |
| `RUVIC_GITLAB_REQUEST_TIMEOUT` | (opcional) segundos, default `20` |

Si estas variables NO existen, el conector no está configurado: no generes código que lo use; indica al usuario que lo configure en **Settings → Conectores**.

## Conexión (siempre igual)

```python
from ruvic_gitlab_connector import GitLabClient

client = GitLabClient()  # lee RUVIC_GITLAB_* del entorno automáticamente
```

El conector soporta dos formas de autenticación configuradas por el admin (transparente para el código que generes): **Personal Access Token** (estático) u **OAuth2 con usuario** (el admin autorizó desde Settings → Conectores; la librería renueva el access token automáticamente cada ~2 horas usando el refresh token). No necesitas saber cuál de los dos está activo.

## Sobre `project_id`

GitLab identifica proyectos por Id numérico **o** por su ruta completa "grupo/subgrupo/proyecto". Este conector acepta ambos formatos indistintamente:

```python
client.list_issues(12345678)                          # por Id numérico
client.list_issues("ruvic-ai/ruvic-engine")            # por ruta
```

## Capacidad 1 — Crear un issue

```python
resultado = client.create_issue(
    "ruvic-ai/ruvic-engine",
    title="Bug en el login con Google",
    description="Pasos para reproducir:\n1. ...",
    labels=["bug"],
)
print(resultado)  # {'iid': 42, 'web_url': '...', ...}
```

`labels` deben existir ya en el proyecto — GitLab los crea automáticamente si no existen (a diferencia de GitHub), pero es mejor confirmar con el usuario antes de inventar labels nuevos.

## Capacidad 2 — Consultar/filtrar issues

```python
issues = client.list_issues("ruvic-ai/ruvic-engine", state="opened")
for i in issues:
    print(f"!{i['iid']}: {i['title']}")
```

## Capacidad 3 — Comentar en un Merge Request

```python
client.comment_on_mr("ruvic-ai/ruvic-engine", 17, "Buen trabajo, aprobado ✅")
```

## Capacidad 4 — Consultar el detalle de un MR

```python
mr = client.get_merge_request("ruvic-ai/ruvic-engine", 17)
print(mr["state"], mr["merge_status"])
```

## Capacidad 5 — Consultar el estado de pipelines (CI/CD)

```python
pipelines = client.list_pipelines("ruvic-ai/ruvic-engine", ref="main")
for p in pipelines:
    print(f"Pipeline {p['id']}: {p['status']}")
```

## Capacidad 6 — Cerrar un issue

```python
client.close_issue("ruvic-ai/ruvic-engine", 42)
```

## Fuera de alcance — NO intentes hacer esto

Este conector **no tiene métodos** para:
- Fusionar (merge) Merge Requests
- Eliminar proyectos o ramas
- Hacer force-push
- Aprobar/rechazar MRs formalmente (approvals)
- Modificar configuración del proyecto (webhooks, variables de CI, etc.)

Si el usuario pide algo de esto, informa que esta versión del conector no lo soporta y que debe hacerse directamente en GitLab.

## Manejo de errores

```python
from ruvic_gitlab_connector import GitLabAuthError, GitLabDataError, GitLabNetworkError

try:
    client.create_issue("ruvic-ai/ruvic-engine", "Título")
except GitLabAuthError:
    print("Token inválido o sin permiso sobre el proyecto — revisa la configuración del conector")
except GitLabNetworkError:
    print("No se pudo alcanzar GitLab — revisa la red")
except GitLabDataError as e:
    print(f"Error de datos: {e}")  # ej. proyecto no existe/sin acceso, rate limit
```

## Buenas prácticas al generar código

1. Lee credenciales SOLO de las variables `RUVIC_GITLAB_*` (el constructor de `GitLabClient` ya lo hace).
2. Nunca imprimas `RUVIC_GITLAB_ACCESS_TOKEN` en logs ni en la salida.
3. No intentes fusionar MRs, eliminar proyectos/ramas, ni hacer force-push: este conector no lo soporta a propósito.
4. Distingue entre `iid` (Id visible dentro del proyecto, el que ve el usuario, ej. "!42") y `id` (Id global de GitLab) — casi siempre quieres usar `iid` al hablar con el usuario.
5. Un HTTP 404 puede significar "no existe" O "no tienes acceso" — no asumas automáticamente que el recurso no existe.
6. El rate limit de la API varía según el plan de GitLab (gitlab.com vs self-managed) — evita loops innecesarios de `list_pipelines`/`list_issues`.
