# -*- coding: utf-8 -*-
"""
verify_regen.py — برهان عقد إعادة التوليد (DEC-220)
====================================================
يثبت أن حقل `audit` **كافٍ لإعادة توليد التقرير حرفياً**:

  ① يُقرأ `sp` من الـaudit وحده — لا من المُدخل الأصلي
  ② يُعاد التوليد
  ③ تُقارَن بصمة المخرج ببصمة `report_sha256` المسجَّلة
  ④ تُقارَن بصمات الحزم — فتغيّر أي حزمة يُرصد لا يمرّ

سند: DEC-220 · 87-PARITY §4 (التطبيع) · ن-7 (يوقف ولا يخمّن)
"""
import hashlib, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import k2_report as R2
import k3_report as R3
import k4_report as R4


def norm(t):
    lines = [l.rstrip() for l in t.replace("\r\n", "\n").split("\n")]
    while lines and not lines[0]:
        lines.pop(0)
    while lines and not lines[-1]:
        lines.pop()
    return "\n".join(lines)


def regen(circle, audit):
    """إعادة التوليد من الـaudit وحده — لا يُمرَّر شيء من المُدخل الأصلي."""
    sp = dict(audit["sp"])
    if circle == "k2":
        return R2.build_report(sp)
    if circle == "k4":
        return R4.build_report(sp)
    return R3.build_report(sp)


def main():
    cases = json.load(open(os.path.join(HERE, "parity_cases.json"), encoding="utf-8"))
    # $K_4$ لها مجموعتها المختومة — والعقد واحد للدوائر الثلاث (`DEC-271`)
    cases["k4"] = json.load(open(os.path.join(HERE, "parity_cases_k4.json"),
                                 encoding="utf-8"))["k4"]
    errs, n = [], 0

    for circle, builder in (("k2", R2.build_report), ("k3", R3.build_report),
                            ("k4", R4.build_report)):
        ok = 0
        for name, sp in cases[circle].items():
            n += 1
            txt, audit = builder(sp)

            # ① البصمة المسجَّلة تطابق المخرج فعلاً
            live = hashlib.sha256(txt.encode("utf-8")).hexdigest()[:16]
            if live != audit["report_sha256"]:
                errs.append(f"{circle}/{name}: البصمة المسجَّلة لا تصف المخرج")
                continue

            # ② إعادة التوليد من الـaudit وحده
            txt2, audit2 = regen(circle, audit)
            if norm(txt) != norm(txt2):
                errs.append(f"{circle}/{name}: المخرج المُعاد يخالف الأصل")
                continue

            # ③ بصمة المُعاد تطابق المسجَّلة
            if audit2["report_sha256"] != audit["report_sha256"]:
                errs.append(f"{circle}/{name}: بصمة المُعاد ≠ المسجَّلة")
                continue

            # ④ بصمات الحزم ثابتة بين التوليدين
            if audit2["pack_sha"] != audit["pack_sha"]:
                errs.append(f"{circle}/{name}: بصمات الحزم تغيّرت بين التوليدين")
                continue
            ok += 1
        print(f"{circle:<5} {ok}/{len(cases[circle])} أُعيد توليدها من الـaudit وحده"
              + ("  ✅" if ok == len(cases[circle]) else "  ❌"))

    # ⑤ اكتمال العقد — الحقول الملزِمة حاضرة
    print("-" * 70)
    REQUIRED = ["sp", "engine_version", "spec_version", "instrument_pin",
                "entries_used", "pack_sha", "report_sha256"]
    # عقد $K_4$ مختوم في `136 §3/④` — و`entries_used` ليست فيه: يعلن `codes`
    # و`sections_rendered` بدلاً منها. تُقرأ القائمة من المشرف: مصدرُ حقيقةٍ واحد.
    import supervisor as _SV
    for circle, builder, sample in (("k2", R2.build_report, list(cases["k2"].values())[0]),
                                    ("k3", R3.build_report, list(cases["k3"].values())[0]),
                                    ("k4", R4.build_report, list(cases["k4"].values())[0])):
        _, a = builder(sample)
        req = _SV.REQUIRED_AUDIT_K4 if circle == "k4" else REQUIRED
        missing = [k for k in req if k not in a]
        if missing:
            errs.append(f"{circle}: حقول ناقصة {missing}")
        print(f"{circle:<5} عقد الحقول: " + ("✅ مكتمل" if not missing else f"❌ ناقص {missing}"))

    # ⑥ برهان الحساسية — تغيّر حزمة يجب أن يُرصد
    print("-" * 70)
    _, a = R2.build_report(list(cases["k2"].values())[0])
    bak = R2.INTENSITY["A"]["M"]["user"]
    R2.INTENSITY["A"]["M"]["user"] = bak + " ."
    _, a2 = R2.build_report(list(cases["k2"].values())[0])
    R2.INTENSITY["A"]["M"]["user"] = bak
    sensitive = (a2["pack_sha"]["INTENSITY_K2"] != a["pack_sha"]["INTENSITY_K2"])
    if not sensitive:
        errs.append("بصمة الحزمة لا تتأثر بتغيّر محتواها")
    print("حساسية بصمة الحزمة لتغيّر حرف واحد: " + ("✅" if sensitive else "❌"))

    print("-" * 70)
    print(f"النتيجة النهائية: " + ("✅ العقد مُستوفى — %d حالة" % n if not errs
                                   else f"❌ {len(errs)} انحراف"))
    for e in errs[:5]:
        print("   ·", e)
    return len(errs)


if __name__ == "__main__":
    raise SystemExit(1 if main() else 0)
