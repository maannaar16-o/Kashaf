# -*- coding: utf-8 -*-
"""
parity_reports.py — تكافؤ طبقة التقارير (المرحلة ③ · DEC-199/200)
==================================================================
يقارن **نصّ التقرير كاملاً** بين بايثون و JS على مجموعة الانحدار نفسها.

تطبيع النصّ وفق 87-PARITY §4:
  · توحيد \\n · حذف الفراغ الذيلي لكل سطر · حذف الأسطر الفارغة الطرفية

عند أي تباعد: يُصدر تقرير تباعد ويُجمَّد الطرفان (DEC-200) —
ما لم تكن النقطة مسجَّلة في parity_frozen.json بشروط DEC-202.
"""
import hashlib, json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import k2_report as R2
import k3_report as R3


def norm(text):
    lines = [ln.rstrip() for ln in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    while lines and not lines[0]:
        lines.pop(0)
    while lines and not lines[-1]:
        lines.pop()
    return "\n".join(lines)


def sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]


def k3_full_py(sp):
    """التقرير التساعي الكامل من بايثون."""
    txt = R3.build_report(sp)
    return txt[0] if isinstance(txt, tuple) else txt


def main():
    cases = json.load(open(os.path.join(HERE, "parity_cases.json"), encoding="utf-8"))
    py = {"k2": {}, "k3": {}}
    for name, sp in cases["k2"].items():
        for mode in ("full", "brief"):          # DEC-225/و — النطاقان
            txt, _ = R2.build_report(sp, mode=mode)
            py["k2"][f"{name}:{mode}"] = norm(txt)
    for name, sp in cases["k3"].items():
        py["k3"][name] = norm(k3_full_py(sp))

    js = json.loads(subprocess.run(
        ["node", os.path.join(HERE, "parity_reports_js.js")],
        capture_output=True, text=True, check=True).stdout)

    frozen = {}
    fp = os.path.join(HERE, "parity_frozen.json")
    if os.path.exists(fp):
        frozen = json.load(open(fp, encoding="utf-8"))

    diverged, frozen_hit, total = [], [], 0
    for grp in ("k2", "k3"):
        for name in sorted(py[grp]):
            total += 1
            a, b = py[grp][name], norm(js[grp].get(name, ""))
            if a == b:
                continue
            key = f"report:{grp}/{name}"
            (frozen_hit if key in frozen else diverged).append((grp, name, a, b))

    print(f"{'المجموعة':<12}{'الحالات':<10}{'الحالة'}")
    print("-" * 78)
    for grp in ("k2", "k3"):
        bad = sum(1 for d in diverged if d[0] == grp)
        print(f"{grp:<12}{len(py[grp]):<10}{'✅ متطابق' if not bad else f'❌ {bad} تباعد'}")
    print("-" * 78)

    for grp, name, a, b in diverged[:3]:
        print(f"\n{'='*78}\n🔴 تقرير تباعد — report:{grp}/{name}\n{'='*78}")
        pa, pb = a.split("\n"), b.split("\n")
        for i in range(max(len(pa), len(pb))):
            x = pa[i] if i < len(pa) else "«لا سطر»"
            y = pb[i] if i < len(pb) else "«لا سطر»"
            if x != y:
                print(f"| موقع التباعد | السطر {i+1} |")
                print(f"| بايثون | {x[:110]} |")
                print(f"| JS     | {y[:110]} |")
                break
        print("| السند الحاكم | ⬜ يُحدَّد قبل الحسم |")
        print("| القرار | 🧊 **تجميد الطرفين** — لا أسبقية لبايثون (DEC-200) |")

    if frozen_hit:
        print(f"\n🧊 نقاط مجمَّدة مسجَّلة: {len(frozen_hit)} (DEC-202)")

    if diverged:
        print(f"\n🧊 **الطرفان مجمَّدان** — {len(diverged)} تباعد غير مسجَّل (DEC-200).")
        return 1

    gh = sha("\n".join(py[g][n] for g in ("k2", "k3") for n in sorted(py[g])))
    print(f"\n✅ تكافؤ نصّي تامّ — {total} تقريراً · صفر تباعد")
    print(f"   بصمة المتن الكلي: {gh}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
