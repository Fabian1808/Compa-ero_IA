# Building AI Workmate Desktop App

AI Workmate es una **aplicación de escritorio nativa** (no web) que se instala como cualquier programa (.exe/.msi en Windows, .dmg en macOS, .AppImage en Linux).

## 🏗️ Arquitectura Local-First

```
┌─────────────────────────────────────────────────────────────┐
│  AI Workmate.app (Tauri)                                    │
├─────────────────────────────────────────────────────────────┤
│  Frontend (React)        │  Backend Sidecar (FastAPI)       │
│  - Assets estáticos      │  - Binario PyInstaller           │
│  - Sin servidor web      │  - Puerto 8000 local             │
├─────────────────────────────────────────────────────────────┤
│  Datos 100% Locales (C:\Users\<user>\AppData\AI Workmate\)   │
│  ├── SQLite (ai-workmate.db)                                │
│  ├── Qdrant Embedded (vectores)                             │
│  ├── Ollama (phi3:3.8b + nomic-embed-text)                  │
│  └── Tokens MS Graph (Windows Credential Manager)           │
├─────────────────────────────────────────────────────────────┤
│  Conexión Externa: Microsoft Graph API (OAuth Device Code)  │
└─────────────────────────────────────────────────────────────┘
```

## 📋 Requisitos Previos

### En la máquina de desarrollo:
| Herramienta | Versión | Instalación |
|-------------|---------|-------------|
| Python | 3.11+ | `winget install Python.Python.3.11` |
| Node.js | 18+ | `winget install OpenJS.NodeJS` |
| Rust | 1.75+ | `winget install Rustlang.Rust` |
| PyInstaller | 6+ | `pip install pyinstaller` |
| Ollama | Latest | `winget install Ollama.Ollama` |

### En la máquina del usuario final:
- **Windows 10/11** (para .msi/.exe)
- **Ollama** instalado con modelos: `phi3:3.8b` y `nomic-embed-text`

```bash
# Instalar Ollama y modelos en máquina del usuario
winget install Ollama.Ollama
ollama pull phi3:3.8b
ollama pull nomic-embed-text
```

## 🔨 Build Commands

### Opción 1: Script automatizado (Linux/macOS/WSL)
```bash
chmod +x build.sh
./build.sh                    # Build completo
./build.sh --backend-only     # Solo backend
./build.sh --frontend-only    # Solo frontend
./build.sh --tauri-only       # Solo Tauri (requiere builds previos)
```

### Opción 2: Batch script (Windows nativo)
```cmd
build.bat                     # Build completo
build.bat --backend-only      # Solo backend
build.bat --frontend-only     # Solo frontend
build.bat --tauri-only        # Solo Tauri
```

### Opción 3: Manual paso a paso

#### 1. Backend → Binario standalone
```bash
cd backend
pip install -e .
pyinstaller ai-workmate-backend.spec --clean --noconfirm
# Genera: backend/dist/ai-workmate-backend.exe
```

#### 2. Frontend → Build estático
```bash
cd frontend
npm install
npm run build
# Genera: frontend/dist/
```

#### 3. Tauri → Instalador nativo
```bash
cd tauri
cargo tauri build
# Genera instaladores en tauri/target/release/bundle/
```

## 📦 Output Files

| Plataforma | Archivo | Ubicación |
|------------|---------|-----------|
| **Windows** | `AI Workmate_0.1.0_x64.msi` | `tauri/target/release/bundle/msi/` |
| **Windows** | `AI Workmate_0.1.0_x64-setup.exe` | `tauri/target/release/bundle/nsis/` |
| **macOS** | `AI Workmate_0.1.0_x64.dmg` | `tauri/target/release/bundle/dmg/` |
| **Linux** | `AI Workmate_0.1.0_amd64.AppImage` | `tauri/target/release/bundle/appimage/` |

## 🚀 Distribución

### Para usuarios Windows:
1. Descargar `AI Workmate_0.1.0_x64.msi`
2. Doble clic → Next → Finish
3. Se instala en `C:\Program Files\AI Workmate\`
4. Acceso directo en Inicio y Escritorio

### Para usuarios macOS:
1. Descargar `.dmg`
2. Arrastrar a Applications
3. Primera vez: Click derecho → Abrir (Gatekeeper)

### Para usuarios Linux:
1. Descargar `.AppImage`
2. `chmod +x AI_Workmate_0.1.0_amd64.AppImage`
3. Ejecutar

## 🔧 Configuración de Usuario (Primera vez)

Al abrir la app por primera vez:
1. **Ollama check** - Verifica que Ollama esté corriendo
2. **Device Code Flow** - Abre navegador para autorizar Microsoft 365
3. **Sync inicial** - Descarga emails, calendario, contactos
4. **Indexado IA** - Crea embeddings para búsqueda semántica

## 📁 Estructura de Datos en Disco

```
Windows: %APPDATA%\AI Workmate\
├── ai-workmate.db          # SQLite principal
├── qdrant/                 # Vector DB embebida
├── logs/                   # Logs de la app
├── ollama/                 # Modelos (opcional, usa sistema global)
└── config.json             # Configuración local
```

## 🐛 Troubleshooting

### Backend no inicia
```bash
# Ver logs
%APPDATA%\AI Workmate\logs\ai-workmate.log

# Verificar puerto 8000 libre
netstat -ano | findstr :8000
```

### Ollama no responde
```bash
# Verificar servicio
ollama list
ollama serve
```

### Tauri build falla
```bash
# Limpiar cache
cd tauri
cargo clean
cargo tauri build
```

### Icono no aparece
- Generar `.ico` desde `frontend/public/icon.svg` (256x256, 128x128, 64x64, 48x48, 32x32, 16x16)
- Herramientas: `magick`, `ImageMagick`, o online converters

## 📝 Versionado

Actualizar versión en:
- `backend/pyproject.toml` → `version = "0.1.0"`
- `frontend/package.json` → `"version": "0.1.0"`
- `tauri/Cargo.toml` → `version = "0.1.0"`
- `tauri/tauri.conf.json` → `"version": "0.1.0"`

## 🔐 Firma de Código (Producción)

### Windows (Certificado EV)
```json
// tauri.conf.json
"bundle": {
  "windows": {
    "certificateThumbprint": "YOUR_THUMBPRINT",
    "digestAlgorithm": "sha256",
    "timestampUrl": "http://timestamp.digicert.com"
  }
}
```

### macOS (Developer ID)
```bash
# En tauri.conf.json
"macOS": {
  "signingIdentity": "Developer ID Application: Your Name (TEAM_ID)",
  "entitlements": "entitlements.plist"
}
```

## 💰 Coste Total: $0

| Componente | Coste |
|------------|-------|
| Python/Rust/Node.js | Gratis |
| Ollama (IA local) | Gratis |
| SQLite/Qdrant | Gratis |
| Tauri/PyInstaller | Gratis |
| Microsoft Graph API | Gratis (con cuenta M365) |
| **Total** | **$0** |

---

**¡Listo para distribuir!** 🎉