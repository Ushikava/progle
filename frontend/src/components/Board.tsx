import { useEffect, useRef, type CSSProperties } from "react";

import type { Letter, LetterHint } from "../api";

interface Props {
  wordLength: number;
  guesses: Letter[][];
  current: string;
  showInput: boolean;
  animateRow: number | null;
  shake: number;
  hints: LetterHint[];
}

export function Board({ wordLength, guesses, current, showInput, animateRow, shake, hints }: Props) {
  const inputRowRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    inputRowRef.current?.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }, [guesses.length]);

  const flipDelay = Math.min(120, 600 / wordLength);

  return (
    <div className="board" style={{ "--len": wordLength } as CSSProperties}>
      {guesses.map((row, r) => (
        <div className="row" key={r}>
          {row.map((l, i) => (
            <div
              key={i}
              className={`tile ${l.status}${r === animateRow ? " flip" : ""}`}
              style={r === animateRow ? { animationDelay: `${i * flipDelay}ms` } : undefined}
            >
              {l.letter}
            </div>
          ))}
        </div>
      ))}

      {showInput && (
        <div className={`row${shake ? " shake" : ""}`} key={`input-${shake}`} ref={inputRowRef}>
          {Array.from({ length: wordLength }, (_, i) => {
            const ghost = current[i] ? undefined : hints.find((h) => h.position === i);
            return (
              <div key={i} className={`tile input${current[i] ? " filled" : ""}${ghost ? " ghost" : ""}`}>
                {current[i] ?? ghost?.letter ?? ""}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
