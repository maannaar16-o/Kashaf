#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""فحوص جسر التسليم — **حقنةٌ مستقلّة لكل عيب** (`DEC-291`)

الحقنة التي تجمع عدّة مخالفاتٍ **تُثبت أن واحدةً منها رُصدت ولا تقول
أيّها** — فكلُّ عيبٍ هنا يُحقن **وحده** في حالةٍ سليمةٍ بغيره.

وتُقاس ثلاث جهات: **الانتقالات المشروعة تمرّ** (فحرسٌ يرفض الصحيح
كما يرفض الخطأ لا يصلح) · **وغيرُ المشروعة تسقط** · **والبصمة تُفحص
صدقاً لا شكلاً**.
"""
import os
import sys
from copy import deepcopy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import validate_ai_handoff as V

FAILS = []


def check(label, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + label + (" - " + detail if detail else ""))
    if not ok:
        FAILS.append(label)


# ── حالةٌ سليمة يُحقن فيها عيبٌ واحدٌ في كل مرّة ─────────────────────────
TASK_ID = "T-001"


def task(status="in_progress", actor="claude", it=0, mx=3):
    return {"id": TASK_ID, "title": "t", "status": status, "next_actor": actor,
            "iteration": it, "max_iterations": mx}


def queue(**kw):
    return {"protocol_version": "1.1", "active_task_id": TASK_ID,
            "tasks": [task(**kw)]}


def handoff(status="in_progress", to="claude", it=0, sha=None):
    return {"protocol_version": "1.1", "task_id": TASK_ID, "status": status,
            "from_actor": "claude", "to_actor": to, "iteration": it,
            "summary": "s", "changed_files": [], "commands_run": [],
            "tests": [], "findings": [], "blockers": [],
            "decisions_needed": [], "last_commit": sha}


class Probe:
    """`git` وهميّ — تُملى عليه الحقيقة فيُقاس المدقّق لا البيئة."""

    def __init__(self, exists=True, ancestor=True, shallow=False, own=None):
        self._e, self._a, self._s, self._own = exists, ancestor, shallow, own

    def is_shallow(self):
        return self._s

    def exists(self, sha):
        return self._e

    def is_ancestor(self, sha):
        return self._a

    def last_handoff_commit(self):
        return self._own


OK_PROBE = Probe(own="ffffffffffffffffffffffffffffffffffffffff")


def errs(q, h, history=(), probe=OK_PROBE):
    e, _c, _s = V.validate(q, h, history, probe)
    return e


# ── ٠) الحالة السليمة تمرّ — وإلّا فما بعدها بلا معنى ────────────────────
def test_clean():
    check("0 الحالة السليمة تمرّ بلا خطأ", not errs(queue(), handoff()),
          str(errs(queue(), handoff()))[:80])


# ── ١) الانتقالات المشروعة **تمرّ** ──────────────────────────────────────
LEGAL = [("queued", "in_progress", 0, 0),
         ("in_progress", "ready_for_codex", 0, 0),
         ("ready_for_codex", "approved", 0, 0),
         ("ready_for_codex", "changes_requested", 0, 1),
         ("changes_requested", "in_progress", 1, 1)]


def test_legal_transitions():
    for a, b, i0, i1 in LEGAL:
        hist = [(queue(status=a, it=i0), handoff(status=a, it=i0)),
                (queue(status=b, it=i1), handoff(status=b, it=i1))]
        e = V.transition_errors(*hist[0], *hist[1])
        check(f"1 انتقالٌ مشروع يمرّ: {a} → {b}", e == [], str(e)[:90])
    # وبلوغُ الحدّ الأقصى ينتهي إلى وقفةِ المالك — لا إلى دورةٍ سادسة
    e = V.transition_errors(queue(status="ready_for_codex", it=2),
                            handoff(status="ready_for_codex", it=2),
                            queue(status="owner_decision_required", it=2),
                            handoff(status="owner_decision_required", it=2))
    check("1 بلوغ الحدّ → owner_decision_required يمرّ", e == [], str(e)[:90])
    # والبقاءُ في الحالة نفسها (التزاماتُ تنفيذٍ متتابعة) مشروع
    e = V.transition_errors(queue(), handoff(), queue(), handoff())
    check("1 البقاء في الحالة نفسها مشروع", e == [], str(e)[:90])


# ── ٢) حقنات `AIB-01` — كلُّ عيبٍ وحده ───────────────────────────────────
def test_illegal_transition():
    e = V.transition_errors(queue(status="queued"), handoff(status="queued"),
                            queue(status="approved"), handoff(status="approved"))
    check("2 حقنة: قفزةٌ queued → approved", any("illegal transition" in x for x in e),
          str(e)[:90])


def test_after_terminal():
    e = V.transition_errors(queue(status="approved"), handoff(status="approved"),
                            queue(status="in_progress"), handoff(status="in_progress"))
    check("2 حقنة: انتقالٌ بعد الحالة النهائية approved",
          any("illegal transition" in x for x in e), str(e)[:90])


def test_status_mismatch():
    # البصمة صحيحةٌ عمداً: الحقنة **عيبٌ واحد** لا عيبان مجتمعان
    e = errs(queue(status="in_progress"),
             handoff(status="ready_for_codex", sha="a" * 40))
    check("2 حقنة: حالةُ المهمّة ≠ حالةُ التسليم",
          len(e) == 1 and "must equal HANDOFF.status" in e[0], str(e)[:90])


def test_actor_mismatch():
    e = errs(queue(actor="codex"), handoff(to="claude"))
    check("2 حقنة: next_actor ≠ to_actor",
          any("must equal HANDOFF.to_actor" in x for x in e), str(e)[:90])


def test_active_mismatch():
    q = queue(); q["active_task_id"] = "T-OTHER"
    e = errs(q, handoff())
    check("2 حقنة: المهمّة النشطة ليست مهمّة التسليم",
          any("active_task_id" in x for x in e), str(e)[:90])


def test_iteration_bump_without_reason():
    e = V.transition_errors(queue(it=0), handoff(it=0),
                            queue(it=1), handoff(it=1))
    check("2 حقنة: iteration تزيد بلا طلب تصحيح",
          any("may only change" in x for x in e), str(e)[:90])


def test_iteration_wrong_delta():
    e = V.transition_errors(queue(status="ready_for_codex", it=0),
                            handoff(status="ready_for_codex", it=0),
                            queue(status="changes_requested", it=2),
                            handoff(status="changes_requested", it=2))
    check("2 حقنة: iteration تقفز اثنتين لا واحدة",
          any("exactly 1" in x for x in e), str(e)[:90])


def test_iteration_decrease():
    e = V.transition_errors(queue(it=2), handoff(it=2), queue(it=1), handoff(it=1))
    check("2 حقنة: iteration تنقص",
          any("must not decrease" in x for x in e), str(e)[:90])


def test_max_reached_but_running():
    e = errs(queue(status="in_progress", it=3, mx=3), handoff(status="in_progress", it=3))
    check("2 حقنة: بلغت الحدّ وما زالت جارية",
          any("reached max_iterations" in x for x in e), str(e)[:90])


def test_new_task_starts_midcycle():
    prev_q, prev_h = queue(status="approved"), handoff(status="approved")
    cur_q, cur_h = deepcopy(queue(status="ready_for_codex")), \
        deepcopy(handoff(status="ready_for_codex"))
    for o in (cur_q["tasks"][0], cur_h):
        o["id" if "id" in o and o is not cur_h else "task_id"] = "T-002"
    cur_q["active_task_id"] = "T-002"
    e = V.transition_errors(prev_q, prev_h, cur_q, cur_h)
    check("2 حقنة: مهمّةٌ جديدة تبدأ من منتصف الدورة",
          any("must start at" in x for x in e), str(e)[:90])


# ── ٣) حقنات `AIB-02` — صدقُ البصمة، كلٌّ وحده ───────────────────────────
GOOD = "a" * 40


def test_commit_required():
    e = V.commit_errors(handoff(status="ready_for_codex", sha=None), OK_PROBE)
    check("3 حقنة: تسليمٌ للمراجعة بلا بصمة",
          any("is required" in x for x in e), str(e)[:90])


def test_commit_malformed():
    e = V.commit_errors(handoff(status="ready_for_codex", sha="not-a-sha"), OK_PROBE)
    check("3 حقنة: بصمةٌ ليست SHA", any("not a valid sha" in x for x in e), str(e)[:90])


def test_commit_dead():
    e = V.commit_errors(handoff(status="ready_for_codex", sha=GOOD),
                        Probe(exists=False))
    check("3 حقنة: بصمةٌ لالتزامٍ غير موجود",
          any("does not exist" in x for x in e), str(e)[:90])


def test_commit_orphan():
    e = V.commit_errors(handoff(status="ready_for_codex", sha=GOOD),
                        Probe(ancestor=False))
    check("3 حقنة: بصمةٌ يتيمةٌ غير بالغةٍ من الفرع",
          any("not reachable" in x for x in e), str(e)[:90])


def test_commit_circular():
    e = V.commit_errors(handoff(status="ready_for_codex", sha=GOOD),
                        Probe(own=GOOD))
    check("3 حقنة: بصمةٌ تشير إلى التزام السجلّ نفسه (ادّعاءٌ دائري)",
          any("circular claim" in x for x in e), str(e)[:90])


def test_commit_shallow():
    e = V.commit_errors(handoff(status="ready_for_codex", sha=GOOD),
                        Probe(shallow=True))
    check("3 حقنة: مستنسخٌ ضحل — يُقال متعذّراً لا يُمرَّر",
          any("shallow clone" in x for x in e), str(e)[:90])


def test_commit_valid_passes():
    check("3 بصمةٌ صادقة تمرّ",
          V.commit_errors(handoff(status="ready_for_codex", sha=GOOD), OK_PROBE) == [],
          "")


# ── ٤) الأثر الرجعي مرفوض — واللقطات القديمة تُستثنى وتُعدّ ─────────────
def test_legacy_snapshot_skipped():
    old_q, old_h = queue(status="queued"), handoff(status="queued")
    old_q["protocol_version"] = old_h["protocol_version"] = "1.0"
    step = V.transition_errors(old_q, old_h, queue(status="approved"),
                               handoff(status="approved"))
    check("4 لقطةٌ أقدم من 1.1 تُستثنى من قياس الانتقال", step is None,
          str(step)[:80])
    hist = [(old_q, old_h), (queue(), handoff())]
    _e, checked, skipped = V.validate(queue(), handoff(), hist, OK_PROBE)
    check("4 والمستثنى يُعدّ ويُعلَن لا يُسكت عنه",
          (checked, skipped) == (0, 1), f"مقيس {checked} · مستثنىً {skipped}")


if __name__ == "__main__":
    print("=" * 76)
    test_clean()
    test_legal_transitions()
    test_illegal_transition()
    test_after_terminal()
    test_status_mismatch()
    test_actor_mismatch()
    test_active_mismatch()
    test_iteration_bump_without_reason()
    test_iteration_wrong_delta()
    test_iteration_decrease()
    test_max_reached_but_running()
    test_new_task_starts_midcycle()
    test_commit_required()
    test_commit_malformed()
    test_commit_dead()
    test_commit_orphan()
    test_commit_circular()
    test_commit_shallow()
    test_commit_valid_passes()
    test_legacy_snapshot_skipped()
    print("-" * 76)
    if FAILS:
        print("النتيجة النهائية: انحدار - " + str(len(FAILS)) + ": " +
              " · ".join(FAILS))
        raise SystemExit(1)
    print("النتيجة النهائية: لا انحدار")
