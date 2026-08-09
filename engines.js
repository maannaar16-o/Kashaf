"use strict";
/**
 * engines.js — نقل منطق محرّكَي K2 و K3 إلى JS (المرحلة ①)
 * =========================================================
 * نطاق النقل: **المنطق فقط**. صفر نصّ محتوى — طبقتا التركيب النصّي
 * (k2_content / k3_content / COMPOSE-*) تبقيان للمرحلة ③.
 *
 * الاستثناء الوحيد: عبارات `t8_conditioning` و`fric02_stitch` في K2
 * مولَّدة داخل المحرك لا من حزمة محتوى — تُنقَل **حرفياً** لأن التكافؤ
 * (DEC-199) يقتضي تطابق المخرج، ولأن تعديلها تأليف محظور.
 *
 * الثوابت الحاكمة (لا تُمسّ):
 *   SS = x − 2z + y  ·  K2: SP = SS/42*100 و y+z=7  ·  K3: SP = SS/66*100 و y+z=11
 *   حدود K2 عليا (≤) · حدود K3 دنيا (<) — DEC-184 · حدّ 50.0 من core (DEC-133)
 */

// ═══════════════════════════════════════════════════════════════════ K2 ═══

class InputContractError extends Error {
  constructor(msg) { super(msg); this.name = "InputContractError"; }
}

