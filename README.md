# conector-gitlab

Conector Ruvic para GitLab: gestión de issues, comentarios en Merge Requests y consulta de pipelines (CI/CD), autenticado con un **Personal Access Token**.

## Capacidades

`create_issue`, `list_issues`, `comment_on_mr`, `get_merge_request`, `list_pipelines`, `close_issue`. No incluye fusionar MRs, eliminar proyectos/ramas, ni force-push (fuera de alcance a propósito).

## Instalación

Requiere **Python ≥ 3.10**.

```bash
pip install git+https://github.com/tu-org/conector-gitlab.git#subdirectory=lib
```

Para desarrollo local (editable, en un venv limpio):

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ./lib
```

## Variables de entorno

| Variable | Obligatoria | Descripción |
|----------|-------------|-------------|
| `RUVIC_GITLAB_ACCESS_TOKEN` | Sí | Personal Access Token de GitLab |
| `RUVIC_GITLAB_API_BASE_URL` | No | Default `https://gitlab.com/api/v4`; usar la URL de la instancia self-managed si aplica |
| `RUVIC_GITLAB_REQUEST_TIMEOUT` | No | Segundos, default `20` |

## Permisos / prerrequisitos en GitLab

1. En GitLab: **User Settings → Access Tokens**.
2. Nombre descriptivo, fecha de expiración (recomendado, aunque no siempre obligatoria según la instancia).
3. **Scopes:** marca `api` (acceso completo) o, para un enfoque más acotado, `read_api` + los scopes de repositorio que necesites.
4. El token opera con los permisos del **rol** que el usuario tenga en cada proyecto (Developer o superior, para crear issues/comentar/ver pipelines) — otorgar el scope correcto no basta si el usuario no tiene rol suficiente en el proyecto específico.
5. Genera y copia el token — GitLab solo lo muestra completo una vez.

Este conector **no soporta** fusionar Merge Requests, eliminar proyectos/ramas, ni force-push (fuera de alcance a propósito).

## Cómo correr las pruebas locales

```bash
export RUVIC_GITLAB_ACCESS_TOKEN=glpat-xxxxxxxx
python test_connection.py
python validate_local.py   # edita PROJECT_ID en el script primero
```

Prueba también el caso de error:

```bash
RUVIC_GITLAB_ACCESS_TOKEN=invalido python test_connection.py
# FALLO: Autenticación fallida: ...
```

## Límites de la API a tener en cuenta

- GitLab.com aplica rate limiting variable según el tipo de endpoint y el plan; instancias self-managed pueden tener límites configurados por el administrador.
- Un **HTTP 404** puede significar tanto "no existe" como "sin acceso" al proyecto.
- `iid` (Id visible dentro del proyecto, ej. "!42") es distinto de `id` (Id global de GitLab) — el conector siempre expone `iid`, que es el que el usuario reconoce.

## Limitaciones conocidas

- No permite fusionar (merge) Merge Requests.
- No permite eliminar proyectos ni ramas.
- No permite force-push.
- No implementa approvals formales de MR, solo comentarios simples.
- No cubre Wikis, Snippets, ni Container Registry — solo Issues, Merge Requests (lectura + comentarios) y Pipelines (solo lectura).

## Notas de integración

- El paquete pip es `ruvic-gitlab-connector`; el import name es `ruvic_gitlab_connector`.
- Única dependencia externa: `requests`.
- Ver `SKILL.md` para los ejemplos de uso que consume el agente.
