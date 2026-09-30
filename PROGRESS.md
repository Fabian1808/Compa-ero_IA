# AI WORKMATE — Progreso del Sprint (commit 75e87b2)

## Resumen ejecutivo
Versión **web-first** de AI WORKMATE. Migrado el 90 % de las páginas de usuario al catálogo i18n (417 claves, paridad es-PE/en-US). Correcciones de autorización tenant, helper `enumLabel` para mapeo snake_case → camelCase, build y tests verdes.

---

## ✅ Completado (commit 75e87b2)

### i18n – Páginas de usuario migradas
| Página | Claves añadidas | Estado |
|--------|----------------|--------|
| `SettingsPage` | `sections.*`, `fields.*`, `themes.*`, `languages.*`, `notifications.*`, `data.*`, `ai.*`, `danger.*`, `account.*`, `states.*` | ✅ completa + selector idioma cableado |
| `CommitmentsPage` | `edit`, `created`, `overdue`, `statuses.*`, `deleteConfirm` | ✅ completa (enumLabel en badges) |
| `FollowupsPage` | `detect`, `statuses.*` (reminderSent, draftPrepared) | ✅ completa (enumLabel) |
| `WorkMapPage` | `tabs.*`, `cards.*`, `sublabels.*` (plurales), `dueOn`, `dueInDays`, `noDate`, `overdueBadge`, `tomorrowBadge`, `inDaysBadge`, `minutes`, `hours`, `progress`, `noProjects`, `noTasks`, `noBottlenecks`, `refresh`, `blockingTask`, `nextCritical`, `nextDeadlines`, `upcomingMeetings`, `projectProgress`, `online` | ✅ completa (helpers con `t` prop, enumLabel) |
| `FocusPage` | `title`, `subtitle`, `empty`, `emptyHint`, `resume`, `pause`, `stop`, `overtime`, `notes`, `markCompleted`, `back` | ✅ |
| `AuthPage` | `title`, `subtitle`, `connect`, `copy`, `success`, `failure`, `retry`, `expiresIn` | ✅ (fix "AI Workmate" → catálogo) |
| `DeadlinesPage` | `title`, `subtitle`, `empty`, `overdue`, `next24h`, `thisWeek`, `all30d` | ✅ (helpers `DeadlinesList`/`DeadlineItem` con `t` prop) |
| `TasksPage` | `title`, `subtitle`, `empty`, `emptyHint`, `new`, `filter`, `statusFilters.*`, `priorityFilters.*`, `projectFilters.*`, `noProject` | ✅ (re-restaurada tras corrupción UTF-8) |
| `ProjectsPage` | `title`, `subtitle`, `new`, `empty`, `emptyHint`, `createFirst`, `fields.*`, `actions.*` | ✅ (script `spec-projects.json` aplicado) |
| `HomePage` | `whatNow`, `startTask`, `newTask`, `newProject`, `quickActions`, `askAi`, `askPlaceholder`, `aiRecommendation`, `sync`, `dismiss` | ✅ |

**Total claves catálogo:** 417 (paridad exacta es-PE/en-US, verificado runtime con plurales 0/1/2/10/21).

### Helper `enumLabel.ts`
- Convierte automáticamente `snake_case` de la API (`in_progress`, `on_hold`) a `camelCase` del catálogo (`inProgress`, `onHold`).
- Usado en `WorkMapPage`, `CommitmentsPage`, `FollowupsPage`, `TasksPage` para estados, prioridades, urgencias, projectStates, followups.statuses, commitments.statuses.
- Exporta `TFunction` desde `types.ts` sin arrastrar JSX.

### Arquitectura i18n
- `types.ts`: `TFunction`, `TranslateOptions`, `Catalog`, `MessageValue`, `PluralMessage`, `SupportedLocale` (sin JSX).
- `I18nProvider.tsx` re-exporta `TFunction` y define `I18nContextValue`.
- `lookup()` en `i18n.ts` recorre catálogos anidados correctamente.
- Scripts de migración (`migrate-i18n.mjs`) toleran BOM UTF-8 y CRLF; no usan PowerShell `Set-Content` (corrompe acentos).

### Autorización / Auth (backend)
- `require_tenant_admin` en `middleware.py`: consulta `TenantUser`, exige membership activa + rol `owner`/`admin`, 401/403.
- Constantes canónicas `TENANT_ROLES`, `TENANT_ADMIN_ROLES` en `models.py`.
- `admin/api.py` usa la dependencia real (antes stub roto con `request.state.get()`).
- `GET /api/v1/auth/me` implementado (transitional: primer usuario local, `X-Tenant-ID` o membership más antiguo por `invited_at`).
- Frontend `useAuth` llama a `/auth/me`; `authStore` persiste `role`, `tenantId`, `isAdmin`.
- `AdminRoute` y `Sidebar` muestran admin solo si `isAdmin`.

### Tests & Build
- **Backend:** 38 passed (9 nuevos `test_tenant_authorization.py`), 7 warnings (Pydantic config deprecation).
- **Frontend:** `tsc --noEmit` 0 errores; `npm run build` 538.60 kB / 7.41 s.

### Limpieza técnica
- Eliminado `useSystemTray.ts` (277 líneas, APIs Tauri inexistentes).
- Confirmado `tauri/` sin código Rust → desktop no compilable (decisión usuario: web-first).

---

## 🚧 Próximos pasos (prioridad)

