"use strict";
/*
 * sp_gate.js — حرّاس مخرج العرض: `ح-4` و`ح-5`
 * ==============================================
 * نظيرٌ حرفي لـ`sp_gate.py`. سند: `DEC-183` · `DEC-230` · `DEC-232` · `ن-7` · `DEC-199`.
 *   `ح-4` حضور الرمز `SP%`            ← spGate()
 *   `ح-5` حضور نسبة مئوية غير مسجَّلة ← pctGate()
 * حارسان مستقلّان (`ن-7/②`) · حدّ قاطع لا مخترَع (`ن-7/④`).
 */
(function (root) {

  var SP_TOKEN  = /SP\s*%/gi;
  var PCT_VALUE = /\d+(?:[.,]\d+)?\s*%/g;

  var MENTION_REGISTRY = Object.create(null);

  // نصوص كاملة مُسنَدة إلى حزمة ومسار — مطابقة لنظيرتها في بايثون
  var PCT_REGISTRY = {
    "INTENSITY_K2:/S/A/M+/lock":
      'هذه أول كتلة "مشتعلة" (فوق 50%) — عدسة مساندة نشطة، لا ثانوية ولا ناقصة. `P = C + G`.',
    "CONTENT_K2:/R/lines/R-C-D/presence":
      "تشغيلك اليومي داخل التزام آمن؛ تختبر البديل في بيئة معزولة ثم يُحوَّل سابقةً معتمدة — كفاءة فورية والتزام 100%"
  };

  function mkErr(name, message) { var e = new Error(message); e.name = name; return e; }
  function ctx(t, i) { return t.slice(Math.max(0, i - 60), i + 40).replace(/\n/g, " "); }
  function fmt(hits) {
    return hits.slice(0, 8).map(function (h) { return "    [" + h[0] + "] …" + h[1] + "…"; }).join("\n");
  }

  function scan(text) {
    if (typeof text !== "string") return [];
    var hits = [], m; SP_TOKEN.lastIndex = 0;
    while ((m = SP_TOKEN.exec(text)) !== null) {
      var c = ctx(text, m.index);
      if (Object.prototype.hasOwnProperty.call(MENTION_REGISTRY, c.trim())) continue;
      hits.push([m.index, c]);
    }
    return hits;
  }

  function spGate(text, where) {
    where = where || "<مخرج غير مسمّى>";
    var hits = scan(text);
    if (hits.length) throw mkErr("SPLeakError",
      "ح-4/DEC-183 — الرمز `SP%` حاضر في مخرج «" + where + "» (" +
      hits.length + " إصابة). الإصدار موقوف.\n" + fmt(hits));
    return text;
  }

  function stripRegistered(text) {
    for (var k in PCT_REGISTRY) {
      if (!Object.prototype.hasOwnProperty.call(PCT_REGISTRY, k)) continue;
      text = text.split(PCT_REGISTRY[k]).join("");
    }
    return text;
  }

  function scanPct(text) {
    if (typeof text !== "string") return [];
    var s = stripRegistered(text), hits = [], m;
    PCT_VALUE.lastIndex = 0;
    while ((m = PCT_VALUE.exec(s)) !== null) hits.push([m.index, ctx(s, m.index)]);
    return hits;
  }

  function pctGate(text, where) {
    where = where || "<مخرج غير مسمّى>";
    var hits = scanPct(text);
    if (hits.length) throw mkErr("PctLeakError",
      "ح-5/DEC-183 — نسبة مئوية غير مسجَّلة في مخرج «" + where + "» (" +
      hits.length + " إصابة). الإصدار موقوف.\n" + fmt(hits));
    return text;
  }

  function outputGate(text, where) { spGate(text, where); pctGate(text, where); return text; }

  var API = { scan: scan, spGate: spGate, scanPct: scanPct, pctGate: pctGate,
              outputGate: outputGate, SP_TOKEN: SP_TOKEN, PCT_VALUE: PCT_VALUE,
              MENTION_REGISTRY: MENTION_REGISTRY, PCT_REGISTRY: PCT_REGISTRY };
  if (typeof module !== "undefined" && module.exports) module.exports = API;
  root.RawahilSPGate = API;

})(typeof window !== "undefined" ? window : globalThis);
