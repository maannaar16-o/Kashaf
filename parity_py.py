# -*- coding: utf-8 -*-
"""
parity_py.py — الطرف البايثوني من أداة التكافؤ + المقارن (DEC-199 · DEC-200)
============================================================================
يُشغّل النسختين على مجموعة الانحدار نفسها ويقارن البصمات.
عند أي اختلاف: **يُجمَّد الطرفان** ويُصدر تقرير تباعد (87-PARITY §4-ب).
لا أسبقية لبايثون — المرجع هو خط الأساس.
"""
import hashlib, json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import k2_engine as E2
import k3_engine as E3


# ── التقنين — مطابق حرفياً لنظيره في parity_js.js ────────────────────────
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


def fail_mode(fn):
    try:
        fn()
        return "no-error"
    except E2.InputContractError:
        return "InputContractError"
    except E3.InputContractError:
        return "InputContractError"
    except Exception as e:
        return "other:" + type(e).__name__


def _gates_baseline(a):
    """يعيد صياغة gates_fired وفق نصّ السند (57 §audit) — الطرفان كانا يخالفانه."""
    out = []
    for g in a["gates_fired"]:
        if g.startswith("G5"):
            continue
        if g.startswith("G1:"):
            out.append("G1:low_trust=" + ("true" if "True" in g else "false"))
        elif g.startswith("G2:"):
            hi = a["bands"]
            lst = [s for s in ("IR", "BI", "CF", "ST") if hi[s] == "high"]
            out.append("G2:high=[" + ",".join(lst) + "]")
        else:
            out.append(g)
    return out


def build():
    cases = json.load(open(os.path.join(HERE, "parity_cases.json"), encoding="utf-8"))
    out = {"k2": {}, "k3": {}, "failure": {}, "boundary": {}}

    for name, sp in cases["k2"].items():
        r = E2.run(sp=sp)
        p = r.profile
        out["k2"][name] = canon({
            "center": p.center, "ranked": p.ranked, "dominant": p.dominant,
            "support": p.support, "off": p.off, "ignited": p.ignited,
            "lines": [{"code": l.code, "lens": l.lens, "kind": l.kind,
                       "state": l.state, "layer": l.layer} for l in r.lines],
            "t8": r.t8,
            "delivery": r.delivery_questions,
            "stitch": r.stitch,
            "codes": {d: E2.octal_code(sp[d]) for d in E2.LENSES},
        })

    for name, sp in cases["k3"].items():
        res = E3.run(sp)
        a = res.audit
        out["k3"][name] = canon({
            "sp": a["sp"], "codes": a["codes"], "bands": a["bands"],
            "cells_activated": a["cells_activated"], "cost_map": a["cost_map"],
            "patterns_recognized": a["patterns_recognized"],
            "containment_state": a["containment_state"],
            "root_question": a["root_question"], "excluded_out": a["excluded_out"],
            # DEC-206: G5 صار منقولاً — لا استثناء (كان مستثنى حين لم يُنقل)
            "gates_fired": a["gates_fired"],
            "engine_version": E3.ENGINE_VERSION, "spec_version": E3.SPEC_VERSION,
            "instrument_pin": E3.INSTRUMENT_PIN,
        })

    out["failure"]["k2:y+z!=7"]  = fail_mode(lambda: E2.compute_ss_sp(30, 5, 1))
    out["failure"]["k2:y+z==7"]  = fail_mode(lambda: E2.compute_ss_sp(30, 5, 2))
    out["failure"]["k3:y+z!=11"] = fail_mode(lambda: E3.compute_ss_sp(44, 8, 4))
    out["failure"]["k3:y+z==11"] = fail_mode(lambda: E3.compute_ss_sp(44, 8, 3))
    out["failure"]["k2:missing-lens"] = fail_mode(lambda: E2.run(sp={"A": 50}))

    for v in [-0.1, 0, 19.9, 20, 20.1, 39.9, 40, 40.1, 49.9, 50, 50.1,
              69.9, 70, 70.1, 85, 100, 100.1]:
        out["boundary"][f"k2:{v}"] = canon([E2.octal_code(v), E2.comp_state(v)])
        out["boundary"][f"k3:{v}"] = canon([E3.octal_code(v), E3.band(v), E3.pole(v)])

    hashes = {g: {k: sha(t) for k, t in out[g].items()} for g in ("k2", "k3")}
    hashes["failure"] = out["failure"]
    hashes["boundary"] = out["boundary"]
    hashes["frozen_registry"] = sha(canon(sorted(load_frozen().keys())))
    hashes["GLOBAL"] = sha(canon(hashes))
    return hashes, out


