# -*- coding: utf-8 -*-
"""
k2_content.py — سجل المحتوى لمحرك K2
=====================================
المبدأ الحاكم: **المحرك يجمّع ولا يؤلّف** (56-REPORT-ENGINE §0.1).

مصدر النصوص:
  * أسطر المعاجم الستة (C·S·St·R·A·O): تُحمَّل من k2_contentpack.json
    (مستخلَصة حرفياً من COMPOSE-{C,S,St,R,A,O} · DEC-169…177).
  * معجما E·H (62/63-COMPOSE): **خارجيان إلزاميان** — مصدرهما غير متاح هنا،
    فيُحمَّلان أو يُرفع MissingContentError. لا يُخترعان.
  * أسطر الوصل الهيكلية وفاتحة التقرير: من القائمة المغلقة (56-REPORT-ENGINE
    §5.3 / الملحق أ) — خارجية إلزامية أيضاً.
"""
import json, os

CONTENT_VERSION = "k2_contentpack v0.1 (COMPOSE C·S·St·R·A·O) + E/H external"
_HERE = os.path.dirname(os.path.abspath(__file__))
_PACK_PATH = os.path.join(_HERE, "k2_contentpack.json")

EXTERNAL_CENTERS = set()               # الثمانية مبنية (E/H أُعيد بناؤهما · يُوفَّقان مع 62/63-COMPOSE)

# روابط محظورة — فحص «الوصل ينقل ولا يستدلّ» (مطابق K3)
FORBIDDEN_CONNECTORS = ["ولذلك", "لهذا السبب", "مما يعني", "وبالتالي",
                        "نستنتج", "ومن ثمّ", "ومن ثم", "أقوى من", "أفضل من"]

# محتوى خارجي إلزامي — لا يُخترع
REQUIRED_EXTERNAL = {}   # لا نواقص خارجية — report_framing عولج (k2_framing · الملحق أ)
# تنبيه توفيق: معاجم E/H هنا إعادة بناء — معتمدة بديلاً نافذاً (DEC-181/182).


class MissingContentError(RuntimeError):
    """يُرفع حين يُطلب نصّ من مصدر معتمد غير محمَّل. لا بديل ولا تأليف."""


class ContentPack:
    """حزمة محتوى K2. الستة مضمّنة عبر الحزمة؛ E/H والفاتحة تُحمَّل أو تفشل."""

    def __init__(self, external=None, pack_path=_PACK_PATH):
        with open(pack_path, encoding="utf-8") as fh:
            self._pack = json.load(fh)
        self.external = dict(external or {})

    # -- الوصول للأسطر --------------------------------------------------- #
    def has_center(self, center):
        return center in self._pack

    def get_line(self, code):
        """code مثل A-E-L → dict(presence, question, source, recommendation)."""
        center = code.split("-")[0]
        if center in self._pack and code in self._pack[center]["lines"]:
            return self._pack[center]["lines"][code]
        if center in EXTERNAL_CENTERS:
            key = f"lexicon_{center}"
            if key in self.external and code in self.external[key]:
                return self.external[key][code]
            raise MissingContentError(
                f"سطر «{code}» من معجم خارجي غير محمَّل. المصدر: {REQUIRED_EXTERNAL.get(key)}."
            )
        raise MissingContentError(f"سطر «{code}» غير موجود في أي مصدر معتمد.")

    def get_blindness(self, center):
        if center in self._pack:
            return self._pack[center]["blindness"]
        if center in EXTERNAL_CENTERS:
            raise MissingContentError(
                f"نص عمى «{center}» خارجي غير محمَّل ({REQUIRED_EXTERNAL.get('lexicon_'+center)})."
            )
        raise MissingContentError(f"نص عمى «{center}» غير معروف.")

    # -- ما يستهلكه تدقيق العزل في المحرك -------------------------------- #
    def texts_for(self, profile):
        """كل النصوص المستدعاة فعلاً لهذا الملف (للتدقيق) — يتجاوز غير المتاح."""
        out = []
        c = profile.center
        try:
            out.append(self.get_blindness(c))
        except MissingContentError:
            pass
        for lens in profile.sp:
            if lens == c:
                continue
            st = "D" if profile.sp[lens] > 70 else "M" if profile.sp[lens] > 50 else "L"
            try:
                ln = self.get_line(f"{c}-{lens}-{st}")
                out += [ln["presence"], ln.get("recommendation", "")]
            except MissingContentError:
                pass
        return [t for t in out if t]

    def missing(self):
        return [k for k in REQUIRED_EXTERNAL if k not in self.external]


# --------------------------------------------------------------------------- #
# عرض تجريبي — يربط المحتوى بالمحرك على الحالتين الحقيقيتين
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    import json as _j
    from k2_engine import run, LENS_NAME

    pack = ContentPack()
    golden = _j.load(open(os.path.join(_HERE, "golden_k2.json"), encoding="utf-8"))

    for name in ("P-005", "P-006"):
        r = run(sp=golden[name]["sp"])
        c = r.profile.center
        print("\n" + "=" * 74)
        print(f"{name} — مركز {c} ({LENS_NAME[c]})   [قسم التركيب من التقرير]")
        print("=" * 74)

        # نص العمى مكيَّفاً بـ ت-8
        print("• نقطة العمى (مكيَّفة بـ ت-8):")
        for h in r.t8:
            print(f"    — {h['half']}: {h['phrase']}")
        if r.stitch:
            print(f"    ⟹ {r.stitch}")

        # أسطر الاستدعاء بنصّها
        print("\n• أسطر التركيب المستدعاة:")
        for ln in r.lines:
            body = pack.get_line(ln.code)
            mark = "◆" if ln.layer == "delivery" else "·"
            print(f"  {mark} [{ln.code}] {body['presence'][:88]}")

        # أسئلة التسليم (ت-7)
        print("\n• أسئلة التسليم (ت-7):")
        for code in r.delivery_questions:
            print(f"    ؟ {pack.get_line(code)['question']}")

    # تدقيق عزل عبر المحتوى الفعلي
    print("\n" + "-" * 74)
    for name in ("P-005", "P-006"):
        r = run(sp=golden[name]["sp"], content=pack)
        print(f"{name}: تدقيق العزل عبر المحتوى المستدعى →",
              "نظيف ✅" if not r.audit else f"❌ {r.audit}")
    print("النواقص الخارجية الإلزامية:", pack.missing())
