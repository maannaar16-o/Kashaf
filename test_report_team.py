# -*- coding: utf-8 -*-
"""
test_report_team.py — عقد تقرير الفريق: صفر تأليف · الأقفال الخمسة · الانحدار
==============================================================================
سند: `DEC-277` (تشغيل `56-TEAM-00`) · `DEC-278` (الباني) · `DEC-039`

**بصمة انحدار لا بصمة تكافؤ** — والتسمية مقصودة: لا توأم `JS` لهذه الطبقة،
فليس ثمّة طرفان يُقاس التطابق بينهما. والسند سابقةٌ مختومة: أدوات المشغّل
(`contrib_pull`/`contrib_analyze` — `DEC-254`) **بايثون وحدها**، والتوأمة
لِما يعمل في متصفح (`supervisor_core.js` لأن له `Supervisor.html`).

**وحرس التأجيل نافذ** (الفحص السادس): إن ظهر لهذه الطبقة سطحٌ في المتصفح
بلا توأم، تسقط البوابة — فلا تبقى فترةٌ بلا حرس (`140 §5`).

**والبصمة المتوقَّعة لا تُكتب هنا**: `gate.py` سلطتُها الواحدة (`DEC-273`).
"""
import hashlib
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import team_engine as TE
import team_report as TR

FAILS = []


def check(label, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + label + (" - " + detail if detail else ""))
    if not ok:
        FAILS.append(label)


PACK = json.load(io.open(os.path.join(HERE, "team_contentpack.json"),
                         encoding="utf-8"))
CASES = json.load(io.open(os.path.join(HERE, "team_cases.json"), encoding="utf-8"))


def _src(name):
    return io.open(os.path.join(HERE, name), encoding="utf-8").read()


# -- 1) صفر تأليف: كل نصٍّ موجودٌ حرفياً في مصدره المختوم -----------------
def test_zero_authoring():
    srcs = {k: _src(v) for k, v in PACK["_meta"]["sources"].items()}
    blob = "\n".join(srcs.values())
    # يُزال تشديد ماركداون من الطرفين: العناوين تُنقل بلا تشديد والنصّ واحد.
    # والتطبيع **معلَن** لا صامت - وهو الفارق الوحيد المسموح به.
    flat = blob.replace("**", "")
    missing = []

    def seen(v):
        return (v in blob) or (v.replace("**", "") in flat)

    def walk(node, path):
        if isinstance(node, str):
            if node.strip() and not seen(node):
                missing.append((path, node[:60]))
        elif isinstance(node, dict):
            for k, v in node.items():
                walk(v, path + (str(k),))
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, path + (str(i),))

    for key in ("dyad", "polar", "blind", "rebound", "combo", "heading",
                "lock", "banner"):
        walk(PACK[key], (key,))
    check("1 صفر تأليف - كل نصٍّ في مصدره", not missing,
          str(len(missing)) + " بلا مصدر: " + str(missing[:3]) if missing
          else "الحزمة كلّها مفكوكة من جداول مختومة")

    # الوسمان: صيغتهما الحاكمة في `k2_report` - لا صيغة ثانية لوسمٍ واحد
    k2 = _src("k2_report.py")
    bad = [t for t in PACK["tag"] if t not in k2]
    check("1 الوسمان بصيغة k2_report حرفياً", not bad, str(bad) if bad else "")


# -- 2) الأقفال الخمسة: مطبَّقة لا مذكورة ---------------------------------
BANNED = ["الأفضل", "الأضعف", "أفضل من", "أضعف من", "الأقوى",
          "تقييم أداء", "يستحق الترقية"]


def test_locks():
    body, audit = TR.build_report(CASES["team"]["P001-الثلاثي-المعتمد"])
    # اللفظ المحرَّم يظهر **في نصّ التحريم نفسه**: قفل «صفر مقارنة تفاضلية
    # (الأفضل/الأضعف)» والتنبيه «لا أداة تقييم أداء». فالفحص الساذج يعدّ
    # المنعَ مخالفةً - وهو الحقل الذي يعدّ الصحيحَ خطأً. فيُشدّ إلى معناه:
    # لا لفظ محرَّم **خارج** سطرٍ مختوم من الحزمة.
    sealed = set(PACK["lock"]) | {PACK["banner"]}
    hits = []
    for line in body.split("\n"):
        if any(sl in line for sl in sealed):
            continue
        hits += [(w, line[:50]) for w in BANNED if w in line]
    check("2 صفر مقارنة تفاضلية خارج نصوص التحريم", not hits,
          str(hits[:3]) if hits else str(len(sealed)) + " سطراً مختوماً مستثنىً")

    # صفر كشف خام: لا رقم SP في المتن - الرموز الوصفية وحدها
    nums = re.findall(r"(?<![\w-])\d{2,3}(?:\.\d)?(?![\w\d-])", body)
    check("2 صفر درجة خام في المتن", not nums,
          "أرقام: " + str(nums[:6]) if nums else "الرموز الوصفية وحدها")

    check("2 نصّ قفل العرض مطبوع",
          all(l in body for l in PACK["lock"]), "")
    check("2 التنبيه الإلزامي في الرأس",
          body.lstrip().startswith("> ") and PACK["banner"] in body[:200], "")
    check("2 الأقسام التسعة مصيَّرة", audit["sections_rendered"] == 9,
          str(audit["sections_rendered"]))


