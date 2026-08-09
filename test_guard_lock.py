# -*- coding: utf-8 -*-
"""
test_guard_lock.py — انحدار الحارس `ح-7` (`DEC-241`)
======================================================
سند: `GAP-LOCK-01` · `DEC-217/ب` · `DEC-229` · `ن-7`

`ح-7` يقيس **شيئاً واحداً**: أن الصياغة المعتمدة ما زالت تحكم كل ظهور
للمصطلح المحظور داخل حقل القفل.

الأقسام أربعة — شروط `ن-7` مطبَّقة على المقياس الواحد:
  أ  **العيب المعلوم**: الانقلاب الموصوف في `GAP-LOCK-01` نصّاً —
     «لا تشخيص» ← «تشخيص»  (`ن-7/①`)
  ب  **ثغرة الإلحاق**: ذِكرٌ ثانٍ خلف الصياغة المعتمدة
  ج  **الحالة القائمة**: صفر إنذار كاذب
  د  **تكافؤ النسخ** بايثون ↔ JS  (`ن-7/③`)
"""
import copy
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import k2_report as R2

TARGET = "K2-E-S-H"          # القفل الذي يحمل «تشخيص» تحت نفي صريح
TERM = "تشخيص"


def find_lock(code):
    for d, bands in R2.INTENSITY.items():
        for band, v in bands.items():
            if v.get("code") == code and v.get("lock"):
                return d, band, v["lock"]
    return None, None, None


NODE = r"""
const R = require("./reports.js");
const P = require("./packs.js").PACKS;
const [code, mode] = [process.argv[1], process.argv[2]];
let target = null;
for (const bands of Object.values(P.INTENSITY_K2.S))
  for (const v of Object.values(bands))
    if (v.code === code && v.lock) target = v;
const original = target.lock;
if (mode === "negation") target.lock = original.replace("، لا \"تشخيص\"", "، \"تشخيص\"");
if (mode === "append")   target.lock = original + " وهذا تشخيص فعلاً.";
const hits = R.scanLockDrift();
target.lock = original;
console.log(JSON.stringify(hits));
"""


def js(mode):
    r = subprocess.run(["node", "-e", NODE, TARGET, mode],
                       capture_output=True, text=True, cwd=HERE)
    if r.returncode != 0:
        raise RuntimeError((r.stderr or r.stdout)[:600])
    return json.loads(r.stdout)


def py(mode):
    d, band, original = find_lock(TARGET)
    if original is None:
        raise RuntimeError(f"لم يُعثر على القفل {TARGET}")
    try:
        if mode == "negation":
            R2.INTENSITY[d][band]["lock"] = original.replace('، لا "تشخيص"', '، "تشخيص"')
        elif mode == "append":
            R2.INTENSITY[d][band]["lock"] = original + " وهذا تشخيص فعلاً."
        return R2.scan_lock_drift()
    finally:
        R2.INTENSITY[d][band]["lock"] = original


def main():
    errs = []

    # ── ج — الحالة القائمة: صفر إنذار كاذب ────────────────────────────
    clean_py, clean_js = py("clean"), js("clean")
    n_reg = len(R2.LOCK_REGISTRY)
    if not clean_py and not clean_js:
        print(f"✅ ج الحالة القائمة — {n_reg} ذِكراً مسجَّلاً · صفر إنذار كاذب في الطرفين")
    else:
        errs.append(f"ج: بايثون={clean_py} · JS={clean_js}")
        print("❌ ج الحالة القائمة")

    # ── أ — العيب المعلوم: الانقلاب الموصوف في GAP-LOCK-01 ────────────
    neg_py, neg_js = py("negation"), js("negation")
    ok = (len(neg_py) == 1 and len(neg_js) == 1
          and neg_py[0]["check"] == "قفل-منجرف" == neg_js[0]["check"]
          and neg_py[0]["why"] == neg_js[0]["why"])
    if ok:
        print(f"✅ أ العيب المعلوم — «لا {TERM}» ← «{TERM}» أُوقف في الطرفين "
              f"· السبب: {neg_py[0]['why']}")
    else:
        errs.append(f"أ: بايثون={neg_py} · JS={neg_js}")
        print("❌ أ العيب المعلوم")

    # ── ب — ثغرة الإلحاق خلف الصياغة المعتمدة ─────────────────────────
    app_py, app_js = py("append"), js("append")
    ok = (len(app_py) == 1 and len(app_js) == 1
          and app_py[0]["why"] == app_js[0]["why"] == "ذِكرٌ خارج الصياغة المسجَّلة")
    if ok:
        print(f"✅ ب ثغرة الإلحاق — ذِكرٌ ثانٍ خلف السياق أُوقف في الطرفين")
    else:
        errs.append(f"ب: بايثون={app_py} · JS={app_js}")
        print("❌ ب ثغرة الإلحاق")

    # ── د — تكافؤ النسخ ───────────────────────────────────────────────
    same = all(json.dumps(a, ensure_ascii=False, sort_keys=True)
               == json.dumps(b, ensure_ascii=False, sort_keys=True)
               for a, b in [(clean_py, clean_js), (neg_py, neg_js), (app_py, app_js)])
    if same:
        print("✅ د تكافؤ النسخ — ثلاث حالات · المخرج متطابق حرفياً")
    else:
        errs.append("د: تباعد بين النسختين ⇒ يُجمَّد الطرفان (DEC-200)")
        print("❌ د تكافؤ النسخ")

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
