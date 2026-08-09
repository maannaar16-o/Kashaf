"use strict";
/**
 * reports.js — مُركّبا التقرير الفردي (K2 · K3) — المرحلة ③
 * ==========================================================
 * نقل حرفي لمنطق `k2_report.py` و`k3_report.py` بعد إصلاحاتهما المختومة.
 * 🔒 يجمّع ولا يؤلّف: كل نصّ من `packs.js`؛ ولا سطر مؤلَّف هنا.
 *
 * القرارات المطبَّقة:
 *   DEC-183  حذف SP% من الشاشة وكل التصديرات (K2 و K3)
 *   DEC-187  K2: الحالة بالكلمة + الرمز · K3: كلمات النطاق فقط (ق1)
 *   DEC-188  «قبل أن تقرأ» يُبقى حرفياً
 *   DEC-190  K2: استدعاء المداخل بالوظيفة لا بالرقم + حارس _CARD
 *   DEC-195/ج K3: المشترك في ② · الخاتمات في ③
 *   DEC-196  K3: BAND_LABEL["OUT"] صريح + إيقاف عند نطاق مجهول
 *   DEC-197/ج K3: الاسم المزدوج في العنوان متى اختلف الاسمان
 *
 * المؤجَّل لآخر خطوة (بأمر المالك): DEC-189 §8.1 · TC-K2-01 ·
 *   GAP-RPT-K2-01/02/03 · RSK-DUP-01.
 */

const { K2, K3 } = require("./engines.js");
const PK = require("./packs.js");
const { PACKS, verifyPacks } = PK;
const SPG = require("./sp_gate.js");   // ح-4 · DEC-183 · ن-7

const AR_NUM = "١٢٣٤٥٦٧٨٩";

// ════════════════════════════════════════════════════ أسطر الوصل (K2) ═══
// k2_framing — قائمة مغلقة. يُحظر تعديل صياغتها (56-REPORT-ENGINE الملحق أ).
const J1 = (section) => `> فيما يلي ${section}:`;
const J6 = "نهاية التقرير.";
const PCG_LOCK = "الدرجة تصف موقع العدسة في ترتيب تفضيلك المعرفي الفطري، " +
                 "لا مستوى قدرتك ولا جودة أدائك. لا درجة «أفضل» — يوجد نمط مختلف.";

// ═════════════════════════════════════════════════════════════ K2 ═══════

class SlotResolutionError extends Error {
  constructor(m) { super(m); this.name = "SlotResolutionError"; }
}

const SLOT_KW = {
  CYCLE: "دورة المعالجة", ENGINE: "المحرك", POSITION: "الموقع في الفريق",
  BLIND: "نقطة العمى", PRESSURE: "الضغط القصوى", FOOTPRINT: "البصمة",
  NOTMINE: "ما لا تعنيه",
};
// DEC-211/ج₂ — الأنماط الأربعة تامّة التغطية + الآلية الخاصة
const FILTER_KW = ["قاعدة الإهمال", "قاعدة الاختزال", "قاعدة الحجب", "صانع الشكل",
                   "العدسة الأفقية", "القراءة الهادئة", "العدسة التوسيعية"];
const MECH_KW = ["الملاذ الإبداعي", "الحس الزمني", "سلطة الاعتراض", "المنطق الاقتصادي",
                 "المغلِّف لا المصدر", "الرادار لا يُستغَل", "المخرج إمكان لا قرار"];
const CENTER_SLOTS = ["CYCLE", "ENGINE", "POSITION"];
const SUPPORT_SLOTS = ["CYCLE", "ENGINE", "POSITION"];
const _CARD = {
  CYCLE: [1, 1], ENGINE: [1, 1], POSITION: [1, 1], BLIND: [1, 2],
  PRESSURE: [1, 1], FOOTPRINT: [1, 1], NOTMINE: [0, 1],
};

const _sortCP = (arr) => arr.slice().sort((a, b) => (a < b ? -1 : a > b ? 1 : 0));

function resolveSlot(dim, slot, strict = true) {
  const kw = SLOT_KW[slot];
  const layer = PACKS.USERLAYER_K2[dim] || {};
  const hits = _sortCP(Object.keys(layer)).filter((k) => layer[k].title.includes(kw));
  const [lo, hi] = _CARD[slot];
  if (strict && !(hits.length >= lo && hits.length <= hi)) {
    throw new SlotResolutionError(
      `DEF-K2-01/حارس: البُعد ${dim} · الوظيفة ${slot} → ${hits.length} مدخلاً ` +
      `(المتوقَّع ${lo}..${hi}). لا يُخمَّن مدخل — يُصدر تقرير فجوة.`);
  }
  return hits;
}

