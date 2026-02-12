# lasvegarscorp

Cross-platform Electron + Python automation suite.

Planned stack:
- Electron + Vue + Tailwind (UI)
- Python + FastAPI + pandas (backend)
- Python-only plugin system

## Build installers (Windows/Linux)

### Recommended: GitHub Actions from macOS
- Push your code to GitHub.
- Run workflow `.github/workflows/build-installers.yml` via `Actions -> Build Installers -> Run workflow`.
- Download artifacts:
  - `windows-installers` for `.exe` installer
  - `linux-installers` for `AppImage`/`deb`
  - `macos-installers` for `.dmg`/`.zip`

### Local packaging prerequisites
- Python 3.11+
- Node.js 20+
- `pip install -r app/python/requirements.txt pyinstaller`
- `cd app/electron && npm install`

### Build backend executable
```bash
pyinstaller --onefile --name lasvegarscorp-backend --distpath app/python/dist app/python/run_server.py
```

### Build Electron installers
```bash
cd app/electron
npm run dist:win   # run on Windows or CI windows-latest
npm run dist:linux # run on Linux or CI ubuntu-latest
```
