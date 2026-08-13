"use strict";
/*
 * supervisor_core.js — نواة أداة المشرف (نظير `supervisor.py`)
 * ==============================================================
 * سند: `100-AUDIT-REGEN` (`DEC-220`) · `DEC-231` · `DEC-233` · `DEC-199` (تكافؤ النسخ)
 *
 * ترتيب الدرجات وأسماؤها ونصوص تفاصيلها **مطابقة حرفياً** لنظيرتها في
 * بايثون. أي تباعد يُجمَّد الطرفان (`DEC-200`) ولا يُرجَّح أحدهما.
 */
(function (root) {

  var SCHEMA_SUPPORTED = ["RAWAHIL-REPORT-v1.1", "RAWAHIL-REPORT-v1.2"];
  var CIRCLES = ["K2", "K3", "K4"];
  var REQUIRED_AUDIT = ["sp", "engine_version", "spec_version", "instrument_pin",
                        "entries_used", "pack_sha", "report_sha256"];

  // قائمة $K_4$ **منقولة حرفياً** من `136 §3/④` — لا تُختصر ولا يُزاد عليها.
  // و`entries_used` ليست فيها: عقد $K_4$ يعلن `codes` و`sections_rendered`
  // بدلاً منها، فطلبها كان سيوقف كل تقرير سليم بلا سند.
  var REQUIRED_AUDIT_K4 = [
    "sp", "codes", "bands", "constraints_activated", "constraint_map",
    "patterns_recognized", "interruption_points", "bottleneck",
    "choke_readings", "lookalike_flags", "reading_reserve", "excluded_out",
    "gap_report", "engine_version", "spec_version", "instrument_pin",
    "missing_content", "accepted_debts", "open_debts", "sections_rendered",
    "pack_sha", "report_sha256"];
  var FIELD_DEBT_K4 = "DEBT-K4-FIELD-01";

  function norm(t) {
    var lines = t.replace(/\r\n/g, "\n").split("\n").map(function (l) {
      return l.replace(/\s+$/, "");
    });
    while (lines.length && !lines[0]) lines.shift();
    while (lines.length && !lines[lines.length - 1]) lines.pop();
    return lines.join("\n");
  }

  /** يجزّئ المتن **الخام** — كما يفعل المحرك عند تسجيل البصمة. */
  function sha16(t) { return root.RawahilPacks._sha256(t).slice(0, 16); }

  function regen(circle, audit, mode) {
    var RP = root.RawahilReports;
    var sp = JSON.parse(JSON.stringify(audit.sp));
    if (circle === "K2") return RP.buildReportK2(sp, mode || "full");
    if (circle === "K4") return RP.buildReportK4(sp);
    return RP.buildReportK3(sp);
  }

  /** نظير `repr` البايثوني — التفاصيل نصّ مقارَن، فلا بدّ أن تتطابق حرفياً. */
  function repr(v) {
    if (v === undefined || v === null) return "None";
    if (typeof v === "string") return "'" + v + "'";
    if (typeof v === "boolean") return v ? "True" : "False";
    if (Array.isArray(v)) return "[" + v.map(repr).join(", ") + "]";
    return JSON.stringify(v);
  }

  /** نظير `str` البايثوني: النصّ بلا علامات، وغيره كـrepr. */
  function str(v) { return (typeof v === "string") ? v : repr(v); }

  function grade(payload) {
    var out = [], errs = [];
    function ok(name, passed, detail) {
      out.push([name, passed, detail || ""]);
      if (!passed) errs.push(name + (detail ? " — " + detail : ""));
    }

    // ⓪ صلاحية المخطَّط والبنية
    var schema = payload.schema;
    ok("⓪ المخطَّط معروف", SCHEMA_SUPPORTED.indexOf(schema) !== -1, "وُجد «" + schema + "»");
    var circle = String(payload.circle || "").toUpperCase();
    ok("⓪ الدائرة معلومة", CIRCLES.indexOf(circle) !== -1, "وُجد «" + circle + "»");
    if (CIRCLES.indexOf(circle) === -1) return [out, errs];

    var audit = payload.audit;
    if (!audit || typeof audit !== "object" || Array.isArray(audit)) {
      ok("⓪ حقل audit حاضر", false, "غائب أو ليس كائناً");
      return [out, errs];
    }
    ok("⓪ حقل audit حاضر", true);

    // ① اكتمال العقد — قائمةٌ لكل دائرة عقدُها
    var req = (circle === "K4") ? REQUIRED_AUDIT_K4 : REQUIRED_AUDIT;
    var name1 = (circle === "K4")
      ? "① حقول كتلة التدقيق الاثنان والعشرون (136 §3/④)"
      : "① الحقول السبعة الملزِمة";
    var missing = req.filter(function (k) { return !(k in audit); });
    ok(name1, !missing.length, missing.length ? "ناقص " + repr(missing) : "");
    if (missing.length) return [out, errs];

    // ② النطاقات مُعلَنة (DEC-231)
    var scopes = payload.scopes, hasBrief;
    if (schema === "RAWAHIL-REPORT-v1.2") {
      var declared = Array.isArray(scopes) && scopes.length &&
        scopes.every(function (s) { return s === "full" || s === "brief"; });
      ok("② النطاقات مُعلَنة (DEC-231)", !!declared, "وُجد " + repr(scopes));
      hasBrief = !!(scopes && scopes.indexOf("brief") !== -1);
    } else {
      out.push(["② النطاقات مُعلَنة (DEC-231)", null,
                "مخطَّط v1.1 — سابق للقرار · لا يُحاسَب"]);
      hasBrief = payload.audit_brief !== null && payload.audit_brief !== undefined;
      scopes = hasBrief ? ["full", "brief"] : ["full"];
    }

    var body = payload.delivery || {};
    var briefPresent = ("markdown_brief" in body);
    ok("② اتّساق الإعلان بالمحتوى", briefPresent === hasBrief,
       "scopes=" + str(scopes) + " · markdown_brief " + (briefPresent ? "حاضر" : "غائب"));

    // $K_4$ **لا نطاق مختصر لها**: `DEC-231` شرَعه لـ$K_2$ وحدها، وعقد `136 §3`
    // لا يعرفه. وبلا هذه الدرجة يمرّ إعلانٌ كاذب صامتاً — لأن الدرجة ⑧
    // مشروطة بـ$K_2$ فلا تدقّق ما أُعلن هنا.
    if (circle === "K4") {
      ok("② لا نطاق مختصر في K4 (لا وجود له في 136 §3)", !hasBrief,
         "أُعلن " + repr(scopes));
    }

    // ③ المتن المُسلَّم
    var delivered = body.markdown;
    if (typeof delivered !== "string" || !delivered.trim()) {
      ok("③ المتن المُسلَّم حاضر", false, "delivery.markdown غائب أو فارغ");
      return [out, errs];
    }
    ok("③ المتن المُسلَّم حاضر", true);

    // ④ البصمة تصف المُسلَّم — على المتن الخام
    var live = sha16(delivered);
    ok("④ البصمة تصف المُسلَّم", live === audit.report_sha256,
       "محسوبة " + live + " · مسجَّلة " + audit.report_sha256);

    // ⑤ إعادة التوليد من الـaudit وحده
    var pair;
    try { pair = regen(circle, audit); }
    catch (e) {
      // اسم الاستثناء وحده — نصّ الرسالة متباعد بين المحرّكين (`GAP-MSG-PARITY-01`)
      ok("⑤ إعادة التوليد", false, "عقد المدخل مرفوض: " + (e.name || "Error"));
      return [out, errs];
    }
    var text2 = pair[0], audit2 = pair[1];
    var exact = (text2 === delivered);
    ok("⑤ إعادة التوليد تطابق المُسلَّم", exact,
       exact ? "" : (norm(text2) === norm(delivered)
         ? "المتن مطابق **بعد التطبيع** — الفارق مسافات أو أسطر ⇒ النقل غيّر الملف، لا المحرك"
         : "المتن مختلف جوهرياً"));

    // ⑥ بصمة المُعاد
    ok("⑥ بصمة المُعاد = المسجَّلة", audit2.report_sha256 === audit.report_sha256,
       "مُعاد " + audit2.report_sha256 + " · مسجَّل " + audit.report_sha256);

    // ⑦ انجراف الحزم
    var keys = {}, k;
    for (k in audit.pack_sha) keys[k] = 1;
    for (k in audit2.pack_sha) keys[k] = 1;
    var drift = Object.keys(keys).sort().filter(function (x) {
      return audit.pack_sha[x] !== audit2.pack_sha[x];
    });
    ok("⑦ الحزم غير منجرفة", !drift.length, drift.length ? "منجرفة: " + repr(drift) : "");

    // ⑧ النطاق المختصر
    if (hasBrief && circle === "K2") {
      var brief = body.markdown_brief, ab = payload.audit_brief || {};
      if (typeof brief === "string" && brief.trim() && ("report_sha256" in ab)) {
        var pb = regen(circle, ab, "brief");
        ok("⑧ المختصر: البصمة تصف المُسلَّم", sha16(brief) === ab.report_sha256);
        ok("⑧ المختصر: إعادة التوليد تطابق", norm(pb[0]) === norm(brief));
      } else {
        ok("⑧ المختصر مكتمل", false, "متن أو audit_brief ناقص");
      }
    }

    // ⑨ حارسا المخرج على ما وصل المستفيد
    var G = root.RawahilSPGate;
    var lsp = G.scan(delivered), lpct = G.scanPct(delivered);
    ok("⑨ ح-4 — لا رمز SP%", !lsp.length, lsp.length ? lsp.length + " إصابة" : "");
    ok("⑨ ح-5 — لا نسبة غير مسجَّلة", !lpct.length,
       lpct.length ? lpct.length + " إصابة: " +
         repr(lpct.slice(0, 3).map(function (h) { return h[1].trim().slice(0, 40); })) : "");

    if (circle !== "K4") return [out, errs];

    // ── ⑩ الحقل الإعلاني يُقابَل بالمحرك ─────────────────────────────────
    // `open_debts` و`accepted_debts` **مصرَّح بعدم قياسهما** (`136 §3/④`):
    // مصدرهما سجل الحوكمة، ومزامنتهما **يدوية** (`DEC-267`). فما لا يُقاس
    // مصدرُه **يُقاس انجرافه**: قائمة التقرير المُسلَّم تُقابَل بقائمة المحرك
    // الحالي — كما تُقابَل بصمات الحزم في ⑦. وبهذا يصير الحدُّ المُعلَن مقيساً.
    var dSeen = {}, dCode;
    (audit.open_debts || []).forEach(function (c) { dSeen[c] = (dSeen[c] || 0) + 1; });
    (audit2.open_debts || []).forEach(function (c) { dSeen[c] = (dSeen[c] || 0) + 2; });
    var debtDrift = Object.keys(dSeen).filter(function (c) {
      return dSeen[c] !== 3;
    }).sort();
    ok("⑩ الديون المُعلنة غير منجرفة", !debtDrift.length,
       debtDrift.length ? "فارق: " + repr(debtDrift) : "");
    var hasFieldDebt = (audit.open_debts || []).indexOf(FIELD_DEBT_K4) !== -1;
    ok("⑩ دَين الميدان مُعلَن (DEBT-K4-FIELD-01)", hasFieldDebt,
       hasFieldDebt ? "" : "غائب — فتُقرأ الطبقة التفسيرية محقَّقةً ميدانياً");

    // ── ⑪ سطح القراءة العابرة — إن أُعلن فيُدقَّق، **وفصلُه يُقاس** ────────
    var xtext = body.markdown_crossing, xaudit = payload.audit_crossing;
    if ((xtext === undefined || xtext === null) &&
        (xaudit === undefined || xaudit === null)) return [out, errs];
    if (!(typeof xtext === "string" && xtext.trim() && xaudit &&
          typeof xaudit === "object" && !Array.isArray(xaudit) &&
          ("surface_sha256" in xaudit))) {
      ok("⑪ السطح العابر مكتمل", false, "متن أو audit_crossing ناقص");
      return [out, errs];
    }
    var xpair;
    try { xpair = root.RawahilReports.buildCrossingSurface(JSON.parse(JSON.stringify(audit.sp))); }
    catch (e2) {
      ok("⑪ السطح العابر: إعادة التوليد", false,
         "عقد المدخل مرفوض: " + (e2.name || "Error"));
      return [out, errs];
    }
    var xt2 = xpair[0], xa2 = xpair[1];
    var xlive = sha16(xtext);
    ok("⑪ السطح العابر: البصمة تصف المُسلَّم", xlive === xaudit.surface_sha256,
       "محسوبة " + xlive + " · مسجَّلة " + xaudit.surface_sha256);
    ok("⑪ السطح العابر: إعادة التوليد تطابق", xt2 === xtext,
       xt2 === xtext ? "" : "المتن مختلف");
    ok("⑪ السطح العابر: القيود غير منجرفة",
       repr(xaudit.entries) === repr(xa2.entries),
       "مُسلَّم " + str(xaudit.entries) + " · مُعاد " + str(xa2.entries));
    // `DEC-268`: سطحٌ **خارج متن أي تقرير**. الدمج يُبطل العزل، فيُقاس بأن
    // لا يظهر أي قيدٍ من قيود السطح في المتن المُسلَّم.
    var leak = xtext.split("\n").filter(function (l) {
      return l.indexOf("- ") === 0 && delivered.indexOf(l) !== -1;
    });
    ok("⑪ السطح العابر خارج المتن (DEC-268)", !leak.length,
       leak.length ? leak.length + " قيداً مدموجاً" : "");

    return [out, errs];
  }

  var API = { grade: grade, norm: norm, sha16: sha16, regen: regen,
              SCHEMA_SUPPORTED: SCHEMA_SUPPORTED, REQUIRED_AUDIT: REQUIRED_AUDIT };
  if (typeof module !== "undefined" && module.exports) module.exports = API;
  root.RawahilSupervisor = API;

})(typeof window !== "undefined" ? window : globalThis);
