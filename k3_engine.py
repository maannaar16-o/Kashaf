# -*- coding: utf-8 -*-
"""
k3_engine.py — محرك تقارير دائرة الانفعال (K3)
================================================
ترجمة `57-K3-ENGINE-SPEC v2.1` إلى كود (استحقاق ق6 الثاني).

الثوابت الحاكمة:
  * القياس لا يُمسّ: SS = x - 2z + y ، SP = SS/66*100 ، instrument_pin ثابت.
  * صفر أوزان · صفر عتبات مستحدثة (DEC-064 + DEC-133) · صفر صيغ تجميع.
  * المحرك يجمّع ولا يؤلّف: كل نص من k3_content أو من حزمة خارجية معتمدة.
  * audit داخلي بالكامل (ق1 / DEC-092).
"""
from dataclasses import dataclass, field
from k3_content import (TEMPLATES, CONTAINMENT_TEXT, LOAD_TAG, CONNECTIVES,
                        ROOT_QUESTIONS, FORBIDDEN_CONNECTORS, ContentPack)

ENGINE_VERSION = "0.4"
SPEC_VERSION = "57-K3-ENGINE-SPEC v2.1"
INSTRUMENT_PIN = "40 v5.0 + 41 v4.2"

SKILLS = ["EP", "IR", "BI", "CF", "ST"]           # ترتيب العرض = مسار المعالجة
# DEC-215 — الأسماء المعتمدة للعرض بأمر مالك المشروع (تنسخ ما قبلها)
USER_NAME = {"EP": "مهارة قوة الملاحظة", "IR": "مهارة التحكم الانفعالي",
             "BI": "مهارة كبح جماح النفس", "CF": "مهارة المرونة",
             "ST": "مهارة تحمل الضغوط"}

# --------------------------------------------------------------------------- #
# 1) الحساب والتصنيف — SPEC §1-§2 (لا يُمسّ)
# --------------------------------------------------------------------------- #
MAX_RAW = 66


class InputContractError(ValueError):
    """خرق عقد المدخل — إيقاف بلا إصلاح صامت (SPEC §1.4)."""


def _num(v):
    """تصيير موحَّد للعدد في رسائل العقد (`DEC-235`).
    الصحيح بلا فاصلة عشرية. صريحٌ في الطرفين كي لا يُعاد الانجراف
    بالاتّكال على سلوك اللغة الضمني."""
    try:
        f = float(v)
    except (TypeError, ValueError):
        return str(v)
    return str(int(f)) if f.is_integer() else str(f)

def compute_ss_sp(x, y, z):
    if y + z != 11:
        raise InputContractError(
            f"y+z يجب أن يساوي 11 (y={_num(y)}, z={_num(z)})")
    ss = x - 2 * z + y
    return ss, ss / MAX_RAW * 100.0


def octal_code(sp):
    if sp < 0:   return "OUT"
    if sp < 20:  return "L-"
    if sp < 40:  return "L"
    if sp < 50:  return "M"
    if sp <= 70: return "M+"
    if sp <= 85: return "H"
    if sp <= 100: return "H+"
    return "H++"


def band(sp):
    """التثليث الحاكم — DEC-064 + DEC-133 (حدّ 50.0 محايد)."""
    if sp < 0:    return "OUT"
    if sp < 50:   return "limited"    # حضور محدود
    if sp <= 70:  return "core"       # كفاءة أساسية — محايد
    return "high"                     # قدرة عالية


def pole(sp):
    """قطب الاستدعاء — ح-1. المحايد و OUT لا يُستدعيان."""
    b = band(sp)
    if b == "limited": return "W"
    if b == "high":    return "S"
    return None


# --------------------------------------------------------------------------- #
# 2) سجل الاقتران — 28 خلية (62 / 62-B / 62-C)
# --------------------------------------------------------------------------- #
# locus: none | internal | external | to_ST | post_hoc | repeat_effort | transferred_out | misdirected
EDGES = [
    ("IR", "BI", "hub"),  ("IR", "CF", "hub"),
    ("BI", "CF", "lateral"),
    ("IR", "ST", "load"), ("BI", "ST", "load"), ("CF", "ST", "load"),
    ("EP", "IR", "feed"),
]
FAMILY_ORDER = {"hub": 0, "lateral": 1, "load": 2, "feed": 3}   # ب-1 / 64 §4.1
EDGE_INDEX = {(a, b): i for i, (a, b, _) in enumerate(EDGES)}    # M3-00 v2.0 §3.1

