# -*- coding: utf-8 -*-
"""
k3_guard.py — حارس سلامة مخرج K3 (نظير validate_slots في K2)
سند: ن-7 (DEC-193) · الفحص 10 · بروتوكول صفر هلوسة البند 10
المبدأ: يوقف الإصدار عند الشذوذ ولا يعود بقيمة فارغة صامتة.
"""
import json, os, re

_HERE = os.path.dirname(os.path.abspath(__file__))
_J = lambda n: json.load(open(os.path.join(_HERE, n), encoding="utf-8"))

SKILLS = ["EP", "IR", "BI", "CF", "ST"]

# ربط صريح: المفتاح ← العنوان الذي يُعرض تحته (55-USER-K3-* §1)
SLOT_BINDING = {
    "U01": "الوظيفة المركزية — يُفتتح به كل قسم مهاري",
    "U08": "إشارات القوة — تحت «ما يظهر عندك» (core/high)",
    "U09": "إشارات تحتاج انتباهاً — تحت «ما يحتاج انتباهاً» (limited)",
    "U10": "حالة الضغط القصوى — تحت فرع OUT",
}
# كل مخرج ممكن من band() يجب أن يقابله وسم صريح — لا افتراضي صامت
BANDS_REQUIRED = {"limited", "core", "high", "OUT"}
BAND_LABELS_APPROVED = {          # DEC-064 · DEC-133 · 80-K3-TEXTS
    "limited": "حضور محدود", "core": "كفاءة أساسية",
    "high": "قدرة عالية", "OUT": "قراءة خاصة",
}
# توقيع الخاتمة الخاصة بكل ملف (79-K3-USERMAP §2.2) — لا تجوز في قسم عام
TAIL_SIGNATURE = "وهذه المهارة"


class K3IntegrityError(RuntimeError):
    """شذوذ يمنع الإصدار — يُصدر تقرير فجوة ولا يُخمَّن."""


def _err(code, msg):
    return f"[{code}] {msg}"


def check_pack():
    """ص-1 · ص-2 — اكتمال الحزم بنيوياً وعدم الفراغ."""
    out = []
    ss = _J("skill_sections.json")
    for s in SKILLS:
        if s not in ss:
            out.append(_err("ص-1", f"skill_sections: المهارة {s} غائبة")); continue
        for k in SLOT_BINDING:
            v = ss[s].get(k)
            if not v or not str(v).strip():
                out.append(_err("ص-1", f"skill_sections[{s}][{k}] فارغ أو غائب — الربط: {SLOT_BINDING[k]}"))
    three = _J("three_texts.json")
    for k in ("covenant_opening", "out_text", "reflective_frame"):
        if not three.get(k, "").strip():
            out.append(_err("ص-2", f"three_texts[{k}] فارغ أو غائب"))
    try:
        cm = _J("circle_map_v2.json")
    except FileNotFoundError:
        return out + [_err("ص-2", "circle_map_v2.json غائب — الحزمة مدموجة (DEF-K3-01 قائم)")]
    if not cm.get("shared", "").strip():
        out.append(_err("ص-2", "circle_map_v2[shared] فارغ أو غائب"))
    for s in SKILLS:
        if not cm.get("tail", {}).get(s, "").strip():
            out.append(_err("ص-2", f"circle_map_v2[tail][{s}] فارغ أو غائب"))
    return out


def check_band_labels(band_label_map):
    """ص-4 — تغطية صريحة لكل نطاق: لا وسم افتراضي صامت."""
    out = []
    missing = BANDS_REQUIRED - set(band_label_map)
    for b in sorted(missing):
        out.append(_err("ص-4", f"BAND_LABEL لا يغطي «{b}» صراحةً "
                               f"⇒ يُسحب وسم افتراضي صامت. المعتمد: «{BAND_LABELS_APPROVED[b]}»"))
    for b, lab in band_label_map.items():
        if b in BAND_LABELS_APPROVED and lab != BAND_LABELS_APPROVED[b]:
            out.append(_err("ص-4", f"وسم «{b}» = «{lab}» يخالف المعتمد «{BAND_LABELS_APPROVED[b]}»"))
    return out


