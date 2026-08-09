# -*- coding: utf-8 -*-
"""
k2_engine.py — محرك تقارير دائرة التفكير (K2)
================================================
ترجمة `56-REPORT-ENGINE v1.2` + طبقة التركيب الأعلى 8/8 إلى كود.
مبنيّ على تشغيلين حقيقيين مُتحقَّقين (P-005 مركز A · P-006 مركز C).

الثوابت الحاكمة (لا تُمسّ):
  * القياس:  SS = x - 2z + y ،  SP = SS/42*100 ،  y+z=7 لكل بُعد.
    (مُثبَت 8/8 مقابل الأداة الإنتاجية — VERIFY-COMPOSE-03.)
  * صفر أوزان/عتبات مستحدثة · صفر تأليف: المحرك مُركِّب لا مؤلِّف.
  * النصوص كلها من حزمة محتوى خارجية معتمدة (k2_content / COMPOSE-*).
  * جدران العزل: K2 حصراً — صفر لمس K1/K3/K4 · قفل P = C + G.
  * قواعد الإخراج: ت-1…ت-8 · DEC-157 · DEC-163 (لا سطر تجميعي).
"""
from dataclasses import dataclass, field
from typing import Optional

ENGINE_VERSION = "0.1"
SPEC_VERSION   = "56-REPORT-ENGINE v1.2"
INSTRUMENT_PIN = "40 v5.0 + 41 v4.2"
MAX_RAW = 42                                   # 7 بنود × 6

LENSES = ["A", "R", "C", "O", "S", "E", "St", "H"]   # الأبعاد الثمانية
LENS_NAME = {"A": "التحليلي", "R": "الواقعي", "C": "المحافظ", "O": "المنظم",
             "S": "الاجتماعي", "E": "المتفهم", "St": "الاستراتيجي", "H": "التصوري"}

# --------------------------------------------------------------------------- #
# 0) عقد المدخل
# --------------------------------------------------------------------------- #
class InputContractError(ValueError):
    """خرق عقد المدخل — إيقاف بلا إصلاح صامت (بروتوكول صفر هلوسة)."""

# --------------------------------------------------------------------------- #
# 1) طبقة الحساب — 41-Raw_Measure §3/§5.2 (مُثبَتة 8/8 · لا تُمسّ)
# --------------------------------------------------------------------------- #
# مصفوفة البنود: لكل بُعد 7 بنود بصيغة (رقم البند، الخيار المحمِّل a/b)
K2_ITEM_MAP = {
    "A":  [(1, "a"), (22, "a"), (40, "a"), (55, "a"), (67, "a"), (76, "a"), (82, "a")],
    "R":  [(1, "b"), (4, "a"),  (25, "a"), (43, "a"), (58, "a"), (70, "a"), (79, "a")],
    "C":  [(4, "b"), (7, "a"),  (22, "b"), (28, "a"), (46, "a"), (61, "a"), (73, "a")],
    "O":  [(7, "b"), (10, "a"), (25, "b"), (31, "a"), (40, "b"), (49, "a"), (64, "a")],
    "S":  [(10, "b"),(13, "a"), (28, "b"), (34, "a"), (43, "b"), (52, "a"), (55, "b")],
    "E":  [(13, "b"),(16, "a"), (31, "b"), (37, "a"), (46, "b"), (58, "b"), (67, "b")],
    "St": [(16, "b"),(19, "a"), (34, "b"), (49, "b"), (61, "b"), (70, "b"), (76, "b")],
    "H":  [(19, "b"),(37, "b"), (52, "b"), (64, "b"), (73, "b"), (79, "b"), (82, "b")],
}


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
    if y + z != 7:
        raise InputContractError(
            f"y+z يجب أن يساوي 7 (y={_num(y)}, z={_num(z)})")
    ss = x - 2 * z + y
    return ss, ss / MAX_RAW * 100.0


