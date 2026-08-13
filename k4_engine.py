# -*- coding: utf-8 -*-
"""
k4_engine.py — محرك دائرة الإنجاز (K4)
=======================================
ترجمة بُنى `129…135` إلى كود — بأمر المالك (المرحلة ٨ · `DEC-266`).

الثوابت الحاكمة:
  * القياس لا يُمسّ: `SS = x − 2z + y` · `SP = SS/66*100` · `y+z=11` · `instrument_pin`.
  * **صفر عتبة مستحدثة** (`ن-7/④`): حدود النطاقات مختومة سلفاً (`DEC-261`/`TRF-010`)
    بحدود $K_3$ الدنيا (`<`) — التبنّي حرفي لا إعادة اختراع.
  * **صفر تأليف**: المحرك يجمّع ولا يؤلّف — كل نص من `k4_content`.
  * **صفر ترجيح مخترَع**: عند تعادل عنق الزجاجة يُعرض الجميع (`DEC-150`/`R11` قياساً).
  * **عزل ثلاثي**: لا رمز ولا بند من $K_2$/$K_3$ يدخل هذا المحرك.

توأمه الحرفي: وحدة `K4` في `engines.js` — أي تغيير هنا يُصنع هناك،
ثم يُقاس التكافؤ (`DEC-199`/`DEC-200`).
"""
from dataclasses import dataclass, field

ENGINE_VERSION = "1.0"
SPEC_VERSION = "136-K4-ENGINE v1.0"
INSTRUMENT_PIN = "40 v5.0 + 41 v4.2"

MAX_RAW = 66

# ترتيب المسار — سند مزدوج (`129 §2/①`): التوجيه المالكي + ترقيم الدستور 1…7
VALVES = ["WM", "TI", "F", "PF", "OR", "TM", "PER"]

# الأسماء المختومة في الدستور (`14-CORE-K4 §2`) — والسابعة بقرار المالك (`DEC-257`)
USER_NAME = {
    "WM": "الذاكرة العاملة النشطة",
    "TI": "المبادرة والبدء الفعلي",
    "F": "التركيز وحجب المشتتات",
    "PF": "الالتزام بالأولويات والمسار الحرج",
    "OR": "التنظيم المادي للأشياء",
    "TM": "تقدير الوقت وإدارة الزمن",
    "PER": "المثابرة وإكمال المهام",
}


class InputContractError(ValueError):
    """خرق عقد المدخل — إيقاف بلا إصلاح صامت."""


def _num(v):
    """تصيير موحَّد للعدد في رسائل العقد (`DEC-235`) — نظيره الحرفي في JS."""
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
    """الكتل الثماني — بنية منقولة كما هي (`TRF-010`)، حدود دنيا (`<`)."""
    if sp < 0:    return "OUT"
    if sp < 20:   return "L-"
    if sp < 40:   return "L"
    if sp < 50:   return "M"
    if sp <= 70:  return "M+"
    if sp <= 85:  return "H"
    if sp <= 100: return "H+"
    return "H++"


def band(sp):
    """ثلاثية القدرة (`TRF-011`/`DEC-261`) — الصمامات لازمة معاً لا مفاضلة."""
    if sp < 0:   return "OUT"
    if sp < 50:  return "limited"      # حضور محدود
    if sp <= 70: return "core"         # كفاءة أساسية — محايد
    return "high"                      # قدرة عالية


def state(sp):
    """حال الطرف في قيود الشبكة: قويّ / ضعيف. المحايد و`OUT` لا يُستدعيان."""
    b = band(sp)
    if b == "limited": return "W"
    if b == "high":    return "S"
    return None


# رتبة النطاق للمقارنة الرتبية داخل الفرد الواحد (`132 §2/②`) — لا رقم يُقارَن
BAND_RANK = {"limited": 0, "core": 1, "high": 2}


