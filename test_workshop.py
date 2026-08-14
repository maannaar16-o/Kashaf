# -*- coding: utf-8 -*-
"""
test_workshop.py — عقد مسار الورشة: بوابة القبول · صفر اعتماد · صفر تسرّب
==========================================================================
سند: `DEC-277` (مسار الورشة) · `DEC-279` (هذا العقد) · `DEC-252` · `DEC-271`

يقيس أربعة أشياء **يعلنها القرار**:
  1) **المشرف بوابةُ قبول**: تقريرٌ معطوب **لا يُخزَّن** — يُردّ بحكمه
  2) **صفر اعتمادٍ يُخزَّن**: أي حقلٍ يشبه كلمة مرور يُردّ ولا يُتجاهل
  3) **الإذن الصريح شرط**: بنصّه المعتمد حرفياً لا بمعناه
  4) **الموقع العام لم يُمسّ**: وعدُه وقفلُ صفر الشبكة فيه كما هما

**وبيانات المشاركين لا تدخل المستودع**: الفحص الخامس يرفض أي أثرٍ لها
في `git` — فهي بيانات أشخاص لا مخرَجات بناء.
"""
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import k2_report as R2
import k3_report as R3
import k4_report as R4
import workshop_store as WS

FAILS = []


def check(label, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + label + (" - " + detail if detail else ""))
    if not ok:
        FAILS.append(label)


def _payload(code):
    sp2 = {"A": 80.0, "R": 60.0, "C": 55.0, "O": 45.0,
           "S": 70.0, "E": 40.0, "St": 50.0, "H": 65.0}
    sp3 = list(json.load(io.open(os.path.join(HERE, "parity_cases.json"),
                                 encoding="utf-8"))["k3"].values())[0]
    sp4 = {"WM": 62, "TI": 38, "F": 74, "PF": 44, "OR": 55, "TM": 41, "PER": 40}
    t2, a2 = R2.build_report(sp2, mode="full")
    t3, a3 = R3.build_report(sp3)
    t4, a4 = R4.build_report(sp4)
    xt, xa = R4.build_crossing_surface(sp4)
    return {"schema": WS.SCHEMA, "code": code,
            "consent": {"text": WS.CONSENT_TEXT, "accepted": True},
            "reports": {"K2": {"markdown": t2, "audit": a2},
                        "K3": {"markdown": t3, "audit": a3},
                        "K4": {"markdown": t4, "audit": a4,
                               "crossing": {"markdown": xt, "audit": xa}}}}


def run_in_sandbox(fn):
    """كل فحصٍ في مخزنٍ مؤقّت — فلا يلمس حصيلة ورشةٍ حقيقية."""
    tmp = tempfile.mkdtemp(prefix="ws_test_")
    old_dir, old_codes = WS.STORE_DIR, WS.CODES_FILE
    WS.STORE_DIR = tmp
    WS.CODES_FILE = os.path.join(tmp, "_codes.json")
    try:
        return fn()
    finally:
        WS.STORE_DIR, WS.CODES_FILE = old_dir, old_codes
        shutil.rmtree(tmp, ignore_errors=True)


def _reject(label, mutate):
    def body():
        code = WS.issue("فحص", seed=label)
        p = _payload(code)
        mutate(p)
        try:
            WS.accept(p)
            return False, "مرّ بلا ردّ"
        except WS.WorkshopError as e:
            stored = [f for f in os.listdir(WS.STORE_DIR)
                      if not f.startswith("_")]
            if stored:
                return False, "رُدّ لكنه خُزِّن: " + str(stored)
            return True, str(e)[:60]
    ok, detail = run_in_sandbox(body)
    check(label, ok, detail)


