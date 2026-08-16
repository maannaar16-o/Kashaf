#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""مدقّق جسر التسليم — `DEC-272` (الجسر) · `DEC-291` (التقوية)

كان يفحص **الشكل**: أن الحقل موجودٌ ومن النوع الصحيح. فمرّت عليه ثلاث
مخالفاتٍ معاً (`AIB-01`) وبصمةُ التزامٍ يتيمة (`AIB-02`) — **و«اجتياز
المدقّق» كان يُقرأ أوسع ممّا يقيس**.

فصار يفحص **ثلاثة أشياء لا واحداً**:

  ① **الانتقال**: آلة الحالات منصوصةٌ صراحةً أدناه، والانتقال يُقاس
     **بين لقطتَي التزامَين** لا يُصدَّق من حقلٍ يصف نفسه.
  ② **الاتساق**: حالةُ المهمّة = حالةُ التسليم · `next_actor` = `to_actor`
     · والمهمّة النشطة هي التي يشير إليها التسليم · و`iteration` لا
     تزيد إلّا حيث يأذن البروتوكول.
  ③ **الصدق**: `last_commit` بصمةٌ **قائمةٌ وبالغةٌ وغير دائرية**.

**والدلالة معرَّفةٌ بلا دَور** (`§5` من أمر المهمّة): ملفٌّ **لا يسع أن
يحوي بصمةَ الالتزام الذي يحويه** — فحُدّت الدلالة بما لا يستلزم ذلك:

    `last_commit` = **آخر التزامٍ تنفيذيّ يسبق التزامَ سجلّ التسليم**

فهو يشير إلى **ما يُراجَع** لا إلى نفسه؛ وسجلُّ التسليم يُكتب في التزامٍ
تالٍ يقرؤه المراجع **رأساً للفرع** لا بصمةً مكتوبة. **والدائرية تُرفض
قياساً**: إن ساوت البصمةُ آخرَ التزامٍ مسّ `HANDOFF.json` فذلك ادّعاءٌ
دائريّ ويسقط.

**والانتقال يُقاس على التاريخ المسجَّل**، فيلزم منه أثران:
  · **انتقالٌ واحدٌ لكل التزام** — دمجُ انتقالَين في التزامٍ واحد يُخفي
    أحدهما، فيُرفض.
  · **والتاريخ يجب أن يكون كاملاً**: مستنسخٌ ضحل (`--depth`) يجعل
    القياس متعذّراً — **فيُقال ولا يُمرَّر صامتاً**.

**واللقطات الأقدم من البروتوكول `1.1` تُستثنى** — لا تسامحاً بل لأن
قاعدةً تُطبَّق بأثرٍ رجعيّ تُدين ماضياً لم تكن قائمةً حين جرى؛ **ويُعلَن
عددُ ما استُثني** فلا يُسكَت عنه.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUEUE_REL = ".ai-handoff/TASK_QUEUE.json"
HANDOFF_REL = ".ai-handoff/HANDOFF.json"
QUEUE = ROOT / QUEUE_REL
HANDOFF = ROOT / HANDOFF_REL

STATUSES = {
    "queued", "in_progress", "ready_for_codex", "changes_requested",
    "approved", "owner_decision_required", "blocked",
}
ACTORS = {"owner", "claude", "codex"}

