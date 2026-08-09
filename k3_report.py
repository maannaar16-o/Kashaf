# -*- coding: utf-8 -*-
"""
k3_report.py — مُركِّب التقرير الكامل (v0.2)
=============================================
SPEC v2.1 §7 (تسعة أقسام · ق7) + 82-K3-RPT-HEADINGS v1.0 (DEC-139).

قواعد العرض النافذة:
  ر-1 ترقيم المعروض فعلاً — لا يقفز عند غياب قسم شرطي
  ر-2 ترويسة المصدر تُسقَط — العنوان من الجدول المعتمد
  ر-3 C-01 يُسقَط حين يحمل العنوان معناه
  ر-4 لافتة الثقة كتلة تنبيه بلا عنوان ولا رقم
  ر-5 صفر رقم أو رمز في أي عنوان (ق1)

🔒 يجمّع ولا يؤلّف: كل سطر من مصدر معتمد أو من المحرك.
"""
import hashlib
import json
import re, os
from k3_engine import run, band, SKILLS, USER_NAME
from k3_content import ContentPack, CONNECTIVES
import k3_contentpack as cp
from sp_gate import output_gate            # ح-4 · DEC-183 · ن-7

_HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_SECTIONS = json.load(open(os.path.join(_HERE, "skill_sections.json"), encoding="utf-8"))
CIRCLE_SHARED, CIRCLE_TAIL = cp.CIRCLE_SHARED, cp.CIRCLE_TAIL   # DEC-195/ج
THREE, VERIFY_Q = cp.THREE, cp.VERIFY_QUESTIONS

# العناوين المعتمدة — 82 §2 (DEC-139)
H = {
    1: "قبل أن تقرأ",
    2: "موقعك من النظام",
    4: "قدراتك الخمس",
    5: "تأكُّد من القوة",
    6: "كيف تعمل قدراتك معاً",
    7: "من أين يبدأ هذا؟",
    8: "هل هذا أنا؟",
    9: "فكرة تصلح لما بعد التقرير",
}
AR_NUM = "١٢٣٤٥٦٧٨٩"
# DEC-196 — تغطية صريحة لكل نطاق يخرجه band()؛ لا وسم افتراضي صامت (ن-7)
BAND_LABEL = {"limited": "حضور محدود", "core": "كفاءة أساسية",
              "high": "قدرة عالية", "OUT": "قراءة خاصة"}   # 80-K3-TEXTS


# DEC-197/ج — الاسم المرادف يُشتقّ من نصّ الخاتمة المعتمد (79 §2.2)، لا يُؤلَّف.
_ALT_RE = re.compile(r"وهذه المهارة\s*—\s*\*\*(.+?)\*\*")


def _alt_name(skill):
    m = _ALT_RE.search(CIRCLE_TAIL[skill])
    if not m:
        raise RuntimeError(f"DEC-197/حارس: اسم الخاتمة غير مستخرَج في {skill}")
    return m.group(1).strip()


def skill_heading(skill, b):
    """عنوان القسم المهاري — يجمع الاسمين حين يختلفان فقط (DEC-197/ج)."""
    short, alt = USER_NAME[skill], _alt_name(skill)
    # DEC-228/ب — التطابق التامّ وحده يُسقط القوس. الاحتواء الجزئي أُسقط:
    # قاعدة نصّية لا دلالية، وقد تُسقط القوس خطأً عند أي تغيير أسماء.
    name = short if alt == short else f"{short} ({alt})"
    return f"### {name} — {band_label(b)}"


def band_label(b):
    """يوقف الإصدار عند نطاق غير معتمد بدل تمويهه بوسم افتراضي."""
    if b not in BAND_LABEL:
        raise RuntimeError(f"DEC-196/حارس: نطاق غير معتمد «{b}» — يُصدر تقرير فجوة")
    return BAND_LABEL[b]


