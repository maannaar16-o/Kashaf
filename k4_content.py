# -*- coding: utf-8 -*-
"""
k4_content.py — محمّل حزمة محتوى دائرة الإنجاز (K4)
====================================================
سند: `DEC-266` (`136-K4-ENGINE`) · مصدر النصوص: طبقة المستخدم المختومة
(`DEC-265` — `55-USER-K4-*`).

القاعدة الحاكمة (`صفر تأليف`):
  المحمّل **يقرأ ولا يؤلّف**. النص الغائب **فجوة تُرفع لا فراغ يُملأ** —
  ولا بديل افتراضي صامت (`ن-7/④`).

نظير `k3_content.py` في وظيفته، ومغاير في بنيته: أوعية $K_4$ سبعة،
ومفاتيحه المطلوبة مشتقة من قالب طبقة المستخدم (`135 §4`).
"""
import json
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_PACK_PATH = os.path.join(_HERE, "k4_contentpack.json")

VALVES = ["WM", "TI", "F", "PF", "OR", "TM", "PER"]      # ترتيب المسار (129 §2/①)

# مفاتيح كل صمام — من قالب `135 §4`. أي نقص فجوة تُرفع.
VALVE_KEYS = ["U01", "U03", "U04", "U05"]

# الصمامات ذات القطب الزائف المثبت — `134 §3/②` حصراً (لا يُزاد عليها)
RESERVE_VALVES = ["PER", "OR", "F"]

# الصمام بلا تدريب مسنود — فراغ مصرَّح (`135 §3/③`)
TRAINING_VOID = ["WM"]

BANDS = ["limited", "core", "high", "OUT"]

# قيود العبور المسطَّحة — `138 §2/①` حصراً (وما عداها سجلٌّ لا سطح)
CROSSING_SURFACED = ["K4-XR-03", "K4-XR-02", "K4-XR-05",
                     "K4-XR-06", "K4-XR-04", "K4-XR-08"]

# أنواع العلاقة ذات الصياغة — «تحييد» بلا صياغة عمداً (`138 §4/①`)
COMPOSED_KINDS = ["تعزيز", "مؤازرة", "هدر", "تفاقم"]
PATTERN_CODES = ["K4-PAT-01", "K4-PAT-02", "K4-PAT-03", "K4-PAT-04"]


class ContentGapError(RuntimeError):
    """نقصٌ في حزمة المحتوى — الإصدار موقوف بلا ملء صامت."""


def _load():
    with open(_PACK_PATH, encoding="utf-8") as fh:
        return json.load(fh)


