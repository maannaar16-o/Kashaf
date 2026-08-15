# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

Kashaf is the knowledge base + implementation of **Rawahil (الرواحل)**, an Arabic-language psychometric assessment system. Everything — governance documents, code comments, tool output — is in Arabic. The repository layout is deliberately **flat**: canonical filenames are load-bearing (manifests, the index, and cross-references cite them verbatim), and all tooling resolves sibling files by relative path. Do not reorganize into subdirectories or rename files.

This project is **governance-first**: its own documents define binding rules for how it may be changed. Read `00-HANDOVER_2026-08-05_Resume_Directive.md` before any build work — its §1 is a twelve-mark resume gate, and any mark that fails means *stop and report*, not *proceed carefully*. Every substantive change must be sealed as a decision (`DEC-NNN`) in `01-MASTER-Governance_Foundations_And_Decisions.md` and a change (`CHG-NNN`) in `02-MASTER-Tracking_And_Risks.md`, documented in a numbered analysis doc (`104-…`, `120-…`, `146-…`), and indexed in `00-INDEX_Master_Knowledge_Base_Index.md`. The current last-sealed decision and next number are in the `01-MASTER` header (`الترقيم التالي`) — that header is the only authority for the number, and `gate.py` verifies it equals *highest + 1*. New work awaits the owner's explicit order — do not start build items on your own initiative.

## Setup (mandatory before any tests)

Requires `python3` and `node` (no package installs — zero external dependencies by design, and the CI workflow deliberately runs no `pip install`/`npm install`).

```bash
python3 build_packs.py                              # generates packs.js — REQUIRED first step
cp k3_contentpack_FIXED_DEC-195.py k3_contentpack.py  # legal rename
```

Without the first step, `parity_reports` and `test_packs` fail with `Cannot find module './packs.js'`. Both outputs — plus `Supervisor.html` (built by `build_supervisor_html.py`), `Workshop.html` (built by `build_workshop_html.py`, `DEC-279`) and the whole `workshop_data/` directory (participant data, `DEC-277`) — are gitignored and must **never be committed** (`CHG-054`, machine-checked by `gate.py`). `gate.py` performs both setup steps itself. Also intentionally absent from the repo: `Kashaf.html` (the sealed questionnaire instrument, lives in conversation) and `golden_k3_PRE-DEC-215.json`. Do not add them. Everything else already carries its legal name — do not rename `k2_engine` / `k3_engine` / `k2_report` / `k3_report` / `k3_content`.

## Verification suite — the acceptance gate

All 25 tools must pass, and the six frozen fingerprints must match **verbatim** — five are *parity* fingerprints (Python ⇄ JS) and the sixth is a *regression* fingerprint (`test_report_team.py`; the team layer is Python-only, see Architecture). Any deviation ⇒ stop and report; do not commit. A fingerprint may only move by a prior, justified declaration inside a sealed decision — **a silent shift is a rejected outcome**, not a new baseline. (`DEC-280 §4` is the worked example: the team fingerprint moved, and the decision states what changed, that it was measured before the new case was added, and therefore that behavior on the existing cases did not shift.)

**Run the whole gate with one command — `gate.py` is the single authority** (`DEC-273`): it holds the tool list and the six expected fingerprints and matches them literally. CI (`.github/workflows/gate.yml`) runs exactly this on every push and PR — so never maintain a second copy of the list anywhere.

```bash
python3 gate.py                 # setup + 25 tools + 6 fingerprints + the six self-checks below
python3 gate.py --list          # the list and its fingerprints, without running
```

Beyond running the tools, the gate enforces six things about itself and the repo:

| # | Self-check | Why it exists |
| :-- | :-- | :-- |
| ① | tools run, fingerprints match literally | the baseline |
| ② | zero tool on disk that is not listed (`parity_*` / `test_*` / `guard_*` / `verify_*`), and every listed tool exists | this class broke silently three times |
| ③ | `CLAUDE.md` and `00-HANDOVER` have not drifted from the gate — same tool list, zero stale fingerprint | docs that describe the gate are *checked against it, not believed* |
| ④ | no generated artifact has become git-tracked (`CHG-054`) | `git ls-files` knows the truth; attention does not |
| ⑤ | numbering integrity (`DEC-274`): zero duplicate `DEC`/`CHG`, zero colliding document code, `الترقيم التالي` = highest + 1 | concurrent actors race for numbers |
| ⑥ | declared debts in `146 §5` = `open_debts` in the K4 engine (`DEC-276`) | the last manual sync became a measured one |

