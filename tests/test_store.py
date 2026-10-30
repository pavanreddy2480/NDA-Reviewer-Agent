"""The database tests need a real Postgres: set CC_TEST_DATABASE_URL to run them. They work in a
throwaway schema, so they never touch a seeded database."""

from pathlib import Path
import os
import uuid

import pytest

from counselcopilot.policy import store
from counselcopilot.policy.schema import LawPack, PolicyPack

ROOT = Path(__file__).resolve().parents[1]
TOY_PACK = ROOT / "packs" / "toy" / "toy_pack.yaml"

PACKS = ROOT / "packs"
TEST_URL = os.environ.get("CC_TEST_DATABASE_URL")
needs_db = pytest.mark.skipif(not TEST_URL, reason="CC_TEST_DATABASE_URL not set")


def test_discover_finds_the_three_companies_and_the_law_pack():
    found = {slug: (kind, path, docs) for slug, kind, path, docs in store.discover(PACKS)}
    assert set(found) == {"saas", "hospital", "manufacturer", "us-law"}  # no toy pack, no archived India pack
    assert found["us-law"][0] == "law" and found["us-law"][2][0].name == "us_law_sources.md"
    assert sum(len(docs) for kind, _, docs in found.values() if kind == "policy") == 33


def test_url_comes_from_the_environment_first(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text("OTHER=1\nDATABASE_URL='postgresql://from-file'\n", encoding="utf-8")
    monkeypatch.setenv("DATABASE_URL", "postgresql://from-env")
    assert store.database_url() == "postgresql://from-env"
    monkeypatch.delenv("DATABASE_URL")
    assert store.database_url() == "postgresql://from-file"


def test_missing_url_says_what_to_do(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        store.database_url()


def test_pg_prefix_goes_to_the_store(monkeypatch):
    monkeypatch.setattr(store, "load_pack", lambda slug, kind: {"company": slug, "rules": []})
    assert PolicyPack.load("pg:saas").company == "saas"


@pytest.fixture
def conn():
    import psycopg

    schema = f"cc_test_{uuid.uuid4().hex[:10]}"
    with psycopg.connect(TEST_URL, autocommit=True) as c:
        c.execute(f"CREATE SCHEMA {schema}")
        c.execute(f"SET search_path TO {schema}")
        try:
            yield c
        finally:
            c.execute(f"DROP SCHEMA {schema} CASCADE")


@needs_db
def test_seed_round_trips_every_pack_exactly(conn):
    store.seed(PACKS, conn)
    for slug, kind, path, _ in store.discover(PACKS):
        model = PolicyPack if kind == "policy" else LawPack
        assert model.model_validate(store.fetch_pack(conn, slug, kind)) == model.load(path)
    assert conn.execute("SELECT count(*) FROM rules").fetchone()[0] == 90
    assert conn.execute("SELECT count(*) FROM law_provisions").fetchone()[0] == 7
    assert conn.execute("SELECT count(*) FROM documents").fetchone()[0] == 34


@needs_db
def test_generated_columns_can_be_queried(conn):
    store.seed(PACKS, conn)
    assert conn.execute("SELECT title, hypothesis FROM rules WHERE pack = 'saas' AND id = 'P-01'").fetchone() == (
        "Use limited to the stated purpose", "nda-4")
    assert conn.execute("SELECT count(*) FROM law_provisions WHERE n_checked < 2").fetchone()[0] == 7


@needs_db
def test_seed_twice_replaces_and_status_reports_drift(conn):
    store.seed(PACKS, conn)
    store.seed(PACKS, conn)
    assert conn.execute("SELECT count(*) FROM rules").fetchone()[0] == 90
    assert all("matches" in line for line in store.status(PACKS, conn))
    conn.execute("""UPDATE rules SET data = jsonb_set(data, '{title}', '"edited"')
                    WHERE pack = 'saas' AND id = 'P-01'""")
    assert [line.split(":")[0] for line in store.status(PACKS, conn) if "DIFFERS" in line] == ["saas"]


@needs_db
def test_wrong_kind_or_slug_is_refused(conn):
    store.seed(PACKS, conn)
    with pytest.raises(ValueError, match="no policy pack"):
        store.fetch_pack(conn, "us-law", "policy")
    with pytest.raises(ValueError, match="no law pack"):
        store.fetch_pack(conn, "nope", "law")