CELLS = {
    # ① المحور
    ("IR", "BI", "SS"): ("تعزيز", "none", False, "T-01"),
    ("IR", "BI", "SW"): ("تفاقم موضعي", "external", False, "T-07"),
    ("IR", "BI", "WS"): ("تثبيت", "internal", False, "T-02"),
    ("IR", "BI", "WW"): ("تفاقم", "external", False, "T-07"),
    ("IR", "CF", "SS"): ("تعزيز", "none", False, "T-01"),
    ("IR", "CF", "SW"): ("تثبيت بكلفة", "repeat_effort", False, "T-03"),
    ("IR", "CF", "WS"): ("تهذيب", "post_hoc", False, "T-06"),
    ("IR", "CF", "WW"): ("تفاقم", "to_ST", False, "T-08"),
    # ④ الجانبي
    ("BI", "CF", "SS"): ("تعزيز", "none", False, "T-01"),
    ("BI", "CF", "SW"): ("تفاقم", "to_ST", False, "T-08"),
    ("BI", "CF", "WS"): ("تهذيب", "post_hoc", False, "T-06"),
    ("BI", "CF", "WW"): ("تفاقم", "external", False, "T-07"),
    # ③ التحميل
    ("IR", "ST", "SS"): ("تعزيز", "none", False, "T-01"),
    ("IR", "ST", "SW"): ("تثبيت جزئي", "none", False, "T-05"),
    ("IR", "ST", "WS"): ("تثبيت بكلفة", "to_ST", True, "T-04"),
    ("IR", "ST", "WW"): ("تفاقم", "to_ST", False, "T-08"),
    ("BI", "ST", "SS"): ("تعزيز مشروط", "none", False, "T-01"),
    ("BI", "ST", "SW"): ("تفاقم مشروط", "to_ST", False, "T-08"),
    ("BI", "ST", "WS"): ("محايد على الحافة", "transferred_out", False, "T-09"),
    ("BI", "ST", "WW"): ("محايد على الحافة", "none", False, "T-09"),
    ("CF", "ST", "SS"): ("تعزيز", "none", False, "T-01"),
    ("CF", "ST", "SW"): ("تثبيت جزئي", "none", False, "T-05"),
    ("CF", "ST", "WS"): ("تثبيت بكلفة مضاعفة", "to_ST", True, "T-04"),
    ("CF", "ST", "WW"): ("تفاقم", "to_ST", False, "T-08"),
    # ② التغذية الإدراكية
    ("EP", "IR", "SS"): ("تعزيز", "none", False, "T-01"),
    ("EP", "IR", "SW"): ("محايد على الحافة", "none", False, "T-09"),
    ("EP", "IR", "WS"): ("تثبيت بكلفة", "misdirected", True, "T-11"),  # GAP-CODE-01 مغلقة (DEC-137)
    ("EP", "IR", "WW"): ("تفاقم", "to_ST", False, "T-08"),
}

# خلايا بلا قالب كلفة معتمد — تُرفع فجوةً ولا تُملأ بالتخمين (فارغ بعد DEC-137)
TEMPLATE_GAPS = {}


class StrictGateError(RuntimeError):
    """بوابة `strict` في $K_3$ — الإصدار موقوف (`DEC-240`).

    الرسالة **نصّ صريح** (`ن-8`)، والحمولة البنيوية محفوظة في السمات:
    `gaps` · `violations` · `missing_content`. كانت الحمولة قاموساً
    يُصيَّر ضمناً — تمثيلاً بايثونياً لا نظير له في JS (`GAP-STRICT-K3-01`).
    """

    def __init__(self, gaps, violations, missing_content):
        self.gaps = list(gaps)
        self.violations = list(violations)
        self.missing_content = list(missing_content)
        super().__init__(strict_gate_message(
            self.gaps, self.violations, self.missing_content))


