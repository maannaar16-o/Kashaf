# -*- coding: utf-8 -*-
"""
k2_report.py — مُركّب التقرير الفردي (K2) v0.2
================================================
56-REPORT-ENGINE v1.2 §5.1 + طبقة التركيب الأعلى (ت-1…ت-8).

v0.2: وصل حزمة 55-USER-K2 (الكتالوج/البصمة) — تقرير كامل بلا وسوم انتظار
      للمراكز المتاحة. قرار نقاء: **العمى يُقرأ من طبقة التركيب (ت-8) لا من
      الكتالوج** (تفادي تناقض FRIC-03) — فالكتالوج يعرض الدورة/المحرك/الموقع/البصمة.
🔒 يجمّع ولا يؤلّف. ما ليس في مصدر معتمد يُوسَم خارجياً ولا يُختلق.
"""
import hashlib
import math
import re
import os, json
from k2_engine import (run, LENS_NAME, octal_code, comp_state, audit_isolation,
                       ENGINE_VERSION, SPEC_VERSION, INSTRUMENT_PIN)
from k2_content import ContentPack
import k2_framing as F
from sp_gate import output_gate            # ح-4 · DEC-183 · ن-7

_HERE = os.path.dirname(os.path.abspath(__file__))
AR_NUM = "١٢٣٤٥٦٧٨٩"

PCG_LOCK = ("الدرجة تصف موقع العدسة في ترتيب تفضيلك المعرفي الفطري، "
            "لا مستوى قدرتك ولا جودة أدائك. لا درجة «أفضل» — يوجد نمط مختلف.")

# مداخل الكتالوج المعروضة (العمى مُستثنى — يأتي من التركيب)
# DEF-K2-01 — استدعاء بالوظيفة لا بالرقم (51-MATRIX-06 R3)
# DEC-211/ج₂ — الأنماط الأربعة تامّة التغطية + الآلية الخاصة
FILTER_KW = ["قاعدة الإهمال", "قاعدة الاختزال", "قاعدة الحجب", "صانع الشكل",
             "العدسة الأفقية", "القراءة الهادئة", "العدسة التوسيعية"]
MECH_KW = ["الملاذ الإبداعي", "الحس الزمني", "سلطة الاعتراض", "المنطق الاقتصادي",
           "المغلِّف لا المصدر", "الرادار لا يُستغَل", "المخرج إمكان لا قرار"]

SLOT_KW = {"CYCLE": "دورة المعالجة", "ENGINE": "المحرك",
           "POSITION": "الموقع في الفريق", "BLIND": "نقطة العمى",
           "PRESSURE": "الضغط القصوى", "FOOTPRINT": "البصمة",
           "NOTMINE": "ما لا تعنيه"}
CENTER_SLOTS  = ["CYCLE", "ENGINE", "POSITION"]
SUPPORT_SLOTS = ["CYCLE", "ENGINE", "POSITION"]
FOOTPRINT_SLOT = "FOOTPRINT"

class SlotResolutionError(RuntimeError):
    """فشل حلّ وظيفة إلى مدخل — إيقاف صريح لا صمت (بروتوكول صفر هلوسة)."""

# عدد المداخل المتوقَّع لكل وظيفة: 1 إلزامي · BLIND 1–2 · NOTMINE 0–1
_CARD = {"CYCLE": (1, 1), "ENGINE": (1, 1), "POSITION": (1, 1),
         "BLIND": (1, 2), "PRESSURE": (1, 1), "FOOTPRINT": (1, 1),
         "NOTMINE": (0, 1)}


def resolve_by(dim, keywords):
    """يعيد المداخل المطابقة لأي كلمة من القائمة — استدعاء بالوظيفة (R3)."""
    return [k for k in sorted(USERLAYER.get(dim, {}))
            if any(w in USERLAYER[dim][k]["title"] for w in keywords)]