class ContentPack:
    """حزمة محتوى $K_4$ — تُحمَّل مرة وتُفحص عند التحميل."""

    def __init__(self, raw=None):
        self.raw = raw if raw is not None else _load()
        self._gaps = self._audit()

    # ── الفحص البنيوي (يُجرى دائماً — لا حقل يدّعي الفحص ولا يفحص) ──────
    def _audit(self):
        gaps = []
        bl = self.raw.get("band_label", {})
        for b in BANDS:
            if not bl.get(b):
                gaps.append(f"band_label:{b}")
        valves = self.raw.get("valve", {})
        for v in VALVES:
            node = valves.get(v, {})
            for k in VALVE_KEYS:
                if not node.get(k):
                    gaps.append(f"valve:{v}:{k}")
        res = self.raw.get("reserve", {})
        if not res.get("opening"):
            gaps.append("reserve:opening")
        for v in RESERVE_VALVES:
            if not res.get(v):
                gaps.append(f"reserve:{v}")
        lk = self.raw.get("lookalike", {})
        for code in ("K4-LK-01", "K4-LK-02", "K4-LK-03"):
            if not lk.get(code):
                gaps.append(f"lookalike:{code}")
        tr = self.raw.get("training", {})
        for v in VALVES:
            if v in TRAINING_VOID:
                if v in tr:
                    # تدريبٌ حيث صُرِّح بالفراغ = تأليف — يُرفع مخالفةً لا يُقبل
                    gaps.append(f"training:{v}:محظور — فراغ مصرَّح")
                continue
            if not tr.get(v):
                gaps.append(f"training:{v}")
        if not self.raw.get("training_void", {}).get("WM"):
            gaps.append("training_void:WM")
        # سطح القراءة العابرة (`138 §2`)
        cr = self.raw.get("crossing", {})
        for k in ("heading", "lead", "closing"):
            if not cr.get(k):
                gaps.append(f"crossing:{k}")
        for code in CROSSING_SURFACED:
            if not cr.get("entry", {}).get(code):
                gaps.append(f"crossing:entry:{code}")
        # السطح المركَّب (`138 §3`/`§4`)
        cp = self.raw.get("composed", {})
        for k in ("network_lead", "network_limit", "pattern_limit",
                  "interruption_multi", "bottleneck_meaning", "bottleneck_tie"):
            if not cp.get(k):
                gaps.append(f"composed:{k}")
        for k in COMPOSED_KINDS:
            if not cp.get("kind", {}).get(k):
                gaps.append(f"composed:kind:{k}")
        if "تحييد" in cp.get("kind", {}):
            # صياغةٌ لنوعٍ بصفر قيود = تحضيرٌ لما لا دليل عليه (`138 §4/①`)
            gaps.append("composed:kind:تحييد:محظور — النوع بصفر قيود")
        for c in PATTERN_CODES:
            if not cp.get("pattern", {}).get(c):
                gaps.append(f"composed:pattern:{c}")
        return gaps

    # ── الواجهة ────────────────────────────────────────────────────────
    def missing(self):
        return list(self._gaps)

    def require(self):
        if self._gaps:
            raise ContentGapError(
                "حزمة K4 ناقصة — الإصدار موقوف · فجوات: " + " · ".join(self._gaps))
        return self

    def band_label(self, b):
        lbl = self.raw["band_label"].get(b)
        if not lbl:
            raise ContentGapError(f"نطاق غير معتمد «{b}» — لا وسم افتراضي (ن-7/④)")
        return lbl

    def valve(self, v, key):
        try:
            return self.raw["valve"][v][key]
        except KeyError:
            raise ContentGapError(f"نص مفقود valve:{v}:{key}")

    def reserve_opening(self):
        return self.raw["reserve"]["opening"]

    def reserve(self, v):
        try:
            return self.raw["reserve"][v]
        except KeyError:
            raise ContentGapError(f"سؤال تحفّظ مفقود reserve:{v}")

    def lookalike(self, code):
        try:
            return self.raw["lookalike"][code]
        except KeyError:
            raise ContentGapError(f"سؤال فرز مفقود lookalike:{code}")

    def training(self, v):
        """التدريب — أو نص الفراغ المصرَّح حيث لا بذرة."""
        if v in TRAINING_VOID:
            return None
        try:
            return self.raw["training"][v]
        except KeyError:
            raise ContentGapError(f"تدريب مفقود training:{v}")

    def training_void(self, v):
        return self.raw["training_void"].get(v)

    def crossing(self, code):
        try:
            return self.raw["crossing"]["entry"][code]
        except KeyError:
            raise ContentGapError(f"نص عبور مفقود crossing:entry:{code}")

    def composed_kind(self, kind):
        try:
            return self.raw["composed"]["kind"][kind]
        except KeyError:
            raise ContentGapError(f"صياغة نوع مفقودة composed:kind:{kind}")

    def composed_pattern(self, code):
        try:
            return self.raw["composed"]["pattern"][code]
        except KeyError:
            raise ContentGapError(f"صياغة نمط مفقودة composed:pattern:{code}")

    def sources(self):
        return dict(self.raw["_meta"]["sources"])


def load():
    """تحميل مفحوص — يوقف عند أي نقص."""
    return ContentPack().require()


if __name__ == "__main__":
    p = ContentPack()
    print("فجوات:", p.missing() or "لا شيء")
    print("الأوعية:", len(VALVES), "· نطاقات:", len(BANDS))
