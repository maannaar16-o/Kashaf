# -*- coding: utf-8 -*-
"""
gate.py — مُشغِّل بوابة القبول: **سلطةٌ واحدة** على ما يُقاس وبأي بصمة
=======================================================================
سند: أمر المالك «ادمج الـPR ثم نفّذ `DEC-273`» — 2026-08-13 · `DEC-273`
     `م-2` (مصدر حقيقة واحد) · `00-HANDOVER §6①` (الحقل يفحص أو لا يُضاف)
     `00-HANDOVER §6⑦` (ما لا تشمله البوابة ينكسر صامتاً)

**المشكلة التي يحلّها:** كانت قائمة الأدوات والبصمات مكتوبةً في **ثلاثة
مواضع** — `CLAUDE.md` و`00-HANDOVER §3.4` وذاكرةُ المنفّذ — ولا رابط بينها.
وثلاثة نسخٍ بلا رابطٍ تنجرف؛ وقد انجرفت فعلاً: البوابة سقطت عند علاماتها
السبع (`CHG-088`)، وبانيان خرجا منها فانكسرا صامتاً (`DEC-269`/`DEC-271`).

فصارت القائمة **هنا**، ومعها بصماتها. والأدوات تُشغَّل من هذا الموضع،
**والوثائق تُقابَل به** — فانجراف الوثيقة يوقف البوابة كما يوقفها انجراف
الكود.

الاستعمال:
    python3 gate.py            # التهيئة ثم الأدوات الاثنتان والعشرون
    python3 gate.py --list     # القائمة والبصمات بلا تشغيل

رمز الخروج: `0` قبول · `1` انحدار.
"""
import glob
import io
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# ── التهيئة الإلزامية — `CLAUDE.md §Setup` ───────────────────────────────
SETUP = [
    (["python3", "build_packs.py"], "توليد packs.js — لا يُرفع (CHG-054)"),
]
RENAME = ("k3_contentpack_FIXED_DEC-195.py", "k3_contentpack.py")

# ── الأدوات الاثنتان والعشرون · والبصمات الخمس ───────────────────────────
# البصمة `None` تعني: أداةٌ تحكم بنفسها ولا تُصدر بصمةً مرجعية.
TOOLS = [
    ("parity_py.py",              "2711c24d8155819b"),
    ("parity_reports.py",         "36ae94bfd5a8b60f"),
    ("parity_supervisor.py",      "6b324f996856eac3"),
    ("parity_k4.py",              "e32207bbb8853560"),
    ("parity_supervisor_k4.py",   "a0f83d78b8adbf53"),
    ("parity_messages.py",        None),
    ("parity_isolation.py",       None),
    ("parity_surface.py",         None),
    ("verify_regen.py",           None),
    ("test_packs.py",             None),
    ("test_golden_k2.py",         None),
    ("test_golden_k3.py",         None),
    ("test_report_k2.py",         None),
    ("test_report_k3.py",         None),
    ("test_guard_sp.py",          None),
    ("test_guard_lock.py",        None),
    ("guard_interp.py",           None),
    ("test_report_k4.py",         None),
    ("k4_content.py",             None),
    ("test_site_build.py",        None),
    ("test_supervisor_build.py",  None),
    ("supervisor.py --self-test", None),
]
EXPECTED_COUNT = 22

# الوثائق التي تصف البوابة — **تُقابَل بها ولا تُصدَّق**
DOCS = ["CLAUDE.md", "00-HANDOVER_2026-08-05_Resume_Directive.md"]

FAILS = []


def fail(label, detail=""):
    FAILS.append(label + (f" — {detail}" if detail else ""))


def mark(ok, label, detail=""):
    print(f"{'✅' if ok else '❌'} {label}" + (f" — {detail}" if detail else ""))
    if not ok:
        fail(label, detail)


# ── ① الأدوات ────────────────────────────────────────────────────────────
def run_tools():
    print("═" * 78)
    print(f"البوابة — {len(TOOLS)} أداة · {sum(1 for _, f in TOOLS if f)} بصمة مرجعية")
    print("═" * 78)
    for spec, expected in TOOLS:
        parts = spec.split()
        r = subprocess.run(["python3"] + parts, capture_output=True, text=True,
                           cwd=HERE)
        out = r.stdout + r.stderr
        line = f"{spec:<28}"
        if r.returncode != 0:
            tail = [l for l in out.strip().split("\n") if l.strip()]
            print(f"❌ {line} rc={r.returncode}")
            fail(spec, (tail[-1] if tail else "بلا مخرج")[:120])
            continue
        if expected is None:
            print(f"✅ {line} ✔")
            continue
        # **مطابقة حرفية** — لا «قريبة» ولا «مُطبَّعة» (`ن-8`)
        if expected in out:
            print(f"✅ {line} {expected}")
        else:
            found = sorted(set(re.findall(r"\b[0-9a-f]{16}\b", out)))
            print(f"❌ {line} البصمة تزحزحت")
            fail(spec + " · البصمة",
                 f"المتوقَّع {expected} · الموجود {found or 'لا شيء'}")


