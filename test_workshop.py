# -*- coding: utf-8 -*-
"""
test_workshop.py — عقد مسار الورشة: بوابة القبول · صفر اعتماد · صفر تسرّب
==========================================================================
سند: `DEC-277` (مسار الورشة) · `DEC-279` (هذا العقد) · `DEC-252` · `DEC-271`

يقيس أربعة أشياء **يعلنها القرار**:
  1) **المشرف بوابةُ قبول**: تقريرٌ معطوب **لا يُخزَّن** — يُردّ بحكمه
  2) **صفر اعتمادٍ يُخزَّن**: أي حقلٍ يشبه كلمة مرور يُردّ ولا يُتجاهل
  3) **الإذن الصريح شرط**: بنصّه المعتمد حرفياً لا بمعناه
  4) **الموقع العام لم يُمسّ**: وعدُه وقفلُ صفر الشبكة فيه كما هما

**وبيانات المشاركين لا تدخل المستودع**: الفحص الخامس يرفض أي أثرٍ لها
في `git` — فهي بيانات أشخاص لا مخرَجات بناء.
"""
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import k2_report as R2
import k3_report as R3
import k4_report as R4
import workshop_store as WS

FAILS = []


def check(label, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + label + (" - " + detail if detail else ""))
    if not ok:
        FAILS.append(label)


def _payload(code):
    sp2 = {"A": 80.0, "R": 60.0, "C": 55.0, "O": 45.0,
           "S": 70.0, "E": 40.0, "St": 50.0, "H": 65.0}
    sp3 = list(json.load(io.open(os.path.join(HERE, "parity_cases.json"),
                                 encoding="utf-8"))["k3"].values())[0]
    sp4 = {"WM": 62, "TI": 38, "F": 74, "PF": 44, "OR": 55, "TM": 41, "PER": 40}
    t2, a2 = R2.build_report(sp2, mode="full")
    t3, a3 = R3.build_report(sp3)
    t4, a4 = R4.build_report(sp4)
    xt, xa = R4.build_crossing_surface(sp4)
    return {"schema": WS.SCHEMA, "code": code,
            "consent": {"text": WS.CONSENT_TEXT, "accepted": True},
            "reports": {"K2": {"markdown": t2, "audit": a2},
                        "K3": {"markdown": t3, "audit": a3},
                        "K4": {"markdown": t4, "audit": a4,
                               "crossing": {"markdown": xt, "audit": xa}}}}


def run_in_sandbox(fn):
    """كل فحصٍ في مخزنٍ مؤقّت — فلا يلمس حصيلة ورشةٍ حقيقية."""
    tmp = tempfile.mkdtemp(prefix="ws_test_")
    old_dir, old_codes = WS.STORE_DIR, WS.CODES_FILE
    WS.STORE_DIR = tmp
    WS.CODES_FILE = os.path.join(tmp, "_codes.json")
    try:
        return fn()
    finally:
        WS.STORE_DIR, WS.CODES_FILE = old_dir, old_codes
        shutil.rmtree(tmp, ignore_errors=True)


def _reject(label, mutate):
    def body():
        code = WS.issue("فحص", seed=label)
        p = _payload(code)
        mutate(p)
        try:
            WS.accept(p)
            return False, "مرّ بلا ردّ"
        except WS.WorkshopError as e:
            stored = [f for f in os.listdir(WS.STORE_DIR)
                      if not f.startswith("_")]
            if stored:
                return False, "رُدّ لكنه خُزِّن: " + str(stored)
            return True, str(e)[:60]
    ok, detail = run_in_sandbox(body)
    check(label, ok, detail)


def test_happy_path():
    def body():
        code = WS.issue("فحص-سليم", seed="ok")
        r = WS.accept(_payload(code))
        clean = all(v["clean"] for v in r["verdicts"].values())
        stored = os.path.exists(os.path.join(WS.STORE_DIR, code + ".json"))
        used = json.load(io.open(WS.CODES_FILE, encoding="utf-8"))[code]["used"]
        return (clean and stored and used,
                "الدوائر الثلاث نظيفة والرمز صار مستعملاً")
    ok, detail = run_in_sandbox(body)
    check("1 حمولة سليمة تُقبل وتُخزَّن", ok, detail)