Because of ③, **this file is machine-checked**: every script invoked here with `python3` must belong to the gate's list (only `build_packs.py`, `build_site.py`, `build_supervisor_html.py`, `gate.py` are exempt — so do not write an invocation line for any other script, not even a placeholder), and any 16-hex string near the word fingerprint/parity must be one the gate knows. Editing this section carelessly turns the gate red.

The individual tools (run one directly to test one surface):

```bash
python3 parity_py.py            # fingerprint 2711c24d8155819b — 125 logic cases
python3 parity_reports.py       # fingerprint 36ae94bfd5a8b60f — 142 reports
python3 parity_supervisor.py    # fingerprint 6b324f996856eac3 — 429 supervisor grades
python3 parity_k4.py            # fingerprint 94434230e7dbc0f0 — 387 K4 cases (logic + report + its audit block + crossing surface)
python3 parity_supervisor_k4.py # fingerprint 72790080dc0df8d2 — 80 payloads, 982 supervisor grades on K4
python3 parity_messages.py      # exception-message parity, 15 paths
python3 parity_isolation.py     # isolation-audit parity, 826 texts
python3 parity_surface.py       # systematic surface sweep, 3214 fields (incl. the K2/K3 item maps, py ⇄ js)
python3 verify_regen.py         # regeneration contract, 213 cases (all three circles)
python3 test_packs.py
python3 test_golden_k2.py       ;  python3 test_golden_k3.py
python3 test_report_k2.py       ;  python3 test_report_k3.py
python3 test_guard_sp.py        ;  python3 test_guard_lock.py
python3 guard_interp.py
python3 test_report_k4.py       ;  python3 k4_content.py
python3 test_report_team.py     # fingerprint 21532a8aba568a2d — team-composition contract
python3 test_workshop.py        # workshop-path contract — supervisor-as-admission-gate
python3 test_owner_console.py   # owner-console contract — conditional ح-4 lift, isolation, declared voids
python3 test_site_build.py      # site/app build guard — also verifies docs/ is not stale
python3 test_supervisor_build.py # supervisor-tool build guard — *executes* the generated bundle
python3 supervisor.py --self-test
```

Each tool is a standalone script — run one directly to test one surface. `parity_*` tools shell out to `node` (`parity_js.js`, `parity_k4_js.js`, `parity_reports_js.js`, `_sup_node.js`).

The measured scope is **eight surfaces**: engine logic · report text · supervisor grades · exception messages · isolation audit + audit block · constants, instrument items, raw→SP and the boundary grid · K4's logic, report and crossing surface · site/app build and `docs/` sync.

## Architecture

**Dual implementation with measured parity.** Every engine/report/supervisor behavior exists twice — Python (`k2_engine.py`, `k3_engine.py`, `k4_engine.py`, `k2_report.py`, `k3_report.py`, `k4_report.py`, `supervisor.py`) and JS (`engines.js`, `reports.js`, `supervisor_core.js`) — because the JS side is embedded in browser tools. The governing rule (`DEC-199`/`DEC-200`): every textual or logic change is made **in both versions**, then parity is measured; a single divergence freezes both sides — neither is preferred. Output surfaces are compared literally (including number formatting: explicit `_round2`/`.toFixed(1)`-style rendering, never language-default serialization — `ن-8`). The team layer is the **declared exception**: it is Python-only (precedent `DEC-254`), so its anchor is a regression fingerprint, not a parity one.

**Three circles.** K2 = eight thinking dimensions (A/C/E/H/O/R/S/St). K3 = five emotional-regulation skills (EP/IR/BI/CF/ST). K4 (دائرة الإنجاز — seven executive valves WM/TI/F/PF/OR/TM/PER) was built across phases 0–8 (`DEC-257…266`) and has its own twin engine, report builder (`buildReportK4` in `reports.js`), content pack (`k4_contentpack.json`, zero-authoring — every string is verified to exist literally in its sealed source doc) and parity tool. `DEC-186` was lifted for K4 only (`DEC-266`); K4 is surfaced in the tool as a third report tab with its own crossing-reading surface (`DEC-270`); K1 remains an internal panel. The three circles partition the instrument exactly: 56 + 55 + 77 = 188 = 94×2 slots, verified in `build_site.validate_maps`.

**Isolation wall.** `DEC-205` forbids passing values between circles; `parity_isolation.py` polices it, and cross-circle work (`contrib_analyze.py`, the crossing surfaces) builds each circle's index separately.

