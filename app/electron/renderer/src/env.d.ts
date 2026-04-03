/// <reference types="vite/client" />

export {};

declare module "*.vue" {
  import type { DefineComponent } from "vue";
  const component: DefineComponent<Record<string, never>, Record<string, never>, unknown>;
  export default component;
}

declare global {
  interface Window {
    api?: {
      version: string;
      auth?: {
        getSession: () => Promise<string | null>;
        setSession: (payload: string) => Promise<boolean>;
        clearSession: () => Promise<boolean>;
      };
    };
  }
}
