import type { Status } from "../api";

const ROWS = ["qwertyuiop", "asdfghjkl", "zxcvbnm"];

interface Props {
  statuses: Record<string, Status>;
  disabled: boolean;
  onLetter: (letter: string) => void;
  onEnter: () => void;
  onBackspace: () => void;
}

export function Keyboard({ statuses, disabled, onLetter, onEnter, onBackspace }: Props) {
  return (
    <div className="keyboard" aria-label="Клавиатура">
      {ROWS.map((row, r) => (
        <div className="keyboard-row" key={row}>
          {r === 2 && (
            <button className="key wide" onClick={onEnter} disabled={disabled}>
              Enter
            </button>
          )}
          {[...row].map((letter) => (
            <button
              key={letter}
              className={`key ${statuses[letter] ?? ""}`}
              onClick={() => onLetter(letter)}
              disabled={disabled}
            >
              {letter}
            </button>
          ))}
          {r === 2 && (
            <button className="key wide" onClick={onBackspace} disabled={disabled} aria-label="Стереть">
              ⌫
            </button>
          )}
        </div>
      ))}
    </div>
  );
}
