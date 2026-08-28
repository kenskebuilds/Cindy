# The Deficit Hypertrophy Protocol

A 5-day training split for a 40-year-old intermediate-advanced lifter in a caloric deficit. Primary outcome is hypertrophy; fat loss is secondary and handled by the diet. Every dose is traced to a citation, every citation is graded high/medium/low, and the plan is checked against nine explicit constraints in a validation report rather than asserted.

Open `index.html`, or serve via GitHub Pages.

## Build

    python build.py

Source of truth is `src/protocol.html`. `build.py` wraps it into the standalone page, forces the light theme, and groups the twelve sections into four tabs. Every section must be assigned to a tab in `TABS` or the build aborts.

## Notes

- `robots.txt` and a `noindex` meta tag are included to discourage search indexing. They are not access control - anything on a public GitHub Pages site is publicly readable.
- Single self-contained file. The only external request is Google Fonts.
- General training and nutrition analysis, not medical advice.