function resolveBy(dim, keywords) {
  const layer = PACKS.USERLAYER_K2[dim] || {};
  return _sortCP(Object.keys(layer)).filter((k) => keywords.some((w) => layer[k].title.includes(w)));
}
const slotFilter  = (d) => resolveBy(d, FILTER_KW);
const slotNoise   = (d) => resolveBy(d, ["الإزعاج"]);
const slotOthers  = (d) => resolveBy(d, ["قراءة الآخرين"]);
const slotEconomy = (d) => resolveBy(d, ["اقتصاد الطاقة"]);
const slotMech    = (d) => resolveBy(d, MECH_KW);

function validateSlots() {
  const out = [];
  for (const d of Object.keys(PACKS.USERLAYER_K2)) {
    for (const sl of Object.keys(SLOT_KW)) {
      try { resolveSlot(d, sl); }
      catch (e) { out.push(String(e.message)); }
    }
  }
  return out;
}

let _USED = [];

/** تجزئة مقنَّنة — نظير _sha البايثوني (مفاتيح مرتَّبة · بلا فراغ). */
function _shaObj(o) {
  const canon = (v) => {
    if (v === null) return "null";
    if (typeof v !== "object") return JSON.stringify(v);
    if (Array.isArray(v)) return "[" + v.map(canon).join(",") + "]";
    const ks = Object.keys(v).sort((a, b) => (a < b ? -1 : a > b ? 1 : 0));
    return "{" + ks.map((k) => JSON.stringify(k) + ":" + canon(v[k])).join(",") + "}";
  };
  return PK._sha256(canon(o)).slice(0, 16);
}

function _catalog(dim, entries) {
  const layer = PACKS.USERLAYER_K2[dim];
  if (!layer) return null;
  const out = [];
  for (const code of entries) {
    const e = layer[code];
    if (e && e.user) { _USED.push(`K2-${dim}-${code}`); out.push(`- **${e.title.split("(")[0].trim()}:** ${e.user}`); }
  }
  return out.length ? out : null;
}

// R9 — بوابة التطهير (DEC-212/ب): العبارة المحظورة **كاملة**؛ الشظايا مرفوضة بالقياس
const R11_TAG = "[تجاور عاملي موثق — حزمة توليد-توجيه]";

/** R11 — العرض المزدوج St+H (حسم M-07/الخيار ج): وسم · LD-02 · حظر الفصل الرقمي. */
function r11Block(profile) {
  if (!(profile.sp.St > 50 && profile.sp.H > 50)) return [];
  const ld = PACKS.LOOKALIKE_K2.LD["LD-02"];
  _USED.push("LD-02");                          // DEC-222
  return [`> وسم إلزامي: ${R11_TAG}`, "",
    `- **${K2.LENS_NAME.H} (H):** ${ld.second}`,
    `- **${K2.LENS_NAME.St} (St):** ${ld.first}`,
    "", `> ${ld.question}`,
    "> يُقرآن حزمةً واحدة لا عدستين منفصلتين — ويُحظر فصل إسهامهما رقمياً.", ""];
}

const LOCK_PREFIX = "  > 🔒 ";

/** DEC-217/ب — أسطر الأقفال تُستثنى: القفل يذكر المصطلح ليمنع الخلط. */
/** DEC-229 — فحص محتوى حقول القفل: يرصد الاستجداد لا المشروعية. */
/** `ح-7` (`DEC-241`) — سلامة الصياغة المسجَّلة داخل حقل القفل.
 *  نظيرٌ حرفي لـ`scan_lock_drift` البايثونية. يرصد **الانقلاب** لا الاستجداد:
 *  ① السياق المسجَّل حاضر حرفياً · ② كل ظهور للمصطلح داخله (تكرار متساوٍ).
 *  **حدّه:** لا يحكم على المعنى — يُثبت أن الصياغة المعتمدة لم تتغيّر. */
