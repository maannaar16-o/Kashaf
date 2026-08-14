# -*- coding: utf-8 -*-
"""
test_report_k4.py — فحوص تقرير دائرة الإنجاز (K4)
===================================================
سند: `DEC-266` (`136-K4-ENGINE §5`).

كل فحص هنا **يقيس ما يعلنه** — لا حقل يدّعي الفحص ولا يفحص
(`00-HANDOVER §6①`). والفشل يوقف الإصدار بلا إصلاح صامت.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import k4_engine as E4
from k4_content import ContentPack, VALVES, TRAINING_VOID
from k4_report import build_report, build_crossing_surface, crossing_entries
from sp_gate import scan, scan_pct

FAILS = []


def check(label, ok, detail=""):
    print(f"{'✅' if ok else '❌'} {label}" + (f" — {detail}" if detail else ""))
    if not ok:
        FAILS.append(label)


def _read(name):
    with open(os.path.join(HERE, name), encoding="utf-8") as fh:
        return fh.read()


# ── أ. صفر تأليف — كل نص في الحزمة موجود حرفياً في مصدره ────────────────
def test_zero_authoring():
    pack = ContentPack()
    src = pack.sources()
    docs = {k: _read(v) for k, v in src.items()}
    missing = []

    for v in VALVES:
        for key, txt in pack.raw["valve"][v].items():
            if txt not in docs[v]:
                missing.append(f"valve:{v}:{key}")
    for k, txt in pack.raw["reserve"].items():
        if k == "opening":
            if not any(txt in d for d in docs.values()):
                missing.append("reserve:opening")
            continue
        if txt not in docs[k]:
            missing.append(f"reserve:{k}")
    # أسئلة الفرز — مصدرها وثيقة المميّز (`134`) وطبقة المستخدم معاً
    discrim = _read("134-K4-DISCRIM_DEC-264.md")
    for code, txt in pack.raw["lookalike"].items():
        if txt not in discrim and not any(txt in d for d in docs.values()):
            missing.append(f"lookalike:{code}")
    for v, txt in pack.raw["training"].items():
        if txt not in docs[v]:
            missing.append(f"training:{v}")
    for v, txt in pack.raw["training_void"].items():
        if txt not in docs[v]:
            missing.append(f"training_void:{v}")
    surfaces = _read("138-K4-SURFACES_DEC-268.md")
    cr = pack.raw["crossing"]
    for k in ("heading", "lead", "closing"):
        if cr[k] not in surfaces:
            missing.append(f"crossing:{k}")
    for code, txt in cr["entry"].items():
        if txt not in surfaces:
            missing.append(f"crossing:entry:{code}")
    cp = pack.raw["composed"]
    for k, txt in cp.items():
        if isinstance(txt, dict):
            for k2, t2 in txt.items():
                if t2 not in surfaces:
                    missing.append(f"composed:{k}:{k2}")
        elif txt not in surfaces:
            missing.append(f"composed:{k}")
    contract = docs["_contract"]
    for k, txt in pack.raw["heading"].items():
        if txt not in contract:
            missing.append(f"heading:{k}")
    # الوسم للقارئ (`DEC-283`) مختومٌ في وثيقته لا في العقد — فالمصدر
    # أحدهما، والنقل مقيسٌ في الحالين (`146 §4`: يُختم ثم يُنقل حرفياً).
    notice_doc = docs.get("_notice", "")
    for k, txt in pack.raw["notice"].items():
        if txt not in contract and txt not in notice_doc:
            missing.append(f"notice:{k}")

    check("صفر تأليف — كل نص بمصدره المختوم", not missing,
          f"صفر نص بلا مصدر · فُحص {sum(len(pack.raw[g]) if isinstance(pack.raw[g], dict) else 0 for g in ('reserve','lookalike','training','training_void','heading','notice')) + len(VALVES)*4} نصاً"
          if not missing else "بلا مصدر: " + " · ".join(missing[:8]))


# ── ب. العزل الثلاثي — صفر رمز K2/K3 في محرك K4 ومخرجه ──────────────────
K2_SYMS = ["K2-A", "K2-R", "K2-O", "K2-C", "K2-S", "K2-E", "K2-St", "K2-H"]
K3_SYMS = ["K3-EP", "K3-IR", "K3-BI", "K3-CF", "K3-ST"]


def test_isolation():
    code = _read("k4_engine.py") + _read("k4_report.py") + _read("k4_contentpack.json")
    hits = [s for s in (K2_SYMS + K3_SYMS) if s in code]
    check("العزل الثلاثي — الكود والحزمة", not hits,
          "صفر رمز عابر" if not hits else "تسرّب: " + ",".join(hits))

    body, _ = build_report(dict(WM=62, TI=78, F=74, PF=38, OR=55, TM=41, PER=44))
    out_hits = [s for s in (K2_SYMS + K3_SYMS) if s in body]
    check("العزل الثلاثي — المخرج", not out_hits,
          "صفر رمز عابر في التقرير" if not out_hits else "تسرّب: " + ",".join(out_hits))


# ── ج. حارسا المخرج على كل حالة انحدار ──────────────────────────────────
def test_guards():
    cases = json.load(open(os.path.join(HERE, "parity_cases_k4.json"), encoding="utf-8"))["k4"]
    bad = []
    for name, sp in cases.items():
        body, _ = build_report(sp)
        if scan(body) or scan_pct(body):
            bad.append(name)
    check("ح-4/ح-5 على كل الحالات", not bad,
          f"{len(cases)} تقريراً · صفر تسرّب" if not bad else f"{len(bad)} تسرّب")


# ── د. اكتمال الحزمة + رفض التأليف حيث صُرِّح بالفراغ ───────────────────
def test_pack_contract():
    check("اكتمال الحزمة", not ContentPack().missing(), "صفر فجوة")

    raw = json.loads(json.dumps(ContentPack().raw, ensure_ascii=False))
    raw["training"]["WM"] = "تدريب مُؤلَّف"
    gaps = ContentPack(raw).missing()
    check("رفض التأليف حيث صُرِّح بالفراغ (WM)",
          any(g.startswith("training:WM") for g in gaps),
          "مخالفة تُرفع لا تُقبل")

    raw2 = json.loads(json.dumps(ContentPack().raw, ensure_ascii=False))
    del raw2["valve"]["PER"]["U05"]
    check("النص الغائب فجوة تُرفع",
          "valve:PER:U05" in ContentPack(raw2).missing(), "لا ملء صامت")


# ── هـ. عقد المدخل ──────────────────────────────────────────────────────
def test_input_contract():
    ok = 0
    for spec in ({"WM": 60, "TI": 60, "F": 60, "PF": 60, "OR": 60, "TM": 60},
                 {"WM": "س", "TI": 60, "F": 60, "PF": 60, "OR": 60, "TM": 60, "PER": 60},
                 {}):
        try:
            E4.run(spec)
        except E4.InputContractError:
            ok += 1
    check("عقد المدخل يوقف بلا إصلاح صامت", ok == 3, f"{ok}/3")


# ── و. صفر عتبة مستحدثة في الكود ────────────────────────────────────────
SEALED_NUMBERS = {"0", "1", "2", "10", "11", "20", "40", "50", "66", "70", "85", "100"}


def _strip_prose(src):
    """يحذف السلاسل النصية والتعليقات — الفحص يقيس **أرقام الكود** لا أكواد
    الاستشهاد في التعليقات (`TRF-010` · `DEC-261` وأمثالها ليست عتبات)."""
    src = re.sub(r'"""[\s\S]*?"""', "", src)
    src = re.sub(r"'''[\s\S]*?'''", "", src)
    src = re.sub(r'"[^"\n]*"', '""', src)
    src = re.sub(r"'[^'\n]*'", "''", src)
    return re.sub(r"#[^\n]*", "", src)


def test_no_new_threshold():
    src = _read("k4_engine.py")
    body = _strip_prose(
        src.split("def octal_code")[1].split("# ---")[0]
        + src.split("def band(")[1].split("def state(")[0])
    sealed = {float(s) for s in SEALED_NUMBERS}
    nums = {float(n) for n in re.findall(r"\b\d+(?:\.\d+)?\b", body)}
    novel = nums - sealed
    check("صفر عتبة مستحدثة", not novel,
          f"{len(nums)} رقماً كلها مختومة سلفاً (DEC-261/TRF-010)"
          if not novel else f"أرقام غير مختومة: {sorted(novel)}")


# ── ز-٢. السطحان — الفصل والشرط والصياغة المغلقة ────────────────────────
def test_surfaces():
    pack = ContentPack()
    cr_texts = list(pack.raw["crossing"]["entry"].values()) + \
               [pack.raw["crossing"]["heading"], pack.raw["crossing"]["lead"]]

    # فصلٌ قاطع: نصوص السطح العابر لا تظهر داخل تقرير الدائرة
    cases = json.load(open(os.path.join(HERE, "parity_cases_k4.json"), encoding="utf-8"))["k4"]
    leaked = []
    for name, sp in cases.items():
        body, _ = build_report(sp)
        if any(x in body for x in cr_texts):
            leaked.append(name)
    check("السطح العابر لا يظهر داخل تقرير الدائرة", not leaked,
          f"{len(cases)} تقريراً · صفر تسرّب" if not leaked else f"{len(leaked)} تسرّب")

    # الشرط: لا سطح بلا مشغِّل — ومشغِّله نطاقات K4 وحدها
    none_sp = dict(WM=60, TI=60, F=60, PF=60, OR=60, TM=60, PER=60)
    b0, a0 = build_crossing_surface(none_sp)
    check("لا سطح عابر بلا مشغِّل", b0 == "" and not a0["rendered"], "صفر مشغِّل ⇒ صفر مخرج")

    ti_sp = dict(none_sp, TI=30)
    _, a1 = build_crossing_surface(ti_sp)
    check("مشغِّل المبادرة يستدعي ثلاثة قيود + المبدأ",
          a1["entries"] == ["K4-XR-03", "K4-XR-02", "K4-XR-05", "K4-XR-06"],
          " · ".join(a1["entries"]))

    # القيود غير المسطَّحة لا تظهر أبداً
    all_sp = dict(WM=30, TI=30, F=30, PF=30, OR=30, TM=30, PER=30)
    bx, ax = build_crossing_surface(all_sp)
    unsurfaced = {"K4-XR-01", "K4-XR-07", "K4-XR-09"}
    check("القيود غير المسطَّحة تبقى سجلاً",
          not (unsurfaced & set(ax["entries"])), "ثلاثة قيود سجلاً لا سطحاً")

    # حارسا المخرج على السطح العابر
    check("ح-4/ح-5 على السطح العابر", not scan(bx) and not scan_pct(bx), "صفر تسرّب")

    # بنك الصياغة مغلق: «تحييد» بلا صياغة، ودسّها يُرفع مخالفةً
    raw = json.loads(json.dumps(pack.raw, ensure_ascii=False))
    raw["composed"]["kind"]["تحييد"] = "صياغة مُقحَمة"
    check("بنك الصياغة مغلق — «تحييد» بصفر قيود",
          any("تحييد" in g for g in ContentPack(raw).missing()),
          "الإقحام يُرفع لا يُقبل")

    # السطح المركَّب يُثري ولا يضيف قسماً
    _, a = build_report(dict(WM=60, TI=60, F=90, PF=30, OR=60, TM=30, PER=30))
    check("السطح المركَّب لا يضيف قسماً", a["sections_rendered"] <= 8,
          f"أقسام معروضة: {a['sections_rendered']} ≤ 8")


# ── ز. قواعد العرض ر-3 / ر-4 / ر-5 ──────────────────────────────────────
def test_display_rules():
    # ر-4: التعادل يُعرض بكامله
    body, a = build_report(dict(WM=30, TI=32, F=60, PF=60, OR=60, TM=60, PER=60))
    check("ر-4 — التعادل يُعرض بلا كسر",
          a["bottleneck"]["tie"] and len(a["bottleneck"]["valves"]) == 2
          and "تُعرض جميعاً بلا ترجيح" in body, "محطتان معاً")

    # ر-3: كتلة تحفّظ واحدة مهما تعدّدت الصمامات
    body3, a3 = build_report(dict(WM=60, TI=60, F=90, PF=60, OR=88, TM=60, PER=95))
    check("ر-3 — كتلة تحفّظ واحدة",
          len(a3["reading_reserve"]) == 3
          and body3.count("الأرجح أن درجتك العالية هنا كفاءة حقيقية.") == 1,
          "ثلاثة صمامات · كتلة واحدة")

    # ر-5: OUT ⇒ تقرير فجوة بلا نمط
    body5, a5 = build_report(dict(WM=-4, TI=60, F=60, PF=60, OR=60, TM=60, PER=60))
    check("ر-5 — لا نمط فوق نقص",
          a5["gap_report"] and not a5["patterns_recognized"]
          and "تقرير فجوة تشغيلية" in body5, "الفجوة معلَنة")


# ── ح. الحقول الإعلانية مصرَّح بها لا مقيسة ─────────────────────────────
def test_declared_fields():
    a = E4.run(dict(WM=60, TI=60, F=60, PF=60, OR=60, TM=60, PER=60)).audit
    check("الحقول الإعلانية مصرَّحة",
          a["accepted_debts"] and a["open_debts"],
          "مصدرها سجل الحوكمة — الاستثناء المعلَن (00-HANDOVER §6①)")


if __name__ == "__main__":
    print("=" * 76)
    test_zero_authoring()
    test_isolation()
    test_guards()
    test_pack_contract()
    test_input_contract()
    test_no_new_threshold()
    test_surfaces()
    test_display_rules()
    test_declared_fields()
    print("-" * 76)
    if FAILS:
        print(f"النتيجة النهائية: ❌ انحدار — {len(FAILS)}: " + " · ".join(FAILS))
        raise SystemExit(1)
    print("النتيجة النهائية: ✅ لا انحدار")
