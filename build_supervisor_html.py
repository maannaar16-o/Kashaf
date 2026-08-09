# -*- coding: utf-8 -*-
"""
build_supervisor_html.py — مولّد `Supervisor.html`
===================================================
يجمع الوحدات الخمس في ملف واحد قائم بذاته، بعرف التشييم نفسه المستعمل
في `Kashaf_v2.html` (`window.RawahilX`). لا يُحرَّر الناتج يدوياً.

سند: `DEC-233` (الأداة) · `DEC-110`/`CPL-08A-03` (صفر شبكة) · `DEC-199` (تكافؤ)
"""
import hashlib
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "Supervisor.html")


def read(n):
    return open(os.path.join(HERE, n), encoding="utf-8").read()


def wrap(name, src, shim_head="", shim_tail=""):
    return (f'/* ==== {name} ==== */\n(function(){{\n"use strict";\n'
            f'{shim_head}{src}\n{shim_tail}\n}})();\n')


def modules():
    # ① engines.js
    en = read("engines.js")
    m = ['\n' + wrap("engines.js", en,
                     shim_tail='window.RawahilEngines = { K2, K3, InputContractError };')]

    # ② packs.js
    pk = read("packs.js")
    m.append(wrap("packs.js", pk,
                  shim_tail='window.RawahilPacks = '
                            '{ PACKS, PACK_SHA, PACK_SOURCE, verifyPacks, _sha256, PackIntegrityError };'))

    # ③ sp_gate.js — يعرّف root.RawahilSPGate بنفسه
    m.append(f'/* ==== sp_gate.js ==== */\n{read("sp_gate.js")}\n')

    # ④ reports.js — تُستبدل الاستيرادات بالنطاق العام
    rp = read("reports.js")
    rp = (rp.replace('const { K2, K3 } = require("./engines.js");',
                     'const { K2, K3 } = window.RawahilEngines;')
            .replace('const PK = require("./packs.js");',
                     'const PK = window.RawahilPacks;')
            .replace('const SPG = require("./sp_gate.js");',
                     'const SPG = window.RawahilSPGate;'))
    assert "require(" not in rp, "بقي استيراد غير مُشيَّم في reports.js"
    # التصدير: يُحوَّل شرط `module` إلى إسناد عام — باستبدال حرفي لا بنمط
    head = 'if (typeof module !== "undefined") {\n  module.exports = {'
    assert rp.count(head) == 1, "كتلة التصدير في reports.js غير فريدة"
    rp = rp.replace(head, "window.RawahilReports = {", 1).rstrip()
    assert rp.endswith("};\n}"), "ذيل كتلة التصدير غير متوقَّع"
    rp = rp[:-len("};\n}")] + "};"
    m.append(wrap("reports.js", rp))

    # ⑤ supervisor_core.js — يعرّف root.RawahilSupervisor بنفسه
    m.append(f'/* ==== supervisor_core.js ==== */\n{read("supervisor_core.js")}\n')
    return "\n".join(m)


