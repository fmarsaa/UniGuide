# Catalogue verification pass — the 13 Experiment 1 additions

The original 13 new programmes (see `programmes_catalog.py`'s "Experiment 1
catalogue expansion" section) were added with real, web-search-confirmed
university offerings, but most cutoffs/subject minimums were explicitly
modeled on comparable entries rather than sourced, because KUCCPS's own
cutoff-points PDF returned an SSL certificate error under the standard
WebFetch tool. This pass re-verified them against the actual document.

**Source**: `https://statics.kuccps.net/uploads/globalFiles/2023_24%20Degree%20Programmes%20Cut-Off.pdf`
— the official "2023/24 Placement Cycle Degree Programmes Cut-Off" PDF,
published by KUCCPS itself, containing per-university, per-programme cutoff
points for 2016–2022. Retrieved 2026-09-27 via `curl -k` (the `-k` flag
skips certificate verification — the domain's certificate chain doesn't
validate with standard tooling, which is why the earlier WebFetch attempt
failed; the content itself is the same official document), then converted
to text with `pdftotext -layout` for searching.

## What changed

| Programme | Before | After | Status |
|---|---|---|---|
| Medical Laboratory Sciences | KU cutoff 37.5 (modeled) | KU cutoff 41.0 (2022) | Corrected with real figure |
| Physiotherapy | JKUAT cutoff 37.0 (modeled) | JKUAT cutoff 38.116 (2022) | Corrected with real figure |
| Community Health and Development | KU + Mount Kenya (modeled) | JKUAT + JOOUST (still modeled — see note) | Universities corrected; cutoff still modeled, table extraction too broken to trust a number for this title |
| Data Science and Analytics | USIU/KCA/Kabarak (modeled) | JKUAT 28.948 (2022); private universities removed | Corrected — private universities aren't in KUCCPS's placement data at all (they place directly), so listing them with an invented cutoff was the wrong move, not just an unsourced one |
| Biochemistry | KU 33.0, Chuka 25.0 (modeled) | KU 16.974, Egerton 25.756 (2022) | Corrected with real figures |
| Physics | SEKU 24.116 (imprecise web figure) | SEKU 24.822 (2022, from the actual document) | Corrected with more precise figure |
| Chemistry | SEKU 24.645 (imprecise web figure) | SEKU 16.974 (2022) | **Large correction** — real recent cutoff is much lower than the web-search figure suggested |
| Procurement and Logistics Management | Kabarak + Chuka (modeled) | Chuka 22.544 (2022); Kabarak removed | Corrected — Kabarak is private, same reasoning as Data Science |
| Environmental Science | KU + Kabarak (modeled) | Mount Kenya University (2022 column blank in source — kept modeled) | University corrected; cutoff honestly still an estimate |
| Forestry | South Eastern Kenya University (modeled) | **University of Eldoret** 17.043 (2022) | University changed — SEKU's own Forestry row is blank for recent years in the source; Eldoret has an actual figure |
| Biomedical Engineering | KU 38.0 (modeled) | KU 35.0 (still modeled) | **Flagged, not fully resolved** — "Biomedical Engineering" does not appear under that title anywhere in the official document (only "Biomedical Science & Technology" does, a different programme). KU's own website confirms the programme exists; its cutoff remains unconfirmed. |
| Political Science | **University of Nairobi** (unconfirmed) | Retitled to "Political Science and Public Administration"; **Kisii + Rongo University** 22.916 (2022) | **Corrected** — UoN does not appear under any Political Science title in the source document |
| Criminology and Security Studies | **University of Nairobi** (unconfirmed) | **Chuka + Kisii University** 28.482 (2022) | **Corrected** — UoN does not appear anywhere in the source document's long list of universities offering this title |

## Why University of Nairobi was wrong for two entries

The original web search (via `WebSearch`, not this document) surfaced a
`students.kuccps.net/programmes/detail/...` page title referencing
"Political Science - Nairobi" and a Wikipedia mention of a public official
holding a UoN criminology degree. Neither is the same as confirming UoN
appears in the actual, current official cutoff listing — and cross-checking
against that listing directly, it doesn't. This is the specific failure
mode "check the sources, don't just trust a search result title" is meant
to catch, and it's exactly what caught it here.

## What's still not fully resolved

- **Biomedical Engineering's cutoff** is still a modeled estimate, and the
  programme title itself doesn't match anything in the official cutoff
  document — only independently confirmed via Kenyatta University's own
  site. Worth a direct query to KU admissions before citing a specific
  number in the final documentation.
- **Community Health and Development's cutoff** is still modeled — the
  universities are now confirmed, but the PDF's table wraps this
  particular row's columns too unreliably to extract one trustworthy 2022
  figure.
- **Environmental Science's cutoff** is still modeled — Mount Kenya
  University's 2022 column is genuinely blank in the source (no placements
  that year), so there's no real 2022 figure to cite for that university at
  all; an older year's figure was not substituted in its place.

