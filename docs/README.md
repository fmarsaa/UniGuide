# Documentation generation scripts

One-off scripts used to turn `159056-PROPOSAL.docx` into `159056-DOCUMENTATION.docx`
(adds Chapters 5-6 from real model/testing results, rewrites Chapters 1-4 and the
front matter to completed/past tense, adds the real app screenshot, updates the
List of Tables/Figures). They were run in this order, from `backend/` (so that
`model_metrics.json` and the relative `../159056-*.docx` paths resolve correctly):

```bash
cd backend
python ../docs/build_chapters_5_6.py
python ../docs/rewrite_chapters_1_4.py
python ../docs/add_screenshot.py   # requires ../docs/app_screenshot.png
python ../docs/update_lists.py
```

Only useful again if you retrain the model (numbers in Chapter 5 would need
regenerating) or want to redo this transformation from a fresh proposal draft.
Not part of the application itself.
