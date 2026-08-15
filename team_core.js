"use strict";
/**
 * team_core.js — توأم طبقة الفريق (`DEC-289`)
 * ==============================================
 * سند: `DEC-278` (الطبقة بايثونَ وحدها بحرسٍ على التأجيل) · `DEC-278 §5`
 *      (**قاعدة القلب**: حين يُبنى السطح **يُقلب الحرس لا يُحذف** — من
 *      «لا سطح بلا توأم» إلى «التوأم مقيسٌ بتكافؤ») · `DEC-199`/`DEC-200`
 *
 * **توأمٌ حرفيّ لـ`team_engine.py` + `team_report.py`** — ولا سطرَ منطقٍ
 * يُصاغ هنا صياغةً أخرى: العتبات من `K2.compState` (مصدرُ حقيقةٍ واحد)،
 * والنصوص من حزمة الفريق، والترتيب بالقاعدة نفسها (`SP` تنازلياً وكسرُ
 * التعادل بترتيب `41 §5.2`).
 */
(function (root, factory) {
  if (typeof module !== "undefined" && module.exports) {
    module.exports = factory(require("./engines.js"), require("./packs.js"));
  } else {
    root.RawahilTeam = factory(root.RawahilEngines, root.RawahilPacks);
  }
})(typeof self !== "undefined" ? self : this, function (EN, PK) {

  const K2 = EN.K2;
  const LENSES = K2.LENSES.slice();
  const ENGINE_VERSION = "1.0";
  const SPEC_VERSION = "56-TEAM-00 v1.0";
  const INSTRUMENT_PIN = K2.INSTRUMENT_PIN || "40 v5.0 + 41 v4.2";
  const MIN_MEMBERS = 2;
  const FULL_MATRIX_MAX = 4;
  const AR_NUM = "١٢٣٤٥٦٧٨٩";

  class InputContractError extends Error {}

  function requirePack(raw) {
    if (!raw) throw new InputContractError("حزمة الفريق غائبة");
    const need = ["dyad", "polar", "blind", "rebound", "combo", "heading", "lock"];
    const missing = need.filter((k) => !(k in raw));
    if (missing.length) {
      throw new InputContractError(
        `حزمة الفريق ناقصة ['${missing.join("', '")}'] — لا تقرير بلا حزمة (صفر تأليف)`);
    }
    return raw;
  }

  // ── عقد المدخل — يوقف ولا يخمّن ──────────────────────────────────────
  function validate(members) {
    if (!Array.isArray(members)) throw new InputContractError("قائمة الأعضاء ليست تسلسلاً");
    if (members.length < MIN_MEMBERS) {
      throw new InputContractError(
        `عضوان حدّاً أدنى — وُجد ${members.length} (\`56-TEAM-00 §1\`)`);
    }
    const codes = [];
    for (const m of members) {
      if (!m || typeof m !== "object" || !("code" in m) || !("sp" in m)) {
        throw new InputContractError("عضوٌ بلا `code` أو `sp`");
      }
      const code = String(m.code).trim();
      if (!code) throw new InputContractError("رمز عضوٍ فارغ");
      if (codes.indexOf(code) !== -1) throw new InputContractError(`رمز عضوٍ مكرَّر: ${code}`);
      codes.push(code);
      const sp = m.sp;
      if (!sp || typeof sp !== "object" || Array.isArray(sp)) {
        throw new InputContractError(`${code}: \`sp\` ليس قاموساً`);
      }
      for (const d of LENSES) {
        if (!(d in sp)) throw new InputContractError(`${code}: عدسة ناقصة ${d}`);
        const f = pyFloat(sp[d]);
        // **حدُّ التوأمة هنا دقيق**: `float("NaN")` في بايثون **تنجح**،
        // فالقيمة ليست «غير عددية» بل تسقط في فحص الانتهاء. و`Number()`
        // وحدها تخلط الحالتين — فرصدها التكافؤ أول تشغيل (`DEC-289 §4`).
        if (f === undefined) throw new InputContractError(`${code}/${d}: قيمة غير عددية`);
        // غير المنتهي يُرفض صراحةً — وإلا صُنِّف «مهيمناً» صامتاً
        if (!Number.isFinite(f)) throw new InputContractError(`${code}/${d}: قيمة غير منتهية`);
      }
      const extra = Object.keys(sp).filter((k) => LENSES.indexOf(k) === -1);
      if (extra.length) {
        throw new InputContractError(
          `${code}: حقول من خارج عدسات $K_2$ — ['${extra.join("', '")}'] ` +
          "(`§4`: صفر لمس K1/K3/K4)");
      }
    }
  }


  /**
   * تحويلٌ بدلالة `float()` في بايثون — لا بدلالة `Number()`.
   *
   * `float` **تقبل** `"NaN"`/`"inf"`/`"Infinity"` (بإشارة، بأي حالة أحرف)
   * وتُرجع قيمةً غير منتهية؛ و`Number("inf")` تُرجع `NaN` فتخلط «غير
   * عددية» بـ«غير منتهية». وتُرجع `undefined` حيث ترفع `float` استثناءً.
   */
  function pyFloat(v) {
    if (typeof v === "number") return v;
    if (typeof v === "boolean") return v ? 1 : 0;
    if (typeof v !== "string") return undefined;      // null · مصفوفة · كائن
    const t = v.trim();
    if (!t) return undefined;
    const m = /^([+-]?)(inf|infinity|nan)$/i.exec(t);
    if (m) {
      if (m[2].toLowerCase() === "nan") return NaN;
      return m[1] === "-" ? -Infinity : Infinity;
    }
    const f = Number(t);
    return Number.isNaN(f) ? undefined : f;
  }

  function profile(sp) {
    const st = {}, band = {};
    for (const d of LENSES) {
      st[d] = K2.compState(Number(sp[d]));
      band[d] = K2.octalCode(Number(sp[d]));
    }
    return {
      state: st, band: band,
      dominant: LENSES.filter((d) => st[d] === "D"),
      support: LENSES.filter((d) => st[d] === "M"),
      blind: LENSES.filter((d) => st[d] === "L"),
    };
  }

  /** ترتيب بالـSP تنازلياً · وكسر التعادل بترتيب `41 §5.2` (`DEF-K2-04`). */
  function rank(sp, codes) {
    return codes.slice().sort((a, b) =>
      (Number(sp[b]) - Number(sp[a])) || (LENSES.indexOf(a) - LENSES.indexOf(b)));
  }

  function coverage(mem) {
    const out = {};
    for (const d of LENSES) {
      const dom = mem.filter((m) => m.profile.dominant.indexOf(d) !== -1).map((m) => m.code);
      const sup = mem.filter((m) => m.profile.support.indexOf(d) !== -1).map((m) => m.code);
      out[d] = { dominant: dom, support: sup,
                 level: dom.length ? "led" : (sup.length ? "support_only" : "absent") };
    }
    return out;
  }

  function collectiveBlind(mem, P) {
    const domSet = new Set();
    mem.forEach((m) => m.profile.dominant.forEach((d) => domSet.add(d)));
    const dom = LENSES.filter((d) => domSet.has(d));
    const uncovered = LENSES.filter(
      (d) => !mem.some((m) => m.profile.dominant.indexOf(d) !== -1));
    const matched = [];
    for (const c of P.combo) {
      if (!c.lenses.every((d) => domSet.has(d))) continue;
      const need = LENSES.filter((d) => c.need.indexOf("$" + d + "$") !== -1);
      // **الاحتواء التام لا التقاطع الجزئي** (`DEC-282` · `§7/②`)
      if (need.length && need.every((d) => uncovered.indexOf(d) !== -1)) {
        matched.push(Object.assign({}, c, { need_codes: need }));
      }
    }
    return { team_dominant: dom, uncovered: uncovered, documented: matched };
  }

  const polarPairs = (P) => P.polar.map((p) => [p.a, p.b, p.code]);

  function interPolarity(mem, P) {
    const out = [];
    for (let i = 0; i < mem.length; i++) {
      for (let j = i + 1; j < mem.length; j++) {
        const a = mem[i], b = mem[j];
        for (const [x, y, code] of polarPairs(P)) {
          for (const [p, q] of [[x, y], [y, x]]) {
            if (a.profile.dominant.indexOf(p) !== -1 && b.profile.dominant.indexOf(q) !== -1) {
              out.push({ a: a.code, b: b.code, lens_a: p, lens_b: q, polar: code });
            }
          }
        }
      }
    }
    return out;
  }

  const dyadKey = (x, y, P) => ((x + "–" + y) in P.dyad ? x + "–" + y : y + "–" + x);

  /** §5 — **قاعدةٌ مختومة** (`DEC-282` · `§7/①`): القطبيُّ أولاً وإلا أعلى مهيمنٍ لكلٍّ. */
  function pairMatrix(mem, P) {
    const out = [], polars = polarPairs(P);
    for (let i = 0; i < mem.length; i++) {
      for (let j = i + 1; j < mem.length; j++) {
        const a = mem[i], b = mem[j];
        const da = rank(a.sp, a.profile.dominant), db = rank(b.sp, b.profile.dominant);
        if (!da.length || !db.length) {
          out.push({ a: a.code, b: b.code, cross: null, reason: "no_dominant" });
          continue;
        }
        let pick = null;
        for (const [x, y, code] of polars) {
          if (da.indexOf(x) !== -1 && db.indexOf(y) !== -1) pick = [x, y, code];
          else if (da.indexOf(y) !== -1 && db.indexOf(x) !== -1) pick = [y, x, code];
          if (pick) break;
        }
        const [lx, ly, pcode] = pick ? pick : [da[0], db[0], null];
        // **تقاطعٌ على العدسة نفسها لا خليةَ مختومةً له** — قاعدةٌ دائمة
        // بختم المالك (`DEC-281`): يُعلَن الخلوّ بعدستيه.
        if (lx === ly) {
          out.push({ a: a.code, b: b.code, lens_a: lx, lens_b: ly,
                     dyad: null, polar: pcode, by: "same_lens", reason: "same_lens" });
          continue;
        }
        out.push({ a: a.code, b: b.code, lens_a: lx, lens_b: ly,
                   dyad: dyadKey(lx, ly, P), polar: pcode,
                   by: pick ? "polar" : "top_dominant" });
      }
    }
    return out;
  }

  /** §7 — **كل** عدسةٍ مهيمنة لكل عضو، لا واحدة (`DEC-282` · `§7/③`). */
  function rebound(mem) {
    const out = [];
    for (const m of mem) {
      const dom = rank(m.sp, m.profile.dominant);
      if (!dom.length) { out.push({ code: m.code, lens: null, has_path: false }); continue; }
      for (const d of dom) out.push({ code: m.code, lens: d, has_path: true });
    }
    return out;
  }

  function recommendation(cov) {
    const absent = LENSES.filter((d) => cov[d].level === "absent");
    const supportOnly = LENSES.filter((d) => cov[d].level === "support_only");
    return { absent: absent, support_only: supportOnly, gap: absent.concat(supportOnly) };
  }

  function run(members, pack) {
    const P = requirePack(pack);
    validate(members);
    const mem = members.map((m) => {
      const sp = {};
      for (const d of LENSES) sp[d] = Number(m.sp[d]);
      return { code: String(m.code).trim(), sp: sp, profile: profile(sp) };
    });
    const cov = coverage(mem);
    const band = {}, state = {};
    mem.forEach((m) => { band[m.code] = m.profile.band; state[m.code] = m.profile.state; });
    const audit = {
      engine_version: ENGINE_VERSION, spec_version: SPEC_VERSION,
      instrument_pin: INSTRUMENT_PIN,
      n_members: mem.length, members: mem.map((m) => m.code),
      band: band, state: state, coverage: cov,
      collective_blind: collectiveBlind(mem, P),
      pairs: pairMatrix(mem, P),
      inter_polarity: interPolarity(mem, P),
      rebound: rebound(mem),
      recommendation: recommendation(cov),
      full_matrix: mem.length <= FULL_MATRIX_MAX,
      unification_tag: "GAP-A-01/GAP-A-02 — توحيد تشغيلي مؤقت (DEC-040/041)",
      accepted_debts: ["GAP-A-01", "GAP-A-02"],
      open_debts: ["GAP-K2-TEAMBLIND-01"],
    };
    return { members: mem, audit: audit, pack: P };
  }

  // ── الباني — تسعةُ أقسامٍ من خلايا مختومة، بلا جملة ربطٍ مؤلَّفة ──────
  const cells = (row) => "| " + row.join(" | ") + " |";

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

  function buildReport(members, pack) {
    const P = requirePack(pack);
    const res = run(members, P);
    const a = res.audit;
    const L = [];
    let n = 0;
    const head = () => { n += 1; L.push(`## ${AR_NUM[n - 1]} · ${P.heading[String(n)]}`); L.push(""); };

    L.push(`> ⚠️ ${P.banner}`, "");
    for (const t of P.tag) L.push(`> وسم إلزامي: [${t}]`);
    L.push("");

    head();                                            // ① الأعضاء
    L.push(cells(["العضو", "مهيمن", "مساند", "نقطة عمى"]),
           cells([":---", ":---", ":---", ":---"]));
    for (const m of res.members) {
      const pr = m.profile;
      const fmt = (ds) => ds.map((d) => `${d} (${pr.band[d]})`).join(" · ") || "—";
      L.push(cells([m.code, fmt(pr.dominant), fmt(pr.support),
                    pr.blind.join(" · ") || "—"]));
    }
    L.push("");

    head();                                            // ② التغطية
    L.push(cells(["البُعد", "مهيمن", "مساند", "المستوى"]),
           cells([":---", ":---", ":---", ":---"]));
    const LVL = { led: "مغطّى بقيادة", support_only: "⚠️ بلا مهيمن جماعياً", absent: "⚠️ غائب" };
    for (const d of LENSES) {
      const c = a.coverage[d];
      L.push(cells([`**${d}** ${P.blind[d].name}`,
                    c.dominant.join(" · ") || "—", c.support.join(" · ") || "—",
                    LVL[c.level]]));
    }
    L.push("");

    head();                                            // ③ العمى الجماعي
    const cb = a.collective_blind;
    L.push(cells(["البُعد بلا مهيمن", "نقطة العمى الكبرى", "ما يغيب عن العدسة"]),
           cells([":---", ":---", ":---"]));
    for (const d of cb.uncovered) {
      const b = P.blind[d];
      L.push(cells([`**${d}** ${b.name}`, b.major, b.missing]));
    }
    L.push("");
    if (cb.documented.length) {
      L.push(cells(["تركيبة موثَّقة", "العمى الجماعي المتراكم",
                    "البُعد الغائب المطلوب", "الخطورة"]),
             cells([":---", ":---", ":---", ":---"]));
      for (const c of cb.documented) {
        L.push(cells([c.lenses.join(" + "), c.blind, c.need, c.risk]));
      }
      L.push("");
    }

    head();                                            // ④ مفارقة القطبية
    L.push(cells(["المقياس", "القيمة"]), cells([":---", ":---"]),
           cells(["أبعاد يقودها مهيمن",
                  String(LENSES.filter((d) => a.coverage[d].dominant.length).length)]),
           cells(["أبعاد بلا مهيمن", cb.uncovered.join(" · ") || "—"]),
           cells(["أزواج قطبية بين الأعضاء", String(a.inter_polarity.length)]), "");

    head();                                            // ⑤ مصفوفة الأزواج
    L.push(cells(["الزوج", "التقاطع", "محور الصدام", "بروتوكول الاحتواء",
                  "الكيان الهجين", "العمى المشترك"]),
           cells([":---", ":---", ":---", ":---", ":---", ":---"]));
    for (const pr of a.pairs) {
      if (!pr.dyad) {
        const cross = (pr.lens_a && pr.lens_b) ? `${pr.lens_a}–${pr.lens_b}` : "—";
        L.push(cells([`${pr.a} × ${pr.b}`, cross, "—", "—", "—", "—"]));
        continue;
      }
      const d = P.dyad[pr.dyad];
      L.push(cells([`**${pr.a} × ${pr.b}**`, `${pr.lens_a}–${pr.lens_b}`,
                    d.clash, d.containment, d.hybrid, d.blind]));
    }
    L.push("");

    head();                                            // ⑥ القطبية البينية
    if (a.inter_polarity.length) {
      L.push(cells(["الزوج البيني", "الطرف الأول", "الطرف الثاني",
                    "محور التعامد", "فلترة الطرف الأول", "فلترة الطرف الثاني"]),
             cells([":---", ":---", ":---", ":---", ":---", ":---"]));
      for (const ip of a.inter_polarity) {
        const pol = P.polar.find((p) => p.code === ip.polar);
        const [fa, fb] = pol.a === ip.lens_a
          ? [pol.filter_a, pol.filter_b] : [pol.filter_b, pol.filter_a];
        L.push(cells([`${ip.a} ↔ ${ip.b}`, `${ip.lens_a} (${ip.a})`,
                      `${ip.lens_b} (${ip.b})`, pol.axis, fa, fb]));
      }
    } else L.push("—");
    L.push("");

    head();                                            // ⑦ الارتداد
    L.push(cells(["العضو", "العدسة", "مُطلِق الارتداد", "نمط الانهيار الداخلي"]),
           cells([":---", ":---", ":---", ":---"]));
    for (const rb of a.rebound) {
      if (!rb.has_path) { L.push(cells([rb.code, "—", "—", "—"])); continue; }
      const r = P.rebound[rb.lens];
      L.push(cells([rb.code, `**${rb.lens}** ${r.name}`, r.trigger, r.pattern]));
    }
    L.push("");

    head();                                            // ⑧ التوصية
    const rec = a.recommendation;
    if (rec.gap.length) {
      L.push(cells(["البُعد الغائب", "نقطة العمى الكبرى", "ما يغيب عن العدسة"]),
             cells([":---", ":---", ":---"]));
      for (const d of rec.gap) {
        const b = P.blind[d];
        L.push(cells([`**${d}** ${b.name}`, b.major, b.missing]));
      }
    } else L.push("—");
    L.push("");

    head();                                            // ⑨ قفل العرض
    for (const lock of P.lock) L.push(`- ${lock}`);
    L.push("");

    const body = L.join("\n");
    const out = Object.assign({}, a);
    out.sections_rendered = n;
    out.pack_sha = { CONTENT_TEAM: _shaObj(P) };
    out.report_sha256 = PK._sha256(body).slice(0, 16);
    return [body, out];
  }

  return { LENSES, ENGINE_VERSION, SPEC_VERSION, MIN_MEMBERS, FULL_MATRIX_MAX,
           InputContractError, requirePack, validate, profile, rank, coverage,
           collectiveBlind, interPolarity, pairMatrix, rebound, recommendation,
           run, buildReport };
});