# ── ① آلة الحالات — منصوصةٌ لا مضمرة (`DEC-291`) ─────────────────────────
# البقاء في الحالة نفسها مسموحٌ ضمناً (التزاماتُ تنفيذٍ متتابعة داخل
# `in_progress`)؛ وما عداه يجب أن يَرِد هنا صراحةً.
TRANSITIONS = {
    "queued": {"in_progress", "blocked", "owner_decision_required"},
    "in_progress": {"ready_for_codex", "blocked", "owner_decision_required"},
    "ready_for_codex": {"approved", "changes_requested", "blocked",
                        "owner_decision_required"},
    "changes_requested": {"in_progress", "blocked", "owner_decision_required"},
    "approved": set(),                       # نهائية — لا انتقال بعدها
    "blocked": {"queued", "in_progress", "owner_decision_required"},
    "owner_decision_required": {"queued", "in_progress", "blocked"},
}
# مهمّةٌ جديدة تُستأنف من هنا وحدهما — فلا تُفتح مهمّةٌ عند `approved`
START_STATUSES = {"queued", "in_progress"}
# الزيادةُ الوحيدة المأذون بها في البروتوكول: ردُّ المراجع بطلب تصحيح
ITERATION_BUMP = ("ready_for_codex", "changes_requested")
# الحالات التي يُوجَب عندها وجود بصمةِ التزامٍ صادقة — أي حين يُراجَع عمل
COMMIT_REQUIRED = {"ready_for_codex", "approved", "changes_requested"}
MIN_TRANSITION_VERSION = (1, 1)

SHA_RE = re.compile(r"^[0-9a-f]{7,40}$")
SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"sk-ant-[A-Za-z0-9_-]{20,}"),
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
]
LIST_FIELDS = ("changed_files", "commands_run", "tests", "findings",
               "blockers", "decisions_needed")


def _version(obj):
    raw = (obj or {}).get("protocol_version") or "0"
    try:
        return tuple(int(x) for x in str(raw).split("."))
    except ValueError:
        return (0,)


def _task_of(queue, task_id):
    for t in (queue or {}).get("tasks") or []:
        if isinstance(t, dict) and t.get("id") == task_id:
            return t
    return None


# ── فحص الشكل والاتساق ───────────────────────────────────────────────────
def shape_errors(queue, handoff):
    errors = []
    tasks = queue.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        errors.append("TASK_QUEUE.tasks must be a non-empty list")
        tasks = []

    ids = []
    for index, task in enumerate(tasks):
        if not isinstance(task, dict):
            errors.append(f"task {index} must be an object")
            continue
        task_id = task.get("id")
        if not isinstance(task_id, str) or not task_id:
            errors.append(f"task {index} has no valid id")
        else:
            ids.append(task_id)
        label = task_id or index
        if task.get("status") not in STATUSES:
            errors.append(f"task {label} has invalid status")
        if task.get("next_actor") not in ACTORS:
            errors.append(f"task {label} has invalid next_actor")
        iteration, maximum = task.get("iteration"), task.get("max_iterations")
        if not isinstance(iteration, int) or iteration < 0:
            errors.append(f"task {label} has invalid iteration")
        if not isinstance(maximum, int) or maximum < 1:
            errors.append(f"task {label} has invalid max_iterations")
        if isinstance(iteration, int) and isinstance(maximum, int):
            if iteration > maximum:
                errors.append(f"task {label} exceeds max_iterations")
            # بلوغُ الحدّ **يوقف** ولا يُمضي — وإلّا كان الحدّ زينة
            elif iteration == maximum and task.get("status") not in (
                    "owner_decision_required", "approved", "blocked"):
                errors.append(
                    f"task {label} reached max_iterations and must be "
                    "owner_decision_required")

    if len(ids) != len(set(ids)):
        errors.append("task ids must be unique")

    task_id = handoff.get("task_id")
    if task_id not in ids:
        errors.append("HANDOFF.task_id must match a queued task")
    if handoff.get("status") not in STATUSES:
        errors.append("HANDOFF.status is invalid")
    if handoff.get("from_actor") not in ACTORS or \
            handoff.get("to_actor") not in ACTORS:
        errors.append("HANDOFF actors are invalid")
    for field in LIST_FIELDS:
        if not isinstance(handoff.get(field), list):
            errors.append(f"HANDOFF.{field} must be a list")

    # ── الاتساق بين الملفَّين — `AIB-01` ─────────────────────────────────
    task = _task_of(queue, task_id)
    if task is not None:
        if task.get("status") != handoff.get("status"):
            errors.append(
                f"TASK_QUEUE.status ({task.get('status')}) must equal "
                f"HANDOFF.status ({handoff.get('status')})")
        if task.get("next_actor") != handoff.get("to_actor"):
            errors.append(
                f"task next_actor ({task.get('next_actor')}) must equal "
                f"HANDOFF.to_actor ({handoff.get('to_actor')})")
        if isinstance(handoff.get("iteration"), int) and \
                handoff["iteration"] != task.get("iteration"):
            errors.append("HANDOFF.iteration must equal task iteration")
    active = queue.get("active_task_id")
    if active is not None and active != task_id:
        errors.append(
            f"active_task_id ({active}) must equal HANDOFF.task_id ({task_id})")
    return errors