function scanLockDrift() {
  const reg = PACKS.LOCKREG_K2.ACCEPTED_LOCK_MENTIONS;
  const hits = [];
  const count = (hay, needle) => hay.split(needle).length - 1;
  for (const bands of Object.values(PACKS.INTENSITY_K2.S)) {
    for (const v of Object.values(bands)) {
      const lock = v.lock || "";
      if (!lock) continue;
      for (const [key, entry] of Object.entries(reg)) {
        if (!key.startsWith(v.code + "|")) continue;
        const term = entry.term, ctx = entry.context;
        if (!lock.includes(ctx)) {
          hits.push({ check: "قفل-منجرف", unit: v.code,
                      term: term.slice(0, 40), why: "الصياغة المسجَّلة غائبة" });
        } else if (count(lock, term) !== count(ctx, term)) {
          hits.push({ check: "قفل-منجرف", unit: v.code,
                      term: term.slice(0, 40), why: "ذِكرٌ خارج الصياغة المسجَّلة" });
        }
      }
    }
  }
  return hits;
}

function scanLockFields() {
  const reg = PACKS.LOCKREG_K2.ACCEPTED_LOCK_MENTIONS;
  const hits = [];
  for (const [d, bands] of Object.entries(PACKS.INTENSITY_K2.S)) {
    for (const v of Object.values(bands)) {
      const lock = v.lock || "";
      if (!lock) continue;
      const terms = K2.FORBIDDEN.filter((w) => lock.includes(w))
        .concat((PACKS.PUR_K2.PUR[d] || []).filter((r) => lock.includes(r.forbidden))
          .map((r) => r.forbidden));
      for (const t of terms) {
        if (!(`${v.code}|${t}` in reg)) {
          hits.push({ check: "قفل-مستجدّ", unit: v.code, term: t.slice(0, 40) });
        }
      }
    }
  }
  return hits;
}

function stripLocks(text) {
  const kept = [];
  let n = 0;
  for (const ln of text.split("\n")) {
    if (ln.startsWith(LOCK_PREFIX)) n += 1; else kept.push(ln);
  }
  return [kept.join("\n"), n];
}

// R1 — كتل الشدة الثماني (إلزامية · 51-MATRIX-06/R1)
const _BAND_ALIAS = { "L-": "L−" };

function intensityBlock(dim, code) {
  const key = _BAND_ALIAS[code] || code;
  const b = ((PACKS.INTENSITY_K2.S[dim] || {})[key]);
  if (b) _USED.push(b.code);                    // DEC-222
  if (!b) throw new SlotResolutionError(`R1/حارس: كتلة الشدة K2-${dim}-S-${key} غائبة — لا تُخمَّن.`);
  return b;
}

const _CW = /[\u0600-\u06FF]{4,}/g;
const _contentWords = (t) => new Set(String(t).match(_CW) || []);

/** ت-6 (DEC-224) — تطابق مضموني: يرصد الاحتواء التامّ ويُبلِّغ أقصى تداخل. */
/** تقريب موحَّد لمنزلتين (`DEC-238`) — نصفٌ لأعلى بصيغة صريحة.
 *  نظيرٌ بتّي لـ`_round2` البايثونية؛ لا اتّكال على `Math.round` ولا على
 *  `round()`، فقد أعطتا `0.13` مقابل `0.12` عند `0.125`. */
function _round2(v) { return Math.floor(v * 100 + 0.5) / 100; }

function t6Guard(deliveryLines, calledUnits) {
  const hits = [];
  let worst = 0;
  for (const ln of deliveryLines) {
    const w = _contentWords(ln);
    if (!w.size) continue;
    for (const unit of calledUnits) {
      const wu = _contentWords(unit);
      if (!wu.size) continue;
      let inter = 0;
      for (const x of w) if (wu.has(x)) inter += 1;
      const ratio = inter / w.size;
      if (ratio > worst) worst = ratio;
      if (ratio >= 1.0) { hits.push({ check: "ت-6", line: ln.slice(0, 50), unit: unit.slice(0, 50) }); break; }
    }
  }
  return [hits, _round2(worst)];
}

function purGate(text, dims) {
  const hits = [];
  for (const d of dims) {
    for (const row of (PACKS.PUR_K2.PUR[d] || [])) {
      if (text.includes(row.forbidden)) {
        hits.push({ dim: d, check: "PUR", token: row.forbidden.slice(0, 40),
                    alt: row.alt.slice(0, 60) });
      }
    }
  }
  return hits;
}

function purScanPacks(dims) {
  const hits = [];
  for (const d of dims) {
    const layer = PACKS.USERLAYER_K2[d] || {};
    for (const code of Object.keys(layer)) {
      for (const row of (PACKS.PUR_K2.PUR[d] || [])) {
        if (String(layer[code].user || "").includes(row.forbidden)) {
          hits.push({ dim: d, entry: code, token: row.forbidden.slice(0, 40) });
        }
      }
    }
  }
  return hits;
}

