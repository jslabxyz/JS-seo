"use client";

import { useSyncExternalStore } from "react";
import { getTheme, setTheme, subscribeTheme, type Theme } from "@/lib/theme";

function subscribe(onChange: () => void) {
  return subscribeTheme(onChange);
}

export function ThemeToggle() {
  const theme = useSyncExternalStore<Theme>(subscribe, getTheme, () => "light");
  const next = theme === "dark" ? "light" : "dark";

  return (
    <button
      type="button"
      className="theme-toggle"
      aria-label={theme === "dark" ? "Use the light theme" : "Use the dark theme"}
      aria-pressed={theme === "dark"}
      onClick={() => setTheme(next)}
    >
      <span className="theme-toggle-track">
        <SunIcon />
        <MoonIcon />
        <span className="theme-toggle-thumb" />
      </span>
    </button>
  );
}

function SunIcon() {
  return (
    <svg className="theme-toggle-sun" width="15" height="15" viewBox="0 0 24 24" aria-hidden="true">
      <circle cx="12" cy="12" r="4" fill="none" stroke="currentColor" strokeWidth="1.6" />
      <path
        d="M12 2.5v2.2M12 19.3v2.2M2.5 12h2.2M19.3 12h2.2M4.8 4.8l1.6 1.6M17.6 17.6l1.6 1.6M19.2 4.8l-1.6 1.6M6.4 17.6l-1.6 1.6"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
      />
    </svg>
  );
}

function MoonIcon() {
  return (
    <svg className="theme-toggle-moon" width="15" height="15" viewBox="0 0 24 24" aria-hidden="true">
      <path
        d="M16.5 3.2A8.8 8.8 0 1 0 20.8 16 7 7 0 0 1 16.5 3.2Z"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinejoin="round"
      />
    </svg>
  );
}
