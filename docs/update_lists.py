# -*- coding: utf-8 -*-
"""Adds the new Chapter 5 tables and figure to the front-matter List of
Tables / List of Figures, using the same 'table of figures' paragraph style
as the existing entries so formatting matches exactly.
"""
import docx

PATH = "../159056-DOCUMENTATION.docx"
doc = docx.Document(PATH)

NEW_TABLE_ENTRIES = [
    "Table 5.1: Hardware Specifications\t40",
    "Table 5.2: Software Specifications\t42",
    "Table 5.3: Random Forest Classification Performance per Programme (Held-Out Test Set)\t46",
    "Table 5.4: Functional Testing Results\t48",
]
NEW_FIGURE_ENTRY = "Figure 5.1: Sign-In Screen of the Completed UniGuide Mobile Application, Running on an Android Emulator\t49"

# --- List of Tables: insert after the existing "Table 2.1: ..." entry ---
anchor = None
for p in doc.paragraphs:
    if p.style.name == "table of figures" and p.text.strip().startswith("Table"):
        anchor = p
        break
assert anchor is not None, "Could not find existing Table 2.1 entry"

# Find its position and insert after it (insert_paragraph_before on the
# paragraph AFTER it, i.e. the next sibling); simplest is to insert each new
# entry directly before the paragraph that currently follows the anchor.
following = anchor._p.getnext()
for entry in NEW_TABLE_ENTRIES:
    new_p = anchor.insert_paragraph_before(entry, style="table of figures")
    # move it to right after anchor by re-parenting before `following`
    anchor._p.addnext(new_p._p)
    anchor = new_p  # chain so subsequent entries stay in order

# --- List of Figures: insert after the last existing figure entry (4.11) ---
last_fig = None
for p in doc.paragraphs:
    if p.style.name == "table of figures" and p.text.strip().startswith("Figure"):
        last_fig = p
assert last_fig is not None, "Could not find existing figure entries"
new_fig_p = last_fig.insert_paragraph_before(NEW_FIGURE_ENTRY, style="table of figures")
last_fig._p.addprevious(new_fig_p._p)  # no-op reposition, already correct via insert_paragraph_before
# insert_paragraph_before already placed it right before last_fig; move it to AFTER instead
last_fig._p.addnext(new_fig_p._p)

doc.save(PATH)
print("Saved:", PATH)