def strict_gate_message(gaps, violations, missing_content):
    """صياغة صريحة موحَّدة (`ن-8`) — نظيرها الحرفي في `engines.js`."""
    def part(label, items):
        return f"{label}: " + (" · ".join(items) if items else "لا شيء")
    return ("بوابة strict — الإصدار موقوف · "
            + part("فجوات", gaps) + " · "
            + part("مخالفات", violations) + " · "
            + part("محتوى مفقود", missing_content))


@dataclass
class Cell:
    a: str
    b: str
    state: str
    family: str
    relation: str
    locus: str
    amplifies: bool
    template: str

    @property
    def code(self):
        return f"CPL-{self.a}.{self.b}-{self.state}"


def activate_cells(sp):
    """ح-1: الأقطاب فقط · المحايد لا يُستدعى · OUT مستبعَد (DEC-133)."""
    out = []
    for a, b, fam in EDGES:
        pa, pb = pole(sp[a]), pole(sp[b])
        if pa is None or pb is None:
            continue
        rel, locus, amp, tpl = CELLS[(a, b, pa + pb)]
        out.append(Cell(a, b, pa + pb, fam, rel, locus, amp, tpl))
    # DEC-137/6: الترتيب داخل العائلة بترتيب الحافات في M3-00 §3.1 — لا أبجدياً
    out.sort(key=lambda c: (FAMILY_ORDER[c.family], EDGE_INDEX[(c.a, c.b)]))
    return out


# --------------------------------------------------------------------------- #
# 3) التعرّف على النمط — 65 v1.1 + DEC-133
# --------------------------------------------------------------------------- #
def _has(cells, a, b, states):
    return any(c.a == a and c.b == b and c.state in states for c in cells)


def active_load_channels(cells):
    """«القناة النشطة» — التعريف المركزي M3-04 v1.2 §2.1 (لاتماثل مقصود)."""
    ch = []
    if _has(cells, "IR", "ST", ("WS", "WW")): ch.append("IR")
    if _has(cells, "CF", "ST", ("WS", "WW")): ch.append("CF")
    if _has(cells, "BI", "ST", ("SS", "SW")): ch.append("BI")   # ينشط بالقوة لا بالضعف
    return ch


def recognize_patterns(cells, sp):
    pats = []
    # HF-01 — عطل المحور: IR محدودة + حافتا المحور معاً
    if band(sp["IR"]) == "limited" and \
       _has(cells, "IR", "BI", ("WS", "WW")) and _has(cells, "IR", "CF", ("WS", "WW")):
        pats.append({"code": "HF-01", "family": "hub", "status": "full",
                     "cells": [c.code for c in cells
                               if (c.a, c.b) in (("IR", "BI"), ("IR", "CF"))]})
    # HF-02 — عطل الذراع مع عودة الشحنة
    if _has(cells, "IR", "CF", ("SW",)) and _has(cells, "CF", "ST", ("WS", "WW")):
        pats.append({"code": "HF-02:CF", "family": "hub", "status": "full",
                     "cells": ["CPL-IR.CF-SW"] + [c.code for c in cells if (c.a, c.b) == ("CF", "ST")]})
    if _has(cells, "BI", "CF", ("SW",)) and _has(cells, "BI", "ST", ("SS", "SW")):
        pats.append({"code": "HF-02:BI", "family": "lateral", "status": "full",
                     "cells": ["CPL-BI.CF-SW"] + [c.code for c in cells if (c.a, c.b) == ("BI", "ST")]})
    # HF-04 — تشبّع القاعدة
    if len(active_load_channels(cells)) >= 2 and band(sp["ST"]) == "limited":
        pats.append({"code": "HF-04", "family": "load", "status": "full",
                     "cells": [c.code for c in cells if c.b == "ST"]})
    pats.sort(key=lambda p: FAMILY_ORDER[p["family"]])
    return pats


# --------------------------------------------------------------------------- #
# 4) البوابات
# --------------------------------------------------------------------------- #
def g1_trust(sp):
    return band(sp["EP"]) in ("limited", "OUT")


def g2_false_pole(sp):
    return [s for s in ("IR", "BI", "CF", "ST") if band(sp[s]) == "high"]


