# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

Kashaf is the knowledge base + implementation of **Rawahil (الرواحل)**, an Arabic-language psychometric assessment system. Everything — governance documents, code comments, tool output — is in Arabic. The repository layout is deliberately **flat**: canonical filenames are load-bearing (manifests, the index, and cross-references cite them verbatim), and all tooling resolves sibling files by relative path. Do not reorganize into subdirectories or rename files.

This project is **governance-first**: its own documents define binding rules for how it may be changed. Read `00-HANDOVER_2026-08-05_Resume_Directive.md` before any build work. Every substantive change must be sealed as a decision (`DEC-NNN`) in `01-MASTER-Governance_Foundations_And_Decisions.md` and a change (`CHG-NNN`) in `02-MASTER-Tracking_And_Risks.md`, documented in a numbered analysis doc (`104-…`, `120-…`, `121-…`), and indexed in `00-INDEX_Master_Knowledge_Base_Index.md`. The current last-sealed decision and next number are in the `01-MASTER` header (`الترقيم التالي`). New work awaits the owner's explicit order — do not start build items on your own initiative.

## Setup (mandatory before any tests)

Requires `python3` and `node` (no package installs — zero external dependencies by design).

```bash
python3 build_packs.py                              # generates packs.js — REQUIRED first step
cp k3_contentpack_FIXED_DEC-195.py k3_contentpack.py  # legal rename
```

Both outputs — plus `Supervisor.html` (built by `build_supervisor_html.py`) — are gitignored and must **never be committed** (`CHG-054`). Also intentionally absent from the repo: `Kashaf.html` (the questionnaire instrument, lives in conversation) and `golden_k3_PRE-DEC-215.json`. Do not add them.

## Verification suite — the acceptance gate

All 22 tools must pass, and the five parity fingerprints must match **verbatim**. Any deviation ⇒ stop and report; do not commit.

```bash
python3 parity_py.py            # fingerprint 2711c24d8155819b — 125 logic cases
python3 parity_reports.py       # fingerprint 36ae94bfd5a8b60f — 142 reports
python3 parity_supervisor.py    # fingerprint 6b324f996856eac3 — 429 supervisor grades
python3 parity_k4.py            # fingerprint e32207bbb8853560 — 387 K4 cases (logic + report + its audit block + crossing surface)
python3 parity_supervisor_k4.py # fingerprint a0f83d78b8adbf53 — 982 supervisor grades on K4
python3 parity_messages.py      # exception-message parity, 15 paths
python3 parity_isolation.py     # isolation-audit parity, 826 texts
python3 parity_surface.py       # systematic surface sweep, 3214 fields
python3 verify_regen.py         # regeneration contract, 213 cases (all three circles)
python3 test_packs.py
python3 test_golden_k2.py       ;  python3 test_golden_k3.py
python3 test_report_k2.py       ;  python3 test_report_k3.py
python3 test_guard_sp.py        ;  python3 test_guard_lock.py
python3 guard_interp.py
python3 test_report_k4.py       ;  python3 k4_content.py
python3 test_site_build.py      # site/app build guard — also verifies docs/ is not stale
python3 test_supervisor_build.py # supervisor-tool build guard — *executes* the generated bundle
python3 supervisor.py --self-test
```

Each tool is a standalone script — run one directly to test one surface. `parity_*` tools shell out to `node` (`parity_js.js`, `parity_reports_js.js`, `_sup_node.js`).

## Architecture

**Dual implementation with measured parity.** Every engine/report/supervisor behavior exists twice — Python (`k2_engine.py`, `k3_engine.py`, `k2_report.py`, `k3_report.py`, `supervisor.py`) and JS (`engines.js`, `reports.js`, `supervisor_core.js`) — because the JS side is embedded in browser tools. The governing rule (`DEC-199`/`DEC-200`): every textual or logic change is made **in both versions**, then parity is measured; a single divergence freezes both sides — neither is preferred. Output surfaces are compared literally (including number formatting: explicit `_round2`/`.toFixed(1)`-style rendering, never language-default serialization — `ن-8`).

