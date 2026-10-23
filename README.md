# CounselCopilot (NDA Reviewer Agent)

LMA group project (team 2025201049 · 2025201044 · 2025201068 · 2025201038). CounselCopilot checks a consultant's
NDA draft against company policy and US law with applicability-aware two-way retrieval (RQ1), and hardens it with a
red-team and repair loop (RQ2). The benchmark is PolicyNDA, built on ContractNLI.

- `proposal/proposal.pdf`: the 5-page proposal (`proposal.tex` is the source; other files there are older versions)
- `newdesign.md`: full design (§19 is the latest audit); `ta_change_note.md`: changes since the approved proposal
- `code/`: the Python package, packs, labels and planted benchmark; see `code/README.md`
- `prop.pdf`: the course project brief; other `.md` files are earlier notes and reviews

ContractNLI itself is not in the repo: `cd code && cc data download`.
