# -*- coding: utf-8 -*-
"""
parity_surface.py — المسح المنهجي لأسطح النقل (`DEC-237`)
===========================================================
سند: `DEC-199` (تكافؤ النسخ) · `DEC-200` (التجميد عند التباعد) · `ن-7`

**السبب:** ثلاث فجوات (`GAP-MSG-PARITY-01` · تصيير العشريات ·
`GAP-ISO-JS-01`) خرجت من مصدر واحد: **سطحُ نقلٍ لم يُقَس**. ونجت
كلّها لأن ما لا يُقاس لا يسقط. هذا الملف يمسح ما تبقّى.

**ما كان مقيساً قبله:**
  · `parity_py`         — الملف والأسطر و`t8` والتسليم · 17 قيمة حديّة
  · `parity_reports`    — نصّ التقرير
  · `parity_supervisor` — أحكام المشرف
  · `parity_messages`   — رسائل الاستثناءات
  · `parity_isolation`  — تدقيق العزل وحقل `isolation`

**ما يمسحه هذا الملف — خمسة أسطح لم تُقَس قط:**
  أ  **الثوابت** — النسخ والأوتاد والأسماء وقائمة الألفاظ المحظورة
  ب  **خريطة بنود الأداة** (`ITEM_MAP`) — انجرافها كارثيّ وغير مرئي
  ج  **`score_from_raw`** — مسار الخام→`SP` كاملاً، لا `compute_ss_sp` وحدها
  د  **كتلة التدقيق كاملة** — حقلاً بحقل، في النطاقين وفي الدائرتين
  هـ **شبكة حدّية كثيفة** — 0…100 بخطوة 0.1 على دوالّ الفرز

كل قسم يقيس شيئاً واحداً (`ن-7/②`). أي تباعد ⇒ يُجمَّد الطرفان.
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import k2_engine as E2
import k3_engine as E3
import k2_report as R2
import k3_report as R3

CASES = json.load(open(os.path.join(HERE, "parity_cases.json"), encoding="utf-8"))


def node(script, *args):
    r = subprocess.run(["node", "-e", script, *args],
                       capture_output=True, text=True, cwd=HERE)
    if r.returncode != 0:
        raise RuntimeError((r.stderr or r.stdout)[:900])
    return json.loads(r.stdout)


def canon(v):
    """تقنين مطابق لعرف `parity_py` — الأعداد لعشرة أرقام، المفاتيح مفروزة."""
    if v is None:
        return None
    if isinstance(v, bool):
        return v
    if isinstance(v, float):
        return round(v, 10)
    if isinstance(v, (list, tuple)):
        return [canon(x) for x in v]
    if isinstance(v, dict):
        return {k: canon(v[k]) for k in sorted(v)}
    return v


def diff(a, b, path=""):
    """أول اختلاف بمساره — لا تُبلَّغ الرسالة إلا بموضعها."""
    if type(a) is not type(b) and not (isinstance(a, (int, float))
                                       and isinstance(b, (int, float))):
        return f"{path}: نوع مختلف {type(a).__name__}≠{type(b).__name__}"
    if isinstance(a, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a:
                return f"{path}/{k}: غائب في بايثون"
            if k not in b:
                return f"{path}/{k}: غائب في JS"
            d = diff(a[k], b[k], f"{path}/{k}")
            if d:
                return d
        return None
    if isinstance(a, list):
        if len(a) != len(b):
            return f"{path}: طول مختلف {len(a)}≠{len(b)}"
        for i, (x, y) in enumerate(zip(a, b)):
            d = diff(x, y, f"{path}[{i}]")
            if d:
                return d
        return None
    return None if a == b else f"{path}: {a!r} ≠ {b!r}"


# ══ أ · الثوابت ═════════════════════════════════════════════════════════
NODE_CONST = r"""
const E = require("./engines.js");
const o = {};
for (const [c, M] of [["K2", E.K2], ["K3", E.K3]])
  for (const k of Object.keys(M))
    if (k === k.toUpperCase() && typeof M[k] !== "function") o[c + "." + k] = M[k];
