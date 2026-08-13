# -*- coding: utf-8 -*-
"""
test_site_build.py — حرس بناء الموقع والأداة (البوابة 19 ← 20)
================================================================
سند: أمر المالك «نفذ ① و④» — 2026-08-13 · `DEC-269`.

**لماذا وُجد هذا الحرس:** البوابة الـ19 لم تكن تشمل `build_site.py`، فانكسر
بناء الموقع عند بناء `K4` (استيرادات غير مُشيَّمة) **ومرّ الانكسار صامتاً
في التزامَين** — والملفات المولَّدة في `docs/` بقيت نسخةً لا تعرف `K4`.

فحوصه — وكلٌّ **يقيس ما يعلنه**:
  ① اكتمال التشييم — صفر `require(` في الحزمة الموحَّدة (الانكسار عينه)
  ② صفر تصدير عقدة متسرّب إلى المتصفح
  ③ `K4` **موصولٌ بالأداة** — تبويبه وسطحه العابر وحزمته ومصدر خريطته
  ④ `docs/` **مزامنة** مع بناءٍ طازج — فلا تقادم يمرّ صامتاً
"""
import io
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

FAILS = []


def check(label, ok, detail=""):
    print(f"{'✅' if ok else '❌'} {label}" + (f" — {detail}" if detail else ""))
    if not ok:
        FAILS.append(label)


import build_site as BS


# ── ① اكتمال التشييم — الانكسار الذي مرّ صامتاً ─────────────────────────
def test_shim_completeness():
    # الفشل يُلتقط ويُصاغ — لا رمي خام: البوابة تُقرأ سطراً سطراً،
    # وبقية الفحوص تُكمل بدل أن تُبتَر.
    try:
        mods = BS.js_modules()
    except AssertionError as e:
        check("اكتمال التشييم — صفر استيراد باقٍ", False, f"{e}")
        return ""
    check("اكتمال التشييم — صفر استيراد باقٍ", "require(" not in mods,
          f"{len(mods)} بايت مجمَّعة")
    # التصدير **غير المحروس** هو التسرّب — أما `typeof module` فهو النمط
    # الصحيح للبيئتين (الفرع لا ينفَّذ في المتصفح)، فعدُّه تسرّباً قياسٌ أعمى.
    lines = mods.split("\n")
    unguarded = []
    for i, ln in enumerate(lines):
        if "module.exports" not in ln:
            continue
        window = ln + " " + (lines[i - 1] if i else "")
        if "typeof module" not in window:
            unguarded.append(i + 1)
    guarded = sum(1 for ln in lines if "module.exports" in ln) - len(unguarded)
    check("صفر تصدير عقدة غير محروس", not unguarded,
          f"{guarded} تصديراً محروساً بـtypeof module"
          if not unguarded else f"غير محروس في الأسطر: {unguarded[:6]}")
    return mods


# ── ③ K4 موصولٌ بالأداة — بعد تنفيذ البندين ② و③ (`DEC-270`) ────────────
def test_k4_wired(mods):
    if not mods:
        check("فحوص K4 على الحزمة", False, "الحزمة لم تُجمَّع — الفحص متعذّر")
        return
    check("محرك K4 محمَّل في الحزمة",
          "window.RawahilEngines = { K2, K3, K4," in mods, "الوحدة حاضرة")
    check("حزمة K4 مشيَّمة إلى `packs.js`",
          "PK.PACKS.CONTENT_K4) || null" in mods,
          "مصدر حقيقة واحد — لا نسخة ثانية")
    check("رسالة الرفض باقية نافذة",
          "حزمة K4 غير محمَّلة" in mods, "غياب الحزمة يوقف الإصدار")

    # الوصل — الأداة تعرض التقرير الثالث والسطح العابر
    kashaf = BS.read("docs", "kashaf.html")
    for label, needle in (("تبويب K4", "تقرير الإنجاز (K4)"),
                          ("كتلة السطح العابر", "قراءة عابرة — سطح مستقل"),
                          ("جسر spK4", "function spK4"),
                          ("حزمة K4 في المخرج", "CONTENT_K4")):
        check(f"موصول: {label}", needle in kashaf)

    # لوحة `DEC-186` صارت K1 وحدها — والتصريح مكتوب
    check("لوحة DEC-186 لـK1 وحدها",
          "لوحة تشخيصية داخلية — K1" in kashaf
          and "دائرة الإنجاز (K4) خرجت من هذه اللوحة" in kashaf,
          "K4 خرجت إلى تقرير معتمد")


# ── ④ docs/ مزامنة مع بناء طازج — لا تقادم صامت ─────────────────────────
def test_docs_in_sync():
    docs = os.path.join(HERE, "docs")
    if not os.path.isdir(docs):
        check("docs/ موجودة", False, "المجلد غائب")
        return
    before = {}
    for name in sorted(os.listdir(docs)):
        path = os.path.join(docs, name)
        if os.path.isfile(path):
            with open(path, "rb") as fh:
                before[name] = fh.read()

    buf = io.StringIO()
    old = sys.stdout
    sys.stdout = buf
    err = None
    try:
        rc = BS.main()
    except SystemExit as e:
        rc = e.code if isinstance(e.code, int) else 1
    except AssertionError as e:          # حارسُ الباني نفسه — يُصاغ لا يُرمى
        rc, err = 1, str(e)
    finally:
        sys.stdout = old
    check("بناء الموقع يكتمل", rc in (0, None),
          f"رمز الخروج {rc}" + (f" · {err}" if err else ""))
    if err:
        check("docs/ مزامنة مع بناء طازج", False, "البناء أخفق — المزامنة متعذّرة")
        return

    after = {}
    for name in sorted(os.listdir(docs)):
        path = os.path.join(docs, name)
        if os.path.isfile(path):
            with open(path, "rb") as fh:
                after[name] = fh.read()

    drifted = [n for n in sorted(set(before) | set(after))
               if before.get(n) != after.get(n)]
    check("docs/ مزامنة مع بناء طازج", not drifted,
          f"{len(after)} ملفاً متطابقاً"
          if not drifted else "متقادمة: " + " · ".join(drifted[:6])
          + " — أعد التوليد بـbuild_site.py")


if __name__ == "__main__":
    print("=" * 76)
    mods = test_shim_completeness()
    test_k4_wired(mods)
    test_docs_in_sync()
    print("-" * 76)
    if FAILS:
        print(f"النتيجة النهائية: ❌ انحدار — {len(FAILS)}: " + " · ".join(FAILS))
        raise SystemExit(1)
    print("النتيجة النهائية: ✅ لا انحدار")
