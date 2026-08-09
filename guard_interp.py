# -*- coding: utf-8 -*-
"""
guard_interp.py — حارس `ح-6`: الصياغة الصريحة عند حافة الإخراج
================================================================
سند: `ن-8` (`DEC-239`) · `ن-7` · `DEC-235` · `DEC-238`

**ما يقيسه — شيء واحد (`ن-7/②`):** ألّا يدخل **استيفاء جديد غير مصاغ
صراحةً** عند موضع إصدار. لا يقيس صحّة النصّ ولا التكافؤ — لهما مقاييسهما.

**حدّه — مُصرَّح به:** كشفٌ لا برهان. نوع المتغيّر لا يُحسم ساكناً في
اللغتين، فالحارس **بوّابة انحدار** لا إثبات خلوّ. تقديمه كبرهان تامّ يكون
«حقلاً لا يفحص» — وهو النمط المرفوض في `DEC-236` و`DEC-238`.

**لماذا سجلّ لا حكم آلي:** مسح `DEC-239` أثبت أن الكود القائم **خالٍ**
من الأصناف ④…⑨. فوظيفة الحارس منع **المستجدّ**، لا علاج قائم. وكل
استيفاء قائم مُسجَّل بصنفه؛ وأي استيفاء خارج السجلّ يوقف البوّابة.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REGISTRY = os.path.join(HERE, "interp_registry.json")

# ── مواضع الإصدار — حافة الإخراج وحدها (`ن-8` النطاق أ) ────────────────
EMIT_PY = re.compile(r"(L\.append\(|L\.extend\(|raise\s+\w+Error\(|head\()")
EMIT_JS = re.compile(r"(L\.push\(|throw\s+new\s+\w+\(|download\(|document\.write\()")
INTERP_PY = re.compile(r"(?<!\$)\{([^{}]+)\}")
INTERP_JS = re.compile(r"\$\{([^{}]+)\}")

FILES = [("k2_report.py", EMIT_PY, INTERP_PY), ("k3_report.py", EMIT_PY, INTERP_PY),
         ("k2_engine.py", EMIT_PY, INTERP_PY), ("k3_engine.py", EMIT_PY, INTERP_PY),
         ("reports.js", EMIT_JS, INTERP_JS), ("dualreport.js", EMIT_JS, INTERP_JS),
         ("engines.js", EMIT_JS, INTERP_JS)]

# ليست استيفاءً أصلاً: استيعاب قاموس/مجموعة، أو قاموس حرفي.
# تسجيلها ضجيجاً يُفسد معنى السجلّ؛ فتُستبعد بقاعدة لا بمدخل.
NOT_INTERP = re.compile(r"\bfor\b.*\bin\b|^[\"'][^\"']*[\"']\s*:")

# صياغة صريحة — لا تحتاج تسجيلاً
EXPLICIT = re.compile(r"_num\(|_round2\(|\.join\(|\.toFixed\(|\bString\(|\bstr\(|"
                      r"json\.dumps|JSON\.stringify|\.padStart\(|\.padEnd\(")


class InterpGateError(RuntimeError):
    """استيفاء غير مصاغ ولا مسجَّل عند موضع إصدار — `ح-6`."""


def collect():
    """يجمع كل استيفاء عند موضع إصدار: (الملف، التعبير)."""
    out = set()
    for fn, emit, interp in FILES:
        p = os.path.join(HERE, fn)
        if not os.path.exists(p):
            continue
        lines = open(p, encoding="utf-8").read().split("\n")
        for i, line in enumerate(lines):
            if not emit.search(line):
                continue
            for e in interp.findall("\n".join(lines[i:i + 4])):
                e = " ".join(e.split())          # تطبيع الفراغات والأسطر
                if NOT_INTERP.search(e):         # استيعاب أو قاموس حرفي
                    continue
                out.add((fn, e))
    return out


def load_registry():
    if not os.path.exists(REGISTRY):
        return {}
    return json.load(open(REGISTRY, encoding="utf-8"))


def check():
    """يعيد (المجموع، المصاغ صراحةً، المسجَّل، غير المسجَّل)."""
    found = collect()
    reg = load_registry()
    explicit, registered, orphan = [], [], []
    for fn, e in sorted(found):
        if EXPLICIT.search(e):
            explicit.append((fn, e))
        elif e in reg.get(fn, {}):
            registered.append((fn, e))
        else:
            orphan.append((fn, e))
    return len(found), explicit, registered, orphan


def main():
    total, explicit, registered, orphan = check()
    print(f"مواضع الإصدار المفحوصة: {len(FILES)} ملفاً · {total} استيفاءً")
    print(f"  · مصاغ صراحةً : {len(explicit)}")
    print(f"  · مسجَّل       : {len(registered)}")
    print(f"  · غير مسجَّل   : {len(orphan)}")
    print("-" * 76)
    if orphan:
        print(f"❌ ح-6/ن-8 — {len(orphan)} استيفاءً بلا صياغة ولا تسجيل. الإصدار موقوف.")
        for fn, e in orphan[:15]:
            print(f"   [{fn}] {e[:70]}")
        print("\n   العلاج: إمّا صياغة صريحة (`_num` · `_round2` · `.join` …)،")
        print("           وإمّا تسجيل في `interp_registry.json` بسببٍ مكتوب.")
        return 1
    print("✅ ح-6 لا انحدار — صفر استيفاء غير مصاغ ولا مسجَّل")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