def _drop_heading(text):
    """ر-2: يُسقط سطر عنوان المصدر (### أو #) ويُبقي المتن."""
    lines = text.split("\n")
    if lines and lines[0].lstrip().startswith("#"):
        lines = lines[1:]
    return "\n".join(lines).strip()


def build_report(sp):
    pack = ContentPack(external=cp.build())
    res = run(sp, content=pack)
    a = res.audit
    L, n = [], 0

    def head(key):
        """ر-1: ترقيم متسلسل للمعروض فعلاً."""
        nonlocal n
        n += 1
        L.append(f"## {AR_NUM[n-1]} · {H[key]}")
        L.append("")

    # ① فاتحة العهد
    head(1); L += [THREE["covenant_opening"], ""]

    # ② خريطة الدائرة
    head(2); L += [CIRCLE_SHARED, ""]   # DEC-195/ج: المشترك فقط — لا خاتمة مهارية

    # ③ لافتة الثقة — ر-4: بلا عنوان ولا رقم
    if band(sp["EP"]) in ("limited", "OUT"):
        L += ["> ⚠️ " + cp.TRUST_BANNER, ""]

    # ④ الأقسام المهارية — ر-3: C-01 يُسقَط (العنوان يحمل معناه)
    head(4)
    for s in SKILLS:
        b, sec = band(sp[s]), SKILL_SECTIONS[s]
        L += [skill_heading(s, b), "",
              CIRCLE_TAIL[s], "", sec["U01"], ""]   # DEC-195/ج + 196 + 197/ج
        if b == "OUT":
            L += [THREE["out_text"].replace("{القدرة}", USER_NAME[s]), "", sec["U10"], ""]
        elif b in ("core", "high"):
            L += ["**ما يظهر عندك:**", sec["U08"], ""]
        else:
            L += ["**ما يحتاج انتباهاً:**", sec["U09"], ""]

    # ⑤ كتلة التحقق — قبل القراءة المركّبة (ق7)
    high = [s for s in ("IR", "BI", "CF", "ST") if band(sp[s]) == "high"]
    if high:
        L += [CONNECTIVES["C-02"], ""]
        head(5)
        L += [_drop_heading(cp.VERIFY_BLOCK), ""]
        L += ["- " + VERIFY_Q[s] for s in high] + ["", cp.VERIFY_CLOSING, ""]

    # ⑥ القراءة المركّبة
    if res.section6:
        head(6); L += [res.section6, ""]

    # ⑦ سؤال موضع الجذر
    if res.section7:
        head(7); L += [res.section7, ""]

    # ⑧ أسئلة الفصل
    L += [CONNECTIVES["C-05"], ""]
    head(8); L += [cp.SEPARATION_QS, ""]

    # ⑨ الإطار التأملي
    L += [CONNECTIVES["C-06"], ""]
    head(9); L += [_drop_heading(THREE["reflective_frame"])]

    a["sections_rendered"] = n
    # DEC-206 — الحقل نفسه في الطرفين
    a = dict(a)
    a["sections_rendered"] = n
    # DEC-220 — عقد إعادة التوليد
    _sha = lambda o: hashlib.sha256(
        json.dumps(o, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        .encode("utf-8")).hexdigest()[:16]
    a["pack_sha"] = {"SECTIONS_K3": _sha(SKILL_SECTIONS), "THREE_K3": _sha(THREE),
                     "CIRCLE_K3": _sha({"shared": CIRCLE_SHARED, "tail": CIRCLE_TAIL})}
    a["report_sha256"] = hashlib.sha256("\n".join(L).encode("utf-8")).hexdigest()[:16]
    _out = "\n".join(L)
    output_gate(_out, "تقرير K3")                # ح-4 — يوقف الإصدار عند تسرّب SP%
    return _out, a


if __name__ == "__main__":
    txt, _ = build_report(dict(EP=62, IR=38, BI=78, CF=44, ST=74))
    print(txt)