def test_supervisor_is_the_gate():
    _reject("1 تقرير معطوب لا يُخزَّن (المشرف بوابة)",
            lambda p: p["reports"]["K2"].__setitem__(
                "markdown", p["reports"]["K2"]["markdown"] + " ."))
    _reject("1 بصمة مزوّرة لا تُخزَّن",
            lambda p: p["reports"]["K4"]["audit"].__setitem__(
                "report_sha256", "0000000000000000"))


def test_no_credentials():
    for field in ("password", "token", "hash"):
        _reject("2 حقل اعتماد يُردّ: " + field,
                lambda p, f=field: p.__setitem__(f, "x"))


def test_consent():
    _reject("3 بلا إذن يُردّ", lambda p: p.pop("consent"))
    _reject("3 إذن غير مقبول يُردّ",
            lambda p: p["consent"].__setitem__("accepted", False))
    _reject("3 نصّ إذنٍ مخالف يُردّ",
            lambda p: p["consent"].__setitem__("text", "موافقة عامة"))


def test_structure():
    _reject("3 رمز غير مُصدَر يُردّ", lambda p: p.__setitem__("code", "AAAA-BBBB"))
    _reject("3 مخطَّط مجهول يُردّ", lambda p: p.__setitem__("schema", "X-v9"))
    _reject("3 دائرة غير معروفة تُردّ",
            lambda p: p["reports"].__setitem__("K9", {"markdown": "x", "audit": {}}))


# -- 4) الموقع العام لم يُمسّ ---------------------------------------------
def test_public_site_untouched():
    kashaf = os.path.join(HERE, "docs", "kashaf.html")
    if not os.path.exists(kashaf):
        check("4 الموقع العام موجود", False, "docs/kashaf.html غائب")
        return
    html = io.open(kashaf, encoding="utf-8").read()
    check("4 قفل صفر الشبكة قائم في التطبيق العام",
          "fetch" in html and ("لا شبكة" in html or "صفر شبكة" in html
                               or "NetworkBlocked" in html or "throw" in html),
          "")
    clean = WS.SCHEMA not in html and "workshop" not in html.lower()
    # التفصيل يصف الحال لا يُطبع دائماً: فحصٌ ناجح يطبع رسالة سقوطه
    # يُضلِّل قارئ البوابة — وهو الصنف نفسه الذي قُيِّد في DEC-278.
    check("4 لا نقطة استقبال ورشة في التطبيق العام", clean,
          "" if clean else "ظهرت آثار مسار الورشة في الموقع العام")
    base = os.path.join(HERE, "site", "templates", "base.html")
    if os.path.exists(base):
        check("4 وعد التذييل كما هو",
              "لا تغادر" in io.open(base, encoding="utf-8").read(), "")


# -- 5) بيانات المشاركين خارج المستودع -----------------------------------
def test_data_never_tracked():
    r = subprocess.run(["git", "ls-files"], capture_output=True, text=True,
                       cwd=HERE)
    if r.returncode != 0:
        print("SKIP 5 فحص التتبّع - لا مستودع git")
        return
    tracked = [f for f in r.stdout.split("\n") if f.startswith("workshop_data")]
    check("5 صفر ملف حصيلة متبَع", not tracked, str(tracked[:4]) if tracked else
          "workshop_data/ مُسقَطة")
    gi = io.open(os.path.join(HERE, ".gitignore"), encoding="utf-8").read()
    check("5 الإسقاط مُعلَن في .gitignore", "workshop_data/" in gi, "")


if __name__ == "__main__":
    print("=" * 76)
    test_happy_path()
    test_supervisor_is_the_gate()
    test_no_credentials()
    test_consent()
    test_structure()
    test_public_site_untouched()
    test_data_never_tracked()
    print("-" * 76)
    if FAILS:
        print("النتيجة النهائية: انحدار - " + str(len(FAILS)) + ": " +
              " · ".join(FAILS))
        raise SystemExit(1)
    print("النتيجة النهائية: لا انحدار")
