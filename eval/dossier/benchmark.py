"""Évaluation reproductible de la chaîne Dossier sur des données fictives."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from time import perf_counter

from smart_immigration.dossier.agents import check_dossier, read_document
from smart_immigration.dossier.documents import Specimen, find_contradictions
from smart_immigration.dossier.routes import DossierRequest
from smart_immigration.schemas import ApplicantProfile

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "synthetic"
DOCUMENTS = DATA / "evaluation"


def checked(piece: dict) -> Specimen:
    specimen = Specimen.model_validate(piece)
    for field in specimen.fields:
        field.reviewed_by_human = bool(field.value)
    return specimen


def document_scores() -> tuple[dict, dict]:
    scores = {}
    reference = {}
    for case in json.loads((DOCUMENTS / "annotations.json").read_text(encoding="utf-8")):
        filename = case["file"]
        content = (DATA / filename).read_bytes()
        media = "application/pdf" if filename.endswith(".pdf") else "text/plain"
        result = read_document(filename, content, case["type"], media)
        if result.status != "needs_human":
            raise RuntimeError(f"{filename}: {result.warnings}")
        piece = checked(result.data["document"])
        reference[filename] = piece
        bucket = scores.setdefault(media, Counter())
        bucket["documents"] += 1
        for field in piece.fields:
            expected = case["expected"][field.field_name]
            bucket["fields"] += 1
            bucket["exact"] += field.value == expected
            bucket["expected_values"] += expected is not None
            bucket["extracted_values"] += field.value is not None
    return scores, reference


def profile_scores() -> Counter:
    counts = Counter(profiles=0, verdicts=0, exact=0)
    for case in json.loads((DOCUMENTS / "profiles.json").read_text(encoding="utf-8")):
        dossier = DossierRequest(profile=ApplicantProfile.model_validate(case["profile"]),
                                 document_checks=case["checks"])
        report = check_dossier(case["id"], dossier)
        got = {result["rule_id"]: result["verdict"] for result in report.data["assessment"]["results"]}
        counts["profiles"] += 1
        counts["exact"] += sum(got.get(key) == value for key, value in case["expected"].items())
        counts["verdicts"] += len(case["expected"])
    return counts


def contradiction_scores(reference: dict) -> Counter:
    counts = Counter(cases=0, exact=0, conflicts_caught=0, missed_without_check=0)
    cases = json.loads((DOCUMENTS / "contradictions.json").read_text(encoding="utf-8"))
    for case in cases:
        pieces = [reference[name].model_copy(deep=True) for name in case["files"]]
        for index, field_name in case["unconfirmed"]:
            next(field for field in pieces[index].fields if field.field_name == field_name).reviewed_by_human = False
        profile = ApplicantProfile(**case["profile"])
        got = {item.field_name for item in find_contradictions(pieces, profile)}
        expected = set(case["expected"])
        counts["cases"] += 1
        counts["exact"] += got == expected
        counts["conflicts_caught"] += len(got & expected)
        counts["missed_without_check"] += len(expected)
    return counts


def main() -> None:
    start = perf_counter()
    extraction, reference = document_scores()
    results = {
        "extraction": extraction,
        "profiles": profile_scores(),
        "contradictions": contradiction_scores(reference),
        "seconds": round(perf_counter() - start, 3),
        "paid_calls": 0,
    }
    print(json.dumps(results, ensure_ascii=False, indent=2))
    if results["profiles"]["exact"] != results["profiles"]["verdicts"]:
        raise SystemExit("Écart sur les verdicts attendus.")
    if results["contradictions"]["exact"] != results["contradictions"]["cases"]:
        raise SystemExit("Écart sur les contradictions attendues.")


if __name__ == "__main__":
    main()