# ── فحص الانتقال بين لقطتَين ─────────────────────────────────────────────
def transition_errors(prev_q, prev_h, cur_q, cur_h):
    """يُقاس بين التزامَين متتاليَين. **ولا يُطبَّق بأثرٍ رجعي** على لقطةٍ
    أقدم من البروتوكول الذي شرّع القاعدة."""
    if min(_version(prev_h), _version(prev_q)) < MIN_TRANSITION_VERSION:
        return None                                    # لقطةٌ قديمة — تُستثنى
    errors = []
    prev_status, cur_status = prev_h.get("status"), cur_h.get("status")
    prev_id, cur_id = prev_h.get("task_id"), cur_h.get("task_id")

    if prev_id != cur_id:
        # تبدّلُ المهمّة ليس انتقالاً في آلة الحالات — لكنّه لا يُستأنف
        # من منتصف الدورة: مهمّةٌ تبدأ عند `queued` أو `in_progress`.
        if cur_status not in START_STATUSES:
            errors.append(
                f"new task {cur_id} must start at {sorted(START_STATUSES)}, "
                f"got {cur_status}")
        return errors

    if prev_status != cur_status:
        allowed = TRANSITIONS.get(prev_status, set())
        if cur_status not in allowed:
            errors.append(
                f"illegal transition {prev_status} -> {cur_status} "
                f"(allowed: {sorted(allowed) or 'none'})")

    prev_it, cur_it = prev_h.get("iteration"), cur_h.get("iteration")
    if isinstance(prev_it, int) and isinstance(cur_it, int):
        if cur_it < prev_it:
            errors.append(f"iteration must not decrease ({prev_it} -> {cur_it})")
        elif (prev_status, cur_status) == ITERATION_BUMP:
            if cur_it != prev_it + 1:
                errors.append(
                    f"iteration must increment by exactly 1 on "
                    f"{'->'.join(ITERATION_BUMP)} ({prev_it} -> {cur_it})")
        elif cur_it != prev_it:
            errors.append(
                f"iteration may only change on "
                f"{'->'.join(ITERATION_BUMP)} ({prev_it} -> {cur_it})")
    return errors


# ── فحص صدق البصمة — `AIB-02` ────────────────────────────────────────────
def commit_errors(handoff, probe):
    """`last_commit` = **آخر التزامٍ تنفيذيّ يسبق التزام سجلّ التسليم**.

    فلا يُطلب من الملفّ أن يحوي بصمةَ نفسه — وهو ما لا يكون.
    """
    status, sha = handoff.get("status"), handoff.get("last_commit")
    if sha is None:
        if status in COMMIT_REQUIRED:
            return [f"last_commit is required when status is {status}"]
        return []
    if not isinstance(sha, str) or not SHA_RE.match(sha):
        return [f"last_commit is not a valid sha: {sha!r}"]
    if probe is None:
        return ["last_commit cannot be verified: git is unavailable"]
    if probe.is_shallow():
        return ["last_commit cannot be verified: shallow clone "
                "(checkout with fetch-depth: 0)"]
    if not probe.exists(sha):
        return [f"last_commit {sha} does not exist"]
    if not probe.is_ancestor(sha):
        return [f"last_commit {sha} is not reachable from the working branch "
                "(orphaned or on another branch)"]
    own = probe.last_handoff_commit()
    if own and (own.startswith(sha) or sha.startswith(own)):
        return [f"last_commit {sha} is the handoff record's own commit "
                "(circular claim): it must point at the implementation "
                "commit that precedes it"]
    return []


