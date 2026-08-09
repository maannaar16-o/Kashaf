# -*- coding: utf-8 -*-
"""
supervisor.py — أداة المشرف: تدقيق مستقلّ لتقرير مُصدَّر
=========================================================
سند: `100-AUDIT-REGEN` (`DEC-220`/`221`/`222`/`223`) · `DEC-231` (مخطَّط `v1.2`)
     `DEC-230`/`DEC-232` (حارسا المخرج) · `ن-7`

**ما تفعله:** تأخذ ملف `JSON` مُصدَّراً من الأداة، وتُعيد توليد التقرير
من `audit["sp"]` **وحده**، وتقارن. لا ترجع إلى المُدخل الأصلي ولا إلى
نسخة محفوظة — فالتقرير و`audit`ه وحدة قابلة للتحقّق بذاتها.

**ما لا تفعله:** لا تعرض ولا تفسّر ولا تحكم على المفحوص. أداة **نزاهة**
لا أداة قراءة (`100-AUDIT-REGEN §5`).

الاستعمال:
    python3 supervisor.py <ملف.json> [...]
    python3 supervisor.py --self-test

رمز الخروج: `0` سليم · `1` انجراف · `2` خطأ إدخال.
"""
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import k2_report as R2
import k3_report as R3
from sp_gate import scan, scan_pct

SCHEMA_SUPPORTED = {"RAWAHIL-REPORT-v1.1", "RAWAHIL-REPORT-v1.2"}
REQUIRED_AUDIT = ["sp", "engine_version", "spec_version", "instrument_pin",
                  "entries_used", "pack_sha", "report_sha256"]


class InputError(Exception):
    """إدخال غير صالح — يُبلَّغ ولا يُخمَّن."""


def norm(t):
    lines = [l.rstrip() for l in t.replace("\r\n", "\n").split("\n")]
    while lines and not lines[0]:
        lines.pop(0)
    while lines and not lines[-1]:
        lines.pop()
    return "\n".join(lines)


def sha16(t):
    """يجزّئ المتن **الخام** — تماماً كما يفعل المحرك عند تسجيل البصمة.
    التطبيع قبل التجزئة كان عيباً: نجح مصادفةً لأن مخرج المحرك مُطبَّع
    أصلاً، وكان سيخفي تغيّر النقل للمسافات بدل أن يكشفه."""
    return hashlib.sha256(t.encode("utf-8")).hexdigest()[:16]


def regen(circle, audit, mode="full"):
    """إعادة التوليد من `audit["sp"]` حصراً."""
    sp = dict(audit["sp"])
    if circle == "K2":
        return R2.build_report(sp, mode=mode)
    return R3.build_report(sp)


# ══ الدرجات ═════════════════════════════════════════════════════════════

