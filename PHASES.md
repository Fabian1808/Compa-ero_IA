# AI Workmate - Documentación de Fases

> **Repositorio:** https://github.com/Fabian1808/Compa-ero_IA
> **Proyecto:** Compañero de trabajo digital inteligente, local-first, conectado a herramientas Microsoft 365

---

## 📋 Resumen Ejecutivo

**AI Workmate** no es otro gestor de tareas ni cliente de correo. Es una **capa inteligente** encima de las herramientas que ya usas (Outlook, Calendar, Teams, etc.) que:

- **Detecta automáticamente** tareas, deadlines, compromisos y seguimientos en tus correos
- **Te recomienda** qué hacer ahora basado en deadlines, tiempo disponible y prioridades
- **Te acompaña** en modo foco sin distracciones
- **Aprende** de tus patrones para mejorar con el tiempo

**Principio fundamental:** *Una tarea a la vez* — El usuario avanza: Pendiente → Trabaja → Completa → Siguiente.

---

## 🏗 Arquitectura Técnica

### Stack Tecnológico

| Capa | Tecnología | Versión |
|------|------------|---------|
| **Frontend** | Tauri 2 + React 18 + TypeScript + Vite | Latest |
| **UI** | shadcn/ui (Radix) + Tailwind CSS + Zustand | Latest |
| **Backend** | Python 3.11 + FastAPI + SQLAlchemy 2.0 | Latest |
| **Base de datos** | SQLite (aiosqlite) + Alembic migrations | Latest |
| **IA Local** | Ollama (phi3:3.8b chat + nomic-embed-text embeddings) | Latest |
| **Vector DB** | Qdrant (embebido, sin Docker) | Latest |
| **Auth** | MSAL + Microsoft Graph (Work/School - organizations endpoint) | Latest |
| **Empaquetado** | PyInstaller (sidecar binario) | Latest |

### Estructura del Proyecto

```
ai-workmate/
├── backend/                    # FastAPI + Python
│   ├── app/
│   │   ├── models/            # 14 modelos SQLAlchemy
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── api/v1/            # 11 routers REST
│   │   ├── services/          # Lógica de negocio
│   │   ├── connectors/        # Outlook, Calendar, etc.
│   │   ├── ai/                # Ollama, prompts, tools
│   │   ├── memory/            # Qdrant, embeddings
│   │   ├── events/            # Event bus (blinker)
│   │   ├── security/          # Encryption, tokens
│   │   └── main.py
│   ├── alembic/               # Migraciones
│   └── pyproject.toml
├── frontend/                   # React + TypeScript
│   ├── src/
│   │   ├── components/        # UI + Layout + Home
│   │   ├── pages/             # 11 páginas
│   │   ├── hooks/             # 5 custom hooks
│   │   ├── services/          # API client (Axios)
│   │   ├── store/             # 3 Zustand stores
│   │   └── types/             # TypeScript types
│   └── tailwind.config.js
├── tauri/                      # Tauri config
├── scripts/                    # dev.bat / dev.sh
├── .env.example
├── README.md
└── PHASES.md                  # Este archivo
```

---

## 📦 FASE 1 - MVP (Completada ✅)

**Objetivo:** Conectar Outlook → detectar pendientes → ayudar a avanzar una tarea a la vez.

### Entregables

#### 1. Autenticación Microsoft (Work/School)
- **Device Code Flow** OAuth 2.0 (sin servidor local)
- Tokens encriptados con **Fernet** + **OS Keyring** (Windows Credential Manager)
- Refresh automático de access tokens
- Scopes mínimos: `Mail.Read Mail.ReadWrite Calendars.Read Contacts.Read User.Read`

#### 2. Conector Outlook (Microsoft Graph)
- **Delta Sync incremental** (`/messages/delta`) — no re-descarga todo el buzón
- Sincroniza: emails, threads, contactos, reuniones (calendario)
- Manejo de throttling (429) con exponential backoff
- Guarda `deltaLink` para sincronizaciones posteriores
- Eventos emitidos: `EMAILS_SYNCED`, `SYNC_COMPLETED`, `SYNC_FAILED`

#### 3. Base de Datos (SQLite + SQLAlchemy 2.0)
**14 modelos principales:**
| Modelo | Descripción |
|--------|-------------|
| `User` | Usuario local (aislado por cuenta Microsoft) |
| `Account` | Cuenta conectada + tokens encriptados |
| `Email` / `EmailThread` | Correos e hilos sincronizados |
| `Contact` | Contactos de Outlook |
| `Meeting` | Eventos de calendario |
| `Task` | Tareas con estado, prioridad, deadline, proyecto |
| `Project` | Proyectos auto-detectados o manuales |
| `Commitment` | Compromisos del usuario ("te lo envío mañana") |
| `FollowUp` | Seguimientos de emails enviados sin respuesta |
| `Notification` | Centro de notificaciones (4 severidades) |
| `AIMemory` / `Embedding` | Memoria semántica (RAG) |
| `EventLog` / `AuditLog` | Observabilidad |
| `Setting` | Configuración por usuario |