function _board(profile) {
  // DEC-183: لا SP · DEC-187: الحالة بالكلمة + الرمز
  const rows = ["| البُعد | الرمز | الحالة |", "| :-- | :--: | :-- |"];
  const st = { D: "مهيمنة", M: "مساندة", L: "منطفئة" };
  for (const d of profile.ranked) {
    const sp = profile.sp[d];
    const tag = (d === profile.center) ? "🎯 المركز" : st[K2.compState(sp)];
    rows.push(`| ${K2.LENS_NAME[d]} (${d}) | ${K2.octalCode(sp)} | ${tag} |`);
  }
  return rows.join("\n");
}

function _k2line(code) {
  const center = code.split("-")[0];
  const pack = PACKS.CONTENT_K2[center];
  if (pack && pack.lines && code in pack.lines) return pack.lines[code];
  throw new Error(`سطر «${code}» غير موجود في أي مصدر معتمد.`);
}

// DEC-225/و — نطاقا العرض: brief = R2/R3 حرفياً · full = DEC-211/ج₂
// ════════════════════════════════════ محوّل حزمة المحتوى (DEC-236) ═══
/**
 * نظير `ContentPack.texts_for` في `k2_content.py` — يجمع نصوص المصدر
 * المستدعاة فعلاً لهذا الملف كي يمسحها تدقيق العزل في المحرّك.
 *
 * مطابقة حرفية مقصودة: نصّ العمى أولاً، ثم لكل عدسة غير المركز
 * `presence` فـ`recommendation`، بترتيب مفاتيح `sp` نفسه. والمفقود
 * **يُتجاوَز صمتاً** كما في بايثون — لا يُرفع استثناء.
 */
const K2_CONTENT_ADAPTER = {
  textsFor(profile) {
    const out = [];
    const c = profile.center;
    const pack = PACKS.CONTENT_K2[c];
    if (pack && pack.blindness) out.push(pack.blindness);
    for (const lens of Object.keys(profile.sp)) {
      if (lens === c) continue;
      const v = profile.sp[lens];
      const st = v > 70 ? "D" : v > 50 ? "M" : "L";
      const ln = pack && pack.lines ? pack.lines[`${c}-${lens}-${st}`] : null;
      if (!ln) continue;                       // نظير MissingContentError المتجاوَز
      out.push(ln.presence, ln.recommendation || "");
    }
    return out.filter(Boolean);
  },
};