**Item maps are read, never defined.** Each engine now carries its circle's item map — `K2_ITEM_MAP` in `k2_engine`, `ITEM_MAP` in `k3_engine` (`DEC-275`) and in `k4_engine` (`DEC-270`) — derived by parsing the sealed tables (`41 §5.3` and friends) and re-checked against them on every build in `build_site.validate_maps`. This is *exposure of the measurement layer, not a change to it* (`instrument_pin`): no item, pole, weight or equation is defined in code. The scoring equation stays in one place only — duplicating `score_from_raw` into an engine would create a second authority over one equation (`م-2`), which is why `DEC-275` deliberately did not add it. `build_site.py` derives its maps from the engines rather than holding its own copy, for the same reason.

**Content flows through packs, not code.** Prose lives in JSON packs (`k2_contentpack.json`, `k2_userlayer_pack.json`, `k3_textlayer.json`, `k4_contentpack.json`, …) → `build_packs.py` embeds all thirteen into the generated `packs.js` with SHA checks (`packs_manifest.json`). Python loads the JSON directly (`k2_content.py`, `k3_content.py` — the latter enforces exactly 9 `REQUIRED_EXTERNAL` keys — and `k4_content.py`). Never hand-edit generated output; edit the JSON source and regenerate.

**Pipeline.** Questionnaire answers → `bridge.js` (raw → SP scores) → engines (profile/bands/patterns) → report builders (nine-section Arabic reports, full + brief modes for K2) → output guards (`sp_gate.py`/`sp_gate.js`: no `SP%` codes or unregistered percentages may reach the reader) → `supervisor.py`/`supervisor_core.js`, which grades a delivered report against its audit block — **all three circles** since `DEC-271`, with K4-specific grades for the declared-debt drift and the crossing surface's separation. `build_supervisor_html.py` generates the standalone browser tool, and `test_supervisor_build.py` *executes* the generated bundle rather than only reading it.

**Site and app.** `build_site.py` assembles the public site and the browser instrument from `site/` (`templates/`, `content/`, `static/`, `vendor/`, `app/`, `checks/`, `contrib-receiver/`) plus the sealed docs, and writes the eight tracked pages in `docs/` — including `docs/kashaf.html`, a *generated* embodiment of the questionnaire with three report tabs (`DEC-250`…`DEC-270`). It does not replace or copy the sealed instrument: its measurement layer is read, not defined. `test_site_build.py` runs the build's own JS checks and fails if `docs/` is stale relative to the sources — regenerate and commit `docs/` whenever anything upstream of it changes.

**Team composition (`DEC-277`/`DEC-278`).** `team_engine.py` + `team_report.py` + `team_contentpack.json` (embedded by `build_team_pack.py`) operationalize the sealed `56-TEAM-00` charter — Python-only, hence the regression fingerprint. The engine **defines no threshold and computes no score**: thresholds are read from `k2_engine.comp_state` (one authority), and its input is *approved individual reports* under an input contract — a violation raises `InputContractError` and stops, never a silent fix. It knows the eight K2 lenses only and rejects any field from another circle. Its three generation rules — polar pair first then top dominant each; a documented blindspot combination applies only under *full* containment, not partial overlap; and rebound shows **every** dominant lens — were read from the approved dry run `56-TEAM-P001`, raised as readings, then sealed by the owner into `56-TEAM-00 §7` (`DEC-282`). Each is checked **by name**, not merely held by the fingerprint: a fingerprint proves *unchanged*, never *correct*. Their declared limit is written beside them — proven over the dry run's range (three members with distinct dominants), applied beyond it on their seal, not on that proof. The report is nine sections of sealed cells under sealed headings with **zero authored connective text**, enforcing five locks: no differential comparison or ranking of members, no raw `SP` in the body, zero generation, the `G4` display lock printed in §9, and zero K1/K3/K4 contact.

**Workshop path (`DEC-277`/`DEC-279`).** A separate, code-gated path for coach-run sessions. The rule it establishes: **a published promise is not revoked to add a path — the path is added declaring its own terms.** The public site keeps its promise verbatim ("your answers never leave your device"); the workshop surface announces the opposite up front, and there is **no retroactive migration** of anyone who answered under the old promise. `ح-4` (no `SP%` reaches a reader) is lifted **only on the owner's workshop surface**, on the `DEC-186`-for-K4 precedent — a lift bounded to its scope, resting on the pre-existing "explicit prior permission" clause, not an invented exception. `Workshop.html` (built by `build_workshop_html.py`) **narrows** the network lock rather than lifting it: every connection forbidden except one same-origin `POST /submit`. `workshop_server.py` is stdlib-only with exactly two routes (everything else 404, no path derived from the request) and binds `127.0.0.1` unless the owner passes an explicit flag. `workshop_store.py` makes the supervisor an **admission gate, not a later check** — a payload is graded before storage and a report that fails the audit is returned with its grade, never silently stored. **Zero credentials are stored** (no password, no hash): the owner issues the code, and the code↔name mapping lives outside the store, so the store holds a code and a report — never a name.

