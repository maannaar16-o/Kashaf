# -*- coding: utf-8 -*-
"""
test_report_k2.py — اختبار انحدار **طبقة السحب النصّي** (DEC-191)
=================================================================
الطبقة التي لم تكن محروسة، فمرّ خلالها DEF-K2-01 على أربعة تقارير.
test_golden_k2.py يحرس طبقة الحساب؛ هذا الملف يحرس مطابقة العنوان للمضمون.

سند: الفحص 10 + ن-7 (DEC-193) · 51-MATRIX-06 §3.1/R3
"""
import json
import k2_report as R

LENSES = ["A", "R", "C", "O", "S", "E", "St", "H"]

# الوظيفة ← العنوان الذي تُعرض تحته (ربط صريح لا ضمني)
EXPECTED_CENTER = ["دورة المعالجة", "المحرك", "الموقع في الفريق"]
EXPECTED_FOOTPRINT = "البصمة"


def _entries_under(text, heading_kw):
    """يعيد عناوين المداخل (**عنوان:**) الواقعة تحت قسم بعينه."""
    lines, out, inside = text.split("\n"), [], False
    for l in lines:
        if l.startswith("## "):
            inside = heading_kw in l
        elif inside and l.startswith("- **") and ":**" in l:
            out.append(l.split("**")[1].rstrip(":"))
    return out


def _synthetic_sp(center):
    sp = {d: 30.0 for d in LENSES}
    sp[center] = 90.0
    return sp


def main():
    errs = []

    # 1) حارس الفتحات — لا شذوذ في الحزمة
    anomalies = R.validate_slots()
    if anomalies:
        errs += [f"حارس الفتحات: {a}" for a in anomalies]
    print("✅ حارس الفتحات: صفر شذوذ" if not anomalies else "❌ حارس الفتحات")

    # 2) الأبعاد الثمانية مركزاً — العنوان يحمل مضمونه
    print("-" * 76)
    print(f"{'المركز':<8}{'مركزك':<44}{'بصمتك':<14}")
    for c in LENSES:
        txt, _ = R.build_report(_synthetic_sp(c))
        ctr = _entries_under(txt, "مركزك")[:3]
        fp = _entries_under(txt, "بصمتك")
        fp0 = fp[0] if fp else "—"
        ok = ctr == EXPECTED_CENTER and fp0 == EXPECTED_FOOTPRINT
        if not ok:
            errs.append(f"{c}: مركزك={ctr} · بصمتك={fp0}")
        print(f"{c:<8}{' · '.join(ctr):<44}{fp0:<14}{'✅' if ok else '❌'}")

    # 3) الحالات الحقيقية من golden_k2
    print("-" * 76)
    golden = json.load(open("golden_k2.json", encoding="utf-8"))
    for n, d in golden.items():
        if "sp" not in d:
            continue
        txt, a = R.build_report(d["sp"])
        fp = _entries_under(txt, "بصمتك")
        ok = bool(fp) and fp[0] == EXPECTED_FOOTPRINT
        if not ok:
            errs.append(f"{n}: بصمتك={fp}")
        print(f"{n:<8} مركز={a['center']:<4} بصمتك={fp[0] if fp else '—':<12}{'✅' if ok else '❌'}")

    # 4) لا تكرار مدخل بين قسمَي المركز والبصمة
    print("-" * 76)
    dup = []
    for c in LENSES:
        txt, _ = R.build_report(_synthetic_sp(c))
        overlap = set(_entries_under(txt, "مركزك")) & set(_entries_under(txt, "بصمتك"))
        if overlap:
            dup.append((c, overlap))
    if dup:
        errs += [f"ازدواج مدخل في {c}: {o}" for c, o in dup]
    print("✅ لا ازدواج مداخل بين الأقسام" if not dup else f"❌ ازدواج: {dup}")

    # 5) DEF-K2-03 — لا مدخل يتكرر في التقرير الواحد
    print("-" * 76)
    import collections
    dupcases = []
    for name, sp in list(golden.items()) + [("CENTER-AS-SUPPORT",
            {"H": 62.0, "R": 60.0, "A": 58.0, "E": 56.0, "S": 54.0,
             "O": 48.0, "St": 46.0, "C": 44.0})]:
        sp = sp["sp"] if isinstance(sp, dict) and "sp" in sp else sp
        if not isinstance(sp, dict) or len(sp) != 8:
            continue
        txt, _ = R.build_report(sp)
        cnt = collections.Counter(l for l in txt.split("\n") if l.startswith("- **"))
        d = [k for k, v in cnt.items() if v > 1]
        if d:
            dupcases.append((name, len(d)))
    errs += [f"{n}: {k} مدخلاً مكرَّراً" for n, k in dupcases]
    print("✅ لا تكرار مداخل داخل التقرير (DEF-K2-03)" if not dupcases
          else f"❌ تكرار: {dupcases}")

    print("-" * 76)
    print("النتيجة النهائية:", "✅ لا انحدار" if not errs else f"❌ {len(errs)} انحراف")
    for e in errs:
        print("   ·", e)
    return len(errs)


if __name__ == "__main__":
    raise SystemExit(1 if main() else 0)
