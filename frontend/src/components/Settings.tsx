import { useState } from "react";

import { applyTheme, loadTheme, type Theme } from "../theme";
import { usePopover } from "../usePopover";

const THEMES: { value: Theme; label: string }[] = [
  { value: "system", label: "Системная" },
  { value: "light", label: "Светлая" },
  { value: "dark", label: "Тёмная" },
];

export function Settings() {
  const { open, setOpen, rootRef } = usePopover<HTMLDivElement>();
  const [theme, setTheme] = useState<Theme>(loadTheme);

  const chooseTheme = (value: Theme) => {
    setTheme(value);
    applyTheme(value);
  };

  return (
    <div className="settings" ref={rootRef}>
      <button
        className="icon-btn"
        aria-label="Настройки"
        aria-expanded={open}
        aria-haspopup="dialog"
        onClick={() => setOpen((o) => !o)}
      >
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true">
          <path d="M4 6h10M18 6h2M4 12h4M12 12h8M4 18h12" />
          <circle cx="16" cy="6" r="2" />
          <circle cx="10" cy="12" r="2" />
          <circle cx="18" cy="18" r="2" />
        </svg>
      </button>

      {open && (
        <div className="popover" role="dialog" aria-label="Настройки">
          <h3>Настройки</h3>
          <div className="setting">
            <span className="setting-label" id="theme-label">
              Тема
            </span>
            <div className="segmented" role="radiogroup" aria-labelledby="theme-label">
              {THEMES.map(({ value, label }) => (
                <button key={value} role="radio" aria-checked={theme === value} onClick={() => chooseTheme(value)}>
                  {label}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