console.log(JSON.stringify(o));
"""


def sweep_constants():
    js = node(NODE_CONST)
    py = {
        "K2.ENGINE_VERSION": getattr(E2, "ENGINE_VERSION", None),
        "K2.SPEC_VERSION": getattr(E2, "SPEC_VERSION", None),
        "K2.INSTRUMENT_PIN": getattr(E2, "INSTRUMENT_PIN", None),
        "K2.MAX_RAW": E2.MAX_RAW, "K2.LENSES": list(E2.LENSES),
        "K2.LENS_NAME": dict(E2.LENS_NAME), "K2.FORBIDDEN": list(E2._FORBIDDEN),
        "K3.ENGINE_VERSION": E3.ENGINE_VERSION, "K3.SPEC_VERSION": E3.SPEC_VERSION,
        "K3.INSTRUMENT_PIN": E3.INSTRUMENT_PIN, "K3.MAX_RAW": E3.MAX_RAW,
        "K3.SKILLS": list(E3.SKILLS), "K3.USER_NAME": dict(E3.USER_NAME),
    }
    bad, absent = [], []
    for k in sorted(py):
        if k not in js:
            absent.append(k)
            continue
        d = diff(canon(py[k]), canon(js[k]), k)
        if d:
            bad.append(d)
    extra = sorted(k for k in js if k not in py and not k.endswith("ITEM_MAP")
                   and k.split(".")[1] not in ("EDGES", "CELLS", "FAMILY_ORDER",
                                               "COVERAGE", "BLINDNESS"))
    return len(py), bad, absent, extra


# ══ ب · خريطة بنود الأداة ═══════════════════════════════════════════════
NODE_ITEMS = 'const E=require("./engines.js");console.log(JSON.stringify(E.K2.ITEM_MAP));'


def sweep_items():
    js = node(NODE_ITEMS)
    # الاسم مثبَّت صراحةً — الاكتشاف التلقائي التقط قاموساً خاطئاً
    # في أول تشغيل وأعطى «تباعداً» كاذباً. الحارس لا يُبنى على حدس.
    src = getattr(E2, "K2_ITEM_MAP", None)
    if src is None:
        return None, "`K2_ITEM_MAP` غير موجودة في `k2_engine` بهذا الاسم"
    py = {k: [list(t) for t in v] for k, v in src.items()}
    n = sum(len(v) for v in py.values())
    return n, diff(canon(py), canon(js), "ITEM_MAP")


NODE_ITEMS_K3 = 'const E=require("./engines.js");console.log(JSON.stringify(E.K3.ITEM_MAP));'


def sweep_items_k3():
    """`DEC-275` — خريطة $K_3$ صارت في المحرّك، **فتُقاس كأختها**: حقلٌ
    يُضاف فاحصاً أو لا يُضاف (`00-HANDOVER §6①`). والاسم مثبَّت صراحةً كما
    في $K_2$ — لا اكتشاف بالحدس."""
    js = node(NODE_ITEMS_K3)
    src = getattr(E3, "ITEM_MAP", None)
    if src is None:
        return None, "`ITEM_MAP` غير موجودة في `k3_engine` بهذا الاسم"
    py = {k: [list(t) for t in v] for k, v in src.items()}
    n = sum(len(v) for v in py.values())
    return n, diff(canon(py), canon(js), "ITEM_MAP_K3")


# ══ ج · مسار الخام → SP ═════════════════════════════════════════════════
NODE_RAW = r"""
const E = require("./engines.js");
const cases = JSON.parse(process.argv[1]);
console.log(JSON.stringify(cases.map(r => E.K2.scoreFromRaw(r))));
"""


def raw_grid():
    """شبكة خام حقيقية: إجابة لكل بند (`choice`/`ratingA`/`ratingB`)."""
    items = sorted({it for v in E2.K2_ITEM_MAP.values() for it, _ in v})
    grids = []
    for ch, ra, rb in [("a", 0, 0), ("b", 0, 0), ("a", 5, 1), ("b", 1, 5),
                       ("a", 9, 9), ("b", 9, 0), ("a", 3, 7)]:
        grids.append({it: {"choice": ch, "ratingA": ra, "ratingB": rb}
                      for it in items})
    # شبكات غير متجانسة — تكسر التماثل الذي قد يخفي تباعداً
    for k in range(6):
        grids.append({it: {"choice": "a" if (it + k) % 2 else "b",
                           "ratingA": (it * 3 + k) % 10,
                           "ratingB": (it * 7 + k) % 10} for it in items})
    return grids


def sweep_raw():
    grid = raw_grid()
    js = node(NODE_RAW, json.dumps(grid, ensure_ascii=False))
    py = [E2.score_from_raw(r) for r in grid]
    return len(grid), diff(canon(py), canon(js), "score_from_raw")


# ══ د · كتلة التدقيق كاملة ══════════════════════════════════════════════
NODE_AUDIT = r"""
const R = require("./reports.js");
const cases = JSON.parse(process.argv[1]);
const out = { k2_full: {}, k2_brief: {}, k3: {} };
for (const [n, sp] of Object.entries(cases.k2)) {
  out.k2_full[n]  = R.buildReportK2(sp, "full")[1];
  out.k2_brief[n] = R.buildReportK2(sp, "brief")[1];
}
for (const [n, sp] of Object.entries(cases.k3)) out.k3[n] = R.buildReportK3(sp)[1];
console.log(JSON.stringify(out));
"""


def sweep_audit():
    js = node(NODE_AUDIT, json.dumps(CASES, ensure_ascii=False))
    py = {"k2_full": {}, "k2_brief": {}, "k3": {}}
    for n, sp in CASES["k2"].items():
        py["k2_full"][n] = R2.build_report(sp, mode="full")[1]
        py["k2_brief"][n] = R2.build_report(sp, mode="brief")[1]
    for n, sp in CASES["k3"].items():
        py["k3"][n] = R3.build_report(sp)[1]
    n_fields = sum(len(v) for g in py.values() for v in g.values())
    return len(py["k2_full"]) * 2 + len(py["k3"]), n_fields, \
        diff(canon(py), canon(js), "audit")


# ══ هـ · شبكة حدّية كثيفة ═══════════════════════════════════════════════
NODE_EDGE = r"""
const E = require("./engines.js");
const vals = JSON.parse(process.argv[1]);
console.log(JSON.stringify(vals.map(v =>
  [E.K2.octalCode(v), E.K2.compState(v), E.K3.octalCode(v), E.K3.band(v), E.K3.pole(v)])));
