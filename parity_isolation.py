# -*- coding: utf-8 -*-
"""
parity_isolation.py — تكافؤ **تدقيق العزل** بين النسختين
==========================================================
سند: `DEC-236` (إحياء المسار في JS) · `DEC-199` (تكافؤ النسخ) · `GAP-ISO-JS-01`

الفراغ الذي يسدّه: `parity_py` يقارن منطق المحرّك، و`parity_reports`
يقارن نصّ التقرير — و**كتلة التدقيق نفسها** لم تكن مقارَنة قط. فبقي
حقل `isolation` غير محروس، وهو ما سمح لـ`auditIsolation([])` أن تعيش
مثبَّتة على فارغ دون أن يسقط شيء.

ثلاثة أقسام، كلٌّ يقيس شيئاً واحداً (`ن-7/②`):

  أ  نصوص المصدر المُغذّاة متطابقة  — `texts_for` ↔ `textsFor`
  ب  حقل `isolation` متطابق على كل الحالات
  ج  **عيب معلوم**: تلوّث مُصطنَع يُرصد في الطرفين بالنتيجة نفسها
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import k2_content as C2
import k2_engine as E2
import k2_report as R2

CASES = json.load(open(os.path.join(HERE, "parity_cases.json"), encoding="utf-8"))["k2"]

NODE_TEXTS = r"""
const R = require("./reports.js");
const E = require("./engines.js");
const cases = JSON.parse(process.argv[1]);
console.log(JSON.stringify(cases.map(sp => {
  const prof = E.K2.classify(sp);
  return R.K2_CONTENT_ADAPTER.textsFor(prof);
})));
"""

NODE_ISO = r"""
const R = require("./reports.js");
const cases = JSON.parse(process.argv[1]);
console.log(JSON.stringify(cases.map(sp => R.buildReportK2(sp, "full")[1].isolation)));
"""

# ── العيب المعلوم: نصّ ملوَّث بألفاظ محظورة من ثلاثة أقفال مختلفة ──
DIRTY = "هذا النص فيه اضطراب وعلاج وتنفيذ ميداني وK3 وشدة الانفعال."

NODE_DIRTY = r"""
const E = require("./engines.js");
const dirty = process.argv[1];
const stub = { textsFor() { return [dirty]; } };
const sp = JSON.parse(process.argv[2]);
const res = E.K2.run({ sp, content: stub });
let threw = null;
try { E.K2.run({ sp, content: stub, strict: true }); }
catch (e) { threw = [e.name || "Error", String(e.message)]; }
console.log(JSON.stringify([res.audit, threw]));
"""


class _Stub:
    def __init__(self, texts):
        self._t = texts

    def texts_for(self, profile):
        return self._t


def node(script, *args):
    r = subprocess.run(["node", "-e", script, *args],
                       capture_output=True, text=True, cwd=HERE)
    if r.returncode != 0:
        raise RuntimeError((r.stderr or r.stdout)[:800])
    return json.loads(r.stdout)


def main():
    names = list(CASES)
    sps = [CASES[n] for n in names]
    errs = []

    # ── أ — نصوص المصدر المُغذّاة ──────────────────────────────────────
    pack = C2.ContentPack()
    py_texts = [pack.texts_for(E2.classify(sp)) for sp in sps]
    js_texts = node(NODE_TEXTS, json.dumps(sps, ensure_ascii=False))
    bad = [n for n, a, b in zip(names, py_texts, js_texts) if a != b]
    if not bad:
        n_t = sum(len(t) for t in py_texts)
        print(f"✅ أ نصوص المصدر — {len(names)} ملفاً · {n_t} نصّاً · متطابقة ترتيباً ومحتوىً")
    else:
        errs.append(f"أ: نصوص متباعدة في {bad[:5]}")
        print("❌ أ نصوص المصدر")
        for n in bad[:2]:
            i = names.index(n)
            print(f"   [{n}] بايثون={len(py_texts[i])} · JS={len(js_texts[i])}")
            for x, y in zip(py_texts[i], js_texts[i]):
                if x != y:
                    print(f"     PY: {x[:70]}\n     JS: {y[:70]}")
                    break

    # ── ب — حقل `isolation` في كتلة التدقيق ───────────────────────────
    py_iso = [R2.build_report(sp)[1].get("isolation") for sp in sps]
    js_iso = node(NODE_ISO, json.dumps(sps, ensure_ascii=False))
    bad = [(n, a, b) for n, a, b in zip(names, py_iso, js_iso) if a != b]
    if not bad:
        print(f"✅ ب حقل isolation — {len(names)} تقريراً متطابقاً")
    else:
        errs.append(f"ب: isolation متباعد — {bad[:3]}")
        print("❌ ب حقل isolation")

    # ── ج — عيب معلوم: تلوّث مُصطنَع (`ن-7/①`) ────────────────────────
    sp0 = sps[0]
    py_audit = E2.run(sp=sp0, content=_Stub([DIRTY])).audit
    py_threw = None
    try:
        E2.run(sp=sp0, content=_Stub([DIRTY]), strict=True)
    except Exception as e:
        py_threw = [type(e).__name__, str(e)]
    js_audit, js_threw = node(NODE_DIRTY, DIRTY, json.dumps(sp0, ensure_ascii=False))

    ok_hits = bool(py_audit) and py_audit == js_audit
    ok_stop = py_threw is not None and py_threw == js_threw
    if ok_hits and ok_stop:
        print(f"✅ ج عيب معلوم — {len(py_audit)} لفظاً مرصوداً في الطرفين · "
              f"و`strict` يوقف الطرفين بالرسالة نفسها")
    else:
        if not py_audit:
            errs.append("ج: لم يُرصد التلوّث في بايثون — العيّنة غير صالحة")
        if py_audit != js_audit:
            errs.append(f"ج: ألفاظ متباعدة — بايثون={py_audit} · JS={js_audit}")
        if py_threw != js_threw:
            errs.append(f"ج: strict متباعد — بايثون={py_threw} · JS={js_threw}")
        print("❌ ج عيب معلوم")

    print("-" * 76)
    if errs:
        print("النتيجة النهائية: ❌ انحدار — يُجمَّد الطرفان (DEC-200)")
        for e in errs:
            print("   ·", e)
        return 1
    print("النتيجة النهائية: ✅ لا انحدار")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