def g4_containment(sp, cells):
    bands = {s: band(sp[s]) for s in SKILLS}
    if all(b == "high" for b in bands.values()):    return "strong"
    if all(b == "limited" for b in bands.values()): return "weak"
    if not cells:                                   return None   # DEC-133: لا نصّ حالة
    return "composite"


def g3_question(patterns, cells):
    """ت-1/ت-2 — سؤال واحد كحدّ أقصى."""
    if patterns:
        code = {"HF-01": "RQ-01", "HF-02:CF": "RQ-02",
                "HF-02:BI": "RQ-03", "HF-04": "RQ-04"}[patterns[0]["code"]]
        return code, patterns[1:]
    # DEC-137/4: كلفة داخلية أو مُصدَّرة أو تضخيم — لا post_hoc ولا transferred_out
    COST_LOCI = ("internal", "repeat_effort", "to_ST", "misdirected")
    if any(c.locus in COST_LOCI or c.amplifies for c in cells):
        return "RQ-05", []
    return None, []


G5_CHECKS = {
    "ranking": ["أقوى من", "أضعف من", "ينكسر أولاً", "الأقوى فيك", "الأضعف فيك"],
    "causal_attribution": ["تحمل عبء", "يحمل عبء", "بسبب ضعف", "سببه ضعف"],
    "naming": ["HF-", "CPL-", "أنت نمط"],
    "clinical": ["اضطراب", "مرض", "علاج", "تشخيص", "أعراض", "شفاء"],
    "raw_number": ["SP =", "%,", "درجتك هي"],
    "temporal_prediction": ["ستنهار", "خلال أشهر", "قريباً ستفقد"],
    "connectors": FORBIDDEN_CONNECTORS,
}


def g5_isolation(text, stage="output"):
    """DEC-137/3: بوابة على مرحلتين — content عند التحميل · output عند التوليد."""
    hits = []
    for name, needles in G5_CHECKS.items():
        for n in needles:
            if n in text:
                hits.append({"stage": stage, "check": name, "token": n})
    return hits


def g5_scan_content(pack):
    """المرحلة الأولى: فحص حزمة المحتوى الخارجية — حيث يدخل النص غير المضمون."""
    hits = []
    for key, txt in (pack.external or {}).items():
        for h in g5_isolation(str(txt), stage="content"):
            h["key"] = key; hits.append(h)
    return hits


# --------------------------------------------------------------------------- #
# 5) التركيب — 64 v1.1 §4 + س-1..س-11
# --------------------------------------------------------------------------- #
def compose(cells, patterns, sp, low_trust, out_skills):
    lines, used = [], []

    def add(key, **kw):
        lines.append(CONNECTIVES[key].format(**kw) if kw else CONNECTIVES[key])
        used.append(key)

    def tpl(code, a=None, b=None):
        lines.append(TEMPLATES[code].format(a=USER_NAME.get(a, ""), b=USER_NAME.get(b, "")))
        used.append(code)

    add("C-03")
    lines.append(LOAD_TAG)
    for s in out_skills:                      # س-11 — التصريح بالاستبعاد
        add("C-16", skill=USER_NAME[s])
    if low_trust:
        add("C-12")

    state = g4_containment(sp, cells)
    if state:
        lines.append(CONTAINMENT_TEXT[state]); used.append(f"state:{state}")

    emitted, gaps = set(), []
    pattern_cells = {c for p in patterns for c in p["cells"]}

    def emit_group(group, lead=None):
        if not group:
            return
        if lead:
            add(lead)
        # س-9: الكلفة أولاً ثم التضخيم · س-3: القالب المكرر مرة واحدة
        for c in group:
            if c.template is None:
                # DEC-240 — القراءة من قاموس فارغ كانت ترفع `KeyError`
                # بدل أن تُسجّل فجوة. الوصف صريح عند غياب المدخل.
                gaps.append(TEMPLATE_GAPS.get(
                    (c.a, c.b, c.state),
                    f"خلية {c.code} بلا قالب كلفة معتمد")); continue
            if c.template not in emitted:
                tpl(c.template, c.a, c.b); emitted.add(c.template)
        if any(c.amplifies for c in group) and "T-10" not in emitted:
            tpl("T-10"); emitted.add("T-10")

    by_code = {c.code: c for c in cells}
    if patterns:
        emit_group([by_code[x] for x in patterns[0]["cells"] if x in by_code], "C-10")
        for p in patterns[1:]:
            emit_group([by_code[x] for x in p["cells"] if x in by_code], "C-15")
    rest = [c for c in cells if c.code not in pattern_cells]
    if rest:
        lead = "C-08" if all(c.family == "load" for c in rest) else "C-07"
        emit_group(rest, lead)
    return "\n".join(lines), used, gaps