SHELL = r"""<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>أداة المشرف — الرواحل / الكشاف</title>
<style>
:root{
  --ground:#111820; --panel:#18212C; --panel-2:#1E2936; --rule:#2B3644;
  --bone:#E6E1D6; --dim:#93A0AE; --faint:#63717F;
  --verdigris:#5FA88E; --oxide:#C0563C; --brass:#C8A24A;
  --serif:"Amiri","Traditional Arabic","Times New Roman",serif;
  --sans:"Segoe UI","Noto Sans Arabic","Geeza Pro",Tahoma,sans-serif;
  --mono:ui-monospace,"SF Mono",Menlo,Consolas,monospace;
}
*{box-sizing:border-box}
html,body{margin:0;padding:0}
body{
  background:var(--ground); color:var(--bone); font-family:var(--sans);
  font-size:15px; line-height:1.65; padding:0 0 64px;
  background-image:radial-gradient(circle at 50% -10%, #1A2532 0%, var(--ground) 55%);
  background-attachment:fixed;
}
.wrap{max-width:860px;margin:0 auto;padding:0 20px}

/* ── الترويسة ─────────────────────────────────────────── */
header{border-bottom:1px solid var(--rule);margin-bottom:34px}
.bar{display:flex;justify-content:space-between;align-items:baseline;
     padding:22px 0 16px;gap:16px;flex-wrap:wrap}
h1{font-family:var(--serif);font-size:31px;font-weight:400;margin:0;letter-spacing:.01em}
.eyebrow{font-family:var(--mono);font-size:11px;color:var(--faint);
         letter-spacing:.16em;text-transform:uppercase}
.lede{color:var(--dim);font-size:14px;max-width:60ch;margin:0 0 20px}

/* ── منطقة الإفلات ────────────────────────────────────── */
.drop{border:1px dashed var(--rule);border-radius:3px;background:var(--panel);
      padding:38px 24px;text-align:center;transition:border-color .18s,background .18s}
.drop.hot{border-color:var(--verdigris);background:var(--panel-2)}
.drop p{margin:0 0 14px;color:var(--dim)}
.btn{font:inherit;font-size:14px;background:transparent;color:var(--bone);
     border:1px solid var(--rule);border-radius:2px;padding:8px 18px;cursor:pointer;
     transition:border-color .15s,color .15s}
.btn:hover{border-color:var(--verdigris);color:var(--verdigris)}
.btn:focus-visible{outline:2px solid var(--brass);outline-offset:2px}
.btn.ghost{color:var(--faint);font-size:13px;padding:6px 12px}
.row{display:flex;gap:10px;justify-content:center;flex-wrap:wrap}
textarea{width:100%;min-height:110px;margin-top:14px;background:var(--panel);
  color:var(--bone);border:1px solid var(--rule);border-radius:2px;padding:10px;
  font-family:var(--mono);font-size:12px;resize:vertical}

/* ── الختم — العنصر المميِّز ───────────────────────────── */
.seal{margin:30px 0 10px;padding:22px 26px;position:relative;background:var(--panel);
      border:1px solid var(--rule)}
.seal::before{content:"";position:absolute;inset:5px;border:1px solid var(--rule);
      pointer-events:none}
.seal.clean{border-color:var(--verdigris)}
.seal.clean::before{border-color:var(--verdigris)}
/* الختم المكسور: الإطار الداخلي ينقطع ويزيح */
.seal.broken{border-color:var(--oxide)}
.seal.broken::before{
  border-color:var(--oxide);
  border-style:solid dashed solid dashed;
  transform:translate(4px,-3px) rotate(-.5deg);
}
.verdict{font-family:var(--serif);font-size:30px;line-height:1.2;margin:0 0 4px}
.seal.clean .verdict{color:var(--verdigris)}
.seal.broken .verdict{color:var(--oxide)}
.seal .why{color:var(--dim);font-size:14px;margin:0}
.seal .fp{font-family:var(--mono);font-size:11.5px;color:var(--faint);
          margin-top:12px;word-break:break-all}
.seal .fp b{color:var(--dim);font-weight:400}
@media (prefers-reduced-motion:no-preference){
  .seal{animation:press .34s cubic-bezier(.2,.9,.3,1)}
  @keyframes press{from{opacity:0;transform:scale(1.015)}to{opacity:1;transform:none}}
}

/* ── سجلّ الدرجات ─────────────────────────────────────── */
.file{margin:34px 0 0}
.fname{font-family:var(--mono);font-size:12px;color:var(--dim);
       padding-bottom:8px;border-bottom:1px solid var(--rule);word-break:break-all}
.meta{display:flex;gap:18px;flex-wrap:wrap;font-family:var(--mono);font-size:11.5px;
      color:var(--faint);margin:10px 0 0}
ol.grades{list-style:none;margin:14px 0 0;padding:0}
ol.grades li{display:grid;grid-template-columns:22px 1fr auto;gap:12px;
  align-items:baseline;padding:9px 0;border-bottom:1px solid rgba(43,54,68,.55)}
ol.grades li:last-child{border-bottom:none}
.mark{font-family:var(--mono);font-size:13px;text-align:center}
.pass .mark{color:var(--verdigris)}
.fail .mark{color:var(--oxide)}
.skip .mark{color:var(--brass)}
.gname{font-size:14px}
.fail .gname{color:var(--oxide)}
.skip .gname{color:var(--dim)}
.gdetail{font-family:var(--mono);font-size:11px;color:var(--faint);
  text-align:left;max-width:46%;word-break:break-all}
.fail .gdetail{color:#D98A76}

footer{margin-top:44px;padding-top:18px;border-top:1px solid var(--rule);
  color:var(--faint);font-size:12px}
footer code{font-family:var(--mono);color:var(--dim)}
.err{color:var(--oxide);font-size:14px;margin:10px 0}
</style>
</head>
<body>
<div class="wrap">

<header>
  <div class="bar">
    <h1>أداة المشرف</h1>
    <span class="eyebrow">RAWAHIL · AL-KASHAF</span>
  </div>
</header>

<p class="lede">
  أفلت تقريراً مُصدَّراً بصيغة <code>JSON</code>. تُعاد قراءته من سجلّ تدقيقه وحده،
  ويُقارَن الناتج بما وصل المستفيد. الأداة تتحقّق من النزاهة ولا تقرأ الشخص ولا تفسّره.
</p>

<div class="drop" id="drop">
  <p>أفلت الملفات هنا</p>
  <div class="row">
    <button class="btn" id="pick">اختر ملفات</button>
    <button class="btn ghost" id="paste">أو ألصق نصّ JSON</button>
    <button class="btn ghost" id="self">افحص الأداة نفسها</button>
  </div>
  <input type="file" id="file" accept=".json,application/json" multiple hidden>
  <textarea id="ta" hidden placeholder='{ "schema": "RAWAHIL-REPORT-v1.2", … }'></textarea>
  <div class="row" id="tarow" hidden style="margin-top:10px">
    <button class="btn" id="run">افحص</button>
  </div>
</div>

<div id="out"></div>

<footer>
  قائمة بذاتها · صفر شبكة (<code>CPL-08A-03</code>) · <code>DEC-233</code> —
  عشر درجات · نواة مطابقة لـ<code>supervisor.py</code> (<code>DEC-199</code>).
  <span id="packline"></span>
</footer>

</div>

<!-- ══ قفل صفر شبكة — CPL-08A-03 · DEC-110 ══ -->
<script>
"use strict";
(function(){
  var deny=function(api){return function(){throw new Error(api+" معطَّل — الأداة قائمة بذاتها (CPL-08A-03)");};};
  try{ window.fetch=deny("fetch");
       window.XMLHttpRequest=deny("XMLHttpRequest");
       window.WebSocket=deny("WebSocket");
       window.EventSource=deny("EventSource");
       if(navigator.sendBeacon) navigator.sendBeacon=deny("sendBeacon");
  }catch(e){}
  window.CPL_OFFLINE_RUNTIME=Object.freeze({id:"CPL-08A-03",mode:"OFFLINE_STANDALONE",
    source_decision:"DEC-110",network_allowed:false,gate_m1:"CLOSED"});
})();
</script>

<script>
__MODULES__
</script>

<script>
"use strict";
(function(){
  var S=window.RawahilSupervisor, PK=window.RawahilPacks, RP=window.RawahilReports;
  var out=document.getElementById("out");

  try{ PK.verifyPacks();
       document.getElementById("packline").textContent =
         "· " + Object.keys(PK.PACKS).length + " حزمة سليمة البصمة";
  }catch(e){
       document.getElementById("packline").innerHTML =
         '<span style="color:var(--oxide)">· انجراف حزمة — لا يُعتمد أي حكم</span>';
  }

  function el(t,c,x){var n=document.createElement(t); if(c)n.className=c;
    if(x!==undefined)n.textContent=x; return n;}

  function render(label,payload){
    var box=el("section","file");
    box.appendChild(el("div","fname",label));

    var res,errs;
    try{ var g=S.grade(payload); res=g[0]; errs=g[1]; }
    catch(e){ box.appendChild(el("p","err","تعذّر الفحص: "+(e.message||e))); out.appendChild(box); return; }

    var meta=el("div","meta");
    ["schema","circle","scopes","subject","generated_at"].forEach(function(k){
      if(payload && payload[k]!==undefined && payload[k]!==null)
        meta.appendChild(el("span",null,k+": "+
          (Array.isArray(payload[k])?payload[k].join(" · "):payload[k])));
    });
    box.appendChild(meta);

    var clean=!errs.length;
    var seal=el("div","seal "+(clean?"clean":"broken"));
    seal.appendChild(el("p","verdict",clean?"سليم":"منجرف"));
    seal.appendChild(el("p","why",clean
      ? "المتن مطابق لسجلّ تدقيقه، والحزم غير منجرفة."
      : errs.length+" من الدرجات ساقطة — التفصيل أدناه."));
    var a=(payload&&payload.audit)||{};
    if(a.report_sha256){
      var fp=el("div","fp"); var b=el("b",null,"بصمة المتن  ");
      fp.appendChild(b); fp.appendChild(document.createTextNode(a.report_sha256));
      if(a.engine_version) fp.appendChild(document.createTextNode(
        "   ·   محرك " + a.engine_version));
      seal.appendChild(fp);
    }
    box.appendChild(seal);

    var ol=el("ol","grades");
    res.forEach(function(r){
      var cls=r[1]===null?"skip":(r[1]?"pass":"fail");
      var li=el("li",cls);
      li.appendChild(el("span","mark",r[1]===null?"—":(r[1]?"✓":"✕")));
      li.appendChild(el("span","gname",r[0]));
      li.appendChild(el("span","gdetail",r[2]||""));
      ol.appendChild(li);
    });
    box.appendChild(ol);
    out.appendChild(box);
  }

  function readFiles(list){
    out.innerHTML="";
    Array.prototype.slice.call(list).forEach(function(f){
      var fr=new FileReader();
      fr.onload=function(){
        var p; try{ p=JSON.parse(fr.result); }
        catch(e){ var b=el("section","file");
          b.appendChild(el("div","fname",f.name));
          b.appendChild(el("p","err","JSON غير صالح: "+e.message)); out.appendChild(b); return; }
        if(!p||typeof p!=="object"||Array.isArray(p)){
          var b2=el("section","file"); b2.appendChild(el("div","fname",f.name));
          b2.appendChild(el("p","err","الجذر ليس كائناً")); out.appendChild(b2); return; }
        render(f.name,p);
      };
      fr.readAsText(f,"utf-8");
    });
  }

  var drop=document.getElementById("drop"), file=document.getElementById("file"),
      ta=document.getElementById("ta"), tarow=document.getElementById("tarow");

  ["dragenter","dragover"].forEach(function(ev){
    drop.addEventListener(ev,function(e){e.preventDefault();drop.classList.add("hot");});});
  ["dragleave","drop"].forEach(function(ev){
    drop.addEventListener(ev,function(e){e.preventDefault();drop.classList.remove("hot");});});
  drop.addEventListener("drop",function(e){ if(e.dataTransfer.files.length) readFiles(e.dataTransfer.files); });

  document.getElementById("pick").onclick=function(){file.click();};
  file.onchange=function(){ if(file.files.length) readFiles(file.files); };
  document.getElementById("paste").onclick=function(){
    var on=ta.hidden; ta.hidden=!on; tarow.hidden=!on; if(on) ta.focus(); };
  document.getElementById("run").onclick=function(){
    out.innerHTML="";
    var p; try{ p=JSON.parse(ta.value); }
    catch(e){ out.appendChild(el("p","err","JSON غير صالح: "+e.message)); return; }
    render("نصّ ملصوق",p); };

  // فحص الأداة نفسها: حمولة سليمة تمرّ، ثم تُفسَد بحرف واحد فتسقط
  document.getElementById("self").onclick=function(){
    out.innerHTML="";
    var sp={A:[9,1,1],R:[5,3,3],C:[7,2,2],O:[6,3,2],S:[8,2,1],E:[4,4,3],St:[7,3,1],H:[6,2,3]};
    var pair;
    try{ pair=RP.buildReportK2(sp,"full"); }
    catch(e){ out.appendChild(el("p","err","تعذّر توليد عيّنة: "+e.message)); return; }
    var base={schema:"RAWAHIL-REPORT-v1.2",circle:"K2",generated_at:"self-test",
              scopes:["full"],delivery:{markdown:pair[0]},audit:pair[1]};
    render("فحص ذاتي — حمولة سليمة (المتوقع: سليم)",base);
    var bad=JSON.parse(JSON.stringify(base));
    bad.delivery.markdown+=" .";
    render("فحص ذاتي — أُفسدت بحرف واحد (المتوقع: منجرف)",bad);
  };
})();
</script>
</body>
</html>
"""


def main():
    html = SHELL.replace("__MODULES__", modules())
    open(OUT, "w", encoding="utf-8").write(html)
    b = open(OUT, "rb").read()
    print(f"✅ {os.path.basename(OUT)} — {len(b)} بايت · "
          f"SHA {hashlib.sha256(b).hexdigest()[:16]}")


if __name__ == "__main__":
    main()