def test_happy_path():
    def body():
        code = WS.issue("فحص-سليم", seed="ok")
        r = WS.accept(_payload(code))
        clean = all(v["clean"] for v in r["verdicts"].values())
        stored = os.path.exists(os.path.join(WS.STORE_DIR, code + ".json"))
        used = json.load(io.open(WS.CODES_FILE, encoding="utf-8"))[code]["used"]
        return (clean and stored and used,
                "الدوائر الثلاث نظيفة والرمز صار مستعملاً")
    ok, detail = run_in_sandbox(body)
    check("1 حمولة سليمة تُقبل وتُخزَّن", ok, detail)


def test_supervisor_is_the_gate():
    _reject("1 تقرير معطوب لا يُخزَّن (المشرف بوابة)",
            lambda p: p["reports"]["K2"].__setitem__(
                "markdown", p["reports"]["K2"]["markdown"] + " ."))
    _reject("1 بصمة مزوّرة لا تُخزَّن",
            lambda p: p["reports"]["K4"]["audit"].__setitem__(
                "report_sha256", "0000000000000000"))


def test_no_credentials():
    for field in ("password", "token", "hash"):
        _reject("2 حقل اعتماد يُردّ: " + field,
                lambda p, f=field: p.__setitem__(f, "x"))


def test_consent():
    _reject("3 بلا إذن يُردّ", lambda p: p.pop("consent"))
    _reject("3 إذن غير مقبول يُردّ",
            lambda p: p["consent"].__setitem__("accepted", False))
    _reject("3 نصّ إذنٍ مخالف يُردّ",
            lambda p: p["consent"].__setitem__("text", "موافقة عامة"))


def test_structure():
    _reject("3 رمز غير مُصدَر يُردّ", lambda p: p.__setitem__("code", "AAAA-BBBB"))
    _reject("3 مخطَّط مجهول يُردّ", lambda p: p.__setitem__("schema", "X-v9"))
    _reject("3 دائرة غير معروفة تُردّ",
            lambda p: p["reports"].__setitem__("K9", {"markdown": "x", "audit": {}}))


# -- 4) الموقع العام لم يُمسّ ---------------------------------------------
def test_public_site_untouched():
    kashaf = os.path.join(HERE, "docs", "kashaf.html")
    if not os.path.exists(kashaf):
        check("4 الموقع العام موجود", False, "docs/kashaf.html غائب")
        return
    html = io.open(kashaf, encoding="utf-8").read()
    check("4 قفل صفر الشبكة قائم في التطبيق العام",
          "fetch" in html and ("لا شبكة" in html or "صفر شبكة" in html
                               or "NetworkBlocked" in html or "throw" in html),
          "")
    clean = WS.SCHEMA not in html and "workshop" not in html.lower()
    # التفصيل يصف الحال لا يُطبع دائماً: فحصٌ ناجح يطبع رسالة سقوطه
    # يُضلِّل قارئ البوابة — وهو الصنف نفسه الذي قُيِّد في DEC-278.
    check("4 لا نقطة استقبال ورشة في التطبيق العام", clean,
          "" if clean else "ظهرت آثار مسار الورشة في الموقع العام")
    base = os.path.join(HERE, "site", "templates", "base.html")
    if os.path.exists(base):
        check("4 وعد التذييل كما هو",
              "لا تغادر" in io.open(base, encoding="utf-8").read(), "")


# -- 5) بيانات المشاركين خارج المستودع -----------------------------------
def test_data_never_tracked():
    r = subprocess.run(["git", "ls-files"], capture_output=True, text=True,
                       cwd=HERE)
    if r.returncode != 0:
        print("SKIP 5 فحص التتبّع - لا مستودع git")
        return
    tracked = [f for f in r.stdout.split("\n") if f.startswith("workshop_data")]
    check("5 صفر ملف حصيلة متبَع", not tracked, str(tracked[:4]) if tracked else
          "workshop_data/ مُسقَطة")
    gi = io.open(os.path.join(HERE, ".gitignore"), encoding="utf-8").read()
    check("5 الإسقاط مُعلَن في .gitignore", "workshop_data/" in gi, "")


