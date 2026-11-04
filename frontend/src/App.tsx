import { useCallback, useEffect, useMemo, useState } from "react";

import { api, ApiError, LOGIN_URL, type GameState, type LeaderboardEntry, type Status, type User } from "./api";
import { Board } from "./components/Board";
import { Countdown } from "./components/Countdown";
import { HintButton } from "./components/HintButton";
import { Keyboard } from "./components/Keyboard";
import { Leaderboard } from "./components/Leaderboard";
import { Settings } from "./components/Settings";
import { plural } from "./plural";

interface Toast {
  id: number;
  text: string;
}

const STATUS_RANK: Record<Status, number> = { absent: 1, present: 2, correct: 3 };

export default function App() {
  const [user, setUser] = useState<User | null | undefined>(undefined);
  const [wordLength, setWordLength] = useState<number | null>(null);
  const [game, setGame] = useState<GameState | null>(null);
  const [current, setCurrent] = useState("");
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [toast, setToast] = useState<Toast | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [animateRow, setAnimateRow] = useState<number | null>(null);
  const [shake, setShake] = useState(0);
  const [hintLoading, setHintLoading] = useState<1 | 2 | null>(null);

  const showToast = useCallback((text: string) => setToast({ id: Date.now(), text }), []);

  const refreshLeaderboard = useCallback(() => {
    api.leaderboard().then(setLeaderboard).catch(() => {});
  }, []);

  useEffect(() => {
    if (!toast) return;
    const id = setTimeout(() => setToast(null), 2500);
    return () => clearTimeout(id);
  }, [toast]);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.has("auth_error")) {
      showToast("Вход через Discord отменён");
      window.history.replaceState(null, "", window.location.pathname);
    }

    api.me().then(setUser).catch(() => setUser(null));
    api
      .wordLength()
      .then(setWordLength)
      .catch((e: ApiError) => setLoadError(e.message));
    refreshLeaderboard();
  }, [showToast, refreshLeaderboard]);

  useEffect(() => {
    if (!user) {
      setGame(null);
      return;
    }
    api
      .game()
      .then((g) => {
        setGame(g);
        setWordLength(g.word_length);
      })
      .catch((e: ApiError) => showToast(e.message));
  }, [user, showToast]);

  const length = game?.word_length ?? wordLength;
  const canType = Boolean(user && game && !game.solved && !submitting);

  const keyStatuses = useMemo(() => {
    const result: Record<string, Status> = {};
    for (const row of game?.guesses ?? []) {
      for (const { letter, status } of row) {
        if (!result[letter] || STATUS_RANK[status] > STATUS_RANK[result[letter]]) result[letter] = status;
      }
    }
    return result;
  }, [game?.guesses]);

  const addLetter = (letter: string) => {
    if (!canType || !length) return;
    setCurrent((c) => (c.length < length ? c + letter : c));
  };

  const removeLetter = () => {
    if (!canType) return;
    setCurrent((c) => c.slice(0, -1));
  };

  const submit = async () => {
    if (!canType || !game || !length) return;
    if (current.length !== length) {
      showToast(`Нужно ${length} ${plural(length, ["буква", "буквы", "букв"])}`);
      setShake((s) => s + 1);
      return;
    }

    setSubmitting(true);
    try {
      const result = await api.guess(current);
      setAnimateRow(game.guesses.length);
      setGame({
        ...game,
        guesses: [...game.guesses, result.letters],
        n_of_tries: result.n_of_tries,
        solved: result.solved,
      });
      setCurrent("");
      if (result.solved) refreshLeaderboard();
    } catch (e) {
      const error = e as ApiError;
      if (error.status === 401) setUser(null);
      if (error.status === 409) api.game().then(setGame).catch(() => {});
      showToast(error.message);
      setShake((s) => s + 1);
    } finally {
      setSubmitting(false);
    }
  };

  const takeHint = async (level: 1 | 2) => {
    if (!game || hintLoading) return;
    setHintLoading(level);
    try {
      const result = await api.takeHint(level);
      setGame((g) => g && { ...g, n_of_tries: result.n_of_tries, hints: result.hints });
    } catch (e) {
      const error = e as ApiError;
      if (error.status === 401) setUser(null);
      if (error.status === 409) api.game().then(setGame).catch(() => {});
      showToast(error.message);
    } finally {
      setHintLoading(null);
    }
  };

  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if (e.ctrlKey || e.metaKey || e.altKey) return;
      if (e.target instanceof Element && e.target.closest(".settings, .hint-menu")) return;
      const letter = /^Key([A-Z])$/.exec(e.code)?.[1];
      if (e.key === "Enter") {
        e.preventDefault();
        submit();
      } else if (e.key === "Backspace") {
        removeLetter();
      } else if (letter) {
        addLetter(letter.toLowerCase());
      }
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  });

  const logout = async () => {
    await api.logout().catch(() => {});
    setUser(null);
    setCurrent("");
  };

  return (
    <div className="app">
      <header className="header">
        <div className="brand">
          <img className="logo" src="/logo.svg" alt="" width={40} height={40} />
          <div>
            <h1>Progle</h1>
            <p>угадай слово из проги</p>
          </div>
        </div>

        <div className="header-actions">
          {user === undefined ? null : user ? (
            <div className="user">
              <img src={user.avatar_url} alt="" width={32} height={32} />
              <span className="user-name">{user.username}</span>
              <button className="btn ghost" onClick={logout}>
                Выйти
              </button>
            </div>
          ) : (
            <a className="btn discord" href={LOGIN_URL}>
              Войти через Discord
            </a>
          )}
          {user && game && (
            <HintButton
              hints={game.hints}
              solved={game.solved}
              loading={hintLoading !== null}
              onTake={takeHint}
            />
          )}
          <Settings />
        </div>
      </header>

      <main className="layout">
        <section className="game">
          {loadError ? (
            <div className="card notice">
              <strong>{loadError}</strong>
              <p className="muted">Попробуйте обновить страницу чуть позже.</p>
            </div>
          ) : !length ? (
            <p className="muted center">Загрузка…</p>
          ) : (
            <>
              <div className="game-info">
                <span>
                  Термин дня: <strong>{length}</strong> {plural(length, ["буква", "буквы", "букв"])}
                </span>
                {game && (
                  <span>
                    Попыток: <strong>{game.n_of_tries}</strong>
                    {game.hints.used > 0 && ` (из них ${game.hints.used} за подсказки)`}
                  </span>
                )}
              </div>

              <Board
                wordLength={length}
                guesses={game?.guesses ?? []}
                current={current}
                showInput={!game?.solved}
                animateRow={animateRow}
                shake={shake}
                hints={game?.hints.letters ?? []}
              />

              {user === null && (
                <div className="card notice">
                  <strong>Войдите, чтобы играть</strong>
                  <p className="muted">Попытки и рекорды привязываются к вашему аккаунту Discord.</p>
                  <a className="btn discord" href={LOGIN_URL}>
                    Войти через Discord
                  </a>
                </div>
              )}

              {game?.solved && (
                <div className="card notice success">
                  <strong>
                    Отгадано за {game.n_of_tries} {plural(game.n_of_tries, ["попытку", "попытки", "попыток"])}!
                  </strong>
                  <p className="muted">
                    Новое слово через <Countdown />
                  </p>
                </div>
              )}

              {user && game && !game.solved && (
                <Keyboard
                  statuses={keyStatuses}
                  disabled={!canType}
                  onLetter={addLetter}
                  onEnter={submit}
                  onBackspace={removeLetter}
                />
              )}
            </>
          )}
        </section>

        <Leaderboard entries={leaderboard} currentUsername={user?.username} />
      </main>

      {toast && (
        <div className="toast" key={toast.id} role="status">
          {toast.text}
        </div>
      )}
    </div>
  );
}