# --------------------------------------------------------------------------- #
# 1) قيود الشبكة — `130-K4-RELATIONS` (`DEC-259` + `DEC-260`)
# --------------------------------------------------------------------------- #
# (كود, فاعل, حال الفاعل, مفعول, حال المفعول, النوع)
# «متبادل» يعني قيداً واحداً لا قيدين — استثناء معلَن خاص بنوع «تفاقم» (`DEC-260`).
CONSTRAINTS = [
    ("K4-REL-01", "PF",  "S", "F",   "S", "تعزيز"),
    ("K4-REL-02", "F",   "S", "OR",  "W", "مؤازرة"),
    ("K4-REL-03", "PER", "S", "OR",  "W", "مؤازرة"),
    ("K4-REL-04", "OR",  "S", "WM",  "W", "مؤازرة"),
    ("K4-REL-05", "PER", "W", "TI",  "S", "هدر"),
    ("K4-REL-06", "PF",  "W", "F",   "S", "هدر"),
    ("K4-REL-07", "TM",  "W", "OR",  "S", "هدر"),
    ("K4-REL-08", "TM",  "W", "PER", "S", "هدر"),
    ("K4-REL-09", "PF",  "W", "PER", "S", "هدر"),
    ("K4-REL-10", "WM",  "W", "TI",  "S", "هدر"),
    ("K4-REL-11", "TM",  "W", "PF",  "S", "هدر"),
    ("K4-REL-12", "TM",  "W", "PER", "W", "تفاقم"),
]
TYPE_ORDER = {"تعزيز": 0, "مؤازرة": 1, "تحييد": 2, "هدر": 3, "تفاقم": 4}
CONSTRAINT_INDEX = {c[0]: i for i, c in enumerate(CONSTRAINTS)}


@dataclass
class Constraint:
    code: str
    a: str
    b: str
    kind: str
    mutual: bool


def activate_constraints(sp):
    """يُفعَّل القيد حين يتحقق شرطه البنيوي بحاليه معاً. المحايد و`OUT` لا يُفعّلان."""
    out = []
    for code, a, sa, b, sb, kind in CONSTRAINTS:
        if state(sp[a]) == sa and state(sp[b]) == sb:
            out.append(Constraint(code, a, b, kind, kind == "تفاقم"))
    out.sort(key=lambda c: (TYPE_ORDER[c.kind], CONSTRAINT_INDEX[c.code]))
    return out


# --------------------------------------------------------------------------- #
# 2) الأنماط — `132-K4-CONSTRUCTS §4` (`DEC-262`)
# --------------------------------------------------------------------------- #
PAT_ORDER = ["K4-PAT-01", "K4-PAT-02", "K4-PAT-03", "K4-PAT-04"]


def recognize_patterns(sp):
    """البنية النطاقية الإسمية حصراً — لا رقم ولا عتبة (`132 §4/①`)."""
    b = {v: band(sp[v]) for v in VALVES}
    pats = []
    if any(b[v] == "OUT" for v in VALVES):
        # لا نمط فوق نقص — قاعدة تشغيل `132 §4/③`
        return pats
    limited = [v for v in VALVES if b[v] == "limited"]
    if all(b[v] == "limited" for v in ("PF", "TM", "PER")):
        pats.append({"code": "K4-PAT-01", "valves": ["PF", "TM", "PER"]})
    if all(b[v] == "high" for v in VALVES):
        pats.append({"code": "K4-PAT-02", "valves": list(VALVES)})
    if len(limited) == len(VALVES):
        pats.append({"code": "K4-PAT-03", "valves": list(VALVES)})
    if len(limited) == 1:
        pats.append({"code": "K4-PAT-04", "valves": list(limited)})
    pats.sort(key=lambda p: PAT_ORDER.index(p["code"]))
    return pats