def octal_code(sp):
    """حدود الفرز — 41 §5 (حدود ≤ عليا)."""
    if sp < 0:    return "OUT"
    if sp <= 20:  return "L-"
    if sp <= 40:  return "L"
    if sp <= 50:  return "M"
    if sp <= 70:  return "M+"
    if sp <= 85:  return "H"
    if sp <= 100: return "H+"
    return "H++"


def comp_state(sp):
    """حالة العدسة المرافقة في طبقة التركيب — DEC-157.
       D=مهيمنة (SP>70) · M=مساندة (50<SP≤70) · L=منطفئة (SP≤50)."""
    if sp > 70:   return "D"
    if sp > 50:   return "M"
    return "L"


def score_from_raw(raw):
    """raw: dict item(int)->{'choice','ratingA','ratingB'}. يعيد sp لكل بُعد."""
    out = {}
    for d, items in K2_ITEM_MAP.items():
        x = y = 0
        for it, opt in items:
            a = raw[it] if it in raw else raw[str(it)]
            ch = a["choice"]; ra = a["ratingA"]; rb = a["ratingB"]
            x += ra if opt == "a" else rb
            if ch == opt:
                y += 1
        z = 7 - y
        ss, sp = compute_ss_sp(x, y, z)
        out[d] = dict(x=x, y=y, z=z, ss=ss, sp=round(sp, 1), code=octal_code(sp))
    return out

# --------------------------------------------------------------------------- #
# 2) طبقة التصنيف
# --------------------------------------------------------------------------- #
@dataclass
class Profile:
    sp: dict                         # code -> SP float
    center: str = ""
    ranked: list = field(default_factory=list)
    ignited: list = field(default_factory=list)   # SP>50 (عتبة DEC-033)
    dominant: list = field(default_factory=list)   # SP>70
    support: list = field(default_factory=list)    # 50<SP≤70
    off: list = field(default_factory=list)        # SP≤50


def classify(sp: dict) -> Profile:
    # DEF-K2-04 — الفرز على LENSES لا على مفاتيح sp: كسر التعادل يتبع
    # ترتيب جدول 41 §5.2 (A·R·C·O·S·E·St·H) لا ترتيب إدخال المستدعي.
    ranked = sorted(LENSES, key=lambda d: sp[d], reverse=True)
    p = Profile(sp=sp, center=ranked[0], ranked=ranked)
    for d in ranked:
        s = comp_state(sp[d])
        (p.dominant if s == "D" else p.support if s == "M" else p.off).append(d)
        if sp[d] > 50:
            p.ignited.append(d)
    return p

# --------------------------------------------------------------------------- #
# 3) طبقة التركيب الأعلى — المعاجم الثمانية (DEC-159/163/173/174)
# --------------------------------------------------------------------------- #
# مجموعة تغطية كل مركز (حلفاء العمى) — البقية أسطر تلوين
COVERAGE = {
    "E":  ["O"],
    "H":  ["A", "R", "O"],
    "C":  ["H", "St"],
    "S":  ["A", "St"],
    "St": ["R", "O"],
    "R":  ["A", "St"],
    "A":  ["E", "O", "R"],     # DEC-173 (ثلاثية)
    "O":  ["H", "St", "R"],    # DEC-174 (ثلاثية)
}
# بنية العمى لـ ت-8: قائمة (اسم النصف، حلفاء تغطيته)
BLINDNESS = {
    "E":  [("ذوبان الحدود", ["O"])],
    "H":  [("تشتت الخيارات وغياب التأريض", ["A", "R", "O"])],
    "C":  [("كلفة عدم التغيير", ["H", "St"])],
    "S":  [("تمييع الحقيقة", ["A", "St"])],
    "St": [("الانفصال عن اللحظة", ["R", "O"])],
    "R":  [("السطحية/غياب الجذر", ["A"]), ("تجهيل المستقبل", ["St"])],
    "A":  [("شلل المعالجة", ["O", "R"]), ("إغفال الإشارة الوجدانية", ["E"])],
    "O":  [("تقادم القالب", ["St", "H"]), ("الجمود عند الكسر", ["R", "H"])],
}