**Data-subject rights and where identity lives (`DEC-286`).** `workshop_store.py` implements the two rights `DEC-277 §5` promised: `export <code>` hands a participant their own record, and `forget <code>` erases the record **and the code registry entry together** — it re-checks after erasing and raises rather than leave a half-erase, and it prints what was removed, because a silent erase neither reassures the subject nor holds the owner accountable. The code↔name registry is `workshop_codes.json`, deliberately **outside** `workshop_data/` (both gitignored): the harvest directory therefore contains no name, so a copy of it can be moved or shared without carrying identity, and the store's own claim — "a code and a report, never a name" — is true of the directory and not only of the records. An older registry found inside the store is migrated with the move announced, never silently. Operating steps live in `56-WORKSHOP-RUNBOOK`, not in chat.

**Owner console (`DEC-280`).** `owner_console.py` reads the workshop harvest for the owner — raw scores, grades and the team map. It is an **operator tool, not a web page**: never served, never bundled into a browser pack (`DEC-254` precedent), which is what keeps the team layer's deferral guard valid. It carries **no fingerprint by design** — its output follows changing harvest data, so freezing one would be a false claim of stability; what is measured is *boundary behavior*, not print shape. The `ح-4` lift here is **conditional and executed, not recited**: every record's consent is matched against its approved text literally before any raw number from it is shown, a record without matching consent has its raw values **withheld with the withholding announced** (a silently dropped record would read as never received), and the withholding message itself leaks no number. The console prints its own **declared voids** — no temporal difference (`DEC-244`), no cohort-derived norm, no discrimination test on four, no competence verdict (the mandatory caution is read from the team pack, not copied) — on the reasoning that a limit written in a distant document is forgotten while one printed in the tool is seen. `GAP-TEAM-02` was found by *running* it, not by review: two members sharing a top dominant (`A–A`) have no sealed cell in the 28-pair matrix, and it is resolved by **declaring the void with both lenses shown** (`م-8`) rather than inventing a cell or a fallback rule. The owner ratified that resolution as a permanent rule (`DEC-281`), which closed `GAP-TEAM-02` and amended the charter — so a pair that crosses on one lens prints `A–A` and four dashes, with no authored explanation in the body: the explanation belongs to governance, not to the reader's report.

**Field-data channel (owner-operated).** `contrib_pull.py` drains the contribution store and validates each record against `RAWAHIL-CONTRIB-v1` literally (bad records are quarantined and reported, never silently fixed or dropped); `contrib_analyze.py` produces the four-axis preliminary reading — it **describes and ranks, never judges**: no invented threshold (`ن-7/④`), no validity claim (`DEC-246`). Credentials come from the owner's environment variables and are never committed; all four outputs are gitignored (field data is not a knowledge document). These tools are outside the gate's tool list by design.

**Reader-facing text has one legal route (`DEC-283`).** K4 reports open with a derivation notice in the reader's own language. When no sealed sentence carried that meaning — the only candidate was bound to a different context, and zero-authoring forbids writing one into a pack — the sentence was **sealed in a governing document first, then transferred verbatim**, and that document was added to the pack's `sources` so the zero-authoring check measures the transfer like any other string. Zero-authoring is therefore a constraint on *where* text is written, not a reason text cannot exist. The governance-facing tag (`TRF-002`) stays where it was: two places, each for its audience, and never a second wording for one tag.

**Golden/regression anchors.** `golden_k2.json`, `golden_k3.json`, `parity_cases.json`, `parity_cases_k4.json`, `team_cases.json` are frozen references; `interp_registry.json` registers every approved interpolation (`ح-6`); `k2_lock_registry.json` governs lock phrasing (`ح-7`). Active guards: `ح-1`…`ح-3` (packs), `ح-4` (`SP%`), `ح-5` (unregistered percentage), `ح-6`, `ح-7`, `ص-1…ص-3` (K3), `ت-6` (no threshold).

## Reading the knowledge base

Filename prefixes are the map — the flat layout is indexed, not sorted:

| Prefix | Content |
| :-- | :-- |
| `00-*` | handover, index, manifests, protocols, session closures, patch packs |
| `01-MASTER` / `02-MASTER` | the decision log (`DEC`) and the tracking/risk log (`CHG`, guards, debts) |
| `10`–`14-CORE` | constitutions: core theory, K1, K3, K4 |
| `19`, `56-*` | seeds, report-engine specification, pilots, team protocol, golden references |
| `20`–`23-THINK` | architecture review and the CSLIM matrices |
| `30`, `40`, `41` | K2 operational map and the measurement instrument (**sealed**) |
| `50-DEPTH-*` | per-dimension depth documents (K2 / K3 / K4) |
| `51`/`52-MATRIX-*` | dyadic, polar, fallback, blindspot, lookalike and retrieval registries |
| `55-USER-*` | user-layer prose per dimension |
| `57`–`99` | K3 build chain, parity/port records, gap and defect dossiers |
| `100`–`150` | numbered analysis docs, one per decision or decision cluster |

`00-INDEX_Master_Knowledge_Base_Index.md` lists them all; `00-CROSSMAP_K1_Code_Equivalence_Table.md` maps K1 concepts to code.

## Standing rules (binding, from the KB itself)

- **The measurement layer is untouchable** (`instrument_pin`): questionnaire items, scoring maps, and derived SP math may not be modified. Exposing a sealed table in code is allowed only when it is parsed from that table and machine-compared against it.
- **No invented thresholds** (`ن-7/④`) — numeric cutoffs must have a sealed source.
- **No temporal-difference reading** (`DEC-244`) and **no validity claims** (`DEC-246`).
- **A field is added checking, or not added at all** (`00-HANDOVER §6①`): audit fields that report a constant instead of measuring are a rejected pattern — the sole exception is a declared non-measuring field (like `accepted_debts`).
- **One authority per fact** (`م-2`): never create a second copy of a list, rule, equation or map. `DEC-273` (list in three places), `DEC-274` (rule in two) and `DEC-275` (map copied into the build layer) were all settlements of exactly this.
- **Silence is legitimate** (`م-8`): a gap with no sealed material is bounded and declared, not filled with authored text. Cosmetic closure — making a register *look* complete — is a named, rejected pattern (`137 §5`). `DEC-276` triaged the open items on that basis: some wait on field data, some on human judgment, some are the instrument's declared limit and will never close.
- Before judging any apparent spec deviation as a defect, **search the decision log first** — a sealed decision may govern it (see `120-VALID-STEPS_DEC-248.md` for the cautionary case).
- Commit messages reference the sealed `DEC`/`CHG` numbers; acceptance for any change is `python3 gate.py` green.
- **Numbering under concurrent actors** (`DEC-274`): reading `الترقيم التالي` from `01-MASTER` is a *candidacy, not a reservation* — **the push creates the right**. If another actor took the number first, do **not** force-push: renumber your `DEC`/`CHG`/document code to the next free one, keep `01-MASTER` in chronological order (their row before yours), and record the collision in `02-MASTER`. `gate.py` fails on a duplicate number or a colliding document code, so a collision cannot merge silently.

## AI handoff bridge (owner-authorized draft)

Two agents share this repo: Claude Code implements, Codex reviews (`AGENTS.md` is Codex's counterpart to this file). For tasks explicitly entered by the owner in `.ai-handoff/TASK_QUEUE.json`:

1. Read `.ai-handoff/README.md`, `TASK_QUEUE.json`, and `HANDOFF.json`.
2. Work only inside the declared scope (`allowed_paths` / `forbidden_paths`) and obey every standing governance rule above.
3. Set the task to `in_progress` when starting.
4. Record changed files, commands, tests, blockers, and the last commit in `HANDOFF.json`.
5. Hand completed work to Codex with `status: ready_for_codex` and `next_actor: codex`.
6. For `changes_requested`, fix only the listed findings; increment `iteration`.
7. Stop at `max_iterations` (3) with `owner_decision_required`.

State machine: `queued` → `in_progress` → `ready_for_codex` → `approved`, with `ready_for_codex` → `changes_requested` → `in_progress` for rework and `owner_decision_required` / `blocked` as halts. `.github/workflows/ai-handoff-validate.yml` runs `scripts/validate_ai_handoff.py` on any change to the bridge files, so a malformed handoff fails CI.

This bridge does not authorize a governance, measurement, deployment, destructive, or merge action. Such actions still require explicit owner approval and the repository's DEC/CHG sealing process. No secrets or API keys ever enter the repository.
