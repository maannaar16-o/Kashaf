# -*- coding: utf-8 -*-
"""
sp_gate.py — حرّاس مخرج العرض: `ح-4` و`ح-5`
==============================================
سند: `DEC-183` (حذف `SP%` من الشاشة وكل التصديرات) · `DEC-230` (`ح-4`)
     `DEC-232` (`ح-5`) · `ن-7` (`DEC-193`/`198`/`199`/`200`/`224`)

حارسان **مستقلّان**، كلٌّ يقيس شيئاً واحداً (`ن-7/②`):

  `ح-4`  حضور **الرمز** `SP%`               ← `sp_gate()`
  `ح-5`  حضور **نسبة مئوية** غير مسجَّلة     ← `pct_gate()`

الفصل ليس ترفاً: `ح-4` وحده يمرّ عليه `73.5%`، و`ح-5` وحده يمرّ عليه
رأس جدول `SP%` بلا قيمة. ودمجهما في مقياس واحد يخالف `ن-7/②`.

الحدّ قاطع لا مخترَع (`ن-7/④`): أي مطابقة واحدة توقف الإصدار.

الحقل العددي `sp` خارج نطاق الحارسين **بحكم التعريف** — عددٌ بلا علامة
`%` فلا يطابق أيّ نمط. وسنده `DEC-183` («تعديل عرض») و`100-AUDIT-REGEN §2`
(`sp` حقل ملزِم) و`DEC-220` (كفاية `audit`).
"""
import re

# ══ `ح-4` — الرمز ═══════════════════════════════════════════════════════
SP_TOKEN = re.compile(r"SP\s*%", re.IGNORECASE)

# سجلّ الذِكر المقبول لـ`ح-4` (نمط `DEC-229`) — فارغ: صفر مطابقة على 142 مخرجاً
MENTION_REGISTRY: dict = {}


# ══ `ح-5` — النسبة ══════════════════════════════════════════════════════
PCT_VALUE = re.compile(r"\d+(?:[.,]\d+)?\s*%")

# سجلّ النِّسَب المعتمدة — **نصّ كامل مُسنَد إلى حزمة ومسار**، لا شظية ولا رقم.
# إن تغيّر النصّ في الحزمة سقط تسجيله وأُوقف الإصدار — وهو نمط الفشل المقصود.
PCT_REGISTRY = {
    "INTENSITY_K2:/S/A/M+/lock":
        'هذه أول كتلة "مشتعلة" (فوق 50%) — عدسة مساندة نشطة، لا ثانوية ولا ناقصة. `P = C + G`.',
    "CONTENT_K2:/R/lines/R-C-D/presence":
        "تشغيلك اليومي داخل التزام آمن؛ تختبر البديل في بيئة معزولة ثم يُحوَّل سابقةً معتمدة — كفاءة فورية والتزام 100%",
}


class SPLeakError(RuntimeError):
    """تسرّب الرمز `SP%` إلى مخرج — `ح-4`."""


class PctLeakError(RuntimeError):
    """تسرّب نسبة مئوية غير مسجَّلة إلى مخرج — `ح-5`."""


def _ctx(text, i):
    return text[max(0, i - 60): i + 40].replace("\n", " ")


# ── `ح-4` ───────────────────────────────────────────────────────────────
def scan(text):
    """إصابات `ح-4`. لا ترفع استثناءً."""
    if not isinstance(text, str):
        return []
    hits = []
    for m in SP_TOKEN.finditer(text):
        c = _ctx(text, m.start())
        if c.strip() in MENTION_REGISTRY:
            continue
        hits.append((m.start(), c))
    return hits


def sp_gate(text, where="<مخرج غير مسمّى>"):
    hits = scan(text)
    if hits:
        lines = "\n".join(f"    [{i}] …{c}…" for i, c in hits[:8])
        raise SPLeakError(
            f"ح-4/DEC-183 — الرمز `SP%` حاضر في مخرج «{where}» "
            f"({len(hits)} إصابة). الإصدار موقوف.\n{lines}")
    return text


# ── `ح-5` ───────────────────────────────────────────────────────────────
def _strip_registered(text):
    """يحذف النصوص المسجَّلة قبل المسح — حذفٌ حرفي، لا استثناء بالحدس."""
    for approved in PCT_REGISTRY.values():
        text = text.replace(approved, "")
    return text


def scan_pct(text):
    """إصابات `ح-5`. لا ترفع استثناءً."""
    if not isinstance(text, str):
        return []
    stripped = _strip_registered(text)
    return [(m.start(), _ctx(stripped, m.start())) for m in PCT_VALUE.finditer(stripped)]


def pct_gate(text, where="<مخرج غير مسمّى>"):
    hits = scan_pct(text)
    if hits:
        lines = "\n".join(f"    [{i}] …{c}…" for i, c in hits[:8])
        raise PctLeakError(
            f"ح-5/DEC-183 — نسبة مئوية غير مسجَّلة في مخرج «{where}» "
            f"({len(hits)} إصابة). الإصدار موقوف.\n{lines}")
    return text


# ── بوابة الإصدار الموحَّدة (حارسان مستقلّان يُستدعيان تتابعاً) ─────────
def output_gate(text, where="<مخرج غير مسمّى>"):
    sp_gate(text, where)
    pct_gate(text, where)
    return text
