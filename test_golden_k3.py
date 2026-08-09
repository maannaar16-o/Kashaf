# -*- coding: utf-8 -*-
"""
test_golden_k3.py — اختبار الانحدار على حزمة 75-GOLDEN-K3
==========================================================
DEC-137/2: التوقعات تُقرأ من golden_k3.json (بصمات نصّية) — لا تُكتب يدوياً.
أي اختلاف = انحدار يوقف النشر حتى يُفسَّر.
"""
import json, hashlib
from k3_engine import run, band, compute_ss_sp, octal_code, InputContractError

GOLDEN = json.load(open("golden_k3.json", encoding="utf-8"))
GLOBAL_FORBIDDEN = ["CPL-", "HF-", "SP =", "ولذلك", "مما يعني", "وبالتالي",
                    "اضطراب", "علاج", "تشخيص", "أقوى من", "تحمل عبء"]


def check(name, res, exp):
    a, errs = res.audit, []
    if a["cells_activated"] != exp["cells"]:
        errs.append("الخلايا اختلفت")
    if [p["code"] for p in a["patterns_recognized"]] != exp["patterns"]:
        errs.append("الأنماط اختلفت")
    if a["root_question"]["code"] != exp["question"]:
        errs.append(f"السؤال {a['root_question']['code']} ≠ {exp['question']}")
    if a["containment_state"] != exp["state"]:
        errs.append("حالة الاحتواء اختلفت")
    if a["entries_used"] != exp["entries"]:
        errs.append("المداخل المستعملة اختلفت")
    if a["g5_violations"]:
        errs.append(f"G5: {a['g5_violations']}")
    txt = res.section6 + "\n" + res.section7
    sha = hashlib.sha256(txt.encode()).hexdigest()[:16]
    if sha != exp["text_sha256"]:
        errs.append(f"🔴 بصمة النص {sha} ≠ {exp['text_sha256']}")
    for bad in GLOBAL_FORBIDDEN:
        if bad in txt:
            errs.append(f"لفظ محظور: {bad}")
    if name == "SYN-03" and res.section6.count("يعملان معاً بانسجام") != 1:
        errs.append("T-01 تكرر — انحدار س-3")
    if name == "SYN-06" and res.section6.strip():
        errs.append("ظهر القسم ٦ في حالة الصمت المشروع")
    return errs


def main():
    print(f"{'الحالة':<9} {'خلايا':>5} {'الأنماط':<20} {'سؤال':<7} {'الحالة':<10} بصمة      النتيجة")
    print("-" * 84)
    total = 0
    for name, exp in GOLDEN.items():
        res = run(exp["sp"]); errs = check(name, res, exp); total += len(errs)
        a = res.audit
        pats = ",".join(p["code"] for p in a["patterns_recognized"]) or "—"
        print(f"{name:<9} {len(a['cells_activated']):>5} {pats:<20} "
              f"{str(a['root_question']['code'] or '—'):<7} "
              f"{str(a['containment_state'] or '—'):<10} {exp['text_sha256'][:8]}  "
              f"{'✅' if not errs else '❌ ' + ' | '.join(errs)}")
        if a["template_gaps"]:
            print(f"          ⚠️ فجوات قوالب: {set(a['template_gaps'])}")

    print("-" * 84)
    ss, sp_ = compute_ss_sp(x=44, y=8, z=3)
    print(f"عقد المدخل: x=44,y=8,z=3 → SS={ss} SP={sp_:.1f}% code={octal_code(sp_)}")
    try:
        compute_ss_sp(x=40, y=5, z=5); print("❌ لم يُرفع خطأ عند y+z≠11"); total += 1
    except InputContractError:
        print("✅ عقد المدخل يوقف عند y+z≠11")
    print("✅ حدّ 50.0 →", band(50.0), "| 49.9 →", band(49.9), "| 70.0 →", band(70.0))

    # G5 المرحلة الأولى — على حزمة المحتوى الخارجية
    from k3_content import ContentPack
    bad = ContentPack(external={"out_text": "هذا اضطراب يحتاج علاجاً، ولذلك ننصح…"})
    v = run(GOLDEN["SYN-01"]["sp"], content=bad).audit["g5_violations"]
    stages = {h["stage"] for h in v}
    print("✅ G5 المرحلة الأولى ترصد المحتوى:", len(v), "مخالفة", stages if v else "")
    if not v: total += 1

    print("-" * 84)
    print("النتيجة النهائية:", "✅ لا انحدار" if total == 0 else f"❌ {total} انحراف")
    return total


if __name__ == "__main__":
    raise SystemExit(1 if main() else 0)