def grade(payload):
    """يعيد (قائمة النتائج، قائمة الأخطاء). كل درجة تقيس شيئاً واحداً."""
    out, errs = [], []

    def ok(name, passed, detail=""):
        out.append((name, passed, detail))
        if not passed:
            errs.append(f"{name}{(' — ' + detail) if detail else ''}")

    # ⓪ صلاحية المخطَّط والبنية
    schema = payload.get("schema")
    ok("⓪ المخطَّط معروف", schema in SCHEMA_SUPPORTED, f"وُجد «{schema}»")
    circle = str(payload.get("circle", "")).upper()
    ok("⓪ الدائرة معلومة", circle in ("K2", "K3"), f"وُجد «{circle}»")
    if circle not in ("K2", "K3"):
        return out, errs

    audit = payload.get("audit")
    if not isinstance(audit, dict):
        ok("⓪ حقل audit حاضر", False, "غائب أو ليس كائناً")
        return out, errs
    ok("⓪ حقل audit حاضر", True)

    # ① اكتمال العقد — الحقول السبعة
    missing = [k for k in REQUIRED_AUDIT if k not in audit]
    ok("① الحقول السبعة الملزِمة", not missing, f"ناقص {missing}" if missing else "")
    if missing:
        return out, errs

    # ② النطاقات مُعلَنة لا مستنتَجة (`DEC-231`)
    scopes = payload.get("scopes")
    if schema == "RAWAHIL-REPORT-v1.2":
        declared = isinstance(scopes, list) and scopes and all(
            s in ("full", "brief") for s in scopes)
        ok("② النطاقات مُعلَنة (DEC-231)", declared, f"وُجد {scopes!r}")
        has_brief = bool(scopes) and "brief" in scopes
    else:
        out.append(("② النطاقات مُعلَنة (DEC-231)", None,
                    "مخطَّط v1.1 — سابق للقرار · لا يُحاسَب"))
        has_brief = payload.get("audit_brief") is not None
        scopes = ["full", "brief"] if has_brief else ["full"]

    # اتّساق الإعلان مع المحتوى الفعلي
    body = payload.get("delivery", {}) or {}
    brief_present = "markdown_brief" in body
    ok("② اتّساق الإعلان بالمحتوى", brief_present == has_brief,
       f"scopes={scopes} · markdown_brief {'حاضر' if brief_present else 'غائب'}")

    # ③ البصمة المسجَّلة تصف المخرج المُسلَّم فعلاً
    delivered = body.get("markdown")
    if not isinstance(delivered, str) or not delivered.strip():
        ok("③ المتن المُسلَّم حاضر", False, "delivery.markdown غائب أو فارغ")
        return out, errs
    ok("③ المتن المُسلَّم حاضر", True)
    raw_ok = sha16(delivered) == audit["report_sha256"]
    ok("④ البصمة تصف المُسلَّم", raw_ok,
       f"محسوبة {sha16(delivered)} · مسجَّلة {audit['report_sha256']}")

    # ⑤ إعادة التوليد من الـaudit وحده تطابق المُسلَّم نصّاً
    try:
        text2, audit2 = regen(circle, audit)
    except Exception as e:
        # اسم الاستثناء وحده — نصّ الرسالة متباعد بين المحرّكين
        # (`GAP-MSG-PARITY-01`) وغير مغطّى بأي مقياس قائم.
        ok("⑤ إعادة التوليد", False, f"عقد المدخل مرفوض: {type(e).__name__}")
        return out, errs
    exact = (text2 == delivered)
    ok("⑤ إعادة التوليد تطابق المُسلَّم", exact,
       "" if exact else ("المتن مطابق **بعد التطبيع** — الفارق مسافات أو أسطر "
                         "⇒ النقل غيّر الملف، لا المحرك"
                         if norm(text2) == norm(delivered) else "المتن مختلف جوهرياً"))

    # ⑥ بصمة المُعاد = البصمة المسجَّلة
    ok("⑥ بصمة المُعاد = المسجَّلة",
       audit2["report_sha256"] == audit["report_sha256"],
       f"مُعاد {audit2['report_sha256']} · مسجَّل {audit['report_sha256']}")

    # ⑦ بصمات الحزم — انجراف المحتوى يُرصد لا يمرّ
    drift = sorted(k for k in set(audit["pack_sha"]) | set(audit2["pack_sha"])
                   if audit["pack_sha"].get(k) != audit2["pack_sha"].get(k))
    ok("⑦ الحزم غير منجرفة", not drift,
       f"منجرفة: {drift}" if drift else "")

    # ⑧ النطاق المختصر — إن أُعلن، يُدقَّق كالكامل
    if has_brief and circle == "K2":
        brief = body.get("markdown_brief")
        ab = payload.get("audit_brief") or {}
        if isinstance(brief, str) and brief.strip() and "report_sha256" in ab:
            tb, ab2 = regen(circle, ab, mode="brief")
            ok("⑧ المختصر: البصمة تصف المُسلَّم",
               sha16(brief) == ab["report_sha256"])
            ok("⑧ المختصر: إعادة التوليد تطابق", norm(tb) == norm(brief))
        else:
            ok("⑧ المختصر مكتمل", False, "متن أو audit_brief ناقص")

    # ⑨ حارسا المخرج على ما وصل المستفيد فعلاً (`ح-4` · `ح-5`)
    leaks_sp = scan(delivered)
    leaks_pct = scan_pct(delivered)
    ok("⑨ ح-4 — لا رمز SP%", not leaks_sp,
       f"{len(leaks_sp)} إصابة" if leaks_sp else "")
    ok("⑨ ح-5 — لا نسبة غير مسجَّلة", not leaks_pct,
       f"{len(leaks_pct)} إصابة: {[c.strip()[:40] for _, c in leaks_pct[:3]]}"
       if leaks_pct else "")

    return out, errs