def slot_filter(dim):    return resolve_by(dim, FILTER_KW)
def slot_noise(dim):     return resolve_by(dim, ["الإزعاج"])
def slot_others(dim):    return resolve_by(dim, ["قراءة الآخرين"])
def slot_economy(dim):   return resolve_by(dim, ["اقتصاد الطاقة"])
def slot_mech(dim):      return resolve_by(dim, MECH_KW)


def resolve_slot(dim, slot, strict=True):
    kw = SLOT_KW[slot]
    hits = [k for k in sorted(USERLAYER.get(dim, {}))
            if kw in USERLAYER[dim][k]["title"]]
    lo, hi = _CARD[slot]
    if strict and not (lo <= len(hits) <= hi):
        raise SlotResolutionError(
            f"DEF-K2-01/حارس: البُعد {dim} · الوظيفة {slot} → {len(hits)} مدخلاً "
            f"(المتوقَّع {lo}..{hi}). لا يُخمَّن مدخل — يُصدر تقرير فجوة.")
    return hits


def validate_slots():
    """فحص شامل قبل أي إصدار — يعيد قائمة الشذوذ (فارغة = سليم)."""
    out = []
    for d in USERLAYER:
        for sl in SLOT_KW:
            try:
                resolve_slot(d, sl)
            except SlotResolutionError as e:
                out.append(str(e))
    return out

def _load(path):
    return json.load(open(path, encoding="utf-8")) if os.path.exists(path) else None

USERLAYER = _load(os.path.join(_HERE, "k2_userlayer_pack.json"))


PUR = json.load(open(os.path.join(_HERE, "k2_pur.json"), encoding="utf-8"))["PUR"]
INTENSITY = json.load(open(os.path.join(_HERE, "k2_intensity.json"), encoding="utf-8"))["S"]
LOOKALIKE = json.load(open(os.path.join(_HERE, "k2_lookalike.json"), encoding="utf-8"))["LD"]

R11_TAG = "[تجاور عاملي موثق — حزمة توليد-توجيه]"


def r11_block(profile):
    """R11 — العرض المزدوج St+H عند اشتعالهما معاً (SP>50٪ لكليهما).
    حسم M-07/الخيار ج: وسم الحزمة · LD-02 تفسيرياً · **حظر الفصل الرقمي**."""
    if not (profile.sp["St"] > 50 and profile.sp["H"] > 50):
        return []
    ld = LOOKALIKE["LD-02"]
    _USED.append("LD-02")                 # DEC-222
    return [f"> وسم إلزامي: {R11_TAG}", "",
            f"- **{LENS_NAME['H']} (H):** {ld['second']}",
            f"- **{LENS_NAME['St']} (St):** {ld['first']}",
            "",
            f"> {ld['question']}",
            "> يُقرآن حزمةً واحدة لا عدستين منفصلتين — ويُحظر فصل إسهامهما رقمياً.", ""]

# رمز المحرك «L-» يقابل «L−» في الحزمة (شرطة ناقص U+2212)
_BAND_ALIAS = {"L-": "L−"}


def intensity_block(dim, code):
    """R1 — كتلة الشدة للبُعد وفق رمزه. يوقف الإصدار عند غياب الكتلة (ن-7)."""
    key = _BAND_ALIAS.get(code, code)
    b = INTENSITY.get(dim, {}).get(key)
    if b is not None:
        _USED.append(b["code"])           # DEC-222 — K2-X-S-{band}
    if b is None:
        raise SlotResolutionError(
            f"R1/حارس: كتلة الشدة K2-{dim}-S-{key} غائبة — لا تُخمَّن.")
    return b


LOCK_PREFIX = "  > 🔒 "


LOCK_REGISTRY = json.load(open(os.path.join(_HERE, "k2_lock_registry.json"),
                               encoding="utf-8"))["ACCEPTED_LOCK_MENTIONS"]