const K2 = (() => {
  const ENGINE_VERSION = "0.1";
  const SPEC_VERSION = "56-REPORT-ENGINE v1.2";
  const INSTRUMENT_PIN = "40 v5.0 + 41 v4.2";
  const MAX_RAW = 42;                                  // 7 بنود × 6

  const LENSES = ["A", "R", "C", "O", "S", "E", "St", "H"];
  const LENS_NAME = {
    A: "التحليلي", R: "الواقعي", C: "المحافظ", O: "المنظم",
    S: "الاجتماعي", E: "المتفهم", St: "الاستراتيجي", H: "التصوري",
  };

  const ITEM_MAP = {
    A:  [[1,"a"],[22,"a"],[40,"a"],[55,"a"],[67,"a"],[76,"a"],[82,"a"]],
    R:  [[1,"b"],[4,"a"], [25,"a"],[43,"a"],[58,"a"],[70,"a"],[79,"a"]],
    C:  [[4,"b"],[7,"a"], [22,"b"],[28,"a"],[46,"a"],[61,"a"],[73,"a"]],
    O:  [[7,"b"],[10,"a"],[25,"b"],[31,"a"],[40,"b"],[49,"a"],[64,"a"]],
    S:  [[10,"b"],[13,"a"],[28,"b"],[34,"a"],[43,"b"],[52,"a"],[55,"b"]],
    E:  [[13,"b"],[16,"a"],[31,"b"],[37,"a"],[46,"b"],[58,"b"],[67,"b"]],
    St: [[16,"b"],[19,"a"],[34,"b"],[49,"b"],[61,"b"],[70,"b"],[76,"b"]],
    H:  [[19,"b"],[37,"b"],[52,"b"],[64,"b"],[73,"b"],[79,"b"],[82,"b"]],
  };

  /** تصيير موحَّد للعدد في رسائل العقد (`DEC-235`) — نظير `_num` البايثوني.
   *  صريحٌ عمداً: الاتّكال على السلوك الضمني هو ما أنتج `GAP-MSG-PARITY-01`. */
  function _num(v) {
    const f = Number(v);
    if (!isFinite(f)) return String(v);
    return Number.isInteger(f) ? String(f) : String(f);
  }

  function computeSsSp(x, y, z) {
    if (y + z !== 7) throw new InputContractError(
      `y+z يجب أن يساوي 7 (y=${_num(y)}, z=${_num(z)})`);
    const ss = x - 2 * z + y;
    return [ss, ss / MAX_RAW * 100.0];
  }

  /** حدود الفرز — 41 §5 (حدود ≤ عليا). لا تُخلط بحدود K3 (DEC-184). */
  function octalCode(sp) {
    if (sp < 0) return "OUT";
    if (sp <= 20) return "L-";
    if (sp <= 40) return "L";
    if (sp <= 50) return "M";
    if (sp <= 70) return "M+";
    if (sp <= 85) return "H";
    if (sp <= 100) return "H+";
    return "H++";
  }

  /** DEC-157 — D مهيمنة (>70) · M مساندة (>50) · L منطفئة (≤50). */
  function compState(sp) {
    if (sp > 70) return "D";
    if (sp > 50) return "M";
    return "L";
  }

  function scoreFromRaw(raw) {
    const out = {};
    for (const d of LENSES) {
      let x = 0, y = 0;
      for (const [it, opt] of ITEM_MAP[d]) {
        const a = (it in raw) ? raw[it] : raw[String(it)];
        x += (opt === "a") ? a.ratingA : a.ratingB;
        if (a.choice === opt) y += 1;
      }
      const z = 7 - y;
      const [ss, sp] = computeSsSp(x, y, z);
      out[d] = { x, y, z, ss, sp: Math.round(sp * 10) / 10, code: octalCode(sp) };
    }
    return out;
  }

  function classify(sp) {
    // فرز تنازلي بـSP · كسر التعادل بترتيب LENSES (مطابق لاستقرار sorted في بايثون)
    const ranked = LENSES.slice().sort((a, b) => (sp[b] - sp[a]) || (LENSES.indexOf(a) - LENSES.indexOf(b)));
    const p = { sp, center: ranked[0], ranked, ignited: [], dominant: [], support: [], off: [] };
    for (const d of ranked) {
      const s = compState(sp[d]);
      (s === "D" ? p.dominant : s === "M" ? p.support : p.off).push(d);
      if (sp[d] > 50) p.ignited.push(d);
    }
    return p;
  }

  const COVERAGE = {
    E: ["O"], H: ["A", "R", "O"], C: ["H", "St"], S: ["A", "St"],
    St: ["R", "O"], R: ["A", "St"],
    A: ["E", "O", "R"],      // DEC-173
    O: ["H", "St", "R"],     // DEC-174
  };

  const BLINDNESS = {
    E:  [["ذوبان الحدود", ["O"]]],
    H:  [["تشتت الخيارات وغياب التأريض", ["A", "R", "O"]]],
    C:  [["كلفة عدم التغيير", ["H", "St"]]],
    S:  [["تمييع الحقيقة", ["A", "St"]]],
    St: [["الانفصال عن اللحظة", ["R", "O"]]],
    R:  [["السطحية/غياب الجذر", ["A"]], ["تجهيل المستقبل", ["St"]]],
    A:  [["شلل المعالجة", ["O", "R"]], ["إغفال الإشارة الوجدانية", ["E"]]],
    O:  [["تقادم القالب", ["St", "H"]], ["الجمود عند الكسر", ["R", "H"]]],
  };

  /** DEC-157 — سطر واحد لكل عدسة مرافقة. ت-7: التسليم للمنطفئة وحدها. */
  function compose(profile) {
    const c = profile.center;
    const allies = COVERAGE[c];
    const lines = [];
    for (const lens of LENSES) {
      if (lens === c) continue;
      const st = compState(profile.sp[lens]);
      lines.push({
        code: `${c}-${lens}-${st}`,
        lens,
        kind: allies.includes(lens) ? "coverage" : "coloring",
        state: st,
        layer: (st === "L") ? "delivery" : "review",
      });
    }
    return lines;
  }

  /** ت-8 (DEC-178) — تكييف نصّ العمى بحالة تغطيته، لكل نصف على حدة. */
  function t8Conditioning(profile) {
    const c = profile.center;
    const out = [];
    for (const [halfName, allies] of BLINDNESS[c]) {
      const states = allies.map((a) => compState(profile.sp[a]));
      let verdict, phrase;
      if (states.every((s) => s === "D")) {
        verdict = "covered";
        phrase = `حدّ بنيوي يغطّيه ملفك داخلياً عبر ${allies.join("·")}`;
      } else if (states.every((s) => s === "L")) {
        verdict = "exposed";
        phrase = `مكشوف — التغطية خارجية بيني عبر ${allies.join("·")}`;
      } else {
        const present = allies.filter((a) => compState(profile.sp[a]) !== "L");
        const absent = allies.filter((a) => compState(profile.sp[a]) === "L");
        phrase = `مُغطّى غالباً عبر ${present.join("·")}`;
        if (absent.length) phrase += `، ومكشوف من جهة ${absent.join("·")}`;
        verdict = "partial";
      }
      const stateMap = {};
      allies.forEach((a, i) => { stateMap[a] = states[i]; });
      out.push({ half: halfName, allies, states: stateMap, verdict, phrase });
    }
    return out;
  }

  /** FRIC-COMPOSE-02 — سرد بلا ترجيح (DEC-163). */
  function fric02Stitch(profile, t8) {
    const exposed = t8.filter((h) => h.verdict === "exposed");
    const set = new Set();
    for (const h of exposed) for (const a of h.allies) set.add(a);
    // مطابقة sorted() في بايثون: فرز بنقطة الترميز حصراً (DEC-199 §4)
    const offAllies = Array.from(set).sort((a, b) => (a < b ? -1 : a > b ? 1 : 0));
    if (offAllies.length >= 2) {
      return `تغطية العمى خارجية بالكامل عبر ${offAllies.join("·")} (سرد لا ترجيح).`;
    }
    return null;
  }

  const FORBIDDEN = [
    "K3", "K4", "استثارة", "شفقة", "تنفيذ ميداني", "إدارة وقت",
    "علاج", "تشخيص", "اضطراب", "مرض",
    // DEC-214 — عبارات مركّبة: تلتقط الخلط لا الذكر المشروع
    "انفعالك", "انفعاله", "انفعالها", "درجة انفعال", "شدة الانفعال",
    "مستوى انفعال", "أنت منفعل", "تنفعل بسرعة", "الانفعال لديك"];

  function auditIsolation(texts) {
    const hits = [];
    for (const t of texts) {
      if (!t) continue;
      for (const w of FORBIDDEN) if (t.includes(w)) hits.push(w);
    }
    return hits;
  }

  function run({ sp = null, raw = null, content = null, strict = false } = {}) {
    if (sp === null) {
      if (raw === null) throw new InputContractError("مطلوب sp أو raw");
      const scored = scoreFromRaw(raw);
      sp = {};
      for (const d of LENSES) sp[d] = scored[d].sp;
    }
    const keys = Object.keys(sp).sort();
    const expect = LENSES.slice().sort();
    if (keys.length !== expect.length || keys.some((k, i) => k !== expect[i])) {
      throw new InputContractError(
        "الأبعاد يجب أن تكون الثمانية بالضبط: " + LENSES.join(" · "));
    }
    const profile = classify(sp);
    const lines = compose(profile);
    const t8 = t8Conditioning(profile);
    const delivery = lines.filter((l) => l.layer === "delivery").map((l) => l.code);
    const stitch = fric02Stitch(profile, t8);
    // DEC-236 — تدقيق العزل يُغذّى بنصوص المصدر فعلاً، نظير
    // `audit_isolation(*content.texts_for(prof))` في بايثون.
    // بقاؤه مثبَّتاً على `[]` كان `GAP-ISO-JS-01`.
    const audit = auditIsolation(content ? content.textsFor(profile) : []);
    if (strict && audit.length) throw new InputContractError("خرق عزل: " + audit.join(" · "));
    return { profile, lines, t8, delivery_questions: delivery, stitch, audit };
  }

  return { ENGINE_VERSION, SPEC_VERSION, INSTRUMENT_PIN, MAX_RAW, LENSES, LENS_NAME,
           ITEM_MAP, computeSsSp, octalCode, compState, scoreFromRaw, classify,
           COVERAGE, BLINDNESS, compose, t8Conditioning, fric02Stitch,
           auditIsolation, FORBIDDEN, run };
})();