def validate(queue, handoff, history=(), probe=None):
    """`history` لقطاتٌ من الأقدم إلى الأحدث — آخرُها الحالة الجارية."""
    errors = list(shape_errors(queue, handoff))
    errors += commit_errors(handoff, probe)
    checked = skipped = 0
    for (pq, ph), (cq, ch) in zip(history, history[1:]):
        step = transition_errors(pq, ph, cq, ch)
        if step is None:
            skipped += 1
        else:
            checked += 1
            errors += step
    return errors, checked, skipped


# ── وصلُ الواقع: `git` والملفّات ─────────────────────────────────────────
class GitProbe:
    def __init__(self, root):
        self.root = str(root)

    def _run(self, *args):
        return subprocess.run(["git", *args], cwd=self.root,
                              capture_output=True, text=True)

    def available(self):
        return self._run("rev-parse", "--git-dir").returncode == 0

    def is_shallow(self):
        r = self._run("rev-parse", "--is-shallow-repository")
        return r.stdout.strip() == "true"

    def exists(self, sha):
        return self._run("cat-file", "-e", sha + "^{commit}").returncode == 0

    def is_ancestor(self, sha):
        return self._run("merge-base", "--is-ancestor", sha, "HEAD").returncode == 0

    def last_handoff_commit(self):
        r = self._run("log", "-1", "--format=%H", "--", HANDOFF_REL)
        return r.stdout.strip() or None

    def snapshots(self, limit=40):
        """لقطاتُ الملفَّين عند كل التزامٍ مسّ سجلَّ التسليم — الأقدم أولاً."""
        r = self._run("log", f"-{limit}", "--format=%H", "--", HANDOFF_REL)
        shas = [s for s in r.stdout.split() if s][::-1]
        out = []
        for sha in shas:
            try:
                h = json.loads(self._run("show", f"{sha}:{HANDOFF_REL}").stdout)
                q = json.loads(self._run("show", f"{sha}:{QUEUE_REL}").stdout)
            except json.JSONDecodeError:
                continue
            out.append((q, h))
        return out


def main():
    for path in (QUEUE, HANDOFF):
        if not path.exists():
            print(f"ERROR: missing {path.relative_to(ROOT)}")
            return 1
    try:
        queue = json.loads(QUEUE.read_text(encoding="utf-8"))
        handoff = json.loads(HANDOFF.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: invalid JSON: {exc}")
        return 1

    raw = QUEUE.read_text(encoding="utf-8") + HANDOFF.read_text(encoding="utf-8")
    secret = [("possible secret detected in handoff files")] \
        if any(p.search(raw) for p in SECRET_PATTERNS) else []

    probe = GitProbe(ROOT)
    if not probe.available():
        probe = None
        history = []
        note = "git unavailable — transitions unmeasured"
    elif probe.is_shallow():
        history = []
        note = "shallow clone — transitions unmeasured"
    else:
        history = probe.snapshots()
        # الحالةُ الجارية على القرص هي آخر اللقطات — فتُقاس ولو لم تُلتزم بعد
        if not history or history[-1][1] != handoff:
            history = history + [(queue, handoff)]
        note = None

    errors, checked, skipped = validate(queue, handoff, history, probe)
    errors += secret
    if note:
        errors.append(note)

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    tail = f"; {checked} transition(s) checked"
    if skipped:
        tail += f", {skipped} pre-1.1 snapshot pair(s) skipped"
    print(f"PASS: {len(queue['tasks'])} task(s); handoff protocol is valid{tail}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