# -- 3) صفر لمس K1/K3/K4: القفل الخامس مقيسٌ لا موعود ---------------------
K3_K4 = ["EP", "IR", "BI", "CF", "WM", "TI", "PF", "OR", "TM", "PER"]


def test_isolation():
    body, audit = TR.build_report(CASES["team"]["ورشة-أربعة"])
    blob = body + json.dumps(audit, ensure_ascii=False)
    hits = [c for c in K3_K4
            if re.search(r"(?<![A-Za-z])" + c + r"(?![A-Za-z])", blob)]
    check("3 صفر رمز من K3/K4 في المخرج", not hits, str(hits) if hits else "")

    try:
        TE.run(CASES["failure"]["حقل_من_دائرة_أخرى"])
        check("3 حقل من دائرة أخرى يُرفض", False, "مرّ بلا رفض")
    except TE.InputContractError:
        check("3 حقل من دائرة أخرى يُرفض", True, "InputContractError")


# -- 4) عقد المدخل: يوقف ولا يخمّن ----------------------------------------
def test_contract():
    for name, members in CASES["failure"].items():
        try:
            TE.run(members)
            check("4 " + name + " يُرفض", False, "مرّ بلا رفض")
        except TE.InputContractError:
            check("4 " + name + " يُرفض", True)
        except Exception as e:                      # noqa: BLE001 - يُصنَّف
            check("4 " + name + " يُرفض", False,
                  "استثناء آخر: " + type(e).__name__)


# -- 5) مطابقة التشغيل المعتمد 56-TEAM-P001 -------------------------------
def test_dry_run():
    _b, a = TR.build_report(CASES["team"]["P001-الثلاثي-المعتمد"])
    hyb = {}
    for pr in a["pairs"]:
        hyb[pr["a"] + "x" + pr["b"]] = PACK["dyad"][pr["dyad"]]["hybrid"]
    check("5 الكيانات الهجينة الثلاثة",
          hyb == {"T-01xT-02": "العقلاني الرحيم",
                  "T-01xT-03": "مهندس التطور المُحصّن",
                  "T-02xT-03": "مبتكر المعنى"}, str(hyb))
    pol = [x["polar"] for x in a["inter_polarity"]]
    check("5 القطبية البينية P1 و P4", pol == ["P1", "P4"], str(pol))
    check("5 الفجوة R/O", a["collective_blind"]["uncovered"] == ["R", "O"],
          str(a["collective_blind"]["uncovered"]))
    doc = a["collective_blind"]["documented"]
    check("5 تركيبة موثَّقة واحدة",
          len(doc) == 1 and doc[0]["lenses"] == ["H", "St"],
          str([d["lenses"] for d in doc]))


# -- 6) حرس التأجيل: لا سطح متصفح بلا توأم --------------------------------
def test_deferral_guard():
    surfaces = ["engines.js", "reports.js", "dualreport.js",
                os.path.join("site", "app", "app.js")]
    leaked = []
    for f in surfaces:
        p = os.path.join(HERE, f)
        if os.path.exists(p) and re.search(
                r"buildReportTeam|TeamEngine|RawahilTeam", _src(f)):
            leaked.append(f)
    check("6 طبقة الفريق خارج حزمة المتصفح", not leaked,
          "ظهرت في " + str(leaked) + " بلا توأم" if leaked
          else "بايثون وحدها (سابقة DEC-254) - والحرس يُقلب عند بناء السطح")


# -- 7) بصمة الانحدار ------------------------------------------------------
def fingerprint():
    parts = []
    for name in sorted(CASES["team"]):
        body, audit = TR.build_report(CASES["team"][name])
        parts.append(name + " " + body + " " +
                     json.dumps(audit, ensure_ascii=False, sort_keys=True))
    for name in sorted(CASES["failure"]):
        try:
            TE.run(CASES["failure"][name])
            mode = "no-error"
        except TE.InputContractError:
            mode = "InputContractError"
        except Exception as e:                      # noqa: BLE001
            mode = "other:" + type(e).__name__
        parts.append(name + " " + mode)
    return hashlib.sha256("".join(parts).encode("utf-8")).hexdigest()[:16]


if __name__ == "__main__":
    print("=" * 76)
    test_zero_authoring()
    test_locks()
    test_isolation()
    test_contract()
    test_dry_run()
    test_deferral_guard()
    print("-" * 76)
    print("   بصمة انحدار الفريق: " + fingerprint())
    print("-" * 76)
    if FAILS:
        print("النتيجة النهائية: انحدار - " + str(len(FAILS)) + ": " +
              " · ".join(FAILS))
        raise SystemExit(1)
    print("النتيجة النهائية: لا انحدار")