# -- 6) صفحة الورشة: القفل مضيَّق لا مرفوع ---------------------------------
def test_page_build():
    import build_workshop_html as BW
    html = BW.build()
    io.open(BW.OUT, "w", encoding="utf-8").write(html)   # مولَّد مُسقَط (CHG-054)

    # **القفل يُقاس بتشغيله**: قراءة رمزه في الصفحة لا تقيس شيئاً - قفلٌ
    # وُسِّع خطأً يُبقي رمزَه. فيُركَّب على نافذةٍ وهمية وتُجرَّب عليه
    # تسعُ محاولاتٍ تُرفض وواحدةٌ تمرّ (`00-HANDOVER §6①`).
    tmp = tempfile.mkdtemp(prefix="ws_lock_")
    try:
        lock_path = os.path.join(tmp, "lock.js")
        io.open(lock_path, "w", encoding="utf-8").write(BW.NARROW_NET)
        r = subprocess.run(["node", os.path.join(HERE, "_ws_lock_probe.js"),
                            lock_path], capture_output=True, text=True, cwd=HERE)
        probe = json.loads(r.stdout) if r.returncode == 0 and r.stdout else {}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    denials = ["xhr_denied", "ws_denied", "es_denied", "beacon_denied",
               "foreign_origin_denied", "other_path_denied", "get_denied",
               "no_opts_denied"]
    open_paths = [k for k in denials if not probe.get(k)]
    check("6 القفل مقيسٌ بتشغيله - كل ما عدا المنفذ يُرفض", not open_paths,
          str(open_paths) if open_paths else str(len(denials)) + " محاولةً مرفوضة")
    check("6 المنفذ الواحد يمرّ إلى الأصل نفسه",
          probe.get("installed") and probe.get("submit_allowed")
          and probe.get("submit_same_origin"), "POST /submit")
    # القفل المضيَّق **بديلٌ** لا إضافة: زمنُ تشغيل التطبيق العام لا يُركَّب هنا
    check("6 زمن تشغيل التطبيق العام غير مركَّب هنا",
          "CPL_OFFLINE_RUNTIME" not in html, "")
    check("6 وحدة بناء الحمولة مضمومة",
          "RawahilWorkshopPayload" in html, "")
    # النصّ الحاكم **مصدرُه واحد**: يُحقَن من `workshop_store` مرّةً واحدة
    # ويستدعيه السطح بالمرجع - فنسخةٌ ثانية في الكود خرقُ `م-2` لا زخرفة.
    app_src = io.open(os.path.join(HERE, "site", "workshop", "workshop_app.js"),
                      encoding="utf-8").read()
    check("6 نصّ الإذن محقونٌ مرّةً ولا نسخة له في الكود",
          html.count(WS.CONSENT_TEXT) == 1 and WS.CONSENT_TEXT not in app_src,
          str(html.count(WS.CONSENT_TEXT)) + " موضعاً في الصفحة")
    check("6 السطح يستدعي النصّ بمرجعه", "W.CONSENT_TEXT" in app_src, "")
    check("6 المخطَّط من مصدره الواحد", '"' + WS.SCHEMA + '"' in html, "")
    check("6 صفر حقل اعتماد في الصفحة", 'type="password"' not in html, "")
    ext = re.findall(r'(?:src|href)="https?://', html)
    check("6 صفر مورد خارجي", not ext, str(ext[:3]) if ext else "")
    check("6 الناتج مُسقَط في .gitignore",
          "Workshop.html" in io.open(os.path.join(HERE, ".gitignore"),
                                     encoding="utf-8").read(), "")