# --------------------------------------------------------------------------- #
# 3) قراءتا المسار — `132 §1` و`§2`
# --------------------------------------------------------------------------- #
def interruption_points(sp):
    """مواضع الانقطاع — بترتيب المسار، بلا ترتيب أهمية (`132 §1/③/4`)."""
    return [v for v in VALVES if band(sp[v]) == "limited"]


def bottleneck(sp):
    """أدنى نطاق داخل الفرد — **مقارنة رتبية بين النطاقات لا بين الأرقام**
    (`132 §2/②`: لا عتبة تُخترع). وعند التعادل يُعرض الجميع بلا كسر
    (`DEC-150` قفلاً · `R11` قياساً — `132 §2/③`)."""
    ranked = [v for v in VALVES if band(sp[v]) != "OUT"]
    if not ranked:
        return {"valves": [], "band": None, "tie": False}
    lo = min(BAND_RANK[band(sp[v])] for v in ranked)
    picks = [v for v in ranked if BAND_RANK[band(sp[v])] == lo]
    label = [k for k, r in BAND_RANK.items() if r == lo][0]
    return {"valves": picks, "band": label, "tie": len(picks) > 1}


def choke_readings(sp, constraints):
    """«تخنق ما بعدها» — تُقرأ **بقيدها** حيث قام قيد يربط الأدنى بما بعده
    على المسار؛ وإلا بقيت وصفَ موضع (`132 §2/④`). لا استدلال درجة↔علاقة."""
    bn = bottleneck(sp)
    out = []
    for v in bn["valves"]:
        i = VALVES.index(v)
        after = set(VALVES[i + 1:])
        codes = [c.code for c in constraints
                 if (c.a == v and c.b in after) or (c.b == v and c.a in after)]
        out.append({"valve": v, "constraints": codes,
                    "reading": "بقيد" if codes else "وصف موضع"})
    return out


# --------------------------------------------------------------------------- #
# 4) المميّز والتحفّظ — `134-K4-DISCRIM`
# --------------------------------------------------------------------------- #
def lookalike_flags(sp):
    """يُرفع سؤال الفرز حين يكون المشهد **ملتبساً فعلاً** — لا كلما ذُكر الزوج."""
    b = {v: band(sp[v]) for v in VALVES}
    flags = []
    if b["PF"] == "limited" and b["F"] == "limited":
        flags.append({"code": "K4-LK-01", "valves": ["PF", "F"]})
    if b["OR"] == "high" and b["PER"] == "limited":
        flags.append({"code": "K4-LK-02", "valves": ["OR", "PER"]})
    if b["TM"] == "limited" and b["PER"] == "limited":
        flags.append({"code": "K4-LK-03", "valves": ["TM", "PER"]})
    return flags


# القطب الزائف المثبت — `134 §3/②` حصراً · وترتيب العرض ترتيب المسار
RESERVE_VALVES = ["F", "OR", "PER"]
RESERVE_CODE = {"PER": "FR-K4-01", "OR": "FR-K4-02", "F": "FR-K4-03"}


def reserve_triggered(sp):
    """يُستدعى التحفّظ **بالنطاق الإسمي** لا برقم (`134 §4/①`)."""
    return [v for v in RESERVE_VALVES if band(sp[v]) == "high"]


# --------------------------------------------------------------------------- #
# 5) خط الأنابيب
# --------------------------------------------------------------------------- #
@dataclass
class Result:
    audit: dict = field(default_factory=dict)
    gap_report: bool = False


