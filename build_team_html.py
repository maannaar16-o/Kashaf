# -*- coding: utf-8 -*-
"""
build_team_html.py — سطح الفريق في المتصفح (`DEC-289`)
========================================================
يبني `Team.html` ملفاً واحداً قائماً بذاته — **أداةُ مالكٍ محلّية** كـ
`Supervisor.html`: تُفتح من القرص، **ولا تُنشر ولا تدخل `docs/`**.

**ولماذا لا تُنشر:** مدخلُها درجاتٌ خام (`SP`)، فهي في نطاق رفع `ح-4`
المحصور بسطح المالك (`DEC-277 §2`). **ومخرجُها بلا خامٍ أصلاً** (قفلُ
الميثاق الثاني) — لكنّ المدخل وحده يكفي لإبقائها محلّية.

**وقفلُ صفر الشبكة كامل** (`CPL-08A-03`): لا تحتاج شبكةً البتّة.
"""
import io
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import build_site as BS                    # noqa: E402 — قفل الشبكة والأنماط
import team_engine as TE                   # noqa: E402 — الحزمة ومصدرها

OUT = os.path.join(HERE, "Team.html")

EXTRA_CSS = """\
.tm-head{border-bottom:1px solid #3a4a52;padding:10px 16px;background:#141c20;font-size:14px;color:#9fb0b6}
.tm-wrap{max-width:1080px;margin:0 auto;padding:16px 16px 80px}
.tm-note{background:#2a1f10;border:1px solid #E8A33D;color:#E8A33D;padding:9px 14px;border-radius:8px;font-size:13.5px;margin:12px 0}
.tm-ta{width:100%;box-sizing:border-box;min-height:150px;background:#141c20;border:1px solid #3a4a52;border-radius:10px;color:#EDEAE3;font:14px/1.8 monospace;padding:12px;direction:ltr;text-align:left}
.tm-out table{border-collapse:collapse;width:100%;margin:10px 0;font-size:14px}
.tm-out th,.tm-out td{border:1px solid #3a4a52;padding:7px 9px;text-align:right;vertical-align:top}
.tm-out th{background:#141c20;color:#4FD1C5}
.tm-out h2{color:#4FD1C5;font-size:18px;margin:26px 0 6px;border-bottom:1px solid #3a4a52;padding-bottom:6px}
.tm-out blockquote{border-right:3px solid #E8A33D;background:#202b30;color:#ffb86b;margin:12px 0;padding:9px 14px;border-radius:0 8px 8px 0}
.tm-err{border-right:3px solid #a04030;background:#2a1414;color:#e08070;margin:12px 0;padding:10px 14px;border-radius:0 8px 8px 0}
"""

SHELL = """<!doctype html>
<html dir="rtl" lang="ar">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>خريطة الفريق — الرواحل</title>
<!--
__MANIFEST__
-->
<style>
__APPCSS__
__EXTRACSS__
</style>
</head>
<body>
<div class="tm-head">خريطة التغطية والتكامل — أداةُ مالكٍ محلّية · لا تُنشر · قفل صفر شبكة (CPL-08A-03)</div>
<div class="tm-wrap">
  <div class="tm-note">⚠️ المدخل درجاتٌ خام — وهذا سطحُ المالك وحده (DEC-277 §2). والمخرج بلا خامٍ بقفل الميثاق.</div>
  <p style="color:#9fb0b6;font-size:14px">ألصق الأعضاء بصيغة JSON: <code style="direction:ltr;display:inline-block">[{"code":"T-01","sp":{"A":92,...}}, ...]</code> — أو اضغط «مثال».</p>
  <textarea class="tm-ta" id="in" spellcheck="false"></textarea>
  <div class="actions" style="justify-content:flex-start">
    <button class="btn" id="go">اقرأ التركيب</button>
    <button class="btn ghost" id="demo">مثال</button>
  </div>
  <div class="tm-out" id="out"></div>
</div>

<!-- ══ قفل صفر شبكة — CPL-08A-03 · DEC-110 ══ -->
<script>
__ZERONET__
</script>

<script>
__MODULES__
</script>

<script>
"use strict";
window.TEAM_PACK = __PACK__;
</script>

<script>
__APP__
</script>
</body>
</html>
"""