| # | Tarea | Detalle |
|---|-------|---------|
| 1 | **Migrar páginas admin** | `AdminDashboardPage`, `AdminMetricsPage`, `AdminTenantsPage`, `AdminUsersPage`, `AdminAuditLogsPage`, `AdminSettingsPage`, `AdminSecurityPage` (≈200 strings hardcodeadas). Dejar para después de user-facing. |
| 2 | **Corregir `FirstRunInstallerPage` polling duplicado** | `startInstallation()` + `useEffect` por cambio de step inician dos loops. Unificar en un solo efecto. |
| 3 | **Resolver `/auth/status` hardcoded `false`** | Hoy siempre `authenticated: false`. `completeLogin()` no carga sesión; solo `setAuthenticated(true)`. `useAuth` llama a `/auth/me` si hay token, pero flujo login real no probado. |
| 4 | **Seguridad tokens en `localStorage`** | `access_token`/`refresh_token` Microsoft Graph guardados en `localStorage` (riesgo XSS). Evaluar httpOnly cookies o secure storage. |
| 5 | **Migración datos legacy** | `./data/ai-workmate.db` → nuevo storage `%LOCALAPPDATA%\AIWorkmate\`. Script pendiente. |
| 6 | **Lint repo-wide** | 1 748 warnings (mayoría B008 FastAPI `Depends`, E501 líneas largas). Configurar ignores justificados en `pyproject.toml`. |
| 7 | **Pruebas OAuth / modelos reales** | 14/14 pruebas contrato pendientes (credenciales/binarios reales). |
| 8 | **Documentación** | `PHASES.md`, `README.md` actualizar con estado actual. |
| 9 | **OLLAMA_INSTALLER_SHA256** | Vacío → instalación automática Ollama deshabilitada. Definir hash o documentar. |

---

## ❌ Fallas / Deuda técnica conocida

| Área | Descripción | Severidad |
|------|-------------|-----------|
| **Auth transitional** | `get_current_user_id` toma primer usuario; no hay validación JWT/session real. `/auth/status` siempre `false`. | Alta (bloquea multi-usuario real) |
| **Tokens en localStorage** | Microsoft Graph tokens expuestos a XSS. | Alta (seguridad) |
| **Polling duplicado FirstRun** | Dos `setInterval` concurrentes al instalar. | Media (UX/instalador) |
| **`require_tenant_admin` lanza 500 si tenant no existe** | En `get_current_tenant` → `Exception` genérica. Middleware atrapa y devuelve 404, pero dependencia directa podría fallar. | Media |
| **`enumLabel` fallback devuelve raw snake_case** | Si catálogo falta, muestra `in_progress` en vez de `En curso`. Acceptable como señal visible. | Baja |
| **`zero` plural en en-US no usado** | CLDR inglés no tiene forma `zero` para enteros; 0 usa `other`. Comportamiento correcto. | Info |
| **Scripts de migración en repo** | `frontend/scripts/*.json/.mjs` son herramienta temporal. Podrían moverse a `tools/` o eliminarse tras uso. | Baja |
| **package.json incluye Tauri** | `@tauri-apps/api@^2`, `@tauri-apps/cli@^2` instalados pero desktop pospuesto. No rompen web. | Info |

---

## 📁 Archivos clave tocados (no exhaustivo)

**Backend**
- `backend/app/api/v1/auth.py` – `/auth/me`, `/login`, `/callback`
- `backend/app/multi_tenancy/middleware.py` – `require_tenant_admin`, `get_current_tenant`
- `backend/app/multi_tenancy/models.py` – `TENANT_ROLES`, `TENANT_ADMIN_ROLES`, `TenantUser.invited_at`
- `backend/app/admin/api.py` – admin routes protegidas
- `backend/tests/unit/test_tenant_authorization.py` – 9 tests

**Frontend i18n**
- `frontend/src/i18n/locales/es-PE.ts` / `en-US.ts` – 417 claves
- `frontend/src/i18n/I18nProvider.tsx` – `lookup` fix, re-export types
- `frontend/src/i18n/types.ts` – `TFunction` sin JSX
- `frontend/src/i18n/enumLabel.ts` – helper snake_case→camelCase
- `frontend/scripts/migrate-i18n.mjs` – migración segura UTF-8
- `frontend/scripts/check-parity.mjs` / `check-runtime.mjs` – validación CI

**Páginas migradas (ejemplos)**
- `SettingsPage.tsx`, `CommitmentsPage.tsx`, `FollowupsPage.tsx`, `WorkMapPage.tsx`, `FocusPage.tsx`, `AuthPage.tsx`, `DeadlinesPage.tsx`, `TasksPage.tsx`, `ProjectsPage.tsx`, `HomePage.tsx`

**Componentes/UI**
- `Sidebar.tsx`, `AdminRoute.tsx`, `useAuth.ts`, `authStore.ts`
- `Badge.tsx`, `Button.tsx` (variantes añadidas)

---

## 🔗 Referencias Git
- **Commit actual:** `75e87b2` (master, pushed)
- **Commit previo publicado:** `43dc0b8` (i18n oficial, plurales, first-run)
- **Stash intacto:** `stash@{0}: local changes: search API, connectors, memory`
- **Remoto:** `https://github.com/Fabian1808/Compa-ero_IA.git`

---

## 🧭 Cómo continuar (guía rápida)

```bash
# 1. Verificar estado actual
git status
cd frontend && npm run build    # build web
cd ../backend && python -m pytest -q  # tests auth

# 2. Siguiente página admin sugerida
#   Usar migrate-i18n.mjs con spec-* JSON como patrón

# 3. Corregir polling FirstRun
#   Editar FirstRunInstallerPage.tsx → unificar startInstallation + useEffect

# 4. Resolver auth real
#   Implementar JWT/session, /auth/status real, secure token storage

# 5. Lint configurado
#   Añadir a pyproject.toml: [tool.ruff.lint] ignore = ["B008"] # FastAPI Depends idiom
```

---

*Documento generado automáticamente tras commit 75e87b2. Actualizar al completar cada hito.*