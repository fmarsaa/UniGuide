"""Second batch of catalogue corrections, all taken from KUCCPS's official 2025/2026
degree programmes list (DEGREE_PROGRAMMES_2025.pdf), matched by university + course name.

  * FIX_CODE      - cutoffs already match the official row exactly; only the KUCCPS code was wrong/missing
  * FIX_VALUES    - official code AND cutoffs (our two years were shifted by one)
  * REMOVE        - entries with no official source (private university, not in KUCCPS's cutoff list)

Applies to backend/programmes_catalog.py and flutter_app/lib/data/programme_repository.dart.
Dry-runs both files first and refuses to touch either unless every change is found exactly once.
"""
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "backend"))
from programmes_catalog import PROGRAMMES  # noqa: E402

PY = os.path.join(ROOT, "backend", "programmes_catalog.py")
DART = os.path.join(ROOT, "flutter_app", "lib", "data", "programme_repository.dart")

UON, MOI, KU, JKUAT = "University of Nairobi", "Moi University", "Kenyatta University", "Jomo Kenyatta University (JKUAT)"

# (course title prefix, university name, new code)
FIX_CODE = [
    ("Bachelor of Medicine and Bachelor of Surgery", UON, "1263131"),
    ("Bachelor of Medicine and Bachelor of Surgery", MOI, "1253131"),
    ("Bachelor of Pharmacy", UON, "1263129"),
    ("Bachelor of Science in Nursing", UON, "1263132"),
    ("Bachelor of Science in Informatics", UON, "1263115"),
    ("Bachelor of Science in Software Engineering", "Kisii University", "1087542"),
    ("Bachelor of Science in Electrical", UON, "1263117"),
    ("Bachelor of Science in Civil Engineering", UON, "1263116"),
    ("Bachelor of Science in Civil Engineering", JKUAT, "1249116"),
    ("Bachelor of Laws", UON, "1263134"),
    ("Bachelor of Science in Actuarial", UON, "1263107"),
    ("Bachelor of Commerce", UON, "1263133"),
    ("Bachelor of Science in Community Health", JKUAT, "1249423"),
    ("Bachelor of Science in Community Health", "Jaramogi Oginga Odinga University of Science and Technology", "1053423"),
    ("Bachelor of Science in Forestry", "University of Eldoret", "1114175"),
    ("Bachelor of Science in Biomedical", KU, "1111696"),
]
# (course title prefix, university name, new code, latest 2023, previous 2022)
FIX_VALUES = [
    ("Bachelor of Pharmacy", KU, "1111129", "44.01", "43.541"),
    ("Bachelor of Science in Informatics", JKUAT, "1249115", "44.101", "43.809"),
    ("Bachelor of Science in Business Information", "Kabarak University", "1061206", "21.375", "21.444"),
    ("Bachelor of Science in Electrical", JKUAT, "1249117", "42.434", "42.291"),
]
REMOVE = [
    ("Bachelor of Science in Informatics", "Strathmore University"),
    ("Bachelor of Science in Software Engineering", "Strathmore University"),
    ("Bachelor of Science in Business Information", "Strathmore University"),
    ("Bachelor of Laws", "Strathmore University"),
    ("Bachelor of Science in Actuarial", "Strathmore University"),
    ("Bachelor of Commerce", "Strathmore University"),
]


def full_title(prefix):
    hits = [p["title"] for p in PROGRAMMES if p["title"].startswith(prefix)]
    assert len(hits) == 1, ("ambiguous or missing course", prefix, hits)
    return hits[0]


def programme_span(text, title_pattern, next_pattern):
    start = text.index(title_pattern)
    nxt = re.search(next_pattern, text[start + 10:])
    end = start + 10 + nxt.start() if nxt else len(text)
    return start, end


# ---------- Python file ----------
def py_entry_re(uni):
    return re.compile(r'^[ \t]*\{"universityName": "%s",[^\n]*\},?\n' % re.escape(uni), re.M)


