import type { LeaderboardEntry } from "../api";
import { plural } from "../plural";

interface Props {
  entries: LeaderboardEntry[];
  currentUsername?: string;
}

export function Leaderboard({ entries, currentUsername }: Props) {
  return (
    <aside className="card leaderboard">
      <h2>Лидеры дня</h2>
      {entries.length === 0 ? (
        <p className="muted">Пока никто не отгадал. Будьте первым!</p>
      ) : (
        <ol>
          {entries.map((e) => (
            <li key={e.rank} className={e.username === currentUsername ? "me" : undefined}>
              <span className="rank">{e.rank}</span>
              <img src={e.avatar_url} alt="" width={28} height={28} />
              <span className="name">{e.username}</span>
              <span className="tries" title={`Отгадано в ${new Date(e.solved_at).toLocaleTimeString()}`}>
                {e.n_of_tries} {plural(e.n_of_tries, ["попытка", "попытки", "попыток"])}
              </span>
              {e.hints_used > 0 && (
                <span
                  className="hint-badge"
                  title={`${e.hints_used} ${plural(e.hints_used, ["подсказка", "подсказки", "подсказок"])}, учтены в попытках`}
                >
                  💡{e.hints_used}
                </span>
              )}
            </li>
          ))}
        </ol>
      )}
    </aside>
  );
}
