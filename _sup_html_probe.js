"use strict";
/*
 * _sup_html_probe.js — مِسبار تشغيل الحزمة المولَّدة في `Supervisor.html`
 * ======================================================================
 * سند: `DEC-271` · درس `DEC-269` (البناء الناجح ليس تشغيلاً ناجحاً).
 *
 * لا منطق هنا: يُقيم نطاقاً عامّاً أدنى، **ينفّذ كتلة الوحدات كما وُلِّدت
 * حرفياً** (لا كما هي في المستودع)، ثم يحكم حمولةً حقيقية من كل دائرة.
 * فما ينكسر في التشييم يظهر هنا لا في يد المستخدم.
 */
const fs = require("fs");
const vm = require("vm");

const modules = fs.readFileSync(process.argv[2], "utf8");
const sandbox = { console, JSON, Math, Date, Object, Array, String, Number,
                  Boolean, Error, TypeError, RangeError, isNaN, isFinite,
                  parseInt, parseFloat, undefined: undefined };
sandbox.window = sandbox;
sandbox.globalThis = sandbox;
vm.createContext(sandbox);
vm.runInContext(modules, sandbox, { filename: "Supervisor.html#modules" });

const RP = sandbox.window.RawahilReports;
const SV = sandbox.window.RawahilSupervisor;
const out = { present: {}, graded: {} };
out.present = {
  engines: !!sandbox.window.RawahilEngines,
  k4engine: !!(sandbox.window.RawahilEngines && sandbox.window.RawahilEngines.K4),
  packs: !!sandbox.window.RawahilPacks,
  packK4: !!(sandbox.window.RawahilPacks && sandbox.window.RawahilPacks.PACKS.CONTENT_K4),
  gate: !!sandbox.window.RawahilSPGate,
  reports: !!RP, supervisor: !!SV,
  buildK4: !!(RP && RP.buildReportK4),
  crossing: !!(RP && RP.buildCrossingSurface),
};

function judge(tag, payload) {
  try {
    const r = SV.grade(payload);
    out.graded[tag] = { grades: r[0].length, errors: r[1].length, err0: r[1][0] || "" };
  } catch (e) { out.graded[tag] = { exception: e.name + ": " + e.message }; }
}

// K2 — الدائرة الأصل، للتأكد أن التشييم لم يكسر ما كان يعمل
try {
  // قاموس SP تركيبي — كما في الفحص الذاتي المصوَّب (لا ثلاثيات خام)
  const sp2 = { A: 80.0, R: 60.0, C: 55.0, O: 45.0,
                S: 70.0, E: 40.0, St: 50.0, H: 65.0 };
  const p2 = RP.buildReportK2(sp2, "full");
  judge("k2", { schema: "RAWAHIL-REPORT-v1.2", circle: "K2", scopes: ["full"],
                delivery: { markdown: p2[0] }, audit: p2[1] });
} catch (e) { out.graded.k2 = { exception: "توليد: " + e.message }; }

// K4 — الدائرة المستجدّة، بسطحها العابر ثم مُفسَدةً بحذف دَين الميدان
try {
  const sp4 = { WM: 62, TI: 38, F: 74, PF: 44, OR: 55, TM: 41, PER: 40 };
  const p4 = RP.buildReportK4(sp4), x4 = RP.buildCrossingSurface(sp4);
  const b4 = { schema: "RAWAHIL-REPORT-v1.2", circle: "K4", scopes: ["full"],
               delivery: { markdown: p4[0] }, audit: p4[1] };
  if (x4[0]) { b4.delivery.markdown_crossing = x4[0]; b4.audit_crossing = x4[1]; }
  out.k4 = { body: p4[0].length, sha: p4[1].report_sha256,
             packSha: (p4[1].pack_sha || {}).CONTENT_K4 || null,
             surface: x4[0].length, entries: (x4[1].entries || []).length };
  judge("k4", b4);
  const bad = JSON.parse(JSON.stringify(b4));
  bad.audit.open_debts = (bad.audit.open_debts || [])
    .filter((d) => d !== "DEBT-K4-FIELD-01");
  judge("k4_debt_stripped", bad);
  const merged = JSON.parse(JSON.stringify(b4));
  merged.delivery.markdown += "\n" + merged.delivery.markdown_crossing;
  judge("k4_surface_merged", merged);
} catch (e) { out.graded.k4 = { exception: "توليد: " + e.message }; }

process.stdout.write(JSON.stringify(out));
