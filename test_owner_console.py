# -*- coding: utf-8 -*-
"""
test_owner_console.py — عقد لوحة المالك: رفعٌ مشروط · صفر تسرّب · حدٌّ مُعلَن
==============================================================================
سند: `DEC-280` (اللوحة) · `DEC-277 §2` (رفع `ح-4` بشرطه) · `DEC-278` (الفريق)

يقيس أربعة أشياء **يعلنها القرار**:
  1) **الرفع مشروطٌ لا مطلق**: سجلٌّ بإذنٍ غير مطابقٍ **لا يُعرَض خامُه**
     — ويُعلَن حجبُه ولا يُسقَط صامتاً
  2) **جدار العزل قائمٌ في اللوحة**: خريطة الفريق بعدسات $K_2$ وحدها
  3) **الحدود مُعلَنةٌ في اللوحة نفسها** لا في وثيقةٍ بعيدة
  4) **لا سطح متصفح**: الأداة مشغِّلٌ بايثونية — وحرس التأجيل نافذ

**ولا بصمةَ لها**: مخرجُها يتبع حصيلةً متغيّرة، فبصمةٌ عليه ادّعاءُ ثباتٍ
كاذب. والانحدارُ المقيس هنا **سلوكُ الحدود** لا شكلُ الطباعة.
"""
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import k2_report as R2
import k3_report as R3
import k4_report as R4
import owner_console as OC
import team_engine as TE
import workshop_store as WS

FAILS = []


def check(label, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + label + (" - " + detail if detail else ""))
    if not ok:
        FAILS.append(label)


# ── حصيلةٌ اصطناعية في مخزنٍ مؤقّت ────────────────────────────────────────
SP2_BASE = {"A": 80.0, "R": 60.0, "C": 55.0, "O": 45.0,
            "S": 70.0, "E": 40.0, "St": 50.0, "H": 65.0}
SP4_BASE = {"WM": 62, "TI": 38, "F": 74, "PF": 44, "OR": 55, "TM": 41, "PER": 40}


def _sp3():
    return list(json.load(io.open(os.path.join(HERE, "parity_cases.json"),
                                  encoding="utf-8"))["k3"].values())[0]


def _payload(code, shift=0.0):
    sp2 = {k: max(5.0, min(95.0, v + shift)) for k, v in SP2_BASE.items()}
    t2, a2 = R2.build_report(sp2, mode="full")
    t3, a3 = R3.build_report(_sp3())
    t4, a4 = R4.build_report(SP4_BASE)
    xt, xa = R4.build_crossing_surface(SP4_BASE)
    return {"schema": WS.SCHEMA, "code": code,
            "consent": {"text": WS.CONSENT_TEXT, "accepted": True},
            "reports": {"K2": {"markdown": t2, "audit": a2},
                        "K3": {"markdown": t3, "audit": a3},
                        "K4": {"markdown": t4, "audit": a4,
                               "crossing": {"markdown": xt, "audit": xa}}}}


def seed(n=3, tamper_consent_on=None):
    """يزرع `n` سجلاً مقبولاً — ويكسر إذن واحدٍ منها **بعد** التخزين.

    الكسر بعد التخزين لا قبله: بوابة `accept` ترفض الإذن المخالف أصلاً،
    والمقيس هنا سلوك **اللوحة** أمام سجلٍّ قائمٍ إذنُه غير مطابق.
    """
    codes = []
    for i in range(n):
        code = WS.issue(f"عضو-{i}", seed=f"s{i}")
        WS.accept(_payload(code, shift=i * 9.0))
        codes.append(code)
    if tamper_consent_on is not None:
        path = os.path.join(WS.STORE_DIR, codes[tamper_consent_on] + ".json")
        rec = json.load(io.open(path, encoding="utf-8"))
        rec["consent"]["text"] = "موافقة عامة"
        io.open(path, "w", encoding="utf-8").write(
            json.dumps(rec, ensure_ascii=False, sort_keys=True, indent=1))
    return codes


def run_in_sandbox(fn):
    tmp = tempfile.mkdtemp(prefix="oc_test_")
    old_dir, old_codes = WS.STORE_DIR, WS.CODES_FILE
    WS.STORE_DIR = tmp
    WS.CODES_FILE = os.path.join(tmp, "_codes.json")
    try:
        return fn()
    finally:
        WS.STORE_DIR, WS.CODES_FILE = old_dir, old_codes
        shutil.rmtree(tmp, ignore_errors=True)


def capture(fn, *a):
    """يلتقط المطبوع — فالمقيس ما **يراه المالك** لا ما تُرجعه الدالّة."""
    old = sys.stdout
    sys.stdout = buf = io.StringIO()
    try:
        rc = fn(*a)
    finally:
        sys.stdout = old
    return rc, buf.getvalue()


# -- 1) الرفع مشروطٌ لا مطلق ----------------------------------------------
def test_conditional_lift():
    def body():
        codes = seed(3, tamper_consent_on=2)
        good, held = codes[0], codes[2]

        rc, out = capture(OC.cmd_show, [good])
        nums = re.findall(r"\d+\.\d", out)
        check("1 الخام يُعرَض لمن أذِن بنصّه", rc == 0 and len(nums) >= 8,
              str(len(nums)) + " قيمة خام")

        rc, out = capture(OC.main, ["show", held])
        blocked = rc == 1 and "لا يُعرَض خامُه" in out
        check("1 الخام محجوبٌ عمّن إذنُه غير مطابق", blocked, out.strip()[:70])
        leaked = re.findall(r"\d+\.\d", out)
        check("1 ولا رقم خام يتسرّب في رسالة الحجب", not leaked,
              str(leaked[:4]) if leaked else "")

        rc, out = capture(OC.cmd_list, [])
        check("1 الحجب مُعلَنٌ في القائمة لا صامت",
              "محجوب" in out and held in out, "")
        return True, ""
    run_in_sandbox(body)


