export type Status = "correct" | "present" | "absent";

export interface Letter {
  letter: string;
  status: Status;
}

export interface User {
  id: number;
  username: string;
  avatar_url: string;
}

export interface LetterHint {
  position: number;
  letter: string;
}

export interface Hints {
  used: number;
  letters: LetterHint[];
}

export interface GameState {
  word_length: number;
  n_of_tries: number;
  solved: boolean;
  guesses: Letter[][];
  hints: Hints;
}

export interface HintResponse {
  n_of_tries: number;
  hints: Hints;
}

export interface GuessResult {
  letters: Letter[];
  n_of_tries: number;
  solved: boolean;
}

export interface LeaderboardEntry {
  rank: number;
  username: string;
  avatar_url: string;
  n_of_tries: number;
  hints_used: number;
  solved_at: string;
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

export const LOGIN_URL = "/api/auth/discord/login";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`/api${path}`, {
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      ...init,
    });
  } catch {
    throw new ApiError(0, "Сервер недоступен");
  }

  if (!response.ok) {
    let message = response.statusText || "Ошибка сервера";
    try {
      const body = await response.json();
      if (typeof body.detail === "string") message = body.detail;
      else if (Array.isArray(body.detail) && body.detail[0]?.msg) message = body.detail[0].msg;
    } catch {
      if (response.status >= 500) message = "Сервер недоступен";
    }
    throw new ApiError(response.status, message);
  }

  if (response.status === 204) return undefined as T;
  return response.json();
}

export const api = {
  me: () => request<User>("/auth/me"),
  logout: () => request<void>("/auth/logout", { method: "POST" }),
  wordLength: () => request<number>("/progle/word_length"),
  game: () => request<GameState>("/progle/game"),
  guess: (word: string) =>
    request<GuessResult>("/progle/guess", { method: "POST", body: JSON.stringify({ word }) }),
  takeHint: (level: 1 | 2) => request<HintResponse>(`/progle/hints/${level}`, { method: "POST" }),
  leaderboard: () => request<LeaderboardEntry[]>("/progle/leaderboard"),
};
