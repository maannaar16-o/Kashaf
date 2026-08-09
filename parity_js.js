"use strict";
/**
 * parity_js.js — الطرف JS من أداة التكافؤ (DEC-199 · DEC-200)
 * ============================================================
 * يُنتج بصمة SHA-256 لكل حالة وفق التطبيع المنصوص في 87-PARITY §4:
 *   · مفاتيح مرتَّبة تصاعدياً بنقطة الترميز حصراً (لا localeCompare)
 *   · كل عدد يُسلسَل نصّاً بمنزلة عشرية واحدة ثابتة (50.0 لا 50)
 *   · بلا مسافات زائدة
 * ويُقارَن الناتج بالطرف البايثوني. التطابق تامّ بلا هامش.
 */
const crypto = require("crypto");
const fs = require("fs");
const { K2, K3, InputContractError } = require("./engines.js");

// ── التقنين ──────────────────────────────────────────────────────────────
function canon(v) {
  if (v === null) return "null";
  if (typeof v === "boolean") return v ? "true" : "false";
  if (typeof v === "number") {
    if (!Number.isFinite(v)) throw new Error("عدد غير منتهٍ في المخرج");
    // تطبيع إلزامي — يزيل تباين str(50.0)="50.0" مقابل String(50.0)="50"
    return (Math.round(v * 10) / 10).toFixed(1);
  }
  if (typeof v === "string") return JSON.stringify(v);
  if (Array.isArray(v)) return "[" + v.map(canon).join(",") + "]";
  const keys = Object.keys(v).sort((a, b) => (a < b ? -1 : a > b ? 1 : 0));
  return "{" + keys.map((k) => JSON.stringify(k) + ":" + canon(v[k])).join(",") + "}";
}

const sha = (s) => crypto.createHash("sha256").update(s, "utf8").digest("hex").slice(0, 16);

// ── حالات الاختبار ───────────────────────────────────────────────────────
const CASES = JSON.parse(fs.readFileSync(process.argv[2] || "parity_cases.json", "utf8"));

const out = { k2: {}, k3: {}, failure: {} };

for (const [name, sp] of Object.entries(CASES.k2)) {
  const r = K2.run({ sp });
  out.k2[name] = canon({
    center: r.profile.center,
    ranked: r.profile.ranked,
    dominant: r.profile.dominant,
    support: r.profile.support,
    off: r.profile.off,
    ignited: r.profile.ignited,
    lines: r.lines,
    t8: r.t8,
    delivery: r.delivery_questions,
    stitch: r.stitch,
    codes: Object.fromEntries(K2.LENSES.map((d) => [d, K2.octalCode(sp[d])])),
  });
}

for (const [name, sp] of Object.entries(CASES.k3)) {
  const r = K3.run(sp);
  // نطاق هذا المقارن: طبقة المنطق. التركيب النصّي يُقارَن في parity_reports.
  out.k3[name] = canon({
    sp: r.sp, codes: r.codes, bands: r.bands,
    cells_activated: r.cells_activated, cost_map: r.cost_map,
    patterns_recognized: r.patterns_recognized,
    containment_state: r.containment_state, root_question: r.root_question,
    excluded_out: r.excluded_out, gates_fired: r.gates_fired,
    engine_version: r.engine_version, spec_version: r.spec_version,
    instrument_pin: r.instrument_pin,
  });
}

// ── تكافؤ سلوك الفشل (87-PARITY §5) ──────────────────────────────────────
function failMode(fn) {
  try { fn(); return "no-error"; }
  catch (e) { return e.name === "InputContractError" ? "InputContractError" : "other:" + e.name; }
}
out.failure["k2:y+z!=7"]   = failMode(() => K2.computeSsSp(30, 5, 1));
out.failure["k2:y+z==7"]   = failMode(() => K2.computeSsSp(30, 5, 2));
out.failure["k3:y+z!=11"]  = failMode(() => K3.computeSsSp(44, 8, 4));
out.failure["k3:y+z==11"]  = failMode(() => K3.computeSsSp(44, 8, 3));
out.failure["k2:missing-lens"] = failMode(() => K2.run({ sp: { A: 50 } }));

// ── مسح الحدود (DEC-133 · DEC-184) ───────────────────────────────────────
out.boundary = {};
for (const v of [-0.1, 0, 19.9, 20, 20.1, 39.9, 40, 40.1, 49.9, 50, 50.1, 69.9, 70, 70.1, 85, 100, 100.1]) {
  out.boundary[`k2:${v}`] = canon([K2.octalCode(v), K2.compState(v)]);
  out.boundary[`k3:${v}`] = canon([K3.octalCode(v), K3.band(v), K3.pole(v)]);
}

const hashes = {};
for (const grp of ["k2", "k3"]) {
  hashes[grp] = Object.fromEntries(Object.entries(out[grp]).map(([k, v]) => [k, sha(v)]));
}
hashes.failure = out.failure;
hashes.boundary = out.boundary;
// DEC-202 — سجل التجميد داخل البصمة: لا يُوسَّع صامتاً
const frozenPath = require("path").join(__dirname, "parity_frozen.json");
const frozenKeys = fs.existsSync(frozenPath)
  ? Object.keys(JSON.parse(fs.readFileSync(frozenPath, "utf8")))
  : [];
hashes.frozen_registry = sha(canon(frozenKeys.sort((a, b) => (a < b ? -1 : a > b ? 1 : 0))));
hashes.GLOBAL = sha(canon(hashes));

process.stdout.write(JSON.stringify({ hashes, raw: out }, null, 0));
