# -*- coding: utf-8 -*-
"""
test_guard_sp.py — انحدار الحارس `ح-4` (منع `SP%` في أي مخرج)
================================================================
سند: `DEC-183` · `ن-7` (`DEC-193`/`198`/`199`/`200`/`224`)

`ح-4` يقيس **شيئاً واحداً**: حضور الرمز `SP%` في نصّ قابل للعرض.
الأقسام الأربعة أدناه ليست أربعة مقاييس، بل **شروط `ن-7` الأربعة**
لقبول الحارس، مطبَّقة على المقياس الواحد:

  أ  يُختبَر على عيب معلوم قبل اعتماده        (`ن-7/①` · `DEC-194`)
  ب  القياس على المصادر والمخرجات الفعلية      (المقياس نفسه)
  ج  تكافؤ النسخ بايثون ↔ JS                  (`ن-7/③` · `DEC-199`)
  د  يوقف الإصدار فعلاً — لا يرصد صامتاً        (`ن-7` · صفر هلوسة/10)
"""
import json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import sp_gate
from sp_gate import sp_gate as gate, scan, scan_pct, SPLeakError, PctLeakError
import k2_report as R2
import k3_report as R3

# ── العيب المعلوم: مقاطع واقعية مستخرَجة من `Kashaf_v2.html` ──────────────
# السطح الميت `ReportView`/`handleExport` — أُبقي بأمر المالك (خيار «ب»)
KNOWN_DEFECT = [
    'React.createElement("th", { style: th }, "SP%")',
    'دائرة الانفعال K3 (SP%)',
    'دائرة الإنجاز K4 (SP%)',
    '| البُعد | SP% | الرمز | الفئة | الاشتعال |',
    '["الدائرة","الكود","الاسم","SP%/الدرجة","الرمز","الفئة"]',
    '<th>البُعد</th><th>SP%</th><th>الرمز</th>',
]
# نصوص مشروعة يجب ألّا يسقط عليها الحارس
BENIGN = [
    '> 🔒 هذه أول كتلة "مشتعلة" (فوق 50%) — عدسة مساندة نشطة.',   # كتلة الشدة R1
    '{"sp": [33,7,0], "engine_version": "1.2"}',                    # حقل audit العددي
    '| التحليلي (A) | H+ | 🎯 المركز |',                            # لوحة DEC-187
]
# العيب المعلوم لـ`ح-5`: قوالب السطح الميت في `Kashaf_v2.html` تُصيّر نسبة
# المفحوص نفسها — `${d.sp}%` · `${k.sp}%` · `${avg}%` · `${k.name}=${k.sp}%`
# وهي **بلا الحرفين `SP`** فتنفذ من `ح-4` كاملةً.
KNOWN_DEFECT_PCT = [
    '["K2","A","التحليلي","73.5%","H+","مهيمنة"]',
    '["K3","","مهارة قوة الملاحظة","61%","",""]',
    '**K3:** مهارة المرونة=48.5% · مهارة تحمل الضغوط=52%',
    'التحليلي: 73.5%',
]
# نصوص مشروعة يجب أن تمرّ `ح-5` بفضل السجلّ لا بالحدس
BENIGN_PCT = [
    '> 🔒 هذه أول كتلة "مشتعلة" (فوق 50%) — عدسة مساندة نشطة، لا ثانوية ولا ناقصة. `P = C + G`.',
    "تشغيلك اليومي داخل التزام آمن؛ تختبر البديل في بيئة معزولة ثم يُحوَّل سابقةً معتمدة — كفاءة فورية والتزام 100%",
    '{"sp": {"A": 73.5}, "engine_version": "1.2"}',
]

PACK_FILES = ["k2_userlayer_pack.json", "k2_contentpack.json", "skill_sections.json",
              "three_texts.json", "circle_map_v2.json", "k3_banner.json",
              "k3_textlayer.json", "k3_g5.json", "k2_pur.json", "k2_intensity.json",
              "k2_lookalike.json", "k2_lock_registry.json"]


def pack_strings(path):
    """يعيد كل قيمة نصّية داخل حزمة — بعد التحليل، لا بايتات الملف.
    المهرَّب في الملف (`\\"`) ليس ما يصل المستفيد؛ الحارس يقيس النصّ المعروض."""
    def walk(o):
        if isinstance(o, dict):
            for v in o.values():
                yield from walk(v)
        elif isinstance(o, list):
            for v in o:
                yield from walk(v)
        elif isinstance(o, str):
            yield o
    return "\n".join(walk(json.load(open(path, encoding="utf-8"))))


