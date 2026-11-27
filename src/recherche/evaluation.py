"""Outils d'évaluation de la recherche : correspondance avec les éléments attendus, Recall@k, MRR@k."""
from __future__ import annotations

import re


def parser_attendus(texte: str) -> list[tuple[str, int | None]]:
    """'manuel_pompe_a p.18 ; photo_plaque_pompe_a' -> [('manuel_pompe_a', 18), ('photo_plaque_pompe_a', None)]"""
    if not texte.strip() or texte.strip().lower().startswith("aucun"):
        return []
    out = []
    for morceau in texte.split(";"):
        m = re.match(r"\s*([a-z0-9_]+)(?:\s+p\.(\d+))?\s*$", morceau)
        if not m:
            raise ValueError(f"Élément attendu mal formé : {morceau!r}")
        out.append((m.group(1), int(m.group(2)) if m.group(2) else None))
    return out


def correspond(resultat: dict, attendus: list[tuple[str, int | None]]) -> bool:
    for doc, page in attendus:
        if resultat["document_id"] == doc and (page is None or resultat.get("page") == page):
            return True
    return False


def rang_premier_bon(resultats: list[dict], attendus) -> int | None:
    for i, r in enumerate(resultats, 1):
        if correspond(r, attendus):
            return i
    return None


def recall_at_k(rangs: list[int | None], k: int = 5) -> float:
    return sum(1 for r in rangs if r is not None and r <= k) / len(rangs) if rangs else 0.0


def mrr_at_k(rangs: list[int | None], k: int = 10) -> float:
    return sum((1 / r) if r is not None and r <= k else 0 for r in rangs) / len(rangs) if rangs else 0.0