function buildReportK2(sp, mode) {
  mode = mode || "full";
  _USED = [];                                   // DEC-220
  const res = K2.run({ sp, content: K2_CONTENT_ADAPTER });   // DEC-236
  const c = res.profile.center;
  const L = [];
  let n = 0;
  const extPending = [];

  const head = (t) => { n += 1; L.push(`## ${AR_NUM[n - 1]} · ${t}`, J1(t), ""); };

  // ① قبل أن تقرأ — DEC-188: حرفياً
  head("قبل أن تقرأ"); L.push(`> ${PCG_LOCK}`, "");

  // ② لوحة الرموز
  head("لوحة رموزك الثمانية"); L.push(_board(res.profile), "");
  L.push("**ماذا يعني رمز كل عدسة عندك:**", "");
  for (const d of res.profile.ranked) {
    const b = intensityBlock(d, K2.octalCode(res.profile.sp[d]));
    L.push(`- **${K2.LENS_NAME[d]} (${d}) — ${b.code.split("-").pop()}`
      + (b.label ? ` · ${b.label}` : "") + `:** ` + b.user);
    if (b.lock) L.push(`  > 🔒 ${b.lock}`);
  }
  L.push("");

  // ③ مركزك
  const centerEntries = CENTER_SLOTS.flatMap((sl) => resolveSlot(c, sl));
  const cat = _catalog(c, centerEntries);
  head(`مركزك — ${K2.LENS_NAME[c]}`);
  if (cat) L.push(...cat, "");
  else { extPending.push(`55-USER-K2-${c}`); L.push("> وسم إلزامي: [كتالوج المركز — خارجي]", ""); }   // DEC-210 · ج-4

  // ④ عدساتك المهيمنة والمساندة
  // DEF-K2-03 — المركز قد يقع في support إن كان SP ≤ 70
  const others = res.profile.dominant.concat(res.profile.support).filter((d) => d !== c);
  if (others.length) {
    head("عدساتك المهيمنة والمساندة");
    for (const d of others) {
      const sc = _catalog(d, SUPPORT_SLOTS.flatMap((sl) => resolveSlot(d, sl)));
      L.push(`### ${K2.LENS_NAME[d]} (${d}) — ${K2.octalCode(res.profile.sp[d])}`);
      L.push(...(sc || ["> وسم إلزامي: [محتوى خارجي]"]), "");
    }
  }

  // العدسات المعروضة — المركز + المهيمنة + المساندة
  const shown = (mode === "brief") ? [c] : [c].concat(others);
  const sub = (d, entries) => {
    const e = _catalog(d, entries);
    if (e) { L.push(`### ${K2.LENS_NAME[d]} (${d})`); L.push(...e, ""); }
    return Boolean(e);
  };

  // ⑤ كيف تتركّب عدساتك
  head("كيف تتركّب عدساتك");
  L.push("**نقطة عماك — مقروءةً مع ملفك (ت-8):**", "");
  for (const h of res.t8) L.push(`- ${h.half}: ${h.phrase}.`);
  if (res.stitch) L.push("", `> ${res.stitch}`);
  L.push("");
  const cov = res.lines.filter((x) => x.kind === "coverage");
  const col = res.lines.filter((x) => x.kind === "coloring");
  L.push("**تغطية عماك عبر عدساتك:**", "");
  for (const x of cov) L.push(`- ${_k2line(x.code).presence}`);
  L.push("", "**كيف تلوّن عدساتك تعبيرك:**", "");
  for (const x of col) L.push(`- ${_k2line(x.code).presence}`);
  L.push("");
  L.push("**ما تُسقطه كل عدسة قبل أن تعالج · ونقطة عماها:**", "");
  for (const d of shown) sub(d, slotFilter(d).concat(resolveSlot(d, "BLIND")));

  // ⑥ حين تلتقي عدستان
  head("حين تلتقي عدستان");
  const r11 = r11Block(res.profile);
  if (r11.length) L.push("**حين يشتعل التوليد والتوجيه معاً (R11):**", "", ...r11);
  L.push("**كيف تقرأ من أمامك بكل عدسة:**", "");
  for (const d of shown) sub(d, slotOthers(d));

  // ⑦ تحت الضغط
  head("تحت الضغط");
  for (const d of shown) sub(d, resolveSlot(d, "PRESSURE").concat(slotNoise(d)));

  // ⑧ أسئلة تخصّك (ت-7)
  head("أسئلة تخصّك وحدك");
  L.push(res.delivery_questions.length
    ? "> هذه أسئلة تساعدك على قراءة ما سبق بنفسك — لا أحكام."
    : "> ملاحظة تخادم: راجع مقطع كيف تتركّب عدساتك.", "");
  for (const code of res.delivery_questions) L.push(`- ${_k2line(code).question}`);
  L.push("");

  // ⑨ نقاط عماك · بصمتك
  head("نقاط عماك · بصمتك");
  if (res.profile.off.length) {
    L.push("> غياب أولوية لا نقص — تُغطّى بالتخادم لا بالإصلاح الذاتي (P = C + G).", "");
    for (const d of res.profile.off) {
      L.push(`- **${K2.LENS_NAME[d]} (${d})** منطفئة (${K2.octalCode(res.profile.sp[d])}).`);
    }
    L.push("");
  }
  for (const d of shown) {
    const ok = sub(d, resolveSlot(d, "FOOTPRINT")
      .concat(resolveSlot(d, "NOTMINE", false), slotEconomy(d), slotMech(d)));
    if (!ok && d === c) { extPending.push(`55-USER-K2-${c}/البصمة`); L.push("> وسم إلزامي: [محتوى خارجي]", ""); }
  }

  // R10 — الوسمان الإجرائيان الملازمان (51-MATRIX-06 §15 · DEC-219) بقالب ج-4
  L.push("", "> وسم إلزامي: [توحيد تشغيلي مؤقت — GAP-A-01 — قابل للترقية]",
         "> وسم إلزامي: [توحيد تشغيلي مؤقت — GAP-A-02 — قابل للمراجعة]");

  L.push("", J6);

  // R9 — البوابة على كامل المخرج قبل الإصدار (DEC-213)
  // ت-6 (DEC-224)
  const _deliveryLines = res.lines.map((x) => _k2line(x.code).presence);
  const _calledUnits = res.profile.ranked
    .map((d) => intensityBlock(d, K2.octalCode(res.profile.sp[d])).user)
    .concat(CENTER_SLOTS.flatMap((sl) => resolveSlot(c, sl))
      .map((k) => ((PACKS.USERLAYER_K2[c] || {})[k] || {}).user).filter(Boolean));
  const [t6Hits, t6Worst] = t6Guard(_deliveryLines, _calledUnits);

  const textOut = L.join("\n");
  const [scanned, locksExcluded] = stripLocks(textOut);   // DEC-217/ب
  const dimsCalled = [c].concat(others);
  const gate = K2.auditIsolation([scanned])
    .map((w) => ({ check: "isolation", token: w }))
    .concat(purGate(scanned, dimsCalled), purScanPacks(dimsCalled),
            scanLockFields(), scanLockDrift());   // ح-7 · DEC-241

  const packSha = {
    USERLAYER_K2: _shaObj(PACKS.USERLAYER_K2), PUR_K2: _shaObj(PACKS.PUR_K2.PUR),
    INTENSITY_K2: _shaObj(PACKS.INTENSITY_K2.S), LOOKALIKE_K2: _shaObj(PACKS.LOOKALIKE_K2.LD),
    CONTENT_K2: _shaObj(PACKS.CONTENT_K2),          // DEC-223
  };
  const spR = {};
  for (const d of Object.keys(sp).sort((a, b) => (a < b ? -1 : a > b ? 1 : 0))) {
    spR[d] = Math.round(sp[d] * 10) / 10;
  }

  const audit = {
    sp: spR, engine_version: K2.ENGINE_VERSION, spec_version: K2.SPEC_VERSION,
    instrument_pin: K2.INSTRUMENT_PIN,
    entries_used: Array.from(new Set(_USED
      .concat(res.lines.map((x) => x.code))                     // DEC-222
      .concat(dimsCalled.map((d) => `PUR-${d}`))))
      .sort((a, b) => (a < b ? -1 : a > b ? 1 : 0)),
    pack_sha: packSha,
    report_sha256: PK._sha256(textOut).slice(0, 16),
    r9_gate: gate.length ? gate : "clean",
    r9_locks_excluded: locksExcluded,
    lock_registry_size: Object.keys(PACKS.LOCKREG_K2.ACCEPTED_LOCK_MENTIONS).length,
    r10_tags: ["GAP-A-01", "GAP-A-02"],
    // DEC-245 — إعلان حالة الديون، نظيرَ ما في K3. **إعلانٌ لا قياس**:
    // مستخرَج من `02-MASTER` ولا يُحسب من الكود. المحتوى مطابق للنظير البايثوني.
    accepted_debts: ["DEBT-K2-BALANCE-01", "GAP-LOCK-01"],
    open_debts: [],
    t6_gate: t6Hits.length ? t6Hits : "clean", t6_max_overlap: t6Worst,
    mode: mode, sections_rendered: n, center: c, composition_lines: res.lines.length,
    delivery: res.delivery_questions,
    t8: res.t8.map((h) => [h.half, h.verdict]),
    fric02: Boolean(res.stitch),
    isolation: res.audit.length ? res.audit : "clean",
    external_pending: _sortCP(Array.from(new Set(extPending))),
  };
  return [SPG.outputGate(L.join("\n"), `تقرير K2 · ${mode}`), audit];
}