#### 4. IA Local (Ollama)
- **Chat:** `phi3:3.8b` (Microsoft, eficiente, 2.3GB RAM)
- **Embeddings:** `nomic-embed-text` (768 dims)
- **Provider abstraction** para cambiar modelo sin tocar código
- **Tool Calling** controlado (6 herramientas definidas)

#### 5. Extracción de Información (Prompts Few-Shot)
| Prompt | Detecta | Output |
|--------|---------|--------|
| `TASK_EXTRACTION` | Solicitudes accionables | title, deadline, priority, estimated_min, project_hint, confidence |
| `COMMITMENT_EXTRACTION` | Promesas propias | description, due_date, confidence |
| `DEADLINE_EXTRACTION` | Fechas límite externas | description, deadline, is_external |
| `FOLLOWUP_DETECTION` | Emails sin respuesta >48h | contact, subject, days_waiting, suggested_action |
| `NEXT_TASK_RECOMMENDATION` | Qué hacer ahora | task_id, reasoning, confidence |

#### 6. Confidence Scoring (3 Tiers)
| Tier | Score | Acción |
|------|-------|--------|
| `AUTO_CREATE` | ≥95% | Crea automáticamente (bajo riesgo) |
| `SUGGEST_CONFIRM` | 80-94% | Tarjeta confirmación [Agregar][Editar][Ignorar] |
| `LOW_CONFIDENCE` | <80% | Solo log, no muestra al usuario |

#### 7. Task Management
- Estados: `pending → in_progress → completed/blocked/waiting_response/requires_decision/cancelled`
- Prioridades: `low/medium/high/critical`
- Dependencias entre tareas (`blocks`, `relates_to`)
- Focus Mode: timer, pausa, completar con minutos reales

#### 8. API REST Completa (11 routers)
```
/auth          → login, callback, refresh, logout
/emails        → list, get, search, process, threads
/tasks         → CRUD, stats, recommend-next, focus, complete
/projects      → CRUD, progress
/ai            → analyze-email, daily-briefing, end-of-day, ask, what-am-i-forgetting
/calendar      → events today/upcoming/range
/commitments   → CRUD, complete
/deadlines     → list (30d), upcoming (hours)
/followups     → list, detect, prepare-draft, dismiss
/notifications → list, mark-read, settings
/health        → app + AI health
```

#### 9. Frontend (React + Zustand)
**Páginas:**
- `HomePage` — Dashboard principal + IA question + Next Task Card
- `TasksPage` — Lista filtrable + modal crear + focus
- `ProjectsPage` — Grid + progreso + modal CRUD
- `FocusPage` — Timer persistente + notas + controles
- `AuthPage` — Device Code Flow UI

**Componentes UI (shadcn-style):** Button, Card, Input, Badge, Separator
**Stores:** `authStore`, `taskStore`, `uiStore` (persistidos)

#### 10. Event Bus & Scheduler
- **Blinker** para eventos internos (30+ tipos)
- **APScheduler** jobs: sync 5min, daily briefing 8am, end-of-day 6pm, notifications 1min

---

## 📦 FASE 2 - Calendar & Intelligence (Completada ✅)

**Objetivo:** Añadir calendario, briefing diario, seguimientos, compromisos, deadlines unificados.

### Entregables

#### 1. Calendar API (`/api/v1/calendar`)
```python
GET /calendar/events?start=&end=      # Rango de fechas
GET /calendar/events/today            # Eventos de hoy
GET /calendar/events/upcoming?hours=24  # Próximas N horas
GET /calendar/events/{id}             # Detalle evento
```
- Integración real con meetings sincronizados de Outlook
- Time-until calculado dinámicamente

#### 2. Daily Briefing (`POST /ai/daily-briefing`)
**Genera cada mañana (8:00):**
- Compromisos importantes del día
- Tareas pendientes (deadlines hoy, alta prioridad)
- Reuniones programadas
- Tareas bloqueadas
- Emails importantes sin leer
- Seguimientos pendientes
- **Resumen IA** en lenguaje natural (max 200 palabras)

#### 3. End of Day (`POST /ai/end-of-day`)
**Genera cada tarde (18:00):**
- Tareas completadas hoy
- Emails procesados
- Proyectos avanzados
- Pendientes abiertos para mañana
- Deadlines de mañana
- Seguimientos pendientes
- **Resumen reflexivo IA** (max 150 palabras)

