"use strict";
/**
 * parity_k4_js.js — الطرف JS من أداة تكافؤ محرّك K4 (DEC-266)
 * ==============================================================
 * التقنين مطابق حرفياً لنظيره في `parity_js.js` (87-PARITY §4):
 *   · مفاتيح مرتَّبة بنقطة الترميز حصراً (لا localeCompare)
 *   · كل عدد بمنزلة عشرية واحدة ثابتة · بلا مسافات زائدة
 * لا أسبقية لطرف على طرف — أي اختلاف يجمّد الاثنين (DEC-200).
 */
const crypto = require("crypto");
const fs = require("fs");
const { K4, InputContractError } = require("./engines.js");
const { buildReportK4, buildCrossingSurface } = require("./reports.js");

function canon(v) {
  if (v === null || v === undefined) return "null";
  if (typeof v === "boolean") return v ? "true" : "false";
  if (typeof v === "number") {
    if (!Number.isFinite(v)) throw new Error("عدد غير منتهٍ في المخرج");
    return (Math.round(v * 10) / 10).toFixed(1);
  }
  if (typeof v === "string") return JSON.stringify(v);
  if (Array.isArray(v)) return "[" + v.map(canon).join(",") + "]";
  const keys = Object.keys(v).sort((a, b) => (a < b ? -1 : a > b ? 1 : 0));
  return "{" + keys.map((k) => JSON.stringify(k) + ":" + canon(v[k])).join(",") + "}";
}

const sha = (s) => crypto.createHash("sha256").update(s, "utf8").digest("hex").slice(0, 16);

const CASES = JSON.parse(fs.readFileSync(process.argv[2] || "parity_cases_k4.json", "utf8"));

const out = { k4: {}, report: {}, crossing: {}, failure: {} };
const raw = { k4: {}, report: {}, crossing: {}, failure: {} };

for (const [name, sp] of Object.entries(CASES.k4)) {
  const a = K4.run(sp).audit;
  const s = canon(a);
  raw.k4[name] = s;
  out.k4[name] = sha(s);
  const [body, repAudit] = buildReportK4(sp);
  const sRep = body + "\u0000" + canon(repAudit);
  raw.report[name] = sRep;
  out.report[name] = sha(sRep);
  const [xbody, xa] = buildCrossingSurface(sp);
  const xs = xbody + "\u0000" + canon(xa);
  raw.crossing[name] = xs;
  out.crossing[name] = sha(xs);
}

for (const [name, spec] of Object.entries(CASES.failure)) {
  let mode;
  // القيم النصية "NaN"/"Infinity" تُحوَّل عدداً في الطرفين قبل التمرير —
  // كي يقيس الاختبارُ عقدَ المحرك لا تحويلَ JSON.
  const cast = {};
  for (const k of Object.keys(spec)) {
    const v = spec[k];
    cast[k] = (v === "NaN" || v === "Infinity" || v === "-Infinity") ? Number(v) : v;
  }
  try {
    K4.run(cast);
    mode = "no-error";
  } catch (e) {
    mode = e instanceof InputContractError ? "InputContractError" : "other:" + e.name;
  }
  const s = canon({ mode });
  raw.failure[name] = s;
  out.failure[name] = sha(s);
}

const globalStr = canon({ k4: out.k4, report: out.report, crossing: out.crossing, failure: out.failure });
out.GLOBAL = sha(globalStr);

process.stdout.write(JSON.stringify({ hashes: out, raw }));
