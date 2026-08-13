# -*- coding: utf-8 -*-
"""
test_supervisor_build.py — حرس بناء أداة المشرف وتشغيلها (البوابة 20 ← 22)
===========================================================================
سند: أمر المالك «نفّذ بالترتيب الموصى به» — 2026-08-13 · `DEC-271`
     درس `DEC-269`/`00-HANDOVER §6⑦` (ما لا تشمله البوابة ينكسر صامتاً)

**لماذا وُجد هذا الحرس:** بعد بناء $K_4$ صار `build_supervisor_html.py`
**مكسوراً بالفعل** — أربعة استيرادات مستجدّة في `reports.js` بلا تشييم —
فتعذّر توليد `Supervisor.html` أصلاً. ولم تكشفه البوابة العشرينية لأنها
تشغّل `supervisor.py --self-test` (بايثون) ولا تبني الأداة. وهو **الانكسار
الصامت نفسه** الذي وقع في `build_site.py`، في الباني الآخر.

**وفحصه الثالث درسٌ ثانٍ:** أول تشييم كتبتُه لحزمة $K_4$ كان
`JSON.parse(PK.PACKS.CONTENT_K4)` — و`PACKS[k]` **كائنٌ مُفكَّك سلفاً**.
بُنيت الأداة بلا شكوى وكانت ستسقط في يد المستخدم. فالحرس **يشغّل** الحزمة
المولَّدة ولا يقرأها فقط.

فحوصه — وكلٌّ **يقيس ما يعلنه**:
  ① البناء يكتمل · صفر `require(` باقٍ في الحزمة المولَّدة
  ② صفر تصدير عقدة غير محروس
  ③ **الحزمة المولَّدة تعمل**: $K_2$ و$K_4$ يُحكَمان فعلاً، والإفساد يُرصد
  ④ تغطية $K_4$ حاضرة في الأداة: محرّكها وحزمتها وسطحها وفحصها الذاتي
"""
import io
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

FAILS = []


def check(label, ok, detail=""):
    print(f"{'✅' if ok else '❌'} {label}" + (f" — {detail}" if detail else ""))
    if not ok:
        FAILS.append(label)


import build_supervisor_html as BSH


# ── ① البناء يكتمل والتشييم مكتمل ────────────────────────────────────────
def test_build():
    try:
        mods = BSH.modules()
    except AssertionError as e:
        check("بناء أداة المشرف يكتمل", False, f"{e}")
        return ""
    check("بناء أداة المشرف يكتمل", True, f"{len(mods)} بايت مجمَّعة")
    check("صفر استيراد باقٍ", "require(" not in mods)

    # التصدير **غير المحروس** هو التسرّب — `typeof module` نمطٌ صحيح للبيئتين
    lines = mods.split("\n")
    unguarded = [i + 1 for i, ln in enumerate(lines)
                 if "module.exports" in ln
                 and "typeof module" not in (ln + " " + (lines[i - 1] if i else ""))]
    check("صفر تصدير عقدة غير محروس", not unguarded,
          f"غير محروس في: {unguarded[:6]}" if unguarded else "")
    return mods


# ── ④ تغطية K4 معلَنة في الأداة المولَّدة ────────────────────────────────
def test_k4_surfaced(html):
    for label, needle in (
            ("محرك K4 في الحزمة", "{ K2, K3, K4, InputContractError }"),
            ("حزمة K4 مشيَّمة بلا تفكيك ثانٍ", "PK.PACKS.CONTENT_K4) || null"),
            ("رسالة الرفض باقية نافذة", "حزمة K4 غير محمَّلة"),
            ("الفحص الذاتي يشمل K4", "K4 سليمة بسطحها العابر"),
            ("الفحص الذاتي يُفسد دَين الميدان", "حُذف دَين الميدان")):
        check(f"معلَن: {label}", needle in html)


# ── ③ الحزمة المولَّدة **تعمل** — تشغيل فعلي لا قراءة ────────────────────
def test_runtime(html):
    blocks = re.findall(r"<script>(.*?)</script>", html, re.S)
    mods = [b for b in blocks if "/* ==== engines.js ==== */" in b]
    if not mods:
        check("كتلة الوحدات موجودة في المخرج", False, "لم تُعثر")
        return
    check("كتلة الوحدات موجودة في المخرج", True, f"{len(mods[0])} بايت")

    tmp = os.path.join(HERE, "_sup_html_mods.js")
    io.open(tmp, "w", encoding="utf-8").write(mods[0])
    try:
        r = subprocess.run(["node", os.path.join(HERE, "_sup_html_probe.js"), tmp],
                           capture_output=True, text=True, cwd=HERE)
    finally:
        os.remove(tmp)
    if r.returncode != 0:
        check("الحزمة المولَّدة تُنفَّذ", False,
              (r.stderr or r.stdout)[:200].replace("\n", " "))
        return
    check("الحزمة المولَّدة تُنفَّذ", True)
    probe = json.loads(r.stdout)

    absent = [k for k, v in probe["present"].items() if not v]
    check("الوحدات التسع حاضرة في النطاق", not absent,
          f"غائب: {absent}" if absent else "engines · packs · gate · reports · supervisor")

    g = probe.get("graded", {})
    for tag, label in (("k2", "K2 سليمة تُحكَم سليمة"),
                       ("k4", "K4 سليمة تُحكَم سليمة")):
        r_ = g.get(tag, {})
        check(label, r_.get("errors") == 0 and "exception" not in r_,
              r_.get("exception") or r_.get("err0") or f"{r_.get('grades')} درجة")

    # وبرهان الحساسية: الإفساد **يُرصد** — وإلا فالأداة تُصادق على المعطوب
    for tag, label in (("k4_debt_stripped", "حذف دَين الميدان يُرصد"),
                       ("k4_surface_merged", "دمج السطح العابر في المتن يُرصد")):
        r_ = g.get(tag, {})
        check(label, r_.get("errors", 0) > 0 and "exception" not in r_,
              r_.get("exception") or "مرّ بلا رصد" if not r_.get("errors") else "")

    k4 = probe.get("k4", {})
    check("كتلة تدقيق K4 كاملة في المتصفح",
          bool(k4.get("sha")) and bool(k4.get("packSha")),
          f"report_sha256={k4.get('sha')} · pack_sha={k4.get('packSha')}")
    check("السطح العابر يُبنى في الحزمة المولَّدة", (k4.get("surface") or 0) > 200,
          f"{k4.get('surface')} حرفاً · {k4.get('entries')} قيداً")


if __name__ == "__main__":
    print("=" * 76)
    mods = test_build()
    if mods:
        rc = BSH.main()
        html = io.open(os.path.join(HERE, "Supervisor.html"), encoding="utf-8").read()
        check("الملف يُكتب", bool(html), f"{len(html)} بايت")
        test_k4_surfaced(html)
        test_runtime(html)
    print("-" * 76)
    if FAILS:
        print(f"النتيجة النهائية: ❌ انحدار — {len(FAILS)}: " + " · ".join(FAILS))
        raise SystemExit(1)
    print("النتيجة النهائية: ✅ لا انحدار")
