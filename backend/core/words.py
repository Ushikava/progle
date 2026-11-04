import gzip
import json
from functools import cache
from pathlib import Path

WORDS_FILE = Path(__file__).resolve().parent.parent / "words.json"
DICTIONARY_FILE = Path(__file__).resolve().parent.parent / "dictionary.txt.gz"


@cache
def load_words() -> tuple[str, ...]:
    data = json.loads(WORDS_FILE.read_text(encoding="utf-8"))
    if not isinstance(data, list) or not all(isinstance(w, str) for w in data):
        raise RuntimeError(f"{WORDS_FILE.name} должен быть списком строк")

    words = tuple(dict.fromkeys(w.strip().lower() for w in data))
    bad = [w for w in words if not w.isalpha()]
    if bad:
        raise RuntimeError(f"{WORDS_FILE.name}: слова должны состоять только из букв: {bad}")
    if not words:
        raise RuntimeError(f"{WORDS_FILE.name} пуст")
    return words


@cache
def load_dictionary() -> frozenset[str]:
    with gzip.open(DICTIONARY_FILE, "rt", encoding="ascii") as f:
        words = {line.strip() for line in f if line.strip()}
    return frozenset(words.union(load_words()))


def is_known_word(word: str) -> bool:
    return word in load_dictionary()