#### 4. Follow-ups Center
- **Detección automática:** `detect_followups()` escanea emails enviados (últimos 30d) sin respuesta >48h
- **API:** `GET /followups`, `POST /followups/detect`, `POST /followups/{id}/prepare` (genera borrador IA), `POST /followups/{id}/dismiss`
- **UI:** FollowupsPage con tabla, estados, borradores editables antes de enviar

#### 5. Commitments (Compromisos)
- **Modelo:** `Commitment` (description, due_date, status, confidence, source_email)
- **API CRUD:** `/api/v1/commitments` + complete
- **UI:** CommitmentsPage — tabla, crear/editar/completar/eliminar, badges de estado

#### 6. Deadlines Unificados
- **API:** `/api/v1/deadlines` combina Tasks + Commitments
- **Endpoints:** `?days=30`, `/upcoming?hours=168`
- **UI:** DeadlinesPage con tabs (Próximas 24h, Esta semana, Vencidas, Todas 30d)
- **Agrupación por fecha** con badges de prioridad y tipo (tarea/compromiso)

#### 7. Focus Mode Mejorado
- Timer persistente (usa `task.started_at` en BD)
- Notas de foco guardadas en `metadata_json`
- Controles: Pausar/Continuar, Detener, Completar con minutos reales

#### 8. Home Page Integrada
- Tarjeta **"¿Qué debería hacer ahora?"** con recomendación IA expandida
- Botones: Preguntar a IA, Qué hacer ahora, Nueva tarea, Sincronizar
- Daily Briefing / End of Day integrados
- Quick Actions grid

#### 9. Navegación Actualizada
Sidebar con: Inicio, Pendientes, Proyectos, Calendario, Seguimientos, **Compromisos**, **Deadlines**, Memoria, Aplicaciones, Configuración

---

## 📦 FASE 3 - Teams + Files + Memory (En Progreso 🔄)

**Objetivo:** Conectar Teams, OneDrive, SharePoint + Memoria semántica (RAG) + Búsqueda global.

### Planificación

#### 1. Conectores Adicionales
| Conector | API | Funcionalidad |
|----------|-----|---------------|
| **Teams** | Graph `/chats`, `/messages` | Chats, canales, mensajes, reuniones online |
| **OneDrive** | Graph `/drive` | Archivos personales, búsqueda, metadatos |
| **SharePoint** | Graph `/sites` | Sitios de equipo, listas, documentos compartidos |

#### 2. Memoria Semántica (RAG)
- **Indexado incremental** de emails, tareas, documentos
- **Qdrant embebido** para vector search
- **Hybrid search:** keyword + semantic
- **API:** `POST /ai/ask` con retrieval contextual

#### 3. Búsqueda Global (`/api/v1/search`)
```
"¿Qué pendientes tengo con Juan?"
"¿Qué correos hablan del proyecto X?"
"¿Qué prometí hacer esta semana?"
"¿Qué está bloqueado?"
"¿Qué vence mañana?"
```

#### 4. Detección de Bloqueos Automática
- Analiza dependencias entre tareas
- Detecta: "Dashboard bloqueado → necesita valorizaciones → proveedor no responde"
- Propone seguimiento automático

#### 5. Mapa de Trabajo Visual
- Grafo proyectos-tareas-personas-deadlines
- Vista de progreso por proyecto
- Identificación de cuellos de botella

---

## 📦 FASE 4 - Integrations & Automation (Planificada)

**Objetivo:** Conectores empresariales + automatizaciones + marketplace.

### Planificación

| Integración | Propósito |
|-------------|-----------|
| **Excel** | Leer/escribir datos, importar tareas desde hojas |
| **Power BI** | Métricas de productividad, dashboards |
| **SAP** | Órdenes, proveedores, datos financieros |
| **GitHub** | Issues, PRs, commits vinculados a tareas |
| **n8n / Power Automate** | Workflows visuales, triggers/actions |

### Sistema de Plugins
- Interfaz `Connector` estándar
- Registro dinámico de conectores
- Permisos granulares por conector
- Marketplace interno (futuro)

---

## 📦 FASE 5 - Intelligence & Enterprise (Futura)

**Objetivo:** Agentes especializados + aprendizaje + multi-usuario enterprise.

### Planificación

| Componente | Descripción |
|------------|-------------|
| **Planning Agent** | Planificación automática de día/semana |
| **Email Agent** | Triaje, respuesta, categorización |
| **Follow-up Agent** | Seguimientos proactivos |
| **Research Agent** | Búsqueda web/documentos para contexto |
| **Document Agent** | Generación/extracción docs |
| **Orchestrator** | Coordinación multi-agente |

