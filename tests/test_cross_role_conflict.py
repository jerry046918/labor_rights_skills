"""Tests for cross-role conflict detection logic."""
from scripts.conflict_detection import detect_cross_role_conflicts


def test_no_conflict_when_single_company_speaker():
    cards = [
        {"speaker_role": "HR/人力资源", "evidence_type": "解除意思表示", "quote": "已解除"},
        {"speaker_role": "员工本人", "evidence_type": "解除意思表示", "quote": "我反对"},
    ]
    result = detect_cross_role_conflicts(cards)
    assert all(c["cross_role_conflict"] is False for c in result)


def test_conflict_when_two_company_speakers_same_type():
    """Supervisor says no dismissal + HR says dismissed = conflict."""
    cards = [
        {"speaker_role": "直属主管", "evidence_type": "解除意思表示", "quote": "没说要辞你"},
        {"speaker_role": "HR/人力资源", "evidence_type": "解除意思表示", "quote": "公司已决定解除"},
        {"speaker_role": "员工本人", "evidence_type": "解除意思表示", "quote": "到底辞不辞"},
    ]
    result = detect_cross_role_conflicts(cards)
    company_cards = [c for c in result if c["speaker_role"] != "员工本人"]
    assert all(c["cross_role_conflict"] is True for c in company_cards)
    employee_card = next(c for c in result if c["speaker_role"] == "员工本人")
    assert employee_card["cross_role_conflict"] is False


def test_no_conflict_across_different_evidence_types():
    """Same speakers, different evidence types = no conflict."""
    cards = [
        {"speaker_role": "直属主管", "evidence_type": "解除意思表示", "quote": "..."},
        {"speaker_role": "HR/人力资源", "evidence_type": "工资数额", "quote": "..."},
    ]
    result = detect_cross_role_conflicts(cards)
    assert all(c["cross_role_conflict"] is False for c in result)


def test_unidentified_role_not_treated_as_company():
    """未识别角色 should not trigger conflict."""
    cards = [
        {"speaker_role": "HR/人力资源", "evidence_type": "解除意思表示", "quote": "..."},
        {"speaker_role": "未识别角色", "evidence_type": "解除意思表示", "quote": "..."},
    ]
    result = detect_cross_role_conflicts(cards)
    assert all(c["cross_role_conflict"] is False for c in result)