# --------------------------------------------------------------------------- #
# 6) خط الأنابيب
# --------------------------------------------------------------------------- #
@dataclass
class Result:
    section6: str = ""
    section7: str = ""
    audit: dict = field(default_factory=dict)


def _gates_fired(low_trust, high, qcode, state, n_violations):
    """صياغة موحَّدة عبر البيئات — SPEC §audit: ["G1:low_trust=false","G2:high=[IR,ST]",…]
       البوليان بحرف صغير · القائمة بين قوسين بلا اقتباس ولا فراغ.
       G3 بصيغة `G3:asked:<code>` عند السؤال و`G3:none` عند غيابه (DEC-203)."""
    return [
        "G1:low_trust=" + ("true" if low_trust else "false"),
        "G2:high=[" + ",".join(high) + "]",
        # DEC-203 — الصيغة المركَّبة: الحالة ثم الكود. تصدُق على القراءتين معاً.
        ("G3:asked:" + qcode) if qcode else "G3:none",
        "G4:" + (state or "suppressed"),
        "G5:violations=" + str(n_violations),
    ]


def run(sp, content: ContentPack = None, strict=False):
    content = content or ContentPack()
    out_skills = [s for s in SKILLS if band(sp[s]) == "OUT"]
    low_trust = g1_trust(sp)
    high = g2_false_pole(sp)
    cells = activate_cells(sp)
    patterns = recognize_patterns(cells, sp)
    qcode, secondary = g3_question(patterns, cells)
    state = g4_containment(sp, cells)

    s6, used, gaps = ("", [], [])
    if cells:
        s6, used, gaps = compose(cells, patterns, sp, low_trust, out_skills)

    s7 = ""
    if qcode and cells:
        q = ROOT_QUESTIONS[qcode]
        s7 = "\n".join([CONNECTIVES["C-04"], CONNECTIVES["C-13"],
                        f"[أ] {q['alt'][0]}", f"[ب] {q['alt'][1]}",
                        CONNECTIVES["C-14"], q["q"]])
        used += ["C-04", "C-13", "C-14", qcode]

    violations = g5_scan_content(content) + g5_isolation(s6 + "\n" + s7)
    if strict and (gaps or violations or content.missing()):
        raise StrictGateError(gaps, violations, content.missing())

    audit = {
        "sp": {k: round(v, 1) for k, v in sp.items()},
        "codes": {k: octal_code(v) for k, v in sp.items()},
        "bands": {k: band(v) for k, v in sp.items()},
        "cells_activated": [c.code for c in cells],
        "cost_map": [{"cell": c.code, "locus": c.locus, "amplification": c.amplifies}
                     for c in cells],
        "patterns_recognized": [{"code": p["code"], "status": p["status"]} for p in patterns],
        "containment_state": state,
        "root_question": {"code": qcode, "response": "none", "attribution_source": "none"},
        "excluded_out": out_skills,
        # DEF-K3-02 (DEC-201): يُبنى من بيانات مبنينة وفق نصّ السند (SPEC §audit)،
        # لا بتنسيق لغة الاستضافة — وإلا اختلف المخرج بين البيئات (DEC-199).
        "gates_fired": _gates_fired(low_trust, high, qcode, state, len(violations)),
        "g5_violations": violations,
        "conditional_layers": ["G3:via-67"], "frozen_layers": [],
        "urs_version": "3.0", "engine_version": ENGINE_VERSION,
        "spec_version": SPEC_VERSION, "instrument_pin": INSTRUMENT_PIN,
        "entries_used": used,
        "template_gaps": gaps,
        "missing_content": content.missing(),
        "accepted_debts": ["DEBT-K3-EPPURITY-01", "GAP-Q-09"],
        "open_debts": ["DEBT-K3-FIELD-01"],
    }
    return Result(section6=s6, section7=s7, audit=audit)