def check_general_section_purity():
    """ص-3 — الفحص 10: الفصل البنيوي بين المشترك والخاتمة (79-K3-USERMAP §2 · DEC-195/ج)."""
    out = []
    try:
        cm = _J("circle_map_v2.json")
    except FileNotFoundError:
        return [_err("ص-3", "circle_map_v2.json غائب — الحزمة ما زالت مدموجة (DEF-K3-01)")]
    if "shared" not in cm or "tail" not in cm:
        return [_err("ص-3", "circle_map_v2: بنية غير مفصولة (shared/tail)")]
    if TAIL_SIGNATURE in cm["shared"]:
        out.append(_err("ص-3", "المقطع المشترك (§2.1) يحمل خاتمة مهارية ⇒ تسرّب في القسم العام"))
    for s in SKILLS:
        t = cm["tail"].get(s, "")
        if not t.strip():
            out.append(_err("ص-3", f"خاتمة {s} (§2.2) غائبة أو فارغة"))
        elif TAIL_SIGNATURE not in t:
            out.append(_err("ص-3", f"خاتمة {s} لا تحمل توقيعها ⇒ فصل غير سليم"))
    return out


def check_rendered(report_text, sp, band_fn):
    """ص-3/ص-5 — فحص المخرج نفسه: مطابقة العنوان للمضمون."""
    out = []
    lines = report_text.split("\n")
    # ص-3: الخاتمة المهارية قبل أول قسم مهاري = مرجع معلَّق
    def _is_skill_heading(l):
        return (l.startswith("### ") and "—" in l
                and l.split("—")[-1].strip() in BAND_LABELS_APPROVED.values())
    first_skill = next((i for i, l in enumerate(lines) if _is_skill_heading(l)), len(lines))
    if any(TAIL_SIGNATURE in l for l in lines[:first_skill]):
        out.append(_err("ص-3", "مرجع معلَّق: «وهذه المهارة» يظهر قبل تقديم أي مهارة "
                               "⇒ عنوان القسم لا يحمل مضمونه (الفحص 10)"))
    # ص-5: وسم النطاق في كل عنوان مهاري يطابق band(sp)
    for l in lines:
        if l.startswith("### ") and "—" in l:
            shown = l.split("—")[-1].strip()
            if shown not in BAND_LABELS_APPROVED.values():
                out.append(_err("ص-5", f"وسم غير معتمد في العنوان: «{shown}»"))
    return out


def check_dual_name(report_text, user_name, alt_of):
    """ص-6 — DEC-197/ج: العنوان يجمع الاسمين متى اختلفا. فحص واحد لقياس واحد (ن-7/②)."""
    out = []
    for s_, short in user_name.items():
        alt = alt_of(s_)
        # DEC-228/ب — التطابق التامّ وحده
        expected = short if alt == short else f"{short} ({alt})"
        if not any(l.startswith(f"### {expected} —") for l in report_text.split("\n")):
            out.append(_err("ص-6", f"{s_}: العنوان لا يطابق «{expected}» (DEC-197/ج)"))
    return out


def validate(report_text=None, sp=None, band_fn=None, band_label_map=None,
             user_name=None, alt_of=None):
    """الحارس الشامل — يعيد قائمة الشذوذ (فارغة = سليم)."""
    out = check_pack() + check_general_section_purity()
    if band_label_map is not None:
        out += check_band_labels(band_label_map)
    if report_text is not None:
        out += check_rendered(report_text, sp, band_fn)
        if user_name and alt_of:
            out += check_dual_name(report_text, user_name, alt_of)
    return out


def enforce(**kw):
    """يوقف الإصدار عند أي شذوذ — ن-7."""
    issues = validate(**kw)
    if issues:
        raise K3IntegrityError("حارس K3 أوقف الإصدار:\n- " + "\n- ".join(issues))
    return True
