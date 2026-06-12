import { Sun, Moon, Monitor } from "lucide-react";
import { Button } from "../ui/Button";
import { useUIStore } from "../../stores/uiStore";

export function ThemeToggle() {
  const { theme, toggleTheme } = useUIStore();

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={toggleTheme}
      title={`Current theme: ${theme}. Click to change.`}
      aria-label="Toggle theme"
    >
      {theme === "light" && <Sun className="h-5 w-5 text-text transition-all" />}
      {theme === "dark" && <Moon className="h-5 w-5 text-text transition-all" />}
      {theme === "system" && <Monitor className="h-5 w-5 text-text transition-all" />}
    </Button>
  );
}
