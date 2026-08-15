# -*- coding: utf-8 -*-
"""
build_workshop_html.py — مولّد صفحة مسار الورشة (`DEC-279`)
=============================================================
يبني `Workshop.html` ملفاً واحداً قائماً بذاته، بعرف التجميع نفسه المستعمل
في `build_site.py`/`build_supervisor_html.py` — **وبإعادة استعمال دوالّه
حرفياً** لا بنسخها: البنود والخرائط والوحدات كلّها من هناك، فلا أداةَ ثانية
ولا خريطةَ ثانية (`م-2`).

**والفارق الوحيد عن التطبيق العام قفلُ الشبكة — يُضيَّق ولا يُرفع:**
التطبيق العام يمنع كل اتصال (`CPL-08A-03`)، وهذه الصفحة تمنع كلَّ اتصال
**إلا `POST` واحداً إلى `/submit` على الأصل نفسه**. فالوعد المنشور لم
يُنقَض — أُضيف مسارٌ ثانٍ يعلن شرطه (`DEC-277 §1`).

**والناتج مولَّد لا يُرفَع** (`CHG-054`): `Workshop.html` مُسقَط في
`.gitignore` ويفحصه `gate.py` كبقية المولَّدات.
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import build_site as BS                       # noqa: E402 — مصدر الوحدات والبنود
import workshop_store as WS                   # noqa: E402 — مصدر المخطَّط ونصّ الإذن

OUT = os.path.join(HERE, "Workshop.html")


# قفلٌ **مضيَّق** لا مرفوع: نافذةٌ واحدة بمقاسها، وكلُّ ما عداها يُرمى.
NARROW_NET = """\
"use strict";
(function(){
  var send = window.fetch ? window.fetch.bind(window) : null;
  var deny=function(api){return function(){throw new Error(api+" معطَّل — مسار الورشة له منفذٌ واحد (DEC-279)");};};
  try{
    window.XMLHttpRequest=deny("XMLHttpRequest");
    window.WebSocket=deny("WebSocket");
    window.EventSource=deny("EventSource");
    if(navigator.sendBeacon) navigator.sendBeacon=deny("sendBeacon");
    window.fetch=function(url, opts){
      var u;
      try{ u=new URL(String(url), location.href); }
      catch(e){ throw new Error("عنوان غير صالح — لا إرسال"); }
      var post = opts && String(opts.method||"").toUpperCase()==="POST";
      if(u.origin!==location.origin || u.pathname!=="/submit" || !post)
        throw new Error("fetch معطَّل إلا POST إلى /submit على الأصل نفسه (DEC-279)");
      if(!send) throw new Error("لا منفذ إرسال في هذا المتصفح");
      return send(u.href, opts);
    };
  }catch(e){}
  window.CPL_WORKSHOP_RUNTIME=Object.freeze({id:"CPL-WS-01",mode:"WORKSHOP_SINGLE_ENDPOINT",
    source_decision:"DEC-279",network_allowed:"POST /submit (same-origin)",
    public_promise:"unchanged (CPL-08A-03 في التطبيق العام كما هو)"});
})();"""

EXTRA_CSS = """\
.ws-banner{background:#2a1f10;border:1px solid #E8A33D;color:#E8A33D;padding:9px 16px;font-size:14px;text-align:center}
.privacy p{margin:0}
"""

SHELL = """<!doctype html>
<html dir="rtl" lang="ar">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>مسار الورشة — الرواحل</title>
<!--
__MANIFEST__
-->
<style>
__APPCSS__
__EXTRACSS__
</style>
</head>
<body>
<div class="ws-banner">مسار ورشة — نتيجتك تصل مدرّبك. هذا غير الموقع العام حيث لا تغادر إجاباتك جهازك.</div>
<div id="app"><noscript><p style="padding:30px;text-align:center">تشغيل هذه الصفحة يتطلب JavaScript.</p></noscript></div>

<!-- ══ __LOCKNOTE__ ══ -->
<script>
__NARROWNET__
</script>

<script>
__VENDOR__
</script>

<script>
__MODULES__
</script>

<script>
__PAYLOAD__
</script>

<script>
"use strict";
window.KashafData = __DATA__;
window.WorkshopData = __WSDATA__;
</script>

<script>
__APP__
</script>
</body>
</html>
"""


def build(mode="server"):
    """`server`: قفلٌ مضيَّق ومنفذُ إرسال · `offline`: **قفلٌ كامل بلا منفذ**.

    والنسخة المنشورة تأخذ قفل التطبيق العام نفسه (`CPL-08A-03`) **لأنها
    لا تحتاج شبكةً أصلاً** — فلا استثناءَ يُحمَل إلى أصلٍ عام (`DEC-285`).
    """
    if mode not in ("server", "offline"):
        BS.die(f"وضعٌ غير معروف: {mode}")
    BS.check_vendor()
    r = subprocess.run([sys.executable, os.path.join(HERE, "build_packs.py")],
                       capture_output=True, text=True, cwd=HERE)
    if r.returncode != 0:
        BS.die("build_packs.py أخفق:\n" + r.stderr[:500])

    items = BS.parse_items()
    BS.validate_maps()
    data = {"ITEMS": items, "BLOCKS": BS.BLOCKS, "K3_MAP": BS.K3_MAP}
    data["BUILD"] = {"hash": BS.sha256(json.dumps(
        {"ITEMS": items, "K2": BS.K2_EXPECT, "K3": BS.K3_MAP, "B": BS.BLOCKS},
        ensure_ascii=False, sort_keys=True))[:16]}

    # المخطَّط ونصّ الإذن وصيغة الرمز **من `workshop_store` وحده** — فالنصّ
    # الحاكم مصدرُه واحد، ولا نسخة ثانية له في هذه الطبقة (`م-2`).
    wsdata = {"SCHEMA": WS.SCHEMA, "CONSENT_TEXT": WS.CONSENT_TEXT,
              "CODE_RE_SRC": WS.CODE_RE.pattern,
              "DELIVERY": "file" if mode == "offline" else "both"}

    manifest = "\n".join(
        ["مولَّد بـ build_workshop_html.py — لا يُحرَّر يدوياً (DEC-279)",
         ("قفل الشبكة: CPL-08A-03 — كل اتصالٍ ممنوع (نسخةٌ منشورة بلا خادم)"
          if mode == "offline" else
          "قفل الشبكة: CPL-WS-01 — POST /submit على الأصل نفسه وحده"),
         "بصمات المصادر:"] +
        [f"  {n}: {BS.sha256(BS.read(n))[:16]}"
         for n in ("40-MEASURE_Questionnaire_v5.md", "41-Raw_Measure_v4_2.md",
                   "engines.js", "packs.js", "workshop_store.py")] +
        [f"  بصمة البناء (البنود+الخرائط): {data['BUILD']['hash']}"])

    vendor = (f'/* ==== react 18.3.1 ==== */\n'
              f'{BS.read("site", "vendor", "react.production.min.js")}\n'
              f'/* ==== react-dom 18.3.1 ==== */\n'
              f'{BS.read("site", "vendor", "react-dom.production.min.js")}\n')

    locknote = ("قفل صفر شبكة — CPL-08A-03 · DEC-110 (نسخةٌ منشورة بلا خادم)"
                if mode == "offline" else
                "قفل شبكةٍ مضيَّق — CPL-WS-01 · DEC-279")
    html = (SHELL
            .replace("__LOCKNOTE__", locknote)
            .replace("__MANIFEST__", manifest)
            .replace("__APPCSS__", BS.APP_CSS)
            .replace("__EXTRACSS__", EXTRA_CSS)
            .replace("__NARROWNET__",
                     BS.ZERO_NET if mode == "offline" else NARROW_NET)
            .replace("__VENDOR__", vendor)
            .replace("__MODULES__", BS.js_modules())
            .replace("__PAYLOAD__", BS.read("site", "workshop", "ws_payload.js"))
            .replace("__DATA__", json.dumps(data, ensure_ascii=False))
            .replace("__WSDATA__", json.dumps(wsdata, ensure_ascii=False))
            .replace("__APP__", BS.read("site", "workshop", "workshop_app.js")))

    for token in ("LOCKNOTE", "MANIFEST", "APPCSS", "EXTRACSS", "NARROWNET", "VENDOR",
                  "MODULES", "PAYLOAD", "DATA", "WSDATA", "APP"):
        if "__" + token + "__" in html:
            BS.die(f"قالبٌ لم يُملأ: {token}")

    # توكيداتٌ لا يُكتب الناتج دونها
    if 'type="password"' in html:
        BS.die("حقل اعتماد في صفحة الورشة — خرق DEC-277 §4")
    lock = "CPL-08A-03" if mode == "offline" else "CPL-WS-01"
    if lock not in html:
        BS.die(f"قفل الشبكة غائب: {lock}")
    if mode == "offline":
        # **الضمانة القفلُ لا غيابُ سلسلة**: كود الإرسال مضمومٌ في الحالين
        # (سطحٌ واحد لا سطحان — `م-2`)، لكنه **لا يُعرَض** لأن `DELIVERY`
        # يقول `file`، **ولو بُلِغ لرماه القفل الكامل**. فيُقاس الثلاثة:
        if "CPL-WS-01" in html:
            BS.die("النسخة المنشورة تحمل القفل المضيَّق")
        if '"DELIVERY": "file"' not in html:
            BS.die("النسخة المنشورة بلا إعلان طريق التسليم")
        if "CPL_WORKSHOP_RUNTIME" in html:
            BS.die("زمن تشغيل الاستثناء مركَّبٌ في النسخة المنشورة")
    if WS.CONSENT_TEXT not in html:
        BS.die("نصّ الإذن المعتمد غائب من الصفحة")
    return html


def main():
    html = build()
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ Workshop.html — {len(html.encode('utf-8')):,} بايت · "
          f"بصمة {BS.sha256(html)[:16]}")
    print("   التشغيل: python3 workshop_server.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
