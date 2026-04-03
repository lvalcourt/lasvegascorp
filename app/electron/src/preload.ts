import { contextBridge, ipcRenderer } from "electron";

contextBridge.exposeInMainWorld("api", {
  version: "0.1.0",
  auth: {
    getSession: () => ipcRenderer.invoke("auth:get-session"),
    setSession: (payload: string) => ipcRenderer.invoke("auth:set-session", payload),
    clearSession: () => ipcRenderer.invoke("auth:clear-session"),
  },
});
