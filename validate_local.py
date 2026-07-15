"""Validación local del conector gitlab: ejercita las 6 capacidades.

Requiere la env var RUVIC_GITLAB_ACCESS_TOKEN exportada, y un proyecto de
prueba (PROJECT_ID abajo) donde el token tenga rol Developer o superior.
Usa un proyecto propio de pruebas, no uno productivo.
"""

from ruvic_gitlab_connector import GitLabClient, setup_logging

setup_logging("INFO")
client = GitLabClient()

# Ajusta esto a un proyecto de prueba real donde el token tenga acceso
# (puede ser el Id numérico o la ruta "usuario/proyecto"):
PROJECT_ID = "tu-usuario/tu-proyecto-de-pruebas"

print("== 1. Crear un issue de prueba ==")
issue = client.create_issue(
    PROJECT_ID,
    title="[Ruvic] Issue de prueba (validate_local.py)",
    description="Este issue fue creado automáticamente para validar el conector.",
)
print(f"  {issue}")

print("== 2. Consultar issues abiertos ==")
issues = client.list_issues(PROJECT_ID, state="opened")
print(f"  {len(issues)} issue(s) abierto(s), ej.: {[i['iid'] for i in issues[:5]]}")

print("== 3. Consultar pipelines recientes ==")
pipelines = client.list_pipelines(PROJECT_ID, per_page=5)
print(f"  {len(pipelines)} pipeline(s) reciente(s)")
for p in pipelines:
    print(f"    #{p['id']}: {p['status']} ({p['ref']})")

print("== 4. Cerrar el issue de prueba ==")
cerrado = client.close_issue(PROJECT_ID, issue["iid"])
print(f"  {cerrado}")

print(
    "\nNota: comment_on_mr y get_merge_request no se ejercitan aquí por defecto, "
    "porque requieren un Merge Request real ya existente en el proyecto. "
    "Pruébalos manualmente con un MR de prueba, ej.:\n\n"
    f"  client.get_merge_request('{PROJECT_ID}', NUMERO_DE_MR)\n"
    f"  client.comment_on_mr('{PROJECT_ID}', NUMERO_DE_MR, 'Comentario de prueba')\n"
)
