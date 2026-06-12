import { Toaster as SonnerToaster } from "sonner";
import { useUIStore } from "../../stores/uiStore";

export function Toaster() {
  const { theme } = useUIStore();

  return (
    <SonnerToaster
      theme={theme === "system" ? "system" : theme}
      className="toaster group"
      toastOptions={{
        classNames: {
          toast:
            "group toast group-[.toaster]:bg-card group-[.toaster]:text-text group-[.toaster]:border-border group-[.toaster]:shadow-lg group-[.toaster]:rounded-md font-sans",
          description: "group-[.toast]:text-text-secondary",
          actionButton:
            "group-[.toast]:bg-primary group-[.toast]:text-white group-[.toast]:hover:bg-primary-dark",
          cancelButton:
            "group-[.toast]:bg-bg-secondary group-[.toast]:text-text group-[.toast]:hover:bg-bg-tertiary",
        },
      }}
    />
  );
}