def scan_lock_fields():
    """DEC-229 — حقول القفل مستثناة من بوابة المخرج (DEC-217/ب)، فتُفحص
    عند المحتوى: أي ذِكر لمصطلح محظور **خارج السجلّ المقبول** يُرصد.
    لا يحكم على المشروعية — يرصد **الاستجداد** وحده."""
    from k2_engine import _FORBIDDEN
    hits = []
    for d, bands in INTENSITY.items():
        for band, v in bands.items():
            lock = v.get("lock", "")
            if not lock:
                continue
            code = v["code"]
            terms = ([w for w in _FORBIDDEN if w in lock]
                     + [r["forbidden"] for r in PUR.get(d, []) if r["forbidden"] in lock])
            for t in terms:
                if f"{code}|{t}" not in LOCK_REGISTRY:
                    hits.append({"check": "قفل-مستجدّ", "unit": code, "term": t[:40]})
    return hits


def scan_lock_drift():
    """`ح-7` (`DEC-241`) — سلامة الصياغة المسجَّلة داخل حقل القفل.

    `scan_lock_fields` يرصد **الاستجداد** (ذِكرٌ بلا مفتاح). وهذا يرصد
    **الانقلاب**: تغيير صياغة ذِكرٍ **مسجَّل** من نفيٍ/فصلٍ إلى إثبات —
    «لا تشخيص» ← «تشخيص» (`GAP-LOCK-01`).

    يقيس شيئاً واحداً: **أن الصياغة المعتمدة ما زالت تحكم كل ظهور
    للمصطلح في هذا القفل**. شرطان لا ينفصلان:
      ① السياق المسجَّل حاضر **حرفياً** في نصّ القفل الحالي.
      ② كل ظهور للمصطلح واقعٌ **داخل** ذلك السياق (تكرار متساوٍ)،
         فلا ينفع إلحاق ذِكرٍ ثانٍ خلف السياق المعتمد.

    **حدّه مُصرَّح به:** لا يحكم على المعنى. يُثبت أن الصياغة المعتمدة
    لم تتغيّر، لا أن المعنى صحيح — والحكم الدلالي خارج قدرة الأتمتة.
    وقد تحرّى الفحص أداة النفي فتبيّن أن **قفلين من ثلاثة** يستعملان
    الفصل بـ`≠` لا النفي؛ فاعتماد أداة النفي معياراً كان سيُنتج
    إنذارين كاذبين من ثلاثة.
    """
    hits = []
    for d, bands in INTENSITY.items():
        for band, v in bands.items():
            lock = v.get("lock", "")
            if not lock:
                continue
            code = v["code"]
            for key, entry in LOCK_REGISTRY.items():
                if not key.startswith(f"{code}|"):
                    continue
                term, ctx = entry["term"], entry["context"]
                if ctx not in lock:
                    hits.append({"check": "قفل-منجرف", "unit": code,
                                 "term": term[:40], "why": "الصياغة المسجَّلة غائبة"})
                elif lock.count(term) != ctx.count(term):
                    hits.append({"check": "قفل-منجرف", "unit": code,
                                 "term": term[:40], "why": "ذِكرٌ خارج الصياغة المسجَّلة"})
    return hits


def strip_locks(text):
    """DEC-217/ب — أسطر الأقفال تُستثنى من البوابة.
    القفل نصّ تحصين يُصاغ **بذكر** المصطلح المحظور ليمنع الخلط؛
    فحصُه يقلب غرضه. يعيد (النصّ المفحوص، عدد الأسطر المستثناة)."""
    kept, n = [], 0
    for ln in text.split("\n"):
        if ln.startswith(LOCK_PREFIX):
            n += 1
        else:
            kept.append(ln)
    return "\n".join(kept), n


def _content_words(t):
    """كلمات المحتوى (4 أحرف فأكثر) — بلا حروف الوصل القصيرة."""
    return set(re.findall(r"[\u0600-\u06FF]{4,}", t))


