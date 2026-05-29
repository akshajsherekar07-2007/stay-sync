/**
 * UI Store — global UI state (theme, sidebar, modals).
 */
import { create } from "zustand";

interface UIState {
  theme: "light" | "dark";
  sidebarOpen: boolean;
  toggleTheme: () => void;
  setSidebarOpen: (open: boolean) => void;
}

export const useUIStore = create<UIState>((set) => ({
  theme: (localStorage.getItem("staysync-theme") as "light" | "dark") || "light",
  sidebarOpen: false,

  toggleTheme: () =>
    set((state) => {
      const newTheme = state.theme === "light" ? "dark" : "light";
      localStorage.setItem("staysync-theme", newTheme);
      document.documentElement.classList.toggle("dark", newTheme === "dark");
      return { theme: newTheme };
    }),

  setSidebarOpen: (open: boolean) => set({ sidebarOpen: open }),
}));
