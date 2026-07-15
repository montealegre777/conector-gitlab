# Conector GitLab — Qué hace cada función

Este documento explica, en lenguaje simple, qué hace cada una de las 6 funciones del conector `ruvic_gitlab_connector`.

---

## 1. `create_issue()` — Reportar algo nuevo

**¿Qué hace?** Crea un issue nuevo (un reporte de bug, una tarea, una idea) en un proyecto.

**Ejemplo:**
```python
client.create_issue("ruvic-ai/ruvic-engine", "Bug en login", description="Pasos para reproducir...")
```

**Analogía:** abrir un ticket nuevo en la lista de pendientes del proyecto.

---

## 2. `list_issues()` — Ver qué issues hay

**¿Qué hace?** Trae una lista de issues de un proyecto, filtrando por estado (abiertos/cerrados) o etiquetas.

**Ejemplo:**
```python
client.list_issues("ruvic-ai/ruvic-engine", state="opened")
```

**Analogía:** pedir la lista de pendientes del tablero, filtrada por lo que te interesa.

---

## 3. `comment_on_mr()` — Opinar sobre un cambio de código

**¿Qué hace?** Agrega un comentario a la conversación de un Merge Request (la propuesta de cambio de código en GitLab, equivalente al "Pull Request" de GitHub).

**Ejemplo:**
```python
client.comment_on_mr("ruvic-ai/ruvic-engine", 17, "Buen trabajo, aprobado")
```

**Analogía:** dejar una nota en la conversación de revisión de un cambio.

---

## 4. `get_merge_request()` — Ver el estado de un cambio de código

**¿Qué hace?** Trae los detalles de un Merge Request: si está abierto, cerrado, fusionado, o si se puede fusionar sin conflictos.

**Ejemplo:**
```python
client.get_merge_request("ruvic-ai/ruvic-engine", 17)
```

**Analogía:** consultar el estado de un trámite: en revisión, aprobado, o con problemas.

---

## 5. `list_pipelines()` — Ver si el CI/CD pasó o falló

**¿Qué hace?** Consulta las últimas ejecuciones de los pipelines automatizados de GitLab (las pruebas/despliegues automáticos).

**Ejemplo:**
```python
client.list_pipelines("ruvic-ai/ruvic-engine", ref="main")
```

**Analogía:** revisar el semáforo de estado de las pruebas automáticas: verde (éxito), rojo (falló), amarillo (en progreso).

---

## 6. `close_issue()` — Marcar algo como resuelto

**¿Qué hace?** Cierra un issue existente.

**Ejemplo:**
```python
client.close_issue("ruvic-ai/ruvic-engine", 42)
```

**Analogía:** marcar un pendiente como "listo", sin borrarlo del historial.

---

## Un detalle de GitLab que vale la pena saber: `iid` vs `id`

GitLab le da a cada issue/MR **dos números distintos**:
- `iid`: el número que ves en pantalla (ej. "!42", el que usa un humano para hablar de ese issue).
- `id`: un número interno global de GitLab, que no es el que la gente usa para referirse a las cosas.

Este conector siempre te devuelve el `iid` — el que reconoces normalmente.

---

## Fuera de alcance a propósito

Este conector **no puede**:
- Fusionar (merge) Merge Requests — requiere revisión humana.
- Eliminar proyectos o ramas — es destructivo e irreversible.
- Hacer force-push — puede sobrescribir historial de código.

Si el usuario pide alguna de estas cosas, el agente debe indicar que no está soportado en esta versión y que debe hacerse directamente en GitLab.

---

## Resumen rápido — ¿cuál función usar según lo que pida el usuario?

| El usuario pide... | Función a usar |
|---|---|
| "Reporta/crea un issue sobre X" | `create_issue()` |
| "¿Qué issues tenemos abiertos?" | `list_issues()` |
| "Comenta en el MR X" | `comment_on_mr()` |
| "¿Cómo va el MR X?" | `get_merge_request()` |
| "¿Pasó el pipeline/CI?" | `list_pipelines()` |
| "Cierra el issue X" | `close_issue()` |
| "Fusiona/borra/haz force-push..." | (no soportado — se hace directamente en GitLab) |
