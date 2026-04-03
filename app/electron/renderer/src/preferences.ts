import { computed, reactive } from "vue";

type PreferencesState = {
  defaultMileageMultiplier: number;
  dashboardIncludeHistory: boolean;
};

const PREFERENCES_STORAGE_KEY = "lvc-user-preferences";

const savedPreferences = (() => {
  if (typeof window === "undefined") {
    return null;
  }
  try {
    const raw = window.localStorage.getItem(PREFERENCES_STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
})();

export const preferencesState = reactive<PreferencesState>({
  defaultMileageMultiplier: Number(savedPreferences?.defaultMileageMultiplier ?? 1) || 1,
  dashboardIncludeHistory: Boolean(savedPreferences?.dashboardIncludeHistory),
});

function persistPreferences() {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.setItem(PREFERENCES_STORAGE_KEY, JSON.stringify(preferencesState));
}

export function setDefaultMileageMultiplier(value: number) {
  const normalized = Number(value);
  preferencesState.defaultMileageMultiplier = Number.isFinite(normalized) && normalized >= 0 ? normalized : 1;
  persistPreferences();
}

export function setDashboardIncludeHistory(value: boolean) {
  preferencesState.dashboardIncludeHistory = Boolean(value);
  persistPreferences();
}

export function useMileagePreference() {
  return computed({
    get: () => preferencesState.defaultMileageMultiplier,
    set: (value: number) => {
      setDefaultMileageMultiplier(value);
    },
  });
}
