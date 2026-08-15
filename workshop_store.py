# -*- coding: utf-8 -*-
"""
workshop_store.py — عقد استقبال حصيلة الورشة وتخزينها
=======================================================
سند: `DEC-277` (مسار الورشة) · `DEC-252` (صيغة الأرشيف) · `DEC-220` (عقد
     إعادة التوليد) · `DEC-271` (تغطية المشرف للدوائر الثلاث)

**المشرف بوابةُ قبولٍ لا فحصاً لاحقاً.** الحمولة تُحكَم قبل أن تُخزَّن،
فما يدخل المخزن **مُتحقَّقٌ منه بالبناء** لا بالثقة. وتقريرٌ يسقط في
التدقيق **لا يُخزَّن صامتاً** — يُردّ بحكمه.

**وصفر اعتمادٍ يُخزَّن** (`DEC-277 §4`): لا كلمة مرور ولا تجزئتها. الرمز
يُصدره المالك، والمخزن يعرف الرمز وحده — فيسقط صنفُ اختراقٍ كامل.

**والهوية خارج المخزن:** ربط الرمز بالاسم في سجلّ الرموز الذي يملكه
المالك، لا في حمولة المشارك. فالمخزن يحمل **رمزاً وتقريراً**، لا اسماً.
"""
import hashlib
import io
import json
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import supervisor as SV

SCHEMA = "RAWAHIL-WORKSHOP-v1.0"
CIRCLES = ("K2", "K3", "K4")
STORE_DIR = os.path.join(HERE, "workshop_data")
# **سجلّ الرموز خارج مجلَّد الحصيلة** (`DEC-286`): كان بداخله، فكان نسخُ
# الحصيلة يحمل الأسماء معه — وعقدُ هذا الملف يقول إن المخزن «يحمل رمزاً
# وتقريراً لا اسماً». فصار الصدقُ في المجلَّد كما هو في السجلّات.
CODES_FILE = os.path.join(HERE, "workshop_codes.json")
LEGACY_CODES = os.path.join(STORE_DIR, "_codes.json")

# نصّ الإذن **المعتمد بنصّه** في `DEC-277 §2` — يُطابَق حرفياً ولا يُصاغ.
CONSENT_TEXT = "مدرّبك يرى نتيجتك كاملةً بأرقامها"
CODE_RE = re.compile(r"^[A-Z0-9]{4}-[A-Z0-9]{4}$")


class WorkshopError(ValueError):
    """خرق عقد الاستقبال — يُردّ بحكمه ولا يُخزَّن."""


# ── سجلّ الرموز — يملكه المالك، وربطُ الاسم فيه لا في الحمولة ────────────
def _load_codes():
    """يقرأ السجلّ — ويُرحّل القديم من داخل الحصيلة **مُعلِناً** لا صامتاً."""
    if not os.path.exists(CODES_FILE) and os.path.exists(LEGACY_CODES):
        codes = json.load(io.open(LEGACY_CODES, encoding="utf-8"))
        _save_codes(codes)
        os.remove(LEGACY_CODES)
        sys.stderr.write(
            "· رُحِّل سجلّ الرموز إلى " + os.path.basename(CODES_FILE) +
            " — خارج مجلَّد الحصيلة (DEC-286)\n")
        return codes
    if not os.path.exists(CODES_FILE):
        return {}
    return json.load(io.open(CODES_FILE, encoding="utf-8"))


def _save_codes(codes):
    d = os.path.dirname(CODES_FILE)
    if d:
        os.makedirs(d, exist_ok=True)
    io.open(CODES_FILE, "w", encoding="utf-8").write(
        json.dumps(codes, ensure_ascii=False, sort_keys=True, indent=1) + "\n")


def issue(label, seed=None):
    """يُصدر رمز مشاركة. `label` وسمٌ يعرفه المالك وحده (اسم المشارك مثلاً)."""
    codes = _load_codes()
    base = f"{label}|{len(codes)}|{seed if seed is not None else time.time()}"
    h = hashlib.sha256(base.encode("utf-8")).hexdigest().upper()
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"      # بلا حروفٍ ملتبسة
    raw = [alphabet[int(h[i:i + 2], 16) % len(alphabet)] for i in range(0, 16, 2)]
    code = "".join(raw[:4]) + "-" + "".join(raw[4:8])
    if code in codes:
        raise WorkshopError("تصادم رمز — أعد الإصدار")
    codes[code] = {"label": label, "issued_at": "—", "used": False}
    _save_codes(codes)
    return code