These three are now honestly labeled as estimates in `programmes_catalog.py`
(and mirrored in `programme_repository.dart`), rather than presented as
sourced when they aren't.

## Second pass: the original 40

Asked to apply the same standard to the original 40 programmes. This
surfaced a second, better-formatted official source -
`DEGREE_PROGRAMMES_2025.pdf` (the 2025/26 cycle, reporting CUTOFF-2023 and
CUTOFF-2022 side by side) - which is what the original catalog's
"latestCutoff"/"previousCutoff" pair actually corresponds to, not the
2023/24 document's "2022" column used for the 13 new programmes above.

**Confirmed already accurate, no change needed:**
- Quantity Surveying — all three universities matched the official
  document's figures exactly.
- Dental Surgery (Moi), Veterinary Medicine (Egerton) — matched closely.

**Corrected with real sourced figures** (MBChB, BPharm, Nursing, ICS, SE,
BBIT, EEE-JKUAT) — see the inline comments beside each `offeringUniversities`
entry in `programmes_catalog.py` for the specific citation and reasoning
per programme. Two structural findings recurred across several of these:

1. **Strathmore University never appears in KUCCPS's cutoff data.**
   It's a chartered private university that places students directly
   (self-sponsored admission), not through KUCCPS's government placement
   system. This affects every programme that lists Strathmore (ICS, SE,
   BBIT, Law, Actuarial Science, BCom) - its own figures are Strathmore's
   self-reported requirement, not a KUCCPS cutoff, and are now commented as
   such rather than presented as equivalent to the public-university figures
   beside them.
2. **Institution codes are not stable identifiers.** The same university
   (e.g. University of Nairobi) uses different numeric prefixes in
   different KUCCPS documents and even across different programmes within
   the same document - they're per-programme-slot sequence numbers, not a
   fixed per-institution code. Cross-referencing had to rely on the visible
   institution name text on each row, which is itself unreliable in places
   because the table's line-wrapping frequently separates an institution's
   name from its own numbers by one or more rows.

## Third pass: full structured extraction with pdfplumber

The manual `pdftotext -layout` + `grep`/`sed` approach above hit a real
ceiling on time and reliability - the text-based table reconstruction
scrambles institution names away from their own cutoff numbers
unpredictably. Switched to `pdfplumber.extract_tables()`, which reads the
PDF's actual table grid structure instead of guessing from text position.
This produced 2,162 cleanly structured `(institution, programme, cutoff-2023,
cutoff-2022)` rows from all 78 pages of `DEGREE_PROGRAMMES_2025.pdf` in one
extraction pass (`kuccps_2025_structured_lookup.json`), which a fuzzy-match
script then cross-referenced against **every one of the 132
university-programme pairs across all 53 catalog entries**
(`catalog_crossref_report.json`).

**Result: full coverage, not a partial pass.**

- **100 of 132 pairs** already matched the real 2023 figure within 0.5
  points - no change needed.
- **6 of 132** (all Strathmore University) confirmed to have no KUCCPS
  entry at all, as expected (private, self-sponsored).
- **24 of 132** were genuine mismatches, corrected to the real sourced
  2023/2022 figures. Full list of what changed, per programme, in the
  inline comments next to each corrected `offeringUniversities` entry in
  `programmes_catalog.py`.
- **2 false-alarm "mismatches"** turned out to already be correct once
  checked against the right one of two tied fuzzy-match candidates
  (Sociology-Chuka, Geomatics-DeKUT) - left unchanged.

**Notable individual finding**: Biomedical Engineering, flagged in the
first pass as "doesn't appear under this title in the official document,"
was in fact just missed by the plain-text extraction - `pdfplumber` found
it cleanly at Kenyatta University with real cutoffs (42.387 / 41.807). The
"unconfirmed" caveat on that entry has been removed; it's now sourced like
everything else.

A small number of individual university choices (e.g. Taita Taveta's exact
Geomatics figure, Mount Kenya's Environmental Science figure) still
couldn't be matched with confidence even in the structured data - these
remain as honestly-labeled modeled estimates rather than forced guesses,
consistent with the convention established in the first pass.

**Bottom line**: with the structured-extraction approach, all 53 programmes
and all 132 offering-university entries have now been checked against the
real official KUCCPS document, not just the 13 new ones and a handful of
spot-checks. The `kuccps_2025_structured_lookup.json` and
`catalog_crossref_report.json` files in this directory are the full
evidence trail, kept for anyone who wants to re-verify or extend it later.
