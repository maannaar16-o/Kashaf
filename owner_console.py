# -*- coding: utf-8 -*-
"""
owner_console.py — لوحة المالك: الخام والأحكام وخريطة الفريق (`DEC-280`)
==========================================================================
سند: `DEC-277 §2` (رفع `ح-4` **محصوراً بسطح المالك وبإذنٍ صريح**) ·
     `DEC-278` (طبقة الفريق) · `DEC-279` (مخزن الورشة) · `DEC-254` (سابقة
     أدوات المشغّل: بايثون وحدها بلا توأم — **ولا سطح متصفح لها**)

**أداةُ مشغّلٍ لا صفحةُ ويب.** لا تُخدَم على شبكة ولا تُبنى في حزمة
متصفح — فحرس التأجيل في `test_report_team` يبقى نافذاً كما هو.

**والرفع مشروطٌ لا مطلق:** `ح-4` مرفوعٌ هنا **بإذن صاحب البيان**، فكل
سجلٍّ يُفحص إذنُه **بنصّه المعتمد حرفياً** قبل أن يُعرَض رقمٌ خام منه.
وسجلٌّ بلا إذنٍ مطابق **لا يُعرَض خامُه** — يُعلَن حجبُه ولا يُسقَط صامتاً.

**والحدود مُعلَنةٌ في اللوحة نفسها** لا في وثيقةٍ بعيدة (`voids`):
لا فارقٌ زمني يُقرأ · لا معيارَ يُشتقّ من فوج · ولا اختبارَ تمييزٍ بأربعة.
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import k2_engine as E2
import team_engine as TE
import team_report as TR
import workshop_store as WS

PACK_PATH = os.path.join(HERE, "team_contentpack.json")

# التنبيه الإلزامي **من حزمة الفريق** — لا صيغة ثانية لنصٍّ حاكم (`م-2`)
_PACK = json.load(io.open(PACK_PATH, encoding="utf-8"))
BANNER = _PACK["banner"]

CIRCLE_LABEL = {"K2": "التفكير", "K3": "الانفعال", "K4": "الإنجاز"}

# حدودٌ **مُعلَنة**: تُطبع في اللوحة، فلا يبحث عنها المالك في وثيقة.
VOIDS = [
    ("لا فارقٌ زمني يُقرأ", "قياسان لفردٍ واحد لا يُطرح أحدهما من الآخر — "
     "`DEC-244` نافذ مهما تكرّر القياس، وهذه اللوحة لا تعرض فارقاً."),
    ("لا معيارَ يُشتقّ من فوج", "التوزيع يصف **فوجك أنت** ولا يصير عتبةً "
     "ولا رتبةً لفرد — `DEBT-K3-NORM-01` قيدٌ دائم."),
    ("لا اختبارَ تمييزٍ بأربعة", "`DEC-277 §6`: احتمال الإصابة الكاملة صدفةً "
     "`6٪`، والعتبة تُشتقّ من العيّنة. **وفوجُ خريطة الفريق يحترق كمادّةٍ "
     "له** — فالاختيار لكل فوج لا لكل مشروع."),
    ("لا حكم كفاءة ولا مقارنة تفاضلية", BANNER),
]


class ConsoleError(ValueError):
    """خرق شرطٍ مُعلَن — يُوقف العرض ولا يُنقّى صامتاً."""


# ── القراءة من المخزن ────────────────────────────────────────────────────
def consented(rec):
    """الإذن **بنصّه** شرطُ عرض الخام — لا بمعناه ولا بوجود الحقل."""
    c = rec.get("consent")
    return (isinstance(c, dict) and c.get("text") == WS.CONSENT_TEXT
            and c.get("accepted") is True)


def records():
    """السجلّات مقسومةً: ما يجوز عرض خامه، وما يُحجب **مُعلَناً**."""
    ok, held = [], []
    for rec in WS.load_all():
        (ok if consented(rec) else held).append(rec)
    return ok, held


def label_of(code):
    try:
        return WS._load_codes().get(code, {}).get("label", "—")
    except Exception:                                   # noqa: BLE001
        return "—"


def sp_of(rec, circle):
    r = rec.get("reports", {}).get(circle)
    if not isinstance(r, dict):
        return None
    return (r.get("audit") or {}).get("sp")


def bands_of(rec, circle):
    """النطاقات **تُقرأ** من كتلة التدقيق، و$K_2$ من دوالّ محرّكها.

    ولا عتبة تُعرَّف في هذه الطبقة — `ن-7/④`.
    """
    r = rec.get("reports", {}).get(circle)
    if not isinstance(r, dict):
        return None
    aud = r.get("audit") or {}
    if aud.get("bands"):
        return aud["bands"]
    sp = aud.get("sp")
    if circle == "K2" and isinstance(sp, dict):
        return {d: E2.comp_state(float(sp[d])) for d in sorted(sp)}
    return None


# ── ① القائمة ────────────────────────────────────────────────────────────
def cmd_list(_argv):
    ok, held = records()
    if not ok and not held:
        print("· المخزن فارغ — لا حصيلة بعد.")
        return 0
    print(f"{'الرمز':<11} {'الوسم':<16} {'الدوائر':<26} الحكم")
    print("-" * 74)
    for rec in ok + held:
        circles = " · ".join(
            f"{c}:{'✅' if rec.get('verdicts', {}).get(c, {}).get('clean') else '❌'}"
            for c in WS.CIRCLES if c in rec.get("reports", {}))
        state = "مقبول" if all(
            v.get("clean") for v in rec.get("verdicts", {}).values()) else "به ملاحظة"
        if rec in held:
            state += " · ⛔ خامُه محجوب (إذنٌ غير مطابق)"
        print(f"{rec['code']:<11} {label_of(rec['code'])[:15]:<16} "
              f"{circles:<26} {state}")
    print("-" * 74)
    print(f"· {len(ok)} سجلاً معروضَ الخام · {len(held)} محجوباً")
    return 0


# ── ② سجلٌّ واحد بخامه — `ح-4` مرفوعٌ هنا بإذن صاحبه ─────────────────────
def cmd_show(argv):
    if not argv:
        raise ConsoleError("يلزم رمز مشاركة")
    code = argv[0].strip().upper()
    hit = [r for r in WS.load_all() if r.get("code") == code]
    if not hit:
        raise ConsoleError(f"لا سجلّ بالرمز {code}")
    rec = hit[0]
    if not consented(rec):
        raise ConsoleError(
            f"{code}: الإذن غير مطابقٍ للنصّ المعتمد — لا يُعرَض خامُه "
            "(`DEC-277 §2`: الرفع مشروطٌ لا مطلق)")
    print("=" * 74)
    print(f"الرمز {code} · الوسم {label_of(code)}")
    print("=" * 74)
    for circle in WS.CIRCLES:
        sp, bands = sp_of(rec, circle), bands_of(rec, circle)
        if sp is None:
            continue
        v = rec.get("verdicts", {}).get(circle, {})
        print(f"\n· دائرة {CIRCLE_LABEL[circle]} ({circle}) — "
              f"{'حكم المشرف: نظيف' if v.get('clean') else 'ملاحظات: ' + str(v.get('errors'))[:60]}")
        for d in sorted(sp):
            b = (bands or {}).get(d, "—")
            # التصيير صريح لا افتراضي (`ن-8`)
            print(f"   {d:<4} {float(sp[d]):>6.1f}   {b}")
    print("\n" + "-" * 74)
    print("⚠️  " + BANNER)
    return 0


# ── ③ توزيع الفوج — وصفٌ لا معيار ────────────────────────────────────────
def cmd_dist(_argv):
    ok, held = records()
    if not ok:
        print("· لا سجلّ معروضَ الخام.")
        return 0
    print(f"توزيع فوجك — {len(ok)} فرداً" +
          (f" · {len(held)} محجوباً" if held else ""))
    for circle in WS.CIRCLES:
        rows = [(bands_of(r, circle)) for r in ok]
        rows = [b for b in rows if b]
        if not rows:
            continue
        keys = sorted({k for b in rows for k in b})
        states = sorted({v for b in rows for v in b.values()})
        print(f"\n· دائرة {CIRCLE_LABEL[circle]} ({circle})")
        print("   " + " " * 6 + "".join(f"{s:>10}" for s in states))
        for k in keys:
            counts = [sum(1 for b in rows if b.get(k) == s) for s in states]
            print(f"   {k:<6}" + "".join(f"{c:>10}" for c in counts))
    print("\n" + "-" * 74)
    print("· التوزيع يصف هذا الفوج ولا يصير عتبةً ولا رتبةً لفرد "
          "(`DEBT-K3-NORM-01`).")
    print("· ولا دائرةٌ تُجمَع بأخرى — جدار العزل `DEC-205` قائمٌ هنا أيضاً.")
    return 0


# ── ④ خريطة الفريق — بعدسات $K_2$ الثماني وحدها ─────────────────────────
def team_members(recs):
    """المدخل: رمزٌ و`sp` من دائرة $K_2$ **وحدها** — القفل الخامس بالبناء."""
    out = []
    for rec in recs:
        sp = sp_of(rec, "K2")
        if not isinstance(sp, dict):
            continue
        out.append({"code": rec["code"],
                    "sp": {d: float(sp[d]) for d in TE.LENSES if d in sp}})
    return out


def cmd_team(_argv):
    ok, held = records()
    members = team_members(ok)
    if len(members) < TE.MIN_MEMBERS:
        raise ConsoleError(
            f"عضوان حدّاً أدنى — وُجد {len(members)} سجلاً صالحاً"
            + (f" ({len(held)} محجوباً بالإذن)" if held else ""))
    body, audit = TR.build_report(members)
    print(body)
    print("\n" + "-" * 74)
    print(f"· {audit['sections_rendered']} أقسام · {len(members)} عضواً")
    if held:
        print(f"· ⛔ {len(held)} سجلاً خارج الخريطة: إذنُه غير مطابق.")
    return 0


# ── ⑤ الحدود المُعلَنة ───────────────────────────────────────────────────
def cmd_voids(_argv):
    print("حدودُ هذه اللوحة — مُعلَنةٌ فيها لا في وثيقةٍ بعيدة")
    print("=" * 74)
    for title, why in VOIDS:
        print(f"\n⛔ {title}\n   {why}")
    return 0


COMMANDS = {"list": cmd_list, "show": cmd_show, "dist": cmd_dist,
            "team": cmd_team, "voids": cmd_voids}


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__.strip())
        print("\n  python3 owner_console.py list"
              "\n  python3 owner_console.py show <رمز>"
              "\n  python3 owner_console.py dist"
              "\n  python3 owner_console.py team"
              "\n  python3 owner_console.py voids")
        return 2
    cmd = COMMANDS.get(argv[0])
    if cmd is None:
        print(f"❌ أمر غير معروف: {argv[0]}")
        return 2
    try:
        return cmd(argv[1:])
    except (ConsoleError, TE.InputContractError) as e:
        print(f"❌ {e}")
        return 1
    except BrokenPipeError:
        # `| head` يغلق الأنبوب — وأداةُ مشغّلٍ تُنبَّب بطبعها، فلا تُخرج
        # أثراً كأنها انهارت. **والترتيب هو الصواب**: يُحوَّل الواصف إلى
        # `devnull` **قبل** أي إغلاق — فإغلاقُ `stdout` ثم طلبُ `fileno()`
        # منه يرفع `ValueError` فيصير الحارسُ نفسه سببَ الأثر.
        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
        return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