// ═════════════════════════════════════════════════════════════ K3 ═══════

// DEC-196 — تغطية صريحة لكل نطاق؛ لا وسم افتراضي صامت
const BAND_LABEL = {
  limited: "حضور محدود", core: "كفاءة أساسية",
  high: "قدرة عالية", OUT: "قراءة خاصة",
};

function bandLabel(b) {
  if (!(b in BAND_LABEL)) throw new Error(`DEC-196/حارس: نطاق غير معتمد «${b}» — يُصدر تقرير فجوة`);
  return BAND_LABEL[b];
}

// DEC-197/ج — الاسم المرادف يُشتقّ من نصّ الخاتمة المعتمد، لا يُؤلَّف
const _ALT_RE = /وهذه المهارة\s*—\s*\*\*(.+?)\*\*/;

function altName(skill) {
  const m = _ALT_RE.exec(PACKS.CIRCLE_K3.tail[skill]);
  if (!m) throw new Error(`DEC-197/حارس: اسم الخاتمة غير مستخرَج في ${skill}`);
  return m[1].trim();
}

function skillHeading(skill, b) {
  const short = K3.USER_NAME[skill], alt = altName(skill);
  // DEC-228/ب — التطابق التامّ وحده (لا احتواء جزئي)
  const name = (alt === short) ? short : `${short} (${alt})`;
  return `### ${name} — ${bandLabel(b)}`;
}

