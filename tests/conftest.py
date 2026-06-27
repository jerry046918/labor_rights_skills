"""Shared pytest fixtures for tests/ directory."""
from pathlib import Path

import pytest

SKILL_ROOT = Path(__file__).resolve().parent.parent
FIXTURES_DIR = SKILL_ROOT / "tests" / "fixtures"


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES_DIR


@pytest.fixture
def dismissal_audio(fixtures_dir: Path) -> Path:
    p = fixtures_dir / "dismissal_2speakers.mp3"
    if not p.exists():
        pytest.skip(f"Fixture missing: {p}. Run generate_fixtures.py first.")
    return p


@pytest.fixture
def conflict_audio(fixtures_dir: Path) -> Path:
    p = fixtures_dir / "cross_role_conflict.mp3"
    if not p.exists():
        pytest.skip(f"Fixture missing: {p}. Run generate_fixtures.py first.")
    return p