def known(code):
    return code in _load_codes()


# ── عقد الحمولة ──────────────────────────────────────────────────────────
def validate(payload):
    """يفحص البنية والإذن والرمز — ويوقف عند أول خرق (`ن-7`: لا تخمين)."""
    if not isinstance(payload, dict):
        raise WorkshopError("الجذر ليس كائناً")
    if payload.get("schema") != SCHEMA:
        raise WorkshopError(f"مخطَّط غير معروف: {payload.get('schema')!r}")
    code = str(payload.get("code", "")).strip()
    if not CODE_RE.match(code):
        raise WorkshopError("رمز مشاركة غير صالح الصيغة")
    if not known(code):
        raise WorkshopError("رمز مشاركة غير مُصدَر")

    consent = payload.get("consent")
    if not isinstance(consent, dict) or consent.get("text") != CONSENT_TEXT:
        raise WorkshopError("نصّ الإذن غائب أو مخالف للنصّ المعتمد")
    if consent.get("accepted") is not True:
        raise WorkshopError("الإذن غير مقبول — لا استقبال بلا إذن صريح")

    # **صفر اعتماد**: أي حقلٍ يشبه كلمة مرور يُردّ، ولا يُتجاهل بصمت.
    banned = [k for k in payload
              if k.lower() in ("password", "passwd", "pass", "hash", "token",
                               "secret", "pin")]
    if banned:
        raise WorkshopError(f"حقول اعتماد ممنوعة: {banned} (DEC-277 §4)")

    reports = payload.get("reports")
    if not isinstance(reports, dict) or not reports:
        raise WorkshopError("لا تقارير في الحمولة")
    unknown = [c for c in reports if c not in CIRCLES]
    if unknown:
        raise WorkshopError(f"دوائر غير معروفة: {unknown}")
    for c, r in reports.items():
        if not isinstance(r, dict) or "markdown" not in r or "audit" not in r:
            raise WorkshopError(f"{c}: صيغة الأرشيف ناقصة (markdown/audit)")
    return code


def supervise(payload):
    """**بوابة القبول**: كل دائرةٍ تُحكَم بأداة المشرف قبل التخزين."""
    verdicts = {}
    for circle, r in payload["reports"].items():
        graded = {"schema": "RAWAHIL-REPORT-v1.2", "circle": circle,
                  "scopes": ["full"],
                  "delivery": {"markdown": r["markdown"]}, "audit": r["audit"]}
        if circle == "K4" and r.get("crossing"):
            graded["delivery"]["markdown_crossing"] = r["crossing"]["markdown"]
            graded["audit_crossing"] = r["crossing"]["audit"]
        _out, errs = SV.grade(graded)
        verdicts[circle] = {"clean": not errs, "errors": errs}
    return verdicts


def accept(payload):
    """يفحص ويحكم ويخزّن — أو يردّ. لا حالة وسطى ولا تخزينٌ لمعطوب."""
    code = validate(payload)
    verdicts = supervise(payload)
    failed = [c for c, v in verdicts.items() if not v["clean"]]
    if failed:
        raise WorkshopError(
            "تقرير ساقط في التدقيق — لا يُخزَّن: " +
            " · ".join(f"{c}: {verdicts[c]['errors'][0]}" for c in failed))
    os.makedirs(STORE_DIR, exist_ok=True)
    record = {"schema": SCHEMA, "code": code, "consent": payload["consent"],
              "reports": payload["reports"], "verdicts": verdicts}
    body = json.dumps(record, ensure_ascii=False, sort_keys=True, indent=1)
    record_sha = hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]
    path = os.path.join(STORE_DIR, code + ".json")
    io.open(path, "w", encoding="utf-8").write(body + "\n")
    codes = _load_codes()
    codes[code]["used"] = True
    _save_codes(codes)
    return {"code": code, "path": os.path.basename(path),
            "record_sha": record_sha, "verdicts": verdicts}



