"""Policy and law packs in Postgres. `--pack pg:saas` and `--law-pack pg:us-law` read a pack from
here and give the same validated objects as the YAML, so nothing past `load` knows the difference.

The YAML files stay the reviewed source: `cc db seed` copies them in, and `cc db status` names
any pack whose rows no longer match, so a benchmark never drifts through an edited row. Each row
keeps the whole rule as JSON (`data`); the other columns are generated from it for querying and
cannot disagree with it. Needs `pip install -e '.[db]'` and DATABASE_URL, in the environment or
in `.env`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..env import env_value

SCHEMA = """
CREATE TABLE IF NOT EXISTS packs (
    slug text PRIMARY KEY,
    kind text NOT NULL CHECK (kind IN ('policy', 'law')),
    name text NOT NULL,
    version text NOT NULL,
    meta jsonb NOT NULL,
    seeded_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS rules (
    pack text NOT NULL REFERENCES packs (slug) ON DELETE CASCADE,
    id text NOT NULL,
    pos integer NOT NULL,
    data jsonb NOT NULL,
    title text GENERATED ALWAYS AS (data->>'title') STORED,
    requirement text GENERATED ALWAYS AS (data->>'requirement') STORED,
    kind text GENERATED ALWAYS AS (data->>'kind') STORED,
    applies_if text GENERATED ALWAYS AS (data->>'applies_if') STORED,
    severity text GENERATED ALWAYS AS (data->>'severity') STORED,
    approval text GENERATED ALWAYS AS (data->>'approval') STORED,
    hypothesis text GENERATED ALWAYS AS (data#>>'{anchor,hypothesis}') STORED,
    PRIMARY KEY (pack, id)  -- ids like P-01 repeat across companies
);
CREATE TABLE IF NOT EXISTS law_provisions (
    pack text NOT NULL REFERENCES packs (slug) ON DELETE CASCADE,
    id text NOT NULL,
    pos integer NOT NULL,
    data jsonb NOT NULL,
    act text GENERATED ALWAYS AS (data->>'act') STORED,
    section text GENERATED ALWAYS AS (data->>'section') STORED,
    title text GENERATED ALWAYS AS (data->>'title') STORED,
    summary text GENERATED ALWAYS AS (data->>'summary') STORED,
    kind text GENERATED ALWAYS AS (data->>'kind') STORED,
    risk_level text GENERATED ALWAYS AS (data->>'risk_level') STORED,
    severity text GENERATED ALWAYS AS (data->>'severity') STORED,
    source_url text GENERATED ALWAYS AS (data->>'source_url') STORED,
    n_checked integer GENERATED ALWAYS AS (jsonb_array_length(data->'checked_by')) STORED,
    PRIMARY KEY (pack, id)
);
CREATE TABLE IF NOT EXISTS documents (
    pack text NOT NULL REFERENCES packs (slug) ON DELETE CASCADE,
    name text NOT NULL,
    body text NOT NULL,
    PRIMARY KEY (pack, name)
);
"""

TABLES = {"policy": ("rules", "rules"), "law": ("law_provisions", "provisions")}  # kind -> table, list field


def database_url() -> str:
    url = env_value("DATABASE_URL")
    if not url:
        raise RuntimeError("set DATABASE_URL, in the environment or in .env (see .env.example)")
    return url


def connect(url: str | None = None):
    try:
        import psycopg
    except ImportError as e:  # pragma: no cover
        raise ImportError("pip install -e '.[db]' to use Postgres packs") from e
    return psycopg.connect(url or database_url())


def discover(root: str | Path = "packs") -> list[tuple[str, str, Path, list[Path]]]:
    """(slug, kind, YAML file, documents) of every pack that belongs in the database."""
    root = Path(root)
    out = [(d.name, "policy", d / "gold_rules.yaml", sorted((d / "policies").glob("*.md")))
           for d in sorted((root / "policynda").iterdir()) if (d / "gold_rules.yaml").exists()]
    law = root / "law"
    return out + [("us-law", "law", law / "us_law_pack.yaml", [law / "us_law_sources.md"])]


def seed_pack(conn, slug: str, kind: str, pack: Any, docs: list[Path]) -> None:
    """Replace one pack's rows. The caller's transaction makes a failed seed change nothing."""
    from psycopg.types.json import Jsonb

    meta = pack.model_dump(mode="json")
    table, field = TABLES[kind]
    items = meta.pop(field)
    conn.execute("INSERT INTO packs (slug, kind, name, version, meta) VALUES (%s, %s, %s, %s, %s) "
                 "ON CONFLICT (slug) DO UPDATE SET kind = excluded.kind, name = excluded.name, "
                 "version = excluded.version, meta = excluded.meta, seeded_at = now()",
                 (slug, kind, meta.get("company") or meta["jurisdiction"], meta["version"], Jsonb(meta)))
    conn.execute(f"DELETE FROM {table} WHERE pack = %s", (slug,))
    conn.execute("DELETE FROM documents WHERE pack = %s", (slug,))
    with conn.cursor() as cur:
        cur.executemany(f"INSERT INTO {table} (pack, id, pos, data) VALUES (%s, %s, %s, %s)",
                        [(slug, x["id"], i, Jsonb(x)) for i, x in enumerate(items)])
        cur.executemany("INSERT INTO documents (pack, name, body) VALUES (%s, %s, %s)",
                        [(slug, d.name, d.read_text(encoding="utf-8")) for d in docs])


def fetch_pack(conn, slug: str, kind: str) -> dict:
    row = conn.execute("SELECT kind, meta FROM packs WHERE slug = %s", (slug,)).fetchone()
    if row is None or row[0] != kind:
        raise ValueError(f"no {kind} pack {slug!r} in the database; `cc db status` lists them")
    table, field = TABLES[kind]
    items = conn.execute(f"SELECT data FROM {table} WHERE pack = %s ORDER BY pos", (slug,)).fetchall()
    return {**row[1], field: [r[0] for r in items]}


def load_pack(slug: str, kind: str) -> dict:
    with connect() as conn:
        return fetch_pack(conn, slug, kind)


def _model(kind: str):
    from .schema import LawPack, PolicyPack

    return PolicyPack if kind == "policy" else LawPack


def seed(root: str | Path = "packs", conn=None) -> list[str]:
    """Validate every YAML pack and copy them all in, in one transaction."""
    packs = [(slug, kind, _model(kind).load(path), docs) for slug, kind, path, docs in discover(root)]
    if conn is None:
        with connect() as c:
            return seed(root, c)
    conn.execute(SCHEMA)
    for slug, kind, pack, docs in packs:
        seed_pack(conn, slug, kind, pack, docs)
    return [f"{slug}: {len(getattr(pack, TABLES[kind][1]))} {TABLES[kind][1]}, {len(docs)} documents"
            for slug, kind, pack, docs in packs]


def status(root: str | Path = "packs", conn=None) -> list[str]:
    """One line per pack: what the database holds and whether it still matches the YAML."""
    if conn is None:
        with connect() as c:
            return status(root, c)
    if conn.execute("SELECT to_regclass('packs')").fetchone()[0] is None:
        return ["database is empty; run `cc db seed`"]
    lines = []
    for slug, kind, path, _ in discover(root):
        model = _model(kind)
        try:
            held = model.model_validate(fetch_pack(conn, slug, kind))
        except ValueError as e:
            lines.append(f"{slug}: {e}")
            continue
        same = "matches" if held == model.load(path) else "DIFFERS FROM"
        lines.append(f"{slug}: {len(getattr(held, TABLES[kind][1]))} {TABLES[kind][1]}, {same} {path.as_posix()}")
    return lines