@dataclass
class Line:
    code: str          # مثال C-St-D
    lens: str          # العدسة المرافقة
    kind: str          # "coverage" | "coloring"
    state: str         # D | M | L
    layer: str         # "delivery" | "review"  (ت-7)


def compose(profile: Profile) -> list:
    """استدعاء أسطر معجم المركز — سطر واحد لكل عدسة مرافقة (DEC-157)."""
    c = profile.center
    allies = COVERAGE[c]
    lines = []
    for lens in LENSES:
        if lens == c:
            continue
        st = comp_state(profile.sp[lens])
        kind = "coverage" if lens in allies else "coloring"
        # ت-7: تُنتقى للتسليم أسئلة الحالات المنطفئة (L) وحدها؛ الباقي للمراجعة
        layer = "delivery" if st == "L" else "review"
        lines.append(Line(f"{c}-{lens}-{st}", lens, kind, st, layer))
    return lines


def t8_conditioning(profile: Profile) -> list:
    """ت-8 (DEC-178): تكييف نص العمى بحالة تغطيته — لكل نصف عمى على حدة."""
    c = profile.center
    out = []
    for half_name, allies in BLINDNESS[c]:
        states = [comp_state(profile.sp[a]) for a in allies]
        if all(s == "D" for s in states):
            verdict, phrase = "covered", f"حدّ بنيوي يغطّيه ملفك داخلياً عبر {'·'.join(allies)}"
        elif all(s == "L" for s in states):
            verdict, phrase = "exposed", f"مكشوف — التغطية خارجية بيني عبر {'·'.join(allies)}"
        else:
            present = [a for a in allies if comp_state(profile.sp[a]) != "L"]
            absent  = [a for a in allies if comp_state(profile.sp[a]) == "L"]
            phrase = f"مُغطّى غالباً عبر {'·'.join(present)}"
            if absent:
                phrase += f"، ومكشوف من جهة {'·'.join(absent)}"
            verdict = "partial"
        out.append(dict(half=half_name, allies=allies,
                        states=dict(zip(allies, states)), verdict=verdict, phrase=phrase))
    return out


def fric02_stitch(profile: Profile, t8: list) -> Optional[str]:
    """FRIC-COMPOSE-02: خيط سرد غير تفسيري عند تعدّد الحلفاء المنطفئين.
       يحترم DEC-163 (سرد بلا وزن)."""
    exposed = [h for h in t8 if h["verdict"] == "exposed"]
    off_allies = sorted({a for h in exposed for a in h["allies"]})
    if len(off_allies) >= 2:
        return f"تغطية العمى خارجية بالكامل عبر {'·'.join(off_allies)} (سرد لا ترجيح)."
    return None

# --------------------------------------------------------------------------- #
# 4) تدقيق العزل — جدران K1/K3/K4 + قفل P=C+G
# --------------------------------------------------------------------------- #
_FORBIDDEN = (
    # ألفاظ مفردة — لا تُطلق كاذباً (مقيس على 49 حالة)
    "K3", "K4", "استثارة", "شفقة", "تنفيذ ميداني", "إدارة وقت",
    "علاج", "تشخيص", "اضطراب", "مرض",
    # DEC-214 — «انفعال» عبارات مركّبة: تلتقط الخلط لا الذكر المشروع.
    # «الانفعال دائرة أخرى» (E/U-11) إنفاذ للقفل لا خرق له.
    "انفعالك", "انفعاله", "انفعالها", "درجة انفعال", "شدة الانفعال",
    "مستوى انفعال", "أنت منفعل", "تنفعل بسرعة", "الانفعال لديك")


