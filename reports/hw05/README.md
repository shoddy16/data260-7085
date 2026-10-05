# HW5 report files

- `Waingankar_HW5.pdf` is the current formatted draft. Yellow evidence panels are explicit placeholders and do not count as screenshots.
- `build_report.py` rebuilds the PDF from the saved raw results, reflection, AI-use disclosure, and verification record. If a required screenshot exists in `screenshots/` with the exact filename shown in `EVIDENCE_CHECKLIST.md`, the builder inserts that image in place of its placeholder.
- `EVIDENCE_CHECKLIST.md` gives the exact required capture names, UI/action, and visible result for the remaining GUI captures.
- The current PDF was rendered and visually checked at all 14 pages. It is not final because screenshots are not saved and final verification, Git review, commit, and `hw5` tag are pending.

To rebuild after adding captures, from the repository root run:

```powershell
python reports/hw05/build_report.py
```

Then visually inspect the regenerated PDF and rerun the HW5 verification before finalizing.