# ── ② لا أداة خارج البوابة — الصنف الذي انكسر ثلاث مرات ──────────────────
def check_coverage():
    print("-" * 78)
    listed = {spec.split()[0] for spec, _ in TOOLS}
    discovered = set()
    for pat in ("parity_*.py", "test_*.py", "guard_*.py", "verify_*.py"):
        discovered |= {os.path.basename(p) for p in glob.glob(os.path.join(HERE, pat))}
    outside = sorted(discovered - listed)
    mark(not outside, "صفر أداة خارج البوابة",
         f"مكتشَفة وغير مدرَجة: {outside}" if outside
         else f"{len(discovered)} أداة مكتشَفة · كلّها مدرَجة")
    missing = sorted(f for f in listed if not os.path.exists(os.path.join(HERE, f)))
    mark(not missing, "كل مدرَجٍ موجود", f"غائب: {missing}" if missing else "")
    mark(len(TOOLS) == EXPECTED_COUNT, "عدد الأدوات كما هو معلَن",
         f"{len(TOOLS)} بدل {EXPECTED_COUNT}")


# ── ③ الوثائق لا تنجرف عن البوابة — عيبُ هذه الجلسة كلّها، مقيساً ────────
def check_docs():
    listed = {spec.split()[0] for spec, _ in TOOLS}
    prints = {f for _, f in TOOLS if f}
    for doc in DOCS:
        path = os.path.join(HERE, doc)
        if not os.path.exists(path):
            mark(False, f"{doc} موجودة", "الملف غائب")
            continue
        text = io.open(path, encoding="utf-8").read()
        named = set(re.findall(r"python3\s+(\S+\.py)", text)) - {
            "build_packs.py", "build_site.py", "build_supervisor_html.py",
            "gate.py"}
        mark(named == listed, f"{doc}: قائمة الأدوات مطابقة",
             f"في الوثيقة لا البوابة {sorted(named - listed)} · "
             f"في البوابة لا الوثيقة {sorted(listed - named)}"
             if named != listed else f"{len(named)} أداة")
        hexes = set(re.findall(r"\b[0-9a-f]{16}\b", text))
        stale = sorted(h for h in hexes if h not in prints
                       and re.search(r"بصمة|fingerprint|parity", text[
                           max(0, text.find(h) - 120):text.find(h) + 40], re.I))
        mark(not stale, f"{doc}: صفر بصمة متقادمة",
             f"بصمات لا تعرفها البوابة: {stale}" if stale
             else f"{len(prints & hexes)}/{len(prints)} بصمة مذكورة")


# ── ④ لا مولَّد في قاعدة المعرفة — `CHG-054` ─────────────────────────────
GENERATED = ["packs.js", "k3_contentpack.py", "Supervisor.html"]


def check_generated():
    """`CHG-054` نصٌّ لا يُصان بالانتباه: `git` يعرف المتبَع فعلاً."""
    r = subprocess.run(["git", "ls-files"], capture_output=True, text=True,
                       cwd=HERE)
    if r.returncode != 0:
        print("⚪ فحص المولَّدات — لا مستودع git · الفحص متعذّر لا مُجتاز")
        return
    tracked = set(r.stdout.split("\n"))
    leaked = sorted(g for g in GENERATED if g in tracked)
    mark(not leaked, "صفر ملف مولَّد متبَع (CHG-054)",
         f"متبَعة خطأً: {leaked}" if leaked
         else " · ".join(GENERATED) + " — كلّها مُسقَطة")


def setup():
    print("── التهيئة " + "─" * 66)
    for cmd, why in SETUP:
        r = subprocess.run(cmd, capture_output=True, text=True, cwd=HERE)
        mark(r.returncode == 0, " ".join(cmd), why if r.returncode == 0
             else (r.stderr or r.stdout)[-160:])
    src, dst = (os.path.join(HERE, RENAME[0]), os.path.join(HERE, RENAME[1]))
    if not os.path.exists(src):
        mark(False, "إعادة التسمية القانونية", f"{RENAME[0]} غائب")
        return
    io.open(dst, "w", encoding="utf-8").write(io.open(src, encoding="utf-8").read())
    mark(True, "إعادة التسمية القانونية", f"{RENAME[0]} → {RENAME[1]}")


def main(argv):
    if "--list" in argv:
        for spec, f in TOOLS:
            print(f"{spec:<28} {f or '—'}")
        return 0
    setup()
    if FAILS:
        print("\n❌ التهيئة أخفقت — لا تشغيل على أساس ناقص")
        return 1
    run_tools()
    check_coverage()
    check_docs()
    check_generated()
    print("═" * 78)
    if FAILS:
        print(f"النتيجة: ❌ انحدار — {len(FAILS)}")
        for f in FAILS:
            print("   · " + f)
        return 1
    print(f"النتيجة: ✅ قبول — {len(TOOLS)}/{EXPECTED_COUNT} أداة · "
          f"{sum(1 for _, f in TOOLS if f)} بصمة حرفياً · "
          f"صفر أداة خارج البوابة · صفر انجراف وثائقي")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