def _validate(sp):
    """عقد المدخل — نظيره الحرفي `_validate` في `engines.js`.

    **قيد غير المنتهي (`NaN`/`inf`) مقصود لا تجميلي:** بايثون يقبل
    `float("nan")` بلا استثناء، ثم تسقط المقارنات كلها فيُصنَّف الوعاء
    «قدرة عالية» صامتاً — تصنيفٌ كاذب، ومعه تباعدٌ عن JS الذي يرفض.
    رصده حارس `ح-6` عند بناء المرحلة ٨، فصار الرفض صريحاً في الطرفين.
    """
    missing = [v for v in VALVES if v not in sp]
    if missing:
        raise InputContractError(
            "أوعية ناقصة في المدخل: " + ",".join(missing))
    for v in VALVES:
        try:
            f = float(sp[v])
        except (TypeError, ValueError):
            raise InputContractError(f"قيمة غير عددية للوعاء {v}: {sp[v]}")
        if f != f or f in (float("inf"), float("-inf")):
            raise InputContractError(f"قيمة غير عددية للوعاء {v}: {sp[v]}")


def _round2(x):
    """تصيير صريح (`ن-8`) — لا اتّكال على تصيير اللغة الضمني."""
    return round(float(x) + 0.0, 1)


def run(sp, content=None, strict=False):
    _validate(sp)
    out_valves = [v for v in VALVES if band(sp[v]) == "OUT"]
    constraints = activate_constraints(sp)
    patterns = recognize_patterns(sp)
    bn = bottleneck(sp)
    flags = lookalike_flags(sp)
    reserve = reserve_triggered(sp)

    missing_content = content.missing() if content is not None else []
    if strict and missing_content:
        raise ContentStrictError(missing_content)

    audit = {
        "sp": {v: _round2(sp[v]) for v in VALVES},
        "codes": {v: octal_code(sp[v]) for v in VALVES},
        "bands": {v: band(sp[v]) for v in VALVES},
        "constraints_activated": [c.code for c in constraints],
        "constraint_map": [{"code": c.code, "a": c.a, "b": c.b,
                            "kind": c.kind, "mutual": c.mutual}
                           for c in constraints],
        "patterns_recognized": [p["code"] for p in patterns],
        "interruption_points": interruption_points(sp),
        "bottleneck": bn,
        "choke_readings": choke_readings(sp, constraints),
        "lookalike_flags": [f["code"] for f in flags],
        "reading_reserve": [RESERVE_CODE[v] for v in reserve],
        "excluded_out": out_valves,
        "gap_report": bool(out_valves),
        "engine_version": ENGINE_VERSION,
        "spec_version": SPEC_VERSION,
        "instrument_pin": INSTRUMENT_PIN,
        "missing_content": missing_content,
        # حقول إعلانية مصرَّح بعدم قياسها (`00-HANDOVER §6①` — الاستثناء المعلَن)
        "accepted_debts": ["RSK-018(41)", "GAP-Q-07:9ب≈94ب",
                           "GAP-Q-07:41ب≈45أ", "GAP-Q-07:14ب≈27أ"],
        # مُزامَنة مع سجل التسوية (`DEC-267` · `137 §8`): `GAP-K4-CASES-01`
        # دُمجت في `DEBT-K4-FIELD-01` — والمزامنة يدوية مصرَّح بها.
        "open_debts": ["DEBT-K4-FIELD-01", "GAP-K4-FR-CORE",
                       "GAP-X-EXH-01", "GAP-K4-FR-04"],
    }
    return Result(audit=audit, gap_report=bool(out_valves))


class ContentStrictError(RuntimeError):
    """بوابة `strict` — الإصدار موقوف عند نقص المحتوى (نظير `DEC-240`)."""

    def __init__(self, missing_content):
        self.missing_content = list(missing_content)
        super().__init__(strict_gate_message(self.missing_content))


def strict_gate_message(missing_content):
    """صياغة صريحة موحَّدة (`ن-8`) — نظيرها الحرفي في `engines.js`."""
    body = " · ".join(missing_content) if missing_content else "لا شيء"
    return "بوابة strict — الإصدار موقوف · محتوى مفقود: " + body


if __name__ == "__main__":
    import json
    demo = dict(WM=62, TI=78, F=74, PF=38, OR=55, TM=41, PER=44)
    print(json.dumps(run(demo).audit, ensure_ascii=False, indent=2))
