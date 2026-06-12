/**
 * UI Store — global UI state (theme, sidebar, modals).
 */
import { create } from "zustand";

export type Theme = "light" | "dark" | "system";

interface UIState {
  theme: Theme;
  sidebarOpen: boolean;
  setTheme: (theme: Theme) => void;
  toggleTheme: () => void;
  setSidebarOpen: (open: boolean) => void;
}

const STORAGE_KEY = "staysync-theme";

const applyTheme = (theme: Theme): void => {
  if (typeof window === "undefined") return;

  const root = document.documentElement;
  let isDark = false;

  if (theme === "system") {
    isDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  } else {
    isDark = theme === "dark";
  }

  if (isDark) {
    root.classList.add("dark");
  } else {
    root.classList.remove("dark");
  }
};

let mediaQueryListener: ((e: MediaQueryListEvent) => void) | null = null;

const setupSystemThemeListener = (theme: Theme): void => {
  if (typeof window === "undefined") return;

  const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");

  if (mediaQueryListener) {
    mediaQuery.removeEventListener("change", mediaQueryListener);
    mediaQueryListener = null;
  }

  if (theme === "system") {
    mediaQueryListener = (e: MediaQueryListEvent) => {
      const root = document.documentElement;
      if (e.matches) {
        root.classList.add("dark");
      } else {
        root.classList.remove("dark");
      }
    };
    mediaQuery.addEventListener("change", mediaQueryListener);
  }
};

const getInitialTheme = (): Theme => {
  if (typeof window === "undefined") return "system";
  const saved = localStorage.getItem(STORAGE_KEY);
  if (saved === "light" || saved === "dark" || saved === "system") {
    return saved;
  }
  return "system";
};

const initialTheme = getInitialTheme();
applyTheme(initialTheme);
setupSystemThemeListener(initialTheme);

export const useUIStore = create<UIState>((set) => ({
  theme: initialTheme,
  sidebarOpen: false,

  setTheme: (theme: Theme) => {
    localStorage.setItem(STORAGE_KEY, theme);
    applyTheme(theme);
    setupSystemThemeListener(theme);
    set({ theme });
  },

  toggleTheme: () =>
    set((state) => {
      let newTheme: Theme;
      if (state.theme === "light") {
        newTheme = "dark";
      } else if (state.theme === "dark") {
        newTheme = "system";
      } else {
        newTheme = "light";
      }
      localStorage.setItem(STORAGE_KEY, newTheme);
      applyTheme(newTheme);
      setupSystemThemeListener(newTheme);
      return { theme: newTheme };
    }),

  setSidebarOpen: (open: boolean) => set({ sidebarOpen: open }),
}));