"""


def sweep_edges():
    vals = [round(i / 10, 1) for i in range(-20, 1021)]
    js = node(NODE_EDGE, json.dumps(vals))
    py = [[E2.octal_code(v), E2.comp_state(v),
           E3.octal_code(v), E3.band(v), E3.pole(v)] for v in vals]
    return len(vals), diff(canon(py), canon(js), "edges")


# ══ التشغيل ═════════════════════════════════════════════════════════════
def main():
    errs = []

    n, bad, absent, extra = sweep_constants()
    if not bad and not absent:
        print(f"✅ أ الثوابت — {n} ثابتاً متطابقاً (نسخ · أوتاد · أسماء · محظورات)")
    else:
        print("❌ أ الثوابت")
        errs += [f"أ/{x}" for x in bad] + [f"أ: {k} غائب في JS" for k in absent]
    if extra:
        print(f"   ⚠️ ثوابت في JS بلا نظير مقيس في بايثون: {extra}")

    n, d = sweep_items()
    if n is None:
        print(f"⚠️ ب خريطة البنود — {d}")
        errs.append(f"ب: {d}")
    elif d:
        print("❌ ب خريطة البنود"); errs.append(f"ب/{d}")
    else:
        print(f"✅ ب خريطة البنود — {n} بنداً متطابقاً عبر الأبعاد الثمانية")

    n3, d3 = sweep_items_k3()
    if n3 is None:
        print(f"⚠️ ب-٢ خريطة بنود K3 — {d3}")
        errs.append(f"ب-٢: {d3}")
    elif d3:
        print("❌ ب-٢ خريطة بنود K3"); errs.append(f"ب-٢/{d3}")
    else:
        print(f"✅ ب-٢ خريطة بنود K3 — {n3} بنداً متطابقاً عبر المهارات الخمس")

    n, d = sweep_raw()
    print(("✅" if not d else "❌") + f" ج مسار الخام→SP — {n} شبكة")
    if d:
        errs.append(f"ج/{d}")

    n_r, n_f, d = sweep_audit()
    print(("✅" if not d else "❌") +
          f" د كتلة التدقيق — {n_r} تقريراً · {n_f} حقلاً · النطاقان والدائرتان")
    if d:
        errs.append(f"د/{d}")

    n, d = sweep_edges()
    print(("✅" if not d else "❌") + f" هـ الشبكة الحدّية — {n} قيمة (‑2.0…102.0 بخطوة 0.1)")
    if d:
        errs.append(f"هـ/{d}")

    print("-" * 76)
    if errs:
        print(f"النتيجة النهائية: ❌ انحدار — {len(errs)} · يُجمَّد الطرفان (DEC-200)")
        for e in errs[:12]:
            print("   ·", e)
        return 1
    print("النتيجة النهائية: ✅ لا انحدار")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