### Enterprise Features
- **Multi-tenancy** con aislamiento total
- **Admin Panel:** Users, Connectors, Permissions, Audit, AI Config, Security
- **SSO/Entra ID** integration
- **Políticas de retención** y compliance
- **Métricas de producto:** tareas detectadas/aceptadas/rechazadas, falsos positivos, tiempo ahorrado

---

## 🔐 Seguridad & Privacidad (Desde Fase 1)

| Medida | Implementación |
|--------|----------------|
| **Cifrado tokens** | Fernet + OS Keyring (no archivo plano) |
| **Principio mínimo privilegio** | Scopes mínimos, permisos por conector |
| **Confirmación humana** | IA propone → usuario confirma (nunca auto-ejecuta acciones críticas) |
| **Datos locales** | SQLite + embeddings en disco del usuario |
| **Sin telemetría oculta** | Logs locales, sin envío externo |
| **Auditoría** | `AuditLog` para acciones sensibles |

---

## 🧪 Testing & Calidad

| Herramienta | Uso |
|-------------|-----|
| **pytest + pytest-asyncio** | Unit + integration tests |
| **ruff** | Linting + formatting (line-length=100) |
| **mypy** | Type checking (strict) |
| **httpx TestClient** | API testing |
| **Fixtures** | Emails de prueba (task, deadline, commitment, followup, blocker, info) |

### Criterios de Aceptación por Fase
Ver `docs/testing.md` (pendiente)

---

## 📦 Empaquetado y Distribución

### Desarrollo
```bash
# Backend
cd backend && uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend && npm run dev  # http://localhost:1420

# Tauri (app escritorio)
cd tauri && cargo tauri dev
```

### Producción (PyInstaller + Tauri Bundle)
```bash
# Backend → binario único
cd backend && pyinstaller ai-workmate-backend.spec

# Frontend → build estático
cd frontend && npm run build

# Tauri → .msi/.exe/.dmg/.AppImage
cd tauri && cargo tauri build
```

**Recursos incluidos:** `backend/dist/ai-workmate-backend*` como sidecar

---

## 📚 Documentación Adicional (en `docs/`)

| Archivo | Contenido |
|---------|-----------|
| `architecture.md` | Diagramas capas, patrones, decisiones |
| `setup.md` | Instalación paso a paso |
| `authentication.md` | OAuth Microsoft, troubleshooting |
| `microsoft-graph.md` | Delta sync, throttling, scopes |
| `ai.md` | Prompts, confidence, tool calling, Ollama |
| `memory.md` | RAG, Qdrant, embeddings |
| `database.md` | ERD, migraciones, modelos |
| `connectors.md` | Interfaz, agregar nuevos |
| `notifications.md` | Scheduler, severidades, focus mode |
| `security.md` | Cifrado, keyring, auditoría |
| `development.md` | Workflow, commits, branching |
| `roadmap.md` | Fases 3-5 detalle |

---

## 🚀 Comandos Rápidos

```bash
# Iniciar todo (requiere Ollama corriendo)
./scripts/dev.bat     # Windows
./scripts/dev.sh      # Linux/Mac

# Solo backend
cd backend && uvicorn app.main:app --reload

# Migraciones
cd backend && python -m alembic revision --autogenerate -m "msg"
cd backend && python -m alembic upgrade head

# Tests
cd backend && pytest --cov=app
cd frontend && npm test

# Lint/Format
cd backend && ruff check . && ruff format .
cd frontend && npm run lint
```

---

## 📈 Métricas de Progreso

| Fase | Estado | Archivos | Líneas Código | Tests |
|------|--------|----------|---------------|-------|
| **Fase 1** | ✅ Completa | ~80 | ~7,000 | Pendientes |
| **Fase 2** | ✅ Completa | ~30 | ~4,300 | Pendientes |
| **Fase 3** | 🔄 En progreso | — | — | — |
| **Fase 4** | 📋 Planificada | — | — | — |
| **Fase 5** | 📋 Planificada | — | — | — |

**Total actual:** ~110 archivos, ~11,300 líneas (backend + frontend + config)

---

## 🤝 Contribución

```bash
# 1. Fork
# 2. Rama feature
git checkout -b feature/nueva-funcionalidad
# 3. Commit convencional
git commit -m "feat: descripción breve"
# 4. Push + PR
```

**Convenciones:**
- Commits: `feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `chore:`
- TypeScript strict + Python type hints
- Ruff + mypy passing en CI

---

## 📄 Licencia

MIT License — Ver `LICENSE` (pendiente)

---

## 📞 Contacto

- **Repo:** https://github.com/Fabian1808/Compa-ero_IA
- **Issues:** Bugs, features, preguntas
- **Discussions:** Ideas, arquitectura, roadmap

---

*Última actualización: 2026-09-29 — Fases 1 & 2 completadas, iniciando Fase 3*