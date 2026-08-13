# OSPilot - Deployment & Desktop Installer Build Guide

This guide details how to build standalone production desktop executables (`.exe`), configure environment variables, deploy local Ollama models, and run OSPilot in production.

---

## 1. Prerequisites & Environment Setup

### System Requirements
- **OS**: Windows 10 / 11 (64-bit)
- **Node.js**: v18.x or higher
- **Python**: v3.10 to v3.14 (Virtual Environment in `venv/`)
- **Ollama**: Local Ollama runtime installed (`https://ollama.com`)

### Pulling Required Ollama Models
Before running in production, ensure the following local LLM models are pulled into Ollama:
```powershell
ollama pull qwen3:8b
ollama pull qwen2.5-coder:7b
ollama pull gemma3:latest
```

---

## 2. Local Production Setup

```powershell
# 1. Clone repository
git clone https://github.com/your-org/ospilot.git
cd ospilot

# 2. Setup Python Virtual Environment
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r backend/requirements.txt

# 3. Install Node.js Dependencies
npm install

# 4. Run Desktop Application
npm start
```

---

## 3. Building Standalone Windows Executable Installer (`.exe`)

OSPilot uses `electron-builder` to bundle the Electron shell, Python backend script triggers, static frontend assets, and installer scripts into a standalone installer (`ospilot-Setup.exe`).

### Build Command
```powershell
npm run dist
```

### Output Files
After completion, standalone installer executables are generated in `dist/`:
- `dist/OSPilot Desktop Setup 1.0.0.exe` (NSIS Interactive Installer)
- `dist/OSPilot Desktop 1.0.0.exe` (Portable Executable)

---

## 4. Production Database & Logging Maintenance

- **SQLite Database**: Located at `d:\OS Pilot\ospilot.db`. Uses `PRAGMA journal_mode=WAL;` for concurrent read/write access.
- **Log Files**: Written to `d:\OS Pilot\data\logs\ospilot.log` via `RotatingFileHandler` (max 10MB per file, 5 backup rotations).
- **FAISS Vector Index**: Stored in SQLite and memory space.

---

## 5. Security Checklist
1. **Safety Modal Protocol**: Ensure safety confirmation dialogs remain active for `delete_file`, `close_application`, `shutdown`, `restart`, `sleep`.
2. **CORS Headers**: Backend endpoints restrict external network exposure to local IPC `127.0.0.1`.
3. **No Telemetry**: 100% offline local inference guaranteed.