# -- 7) الحمولة تُبنى بجانب JS ويحكمها جانب بايثون ------------------------
def test_js_payload_accepted():
    """برهانٌ طرفيّ بالتنفيذ: ما تُصدره الصفحة فعلاً يقبله المخزن فعلاً."""
    def body():
        code = WS.issue("عبر-JS", seed="js")
        sp3 = list(json.load(io.open(os.path.join(HERE, "parity_cases.json"),
                                     encoding="utf-8"))["k3"].values())[0]
        cfg = {"sp2": {"A": 80.0, "R": 60.0, "C": 55.0, "O": 45.0,
                       "S": 70.0, "E": 40.0, "St": 50.0, "H": 65.0},
               "sp3": sp3,
               "sp4": {"WM": 62, "TI": 38, "F": 74, "PF": 44,
                       "OR": 55, "TM": 41, "PER": 40},
               "schema": WS.SCHEMA, "consent": WS.CONSENT_TEXT, "code": code}
        cfg_path = os.path.join(WS.STORE_DIR, "_cfg.json")
        os.makedirs(WS.STORE_DIR, exist_ok=True)
        io.open(cfg_path, "w", encoding="utf-8").write(
            json.dumps(cfg, ensure_ascii=False))
        r = subprocess.run(["node", os.path.join(HERE, "_ws_node.js"), cfg_path],
                           capture_output=True, text=True, cwd=HERE)
        if r.returncode != 0:
            return False, "node أخفق: " + (r.stderr or r.stdout)[:120]
        out = WS.accept(json.loads(r.stdout))
        return (all(v["clean"] for v in out["verdicts"].values()),
                "تقارير JS قبلها مخزن بايثون")
    ok, detail = run_in_sandbox(body)
    check("7 حمولة جانب JS يقبلها المخزن", ok, detail)


# -- 8) عقد الخادم: مساران لا ثالث، والمردود لا يُخزَّن --------------------
def test_server_contract():
    import workshop_server as SRV

    def post(port, path, obj):
        req = urllib.request.Request(
            "http://127.0.0.1:" + str(port) + path,
            data=json.dumps(obj, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                return r.status, json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read().decode("utf-8"))

    def get(port, path):
        try:
            with urllib.request.urlopen(
                    "http://127.0.0.1:" + str(port) + path, timeout=20) as r:
                return r.status, r.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode("utf-8")

    def body():
        httpd = SRV.serve("127.0.0.1", 0)
        port = httpd.server_address[1]
        th = threading.Thread(target=httpd.serve_forever, daemon=True)
        th.start()
        try:
            st, page = get(port, "/")
            check("8 GET / يخدم صفحة الورشة",
                  st == 200 and "CPL-WS-01" in page, str(st))
            st, _ = get(port, "/../workshop_store.py")
            check("8 مسارٌ آخر يُردّ 404", st == 404, str(st))

            code = WS.issue("خادم", seed="srv")
            st, j = post(port, "/submit", _payload(code))
            stored = os.path.exists(os.path.join(WS.STORE_DIR, code + ".json"))
            check("8 حمولة سليمة تُقبل وتُخزَّن عبر الخادم",
                  st == 200 and j.get("ok") is True and stored, str(st))

            code2 = WS.issue("خادم-معطوب", seed="srv2")
            bad = _payload(code2)
            bad["reports"]["K2"]["markdown"] += " ."
            st, j = post(port, "/submit", bad)
            stored2 = os.path.exists(os.path.join(WS.STORE_DIR, code2 + ".json"))
            check("8 حمولة معطوبة تُردّ 400 ولا تُخزَّن",
                  st == 400 and not stored2, str(st))

            st, _ = post(port, "/nope", {"x": 1})
            check("8 مسار إرسالٍ آخر يُردّ 404", st == 404, str(st))
        finally:
            httpd.shutdown()
            httpd.server_close()
        return True, ""
    run_in_sandbox(body)


if __name__ == "__main__":
    print("=" * 76)
    test_happy_path()
    test_supervisor_is_the_gate()
    test_no_credentials()
    test_consent()
    test_structure()
    test_public_site_untouched()
    test_data_never_tracked()
    test_page_build()
    test_js_payload_accepted()
    test_server_contract()
    print("-" * 76)
    if FAILS:
        print("النتيجة النهائية: انحدار - " + str(len(FAILS)) + ": " +
              " · ".join(FAILS))
        raise SystemExit(1)
    print("النتيجة النهائية: لا انحدار")
