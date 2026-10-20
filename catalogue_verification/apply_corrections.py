"""Applies the 11 verified corrections (from KUCCPS's official 2025/2026 degree
programmes list) to the two copies of the catalogue kept in the repository:
backend/programmes_catalog.py and flutter_app/lib/data/programme_repository.dart.

Every replacement is an exact-line match and the script refuses to run if any line
is not found exactly once, so it can never half-apply. Run once from the project root.
"""
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PY = os.path.join(ROOT, "backend", "programmes_catalog.py")
DART = os.path.join(ROOT, "flutter_app", "lib", "data", "programme_repository.dart")

# (old code, new code, new latest, new previous, replace university?)
JKUAT = ("Jomo Kenyatta University (JKUAT)", "Public", "Juja")
CORRECTIONS = [
    # Right numbers, wrong code
    dict(old="1249132", only_if_latest="45.048", new="1249131"),          # JKUAT MBChB (1249132 is JKUAT Nursing)
    dict(old="1249619", new="1249719"),                                    # JKUAT Geospatial Information Science
    dict(old="1080409", new="1249409"),                                    # JKUAT Data Science and Analytics
    dict(old="1263112", new="1111112"),                                    # Kenyatta University Biochemistry
    dict(old="1105112", new="1057112"),                                    # Egerton University Biochemistry
    dict(old="1229170", new="1480366"),                                    # CUEA Physics
    dict(old="1087520", new="1165513"),                                    # Maasai Mara University Chemistry
    # Wrong code AND cutoff values taken from the official row
    dict(old="1279194", new="1082194", latest="38.872", previous="38.739"),   # Masinde Muliro Medical Lab
    dict(old="1249562", new="1249465", latest="38.224", previous="38.116"),   # JKUAT Physiotherapy
    dict(old="1087159", new="1073550", latest="22.449", previous="25.712"),   # Rongo Political Science
    # No official basis for Kenyatta University here; the official list has JKUAT
    dict(old="1246194", new="1249194", latest="40.675", previous="40.68", university=JKUAT),
]


def fix_python(text):
    for c in CORRECTIONS:
        pat = re.compile(r'^(?P<line>[^\n]*"kuccpsCode": "%s"[^\n]*)$' % c["old"], re.M)
        lines = [m for m in pat.finditer(text) if not c.get("only_if_latest") or ('"latestCutoff": %s,' % c["only_if_latest"]) in m.group("line")]
        assert len(lines) == 1, ("python", c["old"], len(lines))
        line = lines[0].group("line")
        new = line.replace('"kuccpsCode": "%s"' % c["old"], '"kuccpsCode": "%s"' % c["new"])
        if "latest" in c:
            new = re.sub(r'"latestCutoff": [\d.]+', '"latestCutoff": %s' % c["latest"], new)
            new = re.sub(r'"previousCutoff": [\d.]+', '"previousCutoff": %s' % c["previous"], new)
        if "university" in c:
            name, kind, place = c["university"]
            new = re.sub(r'"universityName": "[^"]*"', '"universityName": "%s"' % name, new)
            new = re.sub(r'"universityType": "[^"]*"', '"universityType": "%s"' % kind, new)
            new = re.sub(r'"location": "[^"]*"', '"location": "%s"' % place, new)
        text = text.replace(line, new, 1)
    return text


def fix_dart(text):
    # The JKUAT MBChB entry is formatted over several lines in the Dart file.
    indent = "\n          "
    multi_old = "latestCutoff: 45.048," + indent + "previousCutoff: 44.611," + indent + "kuccpsCode: '1249132',"
    multi_new = "latestCutoff: 45.048," + indent + "previousCutoff: 44.611," + indent + "kuccpsCode: '1249131',"
    assert text.count(multi_old) == 1, ("dart multi-line MBChB", text.count(multi_old))
    text = text.replace(multi_old, multi_new)
    for c in CORRECTIONS:
        if c.get("only_if_latest"):
            continue  # handled above
        pat = re.compile(r"^(?P<line>[^\n]*kuccpsCode: '%s'[^\n]*)$" % c["old"], re.M)
        lines = [m for m in pat.finditer(text) if not c.get("only_if_latest") or ("latestCutoff: %s," % c["only_if_latest"]) in m.group("line")]
        assert len(lines) == 1, ("dart", c["old"], len(lines))
        line = lines[0].group("line")
        new = line.replace("kuccpsCode: '%s'" % c["old"], "kuccpsCode: '%s'" % c["new"])
        if "latest" in c:
            new = re.sub(r"latestCutoff: [\d.]+", "latestCutoff: %s" % c["latest"], new)
            new = re.sub(r"previousCutoff: [\d.]+", "previousCutoff: %s" % c["previous"], new)
        if "university" in c:
            name, kind, place = c["university"]
            new = re.sub(r"universityName: '[^']*'", "universityName: '%s'" % name, new)
            new = re.sub(r"universityType: '[^']*'", "universityType: '%s'" % kind, new)
            new = re.sub(r"location: '[^']*'", "location: '%s'" % place, new)
        text = text.replace(line, new, 1)
    return text


def rewrite(path, fn):
    raw = open(path, encoding="utf-8", newline="").read()
    crlf = "\r\n" in raw
    text = fn(raw.replace("\r\n", "\n"))
    if crlf:
        text = text.replace("\n", "\r\n")
    open(path, "w", encoding="utf-8", newline="").write(text)


if __name__ == "__main__":
    # Dry-run both first so a failure in either leaves both files untouched.
    for path, fn in ((PY, fix_python), (DART, fix_dart)):
        fn(open(path, encoding="utf-8", newline="").read().replace("\r\n", "\n"))
    rewrite(PY, fix_python)
    rewrite(DART, fix_dart)
    print("applied %d corrections to both catalogue copies" % len(CORRECTIONS))
