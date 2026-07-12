"use client";

import { useTheme } from "./ThemeProvider";

export function DarkModeToggle() {
  const { dark, toggle } = useTheme();
  return (
    <button
      onClick={toggle}
      aria-label="Toggle dark mode"
      className="card px-3 py-2 text-sm font-medium hover:bg-plane dark:hover:bg-plane-dark transition-colors"
    >
      {dark ? "☀️ Light" : "🌙 Dark"}
    </button>
  );
}