def _round2(v):
    """تقريب موحَّد لمنزلتين (`DEC-238`) — **نصفٌ لأعلى** بصيغة صريحة.
    `round()` البايثونية تقرّب مصرفياً (نحو الزوجي) و`Math.round` تقرّب
    نصفاً لأعلى؛ فأعطتا `0.12` مقابل `0.13` عند `0.125`. الصيغة أدناه
    متطابقة بتاً في اللغتين (IEEE-754) ولا تتّكل على سلوك أيّهما.
    تُطبَّق على نسب غير سالبة."""
    return math.floor(v * 100 + 0.5) / 100

def t6_guard(delivery_lines, called_units):
    """ت-6 — أي سطر تسليم يطابق مضموناً وحدةً مستدعاة أصلاً يُنقل للمراجعة.

    **بلا عتبة مخترعة:** يوقف الإصدار عند **الاحتواء التامّ** وحده
    (كلمات السطر كلها داخل الوحدة)، ويُبلِّغ أقصى تداخل مقيس ليُبنى
    عليه قرار العتبة إن أُريد (DEC-224).
    """
    hits, worst = [], 0.0
    for ln in delivery_lines:
        w = _content_words(ln)
        if not w:
            continue
        for unit in called_units:
            wu = _content_words(unit)
            if not wu:
                continue
            ratio = len(w & wu) / len(w)
            worst = max(worst, ratio)
            if ratio >= 1.0:                      # احتواء تامّ — لا اجتهاد
                hits.append({"check": "ت-6", "line": ln[:50], "unit": unit[:50]})
                break
    return hits, _round2(worst)


def pur_gate(text, dims):
    """R9 — بوابة التطهير (DEC-212/ب): مطابقة العبارة المحظورة **كاملة**.
    الشظايا مرفوضة بالقياس: 100% إنذار كاذب (96-GAP-RPT-K2-02 §3)."""
    hits = []
    for d in dims:
        for row in PUR.get(d, []):
            if row["forbidden"] in text:
                hits.append({"dim": d, "check": "PUR", "token": row["forbidden"][:40],
                             "alt": row["alt"][:60]})
    return hits


def pur_scan_packs(dims):
    """المرحلة الأولى — فحص الحزم عند التحميل (نظير g5_scan_content في K3)."""
    hits = []
    for d in dims:
        for code, e in (USERLAYER.get(d) or {}).items():
            for row in PUR.get(d, []):
                if row["forbidden"] in str(e.get("user", "")):
                    hits.append({"dim": d, "entry": code, "token": row["forbidden"][:40]})
    return hits


def _board(profile):
    # DEC-183: لا SP في الشاشة ولا في أي تصدير · DEC-187: الحالة بالكلمة + الرمز
    rows = ["| البُعد | الرمز | الحالة |", "| :-- | :--: | :-- |"]
    st = {"D": "مهيمنة", "M": "مساندة", "L": "منطفئة"}
    for d in profile.ranked:
        sp = profile.sp[d]
        tag = "🎯 المركز" if d == profile.center else st[comp_state(sp)]
        rows.append(f"| {LENS_NAME[d]} ({d}) | {octal_code(sp)} | {tag} |")
    return "\n".join(rows)


_USED = []


def _catalog(dim, entries):
    """يعيد نصوص 🗣️ للمداخل المطلوبة من حزمة المستخدم، أو None إن غابت."""
    if not USERLAYER or dim not in USERLAYER:
        return None
    out = []
    for code in entries:
        e = USERLAYER[dim].get(code)
        if e and e.get("user"):
            _USED.append(f"K2-{dim}-{code}")
            out.append(f"- **{e['title'].split('(')[0].strip()}:** {e['user']}")
    return out or None


# DEC-225/و — نطاقا العرض. لا قاعدة مخترعة: brief = R2/R3 كما وردا حرفياً
# (المركز كتالوجاً كاملاً · الرتبتان 2–3 بالوظائف الخمس · الباقي لا شيء)،
# وfull = توزيع DEC-211/ج₂. الاستدعاء واحد؛ النطاق وحده يختلف.
MODES = ("full", "brief")


