import { contextBridge } from "electron";

contextBridge.exposeInMainWorld("api", {
  version: "0.1.0",
});