def fix_python(text):
    def block(title):
        return programme_span(text, '"title": "%s"' % title, r'\n    \{\n        "id": "prog_')

    def edit(title, uni, fn):
        nonlocal text
        s, e = block(title)
        seg = text[s:e]
        ms = list(py_entry_re(uni).finditer(seg))
        assert len(ms) == 1, ("python entry", title, uni, len(ms))
        m = ms[0]
        new = fn(m.group(0))
        text = text[:s] + seg[:m.start()] + new + seg[m.end():] + text[e:]

    for prefix, uni, code in FIX_CODE:
        edit(full_title(prefix), uni, lambda line, code=code: re.sub(r'"kuccpsCode": "[^"]*"', '"kuccpsCode": "%s"' % code, line))
    for prefix, uni, code, latest, prev in FIX_VALUES:
        def f(line, code=code, latest=latest, prev=prev):
            line = re.sub(r'"kuccpsCode": "[^"]*"', '"kuccpsCode": "%s"' % code, line)
            line = re.sub(r'"latestCutoff": [\d.]+', '"latestCutoff": %s' % latest, line)
            return re.sub(r'"previousCutoff": [\d.]+', '"previousCutoff": %s' % prev, line)
        edit(full_title(prefix), uni, f)
    for prefix, uni in REMOVE:
        edit(full_title(prefix), uni, lambda line: "")
    return text


# ---------- Dart file ----------
def dart_entry_re(uni):
    # one UniversityOffering(...) call, single- or multi-line, ending at its own kuccpsCode
    return re.compile(
        r"[ \t]*UniversityOffering\(\s*universityName: '%s',.*?kuccpsCode: '[^']*',?\s*\),?\n" % re.escape(uni), re.S
    )


def fix_dart(text):
    def edit(title, uni, fn):
        nonlocal text
        start = text.index("title: '%s'" % title)
        nxt = re.search(r"\n    Programme\(\n", text[start + 10:])
        end = start + 10 + nxt.start() if nxt else len(text)
        seg = text[start:end]
        ms = list(dart_entry_re(uni).finditer(seg))
        assert len(ms) == 1, ("dart entry", title, uni, len(ms))
        m = ms[0]
        text = text[:start] + seg[:m.start()] + fn(m.group(0)) + seg[m.end():] + text[end:]

    for prefix, uni, code in FIX_CODE:
        edit(full_title(prefix), uni, lambda s, code=code: re.sub(r"kuccpsCode: '[^']*'", "kuccpsCode: '%s'" % code, s))
    for prefix, uni, code, latest, prev in FIX_VALUES:
        def f(s, code=code, latest=latest, prev=prev):
            s = re.sub(r"kuccpsCode: '[^']*'", "kuccpsCode: '%s'" % code, s)
            s = re.sub(r"latestCutoff: [\d.]+", "latestCutoff: %s" % latest, s)
            return re.sub(r"previousCutoff: [\d.]+", "previousCutoff: %s" % prev, s)
        edit(full_title(prefix), uni, f)
    for prefix, uni in REMOVE:
        edit(full_title(prefix), uni, lambda s: "")
    return text


def rewrite(path, fn):
    raw = open(path, encoding="utf-8", newline="").read()
    crlf = "\r\n" in raw
    text = fn(raw.replace("\r\n", "\n"))
    if crlf:
        text = text.replace("\n", "\r\n")
    open(path, "w", encoding="utf-8", newline="").write(text)


if __name__ == "__main__":
    for path, fn in ((PY, fix_python), (DART, fix_dart)):  # dry run both first
        fn(open(path, encoding="utf-8", newline="").read().replace("\r\n", "\n"))
    rewrite(PY, fix_python)
    rewrite(DART, fix_dart)
    print("applied: %d code fixes, %d value fixes, %d removals" % (len(FIX_CODE), len(FIX_VALUES), len(REMOVE)))
