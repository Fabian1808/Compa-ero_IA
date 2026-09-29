# AI Workmate

> Un compañero de trabajo digital que te ayuda a organizar y avanzar en tu trabajo, una tarea a la vez.

## 🎯 Visión

AI Workmate no es otro gestor de tareas ni otro cliente de correo. Es una **capa inteligente** encima de las herramientas que ya usas (Outlook, Calendar, Teams, etc.) que:

- **Detecta automáticamente** tareas, deadlines, compromisos y seguimientos en tus correos
- **Te recomienda** qué hacer ahora basado en deadlines, tiempo disponible y prioridades
- **Te acompaña** en modo foco sin distracciones
- **Aprende** de tus patrones para mejorar con el tiempo

## 🚀 Estado del Proyecto

**Fase 1 - MVP** (En desarrollo)
- [x] Arquitectura base (Tauri + React + FastAPI)
- [x] Modelos de datos (SQLAlchemy + SQLite)
- [x] Autenticación Microsoft OAuth (Device Code Flow)
- [x] Conector Outlook (Microsoft Graph + Delta Sync)
- [x] IA Local (Ollama + phi3:3.8b)
- [x] Extracción de tareas, compromisos, deadlines
- [x] API REST completa
- [x] UI: Home, Tasks, Projects, Settings, Focus Mode
- [ ] Empaquetado Tauri + PyInstaller
- [ ] Tests E2E

## 🛠 Stack Tecnológico

| Capa | Tecnología |
|------|------------|
| **Frontend** | Tauri 2 + React 18 + TypeScript + Vite |
| **UI** | shadcn/ui + Tailwind CSS + Zustand |
| **Backend** | Python 3.11 + FastAPI + SQLAlchemy 2.0 |
| **Base de datos** | SQLite (aiosqlite) + Alembic |
| **IA Local** | Ollama (phi3:3.8b + nomic-embed-text) |
| **Vector DB** | Qdrant (embebido) |
| **Auth** | MSAL + Microsoft Graph (Work/School) |
| **Empaquetado** | PyInstaller (sidecar) |

## 📦 Requisitos Previos

- **Node.js** 18+ y npm
- **Rust** (para Tauri)
- **Python** 3.11+
- **Ollama** instalado y corriendo (`ollama serve`)
  - Modelos: `ollama pull phi3:3.8b` y `ollama pull nomic-embed-text`
- **Cuenta Microsoft Work/School** (Azure AD / Entra ID)

## 🔧 Instalación y Desarrollo

### 1. Clonar y configurar backend

```bash
cd ai-workmate/backend
cp .env.example .env
# Editar .env con tus credenciales Microsoft Graph
pip install -e .[dev]
python -m alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### 2. Configurar frontend

```bash
cd ai-workmate/frontend
npm install
npm run dev
```

### 3. Ejecutar Tauri (ventana de escritorio)

```bash
cd ai-workmate/tauri
cargo tauri dev
```

## 🔐 Configuración Microsoft Graph

1. Ve a [Azure Portal](https://portal.azure.com/)
2. **Azure Active Directory** > **App registrations** > **New registration**
3. Nombre: "AI Workmate"
4. **Supported account types**: "Accounts in this organizational directory only" (Single tenant)
5. **Redirect URI**: `http://localhost:8000/api/v1/auth/callback` (Mobile and desktop applications)
6. Copia **Application (client) ID** y **Directory (tenant) ID**
7. **Certificates & secrets** > **New client secret** > Copia el valor
8. **API permissions** > Add:
   - `Mail.Read`
   - `Mail.ReadWrite`
   - `Calendars.Read`
   - `Contacts.Read`
   - `User.Read`
9. **Grant admin consent** para tu tenant

## 📁 Estructura del Proyecto

```
ai-workmate/
├── backend/                 # FastAPI + Python
│   ├── app/
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── api/v1/         # REST endpoints
│   │   ├── services/       # Business logic
│   │   ├── connectors/     # Outlook, Calendar, etc.
│   │   ├── ai/             # Ollama, prompts, tools
│   │   ├── memory/         # Qdrant, embeddings
│   │   ├── events/         # Event bus (blinker)
│   │   └── security/       # Encryption, tokens
│   ├── alembic/            # Migrations
│   └── pyproject.toml
├── frontend/               # React + TypeScript
│   ├── src/
│   │   ├── components/     # UI components
│   │   ├── pages/          # Page components
│   │   ├── hooks/          # Custom hooks
│   │   ├── services/       # API client
│   │   ├── store/          # Zustand stores
│   │   └── types/          # TypeScript types
│   └── package.json
├── tauri/                  # Tauri config
│   ├── tauri.conf.json
│   └── Cargo.toml
├── .env.example
└── README.md
```

## 🎨 Principios de UX

1. **Una tarea a la vez** - Modo foco sin distracciones
2. **Zero-config** - Funciona out-of-the-box
3. **IA explicable** - Siempre dice por qué recomienda algo
4. **Confirmación humana** - La IA propone, tú decides
5. **Privacidad local** - Datos y IA en tu máquina

## 📋 Roadmap

### Fase 1 - MVP ✅
- Outlook connector + delta sync
- Detección tareas/compromisos/deadlines
- Home + Tasks + Projects + Focus
- IA local (Ollama)

### Fase 2 - Calendar & Followups
- Calendario integrado
- Daily Briefing / End of Day
- Follow-up Center
- Mejoras en recomendaciones

### Fase 3 - Teams + Files + Memory
- Teams connector
- OneDrive/SharePoint
- Memoria semántica (RAG)
- Búsqueda global

### Fase 4 - Integrations
- Excel, Power BI, SAP
- n8n / Power Automate
- Sistema de plugins

### Fase 5 - Intelligence
- Agentes especializados
- Aprendizaje de patrones
- Marketplace conectores

## 🧪 Testing

```bash
# Backend
cd backend
pytest --cov=app --cov-report=html

# Frontend
cd frontend
npm run test
```

## 📄 Licencia

MIT License - Ver [LICENSE](LICENSE) para detalles.

## 🤝 Contribuir

1. Fork el repo
2. Crea una rama (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -am 'Add: nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

## 📞 Soporte

- Issues: [GitHub Issues](https://github.com/tu-usuario/ai-workmate/issues)
- Discusiones: [GitHub Discussions](https://github.com/tu-usuario/ai-workmate/discussions)