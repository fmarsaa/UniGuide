"""Read-only check: compares the app's per-university cutoffs with KUCCPS's official
2025/2026 degree programmes list (DEGREE_PROGRAMMES_2025.pdf, which reports the
2023 and 2022 cutoffs). Changes nothing - it only prints a report.

Run from the project root:  python catalogue_verification/compare_catalogue.py
"""
import os
import re
import sys

import pdfplumber

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "backend"))
from programmes_catalog import PROGRAMMES  # noqa: E402

ROW = re.compile(r"^(\d{8,10})\s+(.*?)\s(\d{1,2}\.\d{1,3})\s+(\d{1,2}\.\d{1,3})")


def load_official():
    rows = {}
    with pdfplumber.open(os.path.join(HERE, "DEGREE_PROGRAMMES_2025.pdf")) as pdf:
        for page in pdf.pages:
            for line in (page.extract_text() or "").splitlines():
                m = ROW.match(line.strip())
                if m:
                    code = m.group(1)[-7:]  # leading digits are the row number
                    rows[code] = {
                        "name": m.group(2),
                        "c2023": float(m.group(3)),
                        "c2022": float(m.group(4)),
                    }
    return rows


def main():
    official = load_official()
    print(f"official rows read from the KUCCPS PDF: {len(official)}")

    total = found = exact = close = off = 0
    problems, missing = [], []
    for p in PROGRAMMES:
        for u in p["offeringUniversities"]:
            total += 1
            row = official.get(str(u["kuccpsCode"]))
            if row is None:
                missing.append((p["title"], u["universityName"], u["kuccpsCode"]))
                continue
            found += 1
            d_latest = abs(u["latestCutoff"] - row["c2023"])
            d_prev = abs(u["previousCutoff"] - row["c2022"])
            if d_latest < 0.0015 and d_prev < 0.0015:
                exact += 1
            elif d_latest <= 0.5 and d_prev <= 0.5:
                close += 1
            else:
                off += 1
                problems.append((p["title"], u["universityName"], u["kuccpsCode"],
                                 u["latestCutoff"], row["c2023"], u["previousCutoff"], row["c2022"]))

    print(f"\ncatalogue university entries: {total}")
    print(f"  found in the official list by KUCCPS code: {found}")
    print(f"    exact match on both years:      {exact}")
    print(f"    within 0.5 points:              {close}")
    print(f"    differs by more than 0.5:       {off}")
    print(f"  NOT found by code in the official list: {len(missing)}")

    if problems:
        print("\nDIFFERENCES (programme | university | code | ours 2023 vs official | ours 2022 vs official):")
        for t, uni, code, l, ol, pv, op in problems:
            print(f"  {t[:44]} | {uni[:28]} | {code} | {l} vs {ol} | {pv} vs {op}")
    if missing:
        print("\nNOT FOUND:")
        for t, uni, code in missing:
            print(f"  {t[:44]} | {uni[:28]} | {code}")


if __name__ == "__main__":
    main()
