# -*- coding: utf-8 -*-
"""
test_golden_k2.py — اختبار الانحدار على حزمة golden_k2
========================================================
التوقعات تُقرأ من golden_k2.json (مجمّدة من المحرك على حالتين حقيقيتين).
أي اختلاف = انحدار يوقف النشر حتى يُفسَّر.

يحرس: طبقة الحساب (raw→sp · مُثبَتة 8/8) · التصنيف · استدعاء المعاجم ·
       ت-8 (الفرعان) · ت-7 · خيط FRIC-02 · عقد المدخل · حدود التصنيف · العزل.
"""
import json
from k2_engine import (run, score_from_raw, compute_ss_sp, octal_code,
                       comp_state, InputContractError, LENSES)

GOLDEN = json.load(open("golden_k2.json", encoding="utf-8"))


class _StubContent:
    """حزمة محتوى وهمية لاختبار تدقيق العزل (المرحلة الأولى)."""
    def __init__(self, texts): self._t = texts
    def texts_for(self, profile): return self._t


def check(name, exp):
    errs = []
    raw = exp["raw"]

    # 1) طبقة الحساب: raw → sp تُعيد إنتاج الملف (يُتخطّى إن غاب الخام)
    if raw:
        raw = {int(k): v for k, v in raw.items()}
        scored = score_from_raw(raw)
        sp = {d: v["sp"] for d, v in scored.items()}
        if sp != exp["sp"]:
            errs.append(f"🔴 raw→sp اختلف: {sp} ≠ {exp['sp']}")

    r = run(sp=exp["sp"])

    # 2) التصنيف
    if r.profile.center != exp["center"]:
        errs.append(f"المركز {r.profile.center} ≠ {exp['center']}")
    for f in ("dominant", "support", "off", "ignited"):
        if getattr(r.profile, f) != exp[f]:
            errs.append(f"{f} اختلف")

    # 3) استدعاء المعاجم (كود/نوع/حالة/طبقة)
    lines = [[ln.code, ln.kind, ln.state, ln.layer] for ln in r.lines]
    if lines != exp["lines"]:
        errs.append("أسطر الاستدعاء اختلفت")

    # 4) ت-8 (النصف/الحكم/حالات الحلفاء)
    t8 = [[h["half"], h["verdict"], h["states"]] for h in r.t8]
    if t8 != exp["t8"]:
        errs.append(f"ت-8 اختلف: {[(h[0],h[1]) for h in t8]}")

    # 5) ت-7 + خيط FRIC-02
    if sorted(r.delivery_questions) != exp["delivery"]:
        errs.append(f"أسئلة التسليم اختلفت: {sorted(r.delivery_questions)}")
    if r.stitch != exp["stitch"]:
        errs.append(f"خيط FRIC-02 اختلف: {r.stitch!r}")

    # 6) العزل نظيف
    if (r.audit == []) != exp["audit_clean"]:
        errs.append(f"تدقيق العزل: {r.audit}")

    return r, errs


def main():
    print(f"{'الحالة':<8} {'مركز':<5} {'ت-8':<28} {'تسليم':<20} النتيجة")
    print("-" * 84)
    total = 0
    for name, exp in GOLDEN.items():
        r, errs = check(name, exp)
        total += len(errs)
        t8s = " · ".join(f"{h['half'][:6]}:{h['verdict']}" for h in r.t8)
        dq = ",".join(sorted(r.delivery_questions))
        print(f"{name:<8} {r.profile.center:<5} {t8s:<28} {dq:<20} "
              f"{'✅' if not errs else '❌ ' + ' | '.join(errs)}")

    print("-" * 84)
    # عقد المدخل — يوقف عند y+z≠7
    ss, sp_ = compute_ss_sp(x=33, y=7, z=0)
    print(f"عقد المدخل: x=33,y=7,z=0 → SS={ss} SP={sp_:.1f}% code={octal_code(sp_)}")
    try:
        compute_ss_sp(x=30, y=4, z=4); print("❌ لم يُرفع خطأ عند y+z≠7"); total += 1
    except InputContractError:
        print("✅ عقد المدخل يوقف عند y+z≠7")

    # حدود التصنيف (spec 41 §5)
    checks = [(-1,"OUT"),(20,"L-"),(20.1,"L"),(40,"L"),(50,"M"),(50.1,"M+"),
              (70,"M+"),(70.1,"H"),(85,"H"),(100,"H+"),(100.1,"H++")]
    bad = [(sp,octal_code(sp),c) for sp,c in checks if octal_code(sp)!=c]
    print("✅ حدود octal_code سليمة" if not bad else f"❌ حدود: {bad}")
    total += len(bad)

    # حالة التركيب D/M/L
    cs = [(50,"L"),(50.1,"M"),(70,"M"),(70.1,"D")]
    badc = [(sp,comp_state(sp),c) for sp,c in cs if comp_state(sp)!=c]
    print("✅ حدود comp_state سليمة" if not badc else f"❌ comp_state: {badc}")
    total += len(badc)

    # عقد الأبعاد — يجب أن تكون الثمانية
    try:
        run(sp={"A":80}); print("❌ لم يُرفع خطأ عند أبعاد ناقصة"); total += 1
    except InputContractError:
        print("✅ عقد الأبعاد يوقف عند غير الثمانية")

    # تدقيق العزل — يرصد المحتوى المحظور
    stub = _StubContent(["نص فيه اضطراب وعلاج وتنفيذ ميداني"])
    v = run(sp=GOLDEN["P-005"]["sp"], content=stub).audit
    print("✅ تدقيق العزل يرصد المحتوى:", len(v), "لفظ" if v else "")
    if not v: total += 1

    print("-" * 84)
    print("النتيجة النهائية:", "✅ لا انحدار" if total == 0 else f"❌ {total} انحراف")
    return total


if __name__ == "__main__":
    raise SystemExit(1 if main() else 0)
