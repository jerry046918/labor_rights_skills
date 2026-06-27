"""Shared pytest fixtures for scripts/tests."""
import json
from pathlib import Path

import pytest

SKILL_ROOT = Path(__file__).resolve().parents[2]
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


@pytest.fixture
def sample_hotwords() -> list[str]:
    return ["解除", "劳动合同", "经济补偿", "N+1", "赔偿金", "违法解除"]


@pytest.fixture
def tmp_evidence_dir(tmp_path: Path) -> Path:
    d = tmp_path / "evidence" / "test_audio_2026-06-27"
    d.mkdir(parents=True)
    return d