def main():
    errs = []

    # ── ح-4/أ — يسقط على عيب معلوم (ن-7/①) ────────────────────────────
    caught = sum(1 for d in KNOWN_DEFECT if scan(d))
    false_alarm = [b for b in BENIGN if scan(b)]
    if caught == len(KNOWN_DEFECT) and not false_alarm:
        print(f"✅ ح-4/أ عيب معلوم — {caught}/{len(KNOWN_DEFECT)} أُوقفت · صفر إنذار كاذب")
    else:
        errs.append(f"ح-4/أ: أُوقفت {caught}/{len(KNOWN_DEFECT)} · إنذار كاذب {len(false_alarm)}")
        print("❌ ح-4/أ عيب معلوم")

    # ── ح-4/ب — صفر SP% في المصادر والمخرجات الفعلية ──────────────────
    cases = json.load(open(os.path.join(HERE, "parity_cases.json"), encoding="utf-8"))
    n_out, out_hits = 0, []
    for name, sp in cases["k2"].items():
        for mode in ("full", "brief"):
            txt = R2.build_report(sp, mode=mode)[0]
            n_out += 1
            if scan(txt):
                out_hits.append(f"k2:{name}:{mode}")
    for name, sp in cases["k3"].items():
        txt = R3.build_report(sp)[0]
        n_out += 1
        if scan(txt):
            out_hits.append(f"k3:{name}")

    n_pack, pack_hits = 0, []
    for fn in PACK_FILES:
        path = os.path.join(HERE, fn)
        if not os.path.exists(path):
            errs.append(f"ح-4/ب: حزمة مفقودة {fn} — لا يُفترض نظافتها")
            continue
        n_pack += 1
        if scan(pack_strings(path)):
            pack_hits.append(fn)

    if not out_hits and not pack_hits:
        print(f"✅ ح-4/ب قياس فعلي — {n_out} مخرجاً · {n_pack} حزمة · صفر `SP%`")
    else:
        errs.append(f"ح-4/ب: مخرجات {out_hits} · حزم {pack_hits}")
        print("❌ ح-4/ب قياس فعلي")

    # ── ح-5/أ — عيب معلوم: نسبة المفحوص تنفذ من ح-4 ──────────────────
    evades_h4 = sum(1 for d in KNOWN_DEFECT_PCT if not scan(d))
    caught5 = sum(1 for d in KNOWN_DEFECT_PCT if scan_pct(d))
    false5 = [b for b in BENIGN_PCT if scan_pct(b)]
    if evades_h4 == len(KNOWN_DEFECT_PCT) and caught5 == len(KNOWN_DEFECT_PCT) and not false5:
        print(f"✅ ح-5/أ عيب معلوم — {caught5}/{len(KNOWN_DEFECT_PCT)} أُوقفت "
              f"(وكلها تنفذ من ح-4) · صفر إنذار كاذب")
    else:
        errs.append(f"ح-5/أ: نفذت من ح-4 {evades_h4} · أوقفها ح-5 {caught5} · كاذب {len(false5)}")
        print("❌ ح-5/أ عيب معلوم")

    # ── ح-5/ب — صفر نسبة غير مسجَّلة في المخرجات والحزم ────────────────
    pct_out, pct_pack = [], []
    for name, sp in cases["k2"].items():
        for mode in ("full", "brief"):
            if scan_pct(R2.build_report(sp, mode=mode)[0]):
                pct_out.append(f"k2:{name}:{mode}")
    for name, sp in cases["k3"].items():
        if scan_pct(R3.build_report(sp)[0]):
            pct_out.append(f"k3:{name}")
    for fn in PACK_FILES:
        path = os.path.join(HERE, fn)
        if os.path.exists(path) and scan_pct(pack_strings(path)):
            pct_pack.append(fn)
    if not pct_out and not pct_pack:
        print(f"✅ ح-5/ب قياس فعلي — {n_out} مخرجاً · {n_pack} حزمة · صفر نسبة غير مسجَّلة")
    else:
        errs.append(f"ح-5/ب: مخرجات {pct_out} · حزم {pct_pack}")
        print("❌ ح-5/ب قياس فعلي")

    # ── ح-4/ج — تكافؤ النسخ (ن-7/③ · DEC-199) ─────────────────────────
    probe = KNOWN_DEFECT + BENIGN + KNOWN_DEFECT_PCT + BENIGN_PCT
    r = subprocess.run(
        ["node", "-e",
         'const G=require("./sp_gate.js");'
         'const a=JSON.parse(process.argv[1]);'
         'console.log(JSON.stringify(a.map(t=>[G.scan(t).length,G.scanPct(t).length])));',
         json.dumps(probe, ensure_ascii=False)],
        capture_output=True, text=True, cwd=HERE)
    py_counts = [[len(scan(t)), len(scan_pct(t))] for t in probe]
    if r.returncode == 0 and json.loads(r.stdout) == py_counts:
        print(f"✅ ح-4+ح-5/ج تكافؤ النسخ — {len(probe)} عيّنة متطابقة بايثون↔JS")
    else:
        js = r.stdout.strip() or r.stderr.strip()[:120]
        errs.append(f"ح-4/ج: بايثون={py_counts} · JS={js} ⇒ يُجمَّد الطرفان (DEC-200)")
        print("❌ ح-4/ج تكافؤ النسخ")

    # ── ح-4/د — يوقف الإصدار فعلاً، لا يرصد صامتاً ─────────────────────
    # نبدّل النمط مؤقتاً برمزٍ حاضرٍ يقيناً في المخرج، فإن لم يتوقف
    # الإصدار فالحارس **غير موصول** عند نقطة الإصدار.
    sp_any = next(iter(cases["k2"].values()))
    original = sp_gate.SP_TOKEN
    halted_k2 = halted_k3 = False
    try:
        sp_gate.SP_TOKEN = re.compile(r"المركز")
        try:
            R2.build_report(sp_any, mode="full")
        except SPLeakError:
            halted_k2 = True
        sp_gate.SP_TOKEN = re.compile(r"مهارة")
        try:
            R3.build_report(next(iter(cases["k3"].values())))
        except SPLeakError:
            halted_k3 = True
    finally:
        sp_gate.SP_TOKEN = original

    if halted_k2 and halted_k3:
        print("✅ ح-4/د توصيل الحارس — الإصدار يتوقف في K2 وK3 عند الشذوذ")
    else:
        errs.append(f"ح-4/د: توقف K2={halted_k2} · K3={halted_k3} — الحارس غير موصول")
        print("❌ ح-4/د توصيل الحارس")

    print("-" * 76)
    if errs:
        print("النتيجة النهائية: ❌ انحدار")
        for e in errs:
            print("   ·", e)
        return 1
    print("النتيجة النهائية: ✅ لا انحدار")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
