# Agenda VTA – Copilot Instructions

## Architecture Snapshot
- Flask entrypoint lives in [backend/app.py](backend/app.py); all page routes, REST APIs, and PDF exports sit in the monolithic [backend/routes.py](backend/routes.py), so new endpoints should extend that file and reuse the existing helpers instead of creating new blueprints.
- Runtime persistence is SQLite (`agenda.db`) via the `sqlite3` helpers declared at the top of [backend/routes.py](backend/routes.py); Postgres scripts under [backend/setup_db.py](backend/setup_db.py) are legacy and should only be touched if the team confirms a future migration.
- Templates under [backend/templates](backend/templates) are rendered server-side; each screen (login, dashboard, agenda, etc.) is a standalone HTML file with inline CSS/JS, so align with the conventions shown in [backend/templates/2.%20dashboard_vta.html](backend/templates/2.%20dashboard_vta.html) and [backend/templates/6.%20pets_vta.html](backend/templates/6.%20pets_vta.html) when designing new views.
- Shared front-end behavior (sidebar nav, logout, session glue) is centralized in [backend/static/assets/js/vta-nav.js](backend/static/assets/js/vta-nav.js); page-specific logic (e.g., dashboard counters) stays in scripts that live next to each template.
- Reporting relies on ReportLab; see `gerar_relatorio_agendamentos_pdf()` and `gerar_relatorio_dashboard_pdf()` inside [backend/routes.py](backend/routes.py) for examples that stream PDFs using the clinic logo stored in [backend/static/img/logo.png](backend/static/img/logo.png).

## Running & Environment
- Use the bundled venv and run `source backend/venv/bin/activate && python backend/app.py`; the server expects a `.env` with `SECRET_KEY` (defaults to a dev-safe value if absent).
- Database bootstrap for SQLite happens through the helper scripts: run `python backend/setup_sqlite.py` first, then the table-specific scripts such as [backend/setup_clientes_table.py](backend/setup_clientes_table.py), [backend/setup_pets_table.py](backend/setup_pets_table.py), [backend/setup_salas_table.py](backend/setup_salas_table.py), and [backend/create_notifications_table.py](backend/create_notifications_table.py) whenever you need a clean slate.
- Hot reloading comes from `app.run(debug=True)`; there is no task runner, so any asset compilation or linting must be invoked manually.
- Sample admin credentials are seeded by [backend/setup_sqlite.py](backend/setup_sqlite.py) (`admin@vta.com` / `admin123`). When adding auth features, ensure routes continue to guard on `session['user_id']` exactly as shown in existing handlers.

## Backend Patterns & APIs
- Always acquire database connections through `get_db_connection()` and make sure to `conn.close()` in a `finally` block—copy the structure used in each API route of [backend/routes.py](backend/routes.py) to stay consistent.
- Before reading agenda data, call `update_appointment_statuses(conn)` to keep `status` in sync; both `/dashboard` and `/api/dashboard/stats` follow this pattern and your new endpoints should as well.
- CRUD endpoints usually emit JSON with `{ "success": True }` or `{ "message": "..." }`; match the response schema used by `/api/agendamentos`, `/api/pets`, `/api/clientes`, and `/api/usuarios` to avoid breaking the existing fetch calls in the templates.
- Notifications are simple rows in the `notificacoes` table; when mutating appointments, append a new record so the dashboard widget renders the latest events (see `create_agendamento` and `update_agendamento`).
- PDF exports pull all rows ordered by date/time; if you add new filters, propagate them both to the SQL query and to the string formatting used while writing each line to the canvas to keep the report usable.

## Frontend Conventions
- Every template duplicates the dashboard chrome (header, sidebar, quick actions). When touching a page like [backend/templates/4.%20agendamento_vta.html](backend/templates/4.%20agendamento_vta.html), mirror the spacing, palette variables, and card styles defined inline in [backend/templates/6.%20pets_vta.html](backend/templates/6.%20pets_vta.html) so the app keeps a cohesive visual identity.
- Data grids are plain `<table>` elements populated via JavaScript; for example, the pets screen renders rows in `renderizarTabela()` and the agendamentos page fills `#agendamentosTableBody` after calling `/api/agendamentos`. Follow the same pattern (fetch → store array → render) for new modules to plug into the existing filtering/pagination helpers.
- Client-side filtering relies on IDs like `searchInput`, `statusFilter`, and `dataInicio`; if you rename inputs, update the listeners in the accompanying `<script>` block or the filters will silently stop working.
- Navigation highlights (`.nav-link.active`) are toggled manually both in the template and within [backend/static/assets/js/vta-nav.js](backend/static/assets/js/vta-nav.js); keep that class in sync when adding links so the sidebar state remains accurate.

## Data & Tooling Notes
- SQLite schema: `agendamentos`, `clientes`, `pets`, `salas`, `usuarios`, and `notificacoes`. Foreign keys are minimal, so enforce integrity in code (e.g., a pet stores `tutor_id` but deletions do not cascade—double-check usage before deleting records).
- The codebase mixes legacy Postgres helpers with the active SQLite flow. When writing migrations or maintenance scripts, prefer the SQLite versions unless the team explicitly requests Postgres compatibility.
- ReportLab and jsPDF are both in use (server-side PDFs vs. client-side exports). Decide which path to follow based on where the button lives: template exports (like the pets table) lean on jsPDF, while routes behind `/relatorios/...` use ReportLab.
- Shared UI assets live under [backend/static/assets](backend/static/assets); add new CSS or JS there when multiple templates will consume it instead of stuffing everything into each HTML file.

_Feedback welcome: if any workflow or convention above is unclear or incomplete, let me know so we can refine this guide._