# ── حقوق صاحب البيان (`DEC-277 §5` · تُنفَّذ في `DEC-286`) ───────────────
def _record_path(code):
    return os.path.join(STORE_DIR, code + ".json")


def export(code):
    """يسلّم صاحبَ البيان نسختَه **كاملةً** — الحقّ الثاني المنصوص."""
    code = str(code).strip().upper()
    path = _record_path(code)
    if not os.path.exists(path):
        raise WorkshopError(f"لا سجلّ بالرمز {code}")
    return json.load(io.open(path, encoding="utf-8"))


def forget(code):
    """يمحو السجلَّ **وقيدَ الرمز معاً** — ولا محوٌ نصفيّ يترك الاسم.

    ويُعلن ما مُحي: محوٌ صامتٌ لا يُطمئن صاحبَه ولا يُحاسَب عليه المالك.
    """
    code = str(code).strip().upper()
    path = _record_path(code)
    codes = _load_codes()
    had_record, had_code = os.path.exists(path), code in codes
    if not (had_record or had_code):
        raise WorkshopError(f"لا أثر للرمز {code} — لا سجلّ ولا قيد")
    if had_record:
        os.remove(path)
    if had_code:
        codes.pop(code)
        _save_codes(codes)
    left = [os.path.exists(path), code in _load_codes()]
    if any(left):
        raise WorkshopError(f"محوٌ ناقص للرمز {code} — بقي أثر")
    return {"code": code, "record_removed": had_record,
            "code_removed": had_code}


def load_all():
    """الحصيلة المخزَّنة — للوحة المالك (المرحلة ③)."""
    if not os.path.isdir(STORE_DIR):
        return []
    out = []
    for name in sorted(os.listdir(STORE_DIR)):
        if name.endswith(".json") and not name.startswith("_"):
            out.append(json.load(io.open(os.path.join(STORE_DIR, name),
                                         encoding="utf-8")))
    return out


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__.strip())
        print("\n  python3 workshop_store.py issue <وسم>"
              "\n  python3 workshop_store.py codes"
              "\n  python3 workshop_store.py accept <ملف.json>"
              "\n  python3 workshop_store.py export <رمز> [ملف.json]"
              "\n  python3 workshop_store.py forget <رمز>")
        return 2
    cmd = argv[0]
    if cmd == "issue":
        if len(argv) < 2:
            print("❌ يلزم وسم"); return 2
        print("✅ رمز مشاركة: " + issue(argv[1]))
        return 0
    if cmd == "codes":
        for c, v in sorted(_load_codes().items()):
            print(f"{c}  {'مستعمل' if v['used'] else 'متاح  '}  {v['label']}")
        return 0
    if cmd == "accept":
        payload = json.load(io.open(argv[1], encoding="utf-8"))
        try:
            r = accept(payload)
        except WorkshopError as e:
            print(f"❌ مردود: {e}")
            return 1
        print(f"✅ مقبول ومخزَّن — {r['path']} · بصمة السجل {r['record_sha']}")
        return 0
    if cmd == "export":
        if len(argv) < 2:
            print("❌ يلزم رمز"); return 2
        try:
            rec = export(argv[1])
        except WorkshopError as e:
            print(f"❌ {e}"); return 1
        body = json.dumps(rec, ensure_ascii=False, sort_keys=True, indent=1)
        out = argv[2] if len(argv) > 2 else f"rawahil-export-{rec['code']}.json"
        io.open(out, "w", encoding="utf-8").write(body + "\n")
        print(f"✅ صُدِّر — {out} · لصاحبه وحده")
        return 0
    if cmd == "forget":
        if len(argv) < 2:
            print("❌ يلزم رمز"); return 2
        try:
            r = forget(argv[1])
        except WorkshopError as e:
            print(f"❌ {e}"); return 1
        # **يُعلن ما مُحي**: السجلّ والقيد كلاهما، أو ما وُجد منهما
        print(f"✅ مُحي الرمز {r['code']} — "
              f"السجلّ: {'مُحي' if r['record_removed'] else 'لم يكن'} · "
              f"قيد الرمز واسمُه: {'مُحي' if r['code_removed'] else 'لم يكن'}")
        return 0
    print(f"❌ أمر غير معروف: {cmd}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