const H3 = { 1: "قبل أن تقرأ", 2: "موقعك من النظام", 4: "قدراتك الخمس",
             5: "تأكُّد من القوة", 6: "كيف تعمل قدراتك معاً", 7: "من أين يبدأ هذا؟",
             8: "هل هذا أنا؟", 9: "فكرة تصلح لما بعد التقرير" };

/** ر-2: يُسقط سطر عنوان المصدر (### أو #) ويُبقي المتن. */
function dropHeading(text) {
  const lines = text.split("\n");
  if (lines.length && lines[0].trimStart().startsWith("#")) lines.shift();
  return lines.join("\n").trim();
}

/** التقرير الفردي الكامل — تسعة أقسام (SPEC v2.1 §7 · DEC-139). */
// ═══════════════════════════════ عقد المحتوى الخارجي لـK3 (DEC-238) ═══
/**
 * نظير `REQUIRED_EXTERNAL` في `k3_content.py` — **بالمفاتيح وبالترتيب نفسه**،
 * لأن `missing()` تُرجِع بترتيب العقد لا بترتيب الفقد.
 *
 * كلٌّ يشير إلى **مصدره الفعلي في الحزم**، لا إلى قيمة ثابتة: الحقل الذي
 * لا يفحص يُبلّغ سلامةً كاذبة — وهو عين ما كان يفعله `auditIsolation([])`
 * قبل `DEC-236`.
 */
const K3_EXTERNAL_CONTRACT = {
  covenant_opening:  () => PACKS.THREE_K3.covenant_opening,
  circle_map_shared: () => PACKS.CIRCLE_K3.shared,
  circle_map_tail:   () => PACKS.CIRCLE_K3.tail,
  trust_banner:      () => PACKS.BANNER_K3.trust_banner,
  skill_sections:    () => PACKS.SECTIONS_K3,
  verify_block:      () => PACKS.TEXTLAYER_K3.VERIFY_BLOCK,
  separation_qs:     () => PACKS.TEXTLAYER_K3.SEPARATION_QS,
  out_text:          () => PACKS.THREE_K3.out_text,
  reflective_frame:  () => PACKS.THREE_K3.reflective_frame,
};

/** محوّل حزمة محتوى K3 (`DEC-240`) — نظير `ContentPack` في تمرير `missing()`
 *  إلى بوابة `strict` بالمحرّك، كما يفعل `k3_report.py:83`. */
const K3_CONTENT_ADAPTER = { missing: () => k3MissingContent() };

function k3MissingContent() {
  return Object.keys(K3_EXTERNAL_CONTRACT).filter((k) => {
    let v;
    try { v = K3_EXTERNAL_CONTRACT[k](); } catch (e) { return true; }
    if (v === undefined || v === null || v === "") return true;
    if (typeof v === "object" && !Object.keys(v).length) return true;
    return false;
  });
}