# -- 2) جدار العزل في اللوحة ----------------------------------------------
K3_K4 = ["EP", "IR", "BI", "CF", "WM", "TI", "PF", "OR", "TM", "PER"]


def test_isolation():
    def body():
        seed(3)
        # المسار الذي يراه المالك: `main` لا الدالّة - فخرقُ العقد يظهر
        # حكماً مقروءاً لا انهياراً، والفحص يقيسه بدل أن يسقط معه.
        rc, out = capture(OC.main, ["team"])
        hits = [c for c in K3_K4
                if re.search(r"(?<![A-Za-z])" + c + r"(?![A-Za-z])", out)]
        check("2 صفر رمز من K3/K4 في خريطة الفريق", rc == 0 and not hits,
              str(hits) if hits else "بعدسات K2 الثماني وحدها")

        # المدخل نفسه: لا حقل من خارج عدسات K2 يصل المحرّك
        ok, _held = OC.records()
        members = OC.team_members(ok)
        extra = sorted({k for m in members for k in m["sp"]} - set(TE.LENSES))
        check("2 مدخل المحرّك بعدسات K2 حصراً", not extra,
              str(extra) if extra else str(len(TE.LENSES)) + " عدسة")

        # وفي التوزيع: كل دائرةٍ في جدولها ولا رقم يجمع دائرتين
        rc, out = capture(OC.main, ["dist"])
        check("2 التوزيع ثلاثة جداول لا جدولٌ جامع",
              rc == 0 and out.count("· دائرة") == 3 and "جدار العزل" in out,
              str(out.count("· دائرة")) + " جدولاً")
        return True, ""
    run_in_sandbox(body)


# -- 3) الحدود مُعلَنةٌ في اللوحة ------------------------------------------
def test_declared_voids():
    rc, out = capture(OC.cmd_voids, [])
    for frag in ("DEC-244", "DEBT-K3-NORM-01", "DEC-277 §6", OC.BANNER):
        check("3 حدٌّ مُعلَن: " + frag[:38], rc == 0 and frag in out, "")
    # التنبيه الإلزامي **من الحزمة** لا نسخةً مكتوبة في الكود
    src = io.open(os.path.join(HERE, "owner_console.py"), encoding="utf-8").read()
    check("3 التنبيه من حزمة الفريق لا نسخةً في الكود",
          OC.BANNER not in src and 'PACK["banner"]' in src, "")
    # ويظهر في السطح الفردي أيضاً — لا في شاشة الحدود وحدها
    def body():
        codes = seed(2)
        _rc, out2 = capture(OC.cmd_show, [codes[0]])
        return OC.BANNER in out2, ""
    ok, _ = run_in_sandbox(body)
    check("3 التنبيه في ذيل السطح الفردي", ok, "")


# -- 4) عقد التشغيل: يوقف ولا يخمّن ----------------------------------------
def test_contract():
    def body():
        rc, out = capture(OC.main, ["show", "AAAA-BBBB"])
        check("4 رمزٌ غير موجود يُردّ", rc == 1 and "لا سجلّ" in out, "")
        rc, out = capture(OC.main, ["team"])
        check("4 خريطة فريقٍ بلا عضوين تُردّ",
              rc == 1 and "عضوان حدّاً أدنى" in out, out.strip()[:60])
        rc, out = capture(OC.main, ["لاشيء"])
        check("4 أمرٌ غير معروف يُردّ", rc == 2, "")
        rc, out = capture(OC.cmd_list, [])
        check("4 مخزنٌ فارغ يُقال لا يُخمَّن", rc == 0 and "فارغ" in out, "")
        return True, ""
    run_in_sandbox(body)


# -- 5) أداةُ مشغّلٍ لا سطح متصفح ------------------------------------------
def test_no_browser_surface():
    surfaces = ["engines.js", "reports.js", "dualreport.js",
                os.path.join("site", "app", "app.js"),
                os.path.join("site", "workshop", "workshop_app.js")]
    leaked = []
    for f in surfaces:
        p = os.path.join(HERE, f)
        if os.path.exists(p) and re.search(
                r"owner_console|OwnerConsole|RawahilOwner",
                io.open(p, encoding="utf-8").read()):
            leaked.append(f)
    check("5 اللوحة خارج كل حزمة متصفح", not leaked,
          "ظهرت في " + str(leaked) if leaked
          else "بايثون وحدها (سابقة DEC-254)")
    r = subprocess.run(["git", "ls-files"], capture_output=True, text=True, cwd=HERE)
    if r.returncode == 0:
        tracked = [f for f in r.stdout.split("\n") if f.startswith("workshop_data")]
        check("5 صفر ملف حصيلة متبَع", not tracked, str(tracked[:3]) if tracked else "")


if __name__ == "__main__":
    print("=" * 76)
    test_conditional_lift()
    test_isolation()
    test_declared_voids()
    test_contract()
    test_no_browser_surface()
    print("-" * 76)
    if FAILS:
        print("النتيجة النهائية: انحدار - " + str(len(FAILS)) + ": " +
              " · ".join(FAILS))
        raise SystemExit(1)
    print("النتيجة النهائية: لا انحدار")
