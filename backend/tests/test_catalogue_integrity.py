"""Guards the programme catalogue's per-university data, which drives the
"meets the cutoff at N of M universities" message students see. Added after a
verification against KUCCPS's official 2025/2026 list found wrong KUCCPS codes
and shifted cutoff years (see catalogue_verification/)."""

from programmes_catalog import PROGRAMMES


def _entries():
    for p in PROGRAMMES:
        for u in p["offeringUniversities"]:
            yield p, u


def test_every_programme_lists_at_least_one_university():
    assert all(p["offeringUniversities"] for p in PROGRAMMES)


def test_every_university_entry_has_a_kuccps_code():
    missing = [(p["title"], u["universityName"]) for p, u in _entries() if not str(u["kuccpsCode"]).strip()]
    assert not missing, missing


def test_no_kuccps_code_is_shared_by_two_entries():
    seen = {}
    for p, u in _entries():
        code = u["kuccpsCode"]
        assert code not in seen, f"code {code} used by both {seen.get(code)} and {(p['title'], u['universityName'])}"
        seen[code] = (p["title"], u["universityName"])


def test_cutoffs_are_real_positive_numbers():
    bad = [(p["title"], u["universityName"]) for p, u in _entries() if not (u["latestCutoff"] > 0 and u["previousCutoff"] > 0)]
    assert not bad, bad