APP = """\
"use strict";
(function () {
  var T = window.RawahilTeam, PACK = window.TEAM_PACK;
  var inEl = document.getElementById("in"), outEl = document.getElementById("out");

  var DEMO = [
    { code: "T-01", sp: { A: 92, C: 78, O: 62, R: 40, S: 35, E: 30, St: 28, H: 25 } },
    { code: "T-02", sp: { E: 95, S: 88, R: 60, A: 40, O: 35, C: 30, St: 28, H: 25 } },
    { code: "T-03", sp: { H: 90, St: 80, A: 60, R: 40, O: 35, C: 30, S: 28, E: 25 } }
  ];

  // عارضٌ صغير للماركداون الجدولي — **لا يؤلّف نصّاً**، يعرض ما بناه التوأم
  function render(md) {
    var lines = md.split("\\n"), out = [], tbl = null;
    var esc = function (s) {
      return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    };
    var inline = function (s) {
      return esc(s).replace(/\\*\\*([^*]+)\\*\\*/g, "<strong>$1</strong>");
    };
    var flush = function () {
      if (!tbl) return;
      var h = tbl[0], rows = tbl.slice(1).filter(function (r) {
        return !/^:?-{3,}/.test(r[0].trim());
      });
      out.push("<table><thead><tr>" + h.map(function (c) {
        return "<th>" + inline(c) + "</th>"; }).join("") + "</tr></thead><tbody>" +
        rows.map(function (r) {
          return "<tr>" + r.map(function (c) { return "<td>" + inline(c) + "</td>"; }).join("") + "</tr>";
        }).join("") + "</tbody></table>");
      tbl = null;
    };
    lines.forEach(function (ln) {
      if (ln.indexOf("|") === 0) {
        var cs = ln.split("|").slice(1, -1).map(function (c) { return c.trim(); });
        (tbl = tbl || []).push(cs);
        return;
      }
      flush();
      if (!ln.trim()) return;
      if (ln.indexOf("## ") === 0) out.push("<h2>" + inline(ln.slice(3)) + "</h2>");
      else if (ln.indexOf("> ") === 0) out.push("<blockquote>" + inline(ln.slice(2)) + "</blockquote>");
      else if (ln.indexOf("- ") === 0) out.push("<p>• " + inline(ln.slice(2)) + "</p>");
      else out.push("<p>" + inline(ln) + "</p>");
    });
    flush();
    return out.join("\\n");
  }

  function read() {
    outEl.innerHTML = "";
    var members;
    try {
      members = JSON.parse(inEl.value);
    } catch (e) {
      outEl.innerHTML = '<div class="tm-err">مدخلٌ ليس JSON صالحاً: ' + e.message + "</div>";
      return;
    }
    try {
      var r = T.buildReport(members, PACK);
      outEl.innerHTML = render(r[0]) +
        '<p style="color:#7d8d93;font-size:13px">أقسام: ' + r[1].sections_rendered +
        " · أعضاء: " + r[1].n_members + " · بصمة التقرير: " + r[1].report_sha256 + "</p>";
    } catch (e) {
      // **خرقُ العقد يُعرض حكماً لا انهياراً** (درس DEC-280 §5)
      outEl.innerHTML = '<div class="tm-err">عقد المدخل: ' + e.message + "</div>";
    }
  }

  document.getElementById("go").onclick = read;
  document.getElementById("demo").onclick = function () {
    inEl.value = JSON.stringify(DEMO, null, 1);
    read();
  };
})();
"""


def js_modules():
    """المحرّك والحزم والتوأم — بالتشييم نفسه المُثبت في `build_site`."""
    m = [BS.wrap("engines.js", BS.read("engines.js"),
                 shim_tail="window.RawahilEngines = { K2, K3, K4, InputContractError };"),
         BS.wrap("packs.js", BS.read("packs.js"),
                 shim_tail="window.RawahilPacks = { PACKS, PACK_SHA, verifyPacks, _sha256, "
                           "PackIntegrityError };")]
    tc = BS.read("team_core.js")
    assert "require(" in tc, "team_core.js بلا استيراد — تغيّر عرفُ الوحدة"
    m.append(f'/* ==== team_core.js ==== */\n{tc}\n')
    return "\n".join(m)


def build():
    BS.check_vendor()
    r = subprocess.run([sys.executable, os.path.join(HERE, "build_packs.py")],
                       capture_output=True, text=True, cwd=HERE)
    if r.returncode != 0:
        BS.die("build_packs.py أخفق:\n" + r.stderr[:500])
    pack = TE.ContentPack().require().raw
    manifest = "\n".join(
        ["مولَّد بـ build_team_html.py — لا يُحرَّر يدوياً (DEC-289)",
         "أداةُ مالكٍ محلّية: لا تُنشر ولا تدخل docs/",
         "بصمات المصادر:"] +
        [f"  {n}: {BS.sha256(BS.read(n))[:16]}"
         for n in ("team_core.js", "team_contentpack.json", "engines.js", "packs.js")])
    html = (SHELL
            .replace("__MANIFEST__", manifest)
            .replace("__APPCSS__", BS.APP_CSS)
            .replace("__EXTRACSS__", EXTRA_CSS)
            .replace("__ZERONET__", BS.ZERO_NET)
            .replace("__MODULES__", js_modules())
            .replace("__PACK__", json.dumps(pack, ensure_ascii=False))
            .replace("__APP__", APP))
    for token in ("MANIFEST", "APPCSS", "EXTRACSS", "ZERONET", "MODULES", "PACK", "APP"):
        if "__" + token + "__" in html:
            BS.die(f"قالبٌ لم يُملأ: {token}")
    if "CPL-08A-03" not in html:
        BS.die("قفل صفر الشبكة غائب")
    if "RawahilTeam" not in html:
        BS.die("التوأم غير مضموم")
    return html


def main():
    html = build()
    io.open(OUT, "w", encoding="utf-8").write(html)
    print(f"✅ Team.html — {len(html.encode('utf-8')):,} بايت · بصمة {BS.sha256(html)[:16]}")
    print("   أداةُ مالكٍ محلّية — تُفتح من القرص ولا تُنشر")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