def audit_isolation(*texts) -> list:
    hits = []
    for t in texts:
        if not t:
            continue
        for w in _FORBIDDEN:
            if w in t:
                hits.append(w)
    return hits

# --------------------------------------------------------------------------- #
# 5) التشغيل
# --------------------------------------------------------------------------- #
@dataclass
class Result:
    profile: Profile
    lines: list
    t8: list
    delivery_questions: list        # أكواد أسطر التسليم (ت-7)
    stitch: Optional[str]
    audit: list


def run(sp=None, raw=None, content=None, strict=False) -> Result:
    if sp is None:
        if raw is None:
            raise InputContractError("مطلوب sp أو raw")
        scored = score_from_raw(raw)
        sp = {d: v["sp"] for d, v in scored.items()}
    if set(sp) != set(LENSES):
        raise InputContractError(
            "الأبعاد يجب أن تكون الثمانية بالضبط: " + " · ".join(LENSES))
    prof = classify(sp)
    lines = compose(prof)
    t8 = t8_conditioning(prof)
    delivery = [ln.code for ln in lines if ln.layer == "delivery"]
    stitch = fric02_stitch(prof, t8)
    # التدقيق يفحص المخرجات النصية المستدعاة (عند تمرير حزمة محتوى)
    audit = audit_isolation(*(content.texts_for(prof) if content else []))
    if strict and audit:
        raise InputContractError("خرق عزل: " + " · ".join(audit))
    return Result(prof, lines, t8, delivery, stitch, audit)

# --------------------------------------------------------------------------- #
# 6) اختبار ذاتي — الحالتان الحقيقيتان المُتحقَّقتان
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    # P-005 (مركز A · حلفاء منطفئون → عمى مكشوف)
    P005 = {"A": 95.2, "S": 73.8, "H": 61.9, "St": 54.8,
            "C": 52.4, "R": 47.6, "E": 42.9, "O": 38.1}
    # P-006 (مركز C · St مهيمن → عمى مُغطّى)
    P006 = {"C": 97.6, "O": 90.5, "E": 78.6, "St": 76.2,
            "R": 73.8, "H": 64.3, "A": 54.8, "S": 33.3}

    for tag, sp in [("P-005", P005), ("P-006", P006)]:
        r = run(sp=sp)
        print(f"\n===== {tag} =====")
        print("المركز:", r.profile.center, LENS_NAME[r.profile.center],
              "| مهيمنون:", r.profile.dominant, "| منطفئون:", r.profile.off)
        print("الأسطر المستدعاة:")
        for ln in r.lines:
            print(f"  {ln.code:<8} [{ln.kind:<8}] → {ln.layer}")
        print("ت-8:")
        for h in r.t8:
            print(f"  • {h['half']}: {h['verdict']} — {h['phrase']}")
        print("أسئلة التسليم (ت-7):", r.delivery_questions)
        print("خيط FRIC-02:", r.stitch or "—")
        print("تدقيق العزل:", r.audit or "نظيف")

    # تحققات صريحة (تجميد سلوك المحرك)
    ra = run(sp=P005); rc = run(sp=P006)
    assert ra.profile.center == "A"
    assert rc.profile.center == "C"
    # P-005: نصفا عمى A مكشوفان (O,R,E كلها L)
    assert all(h["verdict"] == "exposed" for h in ra.t8)
    assert ra.stitch is not None                       # خيط FRIC-02 يُفعَّل
    # P-006: عمى C مُغطّى/مختلط (St=D)
    assert rc.t8[0]["verdict"] in ("covered", "partial")
    assert rc.stitch is None
    # ت-7: أسئلة التسليم = الحالات المنطفئة فقط
    assert set(ra.delivery_questions) == {"A-E-L", "A-O-L", "A-R-L"}
    assert set(rc.delivery_questions) == {"C-S-L"}
    print("\n✅ كل التحققات مرّت — سلوك المحرك مُجمَّد على الحالتين الحقيقيتين.")
