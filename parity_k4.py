# -*- coding: utf-8 -*-
"""
parity_k4.py — الطرف البايثوني من أداة تكافؤ محرّك K4 + المقارن
=================================================================
سند: `DEC-199`/`DEC-200` (التكافؤ المقيس · تجميد الطرفين عند التباعد)
     `DEC-266` (`136-K4-ENGINE` — المرحلة ٨)

يُشغّل النسختين على مجموعة الانحدار نفسها ويقارن البصمات.
**لا أسبقية لبايثون** — عند أي اختلاف يُجمَّد الطرفان ويُصدر تقرير تباعد.
"""
import hashlib, json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import k4_engine as E4
from k4_report import build_report as R4, build_crossing_surface as X4

CASES_PATH = os.path.join(HERE, "parity_cases_k4.json")


# ── التقنين — مطابق حرفياً لنظيره في parity_k4_js.js ─────────────────────
def canon(v):
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return f"{round(float(v), 1):.1f}"
    if isinstance(v, str):
        return json.dumps(v, ensure_ascii=False)
    if isinstance(v, (list, tuple)):
        return "[" + ",".join(canon(x) for x in v) + "]"
    if isinstance(v, dict):
        keys = sorted(v.keys())            # فرز بنقطة الترميز — لا locale
        return "{" + ",".join(json.dumps(k, ensure_ascii=False) + ":" + canon(v[k])
                              for k in keys) + "}"
    raise TypeError(f"نوع غير مقنَّن: {type(v)}")


def sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]


def build():
    cases = json.load(open(CASES_PATH, encoding="utf-8"))
    h = {"k4": {}, "report": {}, "crossing": {}, "failure": {}}
    raw = {"k4": {}, "report": {}, "crossing": {}, "failure": {}}

    for name, sp in cases["k4"].items():
        s = canon(E4.run(sp).audit)
        raw["k4"][name] = s
        h["k4"][name] = sha(s)
        # التقرير — النصّ الكامل **وكتلة تدقيقه** يدخلان البصمة.
        # كانت الكتلة مُهمَلة (`_`) فمرّ غياب `pack_sha`/`report_sha256` من
        # التوأم JS صامتاً: تكافؤُ نصٍّ ليس تكافؤَ عقدٍ (`00-HANDOVER §6③`).
        body, rep_audit = R4(sp)
        s_rep = body + "\u0000" + canon(rep_audit)
        raw["report"][name] = s_rep
        h["report"][name] = sha(s_rep)
        # سطح القراءة العابرة — مخرج مستقل يدخل البصمة بذاته
        xbody, xa = X4(sp)
        xs = xbody + "\u0000" + canon(xa)
        raw["crossing"][name] = xs
        h["crossing"][name] = sha(xs)

    for name, spec in cases["failure"].items():
        # القيم النصية "NaN"/"Infinity" تُحوَّل عدداً في الطرفين قبل التمرير —
        # كي يقيس الاختبارُ عقدَ المحرك لا تحويلَ JSON.
        spec = {k: (float(v) if v in ("NaN", "Infinity", "-Infinity") else v)
                for k, v in spec.items()}
        try:
            E4.run(spec)
            mode = "no-error"
        except E4.InputContractError:
            mode = "InputContractError"
        except Exception as e:                     # noqa: BLE001 — تصنيف لا ابتلاع
            mode = "other:" + type(e).__name__
        s = canon({"mode": mode})
        raw["failure"][name] = s
        h["failure"][name] = sha(s)

    h["GLOBAL"] = sha(canon({"k4": h["k4"], "report": h["report"], "crossing": h["crossing"], "failure": h["failure"]}))
    return h, raw


def divergence_report(group, key, a, b, pa, pb):
    print(f"\n❌ تباعد — {group}/{key}")
    print(f"   بايثون = {a}\n   JS     = {b}")
    if pa and pb:
        for i, (ca, cb) in enumerate(zip(pa, pb)):
            if ca != cb:
                lo = max(0, i - 60)
                print(f"   أول اختلاف عند {i}:")
                print(f"     …{pa[lo:i+60]}")
                print(f"     …{pb[lo:i+60]}")
                break
        else:
            print(f"   الطول مختلف: بايثون={len(pa)} · JS={len(pb)}")


def main():
    py_h, py_raw = build()
    js = json.loads(subprocess.run(
        ["node", os.path.join(HERE, "parity_k4_js.js"), CASES_PATH],
        capture_output=True, text=True, check=True).stdout)
    js_h, js_raw = js["hashes"], js["raw"]

    diverged = []
    for group in ("k4", "report", "crossing", "failure"):
        for key in sorted(set(py_h[group]) | set(js_h[group])):
            a, b = py_h[group].get(key), js_h[group].get(key)
            if a != b:
                diverged.append((group, key, a, b))

    total = sum(len(py_h[g]) for g in ("k4", "report", "crossing", "failure"))
    print(f"{'المجموعة':<12}{'الحالات':<10}{'الحالة'}")
    print("-" * 78)
    for g in ("k4", "report", "crossing", "failure"):
        bad = sum(1 for d in diverged if d[0] == g)
        print(f"{g:<12}{len(py_h[g]):<10}{'✅ متطابق' if not bad else f'❌ {bad} تباعد'}")
    print("-" * 78)

    for g, k, a, b in diverged:
        divergence_report(g, k, a, b,
                          py_raw.get(g, {}).get(k), js_raw.get(g, {}).get(k))

    if diverged:
        print(f"\n🧊 **الطرفان مجمَّدان** — {len(diverged)} تباعد. "
              f"لا إصدار قبل الحسم (DEC-200).")
        return 1

    print(f"\n✅ تكافؤ تامّ — {total} حالة · صفر تباعد")
    print(f"   بصمة محرّك K4: بايثون={py_h['GLOBAL']} · JS={js_h['GLOBAL']}")
    assert py_h["GLOBAL"] == js_h["GLOBAL"]
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
