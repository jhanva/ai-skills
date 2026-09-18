"""
catalog.py — Indice BM25 sobre los catalogos CSV del plugin design.

Sin dependencias externas. Lo usa search.py; los tests lo importan directo.
Cada catalogo es un CSV con columna `id` y columna `keywords`; el resto de
columnas de texto tambien se indexan, con menos peso que `keywords`.
"""

import csv
import math
import re
import unicodedata
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# dominio -> (archivo, columnas indexadas, columnas con peso extra)
DOMAINS = {
    "style": ("styles.csv", ("nombre", "resumen", "cuando_usar", "efectos"), ("keywords", "nombre")),
    "palette": ("palettes.csv", ("dominio", "mood", "notas_contraste"), ("keywords", "dominio")),
    "typography": ("typography.csv", ("titulos", "cuerpo", "mood", "cuando_usar", "notas"), ("keywords", "mood")),
    "ux": ("ux-guidelines.csv", ("categoria", "regla", "criterio", "anti_patron"), ("keywords", "categoria")),
    "motion": ("motion.csv", ("nombre", "uso", "reduced_motion"), ("keywords", "nombre")),
    "stack": (None, ("tema", "regla", "implementacion", "anti_patron"), ("keywords", "tema")),
}
STACKS = ("compose", "web")

STOPWORDS = {
    "de", "la", "el", "los", "las", "un", "una", "y", "o", "en", "para", "con", "sin", "por",
    "que", "del", "al", "se", "es", "su", "sus", "the", "a", "an", "of", "for", "and", "or",
    "in", "on", "to", "app", "aplicacion",
}

# Umbral de score relativo: por debajo de esta fraccion del mejor score
# posible (todos los terminos presentes) el resultado se considera ruido.
MIN_COVERAGE = 0.34


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    return text.lower()


def tokenize(text: str) -> list:
    tokens = re.findall(r"[a-z0-9]+", normalize(text))
    return [_stem(t) for t in tokens if t not in STOPWORDS and len(t) > 1]


def _stem(token: str) -> str:
    # Stemming minimo para espanol: plurales y sufijos frecuentes.
    for suffix in ("ciones", "cion", "mente", "es", "s"):
        if token.endswith(suffix) and len(token) - len(suffix) >= 3:
            return token[: -len(suffix)]
    return token


class BM25:
    def __init__(self, k1: float = 1.4, b: float = 0.75):
        self.k1, self.b = k1, b
        self.docs = []          # list de dict (filas)
        self.doc_terms = []     # list de dict term -> freq
        self.doc_len = []
        self.df = {}
        self.avg_len = 0.0

    def add(self, row: dict, fields, boosted) -> None:
        terms = {}
        for column in fields + tuple(boosted):
            weight = 2 if column in boosted else 1
            for token in tokenize(row.get(column, "")):
                terms[token] = terms.get(token, 0) + weight
        self.docs.append(row)
        self.doc_terms.append(terms)
        self.doc_len.append(sum(terms.values()))
        for term in terms:
            self.df[term] = self.df.get(term, 0) + 1
        self.avg_len = sum(self.doc_len) / len(self.doc_len)

    def _idf(self, term: str) -> float:
        n, df = len(self.docs), self.df.get(term, 0)
        return math.log(1 + (n - df + 0.5) / (df + 0.5))

    def score(self, query: str) -> list:
        q_terms = tokenize(query)
        if not q_terms:
            return []
        known = [t for t in q_terms if t in self.df]
        if not known:
            return []
        scored = []
        for i, terms in enumerate(self.doc_terms):
            score, matched = 0.0, 0
            norm = self.k1 * (1 - self.b + self.b * self.doc_len[i] / self.avg_len)
            for term in known:
                freq = terms.get(term, 0)
                if not freq:
                    continue
                matched += 1
                score += self._idf(term) * freq * (self.k1 + 1) / (freq + norm)
            if score > 0:
                # Cobertura sobre los terminos que este catalogo conoce: una
                # palabra ajena al dominio no penaliza, una query sin ninguna
                # palabra conocida no devuelve nada.
                coverage = matched / len(known)
                scored.append((score * (0.5 + coverage), coverage, i))
        scored.sort(key=lambda s: (-s[0], self.docs[s[2]]["id"]))
        return [(s, c, self.docs[i]) for s, c, i in scored]

    def suggest(self, query: str, limit: int = 5) -> list:
        """Terminos del vocabulario que se parecen a los de la query (prefijo comun)."""
        wanted = tokenize(query)
        found = []
        for term in sorted(self.df, key=lambda t: -self.df[t]):
            if any(term[:3] == w[:3] for w in wanted) and term not in wanted:
                found.append(term)
            if len(found) >= limit:
                break
        return found


_INDEX_CACHE = {}


def catalog_path(domain: str, stack=None) -> Path:
    if domain == "stack":
        if stack not in STACKS:
            raise ValueError(f"stack desconocido: {stack!r}; validos: {', '.join(STACKS)}")
        return DATA_DIR / "stacks" / f"{stack}.csv"
    if domain not in DOMAINS:
        raise ValueError(f"dominio desconocido: {domain!r}; validos: {', '.join(DOMAINS)}")
    return DATA_DIR / DOMAINS[domain][0]


def load_rows(path: Path) -> list:
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def index(domain: str, stack=None) -> BM25:
    path = catalog_path(domain, stack)
    key = (str(path), path.stat().st_mtime_ns)
    if key not in _INDEX_CACHE:
        _, fields, boosted = DOMAINS[domain]
        bm25 = BM25()
        for row in load_rows(path):
            bm25.add(row, fields, boosted)
        _INDEX_CACHE[key] = bm25
    return _INDEX_CACHE[key]


def search(query: str, domain: str, stack=None, limit: int = 5, min_coverage: float = MIN_COVERAGE) -> list:
    """Filas del catalogo ordenadas por relevancia; vacio si nada supera el umbral."""
    bm25 = index(domain, stack)
    hits = []
    for score, coverage, row in bm25.score(query):
        if coverage < min_coverage:
            continue
        hit = dict(row)
        hit["_score"] = round(score, 3)
        hit["_coverage"] = round(coverage, 2)
        hits.append(hit)
        if len(hits) >= limit:
            break
    return hits


def suggest(query: str, domain: str, stack=None) -> list:
    return index(domain, stack).suggest(query)


# ---- utilidades de color ----

def _srgb_to_linear(channel: float) -> float:
    channel /= 255.0
    return channel / 12.92 if channel <= 0.03928 else ((channel + 0.055) / 1.055) ** 2.4


def luminance(hex_color: str) -> float:
    value = hex_color.lstrip("#")
    r, g, b = (int(value[i:i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * _srgb_to_linear(r) + 0.7152 * _srgb_to_linear(g) + 0.0722 * _srgb_to_linear(b)


def contrast_ratio(fg: str, bg: str) -> float:
    l1, l2 = sorted((luminance(fg), luminance(bg)), reverse=True)
    return round((l1 + 0.05) / (l2 + 0.05), 2)