function buildReportK3(sp) {
  const TL = PACKS.TEXTLAYER_K3;
  const res = K3.run(sp, TL, PACKS.G5_K3, { content: K3_CONTENT_ADAPTER });   // DEC-240
  const L = [];
  let n = 0;
  const head = (key) => { n += 1; L.push(`## ${AR_NUM[n - 1]} · ${H3[key]}`, ""); };

  // ① فاتحة العهد
  head(1); L.push(PACKS.THREE_K3.covenant_opening, "");

  // ② خريطة الدائرة — DEC-195/ج: المشترك فقط
  head(2); L.push(PACKS.CIRCLE_K3.shared, "");

  // ③ لافتة الثقة — ر-4: بلا عنوان ولا رقم
  if (["limited", "OUT"].includes(K3.band(sp.EP))) {
    L.push("> ⚠️ " + PACKS.BANNER_K3.trust_banner, "");
  }

  // ④ الأقسام المهارية — ر-3: C-01 يُسقَط (العنوان يحمل معناه)
  head(4);
  for (const s of K3.SKILLS) {
    const b = K3.band(sp[s]), sec = PACKS.SECTIONS_K3[s];
    L.push(skillHeading(s, b), "", PACKS.CIRCLE_K3.tail[s], "", sec.U01, "");
    if (b === "OUT") {
      L.push(PACKS.THREE_K3.out_text.replace("{القدرة}", K3.USER_NAME[s]), "", sec.U10, "");
    } else if (b === "core" || b === "high") {
      L.push("**ما يظهر عندك:**", sec.U08, "");
    } else {
      L.push("**ما يحتاج انتباهاً:**", sec.U09, "");
    }
  }

  // ⑤ كتلة التحقق — قبل القراءة المركّبة (ق7)
  const high = ["IR", "BI", "CF", "ST"].filter((s) => K3.band(sp[s]) === "high");
  if (high.length) {
    L.push(TL.CONNECTIVES["C-02"], "");
    head(5);
    L.push(dropHeading(TL.VERIFY_BLOCK), "");
    for (const s of high) L.push("- " + TL.VERIFY_QUESTIONS[s]);
    L.push("", TL.VERIFY_CLOSING, "");
  }

  // ⑥ القراءة المركّبة
  if (res.section6) { head(6); L.push(res.section6, ""); }

  // ⑦ سؤال موضع الجذر
  if (res.section7) { head(7); L.push(res.section7, ""); }

  // ⑧ أسئلة الفصل
  L.push(TL.CONNECTIVES["C-05"], "");
  head(8); L.push(TL.SEPARATION_QS, "");

  // ⑨ الإطار التأملي
  L.push(TL.CONNECTIVES["C-06"], "");
  head(9); L.push(dropHeading(PACKS.THREE_K3.reflective_frame));

  // DEC-206 — audit كامل مطابق لنظيره البايثوني (a في k3_report)
  const audit = {
    pack_sha: {
      SECTIONS_K3: _shaObj(PACKS.SECTIONS_K3), THREE_K3: _shaObj(PACKS.THREE_K3),
      CIRCLE_K3: _shaObj({ shared: PACKS.CIRCLE_K3.shared, tail: PACKS.CIRCLE_K3.tail }),
    },
    report_sha256: PK._sha256(L.join("\n")).slice(0, 16),
    sp: res.sp, codes: res.codes, bands: res.bands,
    cells_activated: res.cells_activated, cost_map: res.cost_map,
    patterns_recognized: res.patterns_recognized,
    containment_state: res.containment_state, root_question: res.root_question,
    excluded_out: res.excluded_out, gates_fired: res.gates_fired,
    entries_used: res.entries_used,
    accepted_debts: res.accepted_debts, open_debts: res.open_debts,
    conditional_layers: res.conditional_layers, frozen_layers: res.frozen_layers,
    template_gaps: res.template_gaps, g5_violations: res.g5_violations,
    missing_content: k3MissingContent(),
    urs_version: res.urs_version,
    engine_version: res.engine_version, spec_version: res.spec_version,
    instrument_pin: res.instrument_pin,
    sections_rendered: n,
  };
  return [SPG.outputGate(L.join("\n"), "تقرير K3"), audit, res];
}

/** نطاق المرحلة ③ — يُبقى للتوافق مع مقارن الطبقة الجزئية. */
function buildReportK3Head(sp) {
  const full = buildReportK3(sp)[0].split("\n");
  const TL = PACKS.TEXTLAYER_K3;
  const bridges = new Set(Object.values(TL.CONNECTIVES).map((v) => String(v).trim()));
  let lastSkill = 0;
  full.forEach((l, i) => { if (l.startsWith("### ")) lastSkill = i; });
  let stop = full.length;
  for (let i = lastSkill + 1; i < full.length; i++) {
    if (full[i].startsWith("## ") || bridges.has(full[i].trim())) { stop = i; break; }
  }
  return [SPG.outputGate(full.slice(0, stop).join("\n"), "ترويسة K3"), {}];
}

if (typeof module !== "undefined") {
  module.exports = {
    buildReportK2, validateSlots, resolveSlot, SlotResolutionError,
    purGate, purScanPacks, t6Guard, scanLockFields, scanLockDrift, intensityBlock, stripLocks, r11Block, buildReportK3, buildReportK3Head, dropHeading, bandLabel, altName, skillHeading, BAND_LABEL,
    verifyPacks, K2_CONTENT_ADAPTER, K3_EXTERNAL_CONTRACT, k3MissingContent, K3_CONTENT_ADAPTER,
  };
}