# ── المقارن ──────────────────────────────────────────────────────────────
def load_frozen():
    """DEC-202 — نقاط مجمَّدة: تُستبعَد من البصمة ولا تُخفى.
       الشروط في 87-PARITY §4-ب. سجل فارغ = لا تجميد قائم."""
    fp = os.path.join(HERE, "parity_frozen.json")
    if not os.path.exists(fp):
        return {}
    return json.load(open(fp, encoding="utf-8"))


def divergence_report(group, key, py_v, js_v, py_raw, js_raw):
    print(f"\n{'='*78}\n🔴 تقرير تباعد — {group}/{key}\n{'='*78}")
    print(f"| موقع التباعد | {group} · {key} |")
    print(f"| مخرج بايثون  | {str(py_v)[:120]} |")
    print(f"| مخرج JS      | {str(js_v)[:120]} |")
    if py_raw and js_raw and py_raw != js_raw:
        for i, (c1, c2) in enumerate(zip(py_raw, js_raw)):
            if c1 != c2:
                print(f"| أول اختلاف   | الموضع {i} |")
                print(f"|   بايثون     | …{py_raw[max(0,i-45):i+45]}… |")
                print(f"|   JS         | …{js_raw[max(0,i-45):i+45]}… |")
                break
        else:
            print(f"| الطول        | بايثون={len(py_raw)} · JS={len(js_raw)} |")
    print("| السند الحاكم | ⬜ يُحدَّد قبل الحسم |")
    print("| القرار       | 🧊 **تجميد الطرفين** — لا أسبقية لبايثون (DEC-200) |")


def main():
    py_h, py_raw = build()
    js = json.loads(subprocess.run(
        ["node", os.path.join(HERE, "parity_js.js"),
         os.path.join(HERE, "parity_cases.json")],
        capture_output=True, text=True, check=True).stdout)
    js_h, js_raw = js["hashes"], js["raw"]

    frozen = load_frozen()
    diverged, frozen_hit = [], []
    for group in ("k2", "k3", "failure", "boundary"):
        for key in sorted(set(py_h[group]) | set(js_h[group])):
            a, b = py_h[group].get(key), js_h[group].get(key)
            if a == b:
                continue
            fk = f"{group}/{key}"
            if fk in frozen:
                frozen_hit.append((fk, frozen[fk]))
            else:
                diverged.append((group, key, a, b))

    total = sum(len(py_h[g]) for g in ("k2", "k3", "failure", "boundary"))
    print(f"{'المجموعة':<12}{'الحالات':<10}{'الحالة'}")
    print("-" * 78)
    for g in ("k2", "k3", "failure", "boundary"):
        bad = sum(1 for d in diverged if d[0] == g)
        print(f"{g:<12}{len(py_h[g]):<10}{'✅ متطابق' if not bad else f'❌ {bad} تباعد'}")
    print("-" * 78)

    if frozen_hit:
        print(f"\n🧊 نقاط مجمَّدة — {len(frozen_hit)} (مستبعَدة من البصمة · مُصرَّح بها · DEC-202):")
        for fk, meta in frozen_hit:
            print(f"   · {fk} — {meta.get('reason','بلا سبب مسجَّل')} "
                  f"[{meta.get('decision','بلا كود')}]")
        print("   ⚠️  تُراجَع عند كل إغلاق جلسة — لا تسقط بالتقادم.")

    for g, k, a, b in diverged:
        divergence_report(g, k, a, b,
                          py_raw.get(g, {}).get(k), js_raw.get(g, {}).get(k))

    if diverged:
        print(f"\n🧊 **الطرفان مجمَّدان** — {len(diverged)} تباعد غير مسجَّل. "
              f"لا إصدار قبل الحسم (DEC-200).")
        return 1

    tail = f" · {len(frozen_hit)} نقطة مجمَّدة" if frozen_hit else ""
    print(f"\n✅ تكافؤ تامّ — {total} حالة · صفر تباعد غير مسجَّل{tail}")
    print(f"   البصمة الشاملة: بايثون={py_h['GLOBAL']} · JS={js_h['GLOBAL']}")
    assert py_h["GLOBAL"] == js_h["GLOBAL"]
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