**Three circles, isolation enforced.** K4 (dائرة الإنجاز — seven executive valves WM/TI/F/PF/OR/TM/PER) was built across phases 0–8 (`DEC-257…266`) and now has its own twin engine (`k4_engine.py` + the `K4` module in `engines.js`), report builder (`k4_report.py` + `buildReportK4` in `reports.js`), content pack (`k4_contentpack.json`, zero-authoring — every string is verified to exist literally in its sealed source doc) and parity tool. `DEC-186` was lifted for K4 only (`DEC-266`) and K4 is now surfaced in the tool as a third report tab with its own crossing-reading surface (`DEC-270`); K1 remains an internal panel. The three circles partition the instrument exactly: 56 + 55 + 77 = 188 = 94×2 slots, verified in `build_site.validate_maps`.

**Two isolated circles.** K2 = eight thinking dimensions (A/C/E/H/O/R/S/St); K3 = five emotional-regulation skills (EP/IR/BI/CF/ST). An isolation wall (`DEC-205`) forbids passing values between them; `parity_isolation.py` polices it.

**Content flows through packs, not code.** Prose lives in JSON packs (`k2_contentpack.json`, `k2_userlayer_pack.json`, `k3_textlayer.json`, …) → `build_packs.py` embeds all thirteen (K4's `k4_contentpack.json` included since `DEC-270`) into the generated `packs.js` with SHA checks. Python loads the JSON directly (`k2_content.py`, `k3_content.py` — the latter enforces exactly 9 `REQUIRED_EXTERNAL` keys). Never hand-edit generated output; edit the JSON source and regenerate.

**Pipeline.** Questionnaire answers → `bridge.js` (raw → SP scores; item maps live in the instrument, not here) → engines (profile/bands/patterns) → report builders (nine-section Arabic reports, full + brief modes for K2) → output guards (`sp_gate.py`/`sp_gate.js`: no `SP%` codes or unregistered percentages may reach the reader) → `supervisor.py`/`supervisor_core.js` (grades a delivered report against its audit block — **all three circles** since `DEC-271`, with K4-specific grades for the declared-debt drift and the crossing surface's separation; `build_supervisor_html.py` generates the standalone browser tool, and `test_supervisor_build.py` *executes* the generated bundle rather than only reading it).

**Golden/regression anchors.** `golden_k2.json`, `golden_k3.json`, `parity_cases.json` are frozen references; `interp_registry.json` registers every approved interpolation (`ح-6`); `k2_lock_registry.json` governs lock phrasing (`ح-7`).

## Standing rules (binding, from the KB itself)

- **The measurement layer is untouchable** (`instrument_pin`): questionnaire items, scoring maps, and derived SP math may not be modified.
- **No invented thresholds** (`ن-7/④`) — numeric cutoffs must have a sealed source.
- **No temporal-difference reading** (`DEC-244`) and **no validity claims** (`DEC-246`).
- **A field is added checking, or not added at all** (`00-HANDOVER §6①`): audit fields that report a constant instead of measuring are a rejected pattern — the sole exception is a declared non-measuring field (like `accepted_debts`).
- Before judging any apparent spec deviation as a defect, **search the decision log first** — a sealed decision may govern it (see `120-VALID-STEPS_DEC-248.md` for the cautionary case).
- Commit messages reference the sealed `DEC`/`CHG` numbers; acceptance for any change is the 20-tool run with fingerprints unmoved.


## AI handoff bridge (owner-authorized draft)

For tasks explicitly entered by the owner in `.ai-handoff/TASK_QUEUE.json`:

1. Read `.ai-handoff/README.md`, `TASK_QUEUE.json`, and `HANDOFF.json`.
2. Work only inside the declared scope and obey every standing governance rule above.
3. Set the task to `in_progress` when starting.
4. Record changed files, commands, tests, blockers, and the last commit in `HANDOFF.json`.
5. Hand completed work to Codex with `status: ready_for_codex` and `next_actor: codex`.
6. For `changes_requested`, fix only the listed findings.
7. Stop at `max_iterations` with `owner_decision_required`.

This bridge does not authorize a governance, measurement, deployment, destructive, or merge action. Such actions still require explicit owner approval and the repository's DEC/CHG sealing process.
