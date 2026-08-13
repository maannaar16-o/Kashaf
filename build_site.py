# -*- coding: utf-8 -*-
"""
build_site.py — مولّد موقع الرواحل العام (`DEC-250` · `CHG-068`)
=================================================================
يبني `docs/` كاملاً: صفحات ثابتة + صفحة «الكشاف» القائمة بذاتها، بعرف
التجميع نفسه المستعمل في `build_supervisor_html.py` (تشييم حرفي + توكيدات).

البناء هو الاختبار: أي توكيد يسقط ⇒ لا يُكتب ناتج.
لا يمسّ طبقة المحرّكات — قراءة فقط. الخرائط تُنقل بقيد مزدوج من `41 §5.2/§5.3`.
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(HERE, "site")
DOCS = os.path.join(HERE, "docs")

sys.path.insert(0, HERE)
import sp_gate  # noqa: E402 — سجلّ النسب المعتمدة (ح-5) هو مرجع الفحص هنا أيضاً

REGISTERED_PCT = list(sp_gate.PCT_REGISTRY.values())


def strip_registered(text):
    """يجرّد النصوص المسجَّلة في ح-5 قبل فحص النسب — محاكاةً لسلوك الحارس نفسه."""
    for t in REGISTERED_PCT:
        text = text.replace(t, " ")
    return text


def read(*parts):
    return open(os.path.join(HERE, *parts), encoding="utf-8").read()


def sha256(data):
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def die(msg):
    raise SystemExit(f"❌ فشل البناء: {msg}")


# ═══════════════ ① المكتبات المضمومة — تثبيت البصمة ═══════════════

VENDOR_PINS = {
    "react.production.min.js":
        "d949f1c3687aedadcedac85261865f29b17cd273997e7f6b2bfc53b2f9d4c4dd",
    "react-dom.production.min.js":
        "35f4f974f4b2bcd44da73963347f8952e341f83909e4498227d4e26b98f66f0d",
}


def check_vendor():
    for name, want in VENDOR_PINS.items():
        got = sha256(open(os.path.join(SITE, "vendor", name), "rb").read())
        if got != want:
            die(f"بصمة {name} انحرفت: {got[:16]}…")


# ═══════════════ ② بنود الاستبيان — 94 بنداً من 40-MEASURE ═══════════════

def split_segments(text):
    """يفصل الجُمل التوضيحية بين الأقواس (قاعدة 40-MEASURE سطر 31)."""
    segs, pos = [], 0
    for m in re.finditer(r"\([^()]*\)", text):
        if m.start() > pos:
            segs.append({"t": "text", "s": text[pos:m.start()]})
        segs.append({"t": "note", "s": m.group(0)})
        pos = m.end()
    if pos < len(text):
        segs.append({"t": "text", "s": text[pos:]})
    return segs


def parse_items():
    src = read("40-MEASURE_Questionnaire_v5.md")
    blocks = re.split(r"^### السؤال .*$", src, flags=re.M)
    n_head = len(re.findall(r"^### السؤال ", src, flags=re.M))
    if n_head != 94:
        die(f"عناوين البنود = {n_head} ≠ 94")
    items, notes = {}, 0
    for i, chunk in enumerate(blocks[1:], start=1):
        ab = re.findall(r"^\* \*\*(أ|ب):\*\* (.+)$", chunk, flags=re.M)
        if [x[0] for x in ab] != ["أ", "ب"]:
            die(f"البند {i}: لا يحوي جملتي أ ثم ب")
        rec = {}
        for letter, text in ab:
            text = text.strip()
            if not text:
                die(f"البند {i}/{letter}: نص فارغ")
            if "%" in text:
                die(f"البند {i}/{letter}: يحوي نسبة")
            segs = split_segments(text)
            notes += sum(1 for s in segs if s["t"] == "note")
            rec["a" if letter == "أ" else "b"] = segs
        items[str(i)] = rec
    if len(items) != 94:
        die(f"عدد البنود المفكوكة = {len(items)}")
    # كناري الجُمل التوضيحية: أربعة أقواس في كامل الأداة (35أ·41أ·47أ·64أ)
    # تثبت مطابقة الفكّ للنص المختوم — قاعدة 40-MEASURE سطر 31 عامة على أي قوس
    noted = sorted(int(n) for n, rec in items.items()
                   for segs in rec.values() for s in segs if s["t"] == "note")
    if notes != 4 or noted != [35, 41, 47, 64]:
        die(f"كناري الجمل التوضيحية: عدّها {notes} في البنود {noted} — المتوقع 4 في [35, 41, 47, 64]")
    return items


# ═══════════════ ③ الخرائط — قيد مزدوج من 41 §5.2/§5.3 ═══════════════
# النقل اليدوي أدناه يُطابَق آلياً مع فكّ جدولَي الوثيقة، ثم يطابق المحرك في node.

K2_EXPECT = {
    "A":  [[1, "a"], [22, "a"], [40, "a"], [55, "a"], [67, "a"], [76, "a"], [82, "a"]],
    "R":  [[1, "b"], [4, "a"], [25, "a"], [43, "a"], [58, "a"], [70, "a"], [79, "a"]],
    "C":  [[4, "b"], [7, "a"], [22, "b"], [28, "a"], [46, "a"], [61, "a"], [73, "a"]],
    "O":  [[7, "b"], [10, "a"], [25, "b"], [31, "a"], [40, "b"], [49, "a"], [64, "a"]],
    "S":  [[10, "b"], [13, "a"], [28, "b"], [34, "a"], [43, "b"], [52, "a"], [55, "b"]],
    "E":  [[13, "b"], [16, "a"], [31, "b"], [37, "a"], [46, "b"], [58, "b"], [67, "b"]],
    "St": [[16, "b"], [19, "a"], [34, "b"], [49, "b"], [61, "b"], [70, "b"], [76, "b"]],
    "H":  [[19, "b"], [37, "b"], [52, "b"], [64, "b"], [73, "b"], [79, "b"], [82, "b"]],
}

K3_CODE_TO_NAME = {   # عكس K3_NAME_TO_CODE في bridge.js:17-23
    "EP": "قوة الملاحظة", "IR": "التحكم الانفعالي", "BI": "كبح جماح النفس",
    "CF": "المرونة", "ST": "تحمل الضغوط",
}

# **لا نقل يدوي لـ$K_3$ بعد `DEC-275`**: الخريطة تُشتقّ من `k3_engine.ITEM_MAP`
# كما تُشتقّ خريطة $K_2$ من محرّكها — فنسخةٌ ثانية في هذا الملف كانت **سلطةً
# ثانية** على خريطةٍ واحدة (`م-2`). والقيد المزدوج باقٍ: `validate_maps` يفكّ
# الجدول المختوم `41 §5.3` ويقابله بالمحرك.
import k3_engine as _E3
K3_MAP = {K3_CODE_TO_NAME[c]: [[i, o] for i, o in _E3.ITEM_MAP[c]]
          for c in ["EP", "IR", "BI", "CF", "ST"]}

BLOCKS = [[1, 10], [11, 20], [21, 30], [31, 40],
          [41, 49], [50, 58], [59, 67], [68, 76], [77, 85], [86, 94]]


def parse_map_table(section_header, code_prefix):
    """يفكّ جدول مصفوفة بنود من 41-Raw_Measure_v4_2.md."""
    src = read("41-Raw_Measure_v4_2.md")
    m = re.search(re.escape(section_header) + r".*?(?=\n### |\n## |\Z)", src, flags=re.S)
    if not m:
        die(f"قسم «{section_header}» غير موجود في 41")
    out = {}
    for row in re.finditer(r"^\| \*\*(" + code_prefix + r"-\w+)\*\* \|[^|]+\|([^|]+)\|", m.group(0), flags=re.M):
        code = row.group(1).split("-", 1)[1]
        pairs = [[int(n), "a" if l == "أ" else "b"]
                 for n, l in re.findall(r"(\d+)\s*\((أ|ب)\)", row.group(2))]
        out[code] = pairs
    return out


def validate_maps():
    # القيد المزدوج: الجدولان المفكوكان == النقل اليدوي
    t52 = parse_map_table("### 5.2", "K2")
    if t52 != K2_EXPECT:
        die("جدول 41 §5.2 المفكوك لا يطابق K2_EXPECT المنقول")
    # $K_3$ (`DEC-275`): الجدول المختوم يُقابَل **بخريطة المحرّك** لا بنسخة
    t53 = parse_map_table("### 5.3", "K3")
    eng3 = {c: [[i, o] for i, o in _E3.ITEM_MAP[c]] for c in _E3.SKILLS}
    if t53 != eng3:
        die("جدول 41 §5.3 المفكوك لا يطابق k3_engine.ITEM_MAP")
    # توكيدات البنية
    slots2 = [tuple(p) for v in K2_EXPECT.values() for p in v]
    slots3 = [tuple(p) for v in K3_MAP.values() for p in v]
    if len(K2_EXPECT) != 8 or any(len(v) != 7 for v in K2_EXPECT.values()):
        die("K2: ليست 8 أبعاد × 7 بنود")
    if len(K3_MAP) != 5 or any(len(v) != 11 for v in K3_MAP.values()):
        die("K3: ليست 5 مهارات × 11 بنداً")
    if len(set(slots2)) != 56 or len(set(slots3)) != 55:
        die("تكرار خانة داخل دائرة")
    if set(slots2) & set(slots3):
        die("تقاطع خانات بين K2 وK3 — خرق عزل")

    # ── K4 (DEC-270): الخريطة **تُقرأ من الجدول المختوم وتُقارَن بالمحرك** ──
    # `instrument_pin`: لا نقل يدوي يُعتمد بلا مقابلة. وقيد التكافؤ المختوم
    # (`128 §1`): صفّ `K4-SP` في الجدول يُقرأ `PER`.
    import k4_engine as _E4
    t54 = parse_map_table("### 5.4", "K4")
    if "SP" in t54:
        t54["PER"] = t54.pop("SP")
    eng4 = {k: [list(p) for p in v] for k, v in _E4.ITEM_MAP.items()}
    if t54 != eng4:
        die("جدول 41 §5.4 المفكوك لا يطابق K4.ITEM_MAP في المحرك")
    if len(eng4) != 7 or any(len(v) != 11 for v in eng4.values()):
        die("K4: ليست 7 صمامات × 11 بنداً")
    slots4 = [tuple(p) for v in eng4.values() for p in v]
    if len(set(slots4)) != 77:
        die(f"K4: {len(set(slots4))} خانة بدل 77")
    if set(slots4) & set(slots2):
        die("تقاطع خانات بين K4 وK2 — خرق عزل (درس DEC-027)")
    if set(slots4) & set(slots3):
        die("تقاطع خانات بين K4 وK3 — خرق عزل (درس DEC-027)")
    # الدوائر الثلاث تقسّم خانات الأداة تقسيماً تاماً — 56+55+77 = 188 = 94×2
    every = set(slots2) | set(slots3) | set(slots4)
    if len(every) != 188:
        die(f"مجموع خانات الدوائر {len(every)} بدل 188")
    for n, l in slots4:
        if not (1 <= n <= 94 and l in ("a", "b")):
            die(f"خانة K4 خارج المدى: {n}{l}")
    for n, l in slots2 + slots3:
        if not (1 <= n <= 94 and l in ("a", "b")):
            die(f"خانة خارج المدى: {n}{l}")


# ═══════════════ ④ التجميع — عرف build_supervisor_html.py ═══════════════

def wrap(name, src, shim_head="", shim_tail=""):
    return (f'/* ==== {name} ==== */\n(function(){{\n"use strict";\n'
            f'{shim_head}{src}\n{shim_tail}\n}})();\n')


def js_modules():
    m = []
    m.append(wrap("engines.js", read("engines.js"),
                  shim_tail="window.RawahilEngines = { K2, K3, K4, InputContractError };"))
    m.append(wrap("packs.js", read("packs.js"),
                  shim_tail="window.RawahilPacks = { PACKS, PACK_SHA, PACK_SOURCE, "
                            "verifyPacks, _sha256, PackIntegrityError };"))
    m.append(f'/* ==== sp_gate.js ==== */\n{read("sp_gate.js")}\n')
    rp = read("reports.js")
    rp = (rp.replace('const { K2, K3, K4 } = require("./engines.js");',
                     'const { K2, K3, K4 } = window.RawahilEngines;')
            .replace('const PK = require("./packs.js");',
                     'const PK = window.RawahilPacks;')
            .replace('const SPG = require("./sp_gate.js");',
                     'const SPG = window.RawahilSPGate;')
            # حزمة K4 صارت مضمومة إلى `packs.js` (`DEC-270`) — فتُشيَّم إلى
            # موضعها هناك، **بمصدر حقيقة واحد** لا نسخة ثانية. وإن غابت
            # بقي الرفض المكتوب نافذاً (`k4RequirePack`).
            .replace('const K4_PACK = require("./k4_contentpack.json");',
                     'const K4_PACK = (PK && PK.PACKS && PK.PACKS.CONTENT_K4) || null;'))
    assert "require(" not in rp, "بقي استيراد غير مُشيَّم في reports.js"
    head = 'if (typeof module !== "undefined") {\n  module.exports = {'
    assert rp.count(head) == 1, "كتلة التصدير في reports.js غير فريدة"
    rp = rp.replace(head, "window.RawahilReports = {", 1).rstrip()
    assert rp.endswith("};\n}"), "ذيل كتلة التصدير غير متوقَّع"
    rp = rp[:-len("};\n}")] + "};"
    m.append(wrap("reports.js", rp))
    m.append(f'/* ==== bridge.js ==== */\n{read("bridge.js")}\n')
    m.append(f'/* ==== dualreport.js ==== */\n{read("dualreport.js")}\n')
    return "\n".join(m)


ZERO_NET = """\
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
})();"""

APP_CSS = """\
body{margin:0;background:#0d1417;color:#EDEAE3;font-family:system-ui,'Segoe UI',Tahoma,sans-serif;line-height:2;font-size:16px}
.top{border-bottom:1px solid #3a4a52;padding:9px 16px;font-size:14px;background:#141c20}
.top a{color:#4FD1C5;text-decoration:none}
#app{max-width:820px;margin:0 auto;padding:16px 16px 80px}
.t-title{font-size:40px;text-align:center;margin:26px 0 4px;font-weight:800}
.t-title.small{font-size:26px}
.t-sub{text-align:center;color:#9fb0b6;margin-top:0}
.covenant{border-right:3px solid #4FD1C5;background:#141c20;margin:22px 0;padding:12px 16px;border-radius:0 10px 10px 0;font-size:16.5px}
.covenant p{margin:6px 0}
.cov-sub{color:#9fb0b6;font-size:14px}
.howto h2{color:#4FD1C5;font-size:19px;margin:22px 0 6px}
.howto ul{margin:6px 22px 6px 0;padding:0}
.howto li{margin:8px 0;color:#c8d2d5}
.privacy{color:#9fb0b6;background:#141c20;border:1px solid #3a4a52;border-radius:10px;padding:10px 14px;font-size:14px}
.actions{display:flex;gap:10px;flex-wrap:wrap;margin:24px 0;justify-content:center}
.btn{padding:12px 22px;border-radius:10px;border:1px solid #4FD1C5;background:#0f5f59;color:#EDEAE3;font-size:15.5px;cursor:pointer;font-family:inherit}
.btn.big{font-size:17px;padding:14px 30px}
.btn.ghost{background:transparent;color:#4FD1C5}
.btn.small{font-size:13.5px;padding:8px 14px;margin-top:14px}
.prog{margin:4px 0 18px}
.prog-line{font-size:13px;color:#9fb0b6}
.prog-bar{height:6px;background:#202b30;border-radius:4px;margin-top:7px}
.prog-fill{height:100%;background:#4FD1C5;border-radius:4px;transition:width .2s}
.q-prompt{font-size:18.5px;color:#4FD1C5;margin:24px 0 2px;text-align:center}
.q-num{text-align:center;color:#7d8d93;font-size:13px;margin:0 0 14px}
.choice-btn{display:flex;gap:12px;width:100%;text-align:right;padding:16px;margin:12px 0;background:#141c20;border:1px solid #3a4a52;border-radius:12px;color:#EDEAE3;font-size:16px;cursor:pointer;font-family:inherit;line-height:1.95;align-items:flex-start}
.choice-btn:hover{border-color:#4FD1C5}
.choice-btn.picked{border-color:#4FD1C5;background:#0f5f59}
.choice-tag{flex:0 0 34px;height:34px;border-radius:50%;background:#202b30;color:#4FD1C5;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:16px}
.choice-text{margin:0}
.rate-card{background:#141c20;border:1px solid #3a4a52;border-radius:12px;padding:22px;margin:16px 0 20px;font-size:17px;line-height:2.1;min-height:96px;display:flex;align-items:center}
.rate-text{margin:0}
.scale{display:flex;gap:8px;justify-content:center;flex-wrap:wrap}
.scale-btn{width:52px;height:52px;border-radius:12px;border:1px solid #3a4a52;background:#141c20;color:#EDEAE3;font-size:19px;cursor:pointer;font-family:inherit}
.scale-btn:hover{border-color:#4FD1C5}
.scale-btn.picked{background:#0f5f59;border-color:#4FD1C5}
.scale-labels{display:flex;justify-content:space-between;color:#7d8d93;font-size:12.5px;margin-top:8px}
.name-label{display:block;color:#9fb0b6;font-size:14.5px;margin-top:20px}
.name-input{display:block;width:100%;box-sizing:border-box;margin:8px 0 18px;padding:12px;background:#141c20;border:1px solid #3a4a52;border-radius:10px;color:#EDEAE3;font-size:16px;font-family:inherit}
.warnbox{border-right:3px solid #E8A33D;background:#202b30;color:#ffb86b;margin:16px;padding:10px 14px;border-radius:0 8px 8px 0}
.q-note{color:#7d8d93;font-size:.85em}
.sec-h{font-size:18px;color:#4FD1C5;margin:26px 0 6px;border-bottom:1px solid #3a4a52;padding-bottom:7px}
.contrib-card{background:#141c20;border:1px dashed #E8A33D;border-radius:12px;padding:16px 18px 12px;margin:26px auto 10px;max-width:820px}
.contrib-h{color:#E8A33D;font-size:16px;margin:0 0 6px}
.contrib-p{color:#9fb0b6;font-size:14px;line-height:1.95;margin:0 0 10px}
.actions.tight{margin:8px 0 4px;justify-content:flex-start}
.home-list{display:flex;flex-direction:column;gap:10px;margin:12px 0}
.profile-card,.arch-item{display:flex;flex-direction:column;gap:2px;text-align:right;width:100%;padding:14px 16px;background:#141c20;border:1px solid #3a4a52;border-radius:12px;color:#EDEAE3;cursor:pointer;font-family:inherit;font-size:15px}
.profile-card:hover,.arch-item:hover{border-color:#4FD1C5}
.p-alias{font-weight:700;font-size:16px}
.p-state{color:#9fb0b6;font-size:13px}
.mirror{max-width:720px;margin:10px auto}
.m-title{font-size:20px;color:#4FD1C5;text-align:center;margin:18px 0 10px}
.m-counter{text-align:center;color:#7d8d93;font-size:13px;margin:4px 0 0}
.m-md p,.m-md h3{line-height:2.05}
.m-md h3{color:#E8A33D;font-size:16.5px}
.m-behavior{background:#141c20;border:1px solid #3a4a52;border-radius:12px;padding:16px 20px;font-size:18px;text-align:center;margin:14px 0}
.m-behavior.dim2{font-size:14px;color:#9fb0b6;padding:8px 14px;border-style:dashed}
.m-behavior p,.m-question p,.m-reveals p{margin:0}
.m-question{background:#141c20;border-right:3px solid #4FD1C5;border-radius:0 10px 10px 0;padding:14px 18px;font-size:16.5px;line-height:2.1;margin:14px 0}
.m-reveals{background:#141c20;border-right:3px solid #E8A33D;border-radius:0 10px 10px 0;padding:14px 18px;font-size:15.5px;line-height:2.05;margin:14px 0;color:#c8d2d5}
.m-note{color:#7d8d93;font-size:13.5px;background:#141c20;border:1px dashed #3a4a52;border-radius:10px;padding:9px 13px}
.m-vq{margin:10px 22px 14px 0}
.m-vq li{margin:12px 0;line-height:2.05}
.m-ta{display:block;width:100%;box-sizing:border-box;min-height:84px;margin:8px 0 14px;padding:11px;background:#141c20;border:1px solid #3a4a52;border-radius:10px;color:#EDEAE3;font-size:15px;font-family:inherit;line-height:1.9}
.mirror .btn.big{display:block;margin:18px auto 0}
.newp{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin:18px 0}
.newp .name-input{flex:1 1 220px;margin:0}
.toprow{margin:4px 0 0}
.faintline{color:#7d8d93;font-size:13px;margin:2px 0 10px}
.danger{border-color:#a04030;color:#e08070}
"""

KASHAF_SHELL = """<!doctype html>
<html dir="rtl" lang="ar">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="الكشاف — استبيان الرواحل: قراءة بنيوية لعدساتك المعرفية وقدراتك التنظيمية، بالكامل داخل متصفحك.">
<title>الكشاف — استبيان الرواحل</title>
<link rel="manifest" href="manifest.json">
<meta name="theme-color" content="#0d1417">
<link rel="icon" href="assets/icons/icon-192.png">
<link rel="apple-touch-icon" href="assets/icons/icon-192.png">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<!--
__MANIFEST__
-->
<style>
__APPCSS__
/* ==== styles.css — أنماط التقريرين ==== */
__REPORTCSS__
</style>
</head>
<body>
<div class="top"><a href="index.html">→ موقع الرواحل</a></div>
<div id="app"><noscript><p style="padding:30px;text-align:center">تشغيل «الكشاف» يتطلب JavaScript — الأداة تعمل بالكامل داخل جهازك.</p></noscript></div>

<!-- ══ قفل صفر شبكة — CPL-08A-03 · DEC-110 ══ -->
<script>
__ZERONET__
</script>

<script>
__VENDOR__
</script>

<script>
__MODULES__
</script>

<script>
"use strict";
window.KashafData = __DATA__;
</script>

<script>
__APP__
</script>

<script>
"use strict";
// تسجيل عامل الخدمة — التثبيت والعمل بلا شبكة (DEC-251).
// لا يمسّ قفل صفر-الشبكة: القفل يمنع اتصالات الصفحة، والعامل يخدم ملفات التطبيق نفسها من التخزين.
(function(){
  if ("serviceWorker" in navigator) navigator.serviceWorker.register("./sw.js").catch(function(){});
})();
</script>
</body>
</html>
"""

MANIFEST_JSON = {
    "name": "الكشاف — استبيان الرواحل",
    "short_name": "الكشاف",
    "description": "قراءة بنيوية لعدساتك المعرفية وقدراتك التنظيمية — بالكامل على جهازك.",
    "lang": "ar",
    "dir": "rtl",
    "start_url": "./kashaf.html",
    "scope": "./",
    "display": "standalone",
    "background_color": "#0d1417",
    "theme_color": "#0d1417",
    "icons": [
        {"src": "assets/icons/icon-192.png", "sizes": "192x192", "type": "image/png"},
        {"src": "assets/icons/icon-512.png", "sizes": "512x512", "type": "image/png"},
        {"src": "assets/icons/icon-512-maskable.png", "sizes": "512x512",
         "type": "image/png", "purpose": "maskable"},
    ],
}

SW_TEMPLATE = """\
"use strict";
/* sw.js — مولَّد بـ build_site.py (DEC-251) — لا يُحرَّر يدوياً.
 * تخزين ذرّي مُصدَّر ببصمة الموقع: إما النسخة الجديدة كاملة أو القديمة كاملة.
 * النطاق: ملفات هذا الموقع نفسها حصراً — لا يمرّر ولا يخزّن أي أصل خارجي. */
const CACHE = "kashaf-__SITE_VER__";
const ASSETS = __ASSETS__;

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(ASSETS)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys()
    .then((ks) => Promise.all(ks.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
    .then(() => self.clients.claim()));
});

self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);
  if (e.request.method !== "GET" || url.origin !== location.origin) return;
  e.respondWith(
    caches.match(e.request, { ignoreSearch: true }).then((r) => r || fetch(e.request)));
});
"""


def build_kashaf(items):
    data = {"ITEMS": items, "BLOCKS": BLOCKS, "K3_MAP": K3_MAP}
    build_hash = sha256(json.dumps(
        {"ITEMS": items, "K2": K2_EXPECT, "K3": K3_MAP, "B": BLOCKS},
        ensure_ascii=False, sort_keys=True))[:16]
    data["BUILD"] = {"hash": build_hash}
    manifest = "\n".join(
        ["مولَّد بـ build_site.py — لا يُحرَّر يدوياً (DEC-250 · CHG-068)", "بصمات المصادر:"] +
        [f"  {n}: {sha256(read(n))[:16]}"
         for n in ("40-MEASURE_Questionnaire_v5.md", "41-Raw_Measure_v4_2.md",
                   "engines.js", "packs.js")] +
        [f"  بصمة البناء (البنود+الخرائط): {build_hash}"])
    vendor = (f'/* ==== react 18.3.1 ==== */\n{read("site", "vendor", "react.production.min.js")}\n'
              f'/* ==== react-dom 18.3.1 ==== */\n{read("site", "vendor", "react-dom.production.min.js")}\n')
    html = (KASHAF_SHELL
            .replace("__MANIFEST__", manifest)
            .replace("__APPCSS__", APP_CSS)
            .replace("__REPORTCSS__", read("styles.css"))
            .replace("__ZERONET__", ZERO_NET)
            .replace("__VENDOR__", vendor)
            .replace("__MODULES__", js_modules())
            .replace("__DATA__", json.dumps(data, ensure_ascii=False))
            .replace("__APP__", read("site", "app", "app.js")))
    assert "__" + "MODULES__" not in html
    return html, build_hash


# ═══════════════ ⑤ الصفحات الثابتة ═══════════════

PAGES = [
    ("index",  "home",   "الرئيسية",        "إطار عربي أصيل لفهم البنية الفطرية للشخصية والأداء الإنساني"),
    ("theory", "theory", "النظرية",         "المعادلة الحاكمة P = C + G والدوائر الأربع للشِفرة البنيوية"),
    ("sample", "sample", "تقرير نموذجي",    "تقارير حقيقية مُخفاة الهوية من برنامج الطيّار"),
    ("teams",  "teams",  "الفرق والمنظمات", "بروتوكول تركيب الفرق والنسخة القيادية من التقرير"),
    ("method", "method", "المنهجية",        "تنفيذ مزدوج يُقاس تكافؤه وبوابة قبول من 16 أداة"),
    ("about",  "about",  "عن المشروع",      "ما الرواحل وما ليس هو — رؤية المشروع وحدوده المختومة"),
    ("contribute", "contribute", "الإسهام الطوعي",
     "بيانات ميدانية مجهّلة تختبر صدق الأداة — بموافقة صريحة والقرار كله للمستجيب"),
]

# قناة الاستقبال المباشر (DEC-253): نشر المالك النقطة المرجعية وفُعِّل الرابط
# بأمره 2026-08-10 — تغييره أو تعطيله يكون هنا وحده ويظهر في المراجعة.
CONTRIB_ENDPOINT = "https://kashaf-contrib.maannaar16.workers.dev/"


def build_static_pages(sample_tabs, sample_bodies):
    base = read("site", "templates", "base.html")
    out = {}
    for slug, frag, title, desc in PAGES:
        body = read("site", "content", f"{frag}.html")
        if slug == "sample":
            body = body.replace("{{SAMPLE_TABS}}", sample_tabs)
            body = body.replace("{{SAMPLE_BODIES}}", sample_bodies)
        if slug == "contribute":
            body = ('<script>window.KASHAF_CONTRIB_ENDPOINT = '
                    + json.dumps(CONTRIB_ENDPOINT) + ";</script>\n" + body)
        html = (base.replace("{{title}}", title)
                    .replace("{{description}}", desc)
                    .replace("{{body}}", body))
        for s, _f, _t, _d in PAGES:
            html = html.replace("{{active:" + s + "}}", ' class="on"' if s == slug else "")
        html = html.replace("{{active:kashaf}}", "")
        if "{{" in html:
            die(f"{slug}.html: بقي وسم قالب غير مُستبدَل")
        out[f"{slug}.html"] = html
    return out


# ═══════════════ ⑥ التقارير النموذجية — تجريد السقالات ═══════════════

SAMPLES = [("P-001", "REPORT_P-001_Full_Brief.md"),
           ("P-005", "REPORT_P-005_Full_Brief.md"),
           ("P-006", "REPORT_P-006_Full_Brief.md"),
           ("P-007", "REPORT_P-007_Full_Brief.md")]

CENTER_NAMES = {"A": "التحليلي", "R": "الواقعي", "C": "المحافظ", "O": "المنظم",
                "S": "الاجتماعي", "E": "المتفهم", "St": "الاستراتيجي", "H": "التصوري"}


def md_to_html(md):
    """منفذ بايثوني لنفس المجموعة الجزئية في dualreport.js:mdToHtml."""
    def esc(s): return s.replace("&", "&amp;").replace("<", "&lt;")
    def inl(s): return re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", esc(s))
    out, tbl, in_list = [], None, False

    def flush_t():
        nonlocal tbl
        if not tbl:
            return
        h, *r = tbl
        out.append("<table class=\"rw-tbl\"><thead><tr>" +
                   "".join(f"<th>{inl(c)}</th>" for c in h) +
                   "</tr></thead><tbody>" +
                   "".join("<tr>" + "".join(f"<td>{inl(c)}</td>" for c in row) + "</tr>" for row in r) +
                   "</tbody></table>")
        tbl = None

    def flush_l():
        nonlocal in_list
        if in_list:
            out.append("</ul>")
            in_list = False

    for l in md.split("\n"):
        if re.match(r"^\|.*\|$", l.strip()):
            cells = [c.strip() for c in l.strip()[1:-1].split("|")]
            if all(re.match(r"^:?-{2,}:?$", c) for c in cells):
                continue
            flush_l()
            tbl = tbl or []
            tbl.append(cells)
            continue
        flush_t()
        if not l.strip():
            flush_l()
            continue
        if l.startswith("### "):
            flush_l(); out.append(f'<h4 class="rw-h4">{inl(l[4:])}</h4>')
        elif l.startswith("## "):
            flush_l(); out.append(f'<h3 class="rw-h3">{inl(l[3:])}</h3>')
        elif l.startswith("> "):
            flush_l(); out.append(f'<blockquote class="rw-q">{inl(l[2:])}</blockquote>')
        elif l.startswith("- "):
            if not in_list:
                out.append('<ul class="rw-ul">'); in_list = True
            out.append(f'<li class="rw-li">{inl(l[2:])}</li>')
        else:
            flush_l(); out.append(f'<p class="rw-p">{inl(l)}</p>')
    flush_t(); flush_l()
    return "\n".join(out)


def strip_report(fname):
    src = read(fname)
    m = re.search(r"·\s*مركز\s+(\w+)", src.split("\n", 1)[0])
    if not m or m.group(1) not in CENTER_NAMES:
        die(f"{fname}: تعذّر استخراج المركز من العنوان")
    center = m.group(1)
    start = re.search(r"^## ١ ", src, flags=re.M)
    if not start:
        die(f"{fname}: القسم ١ غير موجود")
    body = src[start.start():]
    # المتن المُسلَّم ينتهي بسطر «نهاية التقرير.» — وما بعده ختم بصمة داخلي يُسقط.
    # وسوم r10 الإفصاحية (وسم إلزامي/GAP-A) جزء من متن المحرك المولَّد فتبقى (DEC-219).
    cut = re.search(r"^نهاية التقرير\.?\s*$", body, flags=re.M)
    if not cut:
        die(f"{fname}: سطر «نهاية التقرير» غير موجود")
    body = body[:cut.end()].rstrip()
    sections = re.findall(r"^## ([١٢٣٤٥٦٧٨٩]) ", body, flags=re.M)
    if sections != list("١٢٣٤٥٦٧٨٩"):
        die(f"{fname}: الأقسام التسعة غير مكتملة بالترتيب: {sections}")
    scanned = strip_registered(body)
    for tok in ("SP", "DEC-", "DEF-", "%"):
        if tok in scanned:
            die(f"{fname}: بقي «{tok}» بعد التجريد")
    return center, body


def build_samples():
    tabs, bodies = [], []
    for i, (pid, fname) in enumerate(SAMPLES):
        center, body = strip_report(fname)
        on = " class=\"on\"" if i == 0 else ""
        tabs.append(f'<button data-target="sample-{pid}"{on}>ملف {CENTER_NAMES[center]} ({pid})</button>')
        bodies.append(f'<div class="sample-body rw-doc{" on" if i == 0 else ""}" id="sample-{pid}">'
                      f"{md_to_html(body)}</div>")
    return "\n".join(tabs), "\n".join(bodies)


# ═══════════════ ⑦ المراسي — الاقتباسات تُطابَق بمصادرها ═══════════════

ANCHORS = [
    # (ملف المصدر، النص في المصدر، الصفحة، النص في الصفحة)
    ("10-CORE-Rawahil_Core_Theory_And_Manifesto.md",
     "السلوك ليس الأصل، بل هو نتيجة مباشرة لتفاعل البنية الداخلية للشخصية مع عوامل التوجيه المكتسبة",
     "index.html", "السلوك ليس الأصل، بل هو نتيجة مباشرة لتفاعل البنية الداخلية للشخصية مع عوامل التوجيه المكتسبة"),
    ("10-CORE-Rawahil_Core_Theory_And_Manifesto.md",
     "فالإنسان ليس مشروعاً معطوباً ينتظر الإصلاح",
     "index.html", "فالإنسان ليس مشروعاً معطوباً ينتظر الإصلاح"),
    ("10-CORE-Rawahil_Core_Theory_And_Manifesto.md",
     "لا ينشآن من تشابه البشر، بل من تكاملهم",
     "index.html", "لا ينشآن من تشابه البشر، بل من تكاملهم"),
    ("01-MASTER-Governance_Foundations_And_Decisions.md",
     "بناء إطار عربي أصيل وموثق علمياً لفهم الشخصية والأداء الإنساني",
     "about.html", "بناء إطار عربي أصيل وموثق علمياً لفهم الشخصية والأداء الإنساني"),
    ("56-PILOT-P001-LEADER_Individual_Report.md",
     "تخادم وتشكيل فريق", "teams.html", "تخادم وتشكيل فريق"),
    ("three_texts.json",
     "هذا التقرير **وصف لطريقة عملك**، لا حكم عليك",
     "index.html", "هذا التقرير وصف لطريقة عملك، لا حكم عليك"),
]


def check_anchors(pages):
    for src_file, src_q, page, page_q in ANCHORS:
        if src_q not in read(src_file):
            die(f"مرساة غائبة عن مصدرها {src_file}: «{src_q[:40]}…»")
        if page_q not in pages[page]:
            die(f"مرساة غائبة عن صفحتها {page}: «{page_q[:40]}…»")


# ═══════════════ ⑧ فاحص المخرجات ═══════════════

BANNED = ["تشخيص", "اضطراب", "مرض نفسي", "علاج نفسي", "معتمد علمياً", "درجة أفضل من"]

# جُمل مختومة من نصوص المحرك تَرِد فيها مفردة محظورة **نفياً لها** — تُجرَّد قبل
# الفحص بنمط سجلّ ح-5 نفسه: نص كامل لا شظية، وتغيّره يُسقط التسجيل ويوقف البناء.
ALLOWED_SEALED = [
    'قراءتك معلومة تشغيلية، لا "تشخيص" (لغة محظورة) ولا انفعال (K_3).',
]


def visible_text(html):
    html = re.sub(r"<script\b.*?</script>", " ", html, flags=re.S | re.I)
    html = re.sub(r"<style\b.*?</style>", " ", html, flags=re.S | re.I)
    html = re.sub(r"<!--.*?-->", " ", html, flags=re.S)
    return re.sub(r"<[^>]+>", " ", html)


def lint(name, html):
    if 'dir="rtl"' not in html or 'lang="ar"' not in html:
        die(f"{name}: بلا dir=rtl أو lang=ar")
    for m in re.finditer(r'(?:src|href)="(https?://[^"]+)"', html):
        if "github.com/maannaar16-o" not in m.group(1):
            die(f"{name}: مورد خارجي غير مسموح: {m.group(1)}")
    text = strip_registered(visible_text(html))
    hit = re.search(r"\d+(?:[.,]\d+)?\s*%", text)
    if hit:
        die(f"{name}: نسبة مئوية في النص المرئي: «{hit.group(0)}»")
    for t in ALLOWED_SEALED:
        text = text.replace(t, " ")
    for w in BANNED:
        if w in text:
            die(f"{name}: مفردة محظورة في النص المرئي: «{w}»")
    # «لا درجة أفضل — يوجد نمط مختلف» مسموح — الحظر على التفضيل المثبت لا النفي
    for bad in re.finditer(r"الأفضل درجة|أفضل درجةً", text):
        die(f"{name}: صياغة تفضيل درجات: «{bad.group(0)}»")


# ═══════════════ ⑨ التنفيذ ═══════════════

def main():
    check_vendor()

    # طبقة الحزم أولاً (CHG-054: مولَّدة لا تُرفع)
    r = subprocess.run([sys.executable, os.path.join(HERE, "build_packs.py")],
                       capture_output=True, text=True, cwd=HERE)
    if r.returncode != 0:
        die("build_packs.py أخفق:\n" + r.stderr[:500])

    items = parse_items()
    validate_maps()

    # فحوصات جانب JS
    cfg = os.path.join(HERE, "_site_checks.json")
    json.dump({"K2_EXPECT": K2_EXPECT, "K3_MAP": K3_MAP, "BLOCKS": BLOCKS},
              open(cfg, "w", encoding="utf-8"), ensure_ascii=False)
    r = subprocess.run(["node", os.path.join(SITE, "checks", "build_checks.js"), cfg],
                       capture_output=True, text=True, cwd=HERE)
    os.remove(cfg)
    if r.returncode != 0:
        die("فحوصات JS أخفقت:\n" + (r.stderr or r.stdout)[:900])
    print("✅ " + r.stdout.strip())

    kashaf, build_hash = build_kashaf(items)
    tabs, bodies = build_samples()
    pages = build_static_pages(tabs, bodies)
    pages["kashaf.html"] = kashaf

    check_anchors(pages)
    for name, html in pages.items():
        lint(name, html)
        # طبقة التطبيق (DEC-251): كل صفحة تحمل بيان التطبيق وتسجيل عامل الخدمة
        if 'rel="manifest"' not in html:
            die(f"{name}: بلا رابط بيان التطبيق")
        if 'serviceWorker" in navigator' not in html:
            die(f"{name}: بلا تسجيل عامل الخدمة")

    # المرحلة ② (DEC-252): مخزن الجهاز وقيد DEC-244 البنيوي حاضران في التطبيق
    app_src = read("site", "app", "app.js")
    if "indexedDB" not in app_src:
        die("app.js: طبقة IndexedDB غائبة")
    if "قراءة الفارق بين قياسين محظورة" not in app_src:
        die("app.js: لافتة DEC-244 للأرشيف غائبة")
    if "RAWAHIL-KASHAF-BACKUP-v1" not in app_src:
        die("app.js: مخطط النسخة الاحتياطية غائب")

    # المرآة (DEC-255/256): النصوص من الحزم حصراً — لا نسخة مقتبسة في كود التطبيق
    if "TEXTLAYER_K3" not in app_src or "function sepParts" not in app_src:
        die("app.js: وحدة المرآة أو مصدر حزمها غائب")
    for sealed_frag in ("تلتقط الإشارة", "التهدئة الحقيقية تُنهي",
                        "درجاتك في بعض الجوانب", "ظاهرها واحد وجذرها مختلف"):
        if sealed_frag in app_src:
            die(f"app.js: نص مختوم منسوخ في الكود («{sealed_frag}») — المصدر الحزم وحدها")

    # المرحلة ③ (DEC-253): نقاء باني الإسهام — لا حقل هوية في الحمولة
    m = re.search(r"function contribPayload\(answers\) \{.*?\n  \}", app_src, re.S)
    if not m:
        die("app.js: باني الإسهام contribPayload غائب")
    builder = m.group(0)
    for ident in ("name", "alias", "profile", "createdAt", "S\\."):
        if re.search(ident, builder):
            die(f"app.js: باني الإسهام يلمس حقل هوية «{ident}» — خرق DEC-253")
    if '"RAWAHIL-CONTRIB-v1"' not in builder:
        die("app.js: مخطط الإسهام غائب من الباني")
    if "slice(0, 7)" not in builder:
        die("app.js: طابع الإسهام ليس شهرياً — خرق تقليل البيانات")
    if "RAWAHIL-CONTRIB-v1" not in pages["contribute.html"]:
        die("contribute.html: مخطط الإسهام غائب")
    if "CPL-08A-03" not in pages["kashaf.html"]:
        die("kashaf.html: قفل صفر-الشبكة غائب — لا يُنشر بدونه")
    if "window.KASHAF_CONTRIB_ENDPOINT" not in pages["contribute.html"]:
        die("contribute.html: إعداد قناة الاستقبال غائب")

    # أيقونات التطبيق — موجودة وغير فارغة
    icons_src = os.path.join(SITE, "static", "icons")
    icon_names = ["icon-192.png", "icon-512.png", "icon-512-maskable.png"]
    for ic in icon_names:
        p = os.path.join(icons_src, ic)
        if not os.path.isfile(p) or os.path.getsize(p) < 1000:
            die(f"أيقونة غائبة أو فارغة: {ic}")

    # الكتابة — بعد اجتياز كل شيء فقط
    if os.path.isdir(DOCS):
        shutil.rmtree(DOCS)
    os.makedirs(os.path.join(DOCS, "assets", "icons"))
    open(os.path.join(DOCS, ".nojekyll"), "w").close()
    shutil.copyfile(os.path.join(SITE, "static", "site.css"),
                    os.path.join(DOCS, "assets", "site.css"))
    for ic in icon_names:
        shutil.copyfile(os.path.join(icons_src, ic),
                        os.path.join(DOCS, "assets", "icons", ic))
    for name, html in pages.items():
        with open(os.path.join(DOCS, name), "w", encoding="utf-8") as f:
            f.write(html)
    with open(os.path.join(DOCS, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(MANIFEST_JSON, f, ensure_ascii=False, indent=1)

    # عامل الخدمة — قائمة التخزين تُشتق من الناتج الفعلي (لا تُكتب يدوياً)
    assets = ["./"]
    for root_dir, _dirs, files in os.walk(DOCS):
        for fn in sorted(files):
            if fn in ("sw.js", ".nojekyll"):
                continue
            rel = os.path.relpath(os.path.join(root_dir, fn), DOCS).replace(os.sep, "/")
            assets.append("./" + rel)
    site_ver = hashlib.sha256(("".join(
        sha256(open(os.path.join(DOCS, a[2:]), "rb").read()) for a in sorted(assets) if a != "./"
    )).encode()).hexdigest()[:16]
    sw = SW_TEMPLATE.replace("__SITE_VER__", site_ver).replace(
        "__ASSETS__", json.dumps(sorted(assets), ensure_ascii=False))
    with open(os.path.join(DOCS, "sw.js"), "w", encoding="utf-8") as f:
        f.write(sw)
    # توكيد الاكتمال: كل ملف ناتج (عدا العامل نفسه) مذكور في قائمة التخزين
    listed = set(json.loads(re.search(r"const ASSETS = (\[.*?\]);", sw, re.S).group(1)))
    for a in assets:
        if a not in listed:
            die(f"sw.js: ملف ناقص من قائمة التخزين: {a}")
    if site_ver not in sw:
        die("sw.js: بصمة الموقع غائبة")

    print(f"\n✅ docs/ — {len(pages)} صفحات · بصمة البناء {build_hash} · بصمة الموقع (SW) {site_ver}")
    for name in sorted(pages):
        p = os.path.join(DOCS, name)
        b = os.path.getsize(p)
        print(f"   {name:14} {b:>9,} بايت  {sha256(open(p, 'rb').read())[:16]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