# ══ العرض ═══════════════════════════════════════════════════════════════

def audit_file(path):
    if not os.path.exists(path):
        raise InputError(f"الملف غير موجود: {path}")
    try:
        payload = json.load(open(path, encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise InputError(f"JSON غير صالح: {e}")
    if not isinstance(payload, dict):
        raise InputError("الجذر ليس كائناً")

    print(f"\n╔══ {os.path.basename(path)}")
    for k in ("schema", "circle", "scopes", "subject", "generated_at"):
        if k in payload:
            print(f"║  {k}: {payload[k]}")
    print("╟" + "─" * 68)

    results, errs = grade(payload)
    for name, passed, detail in results:
        mark = "✅" if passed else ("⚪" if passed is None else "❌")
        print(f"║  {mark} {name}" + (f"  ·  {detail}" if detail else ""))
    print("╟" + "─" * 68)
    verdict = "✅ سليم — التقرير مطابق لـauditه والحزم غير منجرفة" if not errs \
        else f"❌ انجراف — {len(errs)} درجة ساقطة"
    print(f"║  {verdict}")
    print("╚" + "═" * 68)
    return 0 if not errs else 1


def self_test():
    """يبني حمولة حقيقية من حالة مرجعية ويدقّقها — ثم يُفسدها ويتأكّد أنه يرصد."""
    cases = json.load(open(os.path.join(HERE, "parity_cases.json"), encoding="utf-8"))
    rc = 0
    for circle, R in (("K2", R2), ("K3", R3)):
        sp = list(cases[circle.lower()].values())[0]
        text, audit = (R.build_report(sp, mode="full") if circle == "K2"
                       else R.build_report(sp))
        payload = {"schema": "RAWAHIL-REPORT-v1.2", "circle": circle,
                   "generated_at": "self-test", "scopes": ["full"],
                   "delivery": {"markdown": text}, "audit": audit}
        if circle == "K2":
            brief, ab = R.build_report(sp, mode="brief")
            payload["scopes"] = ["full", "brief"]
            payload["delivery"]["markdown_brief"] = brief
            payload["audit_brief"] = ab

        p = os.path.join(HERE, f"_selftest_{circle}.json")
        json.dump(payload, open(p, "w", encoding="utf-8"), ensure_ascii=False)
        print(f"\n▶ سليم — {circle}")
        rc |= audit_file(p)

        # إفساد مقصود: حرف واحد في المتن ⇒ يجب أن تسقط الدرجة ④ و⑤
        payload["delivery"]["markdown"] = text + " ."
        json.dump(payload, open(p, "w", encoding="utf-8"), ensure_ascii=False)
        print(f"\n▶ مُفسَد عمداً (حرف واحد) — {circle} · المتوقع ❌")
        caught = (audit_file(p) == 1)
        print(f"   {'✅ رُصد' if caught else '❌ لم يُرصد — الأداة عمياء'}")
        rc |= (0 if caught else 1)
        os.remove(p)
    return rc


def main(argv):
    args = argv[1:]
    if not args:
        print(__doc__.strip())
        return 2
    if args[0] == "--self-test":
        return self_test()
    rc = 0
    for path in args:
        try:
            rc |= audit_file(path)
        except InputError as e:
            print(f"❌ {path}: {e}")
            rc |= 2
    return rc


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
