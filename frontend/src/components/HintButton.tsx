import type { Hints } from "../api";
import { usePopover } from "../usePopover";

export const HINTS_TOTAL = 2;

interface Props {
  hints: Hints;
  solved: boolean;
  loading: boolean;
  onTake: (level: 1 | 2) => void;
}

export function HintButton({ hints, solved, loading, onTake }: Props) {
  const { open, setOpen, rootRef } = usePopover<HTMLDivElement>();
  const remaining = HINTS_TOTAL - hints.used;
  const canTake = remaining > 0 && !solved;

  return (
    <div className="hint-menu" ref={rootRef}>
      <button
        className="icon-btn"
        aria-label={`Подсказки: осталось ${remaining} из ${HINTS_TOTAL}`}
        aria-expanded={open}
        aria-haspopup="dialog"
        disabled={solved && hints.used === 0}
        onClick={() => setOpen((o) => !o)}
      >
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <path d="M15 14c.2-1 .7-1.7 1.5-2.5 1-.9 1.5-2.2 1.5-3.5A6 6 0 0 0 6 8c0 1 .2 2.2 1.5 3.5.7.7 1.3 1.5 1.5 2.5" />
          <path d="M9 18h6" />
          <path d="M10 22h4" />
        </svg>
        {canTake && <span className="icon-badge">{remaining}</span>}
      </button>

      {open && (
        <div className="popover" role="dialog" aria-label="Подсказки">
          <h3>Подсказки</h3>
          <p className="popover-note">Каждая открывает одну букву на её месте и стоит +1 попытку.</p>

          {hints.letters.length > 0 && (
            <ul className="hint-list">
              {hints.letters.map((h) => (
                <li key={h.position}>
                  <span className="hint-letter">{h.letter}</span> на {h.position + 1}-м месте
                </li>
              ))}
            </ul>
          )}

          {canTake ? (
            <button className="btn hint-take" onClick={() => onTake((hints.used + 1) as 1 | 2)} disabled={loading}>
              {loading ? "Открываем…" : "Открыть букву · +1 попытка"}
            </button>
          ) : (
            <p className="popover-note">{solved ? "Слово уже отгадано" : "Подсказки на сегодня закончились"}</p>
          )}
        </div>
      )}
    </div>
  );
}
