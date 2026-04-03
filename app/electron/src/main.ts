import { app, BrowserWindow, ipcMain, safeStorage } from "electron";
import { spawn, type ChildProcess } from "child_process";
import fs from "fs";
import path from "path";

let mainWindow: BrowserWindow | null = null;
let backendProcess: ChildProcess | null = null;
const authSessionPath = () => path.join(app.getPath("userData"), "auth-session.bin");

function resolveBackendExecutable(): string | null {
  if (!app.isPackaged) {
    return null;
  }

  const executableName = process.platform === "win32" ? "lasvegarscorp-backend.exe" : "lasvegarscorp-backend";
  const executablePath = path.join(process.resourcesPath, "backend", "dist", executableName);
  if (!fs.existsSync(executablePath)) {
    return null;
  }
  return executablePath;
}

function startBackend() {
  const backendExecutable = resolveBackendExecutable();
  if (!backendExecutable) {
    return;
  }

  const userDataPath = app.getPath("userData");
  const defaultRulesPath = path.join(process.resourcesPath, "backend", "rules.json");
  const env = {
    ...process.env,
    LASVEGASCORP_DATA_DIR: userDataPath,
    LASVEGASCORP_DEFAULT_RULES_PATH: defaultRulesPath,
    LVC_BACKEND_HOST: "127.0.0.1",
    LVC_BACKEND_PORT: "8000",
  };

  backendProcess = spawn(backendExecutable, [], {
    env,
    windowsHide: true,
    stdio: "ignore",
  });
}

function stopBackend() {
  if (backendProcess && !backendProcess.killed) {
    backendProcess.kill();
  }
  backendProcess = null;
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
    },
  });

  const devServerUrl = process.env.VITE_DEV_SERVER_URL;
  if (devServerUrl) {
    mainWindow.loadURL(devServerUrl);
  } else {
    const indexHtml = path.join(__dirname, "../renderer-dist/index.html");
    mainWindow.loadFile(indexHtml);
  }
}

function writeAuthSession(payload: string) {
  const target = authSessionPath();
  fs.mkdirSync(path.dirname(target), { recursive: true });
  const contents = safeStorage.isEncryptionAvailable() ? safeStorage.encryptString(payload) : Buffer.from(payload, "utf-8");
  fs.writeFileSync(target, contents);
}

function readAuthSession() {
  const target = authSessionPath();
  if (!fs.existsSync(target)) {
    return null;
  }
  const raw = fs.readFileSync(target);
  if (!raw.length) {
    return null;
  }
  if (safeStorage.isEncryptionAvailable()) {
    return safeStorage.decryptString(raw);
  }
  return raw.toString("utf-8");
}

function clearAuthSession() {
  const target = authSessionPath();
  if (fs.existsSync(target)) {
    fs.unlinkSync(target);
  }
}

app.whenReady().then(() => {
  ipcMain.handle("auth:get-session", () => readAuthSession());
  ipcMain.handle("auth:set-session", (_event, payload: string) => {
    writeAuthSession(payload);
    return true;
  });
  ipcMain.handle("auth:clear-session", () => {
    clearAuthSession();
    return true;
  });
  startBackend();
  createWindow();
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    stopBackend();
    app.quit();
  }
});

app.on("activate", () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow();
});

app.on("before-quit", () => {
  stopBackend();
});