def build_report(sp, pack=None, mode="full"):
    global _USED
    _USED = []                                    # DEC-220 — تتبّع لكل بناء
    pack = pack or ContentPack()
    res = run(sp, content=pack)
    c = res.profile.center
    L, n = [], 0
    ext_pending = []

    def head(t):
        nonlocal n
        n += 1
        L.append(f"## {AR_NUM[n-1]} · {t}")
        L.append(F.open_section(t))          # ج-1 (الملحق أ · مغلق)
        L.append("")

    def ext(t, key):
        ext_pending.append(key); head(t)
        # DEC-210 — قالب ج-4 المعتمد: «وسم إلزامي: [نص الوسم]»
        L += [f"> وسم إلزامي: [محتوى خارجي — {key} — بانتظار الحزمة]", ""]

    # ① قبل أن تقرأ
    head("قبل أن تقرأ"); L += [f"> {PCG_LOCK}", ""]

    # ② لوحة الرموز + R1 كتل الشدة الثماني (إلزامية — صورة كاملة)
    head("لوحة رموزك الثمانية"); L += [_board(res.profile), ""]
    L += ["**ماذا يعني رمز كل عدسة عندك:**", ""]
    for d in res.profile.ranked:
        b = intensity_block(d, octal_code(res.profile.sp[d]))
        L.append(f"- **{LENS_NAME[d]} ({d}) — {b['code'].split('-')[-1]}"
                 + (f" · {b['label']}" if b["label"] else "") + ":** " + b["user"])
        if b["lock"]:
            L.append(f"  > 🔒 {b['lock']}")
    L.append("")

    # ③ مركزك
    cat = _catalog(c, [k for sl in CENTER_SLOTS for k in resolve_slot(c, sl)])
    head(f"مركزك — {LENS_NAME[c]}")
    if cat: L += cat + [""]
    else:   ext_pending.append(f"55-USER-K2-{c}"); L += ["> وسم إلزامي: [كتالوج المركز — خارجي]", ""]

    # ④ عدساتك المهيمنة والمساندة (المهيمنون غير المركز)
    # DEF-K2-03 — استبعاد المركز من الطرفين: قد يقع في support إن كان SP ≤ 70
    others = [d for d in res.profile.dominant + res.profile.support if d != c]
    if others:
        head("عدساتك المهيمنة والمساندة")
        for d in others:
            sc = _catalog(d, [k for sl in SUPPORT_SLOTS for k in resolve_slot(d, sl)])
            L.append(f"### {LENS_NAME[d]} ({d}) — {octal_code(res.profile.sp[d])}")
            L += (sc if sc else ["> وسم إلزامي: [محتوى خارجي]"]) + [""]

    # العدسات المعروضة — المركز + المهيمنة + المساندة (المنطفئة لها معاملتها في ⑨)
    # brief: المركز وحده يتوسّع (R2)؛ الرتبتان 2–3 اكتفتا بالوظائف الخمس في ④ (R3)
    shown = [c] if mode == "brief" else [c] + others

    # ⑤ كيف تتركّب عدساتك — ت-8 · FRIC-02 · التغطية/التلوين · قاعدة الفلترة
    head("كيف تتركّب عدساتك")
    L += ["**نقطة عماك — مقروءةً مع ملفك (ت-8):**", ""]
    for h in res.t8:
        L.append(f"- {h['half']}: {h['phrase']}.")
    if res.stitch: L += ["", f"> {res.stitch}"]
    L.append("")
    cov = [ln for ln in res.lines if ln.kind == "coverage"]
    col = [ln for ln in res.lines if ln.kind == "coloring"]
    L += ["**تغطية عماك عبر عدساتك:**", ""] + [f"- {pack.get_line(x.code)['presence']}" for x in cov]
    L += ["", "**كيف تلوّن عدساتك تعبيرك:**", ""] + [f"- {pack.get_line(x.code)['presence']}" for x in col]
    L.append("")
    L += ["**ما تُسقطه كل عدسة قبل أن تعالج · ونقطة عماها:**", ""]
    for d in shown:
        e = _catalog(d, slot_filter(d) + resolve_slot(d, "BLIND"))
        if e: L.append(f"### {LENS_NAME[d]} ({d})"); L += e + [""]

    # ⑥ حين تلتقي عدستان — قراءة الآخرين + مصفوفات R4/R5/R6/R8
    head("حين تلتقي عدستان")
    r11 = r11_block(res.profile)
    if r11:
        L += ["**حين يشتعل التوليد والتوجيه معاً (R11):**", ""] + r11
    L += ["**كيف تقرأ من أمامك بكل عدسة:**", ""]
    for d in shown:
        e = _catalog(d, slot_others(d))
        if e: L.append(f"### {LENS_NAME[d]} ({d})"); L += e + [""]

    # ⑦ تحت الضغط — حالة الضغط القصوى + الإزعاج
    head("تحت الضغط")
    for d in shown:
        e = _catalog(d, resolve_slot(d, "PRESSURE") + slot_noise(d))
        if e: L.append(f"### {LENS_NAME[d]} ({d})"); L += e + [""]

    # ⑧ أسئلة تخصّك (ت-7)
    head("أسئلة تخصّك وحدك")
    # DEC-207/ب — ج-5 من القائمة المغلقة حين لا عدسة منطفئة
    if res.delivery_questions:
        L += ["> هذه أسئلة تساعدك على قراءة ما سبق بنفسك — لا أحكام.", ""]
    else:
        L += ["> ملاحظة تخادم: راجع مقطع كيف تتركّب عدساتك.", ""]
    L += [f"- {pack.get_line(code)['question']}" for code in res.delivery_questions] + [""]

    # ⑨ نقاط عماك · بصمتك — البصمة · ما لا تعنيه · اقتصاد الطاقة · الآلية الخاصة
    head("نقاط عماك · بصمتك")
    if res.profile.off:
        L += ["> غياب أولوية لا نقص — تُغطّى بالتخادم لا بالإصلاح الذاتي (P = C + G).", ""]
        for d in res.profile.off:
            L.append(f"- **{LENS_NAME[d]} ({d})** منطفئة ({octal_code(res.profile.sp[d])}).")
        L.append("")
    for d in shown:
        e = _catalog(d, resolve_slot(d, FOOTPRINT_SLOT) + resolve_slot(d, "NOTMINE", strict=False)
                        + slot_economy(d) + slot_mech(d))
        if e: L.append(f"### {LENS_NAME[d]} ({d})"); L += e + [""]
        elif d == c: ext_pending.append(f"55-USER-K2-{c}/البصمة"); L += ["> وسم إلزامي: [محتوى خارجي]", ""]

    # R10 — الوسمان الإجرائيان الملازمان لكل مخرج (51-MATRIX-06 §15 · DEC-219)
    # يُصبّان في قالب ج-4 المعتمد: «وسم إلزامي: [نص الوسم]»
    L += ["", "> وسم إلزامي: [توحيد تشغيلي مؤقت — GAP-A-01 — قابل للترقية]",
          "> وسم إلزامي: [توحيد تشغيلي مؤقت — GAP-A-02 — قابل للمراجعة]"]

    L += ["", F.close_report()]              # ج-6 (الختام المعتمد)

    # ت-6 (DEC-224) — التطابق المضموني بين أسطر التسليم والوحدات المستدعاة
    _delivery_lines = [pack.get_line(x.code)["presence"] for x in res.lines]
    _called_units = ([intensity_block(d, octal_code(res.profile.sp[d]))["user"]
                      for d in res.profile.ranked]
                     + [USERLAYER[c][k]["user"] for k in
                        [x for sl in CENTER_SLOTS for x in resolve_slot(c, sl)]
                        if USERLAYER.get(c, {}).get(k, {}).get("user")])
    t6_hits, t6_worst = t6_guard(_delivery_lines, _called_units)

    # R9 — البوابة على كامل المخرج قبل الإصدار (DEC-213)
    text_out = "\n".join(L)
    scanned, locks_excluded = strip_locks(text_out)   # DEC-217/ب
    dims_called = [c] + others
    gate = audit_isolation(scanned) + pur_gate(scanned, dims_called) \
        + pur_scan_packs(dims_called) + scan_lock_fields() \
        + scan_lock_drift()                        # DEC-229 · ح-7 DEC-241

    # DEC-220 — عقد إعادة التوليد: sp + النسخ + بصمات الحزم + بصمة المخرج
    _sha = lambda o: hashlib.sha256(
        json.dumps(o, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        .encode("utf-8")).hexdigest()[:16]
    pack_sha = {"USERLAYER_K2": _sha(USERLAYER), "PUR_K2": _sha(PUR),
                "INTENSITY_K2": _sha(INTENSITY), "LOOKALIKE_K2": _sha(LOOKALIKE),
                "CONTENT_K2": _sha(getattr(pack, "_pack", {}))}   # DEC-223

    audit = dict(sp={d: round(sp[d], 1) for d in sorted(sp)},
                 engine_version=ENGINE_VERSION, spec_version=SPEC_VERSION,
                 instrument_pin=INSTRUMENT_PIN,
                 entries_used=sorted(set(_USED
                     + [x.code for x in res.lines]          # DEC-222 — أسطر التركيب
                     + [f"PUR-{d}" for d in dims_called])), # القواميس المستشارة
                 pack_sha=pack_sha,
                 report_sha256=hashlib.sha256(text_out.encode("utf-8")).hexdigest()[:16],
                 mode=mode, sections_rendered=n, center=c, composition_lines=len(res.lines),
                 r9_gate=gate or "clean",
                 r9_locks_excluded=locks_excluded,
                 lock_registry_size=len(LOCK_REGISTRY),
                 r10_tags=["GAP-A-01", "GAP-A-02"],
                 # DEC-245 — إعلان حالة الديون، نظيرَ ما في $K_3$.
                 # **إعلانٌ لا قياس**: مستخرَج من `02-MASTER`، لا يُحسب من الكود.
                 #   accepted: `DEBT-K2-BALANCE-01` مقبول (`DEC-243`) ·
                 #             `GAP-LOCK-01` حدُّه الدلالي مُعلَن ومقبول (`DEC-241`)
                 #   open   : فارغ — لا دَين مفتوح يمسّ **التقرير الفردي**.
                 #             `GAP-K2-TEAMBLIND-01` مفتوح لكنه **نطاق الفريق** لا الفرد.
                 #   ويُستثنى `GAP-A-01`/`GAP-A-02` — مُعلَنان أصلاً في `r10_tags`.
                 accepted_debts=["DEBT-K2-BALANCE-01", "GAP-LOCK-01"],
                 open_debts=[],
                 t6_gate=t6_hits or "clean", t6_max_overlap=t6_worst,
                 delivery=res.delivery_questions,
                 t8=[(h["half"], h["verdict"]) for h in res.t8],
                 fric02=bool(res.stitch), isolation=res.audit or "clean",
                 external_pending=sorted(set(ext_pending)))
    _out = "\n".join(L)
    output_gate(_out, f"تقرير K2 · {mode}")      # ح-4 — يوقف الإصدار عند تسرّب SP%
    return _out, audit


if __name__ == "__main__":
    golden = json.load(open(os.path.join(_HERE, "golden_k2.json"), encoding="utf-8"))
    for name in ("P-005", "P-006"):
        txt, a = build_report(golden[name]["sp"])
        print("\n" + "#" * 78)
        print(f"# {name} — مركز {a['center']} · أقسام {a['sections_rendered']} · تركيب {a['composition_lines']}"
              f" · تسليم {len(a['delivery'])} · عزل {a['isolation']}")
        print(f"# خارجي منتظر: {a['external_pending'] or 'لا شيء ✅'}")
        print("#" * 78)
        print(txt)
