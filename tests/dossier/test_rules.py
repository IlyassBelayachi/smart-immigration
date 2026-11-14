from datetime import date

from smart_immigration.dossier.rules import assess
from smart_immigration.schemas import ApplicantProfile, Verdict


def by_id(report, rule_id):
    return next(r for r in report.results if r.rule_id == rule_id)


def test_empty_profile_is_all_unknown():
    report = assess(ApplicantProfile())
    assert all(r.verdict == Verdict.UNKNOWN for r in report.results)
    assert by_id(report, "CA-SP-003").missing_inputs  # liste ce qui manque


def test_funds_new_table_sufficient():
    p = ApplicantProfile(application_date=date(2026, 10, 1), destination_province="ON", family_size=1,
                         funds_available_cad=23448 + 15000 + 2000, tuition_first_year_cad=15000, transport_cost_cad=2000)
    r = by_id(assess(p), "CA-SP-003")
    assert r.verdict == Verdict.MEETS


def test_funds_new_table_one_dollar_short():
    p = ApplicantProfile(application_date=date(2026, 10, 1), destination_province="ON", family_size=1,
                         funds_available_cad=23448 + 15000 + 2000 - 1, tuition_first_year_cad=15000, transport_cost_cad=2000)
    assert by_id(assess(p), "CA-SP-003").verdict == Verdict.DOES_NOT_MEET


def test_funds_uses_old_table_before_sept_2026():
    # 22 895 (ancien bareme, 1 personne) suffit avant le 1er sept. 2026
    p = ApplicantProfile(application_date=date(2026, 8, 31), destination_province="ON", family_size=1,
                         funds_available_cad=22895, tuition_first_year_cad=0, transport_cost_cad=0)
    assert by_id(assess(p), "CA-SP-003").verdict == Verdict.MEETS
    p2 = p.model_copy(update={"application_date": date(2026, 9, 1)})
    assert by_id(assess(p2), "CA-SP-003").verdict == Verdict.DOES_NOT_MEET


def test_funds_family_larger_than_table():
    p = ApplicantProfile(application_date=date(2026, 10, 1), destination_province="ON", family_size=8,
                         funds_available_cad=62054 + 6318, tuition_first_year_cad=0, transport_cost_cad=0)
    assert by_id(assess(p), "CA-SP-003").verdict == Verdict.MEETS


def test_funds_quebec_is_unknown_not_guessed():
    p = ApplicantProfile(application_date=date(2026, 10, 1), destination_province="QC", family_size=1,
                         funds_available_cad=10**6, tuition_first_year_cad=0, transport_cost_cad=0)
    assert by_id(assess(p), "CA-SP-003").verdict == Verdict.UNKNOWN


def test_funds_requires_destination_even_when_amounts_are_complete():
    profile = ApplicantProfile(application_date=date(2026, 10, 1), family_size=1,
                               funds_available_cad=50000, tuition_first_year_cad=15000, transport_cost_cad=2000)
    result = by_id(assess(profile), "CA-SP-003")
    assert result.verdict == Verdict.UNKNOWN
    assert result.missing_inputs == ["destination_province"]


def test_pal_missing_vs_provided_vs_exempt():
    base = dict(destination_province="ON", level_of_study="bachelor")
    assert by_id(assess(ApplicantProfile(**base, pal_provided=True)), "CA-SP-002").verdict == Verdict.MEETS
    assert by_id(assess(ApplicantProfile(**base, pal_provided=False)), "CA-SP-002").verdict == Verdict.DOES_NOT_MEET
    assert by_id(assess(ApplicantProfile(**base)), "CA-SP-002").verdict == Verdict.UNKNOWN
    master = ApplicantProfile(destination_province="ON", level_of_study="master", dli_is_public=True)
    assert by_id(assess(master), "CA-SP-002").verdict == Verdict.MEETS
    private = ApplicantProfile(destination_province="ON", level_of_study="master", dli_is_public=False, pal_provided=False)
    assert by_id(assess(private), "CA-SP-002").verdict == Verdict.DOES_NOT_MEET


def test_quebec_needs_caq_even_for_master():
    p = ApplicantProfile(destination_province="QC", level_of_study="master", dli_is_public=True, caq_provided=False)
    assert by_id(assess(p), "CA-SP-002").verdict == Verdict.DOES_NOT_MEET
    p2 = p.model_copy(update={"caq_provided": True})
    assert by_id(assess(p2), "CA-SP-002").verdict == Verdict.MEETS


def test_letter_of_acceptance_flag():
    assert by_id(assess(ApplicantProfile(has_letter_of_acceptance=False)), "CA-SP-001").verdict == Verdict.DOES_NOT_MEET
    assert by_id(assess(ApplicantProfile(has_letter_of_acceptance=True)), "CA-SP-001").verdict == Verdict.MEETS
