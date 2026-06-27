"""Cross-role conflict detection for evidence cards.

Given a list of evidence cards (each with speaker_role, evidence_type, quote),
returns flagged cards where different company-side speakers contradict each other
on the same evidence type.
"""
from typing import Any

COMPANY_ROLES = {
    "HR/人力资源", "直属主管", "部门经理/总监",
    "高层/老板", "公司法务", "工会代表"
}


def detect_cross_role_conflicts(cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Flag cards that contradict other company-side cards on same evidence_type.

    Returns the input cards list with `cross_role_conflict` field populated.
    """
    by_type: dict[str, list[dict]] = {}
    for card in cards:
        t = card.get("evidence_type", "")
        by_type.setdefault(t, []).append(card)

    for evidence_type, group in by_type.items():
        company_speakers = {
            c["speaker_role"] for c in group
            if c.get("speaker_role") in COMPANY_ROLES
        }
        is_conflict = len(company_speakers) >= 2
        for card in group:
            # Only flag company-side cards; employee/third-party cards
            # in the same group are witnesses, not conflicting parties.
            card["cross_role_conflict"] = (
                is_conflict and card.get("speaker_role") in COMPANY_ROLES
            )

    return cards
