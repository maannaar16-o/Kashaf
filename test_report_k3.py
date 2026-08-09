# -*- coding: utf-8 -*-
"""
test_report_k3.py — اختبار انحدار **طبقة السحب النصّي** لـK3 (DEC-194/195/196)
==============================================================================
test_golden_k3.py يحرس طبقة الحساب؛ هذا الملف يحرس مطابقة العنوان للمضمون.
سند: الفحص 10 + ن-7 (DEC-193) · 79-K3-USERMAP §2 · 80-K3-TEXTS

شرط ن-7: الاختبار يجب أن يسقط على العيب المعلوم — بُرهن عليه بـDEF-K3-01.
"""
import json
import k3_report as R
import k3_guard as G
import k3_engine as E

SKILLS = ["EP", "IR", "BI", "CF", "ST"]
TAIL_SIG = "وهذه المهارة"


def _skill_heading_idx(lines):
    """مواضع العناوين المهارية — تُميَّز بوسم نطاق معتمد في متنها."""
    labels = set(R.BAND_LABEL.values())
    return [i for i, l in enumerate(lines)
            if l.startswith("### ") and "—" in l
            and l.split("—")[-1].strip() in labels]


def main():
    errs = []

    # 1) الحارس الشامل — الحزم والبنية والوسوم
    issues = G.validate(band_label_map=R.BAND_LABEL)
    if issues:
        errs += issues
    print("✅ الحارس الشامل: صفر شذوذ" if not issues else "❌ الحارس الشامل")

    # 2) DEC-196 — كل نطاق يخرجه band() له وسم معتمد صراحةً
    bl = getattr(R, "band_label", None)
    if bl is None:
        errs.append("DEC-196: band_label غير موجودة ⇒ وسم افتراضي صامت قائم")
    else:
        for b in ["limited", "core", "high", "OUT"]:
            try:
                bl(b)
            except Exception as e:
                errs.append(f"band_label({b}): {e}")
        try:
            bl("UNKNOWN")
            errs.append("band_label لم يوقف عند نطاق غير معتمد ⇒ وسم افتراضي صامت")
        except RuntimeError:
            pass
    print("✅ DEC-196: تغطية صريحة + إيقاف عند المجهول"
          if not errs else "❌ DEC-196")

    # 3) DEC-195/ج — الفصل البنيوي
    import k3_contentpack as cp
    if not hasattr(cp, "CIRCLE_SHARED"):
        print("❌ DEC-195/ج: الحزمة مدموجة — CIRCLE_SHARED غير موجودة")
        errs.append("DEC-195/ج: الحزمة غير مفصولة (DEF-K3-01 قائم)")
        print("-" * 76)
        print("النتيجة النهائية:", f"❌ {len(errs)} انحراف")
        for e in errs: print("   ·", e)
        return len(errs)
    if TAIL_SIG in cp.CIRCLE_SHARED:
        errs.append("المقطع المشترك يحمل خاتمة مهارية (§2.1 ملوَّث)")
    for s in SKILLS:
        if TAIL_SIG not in cp.CIRCLE_TAIL.get(s, ""):
            errs.append(f"خاتمة {s} لا تحمل توقيعها")
    print("✅ DEC-195/ج: المشترك نظيف · الخاتمات الخمس سليمة")

    # 4) المخرج المُصدَر — الفحص 10
    print("-" * 76)
    golden = json.load(open("golden_k3.json", encoding="utf-8"))
    cases = [k for k in golden if isinstance(golden[k], dict) and "sp" in golden[k]]
    for n in cases:
        txt = R.build_report(golden[n]["sp"])
        txt = txt[0] if isinstance(txt, tuple) else txt
        lines = txt.split("\n")
        idx = _skill_heading_idx(lines)
        case_errs = []

        # 4-أ) لا خاتمة مهارية قبل أول قسم مهاري (مرجع معلَّق)
        first = idx[0] if idx else len(lines)
        if any(TAIL_SIG in l for l in lines[:first]):
            case_errs.append("مرجع معلَّق قبل تقديم أي مهارة")

        # 4-ب) كل قسم مهاري يحمل خاتمته هو — مطابقة هوية لا تشابه نصّي
        import k3_contentpack as _cp
        bounds = idx + [len(lines)]
        for s, start, end in zip(SKILLS, idx, bounds[1:]):
            seg = "\n".join(lines[start:end])
            if _cp.CIRCLE_TAIL[s] not in seg:
                case_errs.append(f"قسم {s} لا يحمل خاتمته المعتمدة")
            for other in SKILLS:
                if other != s and _cp.CIRCLE_TAIL[other] in seg:
                    case_errs.append(f"قسم {s} يحمل خاتمة {other}")

        # 4-ج) وسم كل عنوان مطابق لـband(sp) الفعلي
        for s, start in zip(SKILLS, idx):
            shown = lines[start].split("—")[-1].strip()
            expected = R.BAND_LABEL[E.band(golden[n]["sp"][s])]
            if shown != expected:
                case_errs.append(f"{s}: وسم «{shown}» ≠ المحسوب «{expected}»")

        errs += [f"{n}: {e}" for e in case_errs]
        print(f"{n:<9} أقسام مهارية={len(idx)}  {'✅ سليم' if not case_errs else '❌ ' + case_errs[0]}")

    # 5) اتساق التسمية بين العنوان والخاتمة — تعارض مجمَّد TC-K3-02
    print("-" * 76)
    from k3_engine import USER_NAME
    import k3_contentpack as _cp
    txt0 = R.build_report(golden[cases[0]]["sp"])
    txt0 = txt0[0] if isinstance(txt0, tuple) else txt0
    dual = G.check_dual_name(txt0, USER_NAME, R._alt_name)
    errs += dual
    if dual:
        print("❌ TC-K3-02 — الاسم المزدوج غير مطبَّق:")
        for d in dual:
            print("     ", d)
    else:
        print("✅ TC-K3-02 مُغلق — العنوان يجمع الاسمين متى اختلفا (DEC-197/ج)")
        for s in SKILLS:
            a = R._alt_name(s)
            if a != USER_NAME[s]:
                print(f"     {s}: ### {USER_NAME[s]} ({a})")

    # 6) DEC-216/ب — سجلّ المصطلحات الوظيفية مثبَّت: أي انزياح يُرصد
    print("-" * 76)
    import os
    reg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "k3_functional_terms.json")
    reg = json.load(open(reg_path, encoding="utf-8"))["FUNCTIONAL_TERMS"]
    import k3_content as _KC, k3_contentpack as _cp
    src = {"TEMPLATES": _KC.TEMPLATES, "CONNECTIVES": _KC.CONNECTIVES,
           "ROOT_QUESTIONS": _KC.ROOT_QUESTIONS}
    drift = []
    for loc, terms in reg.items():
        grp, key = loc.split("/")
        txt = json.dumps(src[grp][key], ensure_ascii=False)
        found = [t for t in ["الاحتمال", "الملاحظة", "التهدئة", "المنع", "المراجعة"] if t in txt]
        if found != terms:
            drift.append(f"{loc}: {terms} → {found}")
    errs += drift
    print("✅ DEC-216/ب — المصطلحات الوظيفية الأربع مطابقة للسجلّ"
          if not drift else f"❌ انزياح: {drift}")

    print("-" * 76)
    print("النتيجة النهائية:", "✅ لا انحدار" if not errs else f"❌ {len(errs)} انحراف")
    for e in errs:
        print("   ·", e)
    return len(errs)


if __name__ == "__main__":
    raise SystemExit(1 if main() else 0)