// ═══════════════════════════════════════════════════════════════════ K3 ═══

const K3 = (() => {
  const ENGINE_VERSION = "0.4";
  const SPEC_VERSION = "57-K3-ENGINE-SPEC v2.1";
  const INSTRUMENT_PIN = "40 v5.0 + 41 v4.2";
  const MAX_RAW = 66;

  const SKILLS = ["EP", "IR", "BI", "CF", "ST"];       // ترتيب العرض = مسار المعالجة
  // DEC-215 — الأسماء المعتمدة للعرض بأمر مالك المشروع
  const USER_NAME = { EP: "مهارة قوة الملاحظة", IR: "مهارة التحكم الانفعالي",
                      BI: "مهارة كبح جماح النفس", CF: "مهارة المرونة",
                      ST: "مهارة تحمل الضغوط" };

  /** تصيير موحَّد للعدد في رسائل العقد (`DEC-235`) — نظير `_num` البايثوني.
   *  صريحٌ عمداً: الاتّكال على السلوك الضمني هو ما أنتج `GAP-MSG-PARITY-01`. */
  function _num(v) {
    const f = Number(v);
    if (!isFinite(f)) return String(v);
    return Number.isInteger(f) ? String(f) : String(f);
  }

  function computeSsSp(x, y, z) {
    if (y + z !== 11) throw new InputContractError(
      `y+z يجب أن يساوي 11 (y=${_num(y)}, z=${_num(z)})`);
    const ss = x - 2 * z + y;
    return [ss, ss / MAX_RAW * 100.0];
  }

  /** حدود K3 دنيا (<) — مغايرة لحدود K2 عمداً (DEC-184). */
  function octalCode(sp) {
    if (sp < 0) return "OUT";
    if (sp < 20) return "L-";
    if (sp < 40) return "L";
    if (sp < 50) return "M";
    if (sp <= 70) return "M+";
    if (sp <= 85) return "H";
    if (sp <= 100) return "H+";
    return "H++";
  }

  /** التثليث الحاكم — DEC-064 + DEC-133 (الحدّ 50.0 من core). */
  function band(sp) {
    if (sp < 0) return "OUT";
    if (sp < 50) return "limited";
    if (sp <= 70) return "core";
    return "high";
  }

  /** قطب الاستدعاء — ح-1. المحايد و OUT لا يُستدعيان. */
  function pole(sp) {
    const b = band(sp);
    if (b === "limited") return "W";
    if (b === "high") return "S";
    return null;
  }

  const EDGES = [
    ["IR", "BI", "hub"], ["IR", "CF", "hub"],
    ["BI", "CF", "lateral"],
    ["IR", "ST", "load"], ["BI", "ST", "load"], ["CF", "ST", "load"],
    ["EP", "IR", "feed"],
  ];
  const FAMILY_ORDER = { hub: 0, lateral: 1, load: 2, feed: 3 };
  const EDGE_INDEX = {};
  EDGES.forEach(([a, b], i) => { EDGE_INDEX[`${a}|${b}`] = i; });

  // 28 خلية — [relation, locus, amplifies, template]
  const CELLS = {
    "IR|BI|SS": ["تعزيز", "none", false, "T-01"],
    "IR|BI|SW": ["تفاقم موضعي", "external", false, "T-07"],
    "IR|BI|WS": ["تثبيت", "internal", false, "T-02"],
    "IR|BI|WW": ["تفاقم", "external", false, "T-07"],
    "IR|CF|SS": ["تعزيز", "none", false, "T-01"],
    "IR|CF|SW": ["تثبيت بكلفة", "repeat_effort", false, "T-03"],
    "IR|CF|WS": ["تهذيب", "post_hoc", false, "T-06"],
    "IR|CF|WW": ["تفاقم", "to_ST", false, "T-08"],
    "BI|CF|SS": ["تعزيز", "none", false, "T-01"],
    "BI|CF|SW": ["تفاقم", "to_ST", false, "T-08"],
    "BI|CF|WS": ["تهذيب", "post_hoc", false, "T-06"],
    "BI|CF|WW": ["تفاقم", "external", false, "T-07"],
    "IR|ST|SS": ["تعزيز", "none", false, "T-01"],
    "IR|ST|SW": ["تثبيت جزئي", "none", false, "T-05"],
    "IR|ST|WS": ["تثبيت بكلفة", "to_ST", true, "T-04"],
    "IR|ST|WW": ["تفاقم", "to_ST", false, "T-08"],
    "BI|ST|SS": ["تعزيز مشروط", "none", false, "T-01"],
    "BI|ST|SW": ["تفاقم مشروط", "to_ST", false, "T-08"],
    "BI|ST|WS": ["محايد على الحافة", "transferred_out", false, "T-09"],
    "BI|ST|WW": ["محايد على الحافة", "none", false, "T-09"],
    "CF|ST|SS": ["تعزيز", "none", false, "T-01"],
    "CF|ST|SW": ["تثبيت جزئي", "none", false, "T-05"],
    "CF|ST|WS": ["تثبيت بكلفة مضاعفة", "to_ST", true, "T-04"],
    "CF|ST|WW": ["تفاقم", "to_ST", false, "T-08"],
    "EP|IR|SS": ["تعزيز", "none", false, "T-01"],
    "EP|IR|SW": ["محايد على الحافة", "none", false, "T-09"],
    "EP|IR|WS": ["تثبيت بكلفة", "misdirected", true, "T-11"],   // DEC-137
    "EP|IR|WW": ["تفاقم", "to_ST", false, "T-08"],
  };

  /** ح-1: الأقطاب فقط · المحايد لا يُستدعى · OUT مستبعَد (DEC-133). */
  function activateCells(sp) {
    const out = [];
    for (const [a, b, fam] of EDGES) {
      const pa = pole(sp[a]), pb = pole(sp[b]);
      if (pa === null || pb === null) continue;
      const state = pa + pb;
      const [rel, locus, amp, tpl] = CELLS[`${a}|${b}|${state}`];
      out.push({ a, b, state, family: fam, relation: rel, locus,
                 amplifies: amp, template: tpl, code: `CPL-${a}.${b}-${state}` });
    }
    // DEC-137/6 — الترتيب داخل العائلة بترتيب الحافات في M3-00 §3.1، لا أبجدياً
    out.sort((c1, c2) =>
      (FAMILY_ORDER[c1.family] - FAMILY_ORDER[c2.family]) ||
      (EDGE_INDEX[`${c1.a}|${c1.b}`] - EDGE_INDEX[`${c2.a}|${c2.b}`]));
    return out;
  }

  const _has = (cells, a, b, states) =>
    cells.some((c) => c.a === a && c.b === b && states.includes(c.state));

  /** «القناة النشطة» — M3-04 v1.2 §2.1 (لاتماثل مقصود: BI ينشط بالقوة). */
  function activeLoadChannels(cells) {
    const ch = [];
    if (_has(cells, "IR", "ST", ["WS", "WW"])) ch.push("IR");
    if (_has(cells, "CF", "ST", ["WS", "WW"])) ch.push("CF");
    if (_has(cells, "BI", "ST", ["SS", "SW"])) ch.push("BI");
    return ch;
  }

  function recognizePatterns(cells, sp) {
    const pats = [];
    if (band(sp.IR) === "limited" &&
        _has(cells, "IR", "BI", ["WS", "WW"]) && _has(cells, "IR", "CF", ["WS", "WW"])) {
      pats.push({ code: "HF-01", family: "hub", status: "full",
        cells: cells.filter((c) => (c.a === "IR" && (c.b === "BI" || c.b === "CF")))
                    .map((c) => c.code) });
    }
    if (_has(cells, "IR", "CF", ["SW"]) && _has(cells, "CF", "ST", ["WS", "WW"])) {
      pats.push({ code: "HF-02:CF", family: "hub", status: "full",
        cells: ["CPL-IR.CF-SW"].concat(
          cells.filter((c) => c.a === "CF" && c.b === "ST").map((c) => c.code)) });
    }
    if (_has(cells, "BI", "CF", ["SW"]) && _has(cells, "BI", "ST", ["SS", "SW"])) {
      pats.push({ code: "HF-02:BI", family: "lateral", status: "full",
        cells: ["CPL-BI.CF-SW"].concat(
          cells.filter((c) => c.a === "BI" && c.b === "ST").map((c) => c.code)) });
    }
    if (activeLoadChannels(cells).length >= 2 && band(sp.ST) === "limited") {
      pats.push({ code: "HF-04", family: "load", status: "full",
        cells: cells.filter((c) => c.b === "ST").map((c) => c.code) });
    }
    // فرز مستقر بالعائلة — مطابق لـlist.sort في بايثون
    return pats.map((p, i) => [p, i])
               .sort((u, v) => (FAMILY_ORDER[u[0].family] - FAMILY_ORDER[v[0].family]) || (u[1] - v[1]))
               .map((u) => u[0]);
  }

  // ── البوابات ──
  const g1Trust = (sp) => ["limited", "OUT"].includes(band(sp.EP));
  const g2FalsePole = (sp) => ["IR", "BI", "CF", "ST"].filter((s) => band(sp[s]) === "high");

  function g4Containment(sp, cells) {
    const bands = SKILLS.map((s) => band(sp[s]));
    if (bands.every((b) => b === "high")) return "strong";
    if (bands.every((b) => b === "limited")) return "weak";
    if (!cells.length) return null;                    // DEC-133: لا نصّ حالة
    return "composite";
  }

  /** ت-1/ت-2 — سؤال واحد كحدّ أقصى. */
  function g3Question(patterns, cells) {
    if (patterns.length) {
      const map = { "HF-01": "RQ-01", "HF-02:CF": "RQ-02",
                    "HF-02:BI": "RQ-03", "HF-04": "RQ-04" };
      return [map[patterns[0].code], patterns.slice(1)];
    }
    // DEC-137/4 — لا post_hoc ولا transferred_out
    const COST_LOCI = ["internal", "repeat_effort", "to_ST", "misdirected"];
    if (cells.some((c) => COST_LOCI.includes(c.locus) || c.amplifies)) return ["RQ-05", []];
    return [null, []];
  }

  /** المرحلة ④ — التركيب النصّي. النصّ كله من TEXTLAYER_K3؛ لا سطر مؤلَّف هنا. */
  /** صياغة صريحة موحَّدة (`ن-8`) — نظير `strict_gate_message` البايثونية. */
  function strictGateMessage(gaps, violations, missingContent) {
    const part = (label, items) =>
      label + ": " + (items.length ? items.join(" · ") : "لا شيء");
    return "بوابة strict — الإصدار موقوف · " +
      part("فجوات", gaps) + " · " +
      part("مخالفات", violations) + " · " +
      part("محتوى مفقود", missingContent);
  }

  function StrictGateError(gaps, violations, missingContent) {
    const e = new Error(strictGateMessage(gaps, violations, missingContent));
    e.name = "StrictGateError";
    e.gaps = gaps; e.violations = violations; e.missing_content = missingContent;
    return e;
  }

  function compose(cells, patterns, sp, lowTrust, outSkills, TL) {
    const lines = [], used = [];
    const fmt = (t, kw) => t.replace(/\{(\w+)\}/g, (m, k) => (k in kw ? kw[k] : m));
    const add = (key, kw) => {
      lines.push(kw ? fmt(TL.CONNECTIVES[key], kw) : TL.CONNECTIVES[key]);
      used.push(key);
    };
    const tpl = (code, a, b) => {
      lines.push(fmt(TL.TEMPLATES[code], { a: USER_NAME[a] || "", b: USER_NAME[b] || "" }));
      used.push(code);
    };

    add("C-03");
    lines.push(TL.LOAD_TAG);
    for (const s of outSkills) add("C-16", { skill: USER_NAME[s] });   // س-11
    if (lowTrust) add("C-12");

    const state = g4Containment(sp, cells);
    if (state) { lines.push(TL.CONTAINMENT_TEXT[state]); used.push("state:" + state); }

    const emitted = new Set();
    const gaps = [];                                 // DEC-240
    const patternCells = new Set();
    for (const p of patterns) for (const c of p.cells) patternCells.add(c);

    function emitGroup(group, lead) {
      if (!group.length) return;
      if (lead) add(lead);
      for (const c of group) {                       // س-9 الكلفة ثم التضخيم · س-3 مرة واحدة
        if (c.template === null) {                   // DEC-240 — تُسجَّل فجوةً لا تُتخطّى
          gaps.push(`خلية ${c.code} بلا قالب كلفة معتمد`); continue;
        }
        if (!emitted.has(c.template)) { tpl(c.template, c.a, c.b); emitted.add(c.template); }
      }
      if (group.some((c) => c.amplifies) && !emitted.has("T-10")) {
        tpl("T-10"); emitted.add("T-10");
      }
    }

    const byCode = {};
    for (const c of cells) byCode[c.code] = c;
    if (patterns.length) {
      emitGroup(patterns[0].cells.filter((x) => x in byCode).map((x) => byCode[x]), "C-10");
      for (const p of patterns.slice(1)) {
        emitGroup(p.cells.filter((x) => x in byCode).map((x) => byCode[x]), "C-15");
      }
    }
    const rest = cells.filter((c) => !patternCells.has(c.code));
    if (rest.length) {
      emitGroup(rest, rest.every((c) => c.family === "load") ? "C-08" : "C-07");
    }
    return [lines.join("\n"), used, gaps];
  }

  /** G5 — بوابة التطهير اللغوي (§5 · DEC-137/3). مرحلتان: المحتوى ثم المخرج. */
  function g5Isolation(text, checks, stage) {
    const hits = [];
    for (const [name, needles] of Object.entries(checks)) {
      for (const n of needles) if (String(text).includes(n)) {
        hits.push({ check: name, stage: stage || "output", token: n });
      }
    }
    return hits;
  }

  function g5ScanContent(packObj, checks) {
    const hits = [];
    for (const [key, txt] of Object.entries(packObj || {})) {
      for (const h of g5Isolation(txt, checks, "content")) { h.key = key; hits.push(h); }
    }
    return hits;
  }

  /** طبقة المنطق — وبالتركيب النصّي إن مُرِّرت الحزمة (TL). */
  function run(sp, TL, G5, { content = null, strict = false } = {}) {
    const outSkills = SKILLS.filter((s) => band(sp[s]) === "OUT");
    const lowTrust = g1Trust(sp);
    const high = g2FalsePole(sp);
    const cells = activateCells(sp);
    const patterns = recognizePatterns(cells, sp);
    const [qcode] = g3Question(patterns, cells);
    const state = g4Containment(sp, cells);
    let s6 = "", used = [], s7 = "", gaps = [];
    if (TL) {
      if (cells.length) [s6, used, gaps] = compose(cells, patterns, sp, lowTrust, outSkills, TL);
      if (qcode && cells.length) {
        const q = TL.ROOT_QUESTIONS[qcode];
        s7 = [TL.CONNECTIVES["C-04"], TL.CONNECTIVES["C-13"],
              `[أ] ${q.alt[0]}`, `[ب] ${q.alt[1]}`,
              TL.CONNECTIVES["C-14"], q.q].join("\n");
        used = used.concat(["C-04", "C-13", "C-14", qcode]);
      }
    }
    const violations = (G5 && (s6 || s7)) ? g5Isolation(s6 + "\n" + s7, G5.G5_CHECKS) : [];
    // DEC-240 — نظير بوابة `strict` البايثونية: الشرط والرسالة والنوع سواء.
    const missing = content ? content.missing() : [];
    if (strict && (gaps.length || violations.length || missing.length))
      throw StrictGateError(gaps, violations, missing);
    const spR = {}, codes = {}, bands = {};
    for (const k of SKILLS) {
      spR[k] = Math.round(sp[k] * 10) / 10;
      codes[k] = octalCode(sp[k]);
      bands[k] = band(sp[k]);
    }
    return {
      section6: s6, section7: s7, entries_used: used,
      sp: spR, codes, bands,
      cells_activated: cells.map((c) => c.code),
      cost_map: cells.map((c) => ({ cell: c.code, locus: c.locus, amplification: c.amplifies })),
      patterns_recognized: patterns.map((p) => ({ code: p.code, status: p.status })),
      containment_state: state,
      root_question: { code: qcode, response: "none", attribution_source: "none" },
      excluded_out: outSkills,
      // DEF-K3-02 (DEC-201) — نظير _gates_fired البايثوني حرفاً بحرف
      gates_fired: [
        "G1:low_trust=" + (lowTrust ? "true" : "false"),
        "G2:high=[" + high.join(",") + "]",
        // DEC-203 — نظير _gates_fired البايثوني: الحالة ثم الكود
        qcode ? "G3:asked:" + qcode : "G3:none",
        "G4:" + (state || "suppressed"),
        "G5:violations=" + violations.length,
      ],
      // حقول الحوكمة — منقولة من نظيرها البايثوني (SPEC §audit)
      accepted_debts: ["DEBT-K3-EPPURITY-01", "GAP-Q-09"],
      open_debts: ["DEBT-K3-FIELD-01"],
      conditional_layers: ["G3:via-67"],
      frozen_layers: [],            // DEC-202/② — سجل التجميد
      template_gaps: gaps, g5_violations: violations,   // DEC-240 — تُحسب لا تُثبَّت
      urs_version: "3.0",
      engine_version: ENGINE_VERSION, spec_version: SPEC_VERSION,
      instrument_pin: INSTRUMENT_PIN,
    };
  }

  return { ENGINE_VERSION, SPEC_VERSION, INSTRUMENT_PIN, MAX_RAW, SKILLS, USER_NAME,
           computeSsSp, octalCode, band, pole, EDGES, CELLS, FAMILY_ORDER,
           activateCells, activeLoadChannels, recognizePatterns,
           StrictGateError, strictGateMessage,
           g1Trust, g2FalsePole, g3Question, g4Containment, compose,
           g5Isolation, g5ScanContent, run };
})();

if (typeof module !== "undefined") module.exports = { K2, K3, InputContractError };
